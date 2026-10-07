# Generates docs/thesis_figures/*.svg for the Group 63 AI thesis.
# Reuses the drawing helpers and style of docs/figures/make_figures.py.
# T9 and T10 are concept sketches (no data); replace them with real plots in month 5.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "figures"))
import make_figures as mf  # noqa: E402
from make_figures import (K, COLORS, MUTED, INK, LINE, text, rect, box, line, path,  # noqa: E402
                          diamond, board, legend)

mf.OUT = HERE
svg = mf.svg


def note(b, x, y, s, size=11, color=MUTED, anchor="start", weight=400):
    b.append(text(x, y, s, size, weight, anchor, color))


# ---------------------------------------------------------------- T1
def t1():
    b = []
    b.append(rect(30, 70, 520, 440, "note"))
    note(b, 50, 96, "Filter column node · ESP32 (30-pin)", 14, INK, weight=700)
    b.append(box(50, 112, 480, 110, "dust", "Sensors",
                 ["GP2Y1010 ×2 + PMS5003 reference (PM2.5)", "MQ-7 ×2 (CO in / out)",
                  "SHT31 (T, RH) · ΔP sensor across the filter", "INA219 (fan power) · KY-003 Hall (RPM)"]))
    b.append(box(50, 252, 480, 120, "mcu", "Edge AI on the ESP32 (TFLite Micro / emlearn)",
                 ["Calibration + Kalman filter (C2)", "Forecast PM2.5 / CO, +1 … +15 min (C3)",
                  "MPC or RL policy → fan duty u every 10 s (C4)", "Fallback: baseline threshold controller"]))
    b.append(box(50, 402, 230, 84, "act", "Fan drive", ["BTS7960, PWM 20 kHz", "duty u ∈ [0, 1]"]))
    b.append(box(300, 402, 230, 84, "rtc", "Local log", ["SD card, 1 s samples", "survives LoRa loss"]))
    b.append(line(290, 224, 290, 250, "orange"))
    note(b, 298, 242, "raw readings")
    b.append(line(165, 374, 165, 400, "blue"))
    note(b, 173, 392, "u")
    b.append(line(415, 374, 415, 400, "gray"))
    b.append(path("M50,444 L40,444 L40,167 L48,167", "purple", dash=True))
    b.append(rect(640, 70, 330, 440, "note"))
    note(b, 660, 96, "Gateway and server", 14, INK, weight=700)
    b.append(box(660, 112, 290, 96, "gw", "Gateway (ESP32, 38-pin)",
                 ["LoRa RX + packet validation", "Downlink: settings, model (OTA)"]))
    b.append(box(660, 238, 290, 120, "web", "Data store + training (PC)",
                 ["Season-long dataset (C1)", "Forecast, plant model, RL", "int8 export (C5) · filter life (C6)"]))
    b.append(box(660, 388, 290, 98, "web", "Web dashboard",
                 ["Live PM, CO, energy, filter life", "Controller A / B / C / D select"]))
    b.append(line(805, 210, 805, 236, "green"))
    b.append(line(805, 360, 805, 386, "purple"))
    b.append(path("M532,290 L590,290 L590,150 L658,150", "teal", sw=2))
    b.append(path("M658,186 L606,186 L606,334 L532,334", "green", dash=True, sw=1.8))
    note(b, 598, 62, "LoRa 433 MHz", 12, COLORS["teal"], "middle", 700)
    y = 540
    b.append(line(40, y, 80, y, "teal", sw=2))
    note(b, 88, y + 4, "data uplink (packet v2, every 10 s)")
    b.append(line(340, y, 380, y, "green", dash=True))
    note(b, 388, y + 4, "settings and model downlink (OTA)")
    b.append(line(640, y, 680, y, "purple", dash=True))
    note(b, 688, y + 4, "airflow changes what the sensors read")
    svg("t1_system_architecture_v2.svg", 1000, 565, "T1 — System architecture v2: AI closes the loop on the node", b)


