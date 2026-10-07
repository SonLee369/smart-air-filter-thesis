# Smart Air Filter Column — Baseline

A reproduction of the system described in the thesis *"Cột lọc bụi thông minh"* (Nhóm đồ án 53), chapter 2.

```
 [Filter column node: ESP32]  --LoRa 433 MHz-->  [Gateway: ESP32]    --WiFi-->  Web dashboard
  2x GP2Y1010 dust (in/out)                       validates SensorPacket          http://<gateway-ip>/
  2x MQ-7 CO (in/out)                             keeps latest data in RAM        polls /get-data (JSON)
  KY-003 Hall (RPM), BTS7960 fan                  serves index.html (LittleFS)
  DS1307 RTC, LoRa Ra-02
```

| Folder | Content |
|---|---|
| `node_esp32/` | Node firmware: sensors, MEASURING/FILTERING control, motor, filter and sensor checks, LoRa TX |
| `gateway_esp32/` | Gateway firmware: LoRa RX, web server, `data/index.html` dashboard |
| `*/SensorPacket.h` | Shared binary packet and radio settings. **Must be identical in both folders.** |
| `tools/upload_fs.sh` | Builds and flashes the LittleFS image (dashboard) to the gateway |

## 1. Wiring

### Node (ESP32-WROOM DevKit, 30-pin) — thesis section 2.3

| Module | Pin | ESP32 |
|---|---|---|
| GP2Y1010 inlet | LED / VOUT | GPIO25 / GPIO33* |
| GP2Y1010 outlet | LED / VOUT | GPIO14 / GPIO32* |
| MQ-7 inlet | AOUT | GPIO4* |
| MQ-7 outlet | AOUT | GPIO35* |
| KY-003 Hall | S | GPIO34 |
| BTS7960 | RPWM / LPWM | GPIO26 / GPIO27 |
| BTS7960 | R_EN, L_EN, VCC | 3.3 V |
| BTS7960 | B+ / B- | 12 V PSU + / − |
| LoRa Ra-02 | NSS / MOSI / MISO / SCK | GPIO5 / 23 / 19 / 18 |
| LoRa Ra-02 | RST, DIO0 | not connected |
| DS1307 | SDA / SCL | GPIO21 / GPIO22 |

\* through a voltage divider (see below). Every GND is shared: ESP32, 5 V adapter, and 12 V PSU minus.

Each GP2Y1010 also needs the datasheet RC network: a 150 Ω resistor from 5 V to V-LED, and a 220 µF capacitor from V-LED to LED-GND.

### Gateway (ESP32-WROOM DevKit, 38-pin)

The thesis uses an ESP8266-12E for the gateway (table 2.3). This build runs the gateway on an ESP32, using the same SPI pins as the node.

| LoRa Ra-02 | NSS | MOSI | MISO | SCK | RST | DIO0 | 3.3V / GND |
|---|---|---|---|---|---|---|---|
| ESP32 | GPIO5 | GPIO23 | GPIO19 | GPIO18 | GPIO14 | GPIO26 | 3V3 / GND |

## 2. Hardware fixes compared to the thesis (important)

The thesis wiring has several electrical problems. The firmware assumes the fixes below.

1. **5 V analog signals into a 3.3 V ADC.** The GP2Y1010 and MQ-7 outputs go up to 5 V, but the ESP32 ADC saturates around 3.1 V. Over 3.6 V can also damage the pin. Fit a divider on each of the 4 analog lines: **33 kΩ** from the sensor output to the pin, and **47 kΩ** from the pin to GND. The firmware undoes the divider using `DIVIDER_GAIN` in `config.h`. The MQ-7 calculation also accounts for the divider sitting in parallel with the module's load resistor.
2. **KY-003 at 5 V on GPIO34.** The module's pull-up drives the pin to 5 V. Power the KY-003 from **3.3 V**; it works fine at that voltage.
3. **DS1307 at 3.3 V.** The DS1307 needs 4.5–5.5 V. Below about 3.75 V it switches to battery mode and stops answering on I2C, so it will not work as the thesis wires it. Power it from **5 V**. The module's I2C pull-ups then pull SDA and SCL to 5 V, so either remove its pull-up resistors (the ESP32 side can use 4.7 kΩ to 3.3 V) or add an I2C level shifter. Without the RTC, the node still runs, but the midnight self-test is disabled.
4. **Packet size.** The thesis says 31 bytes, but the struct has 7 bools, so it is 30 bytes. It is declared `packed` so the node and the gateway agree on the layout.
5. **MQ-7 heater.** The datasheet calls for a 5 V / 1.4 V heater cycle. Like the thesis, this baseline runs the module board at a constant 5 V. Treat the ppm values as indicative, and calibrate R0 as described in section 4.

