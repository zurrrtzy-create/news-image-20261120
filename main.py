#!/usr/bin/env python3
"""One-day world news front page for Friday 20 November 2026.

Pure Python 3.13 standard library only: a hand-written 5x7 bitmap font, a
small vector drawing layer, and a minimal PNG encoder (zlib + struct).
No network, no randomness, no wall-clock time: the same input always
produces the same bytes.

Reads MAKEFUN_OUTPUT_DIR (default /output) and writes entry.png there,
1024x1024 RGB, well under the 1 MiB cap.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)   # warm newsprint
PANEL = (255, 253, 246)   # card white
INK = (18, 32, 56)        # deep navy
RED = (178, 44, 36)       # lead red
GOLD = (176, 141, 44)     # masthead rule
SLATE = (64, 74, 90)      # body grey-blue
TEAL = (23, 94, 94)       # climate accent
LIGHT = (226, 231, 238)   # pictogram wash

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = on. Authored for this entry.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def text_width(s, scale):
    return len(s) * 6 * scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                i = base + (xx - max(0, x)) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color, t=2):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, t=2):
        x, y, d = r, 0, 1 - r
        while x >= y:
            for px, py in ((cx + x, cy + y), (cx + y, cy + x),
                           (cx - y, cy + x), (cx - x, cy + y),
                           (cx - x, cy - y), (cx - y, cy - x),
                           (cx + y, cy - x), (cx + x, cy - y)):
                for a in range(t):
                    for b in range(t):
                        self.set(px + a, py + b, color)
            y += 1
            if d <= 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1

    def arc(self, cx, cy, r, a0, a1, color, t=2):
        steps = max(8, int(abs(a1 - a0) * r / 4))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            for p in range(t):
                for q in range(t):
                    self.set(x + p, y + q, color)

    def ellipse(self, cx, cy, rx, ry, color, t=2):
        steps = max(24, int(2 * math.pi * max(rx, ry) / 3))
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            x = int(round(cx + rx * math.cos(a)))
            y = int(round(cy + ry * math.sin(a)))
            for p in range(t):
                for q in range(t):
                    self.set(x + p, y + q, color)

    def fill_circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            half = int(round(math.sqrt(max(0, r * r - (yy - cy) ** 2))))
            self.fill_rect(cx - half, yy, 2 * half + 1, 1, color)

    # -- text -------------------------------------------------------------
    def char(self, ch, x, y, scale, color):
        glyph = FONT.get(ch, FONT["?"])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "#":
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def text(self, s, x, y, scale, color):
        s = s.upper()  # the font holds capitals, digits and punctuation only
        for ch in s:
            self.char(ch, x, y, scale, color)
            x += 6 * scale

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)

    def wrap(self, s, max_w, scale):
        lines, cur = [], ""
        for word in s.split(" "):
            trial = (cur + " " + word).strip()
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------- pictograms
def pic_cyclone(cv, x, y, s):
    """Spiral storm: concentric broken arcs + rain slashes."""
    cx, cy = x + s // 2, y + s // 2 - 6
    for i, r in enumerate((18, 34, 50, 66, 80)):
        start = 0.4 * i + 0.3
        cv.arc(cx, cy, r, start, start + 4.4, INK, 3)
    cv.arc(cx, cy, 8, 0.0, 5.6, RED, 3)
    for rx in (-70, -30, 10, 50):
        cv.line(cx + rx, cy + 92, cx + rx - 14, cy + 118, INK, 3)


def pic_clock(cv, x, y, s):
    """Clock face with hands + 2027 below: a decision pushed to 2027."""
    cx, cy = x + s // 2, y + s // 2 - 20
    cv.circle(cx, cy, 36, INK, 3)
    cv.line(cx, cy, cx - 16, cy - 18, INK, 3)
    cv.line(cx, cy, cx + 21, cy - 11, RED, 3)
    cv.fill_circle(cx, cy, 4, RED)
    cv.text_center("2027", cx, y + s - 22, 3, INK)


def pic_talks(cv, x, y, s):
    """Two speech bubbles, EU and RU, overlapping."""
    cv.fill_rect(x + 6, y + 8, 58, 36, LIGHT)
    cv.rect(x + 6, y + 8, 58, 36, INK, 2)
    cv.line(x + 16, y + 44, x + 10, y + 58, INK, 2)
    cv.line(x + 10, y + 58, x + 30, y + 44, INK, 2)
    cv.text_center("EU", x + 35, y + 20, 2, INK)
    cv.fill_rect(x + 38, y + 56, 58, 36, PANEL)
    cv.rect(x + 38, y + 56, 58, 36, INK, 2)
    cv.line(x + 84, y + 92, x + 90, y + 106, INK, 2)
    cv.line(x + 90, y + 106, x + 70, y + 92, INK, 2)
    cv.text_center("RU", x + 67, y + 68, 2, INK)


def pic_globe(cv, x, y, s):
    """Globe with a leaf: climate talks."""
    cx, cy = x + s // 2, y + s // 2 - 8
    cv.circle(cx, cy, 38, TEAL, 3)
    cv.ellipse(cx, cy, 15, 38, TEAL, 2)
    for dy in (-19, 0, 19):
        half = int(round(math.sqrt(max(0, 38 * 38 - dy * dy))))
        cv.hline(cx - half, cy + dy, 2 * half, TEAL, 2)
    # leaf
    cv.arc(cx + 34, cy + 40, 16, math.pi * 0.9, math.pi * 2.1, INK, 3)
    cv.arc(cx + 34, cy + 40, 16, math.pi * -0.1, math.pi * 1.1, INK, 3)
    cv.line(cx + 22, cy + 52, cx + 12, cy + 62, INK, 2)


def pic_controller(cv, x, y, s):
    """Game controller."""
    cv.rect(x + 8, y + 28, 88, 48, INK, 3)
    cv.fill_rect(x + 22, y + 42, 8, 24, INK)
    cv.fill_rect(x + 14, y + 50, 24, 8, INK)
    cv.fill_circle(x + 74, y + 46, 5, RED)
    cv.fill_circle(x + 86, y + 58, 5, RED)
    cv.fill_circle(x + 52, y + 38, 3, GOLD)
    cv.fill_circle(x + 62, y + 38, 3, GOLD)


# ---------------------------------------------------------------- layout
def draw_panel(cv, x, y, w, h, kicker, headline, deck, pic):
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, INK, 2)
    pic(cv, x + w - 116, y + 16, 100)
    tx = x + 20
    cv.text(kicker, tx, y + 18, 2, RED)
    hy = y + 44
    for line in headline:
        cv.text(line, tx, hy, 3, INK)
        hy += 24
    dy = y + 112
    for line in deck:
        cv.text(line, tx, dy, 3, SLATE)
        dy += 22


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    cv = Canvas(W, H, PAPER)

    # Masthead
    cv.text_center("THE WORLD IN ONE DAY", W // 2, 26, 8, INK)
    cv.fill_rect(32, 92, W - 64, 3, GOLD)

    # Date band
    cv.fill_rect(32, 100, W - 64, 42, RED)
    cv.text_center("FRIDAY 20 NOVEMBER 2026", W // 2, 108, 5, (255, 255, 255))

    # ---- Lead: Cyclone Akvan
    lx, ly, lw, lh = 32, 158, W - 64, 312
    cv.fill_rect(lx, ly, lw, lh, PANEL)
    cv.rect(lx, ly, lw, lh, INK, 2)
    cv.text("INDIA - CYCLONE AKVAN", lx + 24, ly + 18, 3, RED)
    cv.text("AKVAN HITS", lx + 24, ly + 52, 6, INK)
    cv.text("ODISHA TODAY", lx + 24, ly + 96, 6, INK)
    lead_deck = [
        "Severe storm makes landfall near",
        "Gopalpur by noon - 50,000 people",
        "moved to safety; winds 100 km/h,",
        "gusting to 110 km/h.",
    ]
    dy = ly + 168
    for line in lead_deck:
        cv.text(line, lx + 24, dy, 3, SLATE)
        dy += 24
    pic_cyclone(cv, lx + 700, ly + 40, 220)

    # ---- Row 2: Trump / Europe
    draw_panel(cv, 32, 486, 470, 220,
               "USA - IRAN",
               ["TRUMP: 'NO RUSH'", "ON IRAN"],
               ["No decision on Iran", "before 2027, he says.",
                "Israel's envoy warns it", "may act alone."],
               pic_clock)
    draw_panel(cv, 522, 486, 470, 220,
               "UKRAINE - EUROPE",
               ["EUROPE READY FOR", "RUSSIA TALKS"],
               ["Berlin summit agrees a", "united line on ending",
                "the war; Moscow's terms", "called unrealistic."],
               pic_talks)

    # ---- Row 3: COP31 / GTA VI
    draw_panel(cv, 32, 722, 470, 220,
               "CLIMATE - COP31",
               ["COP31: FINAL DAY"],
               ["Draft deal drops all", "fossil-fuel language",
                "as Antalya talks reach", "their Friday deadline."],
               pic_globe)
    draw_panel(cv, 522, 722, 470, 220,
               "GAMES - GTA VI",
               ["GTA VI: $1.84BN", "IN A DAY"],
               ["Launch sales top The", "Odyssey's entire box",
                "office run, Sensor", "Tower estimates."],
               pic_controller)

    # ---- Ticker
    ty = 958
    cv.fill_rect(32, ty, W - 64, 42, INK)
    cv.text("SHENZHEN: 'PEACE DECLARATION' ISSUED - CRICKET: NZ 243/5 V INDIA",
            48, ty + 13, 2, (255, 255, 255))

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    write_png(path, cv)


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
