#!/usr/bin/env python3
"""bento: invent bento layouts and soft shapes that nobody has shipped yet.

  bento.py invent --tiles "profile:3,music:2,guestbook:2,stats:1,photos:2,now:1"
                  [--cols 6] [--seed 7] [--style sticker|trail|device|scatter] [--html out.html] [--n 3]
  bento.py shapes [--names cookie9,scallop12,flower6,clover4,hex,pentagon,squircle,heart,cloud,blob]
                  [--points 72] [--css]

invent
  Packs weighted tiles into a CSS grid with uneven spans, then rejects anything
  that looks like a stock bento (all equal tiles, 2x2 quadrants, 3 equal columns,
  perfect mirror symmetry) or repeats a layout already in taste memory. Each
  result gets flourishes chosen by style:
    sticker  tilted tiles, tape, one tile breaks the grid edge, one shaped tile
    trail    blushie style: numbered cards alternate along a doodled wavy spine
    device   ivy.rest / lwsg style: tiles inside a bezel with a notch, widget shapes
    scatter  pinboard: tiles keep the grid for reading order but rotate and overlap
  Output: grid-template-areas CSS, a layout signature, and with --html a preview
  page that uses assets/cute-tokens.css.

shapes
  Smooth M3 Expressive style shapes as clip-path polygons, all with the same
  point count so any two can morph with a plain CSS transition (blushie's
  number badges, ivy.rest's stat badges).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS = os.path.join(HERE, "..", "assets", "cute-tokens.css")
MEMORY = os.path.expanduser(os.environ.get("CUTECORE_MEMORY", "~/.claude/cutecore/taste.json"))

# ------------------------------------------------------------------ shapes

def _shape_r(name, th, rnd):
    n = int("".join(c for c in name if c.isdigit()) or 0)
    base = name.rstrip("0123456789")
    if base == "cookie":
        return 1 + 0.07 * math.cos((n or 9) * th)
    if base == "scallop":
        return 0.9 + 0.1 * abs(math.cos((n or 12) * th / 2)) ** 0.6
    if base == "flower":
        return 0.78 + 0.22 * (0.5 + 0.5 * math.cos((n or 6) * th)) ** 0.7
    if base == "clover":
        return 0.8 + 0.2 * abs(math.cos((n or 4) * th / 2)) ** 0.5
    if base in ("hex", "pentagon", "tri", "square"):
        k = {"hex": 6, "pentagon": 5, "tri": 3, "square": 4}[base]
        seg = 2 * math.pi / k
        a = (th + math.pi / 2) % seg - seg / 2
        poly = math.cos(math.pi / k) / math.cos(a)
        return 0.72 * poly + 0.28 * 0.92  # rounded corners by mixing with a circle
    if base == "squircle":
        c, s = abs(math.cos(th)), abs(math.sin(th))
        return 1 / ((c ** 4 + s ** 4) ** 0.25)
    if base == "blob":
        return 1 + sum(rnd[i] * 0.06 * math.cos((i + 2) * th + rnd[i + 4] * 6) for i in range(4))
    raise ValueError(name)


def shape(name, points=72, seed=1):
    rnd = random.Random(seed)
    coeffs = [rnd.uniform(-1, 1) for _ in range(8)]
    pts = []
    if name == "heart":
        for i in range(points):
            t = 2 * math.pi * i / points
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((x / 17, -y / 17 + 0.08))
    elif name == "cloud":
        for i in range(points):
            th = 2 * math.pi * i / points
            r = 0.8 + 0.12 * abs(math.sin(3.5 * th)) ** 0.5
            pts.append((r * math.cos(th) * 1.0, r * math.sin(th) * 0.78))
    else:
        for i in range(points):
            th = 2 * math.pi * i / points - math.pi / 2
            r = _shape_r(name, th, coeffs)
            pts.append((r * math.cos(th), r * math.sin(th)))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    sx, sy = max(xs) - min(xs), max(ys) - min(ys)
    s = max(sx, sy)
    return [((x - min(xs) + (s - sx) / 2) / s * 100, (y - min(ys) + (s - sy) / 2) / s * 100) for x, y in pts]


def clip_path(name, points=72):
    return "polygon(" + ", ".join(f"{x:.1f}% {y:.1f}%" for x, y in shape(name, points)) + ")"


DEFAULT_SHAPES = "cookie9,scallop12,flower6,clover4,hex,pentagon,squircle,heart,cloud,blob"

# ------------------------------------------------------------------ layout

def parse_tiles(spec):
    tiles = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, w = part.partition(":")
        tiles.append((name.strip().replace(" ", "-"), max(1, int(w or 1))))
    return tiles


SPAN_OPTIONS = {1: [(1, 1), (2, 1), (1, 2)], 2: [(2, 2), (3, 1), (2, 1), (1, 2)], 3: [(3, 2), (2, 3), (4, 2), (3, 3)], 4: [(4, 2), (3, 3), (4, 3), (6, 2)]}


def pack(tiles, cols, rnd):
    grid = []  # rows of names

    def fits(r, c, w, h):
        if c + w > cols:
            return False
        for rr in range(r, r + h):
            while rr >= len(grid):
                grid.append(["."] * cols)
            if any(grid[rr][cc] != "." for cc in range(c, c + w)):
                return False
        return True

    placed = []
    order = sorted(tiles, key=lambda t: -t[1]) if rnd.random() < 0.5 else tiles[:]
    for name, weight in order:
        opts = SPAN_OPTIONS[min(weight, 4)][:]
        rnd.shuffle(opts)
        done = False
        for w, h in opts:
            w = min(w, cols)
            for r in range(0, 40):
                starts = list(range(cols))
                rnd.shuffle(starts) if rnd.random() < 0.3 else None
                for c in starts:
                    if fits(r, c, w, h):
                        for rr in range(r, r + h):
                            for cc in range(c, c + w):
                                grid[rr][cc] = name
                        placed.append((name, r, c, w, h))
                        done = True
                        break
                if done:
                    break
            if done:
                break
    # fill holes by growing neighbours to the right/left so no dead cells remain
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == ".":
                if c > 0 and row[c - 1] != ".":
                    row[c] = row[c - 1]
                elif r > 0:
                    row[c] = grid[r - 1][c]
    return grid, placed


def rectangular(grid):
    """grid-template-areas requires every name to form a rectangle."""
    seen = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            seen.setdefault(v, []).append((r, c))
    for v, cells in seen.items():
        rs = [x[0] for x in cells]; cs = [x[1] for x in cells]
        if len(cells) != (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1):
            return False
    return True


def signature(grid):
    norm, ids = [], {}
    for row in grid:
        norm.append("".join(chr(97 + ids.setdefault(v, len(ids))) for v in row))
    return hashlib.sha1("/".join(norm).encode()).hexdigest()[:10]


def cliche(grid, placed):
    sizes = {(w, h) for _, _, _, w, h in placed}
    if len(sizes) == 1:
        return "all tiles the same size"
    if [row[::-1] for row in grid] == grid:
        return "mirror symmetric"
    rows, cols = len(grid), len(grid[0])
    if rows == 2 and len(placed) == 4 and all(w == cols // 2 for _, _, _, w, _ in placed):
        return "2x2 quadrants"
    if all(h == 1 for *_, h in placed) and len({w for *_, w, _ in placed}) == 1:
        return "equal columns"
    return None


def final_square(grid):
    """tiles whose final footprint (after hole filling) is a small square: safe for shapes."""
    box = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            b = box.setdefault(v, [r, c, r, c]); b[0] = min(b[0], r); b[1] = min(b[1], c); b[2] = max(b[2], r); b[3] = max(b[3], c)
    return [v for v, (r0, c0, r1, c1) in box.items() if (r1 - r0) == (c1 - c0) and (r1 - r0) <= 1]


def remembered():
    try:
        return {f.get("layout") for f in json.load(open(MEMORY)).get("fingerprints", [])}
    except Exception:
        return set()


def invent(tiles, cols, seed, style, tries=400):
    rnd = random.Random(seed)
    seen = remembered()
    for _ in range(tries):
        grid, placed = pack(tiles, cols, rnd)
        if not rectangular(grid):
            continue
        why = cliche(grid, placed)
        sig = signature(grid)
        if why or sig in seen:
            continue
        flourishes = {}
        names = [p[0] for p in placed]
        if style in ("sticker", "scatter"):
            for n in names:
                if rnd.random() < (0.45 if style == "sticker" else 0.9):
                    t = round(rnd.choice([-1, 1]) * rnd.uniform(0.8, 2.4), 1)
                    flourishes.setdefault(n, {})["tilt"] = t
            flourishes.setdefault(rnd.choice(names), {})["tape"] = True
            flourishes.setdefault(rnd.choice(names), {})["breakout"] = rnd.choice(["top", "right", "left"])
            square = final_square(grid)
            if square:
                flourishes.setdefault(rnd.choice(square), {})["shape"] = rnd.choice(["cookie9", "scallop12", "flower6", "clover4", "squircle"])
        if style == "device":
            for n in final_square(grid):
                flourishes.setdefault(n, {})["shape"] = rnd.choice(["hex", "pentagon", "cookie9", "squircle"])
        return {"grid": grid, "placed": placed, "signature": sig, "flourishes": flourishes, "style": style, "cols": cols, "seed": seed}
    sys.exit("bento: no fresh layout found; change --seed, --cols or tile weights")


def to_css(L):
    areas = "\n    ".join('"' + " ".join(row) + '"' for row in L["grid"])
    css = [f".cc-bento {{\n  display: grid;\n  grid-template-columns: repeat({L['cols']}, minmax(0, 1fr));\n  grid-auto-rows: minmax(96px, auto);\n  gap: 14px;\n  grid-template-areas:\n    {areas};\n}}"]
    for name, *_ in L["placed"]:
        rule = [f"grid-area: {name};"]
        f = L["flourishes"].get(name, {})
        if "tilt" in f:
            rule.append(f"rotate: {f['tilt']}deg;")
        if "breakout" in f:
            side = f["breakout"]
            rule.append({"top": "margin-top: -28px;", "right": "margin-right: -24px;", "left": "margin-left: -24px;"}[side])
        css.append(f".cc-bento > [data-tile=\"{name}\"] {{ {' '.join(rule)} }}")
    css.append("@media (max-width: 720px) { .cc-bento { grid-template-columns: 1fr 1fr; grid-template-areas: none; } .cc-bento > * { grid-area: auto !important; rotate: none !important; margin: 0 !important; } }")
    return "\n".join(css)


def trail_html(tiles, seed):
    """blushie style feature trail: alternating cards along a wavy spine."""
    rnd = random.Random(seed)
    cards = []
    flavours = ["sky", "ink", "pink", "paper", "blue"]
    for i, (name, w) in enumerate(tiles):
        side = "left" if i % 2 == 0 else "right"
        shape_a, shape_b = rnd.choice(["cookie9", "scallop12", "flower6"]), rnd.choice(["clover4", "hex", "squircle"])
        cards.append(f'<article class="cc-trail-card {side} f-{flavours[i % len(flavours)]}" style="--s:{clip_path(shape_a)};--h:{clip_path(shape_b)}">'
                     f'<div class="cc-trail-num"><span>{i + 1}</span></div><h3>{name.replace("-", " ").title()}</h3>'
                     f'<p>Put a working miniature of {name.replace("-", " ")} here, not a picture of it.</p><div class="cc-demo"></div></article>')
    n = len(tiles)
    pts = " ".join(f"{30 + 22 * math.sin(i * 1.7 + rnd.random()):.1f},{i * 100 / max(n * 2, 1):.1f}" for i in range(n * 2 + 1))
    path = "M" + pts.split(" ")[0] + " " + " ".join("T" + p for p in pts.split(" ")[1:])
    return f'''<section class="cc-trail">
  <svg class="cc-trail-spine" viewBox="0 0 60 100" preserveAspectRatio="none" aria-hidden="true" data-cutecore="doodle"><path d="{path}" fill="none" stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>
  {"".join(cards)}
</section>
<style>
.cc-trail {{ position: relative; display: grid; grid-template-columns: 1fr 1fr; column-gap: 72px; row-gap: 28px; max-width: 1080px; margin: 0 auto; }}
.cc-trail-spine {{ position: absolute; left: 50%; width: 60px; margin-left: -30px; top: 80px; bottom: 40px; height: calc(100% - 120px); overflow: visible; }}
.cc-trail-card {{ position: relative; z-index: 1; border-radius: 40px; padding: 32px; transition: border-radius .6s var(--ease-jelly); }}
.cc-trail-card:hover {{ border-radius: 28px; }}
.cc-trail-card.left {{ grid-column: 1; }} .cc-trail-card.right {{ grid-column: 2; margin-top: 90px; }}
.cc-trail-card h3 {{ font: 700 clamp(1.6rem, 3vw, 2.4rem)/1.06 var(--font-display); margin: 14px 0 10px; }}
.cc-trail-num {{ width: 54px; height: 54px; display: grid; place-items: center; clip-path: var(--s); background: var(--text); color: var(--accent-soft); font: 700 1.3rem var(--font-display); transition: clip-path .8s var(--ease-jelly), rotate .8s var(--ease-jelly); }}
.cc-trail-card:hover .cc-trail-num {{ clip-path: var(--h); rotate: 90deg; }}
.cc-trail-card:hover .cc-trail-num span {{ display: inline-block; rotate: -90deg; }}
.cc-demo {{ margin-top: 18px; min-height: 120px; border-radius: 22px; background: color-mix(in srgb, currentColor 8%, transparent); }}
.f-sky {{ background: var(--alt-2); color: var(--text); }} .f-ink {{ background: var(--text); color: var(--bg); }} .f-ink .cc-trail-num {{ background: var(--accent-soft); color: var(--text); }}
.f-pink {{ background: var(--accent-soft); color: var(--text); }} .f-paper {{ background: var(--paper); color: var(--text); border: 2px solid var(--border); }} .f-blue {{ background: var(--accent); color: var(--bg); }} .f-blue .cc-trail-num {{ background: var(--bg); color: var(--accent); }}
@media (max-width: 760px) {{ .cc-trail {{ grid-template-columns: 1fr; }} .cc-trail-card.right {{ grid-column: 1; margin-top: 0; }} .cc-trail-spine {{ display: none; }} }}
</style>'''


def preview(L, tiles, path):
    tokens = os.path.relpath(TOKENS, os.path.dirname(os.path.abspath(path)))
    if L["style"] == "trail":
        body = trail_html(tiles, L["seed"])
    else:
        cells = []
        for name, *_ in L["placed"]:
            f = L["flourishes"].get(name, {})
            shape_css = f' style="clip-path:{clip_path(f["shape"])};display:grid;place-items:center"' if "shape" in f else ""
            tape = '<i class="tape" aria-hidden="true"></i>' if f.get("tape") else ""
            cells.append(f'<div class="cc-card" data-tile="{name}"{shape_css}>{tape}<b class="cc-display">{name.replace("-", " ")}</b></div>')
        bezel = L["style"] == "device"
        body = (('<div class="bezel"><div class="notch"></div>' if bezel else "") + f'<div class="cc-bento">{"".join(cells)}</div>' + ("</div>" if bezel else "")
                + f"<style>{to_css(L)}\n.cc-card{{padding:18px}} .tape{{position:absolute;top:-10px;left:50%;width:64px;height:20px;translate:-50% 0;rotate:-4deg;background:color-mix(in srgb,var(--alt) 70%,transparent);border-radius:3px}}"
                + ".bezel{position:relative;background:var(--text);padding:16px;border-radius:44px}.bezel .cc-bento{background:var(--bg);border-radius:30px;padding:20px}.notch{position:absolute;left:50%;top:16px;translate:-50% 0;width:110px;height:24px;background:var(--text);border-radius:0 0 16px 16px;z-index:2}</style>")
    html = f'''<!doctype html><html data-flavor="cotton"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bento {L["signature"]}</title><link rel="stylesheet" href="{tokens}"></head>
<body style="padding:48px 16px"><main style="max-width:1100px;margin:0 auto">{body}</main></body></html>'''
    with open(path, "w") as fh:
        fh.write(html)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("invent")
    p.add_argument("--tiles", required=True); p.add_argument("--cols", type=int, default=6); p.add_argument("--seed", type=int, default=None)
    p.add_argument("--style", default="sticker", choices=["sticker", "trail", "device", "scatter"]); p.add_argument("--html"); p.add_argument("--n", type=int, default=1)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("shapes"); p.add_argument("--names", default=DEFAULT_SHAPES); p.add_argument("--points", type=int, default=72); p.add_argument("--css", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "shapes":
        for n in a.names.split(","):
            n = n.strip()
            if a.css:
                print(f".shape-{n} {{ clip-path: {clip_path(n, a.points)}; }}")
            else:
                print(f"{n}: {clip_path(n, a.points)[:90]}...")
        if not a.css:
            print("\nall shapes share the point count, so `transition: clip-path .8s` morphs between any two. Use --css for full rules.")
        return
    tiles = parse_tiles(a.tiles)
    seed = a.seed if a.seed is not None else random.randrange(1 << 30)
    for i in range(a.n):
        L = invent(tiles, a.cols, seed + i * 9973, a.style)
        if a.json:
            print(json.dumps({k: v for k, v in L.items() if k != "placed"}))
        else:
            print(f"/* layout {L['signature']} style={L['style']} seed={L['seed']} */")
            print(to_css(L) if a.style != "trail" else "/* trail layout: see --html output */")
        if a.html:
            out = a.html if a.n == 1 else a.html.replace(".html", f"-{i + 1}.html")
            preview(L, tiles, out)
            print(f"/* preview: {out} */", file=sys.stderr)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