# ---------------------------------------------------------------- T2
def t2():
    b = []
    left = ["EN", "VP 36", "VN 39", "D34", "D35", "D32", "D33", "D25", "D26", "D27", "D14", "D12", "D13", "GND", "VIN"]
    right = ["D23", "D22", "TX0", "RX0", "D21", "D19", "D18", "D5", "TX2", "RX2", "D4", "D2", "D15", "GND", "3V3"]
    ul = {"D34": ("hall", "KY-003  S  (Hall, interrupt)", False),
          "D35": ("co", "MQ-7 outlet  AOUT", True),
          "D32": ("dust", "GP2Y outlet  VOUT", True),
          "D33": ("dust", "GP2Y inlet  VOUT", True),
          "D25": ("dust", "GP2Y inlet  LED (pulse)", False),
          "D26": ("act", "BTS7960  RPWM (speed)", False),
          "D27": ("act", "BTS7960  LPWM (held LOW)", False),
          "D14": ("dust", "GP2Y outlet  LED (pulse)", False),
          "GND": ("gnd", "Common GND (all modules, PSU −)", False),
          "VIN": ("pwr", "5 V adapter  +", False)}
    ur = {"D23": ("lora", "Ra-02  MOSI", False),
          "D22": ("rtc", "I²C SCL: DS1307, SHT31, INA219, ΔP", False),
          "D21": ("rtc", "I²C SDA: DS1307, SHT31, INA219, ΔP", False),
          "D19": ("lora", "Ra-02  MISO", False),
          "D18": ("lora", "Ra-02  SCK", False),
          "D5": ("lora", "Ra-02  NSS (CS)", False),
          "TX2": ("web", "NEW  PMS5003  RX (UART2, GPIO17)", False),
          "RX2": ("web", "NEW  PMS5003  TX (UART2, GPIO16)", False),
          "D4": ("co", "MQ-7 inlet  AOUT", True),
          "GND": ("gnd", "Common GND", False),
          "3V3": ("pwr", "Ra-02, KY-003, BTS7960 logic, I²C sensors", False)}
    legend(b, 50, 70, [("dust", "GP2Y1010"), ("co", "MQ-7"), ("hall", "KY-003"), ("act", "BTS7960"),
                       ("lora", "LoRa Ra-02"), ("rtc", "I²C bus"), ("web", "New: PMS5003"), ("pwr", "Power")])
    bottom = board(b, 500, 150, 30, 180, left, right, "ESP32 DevKit V1 (30-pin)", ul, ur, tag_w=290, gap=130)
    py = bottom + 50
    b.append(rect(40, py, 540, 190, "note"))
    note(b, 60, py + 26, "I²C bus (GPIO21 / GPIO22, shared)", 13, INK, weight=700)
    rows = [("DS1307 RTC", "0x68", "5 V supply, pull-ups removed"),
            ("SHT31 temperature / humidity", "0x44", "3.3 V"),
            ("INA219 power monitor", "0x40", "in series with the fan's 12 V line"),
            ("SDP810 differential pressure", "0x25", "tubes before / after the filter")]
    note(b, 60, py + 52, "Device", 11.5, INK, weight=700)
    note(b, 300, py + 52, "Address", 11.5, INK, weight=700)
    note(b, 370, py + 52, "Note", 11.5, INK, weight=700)
    for i, (d, a, n) in enumerate(rows):
        yy = py + 76 + i * 24
        note(b, 60, yy, d, 11.5)
        note(b, 300, yy, a, 11.5, INK, weight=600)
        note(b, 370, yy, n, 11.5)
    b.append(rect(620, py, 520, 190, "warn"))
    note(b, 640, py + 26, "Changes from the baseline wiring", 13, COLORS["orange"], weight=700)
    for i, s in enumerate(["PMS5003: 5 V supply, 3.3 V UART logic → connects directly to GPIO16/17",
                           "INA219: high side between 12 V PSU + and BTS7960 B+ (check fan current",
                           "    stays under the 3.2 A shunt limit, else change the shunt)",
                           "SDP810: I²C at 3.3 V; route both tubes away from the fan outlet",
                           "Check every I²C address is unique before soldering (i2c scan)",
                           "Dividers (÷ 33k / 47k) stay on the four analog lines"]):
        note(b, 640, py + 54 + i * 21, s, 11.5)
    svg("t2_node_hardware_v2.svg", 1180, py + 215, "T2 — Node hardware v2: new sensors on UART2 and the I²C bus", b)