## 3. Build and flash

The toolchain is already installed: ESP32 core 3.3.12, LoRa 0.8.0 (sandeepmistry) and RTClib 2.1.4 (Adafruit).

**Node:**
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 node_esp32
```
```bash
arduino-cli upload --fqbn esp32:esp32:esp32 -p <node-port> node_esp32
```

**Gateway:**

1. Copy `gateway_esp32/secrets.h.example` to `gateway_esp32/secrets.h`, then put your WiFi SSID and password in it.
2. Build and flash:
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 gateway_esp32
```
```bash
arduino-cli upload --fqbn esp32:esp32:esp32 -p <gateway-port> gateway_esp32
```
```bash
tools/upload_fs.sh <gateway-port>
```
The last command uploads the dashboard. In Arduino IDE 2 you can use the *arduino-littlefs-upload* plugin instead. Keep the default *Partition Scheme: Default 4MB with spiffs* setting.

Open the Serial Monitor at 115200 baud. The gateway prints `dashboard at http://<ip>`; open that address in a browser on the same WiFi.

## 4. Calibration and node serial commands

| Command | Action |
|---|---|
| `r` | MQ-7 R0 calibration. Run it in clean air after at least 10 minutes of warm-up (48 h burn-in is best). Stores R0 in NVS. |
| `t` | Run the sensor self-test now instead of waiting for 00:00 |
| `T2026-10-05 21:30:00` | Set the DS1307 time |

Dust: with the column in clean air, read the `PM ... (x.xxV/x.xxV)` voltages in the status line. Put them in `GP2Y_IN_V_CLEAN` and `GP2Y_OUT_V_CLEAN`.

## 5. Behaviour (thesis 2.6) and tunable values (`node_esp32/config.h`)

| Function | Rule | Key settings |
|---|---|---|
| Phases | MEASURING → FILTERING when CO_in > 50 ppm **or** PM_in > 35 µg/m³ (decided after `MEASURE_SETTLE_MS`). FILTERING → MEASURING after at least `MIN_FILTER_MS` once both are below 80 % of the threshold. | `CO_THRESHOLD_PPM`, `PM_THRESHOLD_UGM3`, `CLEAN_HYSTERESIS` |
| Fan | BTS7960 RPWM at 20 kHz, soft ramp between phase duties | `DUTY_MEASURING` 0.22, `DUTY_FILTERING` 0.52, `DUTY_RAMP_PER_S` |
| RPM | KY-003 falling-edge interrupt, debounce, RPM = 60 × pulses per second | `HALL_MIN_INTERVAL_US` |
| Motor check | Expected RPM = duty × 6000. Fault after 3 s outside ±35 %. Skipped during ramps and for 5 s after. | `RPM_PER_DUTY`, `RPM_TOLERANCE` |
| Filter check | η = (in − out)/in. Flag "REPLACE" when η_PM or η_CO stays below 50 % (about 60 s) | `FILTER_*` |
| Sensor check | At 00:00 (RTC): fan at measuring power, 30 s settle, 10 s average. Fault if the output voltage is dead or saturated, CO > 2000 ppm or PM > 800 µg/m³ | `SELF_TEST_*`, `*_V_MIN/MAX` |
| LoRa | 433 MHz, SF7, 125 kHz, CR 4/5, sync word 0x53, CRC on. TX every 5 s and immediately on a phase or flag change | `SensorPacket.h` |

Set the fan duty cycles so the measured RPM matches duty × 6000 on your motor. The defaults give about 1320 and 3120 RPM, the values in thesis Figures 3.11 and 3.12. If your motor differs, change `RPM_PER_DUTY`.

