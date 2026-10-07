// Smart air filter column - node firmware (ESP32)
// Baseline reproduction of "Cot loc bui thong minh" (thesis, chapter 2).
//
// Flow: read 2x GP2Y1010 + 2x MQ-7 -> decide MEASURING / FILTERING -> drive fan
// through BTS7960 with a soft PWM ramp -> measure RPM with KY-003 (interrupt) ->
// check motor, filter and (at 00:00) sensors -> send SensorPacket over LoRa.
//
// Serial commands (115200 baud):
//   t                      run the sensor self test now
//   r                      calibrate MQ-7 R0 in clean air and store it in NVS
//   T2026-10-05 21:30:00   set the RTC
// Test helpers (bench testing only):
//   sim <co_in|co_out|pm_in|pm_out> <value>   override a reading
//   sim off                                   back to real sensor values
//   fan m | fan f | fan auto                  force MEASURING / FILTERING, or automatic
//   kf on | kf off | kf                       Kalman output drives control / raw drives control / stats
//   ?                                         help

#include <SPI.h>
#include <Wire.h>
#include <LoRa.h>
#include <RTClib.h>
#include <Preferences.h>
#include "config.h"
#include "SensorPacket.h"
#include "kalman.h"

// ---------------- Global state ----------------
struct Readings {
  float coIn, coOut;     // ppm
  float pmIn, pmOut;     // ug/m3
  float vCoIn, vCoOut;   // sensor output voltage (after undoing the divider)
  float vPmIn, vPmOut;
  float rsIn, rsOut;     // MQ-7 sensing resistance
};

static Readings rd = {};
static RTC_DS1307 rtc;
static bool rtcOk = false;
static Preferences prefs;
static float mq7R0In = MQ7_R0_IN_DEFAULT;
static float mq7R0Out = MQ7_R0_OUT_DEFAULT;

static MotorMode mode = MODE_MEASURING;
static uint32_t modeSince = 0;

// Fan
static float targetDuty = DUTY_MEASURING;
static float currentDuty = 0.0f;
static uint32_t dutyReachedAt = 0;   // millis() when currentDuty reached targetDuty
static uint32_t lastRampMs = 0;

// RPM (KY-003 on interrupt, thesis 2.6.3)
static volatile uint32_t hallPulses = 0;
static volatile uint32_t hallLastUs = 0;
static portMUX_TYPE hallMux = portMUX_INITIALIZER_UNLOCKED;
static uint32_t rpm = 0;
static uint32_t lastRpmMs = 0;

// Health flags (true = fault), see SensorPacket.h
static bool motorOk = true;
static int motorBad = 0, motorGood = 0;
static bool filterFlag = false;
static int filterBad = 0, filterGood = 0;
static bool mq7FaultIn = false, mq7FaultOut = false;
static bool gp2yFaultIn = false, gp2yFaultOut = false;
static float etaPm = NAN, etaCo = NAN;

// Self test
static uint32_t lastSelfTestDate = 0;  // yyyymmdd of the last scheduled run
static uint32_t stSamples = 0;
static Readings stSum = {};

// Timers
static uint32_t lastSensorMs = 0;
static uint32_t lastTxMs = 0;
static bool txNow = false;
static bool loraOk = false;

// Test helpers: NAN = use the real sensor
static float simCoIn = NAN, simCoOut = NAN, simPmIn = NAN, simPmOut = NAN;
static bool manualMode = false;

// AI feature F1: one Kalman filter per channel
static Kalman1D kfCoIn(KF_CO_Q, KF_CO_R, KF_GATE_SIGMA), kfCoOut(KF_CO_Q, KF_CO_R, KF_GATE_SIGMA);
static Kalman1D kfPmIn(KF_PM_Q, KF_PM_R, KF_GATE_SIGMA), kfPmOut(KF_PM_Q, KF_PM_R, KF_GATE_SIGMA);
static bool kfForControl = KF_USE_FOR_CONTROL;   // true = 'fan m/f' holds the mode, decideMode() is skipped

// ---------------- Helpers ----------------
static const char* modeName(uint8_t m) {
  switch (m) {
    case MODE_MEASURING: return "MEASURING";
    case MODE_FILTERING: return "FILTERING";
    case MODE_SELF_TEST: return "SELF_TEST";
  }
  return "?";
}