# ---------------------------------------------------------------- T3
def t3():
    b = []
    w, h = 190, 84
    row1 = [(40, "dust", "Node sampling", ["all sensors every 1 s", "duty, RPM, power"]),
            (270, "rtc", "SD card raw log", ["full-rate CSV", "never deleted"]),
            (500, "lora", "LoRa packet v2", ["10 s summary", "+ sequence number"]),
            (730, "gw", "Gateway", ["validate, timestamp", "forward over WiFi"]),
            (960, "web", "Database (PC)", ["SQLite / InfluxDB", "daily backup"])]
    y1 = 96
    for x, k, t, ls in row1:
        b.append(box(x, y1, w, h, k, t, ls))
    for i in range(4):
        b.append(line(row1[i][0] + w + 2, y1 + h / 2, row1[i + 1][0] - 2, y1 + h / 2, "gray"))
    b.append(path(f"M365,{y1 - 2} L365,{y1 - 22} L1055,{y1 - 22} L1055,{y1 - 2}", "gray", dash=True))
    note(b, 710, y1 - 28, "SD card copied weekly to fill LoRa gaps", 11, MUTED, "middle")
    y2 = 260
    row2 = [(960, "web", "Clean + align", ["resample to 10 s", "outliers, gaps, flags"]),
            (730, "web", "Features", ["windows 10–30 min", "time of day, RH, T"]),
            (500, "mcu", "Train + validate", ["time-based split", "no future leakage"]),
            (270, "mcu", "Quantise int8", ["test on ESP32:", "latency, RAM, accuracy"]),
            (40, "gw", "OTA model update", ["gateway → node", "A/B slot, rollback"])]
    for x, k, t, ls in row2:
        b.append(box(x, y2, w, h, k, t, ls))
    b.append(line(1055, y1 + h + 2, 1055, y2 - 2, "gray"))
    for i in range(4):
        b.append(line(row2[i][0] - 2, y2 + h / 2, row2[i + 1][0] + w + 2, y2 + h / 2, "gray"))
    b.append(path(f"M135,{y2} L135,{y1 + h + 2}", "green", sw=2))
    note(b, 143, 212, "new model runs on the node", 11, COLORS["green"])
    b.append(box(960, 400, 190, 70, "note", "Public dataset (C1)", ["README, licence, DOI"]))
    b.append(line(1055, y2 + h + 2, 1055, 398, "gray", dash=True))
    b.append(box(500, 400, 190, 70, "note", "Experiment log", ["controller, block, site"]))
    b.append(line(595, 398, 595, y2 + h + 2, "gray", dash=True))
    svg("t3_data_pipeline.svg", 1190, 495, "T3 — Data pipeline: from sensor sample to model on the node", b)


