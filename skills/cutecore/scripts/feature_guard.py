#!/usr/bin/env python3
"""feature_guard: prove a restyle or rebuild kept every feature.

  feature_guard.py snapshot <paths...> [--out .cutecore/features.before.json]
  feature_guard.py compare  <paths...> [--before .cutecore/features.before.json] [--allow "text:Old label"]
  feature_guard.py snapshot-url <url> --out blueprint-features.json   # from a dissect blueprint.json

The inventory is what a user could notice going missing:
  controls   buttons, links (href), inputs (name/type/placeholder), selects, textareas, forms (action/method)
  behaviour  event handlers (onClick=, @click, on:click, addEventListener('x')), keyboard shortcuts
  data       fetch/axios/WebSocket/EventSource endpoints, supabase .from('table'), API route files
  content    headings, aria-labels, alt text, ids, data-testid
  exports    exported components/functions, routes (Next app/pages dirs, Astro pages, React Router paths)

`compare` exits 1 if anything from the snapshot is gone, listing each item, so the
redesign can be fixed before the user ever sees it. Additions are fine and listed.
Use --allow for removals the user explicitly asked for.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

EXTS = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro", ".mdx"}
SKIP = {"node_modules", ".git", ".next", "dist", "build", ".cutecore", ".turbo", ".vercel", "coverage", "out", ".svelte-kit", ".astro"}

P = {
    "button": re.compile(r"<button\b[^>]*>\s*(?:<[^>]+>\s*)*([^<{]{1,60})", re.I),
    "link": re.compile(r"<(?:a|Link|NuxtLink|RouterLink)\b[^>]*\b(?:href|to)\s*=\s*[\"'{]([^\"'}]+)", re.I),
    "input": re.compile(r"<(?:input|Input)\b[^>]*?(?:name|id)\s*=\s*[\"']([^\"']+)", re.I),
    "textarea": re.compile(r"<(?:textarea|Textarea)\b[^>]*?(?:name|id)\s*=\s*[\"']([^\"']+)", re.I),
    "select": re.compile(r"<(?:select|Select)\b[^>]*?(?:name|id)\s*=\s*[\"']([^\"']+)", re.I),
    "form": re.compile(r"<form\b[^>]*?(?:action|onSubmit|@submit|on:submit)\s*=\s*[\"'{]([^\"'}]+)", re.I),
    "handler": re.compile(r"\b(?:on[A-Z]\w+|@\w+(?:\.\w+)*|on:\w+)\s*=\s*[{\"']\s*([\w.]+)", re.M),
    "listener": re.compile(r"addEventListener\(\s*[\"'](\w[\w:-]*)[\"']"),
    "shortcut": re.compile(r"(?:e|event|ev)\.(?:key|code)\s*===?\s*[\"']([^\"']+)[\"']"),
    "endpoint": re.compile(r"(?:fetch|axios(?:\.\w+)?|ky(?:\.\w+)?|new\s+(?:WebSocket|EventSource))\(\s*[`\"']([^`\"']+)"),
    "table": re.compile(r"\.from\(\s*[\"'](\w+)[\"']\s*\)"),
    "heading": re.compile(r"<h[1-4]\b[^>]*>\s*(?:<[^>]+>\s*)*([^<{]{2,80})", re.I),
    "aria": re.compile(r"aria-label\s*=\s*[\"']([^\"']+)"),
    "alt": re.compile(r"\balt\s*=\s*[\"']([^\"']+)"),
    "id": re.compile(r"\bid\s*=\s*[\"']([\w-]+)[\"']"),
    "testid": re.compile(r"data-testid\s*=\s*[\"']([^\"']+)"),
    "export": re.compile(r"export\s+(?:default\s+)?(?:async\s+)?(?:function|const|class)\s+(\w+)"),
    "route": re.compile(r"<Route\b[^>]*path\s*=\s*[\"']([^\"']+)|path:\s*[\"'](/[^\"']*)[\"']"),
}


def files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, fs in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for f in fs:
                if os.path.splitext(f)[1] in EXTS:
                    yield os.path.join(root, f)


def route_from_path(path):
    m = re.search(r"(?:^|/)(?:app|pages|src/pages|src/routes)/(.+?)(?:/page|/\+page|/index)?\.(?:tsx|jsx|ts|js|astro|svelte|vue|mdx)$", path.replace(os.sep, "/"))
    if m and not re.search(r"(^|/)(_|layout|loading|error|not-found|\+layout)", m.group(1)):
        return "/" + m.group(1).replace("index", "").strip("/")
    return None


def inventory(paths):
    inv = {k: set() for k in P}
    inv["page"] = set()
    for f in files(paths):
        try:
            text = open(f, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        for k, rx in P.items():
            for m in rx.finditer(text):
                val = next((g for g in m.groups() if g), "").strip()
                val = re.sub(r"\s+", " ", val)
                if val and not val.startswith(("data:", "#{", "${")) and len(val) < 160:
                    inv[k].add(val)
        r = route_from_path(f)
        if r is not None:
            inv["page"].add(r or "/")
    return {k: sorted(v) for k, v in inv.items() if v}


def from_blueprint(bp):
    inv = {"button": set(), "link": set(), "input": set(), "form": set(), "endpoint": set(), "heading": set(), "listener": set()}
    for i in bp.get("interactive", []):
        if i["tag"] == "button" and i.get("text"):
            inv["button"].add(i["text"])
        if i.get("href"):
            inv["link"].add(i["href"])
        if i["tag"] in ("input", "textarea", "select") and (i.get("name") or i.get("text")):
            inv["input"].add(i.get("name") or i.get("text"))
    for a in bp.get("apis", []):
        inv["endpoint"].add(a.split(" ", 1)[-1])
    for l in bp.get("windowListeners", []) + bp.get("documentListeners", []):
        inv["listener"].add(l)
    return {k: sorted(v) for k, v in inv.items() if v}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("paths", nargs="+"); s.add_argument("--out", default=".cutecore/features.before.json")
    c = sub.add_parser("compare"); c.add_argument("paths", nargs="+"); c.add_argument("--before", default=".cutecore/features.before.json"); c.add_argument("--allow", action="append", default=[])
    u = sub.add_parser("snapshot-url"); u.add_argument("blueprint"); u.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    if a.cmd in ("snapshot", "snapshot-url"):
        inv = inventory(a.paths) if a.cmd == "snapshot" else from_blueprint(json.load(open(a.blueprint)))
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        json.dump(inv, open(a.out, "w"), indent=2)
        print(f"snapshot: {sum(len(v) for v in inv.values())} features in {len(inv)} kinds -> {a.out}")
        return
    before = json.load(open(a.before))
    after = inventory(a.paths)
    allowed = set(a.allow)
    missing, added = [], []
    for k, vals in before.items():
        now = set(after.get(k, []))
        for v in vals:
            if v not in now and f"{k}:{v}" not in allowed:
                missing.append(f"{k}: {v}")
    for k, vals in after.items():
        old = set(before.get(k, []))
        added += [f"{k}: {v}" for v in vals if v not in old]
    if added:
        print(f"+ {len(added)} added (fine):")
        for x in added[:40]:
            print("   +", x)
    if missing:
        print(f"\n✗ {len(missing)} feature(s) went missing. Put them back, or ask the user and pass --allow \"kind:value\":")
        for x in missing:
            print("   -", x)
        sys.exit(1)
    print("✓ every feature from the snapshot is still here")


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
