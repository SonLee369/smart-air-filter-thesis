# Generates docs/figures/*.svg for the smart air filter baseline.
import math, os
from xml.sax.saxutils import escape

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"
INK, MUTED, LINE = "#1f2937", "#4b5563", "#374151"

# kind -> (fill, stroke)
K = {
    "mcu": ("#e8f0fe", "#2563eb"), "gw": ("#e7f6ec", "#16a34a"), "web": ("#f3e8ff", "#7c3aed"),
    "dust": ("#fff1e6", "#ea580c"), "co": ("#fef3c7", "#b45309"), "hall": ("#f3e8ff", "#7c3aed"),
    "act": ("#fde8e8", "#dc2626"), "lora": ("#e0f7f6", "#0d9488"), "rtc": ("#eef2f7", "#475569"),
    "pwr": ("#fef9c3", "#a16207"), "gnd": ("#e5e7eb", "#111827"), "plain": ("#ffffff", "#9ca3af"),
    "note": ("#f9fafb", "#d1d5db"), "warn": ("#fff7ed", "#ea580c"),
}
COLORS = {"gray": LINE, "blue": "#2563eb", "green": "#16a34a", "red": "#dc2626",
          "orange": "#ea580c", "teal": "#0d9488", "purple": "#7c3aed", "amber": "#a16207"}


def defs():
    m = []
    for name, c in COLORS.items():
        m.append(f'<marker id="a-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                 f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
    return "<defs>" + "".join(m) + "</defs>"


def svg(name, w, h, title, body):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
         f'font-family="{FONT}">\n<title>{escape(title)}</title>\n{defs()}\n'
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>\n'
         f'{text(w/2, 34, title, 18, 700)}\n' + "\n".join(body) + "\n</svg>\n")
    with open(os.path.join(OUT, name), "w") as f:
        f.write(s)


def text(x, y, s, size=12, weight=400, anchor="middle", fill=INK, extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
            f'fill="{fill}" {extra}>{escape(str(s))}</text>')


def rect(x, y, w, h, kind="plain", rx=8, dash=False, sw=1.5):
    f, s = K[kind]
    d = ' stroke-dasharray="6 4"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{s}" stroke-width="{sw}"{d}/>'


def box(x, y, w, h, kind, title, lines=(), size=12, dash=False, align="middle"):
    out = [rect(x, y, w, h, kind, dash=dash)]
    n = 1 + len(lines)
    lh = size + 6
    y0 = y + h / 2 - (n - 1) * lh / 2 + size * 0.35
    tx = x + w / 2 if align == "middle" else x + 12
    out.append(text(tx, y0, title, size + 1, 700, align, K[kind][1] if kind not in ("plain", "note") else INK))
    for i, l in enumerate(lines):
        out.append(text(tx, y0 + (i + 1) * lh, l, size, 400, align, MUTED))
    return "\n".join(out)


def line(x1, y1, x2, y2, color="gray", arrow=True, dash=False, sw=1.6, both=False):
    c = COLORS[color]
    d = ' stroke-dasharray="6 4"' if dash else ""
    a = f' marker-end="url(#a-{color})"' if arrow else ""
    b = f' marker-start="url(#a-{color})"' if both else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}"{d}{a}{b}/>'


def path(d, color="gray", arrow=True, dash=False, sw=1.6):
    c = COLORS[color]
    ds = ' stroke-dasharray="6 4"' if dash else ""
    a = f' marker-end="url(#a-{color})"' if arrow else ""
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{sw}"{ds}{a}/>'


def diamond(cx, cy, w, h, label, kind="plain"):
    f, s = K[kind]
    pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
    return (f'<polygon points="{pts}" fill="{f}" stroke="{s}" stroke-width="1.5"/>' +
            text(cx, cy + 4, label, 12, 600))


# ---------------------------------------------------------------- Fig 1
def fig1():
    b = []
    b.append(box(30, 75, 250, 200, "mcu", "Filter column node",
                 ["ESP32-WROOM (30-pin)", "2× GP2Y1010 dust (in / out)", "2× MQ-7 CO (in / out)",
                  "Fan + BTS7960 + KY-003 Hall", "DS1307 RTC", "LoRa Ra-02 (TX)"]))
    b.append(box(400, 95, 220, 160, "gw", "Gateway",
                 ["ESP32-WROOM (38-pin)", "LoRa Ra-02 (RX) + validate", "Latest packet kept in RAM",
                  "WebServer :80 + LittleFS"]))
    b.append(box(740, 95, 200, 160, "web", "Web dashboard",
                 ["Phone / PC browser", "GET /  → index.html", "GET /get-data → JSON", "polled every 2 s"]))
    b.append(line(282, 175, 398, 175, "teal", sw=2.2))
    b.append(text(340, 150, "LoRa 433 MHz", 12, 600, fill=COLORS["teal"]))
    b.append(text(340, 165, "SF7 · 125 kHz", 11, fill=MUTED))
    b.append(text(340, 195, "SensorPacket", 11, fill=MUTED))
    b.append(text(340, 209, "30 B, every 5 s", 11, fill=MUTED))
    b.append(line(622, 175, 738, 175, "green", sw=2.2, both=True))
    b.append(text(680, 150, "WiFi (STA)", 12, 600, fill=COLORS["green"]))
    b.append(text(680, 165, "HTTP :80", 11, fill=MUTED))
    b.append(text(680, 195, "JSON / HTML", 11, fill=MUTED))
    # more nodes (star topology)
    b.append(box(30, 310, 110, 42, "mcu", "Node 2", [], dash=True))
    b.append(box(170, 310, 110, 42, "mcu", "Node n", [], dash=True))
    b.append(path("M85,352 C90,395 440,395 470,257", "teal", dash=True))
    b.append(path("M280,331 C380,331 450,310 500,257", "teal", dash=True))
    b.append(text(250, 418, "More columns: same protocol, own senderId (star topology)", 11, anchor="middle", fill=MUTED))
    svg("fig1_system_architecture.svg", 970, 435, "Fig 1 — System architecture", b)


