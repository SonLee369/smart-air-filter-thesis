// config.h - filter column node (ESP32) pins, thresholds and timing.
// Values marked [thesis] come from the PDF; [tune] are defaults that the
// thesis does not give and should be adjusted to the real hardware.
#pragma once

// ================= Pins [thesis 2.3] =================
#define PIN_GP2Y_IN_LED     25   // inlet dust sensor LED drive
#define PIN_GP2Y_IN_OUT     33   // inlet dust sensor VOUT  (ADC1)
#define PIN_GP2Y_OUT_LED    14   // outlet dust sensor LED drive
#define PIN_GP2Y_OUT_OUT    32   // outlet dust sensor VOUT (ADC1)
#define PIN_MQ7_IN          4    // inlet CO sensor AOUT  (ADC2, fine because WiFi is off)
#define PIN_MQ7_OUT         35   // outlet CO sensor AOUT (ADC1)
#define PIN_HALL            34   // KY-003 data (input only, needs the module's pull-up)
#define PIN_RPWM            26   // BTS7960 RPWM (speed)
#define PIN_LPWM            27   // BTS7960 LPWM (held LOW, fixed direction)
#define PIN_LORA_NSS        5
#define PIN_LORA_MOSI       23
#define PIN_LORA_MISO       19
#define PIN_LORA_SCK        18
#define PIN_LORA_RST        -1   // not connected [thesis]
#define PIN_LORA_DIO0       -1   // not connected [thesis], TX uses blocking mode
#define PIN_I2C_SDA         21   // DS1307
#define PIN_I2C_SCL         22

// ================= Analog front end [tune] =================
// GP2Y and MQ-7 outputs swing up to 5 V; the ESP32 ADC tops out near 3.1 V.
// A divider Rtop (signal->pin) / Rbot (pin->GND) is required on each analog line.
// GAIN = (Rtop + Rbot) / Rbot.  Set to 1.0 only if you have no divider.
#define DIVIDER_RTOP_OHMS   33000.0f
#define DIVIDER_RBOT_OHMS   47000.0f
#define DIVIDER_GAIN        ((DIVIDER_RTOP_OHMS + DIVIDER_RBOT_OHMS) / DIVIDER_RBOT_OHMS)

// ================= GP2Y1010AU0F dust sensor =================
#define GP2Y_SAMPLE_DELAY_US  280    // sample 0.28 ms after LED on [thesis/datasheet]
#define GP2Y_PULSE_US         320    // LED on 0.32 ms           [thesis/datasheet]
#define GP2Y_PERIOD_US        10000  // one pulse every 10 ms     [thesis/datasheet]
#define GP2Y_SAMPLES          10     // pulses per reading, trimmed mean
#define GP2Y_UG_PER_VOLT      200.0f // 0.5 V per 0.1 mg/m3      [thesis]
#define GP2Y_IN_V_CLEAN       0.90f  // output with no dust, per sensor [tune: datasheet typ 0.9 V]
#define GP2Y_OUT_V_CLEAN      0.90f
#define GP2Y_V_MIN            0.10f  // below this the sensor is disconnected/dead
#define GP2Y_V_MAX            4.00f  // above this the output is saturated

// ================= MQ-7 CO sensor =================
#define MQ7_SAMPLES           20     // ADC samples per reading, trimmed mean
#define MQ7_VC                5.0f   // circuit supply
#define MQ7_RL_OHMS           10000.0f // load resistor on the module [tune: check yours, some are 1k]
// The divider sits in parallel with RL, so the effective load is RL || (Rtop+Rbot).
#define MQ7_RL_EFF_OHMS       (MQ7_RL_OHMS * (DIVIDER_RTOP_OHMS + DIVIDER_RBOT_OHMS) / \
                               (MQ7_RL_OHMS + DIVIDER_RTOP_OHMS + DIVIDER_RBOT_OHMS))