// Sort and average the middle part: drops spikes from motor noise (thesis 2.6.1).
static float trimmedMean(float* v, int n, int trim) {
  for (int i = 1; i < n; i++) {
    float x = v[i];
    int j = i - 1;
    while (j >= 0 && v[j] > x) { v[j + 1] = v[j]; j--; }
    v[j + 1] = x;
  }
  float sum = 0;
  for (int i = trim; i < n - trim; i++) sum += v[i];
  return sum / (n - 2 * trim);
}

// ---------------- GP2Y1010AU0F ----------------
// LED is active LOW. Pulse 0.32 ms every 10 ms, sample at 0.28 ms (datasheet).
static float readGp2yVolts(uint8_t ledPin, uint8_t outPin) {
  float s[GP2Y_SAMPLES];
  for (int i = 0; i < GP2Y_SAMPLES; i++) {
    uint32_t t0 = micros();
    digitalWrite(ledPin, LOW);
    delayMicroseconds(GP2Y_SAMPLE_DELAY_US);
    uint32_t mv = analogReadMilliVolts(outPin);
    while (micros() - t0 < GP2Y_PULSE_US) {}
    digitalWrite(ledPin, HIGH);
    s[i] = mv / 1000.0f * DIVIDER_GAIN;
    uint32_t used = micros() - t0;
    if (used < GP2Y_PERIOD_US) delayMicroseconds(GP2Y_PERIOD_US - used);
  }
  return trimmedMean(s, GP2Y_SAMPLES, 2);
}

static float gp2yToUgm3(float v, float vClean) {
  float d = (v - vClean) * GP2Y_UG_PER_VOLT;
  return d < 0 ? 0 : d;
}

// ---------------- MQ-7 ----------------
static float readMq7Volts(uint8_t pin) {
  float s[MQ7_SAMPLES];
  for (int i = 0; i < MQ7_SAMPLES; i++) {
    s[i] = analogReadMilliVolts(pin) / 1000.0f * DIVIDER_GAIN;
    delay(2);
  }
  return trimmedMean(s, MQ7_SAMPLES, 4);
}

static float mq7Rs(float vout) {
  if (vout < 0.01f) return INFINITY;
  return MQ7_RL_EFF_OHMS * (MQ7_VC - vout) / vout;
}

static float mq7Ppm(float rs, float r0) {
  if (!isfinite(rs) || r0 <= 0) return 0;
  return MQ7_CURVE_A * powf(rs / r0, MQ7_CURVE_B);
}

static void readSensors() {
  rd.vPmIn = readGp2yVolts(PIN_GP2Y_IN_LED, PIN_GP2Y_IN_OUT);
  rd.vPmOut = readGp2yVolts(PIN_GP2Y_OUT_LED, PIN_GP2Y_OUT_OUT);
  rd.pmIn = gp2yToUgm3(rd.vPmIn, GP2Y_IN_V_CLEAN);
  rd.pmOut = gp2yToUgm3(rd.vPmOut, GP2Y_OUT_V_CLEAN);

  rd.vCoIn = readMq7Volts(PIN_MQ7_IN);
  rd.vCoOut = readMq7Volts(PIN_MQ7_OUT);
  rd.rsIn = mq7Rs(rd.vCoIn);
  rd.rsOut = mq7Rs(rd.vCoOut);
  rd.coIn = mq7Ppm(rd.rsIn, mq7R0In);
  rd.coOut = mq7Ppm(rd.rsOut, mq7R0Out);

  // F1: filter every channel; control uses the filtered values only after 'kf on'
  kfCoIn.update(rd.coIn);
  kfCoOut.update(rd.coOut);
  kfPmIn.update(rd.pmIn);
  kfPmOut.update(rd.pmOut);
  if (kfForControl) {
    rd.coIn = kfCoIn.x;
    rd.coOut = kfCoOut.x;
    rd.pmIn = kfPmIn.x;
    rd.pmOut = kfPmOut.x;
  }

  if (!isnan(simCoIn))  rd.coIn = simCoIn;
  if (!isnan(simCoOut)) rd.coOut = simCoOut;
  if (!isnan(simPmIn))  rd.pmIn = simPmIn;
  if (!isnan(simPmOut)) rd.pmOut = simPmOut;
}