# ---------------------------------------------------------------- Fig 2
def fig2():
    b = []
    b.append(box(390, 190, 200, 240, "mcu", "ESP32-WROOM-32",
                 ["30-pin DevKit · node", "ADC (4 ch)", "LEDC PWM 20 kHz", "SPI · I²C", "GPIO interrupt", "NVS (MQ-7 R0)"]))
    b.append(box(390, 70, 200, 60, "pwr", "5 V 1 A adapter", ["control + sensors"]))
    b.append(line(490, 130, 490, 188, "amber"))
    b.append(text(500, 165, "5 V → VIN", 11, anchor="start", fill=COLORS["amber"]))
    b.append(box(720, 40, 230, 50, "pwr", "12 V 15 A PSU", ["motor power only"]))
    left = [("dust", "GP2Y1010 — inlet dust", "LED GPIO25 · VOUT GPIO33", 130, 230, "ADC + pulse"),
            ("dust", "GP2Y1010 — outlet dust", "LED GPIO14 · VOUT GPIO32", 215, 280, "ADC + pulse"),
            ("co", "MQ-7 — inlet CO", "AOUT GPIO4", 300, 330, "ADC"),
            ("co", "MQ-7 — outlet CO", "AOUT GPIO35", 385, 380, "ADC")]
    for kind, t, l, y, ty, lab in left:
        b.append(box(40, y, 230, 60, kind, t, [l]))
        b.append(line(272, y + 30, 388, ty, "orange" if kind == "dust" else "amber"))
        b.append(text(330, (y + 30 + ty) / 2 - 6, lab, 10, fill=MUTED))
    b.append(box(720, 110, 230, 60, "act", "BTS7960 H-bridge", ["RPWM GPIO26 · LPWM GPIO27 (LOW)"]))
    b.append(line(835, 90, 835, 108, "amber"))
    b.append(text(843, 104, "12 V", 10, anchor="start", fill=COLORS["amber"]))
    b.append(line(592, 215, 718, 140, "red"))
    b.append(text(650, 168, "PWM", 10, fill=MUTED))
    b.append(box(720, 195, 230, 50, "act", "Centrifugal fan", ["12 V DC motor · magnet on shaft"]))
    b.append(line(835, 170, 835, 193, "red"))
    b.append(text(843, 186, "M+ / M−", 10, anchor="start", fill=MUTED))
    b.append(box(720, 275, 230, 55, "hall", "KY-003 Hall sensor", ["S → GPIO34 (falling-edge ISR)"]))
    b.append(line(835, 245, 835, 273, "purple", dash=True, arrow=False))
    b.append(text(843, 263, "1 pulse / turn", 10, anchor="start", fill=MUTED))
    b.append(line(718, 302, 592, 300, "purple"))
    b.append(text(655, 294, "INT", 10, fill=MUTED))
    b.append(box(720, 360, 230, 60, "lora", "LoRa Ra-02 (SX1278)", ["433 MHz · NSS 5 · SPI 18/19/23"]))
    b.append(line(592, 375, 718, 390, "teal", both=True))
    b.append(text(655, 372, "SPI", 10, fill=MUTED))
    b.append(text(835, 440, "→ gateway (SensorPacket)", 11, fill=COLORS["teal"]))
    b.append(box(720, 460, 230, 55, "rtc", "DS1307 RTC", ["SDA 21 · SCL 22 · 00:00 self test"]))
    b.append(line(592, 415, 718, 485, "gray", both=True))
    b.append(text(650, 462, "I²C", 10, fill=MUTED))
    b.append(text(155, 480, "Sensors (inputs)", 13, 700, fill=MUTED))
    b.append(text(155, 498, "analog lines through 33k/47k dividers", 11, fill=MUTED))
    svg("fig2_node_block_diagram.svg", 990, 540, "Fig 2 — Filter column node: block diagram", b)


