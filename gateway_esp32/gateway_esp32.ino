// Smart air filter - LoRa gateway + web dashboard (ESP32-WROOM)
// Baseline reproduction of "Cot loc bui thong minh" (thesis 2.4, 2.5, 2.6.7).
// The thesis gateway is an ESP8266; this port runs the same design on an ESP32.
//
// - Listens continuously on LoRa, validates SensorPacket (size + receiverId),
//   keeps the latest packet in RAM (no flash writes).
// - Joins the existing WiFi (STA), serves index.html from LittleFS and the
//   latest data as JSON on /get-data (polled by the page with AJAX).

#include <WiFi.h>
#include <WebServer.h>
#include <LittleFS.h>
#include <SPI.h>
#include <LoRa.h>
#include "config.h"
#include "secrets.h"
#include "SensorPacket.h"

static WebServer server(HTTP_PORT);

static SensorPacket currentPacket = {};
static bool hasData = false;
static uint32_t lastRxMs = 0;
static int lastRssi = 0;
static float lastSnr = 0;
static uint32_t rxOk = 0, rxInvalid = 0;
static uint32_t lastWifiTry = 0;
static bool wifiReported = false;

static const char* modeName(uint8_t m) {
  switch (m) {
    case MODE_MEASURING: return "MEASURING";
    case MODE_FILTERING: return "FILTERING";
    case MODE_SELF_TEST: return "SELF_TEST";
  }
  return "UNKNOWN";
}

// Efficiency (thesis eq. 7, 8); null in JSON when the inlet value is too small.
static void fmtEta(char* out, size_t n, float in, float outVal, float minIn) {
  if (in < minIn) snprintf(out, n, "null");
  else snprintf(out, n, "%.1f", (in - outVal) / in * 100.0f);
}

// ---------------- LoRa ----------------
static void pollLoRa() {
  int size = LoRa.parsePacket();
  if (size == 0) return;

  // Length check: must be exactly one SensorPacket (thesis 2.6.7a)
  if (size != (int)sizeof(SensorPacket)) {
    while (LoRa.available()) LoRa.read();
    rxInvalid++;
    Serial.printf("[LORA] dropped packet: %d bytes, expected %u\n", size, (unsigned)sizeof(SensorPacket));
    return;
  }

  SensorPacket p;
  LoRa.readBytes((uint8_t*)&p, sizeof(p));

  // Id check: ignore packets addressed to other gateways
  if (p.receiverId != GATEWAY_ID) {
    rxInvalid++;
    Serial.printf("[LORA] dropped packet for receiver 0x%02X\n", p.receiverId);
    return;
  }

  currentPacket = p;
  hasData = true;
  lastRxMs = millis();
  lastRssi = LoRa.packetRssi();
  lastSnr = LoRa.packetSnr();
  rxOk++;
  Serial.printf("[LORA] node %u %s CO %.1f/%.1f PM %.0f/%.0f RPM %lu motor=%s filter=%s rssi=%d\n",
                p.senderId, modeName(p.motor_mode), p.CO_ppm, p.CO_ppm_2, p.dust, p.dust_2,
                (unsigned long)p.RPM, p.motor_flag ? "ok" : "FAULT",
                p.filter_flag ? "REPLACE" : "ok", lastRssi);
}

// ---------------- Web ----------------
static void handleRoot() {
  File f = LittleFS.open("/index.html", "r");
  if (!f) {
    server.send(500, "text/plain",
                "index.html not found in LittleFS. Upload the data/ folder (see README).");
    return;
  }
  server.streamFile(f, "text/html");
  f.close();
}

