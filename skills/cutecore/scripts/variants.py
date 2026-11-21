#!/usr/bin/env python3
"""variants: lay up to five design variants side by side so the user can pick one.

  variants.py plan --deviation 6 --count 5 [--seed 3]        # distinct directions to build
  variants.py gallery v1/index.html v2/index.html ... [--labels "Sticker postcard,Jelly OS,..."] [--out .cutecore/variants/index.html]
  variants.py shots   v1/index.html v2/index.html ... [--out .cutecore/variants]   # PNGs via Playwright (node)

plan     turns a deviation level into N directions that differ on real axes
         (layout model, material, motion personality, signature moment), so the
         five results are five ideas, not one idea in five colours.
gallery  writes a static page with every variant live in an iframe, numbered,
         with desktop/mobile toggles. Open it, or screenshot it, then ask the
         user which number wins.
shots    full page screenshots at 1440 and 390 for each variant, for chat.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import shutil
import subprocess
import sys

AXES = {
    "layout": ["reading column (chessie)", "feature trail with spine (blushie)", "device frame with widget tiles (ivy, lwsg)",
               "card grid a character lies across (schuh)", "full bleed art with quiet column (rot.kim)", "invented bento (bento.py)",
               "walk-in WebGL room (milproject)", "pinboard scatter", "folder tabs and drawers", "tamagotchi device", "single sticker sheet"],
    "material": ["sticker paper", "jelly / gummy (candy glass)", "milk glass", "plush felt", "pixel LCD", "risograph print", "doodle sketchbook", "holo foil"],
    "motion": ["snappy sticker presses", "squishy jelly springs", "slow dreamy drift", "8 fps retro steps", "line boil doodle", "peek and react mascot"],
    "moment": ["mascot reacts to the main action", "shader sky follows the cursor", "postmark stamp on submit", "cassette reel on play",
               "cards morph shape on hover", "letters rise one by one", "confetti hearts from the cursor", "page unrolls like an awning"],
}

LEVELS = {
    1: "re-skin only: tokens, type, icons. Same structure and spacing.",
    2: "re-skin + house primitives (stickers, stamps, lined fields).",
    3: "restyle with motifs and micro motion; structure untouched.",
    4: "restyle + one signature moment per page.",
    5: "recompose within the same information architecture; mascot optional.",
    6: "new layout model, same features; mascot or shader expected.",
    7: "invented layout (bento.py / trail), WebGL moment, strong material.",
    8: "unexpected metaphor for the whole page (device, room, drawer, sheet).",
    9: "experimental: mixes two metaphors, custom shader, character driven.",
    10: "never seen before: build the thing the user did not know to ask for, still keeping every feature.",
}


def disliked_words(project):
    path = os.path.expanduser(os.environ.get("CUTECORE_MEMORY", "~/.claude/cutecore/taste.json"))
    try:
        picks = json.load(open(path))["projects"].get(project or "_global", {}).get("picks", [])
    except Exception:
        return set()
    return {w.strip().lower() for x in picks for w in (x.get("disliked") or "").split(",") if w.strip()}


def plan(deviation, count, seed, avoid=()):
    rnd = random.Random(seed)
    lo = 0 if deviation <= 4 else 1
    out, used = [], {k: set() for k in AXES}
    for i in range(count):
        d = {}
        for k, opts in AXES.items():
            pool = [o for o in opts[lo:] if o not in used[k] and not any(w in o.lower() for w in avoid)] or opts
            if deviation <= 3 and k == "layout":
                pool = ["keep the existing layout"]
            if deviation <= 2 and k == "moment":
                pool = ["none (tokens only)"]
            d[k] = rnd.choice(pool)
            used[k].add(d[k])
        out.append(d)
    return out


def cmd_plan(a):
    print(f"deviation {a.deviation}: {LEVELS[a.deviation]}\n")
    avoid = disliked_words(a.project)
    if avoid:
        print("steering away from (taste memory): " + ", ".join(sorted(avoid)) + "\n")
    for i, d in enumerate(plan(a.deviation, a.count, a.seed, avoid), 1):
        print(f"variant {i}: layout = {d['layout']}; material = {d['material']}; motion = {d['motion']}; signature = {d['moment']}")
    print("\nEvery variant keeps every feature. Run feature_guard.py compare on each before showing it.")


def cmd_gallery(a):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    labels = [l.strip() for l in a.labels.split(",")] if a.labels else []
    base = os.path.dirname(os.path.abspath(a.out))
    cells = []
    for i, p in enumerate(a.pages, 1):
        src = p if p.startswith("http") else os.path.relpath(os.path.abspath(p), base)
        label = html.escape(labels[i - 1] if i - 1 < len(labels) else os.path.basename(os.path.dirname(os.path.abspath(p))))
        cells.append(f'<figure><figcaption><b>{i}</b> {label} <a href="{html.escape(src)}" target="_blank">open</a></figcaption>'
                     f'<div class="frame"><iframe src="{html.escape(src)}" loading="lazy" title="variant {i}"></iframe></div></figure>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pick a variant</title>
<style>
:root{{--bg:#fff6f8;--ink:#3d2230;--accent:#b8335f;--soft:#ffd0df;--rim:#fff;--drop:#eea3bb}}
body{{margin:0;background:var(--bg);color:var(--ink);font:500 15px/1.5 Nunito,ui-rounded,system-ui,sans-serif;padding:24px 16px}}
h1{{font:700 28px Fredoka,ui-rounded,system-ui;color:var(--accent);margin:0 0 4px}} p{{margin:0 0 18px}}
.bar{{display:flex;gap:8px;margin-bottom:18px}} .bar button{{font:600 14px Fredoka,ui-rounded,system-ui;border:3px solid var(--rim);background:#fff;border-radius:14px;padding:6px 12px;box-shadow:0 2px 0 var(--drop);cursor:pointer}}
.bar button[aria-pressed=true]{{background:var(--accent);color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--w,460px),1fr));gap:18px}}
figure{{margin:0;background:#fff;border:2px solid #f7c6d5;border-radius:22px;box-shadow:0 3px 0 var(--drop);overflow:hidden}}
figcaption{{display:flex;gap:10px;align-items:center;padding:10px 14px;font-weight:600}} figcaption b{{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--soft)}} figcaption a{{margin-left:auto;color:var(--accent)}}
.frame{{height:var(--h,560px);overflow:hidden}} iframe{{border:0;width:var(--iw,1440px);height:calc(var(--h,560px) / var(--k,.32));transform:scale(var(--k,.32));transform-origin:0 0}}
</style></head><body><h1>Pick a variant</h1><p>Tell Claude the number you like best (and anything you love or hate about the others).</p>
<div class="bar"><button aria-pressed="true" data-m="desk">desktop</button><button aria-pressed="false" data-m="phone">phone</button></div>
<div class="grid">{''.join(cells)}</div>
<script>
const set=m=>{{const r=document.documentElement.style;document.querySelectorAll('.bar button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.m===m));
if(m==='phone'){{r.setProperty('--iw','390px');r.setProperty('--k','.9');r.setProperty('--w','360px');r.setProperty('--h','720px')}}else{{r.setProperty('--iw','1440px');r.setProperty('--w','460px');r.setProperty('--h','560px');fit()}}}};
const fit=()=>{{const f=document.querySelector('.frame');if(f&&document.documentElement.style.getPropertyValue('--iw')!=='390px')document.documentElement.style.setProperty('--k',(f.clientWidth/1440).toFixed(3))}};
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>set(b.dataset.m));addEventListener('resize',fit);fit();
</script></body></html>"""
    open(a.out, "w").write(page)
    print(a.out)