# ---------------------------------------------------------------- pin board helper
def board(b, x, y0, step, w, left, right, title, used_l, used_r, tag_w=260, gap=150):
    n = max(len(left), len(right))
    top, bottom = y0 - 40, y0 + (n - 1) * step + 30
    b.append(f'<rect x="{x}" y="{top}" width="{w}" height="{bottom-top}" rx="10" fill="#1e293b" stroke="#0f172a"/>')
    b.append(text(x + w / 2, top + 22, title, 12, 700, fill="#f8fafc"))
    b.append(f'<rect x="{x+w/2-28}" y="{bottom-6}" width="56" height="20" rx="3" fill="#94a3b8"/>')
    b.append(text(x + w / 2, bottom + 9, "USB", 10, 700, fill="#0f172a"))
    for side, pins, used in (("L", left, used_l), ("R", right, used_r)):
        for i, p in enumerate(pins):
            y = y0 + i * step
            px = x if side == "L" else x + w
            on = p in used
            b.append(f'<circle cx="{px}" cy="{y}" r="5" fill="{"#fbbf24" if on else "#64748b"}" stroke="#0f172a"/>')
            b.append(text(px + (12 if side == "L" else -12), y + 4, p, 11, 700 if on else 400,
                          "start" if side == "L" else "end", "#f8fafc" if on else "#94a3b8"))
            if not on:
                continue
            kind, label, div = used[p]
            col = K[kind][1]
            if side == "L":
                tx = x - gap - tag_w
                b.append(f'<line x1="{x-5}" y1="{y}" x2="{tx+tag_w}" y2="{y}" stroke="{col}" stroke-width="2"/>')
                b.append(rect(tx, y - 11, tag_w, 22, kind, rx=5, sw=1.2))
                b.append(text(tx + 10, y + 4, label, 11.5, 600, "start", INK))
                if div:
                    cx = x - gap / 2
            else:
                tx = x + w + gap
                b.append(f'<line x1="{x+w+5}" y1="{y}" x2="{tx}" y2="{y}" stroke="{col}" stroke-width="2"/>')
                b.append(rect(tx, y - 11, tag_w, 22, kind, rx=5, sw=1.2))
                b.append(text(tx + 10, y + 4, label, 11.5, 600, "start", INK))
                if div:
                    cx = x + w + gap / 2
            if div:
                b.append(f'<rect x="{cx-16}" y="{y-9}" width="32" height="18" rx="9" fill="#ffffff" stroke="{col}" stroke-width="1.5"/>')
                b.append(text(cx, y + 4, "÷", 13, 700, fill=col))
    return bottom


def legend(b, x, y, items):
    for i, (kind, lab) in enumerate(items):
        xx = x + i * 150
        b.append(rect(xx, y - 10, 14, 14, kind, rx=3, sw=1.2))
        b.append(text(xx + 20, y + 2, lab, 11, anchor="start", fill=MUTED))


# ---------------------------------------------------------------- Fig 3
def fig3():
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
          "D22": ("rtc", "DS1307  SCL", False),
          "D21": ("rtc", "DS1307  SDA", False),
          "D19": ("lora", "Ra-02  MISO", False),
          "D18": ("lora", "Ra-02  SCK", False),
          "D5": ("lora", "Ra-02  NSS (CS)", False),
          "D4": ("co", "MQ-7 inlet  AOUT", True),
          "GND": ("gnd", "Common GND", False),
          "3V3": ("pwr", "Ra-02, KY-003, BTS7960 VCC/R_EN/L_EN", False)}
    legend(b, 60, 70, [("dust", "GP2Y1010 dust"), ("co", "MQ-7 CO"), ("hall", "KY-003 Hall"),
                       ("act", "BTS7960"), ("lora", "LoRa Ra-02"), ("rtc", "DS1307"), ("pwr", "Power")])
    b.append(text(1110, 74, "÷ = divider", 11, 700, "start", COLORS["orange"]))
    bottom = board(b, 500, 150, 30, 180, left, right, "ESP32 DevKit V1 (30-pin)", ul, ur, tag_w=270, gap=140)
    # divider panel
    py = bottom + 50
    b.append(rect(40, py, 520, 210, "note"))
    b.append(text(60, py + 26, "÷  Voltage divider on each analog line (×4)", 13, 700, "start"))
    y = py + 80
    b.append(text(60, y + 4, "Sensor OUT", 12, 600, "start"))
    b.append(f'<line x1="140" y1="{y}" x2="180" y2="{y}" stroke="{LINE}" stroke-width="1.6"/>')
    b.append(f'<rect x="180" y="{y-8}" width="60" height="16" fill="#fff" stroke="{LINE}" stroke-width="1.6"/>')
    b.append(text(210, y - 14, "33 kΩ", 11, 600))
    b.append(f'<line x1="240" y1="{y}" x2="400" y2="{y}" stroke="{LINE}" stroke-width="1.6"/>')
    b.append(f'<circle cx="300" cy="{y}" r="3.5" fill="{LINE}"/>')
    b.append(line(300, y, 398, y, "gray"))
    b.append(text(405, y + 4, "ESP32 ADC pin", 12, 600, "start"))
    b.append(f'<line x1="300" y1="{y}" x2="300" y2="{y+20}" stroke="{LINE}" stroke-width="1.6"/>')
    b.append(f'<rect x="292" y="{y+20}" width="16" height="50" fill="#fff" stroke="{LINE}" stroke-width="1.6"/>')
    b.append(text(316, y + 50, "47 kΩ", 11, 600, "start"))
    b.append(f'<line x1="300" y1="{y+70}" x2="300" y2="{y+86}" stroke="{LINE}" stroke-width="1.6"/>')
    for i, hw in enumerate((14, 9, 4)):
        b.append(f'<line x1="{300-hw}" y1="{y+86+i*5}" x2="{300+hw}" y2="{y+86+i*5}" stroke="{LINE}" stroke-width="1.6"/>')
    b.append(text(60, y + 120, "Vpin = Vout × 47 / 80  →  5 V max becomes 2.94 V (ADC limit ≈ 3.1 V)", 11.5, anchor="start", fill=MUTED))
    # power notes
    b.append(rect(600, py, 540, 210, "note"))
    b.append(text(620, py + 26, "Module power", 13, 700, "start"))
    notes = ["GP2Y1010 ×2: VCC 5 V · V-LED via 150 Ω from 5 V + 220 µF to LED-GND",
             "MQ-7 ×2: VCC 5 V (heater) · GND",
             "KY-003: VCC 3.3 V (not 5 V: GPIO34 is not 5 V tolerant)",
             "BTS7960: B+ / B− → 12 V PSU · M+ / M− → fan motor",
             "LoRa Ra-02: 3.3 V only · RST and DIO0 not connected",
             "DS1307: VCC 5 V · remove its I²C pull-ups or use a level shifter",
             "All grounds common: ESP32, 5 V adapter −, 12 V PSU −"]
    for i, n in enumerate(notes):
        b.append(text(620, py + 56 + i * 21, "• " + n, 11.5, anchor="start", fill=MUTED))
    svg("fig3_node_wiring.svg", 1180, py + 235, "Fig 3 — Node wiring (ESP32 30-pin)", b)