#define MQ7_CURVE_A           99.042f  // ppm = A * (Rs/R0)^B, datasheet CO curve fit
#define MQ7_CURVE_B           -1.518f
#define MQ7_CLEAN_AIR_RATIO   27.5f    // Rs/R0 in clean air, used by the 'r' calibration command
#define MQ7_R0_IN_DEFAULT     10000.0f // [tune] overwritten by calibration stored in NVS
#define MQ7_R0_OUT_DEFAULT    10000.0f
#define MQ7_V_MIN             0.05f
#define MQ7_V_MAX             4.90f

// ================= Valid ranges for sensor check [thesis 2.3.3] =================
#define CO_VALID_MAX_PPM      2000.0f  // MQ-7 range 20-2000 ppm
#define PM_VALID_MAX_UGM3     800.0f   // GP2Y range 0-0.8 mg/m3

// ================= Control thresholds [thesis 2.6.2] =================
#define CO_THRESHOLD_PPM      50.0f    // switch to FILTERING above this
#define PM_THRESHOLD_UGM3     35.0f
#define CLEAN_HYSTERESIS      0.8f     // [tune] return to MEASURING below 80 % of the thresholds
#define MEASURE_SETTLE_MS     10000UL  // [tune] airflow settle time before deciding in MEASURING
#define MIN_FILTER_MS         60000UL  // [tune] minimum FILTERING time, avoids rapid on/off

// ================= Fan / PWM =================
#define PWM_FREQ_HZ           20000    // BTS7960 supports up to 25 kHz, 20 kHz is inaudible
#define PWM_RES_BITS          10
#define DUTY_MEASURING        0.22f    // [tune] -> ~1320 RPM expected (thesis Fig 3.12)
#define DUTY_FILTERING        0.52f    // [tune] -> ~3120 RPM expected (thesis Fig 3.11)
#define DUTY_RAMP_PER_S       0.20f    // [tune] soft ramp so speed changes are smooth

// ================= RPM / motor check [thesis 2.6.3] =================
#define RPM_WINDOW_MS         1000UL   // count pulses for 1 s, RPM = 60 * N
#define HALL_MIN_INTERVAL_US  3000UL   // debounce: ignore pulses closer than this (max 20000 RPM)
#define RPM_PER_DUTY          6000.0f  // expected RPM = duty * 6000
#define RPM_SETTLE_MS         5000UL   // skip the check this long after a speed change
#define RPM_TOLERANCE         0.35f    // [tune] allowed relative error
#define RPM_FAULT_COUNT       3        // consecutive bad/good windows to set/clear the fault

// ================= Filter check [thesis 2.6.4] =================
#define FILTER_MIN_EFFICIENCY 50.0f    // %, below this the filter needs replacing
#define FILTER_EVAL_MIN_PM    10.0f    // [tune] only evaluate when inlet has enough dust
#define FILTER_EVAL_MIN_CO    5.0f     // [tune] only evaluate when inlet has enough CO
#define FILTER_BAD_COUNT      30       // [tune] consecutive evaluations (~60 s) to set/clear

// ================= Sensor self test [thesis 2.6.5] =================
#define SELF_TEST_HOUR        0        // run at 00:00 (RTC)
#define SELF_TEST_SETTLE_MS   30000UL  // [tune] fan at measuring power before sampling
#define SELF_TEST_WINDOW_MS   10000UL  // [tune] average readings over this window

// ================= Timing =================
#define SENSOR_PERIOD_MS      2000UL   // [tune] sensor sampling period
#define LORA_TX_PERIOD_MS     5000UL   // [tune] periodic uplink

// ================= AI feature F1: Kalman filter [tune] =================
// Variances in the channel's unit squared. R = sensor noise, Q = how fast the true
// value may move between 2 s samples. Larger Q/R ratio = faster, noisier output.
#define KF_PM_Q               4.0f     // (ug/m3)^2
#define KF_PM_R               100.0f   // GP2Y noise ~ 10 ug/m3 std
#define KF_CO_Q               0.25f    // ppm^2
#define KF_CO_R               4.0f     // MQ-7 noise ~ 2 ppm std
#define KF_GATE_SIGMA         4.0f     // innovations beyond 4 sigma are down-weighted
#define KF_USE_FOR_CONTROL    false    // default: control uses raw values (baseline behaviour)