// ---------------- Fan (BTS7960) ----------------
static void IRAM_ATTR onHallPulse() {
  uint32_t now = micros();
  portENTER_CRITICAL_ISR(&hallMux);
  if (now - hallLastUs >= HALL_MIN_INTERVAL_US) {  // software debounce
    hallPulses = hallPulses + 1;
    hallLastUs = now;
  }
  portEXIT_CRITICAL_ISR(&hallMux);
}

static void setMode(MotorMode m) {
  if (m == mode) return;
  Serial.printf("[MODE] %s -> %s\n", modeName(mode), modeName(m));
  mode = m;
  modeSince = millis();
  targetDuty = (m == MODE_FILTERING) ? DUTY_FILTERING : DUTY_MEASURING;
  txNow = true;
}

// Move currentDuty toward targetDuty at DUTY_RAMP_PER_S (smooth speed change).
static void updateFanRamp() {
  uint32_t now = millis();
  float dt = (now - lastRampMs) / 1000.0f;
  if (dt < 0.02f) return;
  lastRampMs = now;
  if (currentDuty == targetDuty) return;

  float step = DUTY_RAMP_PER_S * dt;
  if (currentDuty < targetDuty) currentDuty = min(currentDuty + step, targetDuty);
  else currentDuty = max(currentDuty - step, targetDuty);
  if (currentDuty == targetDuty) dutyReachedAt = now;

  ledcWrite(PIN_RPWM, (uint32_t)(currentDuty * ((1 << PWM_RES_BITS) - 1)));
}

// RPM = 60 * N with N pulses per second, one magnet (thesis eq. 2).
static void updateRpm() {
  uint32_t now = millis();
  if (now - lastRpmMs < RPM_WINDOW_MS) return;
  uint32_t elapsed = now - lastRpmMs;
  lastRpmMs = now;

  portENTER_CRITICAL(&hallMux);
  uint32_t n = hallPulses;
  hallPulses = 0;
  portEXIT_CRITICAL(&hallMux);
  rpm = (uint32_t)(n * 60000UL / elapsed);

  // Motor check: compare with duty * 6000, skipping speed transitions (thesis 2.6.3e).
  if (currentDuty != targetDuty || now - dutyReachedAt < RPM_SETTLE_MS) return;
  float expected = currentDuty * RPM_PER_DUTY;
  bool bad = fabsf((float)rpm - expected) > expected * RPM_TOLERANCE;
  if (bad) { motorBad++; motorGood = 0; }
  else     { motorGood++; motorBad = 0; }
  if (motorOk && motorBad >= RPM_FAULT_COUNT) {
    motorOk = false;
    txNow = true;
    Serial.printf("[MOTOR] fault: %lu RPM, expected %.0f\n", (unsigned long)rpm, expected);
  } else if (!motorOk && motorGood >= RPM_FAULT_COUNT) {
    motorOk = true;
    txNow = true;
    Serial.println("[MOTOR] back to normal");
  }
}

// ---------------- Checks ----------------
static bool mq7Faulty(float v, float ppm) {
  return v < MQ7_V_MIN || v > MQ7_V_MAX || ppm > CO_VALID_MAX_PPM;
}

static bool gp2yFaulty(float v, float ug) {
  return v < GP2Y_V_MIN || v > GP2Y_V_MAX || ug > PM_VALID_MAX_UGM3;
}

// Filter efficiency (thesis eq. 7, 8, 11). Flag after a sustained low efficiency.
static void checkFilter() {
  bool pmValid = !gp2yFaultIn && !gp2yFaultOut && rd.pmIn >= FILTER_EVAL_MIN_PM;
  bool coValid = !mq7FaultIn && !mq7FaultOut && rd.coIn >= FILTER_EVAL_MIN_CO;
  etaPm = pmValid ? (rd.pmIn - rd.pmOut) / rd.pmIn * 100.0f : NAN;
  etaCo = coValid ? (rd.coIn - rd.coOut) / rd.coIn * 100.0f : NAN;
  if (!pmValid && !coValid) return;

  bool bad = (pmValid && etaPm < FILTER_MIN_EFFICIENCY) || (coValid && etaCo < FILTER_MIN_EFFICIENCY);
  if (bad) { filterBad++; filterGood = 0; }
  else     { filterGood++; filterBad = 0; }
  if (!filterFlag && filterBad >= FILTER_BAD_COUNT) {
    filterFlag = true;
    txNow = true;
    Serial.println("[FILTER] efficiency below 50 %, replace filter");
  } else if (filterFlag && filterGood >= FILTER_BAD_COUNT) {
    filterFlag = false;
    txNow = true;
    Serial.println("[FILTER] efficiency OK");
  }
}