# ---------------------------------------------------------------- Fig 4
def fig4():
    b = []
    left = ["3V3", "EN", "VP 36", "VN 39", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "SD2", "SD3", "CMD", "5V"]
    right = ["GND", "23", "22", "TX0", "RX0", "21", "GND ", "19", "18", "5", "17", "16", "4", "0", "2", "15", "SD1", "SD0", "CLK"]
    ul = {"3V3": ("pwr", "Ra-02  3.3V", False),
          "26": ("lora", "Ra-02  DIO0 (polled)", False),
          "14": ("lora", "Ra-02  RST", False),
          "GND": ("gnd", "Ra-02  GND", False),
          "5V": ("pwr", "USB / 5 V supply", False)}
    ur = {"23": ("lora", "Ra-02  MOSI", False),
          "19": ("lora", "Ra-02  MISO", False),
          "18": ("lora", "Ra-02  SCK", False),
          "5": ("lora", "Ra-02  NSS (CS)", False)}
    bottom = board(b, 470, 120, 28, 170, left, right, "ESP32 DevKitC (38-pin)", ul, ur, tag_w=220, gap=110)
    py = bottom + 45
    b.append(rect(40, py, 1020, 120, "warn"))
    b.append(text(60, py + 26, "Notes", 13, 700, "start", COLORS["orange"]))
    notes = ["Ra-02 is a 3.3 V part: never connect its VCC to 5 V. Fit the 433 MHz antenna before transmitting.",
             "DIO0 uses GPIO26, not GPIO2 (GPIO2 is a boot strapping pin and drives the on-board LED).",
             "Pin order follows the common DevKitC layout; check the silkscreen of your board.",
             "Same SPI pins as the node (VSPI 18/19/23/5), so one wiring habit for both boards."]
    for i, n in enumerate(notes):
        b.append(text(60, py + 50 + i * 19, "• " + n, 11.5, anchor="start", fill=MUTED))
    svg("fig4_gateway_wiring.svg", 1100, py + 140, "Fig 4 — Gateway wiring (ESP32 38-pin + LoRa Ra-02)", b)


