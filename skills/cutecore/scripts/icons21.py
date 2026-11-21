#!/usr/bin/env python3
"""icons21: pull real icons from 21st.dev/community/icons instead of hand drawing SVGs.

The 21st icon catalogue (lucide, phosphor, tabler, heroicons, hugeicons, remix,
line-md and several animated sets, ~29k icons) is served by a public endpoint
that needs no API key. This script searches it, picks icons, and writes them out
as SVG, React (TSX), Vue, plain HTML or data URLs, optionally with cutecore
treatments layered on top of the original artwork (doodle wobble, sticker
outline, hover animations). The icon geometry itself always comes from 21st.

Usage
  icons21.py sets
  icons21.py search "heart" [--set phosphor] [--family lucide] [--style duotone]
                            [--animated] [--category emoji] [--limit 12] [--json]
  icons21.py get phosphor/heart [--format svg|react|vue|html|dataurl]
                            [--style fill] [--size 24] [--animate wiggle]
                            [--doodle] [--sticker] [--out path]
  icons21.py pack heart,star,cloud,moon [--set phosphor] [--style duotone]
                            [--format react] --out src/components/icons
  icons21.py cute-pack --out src/components/icons [--format react] [--style duotone]
  icons21.py inline page.src.html --out page.html   # bake <i data-icon="phosphor/heart" data-style="fill"></i> placeholders

Only the Python standard library is used. Results are cached in
~/.cache/cutecore/icons21 so repeated calls are instant and work offline.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://21st.dev/api/trpc/"
CACHE = os.path.join(os.path.expanduser(os.environ.get("XDG_CACHE_HOME", "~/.cache")), "cutecore", "icons21")
UA = "cutecore-skill/1.0 (+icons21)"
STYLES = ["outline", "fill", "duotone", "bold", "thin", "light"]
ANIMS = ["wiggle", "bounce", "pop", "float", "spin", "draw", "heartbeat", "jelly"]

# A curated starter vocabulary for cute interfaces. Each entry is a list of
# search terms tried in order; the first hit wins. Feel free to extend.
CUTE_VOCAB = {
    "heart": ["heart"], "star": ["star"], "sparkle": ["sparkle", "sparkles"],
    "cloud": ["cloud"], "moon": ["moon"], "sun": ["sun"], "flower": ["flower"],
    "butterfly": ["butterfly"], "cat": ["cat"], "paw": ["paw", "paw print"],
    "rabbit": ["rabbit"], "bunny": ["rabbit", "bunny"], "kitty": ["cat"], "puppy": ["dog"], "bear": ["bear", "teddy bear"], "ghost": ["ghost"],
    "music": ["music", "music note"], "gift": ["gift"], "cake": ["cake", "cupcake"],
    "candy": ["candy", "lollipop"], "ice-cream": ["ice cream"], "cherry": ["cherry", "cherries"],
    "crown": ["crown"], "diamond": ["diamond", "gem"], "magic-wand": ["magic wand", "wand"],
    "rainbow": ["rainbow"], "smile": ["smile", "smiley"], "chat": ["chat", "message"],
    "home": ["home", "house"], "user": ["user"], "settings": ["settings", "gear"],
    "search": ["search"], "bell": ["bell"], "mail": ["mail", "envelope"],
    "camera": ["camera"], "game": ["game controller", "gamepad"], "headphones": ["headphones"],
    "planet": ["planet"], "shooting-star": ["shooting star"], "bow": ["bow", "ribbon", "bow tie", "gift"],
    "cookie": ["cookie"], "coffee": ["coffee", "cup"], "leaf": ["leaf"],
}


# --------------------------------------------------------------------------- api

def _cache_path(key: str) -> str:
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, hashlib.sha1(key.encode()).hexdigest() + ".json")


def trpc(proc: str, payload, ttl: int = 7 * 86400):
    key = proc + json.dumps(payload, sort_keys=True)
    cp = _cache_path(key)
    if os.path.exists(cp) and time.time() - os.path.getmtime(cp) < ttl:
        with open(cp) as fh:
            return json.load(fh)
    qs = urllib.parse.urlencode({"input": json.dumps({"json": payload})})
    req = urllib.request.Request(API + proc + "?" + qs, headers={"User-Agent": UA, "Accept": "application/json"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.load(r)
            break
        except Exception as e:  # network hiccup: back off and retry
            last = e
            time.sleep(1.5 * (attempt + 1))
    else:
        if os.path.exists(cp):  # stale cache beats nothing
            with open(cp) as fh:
                return json.load(fh)
        sys.exit(f"icons21: could not reach 21st.dev ({last}). Is 21st.dev allowed on this network?")
    if "error" in data:
        msg = data["error"].get("json", {}).get("message", data["error"])
        sys.exit(f"icons21: 21st.dev rejected the query: {msg}")
    out = data["result"]["data"]["json"]
    with open(cp, "w") as fh:
        json.dump(out, fh)
    return out


def list_sets():
    return trpc("icons.sets", None, ttl=30 * 86400)


def search(query, set_slug=None, family=None, style=None, animated=False, category=None, limit=12, cursor=None):
    p = {"query": query or None, "limit": max(1, min(int(limit), 120)), "animatedOnly": bool(animated)}
    if set_slug:
        p["setSlugs"] = [s.strip() for s in set_slug.split(",") if s.strip()]
    if family:
        p["families"] = [f.strip() for f in family.split(",") if f.strip()]
    if style:
        p["style"] = style
    if category:
        p["category"] = category
    if cursor is not None:
        p["cursor"] = cursor
    p = {k: v for k, v in p.items() if v is not None}
    return trpc("icons.list", p)


def resolve(ref: str, style=None, set_hint=None, family=None):
    """ref is 'set/slug', or a bare slug/term (best match is chosen)."""
    if "/" in ref:
        set_slug, slug = ref.split("/", 1)
    else:
        set_slug, slug = set_hint, ref
    terms = CUTE_VOCAB.get(slug, [slug.replace("-", " ")])
    best, best_score = None, 0
    for term in terms:
        want = term.replace(" ", "-")
        res = search(term, set_slug=set_slug, family=family, style=style, limit=40)
        for rank, i in enumerate(res.get("items", [])):
            core = STYLE_SUFFIX.sub("", i["slug"])
            toks = core.split("-")
            if core in (slug, want):
                score = 100
            elif core.startswith(want + "-") or toks[0] == want:
                score = 60
            elif want in toks:
                score = 40
            else:
                continue
            score -= rank * 0.1  # keep 21st's relevance order as a tiebreak
            if score > best_score:
                best, best_score = i, score
        if best_score >= 100:
            break
    return best


STYLE_SUFFIX = re.compile(r"-(fill|filled|duotone|bold|thin|light|solid|outline)$")


# ------------------------------------------------------------- cute treatments

def _uid(icon) -> str:
    return re.sub(r"[^a-z0-9]", "", (icon["set_slug"] + icon["slug"]).lower())[:24]


def _add_pathlength(body: str) -> str:
    def fix(m):
        tag = m.group(0)
        return tag if "pathLength" in tag else tag[:-1].rstrip("/") + ' pathLength="1"' + ("/>" if tag.endswith("/>") else ">")
    return re.sub(r"<(path|circle|line|polyline|polygon|rect|ellipse)\b[^>]*>", fix, body)


def treat(icon, doodle=False, sticker=False, animate=None, sticker_color="#ffffff"):
    """Return (defs, wrapped_body, extra_classes). Geometry is never redrawn."""
    uid = _uid(icon)
    body = icon["svg_body"]
    defs, filters, classes = [], [], ["cc-icon"]
    if animate:
        classes.append(f"cc-anim-{animate}")
        if animate == "draw":
            body = _add_pathlength(body)
    if doodle:
        # line boil: displace the real icon with animated turbulence so it reads hand drawn
        defs.append(
            f'<filter id="ccd-{uid}" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="2" result="n">'
            f'<animate attributeName="seed" values="2;7;13;21" dur="0.6s" calcMode="discrete" repeatCount="indefinite"/>'
            f'</feTurbulence><feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G"/></filter>'
        )
        filters.append(f"url(#ccd-{uid})")
        classes.append("cc-doodle")
    if sticker:
        defs.append(
            f'<filter id="ccs-{uid}" x="-30%" y="-30%" width="160%" height="160%">'
            f'<feMorphology in="SourceAlpha" operator="dilate" radius="1.4" result="d"/>'
            f'<feFlood flood-color="{sticker_color}"/><feComposite in2="d" operator="in" result="o"/>'
            f'<feDropShadow in="o" dx="0" dy="0.8" stdDeviation="0.6" flood-color="#d86fa8" flood-opacity="0.35" result="s"/>'
            f'<feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        )
        filters.append(f"url(#ccs-{uid})")
        classes.append("cc-sticker")
    wrapped = body
    for f in filters:  # nest so both filters apply
        wrapped = f'<g filter="{f}">{wrapped}</g>'
    return ("<defs>" + "".join(defs) + "</defs>" if defs else ""), wrapped, classes


# ------------------------------------------------------------------ renderers

def pascal(slug: str, strip_style: bool = False) -> str:
    if strip_style:
        slug = STYLE_SUFFIX.sub("", slug)
    s = "".join(p.capitalize() for p in re.split(r"[^a-zA-Z0-9]+", slug) if p)
    return ("I" + s if s[:1].isdigit() else s) + "Icon"


def provenance(icon) -> str:
    return f"21st.dev/community/icons  set={icon['set_slug']}  slug={icon['slug']}"


def to_svg(icon, size=24, **kw) -> str:
    defs, body, classes = treat(icon, **kw)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{icon["view_box"]}" width="{size}" height="{size}" '
            f'class="{" ".join(classes)}" data-21st="{icon["set_slug"]}/{icon["slug"]}" aria-hidden="true">{defs}{body}</svg>')


_SKIP_CAMEL = ("data-", "aria-")


def jsxify(markup: str) -> str:
    def attr(m):
        name, val = m.group(1), m.group(2)
        if name == "class":
            name = "className"
        elif name.startswith("xlink:"):
            name = "xlink" + name[6:].capitalize()
        elif name.startswith("xml:"):
            name = "xml" + name[4:].capitalize()
        elif "-" in name and not name.startswith(_SKIP_CAMEL):
            head, *rest = name.split("-")
            name = head + "".join(r.capitalize() for r in rest)
        return f" {name}={val}"
    return re.sub(r"\s([a-zA-Z_:][-a-zA-Z0-9_:.]*)=(\"[^\"]*\")", attr, markup)


def to_react(icon, **kw) -> str:
    defs, body, classes = treat(icon, **kw)
    inner = defs + body
    name = pascal(icon["slug"])
    if "style=" in inner:
        jsx_inner = None
    else:
        jsx_inner = jsxify(inner)
    tag_open = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{icon["view_box"]}" width={{size}} height={{size}} '
                f'data-21st="{icon["set_slug"]}/{icon["slug"]}" aria-hidden={{title ? undefined : true}} role={{title ? "img" : undefined}} '
                f'className={{["{" ".join(classes)}", className].filter(Boolean).join(" ")}} {{...props}}')
    if jsx_inner is None:
        render = f'    {tag_open} dangerouslySetInnerHTML={{{{ __html: {json.dumps(inner)} }}}} />'
    else:
        render = f"    {tag_open}>\n      {{title ? <title>{{title}}</title> : null}}\n      {jsx_inner}\n    </svg>"
    return f"""// {provenance(icon)}