static void startSelfTest() {
  Serial.println("[SELFTEST] start");
  setMode(MODE_SELF_TEST);
  stSamples = 0;
  stSum = {};
}

// Sensor check (thesis 2.6.5): fan at measuring power, settle, average, compare with valid range.
static void runSelfTest() {
  uint32_t t = millis() - modeSince;
  if (t < SELF_TEST_SETTLE_MS) return;

  stSum.vCoIn += rd.vCoIn;  stSum.vCoOut += rd.vCoOut;
  stSum.vPmIn += rd.vPmIn;  stSum.vPmOut += rd.vPmOut;
  stSum.coIn += rd.coIn;    stSum.coOut += rd.coOut;
  stSum.pmIn += rd.pmIn;    stSum.pmOut += rd.pmOut;
  stSamples++;
  if (t < SELF_TEST_SETTLE_MS + SELF_TEST_WINDOW_MS) return;

  float n = stSamples;
  mq7FaultIn   = mq7Faulty(stSum.vCoIn / n, stSum.coIn / n);
  mq7FaultOut  = mq7Faulty(stSum.vCoOut / n, stSum.coOut / n);
  gp2yFaultIn  = gp2yFaulty(stSum.vPmIn / n, stSum.pmIn / n);
  gp2yFaultOut = gp2yFaulty(stSum.vPmOut / n, stSum.pmOut / n);
  Serial.printf("[SELFTEST] done (%lu samples) MQ7 in:%s out:%s  GP2Y in:%s out:%s\n",
                (unsigned long)stSamples,
                mq7FaultIn ? "FAULT" : "ok", mq7FaultOut ? "FAULT" : "ok",
                gp2yFaultIn ? "FAULT" : "ok", gp2yFaultOut ? "FAULT" : "ok");
  setMode(MODE_MEASURING);
}

static void checkSchedule() {
  if (!rtcOk || mode == MODE_SELF_TEST) return;
  DateTime now = rtc.now();
  uint32_t date = now.year() * 10000UL + now.month() * 100UL + now.day();
  if (now.hour() == SELF_TEST_HOUR && now.minute() == 0 && date != lastSelfTestDate) {
    lastSelfTestDate = date;
    startSelfTest();
  }
}

// MEASURING <-> FILTERING on inlet CO / dust (thesis 2.6.2) with hysteresis and dwell times.
static void decideMode() {
  if (manualMode) return;
  uint32_t inMode = millis() - modeSince;
  bool polluted = rd.coIn > CO_THRESHOLD_PPM || rd.pmIn > PM_THRESHOLD_UGM3;
  bool clean = rd.coIn < CO_THRESHOLD_PPM * CLEAN_HYSTERESIS &&
               rd.pmIn < PM_THRESHOLD_UGM3 * CLEAN_HYSTERESIS;

  if (mode == MODE_MEASURING && inMode >= MEASURE_SETTLE_MS && polluted) setMode(MODE_FILTERING);
  else if (mode == MODE_FILTERING && inMode >= MIN_FILTER_MS && clean) setMode(MODE_MEASURING);
}

// ---------------- LoRa ----------------
static void sendPacket() {
  if (!loraOk) return;
  SensorPacket p = {};
  p.senderId = NODE_ID;
  p.receiverId = GATEWAY_ID;
  p.CO_ppm = rd.coIn;
  p.CO_ppm_2 = rd.coOut;
  p.dust = rd.pmIn;
  p.dust_2 = rd.pmOut;
  p.motor_flag = motorOk;
  p.motor_mode = mode;
  p.RPM = rpm;
  p.filter_flag = filterFlag;
  p.web_flag = false;
  p.mq7_flag = mq7FaultIn;
  p.mq7_flag_2 = mq7FaultOut;
  p.gp2y_flag = gp2yFaultIn;
  p.gp2y_flag_2 = gp2yFaultOut;

  // Binary struct, no string formatting (thesis 2.6.6d).
  LoRa.beginPacket();
  LoRa.write((const uint8_t*)&p, sizeof(p));
  bool ok = LoRa.endPacket();  // blocking: DIO0 is not wired
  Serial.printf("[LORA] tx %u bytes %s\n", (unsigned)sizeof(p), ok ? "ok" : "FAILED");
}