# ---------------------------------------------------------------- Fig 5
def fig5():
    b = []
    y1, y2 = 110, 230
    b.append(f'<rect x="100" y="{y1}" width="860" height="{y2-y1}" rx="14" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>')
    # sections
    b.append(text(195, y1 - 12, "Inlet duct", 12, 700, fill=MUTED))
    b.append(box(130, 135, 130, 70, "dust", "Sensors IN", ["GP2Y + MQ-7"]))
    # fan
    cx, cy = 345, 170
    b.append(f'<circle cx="{cx}" cy="{cy}" r="48" fill="{K["act"][0]}" stroke="{K["act"][1]}" stroke-width="2"/>')
    for k in range(6):
        a = k * math.pi / 3
        x1, yy1 = cx + 10 * math.cos(a), cy + 10 * math.sin(a)
        x2, yy2 = cx + 40 * math.cos(a + 0.6), cy + 40 * math.sin(a + 0.6)
        b.append(f'<path d="M{x1:.1f},{yy1:.1f} Q{cx+30*math.cos(a+0.1):.1f},{cy+30*math.sin(a+0.1):.1f} {x2:.1f},{yy2:.1f}" '
                 f'fill="none" stroke="{K["act"][1]}" stroke-width="3" stroke-linecap="round"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{K["act"][1]}"/>')
    b.append(text(cx, y1 - 12, "Fan (12 V, PWM)", 12, 700, fill=MUTED))
    # filters
    filt = [("Coarse pre-filter", "#fde68a", "#a16207"), ("Activated carbon", "#d1d5db", "#111827"),
            ("Electrostatic cotton", "#bfdbfe", "#2563eb")]
    for i, (nm, f, s) in enumerate(filt):
        x = 440 + i * 105
        b.append(f'<rect x="{x}" y="{y1+6}" width="85" height="{y2-y1-12}" rx="6" fill="{f}" stroke="{s}" stroke-width="1.5"/>')
        if i == 1:
            for k in range(14):
                b.append(f'<circle cx="{x+12+(k%4)*20}" cy="{y1+22+(k//4)*25}" r="5" fill="#4b5563"/>')
        else:
            for k in range(6):
                xx = x + 10 + k * 13
                b.append(f'<line x1="{xx}" y1="{y1+12}" x2="{xx}" y2="{y2-12}" stroke="{s}" stroke-width="1" opacity=".6"/>')
        b.append(text(x + 42, y2 + 22, nm, 11, 600, fill=s))
    b.append(text(597, y1 - 12, "Filter stack", 12, 700, fill=MUTED))
    b.append(text(860, y1 - 12, "Outlet duct", 12, 700, fill=MUTED))
    b.append(box(795, 135, 130, 70, "dust", "Sensors OUT", ["GP2Y + MQ-7"]))
    # flow arrows
    b.append(line(20, 170, 125, 170, "red", sw=4))
    b.append(text(55, 150, "Polluted", 12, 700, fill=COLORS["red"]))
    b.append(text(55, 196, "air", 12, 700, fill=COLORS["red"]))
    b.append(line(262, 170, 292, 170, "gray", sw=2.5))
    b.append(line(396, 170, 436, 170, "gray", sw=2.5))
    b.append(line(752, 170, 790, 170, "gray", sw=2.5))
    b.append(line(928, 170, 1060, 170, "green", sw=4))
    b.append(text(1015, 150, "Clean", 12, 700, fill=COLORS["green"]))
    b.append(text(1015, 196, "air", 12, 700, fill=COLORS["green"]))
    # phases
    b.append(box(60, 290, 470, 110, "mcu", "MEASURING — fan low",
                 ["duty 0.22 ≈ 1 320 RPM: a small sample flows past the sensors",
                  "CO_in > 50 ppm or PM_in > 35 µg/m³ (after 10 s) → FILTERING"]))
    b.append(box(570, 290, 470, 110, "act", "FILTERING — fan high",
                 ["duty 0.52 ≈ 3 120 RPM: large airflow through the filter stack",
                  "≥ 60 s and both below 80 % of threshold → MEASURING"]))
    b.append(rect(60, 425, 980, 80, "note"))
    b.append(text(550, 452, "Filter efficiency η = (in − out) / in × 100 %   ·   η_total = (η_PM + η_CO) / 2   ·   "
                  "η < 50 % for ≈ 60 s → REPLACE FILTER", 12.5, 600))
    b.append(text(550, 482, "Airflow  Q = k · (2π · r · RPM / 60) · A,   k = 0.6   (thesis eq. 3–5)", 12.5, 400, fill=MUTED))
    svg("fig5_airflow_principle.svg", 1080, 525, "Fig 5 — Airflow and operating principle", b)


# ---------------------------------------------------------------- Fig 6
def fig6():
    b = []
    b.append(box(80, 190, 250, 110, "mcu", "MEASURING", ["fan duty 0.22 (≈ 1 320 RPM)", "motor + filter checks active", "start state"]))
    b.append(box(650, 190, 250, 110, "act", "FILTERING", ["fan duty 0.52 (≈ 3 120 RPM)", "motor + filter checks active", "minimum 60 s"]))
    b.append(box(355, 430, 270, 110, "rtc", "SELF_TEST", ["fan duty 0.22", "30 s settle + 10 s average", "→ set MQ-7 / GP2Y fault flags"]))
    b.append('<circle cx="40" cy="245" r="9" fill="#111827"/>')
    b.append(line(49, 245, 78, 245, "gray"))
    b.append(text(52, 228, "boot", 11, anchor="start", fill=MUTED))
    b.append(path("M330,215 Q490,110 650,215", "red", sw=2))
    b.append(text(490, 132, "settled ≥ 10 s  AND  (CO_in > 50 ppm  OR  PM_in > 35 µg/m³)", 12, 600, fill=COLORS["red"]))
    b.append(path("M650,280 Q490,375 330,280", "blue", sw=2))
    b.append(text(490, 360, "≥ 60 s  AND  CO_in < 40 ppm  AND  PM_in < 28 µg/m³", 12, 600, fill=COLORS["blue"]))
    b.append(text(490, 376, "(80 % hysteresis avoids rapid on/off)", 11, fill=MUTED))
    b.append(line(760, 300, 610, 428, "gray"))
    b.append(text(728, 395, "RTC 00:00 or 't'", 11, 600, "start", MUTED))
    b.append(line(245, 300, 400, 428, "gray"))
    b.append(text(210, 395, "RTC 00:00 or 't'", 11, 600, "start", MUTED))
    b.append(path("M355,505 Q170,505 150,302", "blue", sw=1.8))
    b.append(text(170, 530, "done (≈ 40 s) → MEASURING", 11, 600, fill=COLORS["blue"]))
    b.append(rect(80, 565, 820, 66, "note"))
    b.append(text(100, 590, "Always on (MEASURING/FILTERING): motor check |RPM − duty·6000| ≤ 35 % (3 s to flag) · filter check η ≥ 50 % (≈ 60 s to flag)",
                  11.5, anchor="start", fill=MUTED))
    b.append(text(100, 612, "Bench test: 'fan m' / 'fan f' hold a state (decision skipped), 'fan auto' resumes, 'sim …' overrides readings",
                  11.5, anchor="start", fill=MUTED))
    svg("fig6_state_machine.svg", 980, 650, "Fig 6 — Node control state machine", b)


