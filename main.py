#!/usr/bin/env python3
"""news-image-20261124 (Account B / keen-panda-72).

Draws "The World in One Day" - a 1024x1024 atlas-style image summing up
Tuesday 24 November 2026 world news: a large dotted world map with 35
numbered story markers, and the 35 stories grouped by region below it.

Pure Python standard library only (zlib/struct for the PNG encoder).
Deterministic: no network, no randomness, no timestamps in the output.
Writes to $MAKEFUN_OUTPUT_DIR/entry.png, else /output/entry.png.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
BG      = (11, 27, 46)     # deep navy
PANEL   = (16, 38, 63)     # map panel
PANEL2  = (13, 32, 53)     # alt row band
ROW     = (14, 33, 56)     # row band
INK     = (242, 240, 233)  # near-white text
MUTED   = (159, 179, 200)  # muted text
GOLD    = (232, 184, 75)   # gold rule / accents
DOT     = (91, 122, 158)   # land dots
GRID    = (26, 50, 79)     # graticule
WHITE   = (255, 255, 255)
BLACK   = (5, 12, 22)

REGION_COLORS = {
    "NORTH AMERICA":   (255, 107, 74),
    "LATIN AMERICA":   (255, 197, 61),
    "EUROPE":          (78, 205, 196),
    "AFRICA":          (199, 125, 255),
    "MIDDLE EAST":     (241, 91, 181),
    "ASIA":            (76, 201, 240),
    "OCEANIA & PACIFIC": (128, 237, 153),
}

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, "1" = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
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
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            base = (yy * self.w + x) * 3
            self.px[base:base + w * 3] = bytes(color) * w

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        for yy in range(y, y + h):
            self.set(x, yy, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color):
        for a in range(360):
            import math
            x = cx + int(round(r * math.cos(math.radians(a))))
            y = cy + int(round(r * math.sin(math.radians(a))))
            self.set(x, y, color)

    def text(self, s, x, y, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, s, cx, y, scale, color):
        w = text_width(s, scale)
        return self.text(s, cx - w // 2, y, scale, color)


# ---------------------------------------------------------------- stories
# (number, region, headline, lon, lat, label-offset dx, dy)
STORIES = [
    (1, "NORTH AMERICA", "NVIDIA SHARES JUMP A THIRD AS HUANG RETURNS AS CEO", -122, 37, 0, -11),
    (2, "NORTH AMERICA", "APPEALS COURT GIVES TRUMP PATH TO ERASE HUSH-MONEY CASE", -74, 41, 0, 0),
    (3, "NORTH AMERICA", "DEMOCRATS PLAN 12 DEBATES FOR 2028 PRIMARY, FIRST IN JUNE", -96, 39, 0, 0),
    (4, "NORTH AMERICA", "WAYMO PULLS DRIVERLESS TAXIS OFF ALL US FREEWAYS", -118, 34, 0, 12),
    (5, "NORTH AMERICA", "FBI PROBES POSSIBLE BREACH OF NATIONAL CRIME DATABASE", -77, 39, 12, 0),
    (6, "LATIN AMERICA", "MEXICO ARRESTS SINALOA KINGPIN AFTER FIERCE GUN BATTLE", -104, 24, 0, 0),
    (7, "LATIN AMERICA", "COLOMBIA ASKS X TO SUSPEND EX-PRESIDENT PETRO'S ACCOUNT", -74, 5, 0, 0),
    (8, "LATIN AMERICA", "BUKELE SEEKS THIRD TERM AS EL SALVADOR PRESIDENT", -89, 14, 0, 0),
    (9, "LATIN AMERICA", "PAREDES COLLAPSES ON LIVE TV AFTER BOCA'S COPA WIN", -75, 11, 0, 12),
    (10, "EUROPE", "COP31 CLIMATE SUMMIT COLLAPSES WITH NO DEAL", 30, 37, 0, 0),
    (11, "EUROPE", "FIFA CONFIRMS 2031 AND 2035 WOMEN'S WORLD CUP HOSTS", 8, 47, 0, -16),
    (12, "EUROPE", "ALCARAZ WINS MAIDEN ATP FINALS TITLE IN TURIN", 8, 45, 0, 16),
    (13, "EUROPE", "DENMARK TOP COURT BACKS 'GHETTO LAW' RULES", 12, 56, 0, -11),
    (14, "EUROPE", "THOUSANDS FLEE MANCHESTER CONCERT AFTER SUBSTANCE RELEASED", -2, 53, 0, 0),
    (15, "EUROPE", "RUSSIAN CARGO SHIP SPARTA II BURNS AFTER DRONE STRIKE", 24, 60, 0, 0),
    (16, "EUROPE", "NATO VOWS SPACE DEFENCE AFTER RUSSIA SATELLITE REPORT", 4, 50, -18, 3),
    (17, "EUROPE", "RUSSIAN STRIKES KILL 14 IN UKRAINE'S KYIV REGION", 30, 50, 0, 0),
    (18, "AFRICA", "UKRAINE CLAIMS SINKING OF RUSSIAN WARSHIP OFF LIBYA", 15, 33, 0, 0),
    (19, "AFRICA", "MIGRANT BOAT CAPSIZES OFF SENEGAL, DOZENS MISSING", -17, 15, 0, 0),
    (20, "AFRICA", "SUDAN AIR DEFENCES INTERCEPT DRONES OVER KHARTOUM", 32, 15, 0, 0),
    (21, "MIDDLE EAST", "SETTLER ARSON HITS FIVE PALESTINIAN VILLAGES OVERNIGHT", 35, 32, 0, -16),
    (22, "MIDDLE EAST", "OXFAM: GAZA AIR, SOIL AND WATER TOXIC FOR DECADES", 34, 31, 0, 16),
    (23, "MIDDLE EAST", "IRAN VOWS 'EVERY MEANS' OVER US HORMUZ BLOCKADE THREAT", 51, 26, 16, -12),
    (24, "MIDDLE EAST", "ZELENSKYY OPEN TO PUTIN MEETING IN TURKEY", 32, 40, -16, -11),
    (25, "MIDDLE EAST", "BAHRAIN CONDEMNS IRANIAN-LED STRIKE ON CIVILIAN SITE", 50, 26, -16, 12),
    (26, "ASIA", "INDONESIA FACTORY FIRE KILLS 24, DOZENS MISSING", 106, -6, 0, 0),
    (27, "ASIA", "INDIA AND CHINA HOLD MILITARY TALKS IN ARUNACHAL", 92, 28, 13, -13),
    (28, "ASIA", "MODI OPENS AI CENTRE AT IIT PATNA, RS 400-CRORE PARK", 85, 25, 0, 15),
    (29, "ASIA", "GUKESH BEGINS WORLD CHESS TITLE DEFENCE IN GENEVA", 6, 46, 0, 0),
    (30, "ASIA", "INDIA AND NEPAL SIGN 8 DEALS AS MODI HOSTS BALEN SHAH", 85, 28, 0, -15),
    (31, "ASIA", "TALIBAN ERASES WOMEN'S NAMES FROM DOCUMENTS IN BALKH", 67, 36, 0, 0),
    (32, "ASIA", "BANGLADESH VOWS TO ARREST HASINA IF SHE RETURNS", 90, 24, 15, 11),
    (33, "OCEANIA & PACIFIC", "INDIA POST RECORD 9-720 IN DRAWN TEST VS NEW ZEALAND", 175, -41, 0, 15),
    (34, "OCEANIA & PACIFIC", "AUSTRALIA REGAIN WTC FINAL SPOT AFTER NZ-INDIA DRAW", 151, -34, 0, 0),
    (35, "OCEANIA & PACIFIC", "AUSTRALIA BEAT NZ 3-1 AS TOURE SCORES TWICE IN AUCKLAND", 175, -37, 0, -15),
]

REGIONS = ["NORTH AMERICA", "LATIN AMERICA", "EUROPE", "AFRICA",
           "MIDDLE EAST", "ASIA", "OCEANIA & PACIFIC"]

# Rough land boxes: (lon_min, lon_max, lat_min, lat_max)
LAND = [
    (-168, -125, 49, 72), (-125, -95, 30, 60), (-125, -66, 24, 50),
    (-95, -60, 7, 32), (-60, -20, 60, 84),
    (-80, -35, -56, 12),
    (-11, 32, 36, 70),
    (-18, 50, -35, 32), (43, 51, -26, -12),
    (40, 180, 40, 77), (60, 105, 5, 40), (100, 145, 5, 55),
    (95, 141, -11, 7), (35, 60, 12, 42),
    (113, 154, -40, -10), (166, 179, -47, -34),
]

MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = 12, 86, 1012, 348


def lon_to_x(lon):
    return MAP_X0 + int((lon + 180) / 360.0 * (MAP_X1 - MAP_X0))


def lat_to_y(lat):
    # map covers lat 84 down to -58
    return MAP_Y0 + int((84 - lat) / 142.0 * (MAP_Y1 - MAP_Y0))


def is_land(lon, lat):
    for lo0, lo1, la0, la1 in LAND:
        if lo0 <= lon <= lo1 and la0 <= lat <= la1:
            return True
    return False


# ---------------------------------------------------------------- drawing
def draw_map(cv):
    cv.rect(MAP_X0, MAP_Y0, MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0, PANEL)
    # graticule every 30 degrees
    for lon in range(-180, 181, 30):
        x = lon_to_x(lon)
        cv.vline(x, MAP_Y0, MAP_Y1 - MAP_Y0, GRID)
    for lat in range(-60, 91, 30):
        y = lat_to_y(lat)
        cv.hline(MAP_X0, y, MAP_X1 - MAP_X0, GRID)
    # land dots every 3 degrees
    lon = -180
    while lon <= 180:
        lat = -57
        while lat <= 84:
            if is_land(lon, lat):
                x, y = lon_to_x(lon), lat_to_y(lat)
                cv.rect(x - 1, y - 1, 3, 3, DOT)
            lat += 3
        lon += 3
    # numbered story markers
    cv.text("NUMBERED DOTS SHOW WHERE EACH STORY HAPPENED",
            MAP_X1 - 24 - text_width(
                "NUMBERED DOTS SHOW WHERE EACH STORY HAPPENED", 1),
            MAP_Y0 + 6, 1, MUTED)
    for num, region, _headline, lon, lat, dx, dy in STORIES:
        x, y = lon_to_x(lon), lat_to_y(lat)
        color = REGION_COLORS[region]
        if dx or dy:
            # leader line from true spot to offset marker
            mx, my = x + dx, y + dy
            steps = max(abs(dx), abs(dy), 1)
            for i in range(steps + 1):
                cv.set(x + (mx - x) * i // steps,
                       y + (my - y) * i // steps, color)
            x, y = mx, my
        cv.circle(x, y, 8, color)
        cv.ring(x, y, 8, WHITE)
        cv.text_center(str(num), x, y - 3, 1, WHITE)


def draw_header(cv):
    cv.text("THE WORLD IN ONE DAY", 24, 14, 4, INK)
    cv.text("TUESDAY 24 NOVEMBER 2026", 24, 50, 3, GOLD)
    right = "35 STORIES  -  7 REGIONS"
    cv.text(right, W - 24 - text_width(right, 2), 20, 2, MUTED)
    cv.text("ONE DAY. THE WHOLE WORLD.", W - 24 - text_width(
        "ONE DAY. THE WHOLE WORLD.", 1), 48, 1, MUTED)
    cv.hline(12, 80, W - 24, GOLD)
    cv.hline(12, 82, W - 24, GOLD)


def draw_regions(cv):
    y0 = 356
    row_h = 90
    for i, region in enumerate(REGIONS):
        y = y0 + i * row_h
        band = ROW if i % 2 == 0 else PANEL2
        cv.rect(12, y, W - 24, row_h - 3, band)
        color = REGION_COLORS[region]
        cv.rect(12, y, 8, row_h - 3, color)
        stories = [s for s in STORIES if s[1] == region]
        cv.text(region, 30, y + 6, 2, color)
        cv.text("%d STORIES" % len(stories),
                W - 24 - text_width("%d STORIES" % len(stories), 1),
                y + 9, 1, MUTED)
        # two columns of numbered headlines
        half = (len(stories) + 1) // 2
        cols = [stories[:half], stories[half:]]
        line_h = 14
        for c, col in enumerate(cols):
            cx = 30 if c == 0 else 520
            for j, (num, _r, headline, _lo, _la, _dx, _dy) in enumerate(col):
                ly = y + 30 + j * line_h
                cv.text("%d." % num, cx, ly, 1, color)
                cv.text(headline, cx + 22, ly, 1, INK)


def draw_footer(cv):
    cv.hline(12, 992, W - 24, GOLD)
    cv.text("ALL 35 STORIES WERE REPORTED ON TUESDAY 24 NOVEMBER 2026.",
            24, 1002, 1, MUTED)
    cv.text("SOURCES: REUTERS, BBC, CNN, AP, FIFA, OXFAM.",
            W - 24 - text_width("SOURCES: REUTERS, BBC, CNN, AP, FIFA, OXFAM.", 1),
            1002, 1, MUTED)


# ---------------------------------------------------------------- PNG out
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = b""
    for y in range(cv.h):
        raw += b"\x00" + bytes(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    data = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    cv = Canvas(W, H, BG)
    draw_header(cv)
    draw_map(cv)
    draw_regions(cv)
    draw_footer(cv)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
