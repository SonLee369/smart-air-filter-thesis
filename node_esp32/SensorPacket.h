// SensorPacket.h - shared LoRa protocol between the filter column node and the gateway.
// Based on section 2.6.6 of the baseline-thesis. This file must be IDENTICAL in
// node_esp32/ and gateway_esp32/ (Arduino sketches cannot include files
// outside their own folder, so it is duplicated on purpose).
#pragma once
#include <stdint.h>

// ---------------- Radio settings (must match on both sides) ----------------
#define LORA_FREQUENCY_HZ   433E6   // Ra-02 / SX1278, 433 MHz ISM band (thesis 2.3.5)
#define LORA_SPREADING      7       // SF7: thesis does not specify, short airtime
#define LORA_BANDWIDTH_HZ   125E3
#define LORA_CODING_RATE    5       // 4/5
#define LORA_SYNC_WORD      0x53    // private network id, filters neighbouring LoRa systems
#define LORA_TX_POWER_DBM   17

// ---------------- Network ids ----------------
#define NODE_ID             0x01    // this filter column
#define GATEWAY_ID          0x64    // gateway (receiverId must match, thesis 2.6.7)

// ---------------- motor_mode values ----------------
enum MotorMode : uint8_t {
  MODE_MEASURING = 0,   // low fan power, sampling ambient air
  MODE_FILTERING = 1,   // high fan power, pulling air through the filters
  MODE_SELF_TEST = 2,   // scheduled sensor check (fan at measuring power)
};

// Field list and order exactly as in the thesis. Packed so the binary layout is
// identical on any compiler/target (both boards are little-endian).
// Note: the thesis counts 8 bools (31 bytes) but the struct only has 7 -> 30 bytes.
struct __attribute__((packed)) SensorPacket {
  uint8_t  senderId;     // id of the sending node
  uint8_t  receiverId;   // id of the gateway
  float    CO_ppm;       // CO at inlet (before filter), ppm
  float    CO_ppm_2;     // CO at outlet (after filter), ppm
  float    dust;         // dust at inlet, ug/m3
  float    dust_2;       // dust at outlet, ug/m3
  bool     motor_flag;   // true = fan running at the expected speed, false = stalled/abnormal
  uint8_t  motor_mode;   // MotorMode
  uint32_t RPM;          // measured fan speed (unsigned long in the thesis, same 4 bytes)
  bool     filter_flag;  // true = filter efficiency too low, replace filter
  bool     web_flag;     // reserved for web control (not used in the baseline, always false)
  bool     mq7_flag;     // true = inlet CO sensor fault
  bool     mq7_flag_2;   // true = outlet CO sensor fault
  bool     gp2y_flag;    // true = inlet dust sensor fault
  bool     gp2y_flag_2;  // true = outlet dust sensor fault
};

static_assert(sizeof(SensorPacket) == 30, "SensorPacket layout changed");