# ---------------------------------------------------------------- Fig 7
def fig7():
    b = []
    def pb(cx, y, w, h, kind, t, sub=None):
        lines = [sub] if sub else []
        b.append(box(cx - w / 2, y, w, h, kind, t, lines, size=11))
    # setup column
    b.append(text(200, 66, "setup()", 14, 700, fill=MUTED))
    steps = [("Power on / reset", None, "pwr"),
             ("GPIO: GP2Y LEDs off, LPWM LOW", None, "plain"),
             ("LEDC PWM 20 kHz on RPWM (GPIO26)", None, "plain"),
             ("Hall ISR on GPIO34 (FALLING)", None, "hall"),
             ("Load MQ-7 R0 from NVS", None, "plain"),
             ("DS1307: start, set if stopped", None, "rtc"),
             ("LoRa Ra-02: 3 tries", "radio on, or run without", "lora")]
    for i, (t, s, k) in enumerate(steps):
        y = 80 + i * 70
        pb(200, y, 270, 46, k, t, s)
        if i:
            b.append(line(200, y - 24, 200, y - 2))
    b.append(line(200, 80 + 6 * 70 + 46, 200, 80 + 7 * 70 - 2))
    pb(200, 80 + 7 * 70, 270, 40, "mcu", "→ loop()")
    # ISR
    b.append(text(200, 700, "Interrupt (any time)", 14, 700, fill=MUTED))
    pb(200, 715, 270, 42, "hall", "KY-003 falling edge")
    b.append(line(200, 757, 200, 783))
    b.append(diamond(200, 815, 230, 60, "Δt ≥ 3 ms since last?", "hall"))
    b.append(line(200, 845, 200, 871))
    b.append(text(208, 864, "yes", 11, anchor="start", fill=MUTED))
    pb(200, 873, 270, 40, "hall", "hallPulses += 1")
    b.append(text(60, 860, "no → ignore", 11, anchor="start", fill=MUTED))
    # loop column
    X, W = 640, 330
    b.append(text(X, 66, "loop()", 14, 700, fill=MUTED))
    rows = [(80, "handleSerial()", "t · r · T… · sim · fan · ?", "plain"),
            (150, "updateFanRamp()", "duty → target at 0.2 / s (smooth)", "act"),
            (220, "updateRpm() every 1 s", "RPM = 60 × pulses / s", "hall"),
            (290, "Motor check (skip ramps + 5 s)", "|RPM − duty·6000| > 35 % ×3 → FAULT", "hall")]
    for i, (y, t, s, k) in enumerate(rows):
        pb(X, y, W, 46, k, t, s)
        if i:
            b.append(line(X, y - 24, X, y - 2))
    b.append(line(X, 336, X, 368))
    b.append(diamond(X, 400, 200, 60, "2 s elapsed?"))
    b.append(line(X, 430, X, 458))
    b.append(text(X + 8, 450, "yes", 11, anchor="start", fill=MUTED))
    rows2 = [(460, "readSensors()", "2× GP2Y, 2× MQ-7 (trimmed mean), sim overrides", "dust"),
             (530, "checkSchedule()", "RTC 00:00 → SELF_TEST", "rtc")]
    for y, t, s, k in rows2:
        pb(X, y, W, 46, k, t, s)
    b.append(line(X, 506, X, 528))
    b.append(line(X, 576, X, 608))
    b.append(diamond(X, 640, 220, 60, "mode == SELF_TEST?"))
    b.append(line(X, 670, X, 698))
    b.append(text(X + 8, 690, "no", 11, anchor="start", fill=MUTED))
    pb(X, 700, W, 46, "mcu", "checkFilter() + decideMode()", "η check · MEASURING ↔ FILTERING")
    b.append(line(X + 110, 640, 868, 640))
    b.append(text(X + 120, 632, "yes", 11, anchor="start", fill=MUTED))
    pb(940, 615, 140, 50, "rtc", "runSelfTest()", "settle, average")
    b.append(path(f"M940,665 L940,795 L{X+W/2+2},795", "gray"))
    b.append(line(X, 746, X, 768))
    pb(X, 770, W, 46, "plain", "printStatus()", "3 short lines every 2 s")
    b.append(line(X, 816, X, 848))
    b.append(diamond(X, 880, 220, 60, "txNow or 5 s?"))
    b.append(line(X, 910, X, 938))
    b.append(text(X + 8, 930, "yes", 11, anchor="start", fill=MUTED))
    pb(X, 940, W, 46, "lora", "sendPacket()", "SensorPacket 30 B over LoRa")
    # 2 s "no" branch → tx diamond
    b.append(path(f"M{X-100},400 L460,400 L460,880 L{X-112},880", "gray"))
    b.append(text(470, 392, "no", 11, anchor="start", fill=MUTED))
    # tx "no" + loop back
    b.append(path(f"M{X+110},880 L{X+200},880 L{X+200},1010 L430,1010", "gray", arrow=False))
    b.append(path(f"M{X},986 L{X},1010", "gray", arrow=False))
    b.append(path(f"M430,1010 L430,103 L{X-W/2-2},103", "gray"))
    b.append(text(X + 210, 900, "no", 11, anchor="start", fill=MUTED))
    b.append(path("M335,893 C420,893 420,243 474,243", "purple", dash=True))
    b.append(text(345, 560, "count read", 10, anchor="start", fill=COLORS["purple"]))
    b.append(text(345, 573, "atomically", 10, anchor="start", fill=COLORS["purple"]))
    svg("fig7_firmware_flowchart.svg", 1030, 1040, "Fig 7 — Node firmware flowchart", b)


