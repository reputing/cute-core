#!/usr/bin/env python3
"""deslop: type-check a UI for the tells of generic AI output, before anyone sees it.

  deslop.py <files or dirs...> [--json] [--fix] [--strict]

Checks
  dash        em dash (U+2014), en dash (U+2013) and the ' -- ' stand-in, anywhere
  serif       serif font families, Tailwind font-serif, next/font serif imports
  basic-font  Inter / Roboto / Arial / Helvetica / system-ui as the *primary* face
  saas-copy   stock SaaS phrases ("Unlock", "Seamless", "Trusted by", ...)
  saas-layout hero + 3 feature cards + 3 tier pricing + logo cloud skeletons,
              indigo-to-purple gradient text, icon-in-rounded-square feature grids
  sameness    the same card recipe (rounded + shadow + padding) repeated many times
  hand-svg    24x24 style inline icons that were not fetched from 21st.dev
              (icons21.py stamps data-21st="set/slug"; anything else is suspect)
  lorem       placeholder text left behind

Exit code is 1 when an error-level finding exists, so it can gate a build:
  python3 deslop.py src && npm run build

--fix rewrites dashes in place (spaced dash -> ', ', numeric range -> '-').
Nothing else is auto-fixed: those need a designer's eye, not a regex.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro", ".md", ".mdx", ".json"}
SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".cutecore", ".turbo", ".vercel", "coverage", "out"}

SERIF_FACES = r"Georgia|Times(?: New Roman)?|Playfair(?: Display)?|Merriweather|Lora|(?:EB )?Garamond|Cormorant(?: Garamond)?|DM Serif(?: Display| Text)?|Fraunces|Libre Baskerville|Baskerville|Instrument Serif|Crimson(?: Pro| Text)?|PT Serif|Noto Serif(?: JP)?|Source Serif(?: Pro| 4)?|IBM Plex Serif|Bodoni(?: Moda)?|Didot|Cambria|Spectral|Newsreader|Young Serif|Gloock|Literata|Alegreya|Zilla Slab|Roboto Slab|Bitter|Rockwell|Palatino"
RULES = [
    # (id, level, regex, message)
    ("dash", "error", re.compile("\u2014"), "em dash; rewrite the sentence (comma, period, colon or parentheses)"),
    ("dash", "error", re.compile("(?<=\\S)\u2013(?=\\S)|\\s\u2013\\s"), "en dash; use a hyphen for ranges, rewrite otherwise"),
    ("dash", "warn", re.compile(r"(?<=[a-z]) -- (?=[a-z])"), "' -- ' used as a dash in prose"),
    ("serif", "error", re.compile(r"font-family\s*:[^;}{]*\b(?<!sans-)serif\b(?!-)", re.I), "serif fallback in font-family"),
    ("serif", "error", re.compile(r"(?:font-family\s*:|fontFamily\s*[:=]|family=)[^;\n]*?\b(?:" + SERIF_FACES + r")\b", re.I), "serif typeface"),
    ("serif", "error", re.compile(r"\bfont-serif\b"), "Tailwind font-serif"),
    ("serif", "error", re.compile(r"from\s+['\"]next/font/google['\"]", re.I), None),  # resolved below
    ("basic-font", "warn", re.compile(r"font-family\s*:\s*['\"]?(?:Inter|Roboto|Arial|Helvetica(?: Neue)?|system-ui|-apple-system)\b", re.I), "default-looking primary font; pick a face with character"),
    ("basic-font", "warn", re.compile(r"\b(?:Inter|Roboto)\s*\(\s*\{"), "next/font Inter/Roboto as the face"),
    ("saas-copy", "warn", re.compile(r"\b(?:Unlock (?:the|your)|Elevate your|Supercharge|Revolutioni[sz]e|Seamless(?:ly)?|Empower(?:ing)? (?:you|teams)|All-in-one|Streamline your|Boost your productivity|cutting-edge|next-generation|Trusted by|Loved by (?:thousands|teams)|Get started (?:for free|today)|Start your free trial|No credit card required|Built for (?:modern )?teams|Join thousands|Take your .{1,20} to the next level|game[- ]changer|world-class|best-in-class|effortless(?:ly)?)\b", re.I), "stock SaaS phrase; write like a person who made this"),
    ("saas-layout", "warn", re.compile(r"bg-clip-text[^\"'`]*text-transparent[^\"'`]*from-(?:indigo|blue|violet|purple)-\d00|from-(?:indigo|blue|violet)-[56]00[^\"'`]*to-(?:purple|violet|pink)-[56]00"), "indigo to purple gradient (the default AI gradient)"),
    ("saas-layout", "warn", re.compile(r"Most Popular|Most popular|Pro plan|Enterprise plan|\bper month\b.*\bper month\b", re.S), "three tier pricing skeleton"),
    ("saas-layout", "warn", re.compile(r"(?:rounded-(?:lg|xl)\s+bg-(?:primary|indigo-\d00|blue-\d00)/10\s+p-[23])"), "icon in a tinted rounded square (feature grid cliche)"),
    ("lorem", "error", re.compile(r"\blorem ipsum\b|\bdolor sit amet\b", re.I), "placeholder text"),
]
SERIF_NEXT = re.compile(r"import\s*\{([^}]*)\}\s*from\s*['\"]next/font/google['\"]")
SERIF_NAME = re.compile(r"\b(?:" + SERIF_FACES.replace(" ", "_").replace("(?:_", "(?:_") + r")\b|_Serif\b|Serif_", re.I)
CARD = re.compile(r"rounded-(?:xl|2xl|3xl|lg)\b[^\"'`]{0,80}\bshadow(?:-\w+)?\b[^\"'`]{0,80}\bp-\d|shadow(?:-\w+)?\b[^\"'`]{0,80}rounded-(?:xl|2xl|3xl|lg)\b[^\"'`]{0,80}\bp-\d")
INLINE_SVG = re.compile(r"<svg\b[^>]*>", re.I)


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for f in files:
                if os.path.splitext(f)[1].lower() in EXTS and not f.endswith((".min.js", ".min.css", "lock.json")) and f != "package-lock.json":
                    yield os.path.join(root, f)


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def scan(path, text):
    found = []
    for rid, level, rx, msg in RULES:
        if rid == "serif" and msg is None:
            for m in SERIF_NEXT.finditer(text):
                names = [n.strip() for n in m.group(1).split(",")]
                bad = [n for n in names if SERIF_NAME.search(n)]
                if bad:
                    found.append((rid, "error", line_of(text, m.start()), f"next/font serif import: {', '.join(bad)}"))
            continue
        for m in rx.finditer(text):
            found.append((rid, level, line_of(text, m.start()), msg + f"  [{m.group(0)[:60].strip()}]"))
    cards = CARD.findall(text)
    if len(cards) >= 6:
        found.append(("sameness", "warn", 1, f"{len(cards)} identical card recipes (rounded+shadow+padding). Vary shape, tilt, border, texture"))
    for m in INLINE_SVG.finditer(text):
        tag = m.group(0)
        if "data-21st" in tag or "cc-shader" in tag or "data-cutecore" in tag:
            continue
        if re.search(r'viewBox=["\']0 0 (?:16|20|24|32|256) (?:16|20|24|32|256)["\']', tag) and not re.search(r'(?:width|height)=["\']?(?:[4-9]\d|\d{3,})', tag):
            found.append(("hand-svg", "warn", line_of(text, m.start()), "icon-sized inline <svg> not from 21st; fetch with icons21.py (or add data-cutecore if it is an illustration)"))
    return found


def saas_skeleton(texts):
    """Whole-project heuristic: does the page tree read like the default SaaS landing page?"""
    blob = "\n".join(texts)
    signals = {
        "hero with two CTAs": bool(re.search(r"(?:Get started|Start free|Sign up)[\s\S]{0,400}(?:Learn more|See how|Book a demo|Watch demo)", blob, re.I)),
        "logo cloud": bool(re.search(r"Trusted by|used by teams at|logos?[-_ ]?cloud", blob, re.I)),
        "3 column feature grid": len(re.findall(r"grid-cols-1\s+(?:sm|md):grid-cols-2\s+lg:grid-cols-3|md:grid-cols-3", blob)) >= 1,
        "3 tier pricing": bool(re.search(r"Most popular", blob, re.I)) and len(re.findall(r"/\s*mo(?:nth)?\b", blob)) >= 2,
        "testimonial wall": bool(re.search(r"testimonial", blob, re.I)),
        "FAQ accordion": bool(re.search(r"Frequently asked|FAQ", blob)),
        "max-w-7xl centred everything": len(re.findall(r"max-w-7xl\s+mx-auto|mx-auto\s+max-w-7xl", blob)) >= 3,
    }
    return sum(signals.values()), signals


def fix_dashes(text):
    text = re.sub(r"(\d)\s*[\u2013\u2014]\s*(\d)", r"\1-\2", text)
    text = re.sub(r"\s*\u2014\s*", ", ", text)
    text = re.sub(r"\s\u2013\s", ", ", text)
    text = text.replace("\u2013", "-")
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fix", action="store_true", help="auto-fix dashes only")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args(argv)

    report, texts = {}, []
    for f in iter_files(a.paths):
        try:
            text = open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        if a.fix and re.search("[\u2013\u2014]", text):
            text = fix_dashes(text)
            open(f, "w", encoding="utf-8").write(text)
        texts.append(text)
        hits = scan(f, text)
        if hits:
            report[f] = hits

    score, signals = saas_skeleton(texts)
    errors = sum(1 for h in report.values() for x in h if x[1] == "error")
    warns = sum(1 for h in report.values() for x in h if x[1] == "warn")
    if score >= 3:
        warns += 1

    if a.json:
        print(json.dumps({"errors": errors, "warnings": warns, "saas_skeleton_score": score, "saas_signals": signals,
                          "findings": {f: [dict(rule=r, level=l, line=n, msg=m) for r, l, n, m in h] for f, h in report.items()}}, indent=2))
    else:
        for f, hits in report.items():
            for rid, level, n, msg in sorted(hits, key=lambda x: x[2]):
                print(f"{f}:{n}: {level} [{rid}] {msg}")
        lit = [k for k, v in signals.items() if v]
        print(f"\nsaas skeleton score {score}/7" + (f" ({', '.join(lit)})" if lit else ""))
        if score >= 3:
            print("  reads like the default SaaS landing page; rethink the composition, not just the colours")
        print(f"{errors} error(s), {warns} warning(s)" + ("  ✿ clean" if not errors and not warns else ""))
    fail = errors > 0 or (a.strict and warns > 0)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