# ---------------------------------------------------------------- T4
def t4():
    b = []
    yA, yB = 170, 380
    b.append(box(30, yA - 45, 200, 90, "note", "Objective J", ["exposure + λ·energy", "+ μ·switching"]))
    b.append(box(290, yA - 50, 210, 100, "mcu", "Controller", ["MPC (learned model)", "or RL policy"]))
    b.append(box(560, yA - 50, 210, 100, "warn", "Safety supervisor", ["bounds, rate limit", "fallback to threshold"]))
    b.append(box(830, yA - 45, 180, 90, "act", "Fan + BTS7960", ["PWM duty u"]))
    b.append(box(1070, yA - 55, 210, 110, "dust", "Plant", ["filter column +", "local air near it"]))
    b.append(line(232, yA, 288, yA, "gray"))
    b.append(line(502, yA, 558, yA, "blue", sw=2))
    note(b, 530, yA - 10, "u*", 12, COLORS["blue"], "middle", 700)
    b.append(line(772, yA, 828, yA, "red", sw=2))
    note(b, 800, yA - 10, "u", 12, COLORS["red"], "middle", 700)
    b.append(line(1012, yA, 1068, yA, "red", sw=2))
    note(b, 1040, yA - 10, "airflow", 11, MUTED, "middle")
    b.append(box(1070, 30, 210, 50, "note", "Disturbance d", ["traffic, wind, RH"]))
    b.append(line(1175, 82, 1175, yA - 57, "gray"))
    # feedback row
    b.append(box(1070, yB - 45, 210, 90, "dust", "Sensors", ["PM, CO, RPM, power,", "T, RH, ΔP"]))
    b.append(box(780, yB - 45, 220, 90, "mcu", "Calibration + Kalman", ["state estimate x̂"]))
    b.append(box(480, yB - 45, 230, 90, "mcu", "Forecaster", ["ŷ(t+1 … t+H)"]))
    b.append(line(1175, yA + 57, 1175, yB - 47, "orange", sw=2))
    note(b, 1183, (yA + yB) / 2, "y", 12, COLORS["orange"], weight=700)
    b.append(line(1068, yB, 1002, yB, "orange"))
    b.append(line(778, yB, 712, yB, "blue"))
    note(b, 745, yB - 10, "x̂", 12, COLORS["blue"], "middle", 700)
    b.append(path(f"M478,{yB} L395,{yB} L395,{yA + 52}", "blue", sw=2))
    note(b, 403, yB - 60, "forecast + state", 11, COLORS["blue"])
    b.append(path(f"M890,{yB - 47} L890,{yA + 120} L665,{yA + 120} L665,{yA + 52}", "gray", dash=True))
    note(b, 672, yA + 112, "measured RPM / power: supervisor checks the fan", 11)
    b.append(rect(30, 460, 1250, 50, "note"))
    note(b, 655, 490, "Every 10 s: estimate the state, forecast, choose u*, check it, apply u. "
         "If the AI output is invalid or late, the supervisor falls back to the baseline thresholds.", 12, INK, "middle")
    svg("t4_closed_loop_control.svg", 1310, 530, "T4 — Closed-loop AI control with a safety supervisor", b)