// Fetched with the cutecore skill (icons21.py). Do not redraw by hand; re-fetch instead.
import * as React from "react";

export type {name}Props = React.SVGProps<SVGSVGElement> & {{ size?: number | string; title?: string }};

export function {name}({{ size = 24, title, className, ...props }}: {name}Props) {{
  return (
{render}
  );
}}

export default {name};
"""


def to_vue(icon, **kw) -> str:
    defs, body, classes = treat(icon, **kw)
    return f"""<!-- {provenance(icon)} -->
<script setup lang="ts">
withDefaults(defineProps<{{ size?: number | string }}>(), {{ size: 24 }});
</script>

<template>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="{icon['view_box']}" :width="size" :height="size"
       class="{' '.join(classes)}" data-21st="{icon['set_slug']}/{icon['slug']}" aria-hidden="true">{defs}{body}</svg>
</template>
"""


def to_dataurl(icon, size=24, color="#ff8fc8", **kw) -> str:
    svg = to_svg(icon, size=size, **kw).replace("currentColor", color)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def render(icon, fmt, size, **kw):
    if fmt == "react":
        return to_react(icon, **kw)
    if fmt == "vue":
        return to_vue(icon, **kw)
    if fmt == "dataurl":
        return to_dataurl(icon, size=size, **kw)
    if fmt == "html":
        return f"<!-- {provenance(icon)} -->\n" + to_svg(icon, size=size, **kw)
    return to_svg(icon, size=size, **kw)


EXT = {"svg": ".svg", "react": ".tsx", "vue": ".vue", "html": ".html", "dataurl": ".txt"}


# ------------------------------------------------------------------------ cli

def _kw(a):
    return dict(doodle=a.doodle, sticker=a.sticker, animate=a.animate)


def cmd_sets(a):
    sets = list_sets()
    if a.json:
        print(json.dumps(sets, indent=2))
        return
    for s in sets:
        anim = "animated" if s.get("is_animated") else "static"
        print(f"{s['slug']:<24} {s['icons_count']:>5}  {anim:<8} family={s['base_family']:<10} {s['license']}")


def cmd_search(a):
    res = search(a.query, a.set, a.family, a.style, a.animated, a.category, a.limit)
    if a.json:
        print(json.dumps(res, indent=2))
        return
    print(f"# {res.get('total', '?')} matches for {a.query!r} (showing {len(res.get('items', []))})")
    for i in res.get("items", []):
        flag = "~" if i.get("is_animated") else " "
        ref = f"{i['set_slug']}/{i['slug']}"
        print(f"{flag} {ref:<46} {i['category']:<20} copies={i.get('copies_count', 0)}")
    print("\n'~' = animated set. Fetch one with: icons21.py get <set>/<slug> --format react")


def _write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def cmd_get(a):
    icon = resolve(a.ref, style=a.style, set_hint=a.set, family=a.family)
    if not icon:
        sys.exit(f"icons21: nothing found for {a.ref!r}. Try `icons21.py search {a.ref.split('/')[-1]}`.")
    out = render(icon, a.format, a.size, **_kw(a))
    if a.out:
        _write(a.out, out)
        print(f"wrote {a.out}  ({icon['set_slug']}/{icon['slug']})", file=sys.stderr)
    else:
        print(out)


def _pack(names, a):
    if not a.out:
        sys.exit("icons21: --out <dir> is required for pack")
    os.makedirs(a.out, exist_ok=True)
    index, manifest, missing = [], [], []
    for n in names:
        icon = resolve(n, style=a.style, set_hint=a.set, family=a.family)
        if not icon:
            missing.append(n)
            continue
        base = pascal(icon["slug"], strip_style=True) if a.format in ("react", "vue") else f"{icon['set_slug']}-{icon['slug']}"
        _write(os.path.join(a.out, base + EXT[a.format]), render(icon, a.format, a.size, **_kw(a)))
        manifest.append({"name": n, "set": icon["set_slug"], "slug": icon["slug"], "file": base + EXT[a.format]})
        if a.format == "react":
            index.append(f'export {{ {base} }} from "./{base}";')
    if index:
        _write(os.path.join(a.out, "index.ts"), "\n".join(index) + "\n")
    _write(os.path.join(a.out, "icons21.manifest.json"), json.dumps(manifest, indent=2))
    print(f"wrote {len(manifest)} icons to {a.out}" + (f"; not found: {', '.join(missing)}" if missing else ""), file=sys.stderr)


def cmd_pack(a):
    _pack([n.strip() for n in a.names.split(",") if n.strip()], a)


ICON_TAG = re.compile(r"<i\s+([^>]*\bdata-icon=\"[^\"]+\"[^>]*)>\s*</i>")


def _attrs(t):
    return dict(re.findall(r'([\w-]+)="([^"]*)"', t))


def cmd_inline(a):
    """Replace <i data-icon="set/slug" data-style="fill" data-animate="jelly" data-doodle data-sticker class="x"></i> with real SVGs."""
    src = open(a.file, encoding="utf-8").read()
    count = 0

    def sub(m):
        nonlocal count
        at = _attrs(m.group(1))
        flags = m.group(1)
        icon = resolve(at["data-icon"], style=at.get("data-style"), set_hint=at.get("data-set"))
        if not icon:
            print(f"icons21: no match for {at['data-icon']}", file=sys.stderr)
            return m.group(0)
        svg = to_svg(icon, size=at.get("data-size", "1em"), doodle="data-doodle" in flags, sticker="data-sticker" in flags, animate=at.get("data-animate"))
        if at.get("class"):
            svg = svg.replace('class="cc-icon', f'class="cc-icon {at["class"]}', 1)
        count += 1
        return svg

    out = ICON_TAG.sub(sub, src)
    dest = a.out or a.file
    _write(dest, out)
    print(f"inlined {count} icons -> {dest}", file=sys.stderr)


def cmd_cute_pack(a):
    _pack(list(CUTE_VOCAB), a)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, fetch=False):
        p.add_argument("--set", help="set slug(s), comma separated (see `sets`)")
        p.add_argument("--family", help="base family: lucide, phosphor, tabler, heroicons, hugeicons, remix, line-md")
        p.add_argument("--style", choices=STYLES)
        if fetch:
            p.add_argument("--format", default="svg", choices=list(EXT))
            p.add_argument("--size", default=24)
            p.add_argument("--animate", choices=ANIMS, help="adds cc-anim-* class (CSS lives in assets/cute-tokens.css)")
            p.add_argument("--doodle", action="store_true", help="hand-drawn line boil on the real icon")
            p.add_argument("--sticker", action="store_true", help="white die-cut sticker outline")

    p = sub.add_parser("sets"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_sets)
    p = sub.add_parser("search"); p.add_argument("query"); common(p)
    p.add_argument("--animated", action="store_true"); p.add_argument("--category"); p.add_argument("--limit", type=int, default=12)
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("get"); p.add_argument("ref"); common(p, True); p.add_argument("--out"); p.set_defaults(fn=cmd_get)
    p = sub.add_parser("pack"); p.add_argument("names"); common(p, True); p.add_argument("--out"); p.set_defaults(fn=cmd_pack)
    p = sub.add_parser("cute-pack"); common(p, True); p.add_argument("--out"); p.set_defaults(fn=cmd_cute_pack)
    p = sub.add_parser("inline", help="bake <i data-icon> placeholders in an html file into real 21st svgs"); p.add_argument("file"); p.add_argument("--out"); p.set_defaults(fn=cmd_inline)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