# ---------------------------------------------------------------- Fig 8
def fig8():
    b = []
    fields = [(0, 1, "senderId", "uint8", "node id (0x01)", "rtc"),
              (1, 1, "receiverId", "uint8", "gateway id (0x64), checked by gateway", "rtc"),
              (2, 4, "CO_ppm", "float32", "CO at inlet, ppm", "co"),
              (6, 4, "CO_ppm_2", "float32", "CO at outlet, ppm", "co"),
              (10, 4, "dust", "float32", "dust at inlet, µg/m³", "dust"),
              (14, 4, "dust_2", "float32", "dust at outlet, µg/m³", "dust"),
              (18, 1, "motor_flag", "bool", "true = fan at expected speed", "act"),
              (19, 1, "motor_mode", "uint8", "0 MEASURING · 1 FILTERING · 2 SELF_TEST", "act"),
              (20, 4, "RPM", "uint32", "measured fan speed", "hall"),
              (24, 1, "filter_flag", "bool", "true = replace filter", "web"),
              (25, 1, "web_flag", "bool", "reserved (always false)", "plain"),
              (26, 1, "mq7_flag", "bool", "true = inlet CO sensor fault", "gnd"),
              (27, 1, "mq7_flag_2", "bool", "true = outlet CO sensor fault", "gnd"),
              (28, 1, "gp2y_flag", "bool", "true = inlet dust sensor fault", "gnd"),
              (29, 1, "gp2y_flag_2", "bool", "true = outlet dust sensor fault", "gnd")]
    x0, cw, y = 50, 32, 210
    for off, size, name, typ, mean, kind in fields:
        x = x0 + off * cw
        b.append(rect(x, y, size * cw, 46, kind, rx=3, sw=1.2))
        if size == 4:
            b.append(text(x + size * cw / 2, y + 28, name, 12, 700))
        else:
            b.append(text(x + cw / 2, y - 8, name, 11, 600, "start", INK,
                          f'transform="rotate(-55 {x+cw/2} {y-8})"'))
    for i in range(31):
        b.append(f'<line x1="{x0+i*cw}" y1="{y+46}" x2="{x0+i*cw}" y2="{y+54}" stroke="#9ca3af"/>')
    for i in range(30):
        b.append(text(x0 + i * cw + cw / 2, y + 68, i, 10, fill=MUTED))
    b.append(text(x0, y + 88, "byte offset · packed struct · little-endian · total 30 bytes (thesis says 31: it counts 8 bools, the struct has 7)", 11.5, anchor="start", fill=MUTED))
    groups = [(0, 2, "IDs"), (2, 18, "Measurements (float32)"), (18, 20, "Motor"), (20, 24, "RPM"), (24, 30, "Flags")]
    for a, z, lab in groups:
        xa, xz = x0 + a * cw + 3, x0 + z * cw - 3
        b.append(f'<path d="M{xa},76 L{xa},70 L{xz},70 L{xz},76" fill="none" stroke="{LINE}" stroke-width="1.2"/>')
        b.append(text((xa + xz) / 2, 62, lab, 12, 700, fill=MUTED))
    # table
    ty = 340
    cols = [(50, "Offset"), (120, "Size"), (175, "Type"), (260, "Field"), (400, "Meaning")]
    b.append(f'<rect x="40" y="{ty-18}" width="980" height="26" fill="#f3f4f6"/>')
    for cx, h in cols:
        b.append(text(cx, ty, h, 12, 700, "start"))
    for i, (off, size, name, typ, mean, kind) in enumerate(fields):
        yy = ty + 26 + i * 21
        b.append(rect(40, yy - 13, 6, 16, kind, rx=1, sw=1))
        for (cx, _), v in zip(cols, (off, size, typ, name, mean)):
            b.append(text(cx, yy, v, 11.5, 600 if cx == 260 else 400, "start", INK if cx == 260 else MUTED))
    b.append(text(50, ty + 26 + 15 * 21 + 8, "Sent as raw bytes (no string parsing). Gateway accepts only size == 30 and receiverId == 0x64.",
                  11.5, anchor="start", fill=MUTED))
    svg("fig8_sensor_packet.svg", 1060, ty + 26 + 15 * 21 + 30, "Fig 8 — SensorPacket layout (LoRa payload)", b)