# ---------------------------------------------------------------- T5
def t5():
    b = []
    x0, x1, xn, yt, yb = 90, 1010, 520, 90, 330
    b.append(f'<line x1="{x0}" y1="{yb}" x2="{x1}" y2="{yb}" stroke="{LINE}" stroke-width="1.4"/>')
    b.append(f'<line x1="{x0}" y1="{yb}" x2="{x0}" y2="{yt}" stroke="{LINE}" stroke-width="1.4"/>')
    note(b, 60, 210, "PM near the column", 12, INK, "middle", 600)
    b[-1] = b[-1].replace("<text ", '<text transform="rotate(-90 60 210)" ')
    note(b, x1 + 8, yb + 4, "time", 12, INK, "start", 600)
    b.append(f'<line x1="{xn}" y1="{yt - 10}" x2="{xn}" y2="{yb + 160}" stroke="{COLORS["blue"]}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    note(b, xn, yt - 16, "now (t)", 12, COLORS["blue"], "middle", 700)
    b.append(path(f"M{x0},250 C150,230 190,270 240,240 S330,190 380,215 S470,180 {xn},175", "gray", arrow=False, sw=2.4))
    note(b, 300, yt + 12, "measured (past)", 11.5, MUTED, "middle")
    cands = [("red", "M{0},175 C580,165 640,150 720,145 S900,140 1000,138", "u low: PM keeps rising"),
             ("amber", "M{0},175 C580,180 640,195 720,205 S900,215 1000,220", "u medium"),
             ("green", "M{0},175 C580,195 640,235 720,260 S900,280 1000,285", "u high: lowest PM, most energy")]
    for i, (c, d, lab) in enumerate(cands):
        b.append(path(d.format(xn), c, arrow=False, dash=True, sw=2))
        yy = (138, 220, 285)[i]
        note(b, 1006, yy + 4, lab, 11.5, COLORS[c])
    b.append(f'<path d="M{xn},{yb + 8} L{xn},{yb + 14} L{x1 - 10},{yb + 14} L{x1 - 10},{yb + 8}" fill="none" stroke="{LINE}" stroke-width="1.2"/>')
    note(b, (xn + x1) / 2, yb + 46, "prediction horizon H (e.g. 5–10 steps of 10 s)", 11.5, MUTED, "middle")
    # duty panel
    py = 420
    b.append(f'<line x1="{x0}" y1="{py + 110}" x2="{x1}" y2="{py + 110}" stroke="{LINE}" stroke-width="1.4"/>')
    b.append(f'<line x1="{x0}" y1="{py + 110}" x2="{x0}" y2="{py}" stroke="{LINE}" stroke-width="1.4"/>')
    note(b, 60, py + 55, "duty u", 12, INK, "middle", 600)
    b[-1] = b[-1].replace("<text ", f'<text transform="rotate(-90 60 {py + 55})" ')
    b.append(path(f"M{x0},{py + 80} L300,{py + 80} L300,{py + 70} L{xn},{py + 70}", "gray", arrow=False, sw=2.2))
    steps = [(xn, 600, py + 40), (600, 680, py + 50), (680, 760, py + 55), (760, 840, py + 60), (840, 920, py + 60), (920, 1000, py + 65)]
    for i, (a, z, y) in enumerate(steps):
        col = COLORS["blue"] if i == 0 else "#93c5fd"
        b.append(f'<rect x="{a}" y="{y}" width="{z - a}" height="{py + 110 - y}" fill="{col}" fill-opacity="{0.55 if i == 0 else 0.25}" stroke="{COLORS["blue"]}" stroke-width="1"/>')
    note(b, xn + 8, py - 8, "apply only u(t), then repeat at t + 10 s", 12, COLORS["blue"], "start", 700)
    note(b, 800, py + 30, "rest of the chosen sequence (discarded)", 11, MUTED, "middle")
    b.append(rect(90, 560, 920, 56, "note"))
    note(b, 550, 584, "At each step: simulate every candidate duty sequence with the learned plant model, "
         "score it with J, keep the best.", 12, INK, "middle")
    note(b, 550, 604, "Concept sketch: curve shapes are illustrative, not measured data.", 11, MUTED, "middle")
    svg("t5_mpc_receding_horizon.svg", 1240, 635, "T5 — MPC with a learned model: receding-horizon choice of fan duty", b)


# ---------------------------------------------------------------- T6
def t6():
    b = []
    b.append(box(40, 90, 230, 90, "rtc", "Real data logs (C1)", ["inlet PM / CO series", "duty → outlet response"]))
    b.append(rect(330, 70, 520, 300, "note"))
    note(b, 350, 96, "Training loop (simulation)", 13, INK, weight=700)
    b.append(box(360, 115, 220, 100, "dust", "Simulator", ["learned plant model", "replays real inlet data", "+ noise, disturbances"]))
    b.append(box(610, 115, 210, 100, "mcu", "RL agent", ["DQN (discrete duty)", "PPO (continuous)"]))
    b.append(line(272, 135, 358, 150, "gray"))
    b.append(path("M582,145 L608,145", "blue", sw=2))
    note(b, 595, 108, "state sₜ", 11, COLORS["blue"], "middle", 600)
    b.append(path("M608,190 L582,190", "red", sw=2))
    note(b, 595, 232, "action aₜ = duty", 11, COLORS["red"], "middle", 600)
    b.append(box(360, 250, 460, 100, "warn", "Reward rₜ",
                 ["−(PM + α·CO) − λ·P(u) − μ·|Δu|", "same cost as MPC, so the two are comparable",
                  "+ penalty if a safety bound is hit"]))
    b.append(line(470, 217, 470, 248, "amber"))
    # deployment chain
    chain = [(900, "mcu", "Trained policy", ["best checkpoint"]),
             (900, "mcu", "Distil to small MLP", ["int8, < 50 KB"]),
             (900, "dust", "Chamber validation", ["vs MPC and threshold"]),
             (900, "gw", "Deploy on ESP32", ["behind the supervisor"])]
    for i, (x, k, t, ls) in enumerate(chain):
        y = 80 + i * 92
        b.append(box(x, y, 240, 68, k, t, ls))
        if i:
            b.append(line(1020, y - 22, 1020, y - 2, "gray"))
    b.append(path("M822,165 L860,165 L860,114 L898,114", "blue"))
    b.append(path("M900,310 L870,310 L870,410 L345,410 L345,180 L358,180", "gray", dash=True))
    note(b, 600, 428, "sim-to-real gap too large → recalibrate the simulator", 11, MUTED, "middle")
    b.append(line(715, 248, 715, 217, "amber"))
    note(b, 723, 236, "rₜ", 11, COLORS["amber"], weight=700)
    svg("t6_rl_training_pipeline.svg", 1180, 460, "T6 — RL training in a data-driven simulator, then deployment", b)


# ---------------------------------------------------------------- T7
def t7():
    b = []
    b.append(rect(30, 70, 500, 400, "note"))
    note(b, 50, 96, "Core 1 · real-time work", 13, INK, weight=700)
    tasks1 = [("Sensing task", "every 1 s", ["GP2Y pulses, MQ-7, PMS5003 (UART2)", "I²C: SHT31, INA219, ΔP, RTC"], "dust"),
              ("AI task", "every 10 s", ["calibrate → Kalman → forecast", "MPC search or RL policy → u*"], "mcu"),
              ("Control task", "every 50 ms", ["supervisor: bounds, rate limit", "PWM ramp on RPWM"], "act")]
    for i, (t, per, ls, k) in enumerate(tasks1):
        y = 112 + i * 116
        b.append(box(50, y, 460, 96, k, t, ls))
        note(b, 498, y + 22, per, 11, MUTED, "end", 600)
    b.append(rect(570, 70, 400, 400, "note"))
    note(b, 590, 96, "Core 0 · communication and storage", 13, INK, weight=700)
    tasks0 = [("LoRa task", "every 10 s", ["TX packet v2", "RX settings, model chunks"], "lora"),
              ("Logging task", "every 1 s", ["append CSV to SD card", "rotate files daily"], "rtc"),
              ("Model store", "on update", ["flash slots A / B", "verify CRC, roll back"], "gw")]
    for i, (t, per, ls, k) in enumerate(tasks0):
        y = 112 + i * 116
        b.append(box(590, y, 360, 96, k, t, ls))
        note(b, 938, y + 22, per, 11, MUTED, "end", 600)
    b.append(box(250, 510, 500, 84, "pwr", "Shared state (mutex)",
                 ["latest readings · ring buffer of 30 min · current u · flags"]))
    for x in (150, 280, 400):
        b.append(line(x, 472, x + (500 - x) * 0.2 if x < 300 else x, 508, "amber", both=True))
    for x in (700, 860):
        b.append(line(x, 472, x - 40, 508, "amber", both=True))
    b.append(box(30, 620, 300, 70, "hall", "Hall ISR (GPIO34)", ["count pulses → RPM"]))
    b.append(box(370, 620, 300, 70, "warn", "Watchdog", ["AI task late → fallback controller"]))
    b.append(box(710, 620, 260, 70, "rtc", "RTC schedule", ["00:00 sensor self-test"]))
    b.append(line(180, 618, 330, 596, "purple"))
    b.append(line(520, 618, 520, 596, "orange"))
    b.append(line(840, 618, 700, 596, "gray"))
    svg("t7_firmware_v2_architecture.svg", 1000, 715, "T7 — Firmware v2: FreeRTOS tasks on the two ESP32 cores", b)


# ---------------------------------------------------------------- T8
def t8():
    b = []
    note(b, 40, 72, "(a) Test chamber", 14, INK, weight=700)
    b.append(f'<rect x="40" y="90" width="480" height="300" rx="10" fill="#f8fafc" stroke="{LINE}" stroke-width="2.5"/>')
    note(b, 280, 380, "sealed box, volume V (measure and report)", 11, MUTED, "middle")
    b.append(box(70, 290, 120, 70, "act", "Smoke source", ["incense, fixed time"], size=11))
    b.append(box(70, 120, 120, 60, "plain", "Mixing fan", ["even concentration"], size=11))
    b.append(rect(270, 130, 110, 220, "mcu", rx=8))
    note(b, 325, 155, "Filter column", 12, COLORS["blue"], "middle", 700)
    note(b, 325, 175, "(under test)", 11, MUTED, "middle")
    b.append(line(240, 320, 268, 320, "red", sw=2.5))
    note(b, 236, 312, "inlet", 11, COLORS["red"], "end")
    b.append(line(325, 128, 325, 102, "green", sw=2.5))
    note(b, 333, 112, "outlet", 11, COLORS["green"])
    b.append(box(410, 220, 95, 70, "web", "PMS5003", ["chamber ref."], size=11))
    b.append(path("M190,325 C215,325 225,320 238,320", "red", dash=True))
    note(b, 60, 420, "≥ 10 trials per controller and smoke dose · log decay curves · same start concentration", 11.5)
    note(b, 600, 72, "(b) Field rotation schedule (example randomisation)", 14, INK, weight=700)
    ctrl = {"A": ("#9ca3af", "Threshold"), "B": ("#f59e0b", "PID / fuzzy"), "C": ("#2563eb", "MPC"),
            "D": ("#7c3aed", "RL"), "O": ("#e5e7eb", "Fan off")}
    days = [("Day 1", "CADOBACD"), ("Day 2", "BODCAOBA"), ("Day 3", "DCBAOCDB")]
    hours = ["06", "08", "10", "12", "14", "16", "18", "20", "22"]
    gx, gw = 660, 56
    for i, hh in enumerate(hours):
        note(b, gx + i * gw, 104, hh + ":00", 10.5, MUTED, "middle")
    for r, (dn, seq) in enumerate(days):
        y = 116 + r * 56
        note(b, 600, y + 30, dn, 12, INK, weight=600)
        for i, c in enumerate(seq):
            col, _ = ctrl[c]
            b.append(f'<rect x="{gx + i * gw}" y="{y}" width="{gw - 4}" height="44" rx="5" fill="{col}" fill-opacity="{0.35 if c != "O" else 1}" stroke="{col}" stroke-width="1.2"/>')
            note(b, gx + i * gw + (gw - 4) / 2, y + 27, c if c != "O" else "off", 12, INK, "middle", 700)
    for i, (c, (col, nm)) in enumerate(ctrl.items()):
        x = 600 + i * 120
        b.append(f'<rect x="{x}" y="300" width="14" height="14" rx="3" fill="{col}" fill-opacity="{0.35 if c != "O" else 1}" stroke="{col}"/>')
        note(b, x + 20, 312, (c + " · " if c != "O" else "") + nm, 11.5)
    note(b, 600, 350, "2-hour blocks, order shuffled daily so rush hours hit every controller", 11.5)
    note(b, 600, 370, "≥ 4 weeks (excluding Tết) · paired Wilcoxon tests against A · 95 % CIs", 11.5)
    note(b, 600, 390, "Sequences shown are an example; generate the real ones with a fixed random seed", 11.5)
    svg("t8_experiment_design.svg", 1140, 440, "T8 — Experiment design: chamber trials and field rotation", b)


# ---------------------------------------------------------------- T9
def t9():
    b = []
    x0, x1, y0, y1 = 100, 960, 90, 400
    b.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}" stroke-width="1.4"/>')
    b.append(f'<line x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}" stroke="{LINE}" stroke-width="1.4"/>')
    note(b, 530, y1 + 30, "days in service", 12, INK, "middle", 600)
    note(b, 60, 245, "filter efficiency η", 12, INK, "middle", 600)
    b[-1] = b[-1].replace("<text ", '<text transform="rotate(-90 60 245)" ')
    y50 = 300
    b.append(f'<line x1="{x0}" y1="{y50}" x2="{x1}" y2="{y50}" stroke="{COLORS["red"]}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    note(b, x0 - 8, y50 + 4, "50 %", 11.5, COLORS["red"], "end", 700)
    note(b, x1, y50 - 8, "baseline alarm level", 11, COLORS["red"], "end")
    pts = "M100,130 L130,138 L160,133 L190,146 L220,142 L250,155 L280,152 L310,166 L340,163 L370,176 L400,174 L430,186 L460,184 L490,197 L520,196"
    b.append(path(pts, "gray", arrow=False, sw=2.2))
    note(b, 300, 125, "daily η estimate (measured so far)", 11.5, MUTED, "middle")
    xn = 520
    b.append(f'<line x1="{xn}" y1="{y0}" x2="{xn}" y2="{y1}" stroke="{COLORS["blue"]}" stroke-width="1.4" stroke-dasharray="4 4"/>')
    note(b, xn, y0 - 8, "today", 12, COLORS["blue"], "middle", 700)
    b.append(f'<path d="M520,196 L860,300 L860,398 L520,196 Z" fill="{COLORS["blue"]}" fill-opacity="0.12" stroke="none"/>')
    b.append(f'<path d="M520,196 L860,349" fill="none" stroke="{COLORS["blue"]}" stroke-width="2" stroke-dasharray="7 5"/>')
    note(b, 700, 222, "forecast + uncertainty band", 11.5, COLORS["blue"], "middle")
    b.append(f'<line x1="751" y1="{y50}" x2="751" y2="{y1}" stroke="{COLORS["green"]}" stroke-width="1.5"/>')
    b.append(f'<rect x="695" y="{y1 - 6}" width="165" height="12" rx="6" fill="{COLORS["green"]}" fill-opacity="0.25"/>')
    note(b, 751, y1 + 50, "predicted replacement day (with range)", 11.5, COLORS["green"], "middle", 700)
    b.append(line(xn + 4, 360, 745, 360, "green", both=True))
    note(b, 635, 352, "lead time for maintenance", 11, COLORS["green"], "middle")
    note(b, 530, 470, "Concept sketch, no data: inputs are η trend, RPM at fixed duty, motor current and ΔP.", 11.5, MUTED, "middle")
    svg("t9_filter_life_concept.svg", 1060, 490, "T9 — Predictive maintenance: warn before efficiency reaches 50 %", b)


# ---------------------------------------------------------------- T10
def t10():
    b = []
    x0, x1, y0, y1 = 110, 900, 80, 430
    b.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}" stroke-width="1.4"/>')
    b.append(f'<line x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}" stroke="{LINE}" stroke-width="1.4"/>')
    note(b, 505, y1 + 32, "energy used per hour (Wh)  →  more", 12, INK, "middle", 600)
    note(b, 62, 255, "PM removed (exposure reduction)  →  better", 12, INK, "middle", 600)
    b[-1] = b[-1].replace("<text ", '<text transform="rotate(-90 62 255)" ')
    b.append(path("M150,400 C220,250 380,150 860,110", "blue", arrow=False, sw=2.5))
    note(b, 640, 112, "front traced by sweeping λ", 12, COLORS["blue"], "middle", 700)
    b.append(path("M760,150 C620,190 480,230 360,250", "blue", sw=1.4, dash=True))
    note(b, 560, 238, "increasing λ (energy matters more)", 11, COLORS["blue"], "middle")
    pts = [("A", "Threshold (baseline)", 700, 330, "#6b7280"), ("B", "PID / fuzzy", 560, 250, "#f59e0b"),
           ("C", "MPC", 430, 190, "#2563eb"), ("D", "RL", 330, 232, "#7c3aed")]
    for k, nm, x, y, c in pts:
        b.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{c}" fill-opacity="0.85"/>')
        note(b, x + 15, y + 5, f"{k} · {nm}", 12, INK, weight=600)
    b.append(rect(560, 360, 330, 50, "note"))
    note(b, 575, 382, "Hypothesis H2: C and D sit on the front;", 11.5, INK)
    note(b, 575, 400, "A spends more energy for less removal.", 11.5, INK)
    note(b, 505, 490, "Concept sketch: point positions are the hypothesis to test, not results.", 11.5, MUTED, "middle")
    svg("t10_energy_tradeoff_concept.svg", 1000, 510, "T10 — Energy vs cleanliness: where each controller should land", b)


if __name__ == "__main__":
    for f in (t1, t2, t3, t4, t5, t6, t7, t8, t9, t10):
        f()
    print("ok")
