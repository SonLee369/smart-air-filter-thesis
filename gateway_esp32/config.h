// config.h - gateway (ESP32-WROOM, 38-pin DevKit) pins and settings.
// The thesis uses an ESP8266 here; this build runs the gateway on an ESP32.
#pragma once

// ================= LoRa Ra-02 pins (VSPI, same bus pins as the node) =================
#define PIN_LORA_SCK   18
#define PIN_LORA_MISO  19
#define PIN_LORA_MOSI  23
#define PIN_LORA_NSS   5
#define PIN_LORA_RST   14
#define PIN_LORA_DIO0  26   // wired but polled; avoids strapping pin GPIO2

// ================= Web server [thesis 2.5] =================
#define HTTP_PORT            80
#define WIFI_RETRY_MS        10000UL   // reconnect attempt period
#define DATA_STALE_MS        30000UL   // dashboard shows "no data" after this

// ================= Dashboard ranges (match node config.h) =================
#define CO_VALID_MAX_PPM     2000.0f
#define PM_VALID_MAX_UGM3    800.0f
#define CO_THRESHOLD_PPM     50.0f
#define PM_THRESHOLD_UGM3    35.0f
#define ETA_MIN_PM_UGM3      10.0f     // efficiency shown only above these inlet values
#define ETA_MIN_CO_PPM       5.0f

// ================= Airflow estimate [thesis 2.6.3f] =================
// v_tip = 2*pi*r*RPM/60, v = k*v_tip, Q = v*A
// r and A are NOT given in the thesis: measure your fan and column.
#define FAN_RADIUS_M         0.10f     // [tune] fan blade radius, m
#define INLET_AREA_M2        0.0314f   // [tune] effective column cross-section, m2
#define AIRFLOW_K            0.6f      // correction factor [thesis]