# ---------------------------------------------------------------- Fig 9
def fig9():
    b = []
    b.append(text(500, 58, "Two separate supplies (thesis 2.3.1): motor power never shares the 5 V control rail", 12, fill=MUTED))
    b.append(box(30, 255, 120, 60, "gnd", "AC 220 V", ["mains"]))
    b.append(box(230, 100, 200, 70, "pwr", "12 V 15 A PSU", ["180 W · OVP / OCP / SCP"]))
    b.append(box(230, 390, 200, 70, "pwr", "5 V 1 A adapter", ["control + sensors"]))
    b.append(path("M150,285 L190,285 L190,135 L228,135", "red"))
    b.append(path("M150,285 L190,285 L190,425 L228,425", "amber"))
    b.append(box(520, 100, 180, 70, "act", "BTS7960", ["B+ / B− (power stage)"]))
    b.append(box(790, 100, 170, 70, "act", "Fan motor", ["12 V DC · PWM speed"]))
    b.append(line(432, 135, 518, 135, "red", sw=2.4))
    b.append(text(475, 126, "12 V", 11, 700, fill=COLORS["red"]))
    b.append(line(702, 135, 788, 135, "red", sw=2.4))
    b.append(text(745, 126, "M+ / M−", 11, 600, fill=MUTED))
    # 5 V rail
    b.append(line(432, 425, 470, 425, "amber", arrow=False, sw=2.4))
    b.append(f'<line x1="470" y1="250" x2="470" y2="535" stroke="{COLORS["amber"]}" stroke-width="3"/>')
    b.append(text(478, 238, "5 V rail", 12, 700, "start", COLORS["amber"]))
    five = [(250, "ESP32 VIN", "on-board 3.3 V LDO", "mcu"), (320, "GP2Y1010 ×2", "150 Ω + 220 µF on V-LED", "dust"),
            (390, "MQ-7 ×2", "heaters (largest 5 V load)", "co"), (460, "DS1307 RTC", "needs ≥ 4.5 V", "rtc")]
    for y, t, s, k in five:
        b.append(box(520, y, 180, 52, k, t, [s], size=11))
        b.append(line(470, y + 26, 518, y + 26, "amber"))
    # 3.3 V rail
    b.append(line(702, 276, 740, 276, "blue", arrow=False, sw=2.4))
    b.append(f'<line x1="740" y1="200" x2="740" y2="370" stroke="{COLORS["blue"]}" stroke-width="3"/>')
    b.append(text(748, 195, "3.3 V rail", 12, 700, "start", COLORS["blue"]))
    three = [(210, "LoRa Ra-02", "TX peak ≈ 120 mA", "lora"), (270, "BTS7960 logic", "VCC · R_EN · L_EN", "act"),
             (330, "KY-003 Hall", "keeps GPIO34 ≤ 3.3 V", "hall")]
    for y, t, s, k in three:
        b.append(box(790, y, 170, 48, k, t, [s], size=11))
        b.append(line(740, y + 24, 788, y + 24, "blue"))
    b.append(rect(790, 400, 170, 140, "note"))
    b.append(text(802, 422, "5 V budget (approx.)", 12, 700, "start"))
    for i, s in enumerate(["ESP32 + 3.3 V ≈ 200 mA pk", "MQ-7 2 × ≈ 70 mA", "GP2Y 2 × ≈ 20 mA",
                           "DS1307 < 1 mA", "Total ≈ 380 mA < 1 A ✓"]):
        b.append(text(802, 445 + i * 19, s, 11, 600 if i == 4 else 400, "start", COLORS["green"] if i == 4 else MUTED))
    # ground
    b.append(f'<rect x="30" y="570" width="930" height="26" rx="5" fill="#111827"/>')
    b.append(text(495, 588, "COMMON GND — 12 V PSU −, 5 V adapter −, ESP32 GND, all modules", 12, 700, fill="#f9fafb"))
    # ground returns (dashed) to the common bar
    b.append(path("M430,160 L448,160 L448,568", "gray", arrow=False, dash=True))
    b.append(line(330, 460, 330, 568, "gray", arrow=False, dash=True))
    b.append(path("M700,160 L725,160 L725,190", "gray", arrow=False, dash=True))
    b.append(text(456, 548, "PSU −", 10, anchor="start", fill=MUTED))
    b.append(text(338, 548, "adapter −", 10, anchor="start", fill=MUTED))
    b.append(text(712, 188, "B−", 10, anchor="end", fill=MUTED))
    b.append(rect(30, 360, 170, 160, "warn"))
    b.append(text(42, 382, "Bench tip", 12, 700, "start", COLORS["orange"]))
    for i, s in enumerate(["A PC USB port alone", "cannot feed the MQ-7", "heaters + LoRa: power", "sensors from the 5 V",
                           "adapter to avoid brown-", "outs / USB drop-outs."]):
        b.append(text(42, 404 + i * 18, s, 11, anchor="start", fill=MUTED))
    svg("fig9_power_distribution.svg", 990, 615, "Fig 9 — Power distribution", b)


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9):
        f()
    print("ok")
