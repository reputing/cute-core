#!/usr/bin/env python3
"""memory: remember what the user picked so the next design starts from their taste.

  memory.py show [--project kuro.rip]          # print taste summary to read before designing
  memory.py record --project kuro.rip --task "guestbook layout" --deviation 6 --picked 3
                   --variants "1:sticker postcard reading column,2:jelly OS widgets,3:feature trail with mascot,..."
                   [--loved "the peeking cat, lined fields"] [--disliked "too much glass"] [--notes "..."]
                   [--layout <bento signature>] [--palette "#ffd0df,#e6d3ff"] [--fonts "Fredoka,Nunito"]
  memory.py prefer --project kuro.rip "always use the cotton flavour"   # standing preference
  memory.py forget --project kuro.rip [--all]

Where it lives: ~/.claude/cutecore/taste.json (override with CUTECORE_MEMORY).
One file across projects, keyed by project, so a taste learned on one site can
inform another while project specific rules stay put. Fingerprints of every
shipped variant are kept so bento.py and the skill can avoid repeating themselves.

Claude should also mirror a one line summary into its own memory (CLAUDE.md or
the memory tool) when the user picks, e.g. "cutecore: user picked feature trail
+ mascot at deviation 6 for kuro.rip guestbook; loved peeking cat; dislikes glass".
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter

PATH = os.path.expanduser(os.environ.get("CUTECORE_MEMORY", "~/.claude/cutecore/taste.json"))


def load():
    try:
        return json.load(open(PATH))
    except Exception:
        return {"version": 1, "projects": {}, "fingerprints": []}


def save(d):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"
    json.dump(d, open(tmp, "w"), indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)


def proj(d, name):
    return d["projects"].setdefault(name or "_global", {"picks": [], "prefs": []})


def cmd_show(a):
    d = load()
    names = [a.project] if a.project else list(d["projects"])
    if not names:
        print("no taste memory yet. After the user picks a variant, run `memory.py record ...`.")
        return
    for n in names:
        p = d["projects"].get(n)
        if not p:
            print(f"# {n}: nothing remembered yet")
            continue
        print(f"# taste for {n}")
        for pref in p["prefs"]:
            print(f"  always: {pref}")
        devs = [x["deviation"] for x in p["picks"] if x.get("deviation")]
        if devs:
            print(f"  usual deviation: {round(sum(devs) / len(devs), 1)} (last {devs[-1]})")
        loved = Counter(w.strip() for x in p["picks"] for w in (x.get("loved") or "").split(",") if w.strip())
        disliked = Counter(w.strip() for x in p["picks"] for w in (x.get("disliked") or "").split(",") if w.strip())
        if loved:
            print("  loved: " + ", ".join(k for k, _ in loved.most_common(10)))
        if disliked:
            print("  avoid: " + ", ".join(k for k, _ in disliked.most_common(10)))
        for x in p["picks"][-5:]:
            print(f"  {time.strftime('%Y-%m-%d', time.localtime(x['at']))} {x.get('task', '')}: picked \"{x.get('picked_label', x.get('picked'))}\" over {len(x.get('variants', [])) - 1} others")
    if d["fingerprints"]:
        print(f"\n{len(d['fingerprints'])} past designs fingerprinted (bento.py skips their layouts)")


def cmd_record(a):
    d = load()
    p = proj(d, a.project)
    variants = []
    for part in (a.variants or "").split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            variants.append({"n": k.strip(), "label": v.strip()})
    picked_label = next((v["label"] for v in variants if v["n"] == str(a.picked)), None)
    entry = {"at": time.time(), "task": a.task, "deviation": a.deviation, "picked": a.picked, "picked_label": picked_label,
             "variants": variants, "loved": a.loved, "disliked": a.disliked, "notes": a.notes}
    p["picks"].append(entry)
    d["fingerprints"].append({"project": a.project, "task": a.task, "layout": a.layout, "palette": a.palette, "fonts": a.fonts,
                              "label": picked_label, "at": entry["at"]})
    save(d)
    print(f"remembered: {a.project} / {a.task}: picked {a.picked}" + (f" ({picked_label})" if picked_label else ""))


def cmd_prefer(a):
    d = load()
    proj(d, a.project)["prefs"].append(a.text)
    save(d)
    print(f"standing preference saved for {a.project or 'all projects'}")


def cmd_forget(a):
    d = load()
    if a.all:
        d = {"version": 1, "projects": {}, "fingerprints": []}
    else:
        d["projects"].pop(a.project, None)
        d["fingerprints"] = [f for f in d["fingerprints"] if f.get("project") != a.project]
    save(d)
    print("forgotten")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("show"); p.add_argument("--project"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("record"); p.add_argument("--project", default="_global"); p.add_argument("--task", default="")
    p.add_argument("--deviation", type=int); p.add_argument("--picked", required=True); p.add_argument("--variants")
    p.add_argument("--loved"); p.add_argument("--disliked"); p.add_argument("--notes")
    p.add_argument("--layout"); p.add_argument("--palette"); p.add_argument("--fonts"); p.set_defaults(fn=cmd_record)
    p = sub.add_parser("prefer"); p.add_argument("text"); p.add_argument("--project", default="_global"); p.set_defaults(fn=cmd_prefer)
    p = sub.add_parser("forget"); p.add_argument("--project", default="_global"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_forget)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