// ---------------- Serial commands ----------------
static void calibrateR0() {
  readSensors();
  if (!isfinite(rd.rsIn) || !isfinite(rd.rsOut)) {
    Serial.println("[CAL] invalid MQ-7 reading, check wiring");
    return;
  }
  mq7R0In = rd.rsIn / MQ7_CLEAN_AIR_RATIO;
  mq7R0Out = rd.rsOut / MQ7_CLEAN_AIR_RATIO;
  prefs.putFloat("r0in", mq7R0In);
  prefs.putFloat("r0out", mq7R0Out);
  Serial.printf("[CAL] R0 in=%.0f ohm out=%.0f ohm (saved)\n", mq7R0In, mq7R0Out);
}

static void handleSim(const String& line) {
  char name[16];
  float v;
  if (line == "sim off") {
    simCoIn = simCoOut = simPmIn = simPmOut = NAN;
    Serial.println("[TEST] simulation off");
    return;
  }
  if (sscanf(line.c_str(), "sim %15s %f", name, &v) != 2) {
    Serial.println("[TEST] usage: sim <co_in|co_out|pm_in|pm_out> <value> | sim off");
    return;
  }
  String n(name);
  if (n == "co_in") simCoIn = v;
  else if (n == "co_out") simCoOut = v;
  else if (n == "pm_in") simPmIn = v;
  else if (n == "pm_out") simPmOut = v;
  else { Serial.println("[TEST] unknown signal"); return; }
  Serial.printf("[TEST] %s forced to %.1f\n", name, v);
}

static void handleSerial() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line == "t") {
    startSelfTest();
  } else if (line == "r") {
    calibrateR0();
  } else if (line.startsWith("T")) {
    int y, mo, d, h, mi, s;
    if (sscanf(line.c_str() + 1, "%d-%d-%d %d:%d:%d", &y, &mo, &d, &h, &mi, &s) == 6 && rtcOk) {
      rtc.adjust(DateTime(y, mo, d, h, mi, s));
      Serial.println("[RTC] time set");
    } else {
      Serial.println("[RTC] usage: TYYYY-MM-DD HH:MM:SS (RTC must be present)");
    }
  } else if (line.startsWith("sim")) {
    handleSim(line);
  } else if (line == "fan m" || line == "fan f") {
    manualMode = true;
    setMode(line == "fan f" ? MODE_FILTERING : MODE_MEASURING);
    Serial.printf("[TEST] fan held in %s\n", modeName(mode));
  } else if (line == "fan auto") {
    manualMode = false;
    Serial.println("[TEST] fan back to automatic control");
  } else if (line == "kf on" || line == "kf off") {
    kfForControl = (line == "kf on");
    Serial.printf("[KF] control uses %s values\n", kfForControl ? "filtered" : "raw");
  } else if (line == "kf") {
    Serial.printf("[KF] control=%s  noise reduction (last %d samples): CO in %.0f%% out %.0f%%  PM in %.0f%% out %.0f%%\n",
                  kfForControl ? "filtered" : "raw", KF_STATS_N,
                  kfCoIn.noiseReduction(), kfCoOut.noiseReduction(),
                  kfPmIn.noiseReduction(), kfPmOut.noiseReduction());
  } else if (line == "?") {
    Serial.println("Commands: t | r | TYYYY-MM-DD HH:MM:SS | sim <co_in|co_out|pm_in|pm_out> <v> | "
                   "sim off | fan m | fan f | fan auto | kf on | kf off | kf");
  } else if (line.length()) {
    Serial.printf("[CMD] unknown '%s', type ? for help\n", line.c_str());
  }
}

