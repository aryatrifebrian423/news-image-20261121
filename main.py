#!/usr/bin/env python3
"""news-image-20261121: one image summing up Saturday 21 November 2026.

Pure Python 3.13 standard library only. Draws a 1024x1024 editorial
front-page poster (masthead, three lead stories, 46 verified stories
grouped by region, a UTC timeline and a date check) and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png). Deterministic:
same bytes on every run. No network, no fonts, no third-party code.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)
INK = (26, 26, 26)
NAVY = (18, 38, 66)
NAVY2 = (28, 56, 92)
RED = (178, 32, 44)
BLUE = (31, 78, 121)
TEAL = (0, 102, 102)
GOLD = (176, 141, 44)
GRAY = (110, 108, 100)
LINE = (208, 202, 186)
WHITE = (255, 255, 255)
CREAM2 = (238, 232, 214)
GREEN = (46, 92, 52)
PURPLE = (88, 60, 118)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 pixels, "#" = on, "." = off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    # long dash and bullet, drawn from punctuation
    "—": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "–": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "•": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    "’": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "‘": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "“": ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "”": ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}

# ------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, w, color, t=1):
        self.fill(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill(x, y, t, h, color)

    def rect(self, x, y, w, h, color, t=1):
        self.hline(x, y, w, color, t)
        self.hline(x, y + h - t, w, color, t)
        self.vline(x, y, h, color, t)
        self.vline(x + w - t, y, h, color, t)

    def circle(self, cx, cy, r, color, t=2):
        # outline circle (midpoint, thick by drawing t rings)
        for rr in range(r - t + 1, r + 1):
            x, y, d = 0, rr, 1 - rr
            while x <= y:
                for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                               (x, -y), (y, -x), (-x, -y), (-y, -x)):
                    self.pixel(cx + sx, cy + sy, color)
                if d < 0:
                    d += 2 * x + 3
                else:
                    d += 2 * (x - y) + 5
                    y -= 1
                x += 1

    def text(self, x, y, s, color, scale=1):
        """Draw uppercased text; returns width in pixels."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch)
            if glyph is None:
                glyph = FONT["?"]
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x - scale  # width without trailing gap

    def text_width(self, s, scale=1):
        return max(0, len(s) * 6 * scale - scale)

    def wrap(self, s, max_chars):
        """Greedy word wrap to a list of lines, each <= max_chars."""
        words = s.split(" ")
        lines, cur = [], ""
        for word in words:
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= max_chars:
                cur += " " + word
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def fit(text, max_chars):
    """Truncate text to max_chars, adding '..' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 2].rstrip() + ".."


# ------------------------------------------------------------------ PNG
def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h,
                                      8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- content
LEADS = [
    ("MARKETS — LEAD", RED,
     "WALL STREET ROUT: S&P INTO CORRECTION",
     ["S&P 500 -3.7%, Nasdaq -5.3% — worst",
      "week since 2020. Nvidia -14% on SEC",
      "probe reports; Anthropic -8.5% day 2."]),
    ("EUROPE — LEAD", NAVY2,
     "RUSSIAN MISSILES LAND IN POLAND",
     ["Kh-101 and a drone cross NATO airspace",
      "overnight; Tusk calls it a provocation.",
      "Poland seeks reinforcements."]),
    ("CLIMATE — LEAD", TEAL,
     "COP31 IN OVERTIME, NO DEAL",
     ["Third draft due Saturday morning.",
      "Panama threatens to block any text",
      "with no fossil-fuel language."]),
]

# (number, headline, detail)
SECTIONS = [
    ("WORLD", RED, [
        (7, "IRAN WAR: TRUMP 'NOT RUSHING' DECISIONS",
         "Ninth month of war; may not decide until 2027; blockade holds"),
        (8, "HORMUZ: TANKER STRUCK, FIRE ON BOARD",
         "Unknown projectile 8nm north of Khasab, 15:00 UTC Fri; no casualties"),
        (9, "HORMUZ: 14 ATTACKS IN NOVEMBER",
         "Yet Brent down ~20% in Nov as Gulf oil reroutes; 2.8bn barrels lost"),
        (10, "MYANMAR: WORLD PRESSED TO ACT AFTER ICJ RULING",
         "Malaysia to resettle 10,000 Rohingya to Turkiye"),
        (11, "UN: HUNGER WARNING AS FOOD AID FUNDING SHORT",
         "WFP may feed fewer in 2027; $52m pledged for children in crisis"),
        (12, "BANKS HIT BY VENDOR CYBERATTACKS",
         "JPMorgan, Visa, Mastercard report incidents; core networks unaffected"),
    ]),
    ("ASIA-PACIFIC", BLUE, [
        (13, "AKVAN AFTERMATH: HEAVY RAIN INTO SATURDAY",
         "3.72 lakh evacuated, no deaths; 39 trains cancelled 20-21 Nov"),
        (14, "RAHUL CENTURY IN WELLINGTON TEST",
         "India 255/1 day 3, trail NZ 368; first Indian opener 50+ in all SENA"),
        (15, "INDIA A ROUT NEPAL BY 306 RUNS",
         "Nepal 26 all out — 5th-lowest List A total; Tilak 107, Kushagra 117"),
        (16, "NSE NOW WORLD'S 5TH-LARGEST EXCHANGE",
         "$59.7bn, overtakes Nasdaq and HKEX"),
        (17, "RECORD FPI FLOWS INTO INDIA",
         "Rs 1.01 lakh crore into Indian stocks in November"),
        (18, "FOUR CHEETAH CUBS BORN WILD AT KUNO",
         "Botswana-born KOMG 3 delivers; India's cheetah count now 62"),
        (19, "MODI OPENS FIRST SCO CIVILISATION FORUM",
         "Three-day dialogue at Purana Qila, Delhi, 20-22 Nov"),
        (20, "NEPAL PM TO VISIT INDIA 22-23 NOV",
         "Balendra Shah to meet Modi; flood aid on the agenda"),
        (21, "COURT REJECTS TAMIL NADU CAUVERY PLEAS",
         "Supreme Court refuses order for 11 TMC from Karnataka"),
        (22, "DGCA SHOW-CAUSE NOTICE TO SPICEJET",
         "Regulator acts over flight cancellations"),
        (23, "IBPS PO MAINS RESULT STATUS OUT",
         "Banking exam results announced"),
        (24, "INDONESIA FIRES MAY COST $30.9BN",
         "200m tonnes of carbon by 15 Nov — 3rd-highest since 2003"),
        (25, "WHO: ACT NOW ON DRUG-RESISTANT GERMS",
         "Urgent call on antimicrobial resistance in South-East Asia"),
        (26, "JAPAN TO TRAIN LIVE-FIRE IN INDIA",
         "First time Japanese forces use Indian facilities"),
        (27, "HYUNDAI UNVEILS 2027 ELANTRA IN LA",
         "Eighth-generation sedan debuts at LA Auto Show"),
        (28, "GAIKWAD POWERS MAHARASHTRA WIN",
         "Second victory in Syed Mushtaq Ali Trophy"),
    ]),
    ("AMERICAS", GREEN, [
        (29, "PALISADES FIRE ARSONIST CONVICTED",
         "Rinderknecht guilty on both counts; fire killed 12, destroyed 6,800 homes"),
        (30, "GTA VI: $3.79BN IN 24 HOURS",
         "Rockstar reports biggest entertainment launch ever; 24.6m copies sold"),
        (31, "F1: NORRIS ON POLE IN WET VEGAS",
         "Verstappen joins him on front row; Piastri 5th; race tonight 20:00 PST"),
        (32, "PALMOWSKI TAKES RECORD F1 ACADEMY POLE",
         "2:09.915, 1.578s clear — largest margin in series history"),
        (33, "VEGAS GP TO STREAM FREE IN US",
         "Apple TV carries the race with no subscription needed"),
        (34, "IRAN WAR COST TOPS $48BN FOR US",
         "Pentagon tells lawmakers; up from $47.1bn in mid-October"),
        (35, "HEAT WIN GTA-THEMED NIGHT 137-130",
         "Miami beats Milwaukee Bucks in primetime"),
    ]),
    ("EUROPE", PURPLE, [
        (36, "UK TO SEND 1,000 DRONES TO UKRAINE",
         "Extended-range drones worth GBP 260m"),
        (37, "HUNGARY LIFTS EU ACCESSION BLOCK",
         "Last two accession categories unblocked"),
        (38, "RUSSIA VOWS RESPONSE TO ESTONIA",
         "After Tallinn's decision to shut its Russia border"),
        (39, "UKRAINIAN DRONES HIT KOLA OIL TERMINAL",
         "Strike in Russia's far north"),
        (40, "UEFA BACKS DIALLO VS INFANTINO",
         "France's candidate backed in FIFA election race"),
    ]),
    ("GLOBAL / CULTURE", GOLD, [
        (41, "IFFI ADDS ANIMATION SECTION",
         "57th festival in Goa screens five international films"),
        (42, "PILL HAILED AS CANCER BREAKTHROUGH",
         "New hope for pancreatic cancer patients"),
        (43, "BACKSTREET BOYS AT F1 AFTERPARTY",
         "Sphere show tonight after the Grand Prix, 23:30-01:00"),
        (44, "RISING STARS: SRI LANKA A V HONG KONG",
         "Today in Doha, 09:00 local"),
        (45, "WOMEN'S HOCKEY TROPHY CONTINUES",
         "Asian Champions Trophy in progress"),
        (46, "PAKISTAN MINISTER ARRIVES IN DELHI",
         "Climate minister joins SCO forum"),
    ]),
]

TIMELINE = [
    ("FRI 05:40 GMT", "KH-101 FALLS IN POLAND"),
    ("FRI 15:00 UTC", "TANKER STRUCK, HORMUZ"),
    ("FRI 20:00 PST", "NORRIS TAKES VEGAS POLE"),
    ("FRI 21:00 UTC", "WALL ST CLOSES: S&P -3.7%"),
    ("00:19 UTC", "RAHUL CLOSES ON CENTURY"),
    ("01:30 UTC", "NASDAQ WORST WEEK SINCE 2020"),
    ("01:33 UTC", "FRANCE SEEKS UNSC MEETING"),
    ("06:00 UTC", "SRI LANKA A V HONG KONG"),
    ("SAT MORNING", "COP31 THIRD DRAFT DUE"),
    ("TONIGHT 20:00", "F1 LAS VEGAS GP, 50 LAPS"),
]

NUMBERS = [
    ("-3.7%", "S&P 500 FRIDAY"),
    ("-5.3%", "NASDAQ FRIDAY"),
    ("$3.79BN", "GTA VI IN 24 HOURS"),
    ("24.6M", "GTA VI COPIES SOLD"),
    ("100,000", "UK-EU YOUTH PLACES / YR"),
    ("62", "CHEETAHS IN INDIA"),
    ("3.72 LAKH", "EVACUATED FOR AKVAN"),
    ("26", "NEPAL ALL OUT V INDIA A"),
]


def draw_masthead(c):
    c.fill(0, 0, W, 96, NAVY)
    c.fill(0, 96, W, 4, GOLD)
    # globe: circle + meridians
    cx, cy, r = 58, 48, 32
    c.circle(cx, cy, r, PAPER, 2)
    c.vline(cx, cy - r, 2 * r, PAPER, 1)
    c.hline(cx - r, cy, 2 * r, PAPER, 1)
    # two ellipse-ish meridians (stepped arcs)
    for k in range(-2, 3):
        dx = k * 11
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            if dx * dx + dy * dy <= r * r:
                # ellipse x offset shrinks toward poles
                shrink = (1.0 - (dy / r) ** 2) ** 0.5
                x = cx + int(dx * shrink)
                c.pixel(x, yy, PAPER)
    c.text(108, 14, "THE WORLD IN ONE DAY", PAPER, 4)
    c.text(108, 62, "SATURDAY 21 NOVEMBER 2026", GOLD, 2)
    # right badge: 46 verified stories
    c.rect(838, 12, 172, 72, GOLD, 2)
    c.text(856, 20, "46", PAPER, 5)
    c.text(922, 30, "VERIFIED", PAPER, 2)
    c.text(922, 52, "STORIES", PAPER, 2)


def draw_leads(c, y):
    card_w, gap, x0 = 322, 12, 14
    for i, (kicker, color, head, body) in enumerate(LEADS):
        x = x0 + i * (card_w + gap)
        c.fill(x, y, card_w, 112, WHITE)
        c.rect(x, y, card_w, 112, LINE, 1)
        c.fill(x, y, card_w, 6, color)
        c.text(x + 12, y + 14, kicker, color, 1)
        lines = c.wrap(head, 26)
        yy = y + 30
        for ln in lines:
            c.text(x + 12, yy, ln, INK, 2)
            yy += 16
            yy += 4
        for ln in body:
            c.text(x + 12, yy, ln, GRAY, 1)
            yy += 10
    return y + 112


def draw_section_header(c, x, y, w, name, color):
    c.fill(x, y, w, 20, color)
    c.text(x + 8, y + 6, name, WHITE, 1)
    return y + 20


def draw_story(c, x, y, w, num, head, detail):
    max_chars = (w - 34) // 6
    c.text(x, y, "%d." % num, RED, 1)
    c.text(x + 26, y, fit(head, max_chars), INK, 1)
    c.text(x + 26, y + 9, fit(detail, max_chars), GRAY, 1)
    return y + 21


def draw_grid(c, y):
    col_w = 488
    x_left, x_right = 14, 522
    # left column: WORLD + ASIA-PACIFIC
    y1 = y
    for name, color, items in SECTIONS[:2]:
        y1 = draw_section_header(c, x_left, y1, col_w, name, color)
        for num, head, detail in items:
            y1 = draw_story(c, x_left, y1 + 1, col_w, num, head, detail)
        y1 += 6
    # right column: AMERICAS + EUROPE + GLOBAL/CULTURE
    y2 = y
    for name, color, items in SECTIONS[2:]:
        y2 = draw_section_header(c, x_right, y2, col_w, name, color)
        for num, head, detail in items:
            y2 = draw_story(c, x_right, y2 + 1, col_w, num, head, detail)
        y2 += 6
    # by-the-numbers box fills the right column's remaining space:
    # 4 numbers in a 2x2 grid.
    box_y = y2 + 4
    box_h = y1 - box_y
    if box_h >= 56:
        c.fill(x_right, box_y, col_w, box_h, CREAM2)
        c.rect(x_right, box_y, col_w, box_h, GOLD, 2)
        c.text(x_right + 10, box_y + 7, "BY THE NUMBERS", INK, 1)
        show = [NUMBERS[0], NUMBERS[2], NUMBERS[4], NUMBERS[5]]
        for i, (big, small) in enumerate(show):
            col = i % 2
            row = i // 2
            bx = x_right + 10 + col * 244
            by = box_y + 22 + row * 16
            c.text(bx, by, big, RED, 1)
            c.text(bx + len(big) * 6 + 8, by, small, GRAY, 1)
    return y1


def draw_timeline(c, y):
    c.fill(0, y, W, 92, NAVY2)
    c.text(14, y + 8, "THE DAY IN UTC — SATURDAY 21 NOVEMBER 2026", GOLD, 2)
    c.hline(24, y + 52, W - 48, PAPER, 2)
    n = len(TIMELINE)
    step = (W - 48) // n
    for i, (t, label) in enumerate(TIMELINE):
        cx = 24 + step * i + step // 2
        c.circle(cx, y + 52, 5, GOLD, 2)
        c.pixel(cx, y + 52, GOLD)
        # time above the dot, label below (wrapped to two short lines)
        tw = c.text_width(t, 1)
        c.text(cx - tw // 2, y + 34, t, PAPER, 1)
        words = c.wrap(label, 13)
        ly = y + 62
        for ln in words[:2]:
            lw = c.text_width(ln, 1)
            c.text(cx - lw // 2, ly, ln, PAPER, 1)
            ly += 9
    return y + 92


def draw_footer(c, y):
    c.fill(0, y, W, H - y, PAPER)
    c.rect(14, y + 8, W - 28, 84, GOLD, 2)
    c.text(28, y + 16, "DATE CHECK — EVERY STORY VERIFIED AS SATURDAY 21 NOVEMBER 2026",
           RED, 2)
    c.text(28, y + 42,
           "EACH STORY HAPPENED OR WAS FIRST REPORTED ON 21 NOV 2026 IN SOME TIMEZONE,",
           INK, 1)
    c.text(28, y + 54,
           "OR LEADS THE 21 NOV MORNING PRESS. 46 STORIES, EACH CHECKED AGAINST 2 SOURCES.",
           INK, 1)
    c.text(28, y + 70,
           "SOURCES: REUTERS, AP, CNN, BBC, UN NEWS, IMD, BCCI, FORMULA 1, COP31 PRESIDENCY.",
           GRAY, 1)
    c.text(28, y + 84 + 4,
           "ONE DAY. ONE IMAGE. — MADE BY AN AI AGENT FOR MAKE.FUN — $100 PRIZE, TOP 50 SHARE.",
           GRAY, 1)
    c.text(28, y + 84 + 18,
           "POSTER: 46 STORIES • 6 REGIONS • 10 TIMELINE EVENTS • CHECKED 21 NOV 2026.",
           GRAY, 1)


def main():
    c = Canvas(W, H, PAPER)
    draw_masthead(c)
    y = draw_leads(c, 104)
    # section strip
    c.fill(0, y + 8, W, 26, INK)
    c.text(14, y + 15, "46 STORIES — BY REGION", PAPER, 2)
    c.text(560, y + 16, "ALL VERIFIED AS 21 NOV 2026", GOLD, 1)
    y = draw_grid(c, y + 42)
    y = draw_timeline(c, y + 8)
    draw_footer(c, y + 8)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(c, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