static void handleGetData() {
  const SensorPacket& p = currentPacket;
  char etaPm[16], etaCo[16];
  fmtEta(etaPm, sizeof(etaPm), p.dust, p.dust_2, ETA_MIN_PM_UGM3);
  fmtEta(etaCo, sizeof(etaCo), p.CO_ppm, p.CO_ppm_2, ETA_MIN_CO_PPM);

  // Airflow estimate from RPM (thesis eq. 3-5)
  float vTip = 2.0f * PI * FAN_RADIUS_M * p.RPM / 60.0f;
  float q = AIRFLOW_K * vTip * INLET_AREA_M2;  // m3/s

  char json[900];
  snprintf(json, sizeof(json),
           "{\"has_data\":%s,\"age_ms\":%lu,\"stale_ms\":%lu,"
           "\"node_id\":%u,\"co_in\":%.1f,\"co_out\":%.1f,\"pm_in\":%.1f,\"pm_out\":%.1f,"
           "\"eta_pm\":%s,\"eta_co\":%s,"
           "\"rpm\":%lu,\"airflow_m3h\":%.1f,\"motor_ok\":%s,\"mode\":\"%s\","
           "\"filter_flag\":%s,\"web_flag\":%s,"
           "\"mq7_fault_in\":%s,\"mq7_fault_out\":%s,\"gp2y_fault_in\":%s,\"gp2y_fault_out\":%s,"
           "\"co_max\":%.0f,\"pm_max\":%.0f,\"co_thr\":%.0f,\"pm_thr\":%.0f,"
           "\"rssi\":%d,\"snr\":%.1f,\"rx_ok\":%lu,\"rx_invalid\":%lu}",
           hasData ? "true" : "false", (unsigned long)(hasData ? millis() - lastRxMs : 0),
           (unsigned long)DATA_STALE_MS,
           p.senderId, p.CO_ppm, p.CO_ppm_2, p.dust, p.dust_2,
           etaPm, etaCo,
           (unsigned long)p.RPM, q * 3600.0f, p.motor_flag ? "true" : "false", modeName(p.motor_mode),
           p.filter_flag ? "true" : "false", p.web_flag ? "true" : "false",
           p.mq7_flag ? "true" : "false", p.mq7_flag_2 ? "true" : "false",
           p.gp2y_flag ? "true" : "false", p.gp2y_flag_2 ? "true" : "false",
           CO_VALID_MAX_PPM, PM_VALID_MAX_UGM3, CO_THRESHOLD_PPM, PM_THRESHOLD_UGM3,
           lastRssi, lastSnr, (unsigned long)rxOk, (unsigned long)rxInvalid);

  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", json);
}

static void maintainWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!wifiReported) {
      wifiReported = true;
      Serial.print("[WIFI] connected, dashboard at http://");
      Serial.println(WiFi.localIP());
    }
    return;
  }
  wifiReported = false;
  if (millis() - lastWifiTry >= WIFI_RETRY_MS) {
    lastWifiTry = millis();
    Serial.printf("[WIFI] connecting to %s ...\n", WIFI_SSID);
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\nSmart air filter gateway (ESP32)");

  // WiFi in station mode with the saved credentials (thesis 2.5.3)
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWifiTry = millis();

  if (!LittleFS.begin()) Serial.println("[FS] LittleFS mount failed");
  else if (!LittleFS.exists("/index.html")) Serial.println("[FS] /index.html missing, upload data/");

  server.on("/", HTTP_GET, handleRoot);
  server.on("/get-data", HTTP_GET, handleGetData);
  server.onNotFound([]() { server.send(404, "text/plain", "Not found"); });
  server.begin();

  // LoRa in receive mode, polled from loop() (no SPI access from an ISR)
  SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);
  LoRa.setPins(PIN_LORA_NSS, PIN_LORA_RST, PIN_LORA_DIO0);
  while (!LoRa.begin(LORA_FREQUENCY_HZ)) {
    Serial.println("[LORA] init failed, retrying");
    delay(1000);
  }
  LoRa.setSpreadingFactor(LORA_SPREADING);
  LoRa.setSignalBandwidth(LORA_BANDWIDTH_HZ);
  LoRa.setCodingRate4(LORA_CODING_RATE);
  LoRa.setSyncWord(LORA_SYNC_WORD);
  LoRa.enableCrc();
  Serial.println("[LORA] listening");
}

void loop() {
  pollLoRa();
  maintainWifi();
  server.handleClient();
}