static void printStatus() {
  char ts[20] = "no-rtc";
  if (rtcOk) {
    DateTime n = rtc.now();
    snprintf(ts, sizeof(ts), "%02d:%02d:%02d", n.hour(), n.minute(), n.second());
  }
  // Three short lines so the status fits a narrow Serial Monitor
  Serial.printf("[%s] %-9s duty=%.2f rpm=%lu motor=%s filter=%s\n",
                ts, modeName(mode), currentDuty, (unsigned long)rpm,
                motorOk ? "ok" : "FAULT", filterFlag ? "REPLACE" : "ok");
  Serial.printf("  CO in %.1f ppm (%.2fV)  out %.1f ppm (%.2fV)  eta %.0f%%\n",
                rd.coIn, rd.vCoIn, rd.coOut, rd.vCoOut, etaCo);
  Serial.printf("  PM in %.0f ug (%.2fV)  out %.0f ug (%.2fV)  eta %.0f%%\n",
                rd.pmIn, rd.vPmIn, rd.pmOut, rd.vPmOut, etaPm);
  Serial.printf("  KF CO %.1f/%.1f ppm  PM %.0f/%.0f ug  noise -%.0f%%/-%.0f%% (%s)\n",
                kfCoIn.x, kfCoOut.x, kfPmIn.x, kfPmOut.x,
                kfCoIn.noiseReduction(), kfPmIn.noiseReduction(), kfForControl ? "control" : "shadow");
}

// ---------------- Setup / loop ----------------
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\nSmart air filter node (ESP32)");

  // Dust sensor LEDs off (active LOW)
  pinMode(PIN_GP2Y_IN_LED, OUTPUT);
  pinMode(PIN_GP2Y_OUT_LED, OUTPUT);
  digitalWrite(PIN_GP2Y_IN_LED, HIGH);
  digitalWrite(PIN_GP2Y_OUT_LED, HIGH);
  analogSetAttenuation(ADC_11db);

  // Fan: LPWM low = fixed direction, RPWM = speed
  pinMode(PIN_LPWM, OUTPUT);
  digitalWrite(PIN_LPWM, LOW);
  ledcAttach(PIN_RPWM, PWM_FREQ_HZ, PWM_RES_BITS);
  ledcWrite(PIN_RPWM, 0);

  pinMode(PIN_HALL, INPUT);  // GPIO34 has no internal pull-up; KY-003 module provides it
  attachInterrupt(digitalPinToInterrupt(PIN_HALL), onHallPulse, FALLING);

  prefs.begin("airfilter", false);
  mq7R0In = prefs.getFloat("r0in", MQ7_R0_IN_DEFAULT);
  mq7R0Out = prefs.getFloat("r0out", MQ7_R0_OUT_DEFAULT);
  Serial.printf("MQ-7 R0 in=%.0f out=%.0f ohm\n", mq7R0In, mq7R0Out);

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  rtcOk = rtc.begin(&Wire);
  if (!rtcOk) {
    Serial.println("[RTC] DS1307 not found, scheduled self test disabled");
  } else if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    Serial.println("[RTC] was stopped, set to compile time");
  }

  SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);
  LoRa.setPins(PIN_LORA_NSS, PIN_LORA_RST, PIN_LORA_DIO0);
  for (int i = 0; i < 3 && !loraOk; i++) {
    loraOk = LoRa.begin(LORA_FREQUENCY_HZ);
    if (!loraOk) {
      Serial.println("[LORA] init failed, retrying");
      delay(1000);
    }
  }
  if (!loraOk) {
    Serial.println("[LORA] not found, running without radio");
  } else {
    LoRa.setSpreadingFactor(LORA_SPREADING);
    LoRa.setSignalBandwidth(LORA_BANDWIDTH_HZ);
    LoRa.setCodingRate4(LORA_CODING_RATE);
    LoRa.setSyncWord(LORA_SYNC_WORD);
    LoRa.setTxPower(LORA_TX_POWER_DBM);
    LoRa.enableCrc();
    Serial.println("[LORA] ready");
  }

  modeSince = lastRampMs = lastRpmMs = millis();
  targetDuty = DUTY_MEASURING;
}

void loop() {
  uint32_t now = millis();
  handleSerial();
  updateFanRamp();
  updateRpm();

  if (now - lastSensorMs >= SENSOR_PERIOD_MS) {
    lastSensorMs = now;
    readSensors();
    checkSchedule();
    if (mode == MODE_SELF_TEST) runSelfTest();
    else {
      checkFilter();
      decideMode();
    }
    printStatus();
  }

  if (txNow || millis() - lastTxMs >= LORA_TX_PERIOD_MS) {
    txNow = false;
    lastTxMs = millis();
    sendPacket();
  }
}
