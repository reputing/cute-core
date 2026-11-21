#!/usr/bin/env python3
"""brand: lock an existing site's identity before redesigning it.

  brand.py extract <blueprint.json> [--out .cutecore/brand] [--repo .]
  brand.py show [--dir .cutecore/brand]

Reads a dissect.cjs blueprint (and, with --repo, the project's own css/tailwind
files) and writes:
  brand.json   palette roles, fonts by job, glow/shadow/filter recipes, radii,
               ornament and mascot assets, signature keyframes
  brand.md     the same as a checklist the redesign must honour
  brand.css    the brand mapped onto cute-tokens variables, so every cutecore
               primitive (stickers, stamps, cards, fields) wears the brand's
               colours, glow and type instead of the default strawberry paper

Why: a redesign of a site that already has an art direction must keep it.
The house style supplies craft (states, motion discipline, primitives, layout
invention); the brand supplies palette, type, art, mascot and mood. Variants
differ in structure and treatment, never in identity, unless the user picked a
deviation of 8+ AND said the identity itself may change.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
from collections import Counter

RGB = re.compile(r"rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)(?:[ ,/]+([\d.]+))?\s*\)")
HEX = re.compile(r"#([0-9a-fA-F]{6})\b")
DISPLAY_HINT = re.compile(r"daruma|fredoka|baloo|mochiy|chewy|cherry|dynapuff|sniglet|grandstander|pixel|silkscreen|press start|lobster|pacifico|bubblegum|titan|luckiest|bungee|modak|rubik (?:mono|bubbles)|yusei|potta|reggae|rampart|kosugi maru|hachi", re.I)
HAND_HINT = re.compile(r"mali|patrick hand|gaegu|caveat|kalam|indie flower|shadows into|nanum pen|gochi|delius|sour gummy|coming soon|comic|yomogi|klee|zen kurenaido|noteworthy|bradley", re.I)
PIXEL_HINT = re.compile(r"silkscreen|pixel|press start|vt323|dotgothic|minecraft|tiny5", re.I)


def to_hex(r, g, b):
    return "#%02x%02x%02x" % (int(r), int(g), int(b))


def parse_color(s):
    m = RGB.search(s)
    if m:
        a = float(m.group(4)) if m.group(4) else 1.0
        return to_hex(*m.groups()[:3]), a
    m = HEX.search(s)
    if m:
        return "#" + m.group(1).lower(), 1.0
    return None, 0


def hls(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, l, s


def weighted(pairs):
    c = Counter()
    for val, n in pairs:
        h, a = parse_color(val)
        if h and a >= 0.5:
            c[h] += n
    return c


def extract(bp, repo=None):
    T = bp["tokens"]
    ink = weighted(T.get("color", []))
    bgs = weighted(T.get("background", []))
    allc = ink + bgs
    for v in bp.get("cssVars", {}).values():
        h, a = parse_color(v)
        if h:
            allc[h] += 3

    # glows: coloured shadows / drop-shadows / text-shadows
    glow = Counter()
    for val, n in T.get("shadow", []) + T.get("filter", []):
        for m in RGB.finditer(val):
            h = to_hex(*m.groups()[:3])
            _, l, s = hls(h)
            if s > 0.35 and l > 0.45:
                glow[h] += n
    # theme: is the page dark? use the theme-color, then the darkest frequent bg
    dark_bgs = [c for c, _ in bgs.most_common(20) if hls(c)[1] < 0.2]
    light_ink = [c for c, _ in ink.most_common(10) if hls(c)[1] > 0.8]
    is_dark = bool(dark_bgs) and bool(light_ink) or (bp.get("meta", {}).get("themeColor") or "").lower() in ("#000", "#000000")
    if is_dark:
        tinted = [c for c in dark_bgs if hls(c)[2] > 0.25]  # a violet/navy night beats neutral black
        bg = (tinted or sorted(dark_bgs or ["#140c20"], key=lambda c: hls(c)[1]))[0]
    else:
        lights = [c for c, _ in bgs.most_common(12) if hls(c)[1] > 0.9]
        tinted = [c for c in lights if c not in ("#ffffff",) and hls(c)[2] > 0.2]
        bg = (tinted or lights or ["#fff6f8"])[0]
    text = (light_ink if is_dark else [c for c, _ in ink.most_common(10) if hls(c)[1] < 0.35] or ["#3d2230"])[0]
    muted = next((c for c, _ in ink.most_common(15) if c != text and 0.3 < hls(c)[1] < 0.8 and hls(c)[2] < 0.4), None)
    sat = [c for c, _ in (allc + glow).most_common(40) if hls(c)[2] > 0.45 and 0.45 < hls(c)[1] < 0.9]
    pinks = [c for c in sat if hls(c)[0] >= 290 or hls(c)[0] < 20]
    violets = [c for c in sat if 240 <= hls(c)[0] < 290]
    blues = [c for c in sat if 180 <= hls(c)[0] < 240]
    accent = (pinks or violets or sat or ["#ff8fc8"])[0]
    alt = (violets or blues or [accent])[0]
    alt2 = (blues or violets or [alt])[0] if (blues or violets) else alt

    # fonts by job
    fonts = Counter()
    for val, n in T.get("font", []):
        fonts[val.split(",")[0].strip().strip('"').strip("'")] += n
    for f in bp.get("loadedFonts", []):
        fam = re.sub(r"\s+\d.*$", "", f).strip()
        fonts[fam] += 1
    ui = fonts.most_common(1)[0][0] if fonts else "Nunito"
    # characterful display faces outrank workhorse rounded faces even when used less often
    STRONG = re.compile(r"daruma|mochiy|chewy|cherry|dynapuff|grandstander|lobster|pacifico|bubblegum|titan|luckiest|bungee|modak|rubik bubbles|yusei|potta|reggae|rampart|hachi", re.I)
    display = (next((f for f, _ in fonts.most_common() if STRONG.search(f)), None)
               or next((f for f, _ in fonts.most_common() if DISPLAY_HINT.search(f) and not PIXEL_HINT.search(f)), None))
    hand = next((f for f, _ in fonts.most_common() if HAND_HINT.search(f)), None)
    pixel = next((f for f, _ in fonts.most_common() if PIXEL_HINT.search(f)), None)

    # gradient pills (candy buttons), text glow recipes, rough filters
    def light_gradient(g):
        cols = [to_hex(*m.groups()[:3]) for m in RGB.finditer(g)]
        return len(cols) >= 2 and all(hls(c)[1] > 0.6 and hls(c)[2] > 0.3 for c in cols)
    pills = [g for g, _ in T.get("gradient", []) if g.startswith("linear-gradient") and light_gradient(g)][:3]
    filters = [f for f, _ in T.get("filter", []) if "url(" in f or "drop-shadow" in f][:6]

    # art: same origin images that are not user avatars
    host = re.sub(r"^https?://", "", bp["url"]).split("/")[0]
    art = []
    for im in bp.get("images", []):
        src = im["src"]
        name = src.split("?")[0].split("/")[-1]
        if re.search(r"avatar|artwork|profile|discordapp|a_[0-9a-f]{8}", src, re.I):
            continue
        if name and name not in [a["file"] for a in art]:
            art.append({"file": name, "src": src, "size": f"{im.get('w')}x{im.get('h')}",
                        "role": "mascot" if re.search(r"cat|mascot|bunny|bear|plush|brand|kuro|chara|pet", name, re.I) else
                                "scene" if re.search(r"room|scene|bg|background|landing|hero|wall", name, re.I) else "ornament"})
    keyframes = list(bp.get("keyframes", {}))[:60]
    radii = [r for r, _ in T.get("radius", [])[:6]]

    brand = {
        "site": bp["url"], "mode": "dark" if is_dark else "light",
        "palette": {"bg": bg, "text": text, "text-muted": muted, "accent": accent, "alt": alt, "alt-2": alt2,
                    "glow": (glow.most_common(1) or [(accent, 0)])[0][0], "all_frequent": [c for c, _ in allc.most_common(16)]},
        "fonts": {"ui": ui, "display": display, "hand": hand, "pixel": pixel, "all": [f for f, _ in fonts.most_common(10)]},
        "recipes": {"candy_pills": pills, "filters": filters, "shadows": [s for s, _ in T.get("shadow", [])[:6]],
                    "text_glow": [], "radii": radii},
        "art": art[:30], "signature_motion": keyframes,
    }
    if repo:
        tg = Counter()
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", ".next", "dist", "build")]
            for f in files:
                if f.endswith((".css", ".scss", ".tsx", ".jsx")):
                    try:
                        for m in re.finditer(r"text-shadow\s*:\s*([^;}\n]+)", open(os.path.join(root, f), errors="ignore").read()):
                            tg[m.group(1).strip()] += 1
                    except OSError:
                        pass
        brand["recipes"]["text_glow"] = [t for t, _ in tg.most_common(6) if "none" not in t]
    return brand


def to_css(b):
    p, f = b["palette"], b["fonts"]
    dark = b["mode"] == "dark"
    lines = [
        f"/* brand lock for {b['site']} (generated by brand.py). Load after cute-tokens.css. */",
        f':root, [data-flavor="brand"] {{',
        f"  --bg: {p['bg']};",
        f"  --surface: color-mix(in srgb, {p['bg']} 82%, {p['alt']});",
        f"  --paper: color-mix(in srgb, {p['bg']} 88%, {p['text']});",
        f"  --border: color-mix(in srgb, {p['text']} 14%, transparent);",
        f"  --text: {p['text']};",
        f"  --text-muted: {p['text-muted'] or ('color-mix(in srgb, ' + p['text'] + ' 62%, ' + p['bg'] + ')')};",
        f"  --accent: {p['accent']};",
        f"  --accent-press: color-mix(in srgb, {p['accent']} 70%, #000);",
        f"  --accent-soft: color-mix(in srgb, {p['accent']} {'22' if dark else '35'}%, {p['bg']});",
        f"  --accent-bright: {p['accent']};",
        f"  --alt: {p['alt']};",
        f"  --alt-2: {p['alt-2']};",
        f"  --display: {p['accent'] if not dark else p['text']};",
        f"  --on-soft: {p['text']};",
        f"  --glow: {p['glow']};",
        f"  --star: {p['text'] if dark else '#0000'};",
        f"  --sticker-rim: {('color-mix(in srgb, ' + p['alt'] + ' 55%, transparent)') if dark else '#fff'};",
        f"  --sticker-shadow: {('color-mix(in srgb, ' + p['glow'] + ' 45%, transparent)') if dark else ('color-mix(in srgb, ' + p['accent'] + ' 40%, #fff)')};",
        f"  --sticker-label: var(--paper);",
        f"  --dots: color-mix(in srgb, {p['text']} 8%, transparent);",
        f"  --sparkle: {p['glow']};",
    ]
    if f.get("ui"):
        lines.append(f'  --font-body: "{f["ui"]}", ui-rounded, system-ui, sans-serif;')
    if f.get("display"):
        lines.append(f'  --font-display: "{f["display"]}", "{f["ui"]}", ui-rounded, system-ui, sans-serif;')
    if f.get("hand"):
        lines.append(f'  --font-hand: "{f["hand"]}", "Patrick Hand", cursive;')
    if f.get("pixel"):
        lines.append(f'  --font-pixel: "{f["pixel"]}", ui-monospace, monospace;')
    lines.append("}")
    if b["recipes"]["candy_pills"]:
        lines.append(f".cc-sticker-lit {{ background: {b['recipes']['candy_pills'][0]}; color: {p['bg'] if dark else '#fff'}; }}")
    if dark:
        lines.append(".cc-display { text-shadow: 0 0 6px var(--glow), 0 0 18px color-mix(in srgb, var(--glow) 60%, transparent); }")
        lines.append(".cc-sticker, .cc-card { box-shadow: 0 0 0 1px var(--border), 0 10px 24px -12px #000a, 0 0 14px -6px var(--glow); }")
    return "\n".join(lines) + "\n"


def to_md(b):
    p, f, r = b["palette"], b["fonts"], b["recipes"]
    L = [f"# Brand lock: {b['site']}", "",
         "These are the site's identity. Every variant keeps them; variants differ in structure, composition, motion and craft.",
         "Changing any of these needs deviation 8+ AND the user saying the identity itself may change.", "",
         f"- mode: **{b['mode']}**",
         f"- palette: bg `{p['bg']}`, ink `{p['text']}`, muted `{p['text-muted']}`, accent `{p['accent']}`, alt `{p['alt']}`, alt-2 `{p['alt-2']}`, glow `{p['glow']}`",
         f"- frequent colours: {' '.join('`' + c + '`' for c in p['all_frequent'])}",
         f"- type: UI **{f['ui']}**, display **{f['display']}**, handwriting **{f['hand']}**, pixel **{f['pixel']}**",
         f"- candy pill gradients: {'; '.join('`' + g[:110] + '`' for g in r['candy_pills']) or 'none'}",
         f"- glow / filter recipes: {'; '.join('`' + x[:110] + '`' for x in r['filters']) or 'none'}",
         f"- shadows: {'; '.join('`' + x[:90] + '`' for x in r['shadows'][:4])}",
         f"- radii: {', '.join(r['radii'])}", "", "## Art to reuse (never replace with generic art)"]
    for a in b["art"]:
        L.append(f"- [{a['role']}] `{a['file']}` {a['size']}")
    L += ["", "Mascot: if an art item has role mascot, the mascot IS that art. Use `createMascot({ image: <url> })` so it keeps the brand's own character and gains the behaviours.",
          "", f"## Signature motion ({len(b['signature_motion'])} keyframes; keep the feel, reuse names where possible)", ", ".join(b["signature_motion"])]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract"); p.add_argument("blueprint"); p.add_argument("--out", default=".cutecore/brand"); p.add_argument("--repo")
    p = sub.add_parser("show"); p.add_argument("--dir", default=".cutecore/brand")
    a = ap.parse_args(argv)
    if a.cmd == "show":
        print(open(os.path.join(a.dir, "brand.md")).read())
        return
    b = extract(json.load(open(a.blueprint)), a.repo)
    os.makedirs(a.out, exist_ok=True)
    json.dump(b, open(os.path.join(a.out, "brand.json"), "w"), indent=2)
    open(os.path.join(a.out, "brand.md"), "w").write(to_md(b))
    open(os.path.join(a.out, "brand.css"), "w").write(to_css(b))
    print(to_md(b))
    print(f"wrote {a.out}/brand.json, brand.md, brand.css")


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
