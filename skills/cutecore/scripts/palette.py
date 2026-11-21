#!/usr/bin/env python3
"""palette: make and check cutecore palettes (pink, purple, blue) with real contrast math.

  palette.py make [--seed "#f47fa6"] [--mood candy|milk|midnight|retro|dreamy] [--css] [--json]
  palette.py check "#3d2230" "#fff6f8" [...more pairs as fg bg fg bg]
  palette.py audit path/to/tokens.css        # checks text/bg role pairs it finds

`make` builds a full role set (bg, surface, paper, border, text, text-muted,
accent, accent-press, accent-soft, accent-bright, alt, alt-2, sticker-shadow) in
OKLCH so lightness steps are even, then nudges text colours until body text
reaches 7:1 and muted text 4.5:1 on the background. Output drops straight into
cute-tokens.css.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys

# ------------------------------------------------------------ colour maths

def hex2rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(c):
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02x}" for v in c)


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def luminance(h):
    r, g, b = (_lin(v) for v in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def oklch2hex(L, C, H):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    bb = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    return rgb2hex([_gam(max(0, min(1, v))) for v in (r, g, bb)])


def hex2oklch(h):
    r, g, b = (_lin(v) for v in hex2rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


MOODS = {
    #           bg L, surface, paper, border, text L, muted L, accent L/C, soft L/C, chroma scale
    "candy":   dict(bg=0.975, surf=0.945, paper=0.99, border=0.86, text=0.27, muted=0.44, acc=(0.52, 0.17), soft=(0.89, 0.06), cs=1.0, dark=False),
    "milk":    dict(bg=0.985, surf=0.96, paper=0.995, border=0.9, text=0.3, muted=0.47, acc=(0.6, 0.11), soft=(0.92, 0.035), cs=0.6, dark=False),
    "dreamy":  dict(bg=0.97, surf=0.94, paper=0.985, border=0.87, text=0.29, muted=0.46, acc=(0.56, 0.14), soft=(0.9, 0.05), cs=0.85, dark=False),
    "retro":   dict(bg=0.95, surf=0.91, paper=0.97, border=0.78, text=0.25, muted=0.42, acc=(0.55, 0.19), soft=(0.86, 0.08), cs=1.15, dark=False),
    "midnight": dict(bg=0.22, surf=0.27, paper=0.25, border=0.38, text=0.92, muted=0.76, acc=(0.82, 0.11), soft=(0.38, 0.06), cs=0.9, dark=True),
}


def make(seed="#f47fa6", mood="candy"):
    _, _, H = hex2oklch(seed)
    M = MOODS[mood]
    cs = M["cs"]
    tint = 0.018 * cs
    p = {
        "bg": oklch2hex(M["bg"], tint, H), "surface": oklch2hex(M["surf"], tint * 1.8, H), "paper": oklch2hex(M["paper"], tint * 0.6, H),
        "border": oklch2hex(M["border"], 0.06 * cs, H), "text": oklch2hex(M["text"], 0.05, H), "text-muted": oklch2hex(M["muted"], 0.06, H),
        "accent": oklch2hex(M["acc"][0], M["acc"][1] * cs, H), "accent-press": oklch2hex(M["acc"][0] - (0.12 if not M["dark"] else -0.08), M["acc"][1] * cs, H),
        "accent-soft": oklch2hex(M["soft"][0], M["soft"][1] * cs, H), "accent-bright": oklch2hex(0.74 if not M["dark"] else 0.78, 0.13 * cs, H),
        "alt": oklch2hex(M["soft"][0], M["soft"][1] * cs, (H + 300) % 360 if 330 > H > 250 else 300),  # lilac partner
        "alt-2": oklch2hex(M["soft"][0], M["soft"][1] * cs, 245),  # baby blue partner
        "sticker-shadow": oklch2hex(0.78 if not M["dark"] else 0.15, 0.08 * cs if not M["dark"] else 0.03, H),
        "sticker-rim": "#ffffff" if not M["dark"] else oklch2hex(0.5, 0.06, H),
    }
    # enforce contrast by walking text lightness away from the background
    for role, target in (("text", 7.0), ("text-muted", 4.5), ("accent", 4.5)):
        L, C, h = hex2oklch(p[role])
        step = -0.01 if not M["dark"] else 0.01
        for _ in range(60):
            if contrast(p[role], p["bg"]) >= target:
                break
            L += step
            p[role] = oklch2hex(L, C, h)
    return p


def to_css(p, selector=":root"):
    return selector + " {\n" + "".join(f"  --{k}: {v};\n" for k, v in p.items()) + "}\n"


def report(pairs):
    ok = True
    for fg, bg in pairs:
        r = contrast(fg, bg)
        grade = "AAA" if r >= 7 else "AA" if r >= 4.5 else "AA-large" if r >= 3 else "FAIL"
        ok &= r >= 4.5
        print(f"{fg} on {bg}: {r:5.2f}  {grade}")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("make"); p.add_argument("--seed", default="#f47fa6"); p.add_argument("--mood", default="candy", choices=list(MOODS))
    p.add_argument("--css", action="store_true"); p.add_argument("--json", action="store_true"); p.add_argument("--selector", default=":root")
    p = sub.add_parser("check"); p.add_argument("colors", nargs="+")
    p = sub.add_parser("audit"); p.add_argument("css")
    a = ap.parse_args(argv)
    if a.cmd == "make":
        pal = make(a.seed, a.mood)
        if a.json:
            print(json.dumps(pal, indent=2))
        else:
            print(to_css(pal, a.selector))
            report([(pal["text"], pal["bg"]), (pal["text-muted"], pal["bg"]), (pal["accent"], pal["bg"]), (pal["bg"], pal["accent"])])
    elif a.cmd == "check":
        if len(a.colors) % 2:
            sys.exit("give colours in fg bg pairs")
        sys.exit(0 if report(list(zip(a.colors[::2], a.colors[1::2]))) else 1)
    else:
        css = open(a.css).read()
        bad = False
        for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            vars_ = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,6})\b", block.group(2)))
            if "bg" in vars_:
                print(f"\n{block.group(1).strip()}")
                pairs = [(vars_[k], vars_["bg"]) for k in ("text", "text-muted", "accent") if k in vars_]
                bad |= not report(pairs)
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