SHOT_JS = r"""
const { chromium } = require('playwright');
const [out, ...pages] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  for (let i = 0; i < pages.length; i++) {
    for (const [tag, w, h] of [['desktop', 1440, 900], ['mobile', 390, 844]]) {
      const p = await b.newPage({ viewport: { width: w, height: h } });
      const url = /^https?:/.test(pages[i]) ? pages[i] : 'file://' + pages[i];
      await p.goto(url, { waitUntil: 'load' }).catch(() => {});
      await p.waitForTimeout(1500);
      await p.screenshot({ path: `${out}/variant-${i + 1}-${tag}.png`, fullPage: tag === 'mobile' ? false : true });
      await p.close();
    }
  }
  await b.close();
})();
"""


def cmd_shots(a):
    if not shutil.which("node"):
        sys.exit("variants: node is needed for screenshots (npm i -D playwright)")
    os.makedirs(a.out, exist_ok=True)
    js = os.path.join(a.out, "_shots.cjs")
    open(js, "w").write(SHOT_JS)
    pages = [p if p.startswith("http") else os.path.abspath(p) for p in a.pages]
    r = subprocess.call(["node", js, os.path.abspath(a.out), *pages])
    os.remove(js)
    print(f"screenshots in {a.out}" if r == 0 else "screenshot run failed (is playwright installed? note: file:// pages that import modules need a local server, pass http urls)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--deviation", type=int, required=True, choices=range(1, 11)); p.add_argument("--count", type=int, default=5, choices=range(1, 6)); p.add_argument("--seed", type=int, default=None); p.add_argument("--project")
    p = sub.add_parser("gallery"); p.add_argument("pages", nargs="+"); p.add_argument("--labels"); p.add_argument("--out", default=".cutecore/variants/index.html")
    p = sub.add_parser("shots"); p.add_argument("pages", nargs="+"); p.add_argument("--out", default=".cutecore/variants")
    a = ap.parse_args(argv)
    if getattr(a, "pages", None) and len(a.pages) > 5:
        sys.exit("variants: five at most, so the choice stays easy")
    {"plan": cmd_plan, "gallery": cmd_gallery, "shots": cmd_shots}[a.cmd](a)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