`web_flag` is kept in the packet as in the thesis but is not used; the link is uplink only. The airflow figure on the dashboard uses thesis eq. 3–5. Set `FAN_RADIUS_M` and `INLET_AREA_M2` in `gateway_esp32/config.h` to your real fan and column.

## 6. Bring-up checklist

1. Flash the gateway. The Serial Monitor should show `[LORA] listening` and `[WIFI] connected, dashboard at http://...`.
2. Flash the node. The Serial Monitor should print a status line every 2 s and `[LORA] tx 30 bytes ok`.
3. The gateway should print `[LORA] node 1 MEASURING ...`, and the dashboard should update every 2 s.
4. Hold a smoke or dust source at the inlet. The node should switch to FILTERING (`[MODE] MEASURING -> FILTERING`), the fan should ramp up, and RPM should rise to about 3100.
5. Stop the fan blade by hand (carefully). After about 3 s the motor card should show **ERROR**.
6. Send `t`. After about 40 s, `[SELFTEST] done ...` should appear. Unplug one sensor and repeat; its card should show **WARNING!**

## 7. Figures

All diagrams are in [`docs/figures/`](docs/figures/). To redraw them after a change, edit and run `python3 docs/figures/make_figures.py`.

| Figure | Shows |
|---|---|
| [Fig 1](docs/figures/fig1_system_architecture.svg) | System architecture: node → LoRa → gateway → WiFi → dashboard |
| [Fig 2](docs/figures/fig2_node_block_diagram.svg) | Node block diagram |
| [Fig 3](docs/figures/fig3_node_wiring.svg) | Node wiring on the 30-pin ESP32, with the dividers and module power |
| [Fig 4](docs/figures/fig4_gateway_wiring.svg) | Gateway wiring on the 38-pin ESP32 with the LoRa Ra-02 |
| [Fig 5](docs/figures/fig5_airflow_principle.svg) | Airflow path, the two operating phases, efficiency formulas |
| [Fig 6](docs/figures/fig6_state_machine.svg) | Control state machine: MEASURING / FILTERING / SELF_TEST |
| [Fig 7](docs/figures/fig7_firmware_flowchart.svg) | Node firmware flowchart: setup, loop and Hall interrupt |
| [Fig 8](docs/figures/fig8_sensor_packet.svg) | SensorPacket byte layout (30 bytes) |
| [Fig 9](docs/figures/fig9_power_distribution.svg) | Power distribution, rails and 5 V current budget |

![System architecture](docs/figures/fig1_system_architecture.svg)
![Node wiring](docs/figures/fig3_node_wiring.svg)

## 8. Thesis figures (Group 63 AI thesis)

The figures for the AI thesis are in [`docs/thesis_figures/`](docs/thesis_figures/). To redraw them, run `python3 docs/thesis_figures/make_thesis_figures.py`. That script reuses the drawing helpers from `docs/figures/make_figures.py`.

| Figure | Shows |
|---|---|
| [T1](docs/thesis_figures/t1_system_architecture_v2.svg) | System architecture v2: AI on the node, gateway, training, models sent back over the air |
| [T2](docs/thesis_figures/t2_node_hardware_v2.svg) | Node hardware v2: PMS5003 on UART2, SHT31/INA219/SDP810 on I²C |
| [T3](docs/thesis_figures/t3_data_pipeline.svg) | Data pipeline from a sensor sample to a model running on the node |
| [T4](docs/thesis_figures/t4_closed_loop_control.svg) | Closed-loop AI control with a safety supervisor |
| [T5](docs/thesis_figures/t5_mpc_receding_horizon.svg) | MPC receding horizon (concept) |
| [T6](docs/thesis_figures/t6_rl_training_pipeline.svg) | RL training in a data-driven simulator, then deployment |
| [T7](docs/thesis_figures/t7_firmware_v2_architecture.svg) | Firmware v2: FreeRTOS tasks on the two cores |
| [T8](docs/thesis_figures/t8_experiment_design.svg) | Chamber trials and field rotation schedule |
| [T9](docs/thesis_figures/t9_filter_life_concept.svg) | Filter-life prediction: concept sketch, no data |
| [T10](docs/thesis_figures/t10_energy_tradeoff_concept.svg) | Energy vs cleanliness trade-off: concept sketch, no data |
