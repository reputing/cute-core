#!/usr/bin/env python3
"""components21: browse, read and install 21st.dev components from the terminal.

21st.dev serves a markdown twin of every component, category, library and author
page (append .md), which this script reads without any key. Code retrieval and
`shadcn add` installs need a 21st API key in API_KEY_21ST (free tier: 2 per day).

Usage
  components21.py categories
  components21.py browse background [--limit 30]          # list a category
  components21.py show @collabxconstruct/components/penelope
  components21.py library @gughigug/library/liquid-glass-ui
  components21.py search "pastel shader" [--tags shader,background]
  components21.py inspire candy-glass|retro|doodle|shader|liquid|mascot|bento|any
  components21.py install collabxconstruct/penelope [--run]
  components21.py mcp                                       # how to connect the 21st MCP

Use what you read here as reference for technique, never as something to copy
verbatim: the cutecore skill always makes its own spin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://21st.dev"
CACHE = os.path.join(os.path.expanduser(os.environ.get("XDG_CACHE_HOME", "~/.cache")), "cutecore", "components21")
UA = "cutecore-skill/1.0 (+components21)"

CATEGORIES = [
    "hero", "features", "ai-chat", "cta", "pricing-section", "testimonials", "navigation", "card",
    "button", "animated", "footer", "login", "dashboard", "dialog", "form", "table", "sidebar",
    "landing-page", "text-animation", "background", "marquee", "carousel", "tabs", "tooltip",
    "avatar", "badge", "chart", "accordion", "search", "notification", "shader", "animation",
]

# Which categories to mine for each cutecore mode. These are starting points for
# technique research; the skill restyles and reinvents whatever it learns.
INSPIRE = {
    "candy-glass": ["dashboard", "card", "chart", "sidebar"],
    "liquid": ["card", "navigation", "button", "tabs"],
    "retro": ["text-animation", "card", "button", "background"],
    "doodle": ["footer", "animated", "card", "hero"],
    "shader": ["shader", "background", "animation", "hero"],
    "mascot": ["animated", "hero", "background"],
    "bento": ["features", "dashboard", "card"],
    "any": ["hero", "features", "animated", "background"],
}


def fetch(path: str, ttl: int = 86400, accept: str = "text/markdown") -> str:
    url = path if path.startswith("http") else BASE + path
    os.makedirs(CACHE, exist_ok=True)
    cp = os.path.join(CACHE, hashlib.sha1((url + accept).encode()).hexdigest())
    if os.path.exists(cp) and time.time() - os.path.getmtime(cp) < ttl:
        return open(cp, encoding="utf-8").read()
    headers = {"User-Agent": UA, "Accept": accept}
    key = os.environ.get("API_KEY_21ST")
    if key and "/api/" in url:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            text = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"components21: {url} has no markdown twin (404). Check the path.")
        if e.code == 401:
            sys.exit("components21: this needs a 21st API key. Create one at https://21st.dev/mcp and export API_KEY_21ST.")
        raise
    except Exception as e:
        if os.path.exists(cp):
            return open(cp, encoding="utf-8").read()
        sys.exit(f"components21: could not reach {url} ({e}). Is 21st.dev allowed on this network?")
    with open(cp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


LINK = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>https://21st\.dev/[^)]+?)(?:\.md)?\)(?: [^\w]+ by (?P<author>.+))?$", re.M)


def parse_list(md: str):
    out = []
    for m in LINK.finditer(md):
        url = m.group("url").removesuffix(".md")
        out.append({"title": m.group("title"), "path": url.replace(BASE, ""), "author": (m.group("author") or "").strip()})
    return out


def norm_path(ref: str) -> str:
    ref = ref.strip().replace(BASE, "")
    ref = ref.removesuffix(".md")
    if not ref.startswith("/"):
        ref = "/" + ref
    if not ref.startswith("/@") and ref.count("/") == 2:  # author/slug shorthand
        a, s = ref.strip("/").split("/")
        ref = f"/@{a}/components/{s}"
    return ref


def cmd_categories(a):
    print("\n".join(CATEGORIES))
    print("\nAny tag works too: components21.py browse <tag>")


def cmd_browse(a):
    md = fetch(f"/community/components/s/{a.tag}.md")
    items = parse_list(md)[: a.limit]
    head = md.splitlines()[0] if md else a.tag
    print(head)
    for i in items:
        print(f"  {i['path']:<70} {i['title']}" + (f"  ({i['author']})" if i["author"] else ""))


def cmd_show(a):
    print(fetch(norm_path(a.ref) + ".md"))


def cmd_library(a):
    print(fetch(norm_path(a.ref) + ".md"))


def _words(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def cmd_search(a):
    if os.environ.get("API_KEY_21ST"):
        qs = urllib.parse.urlencode({"q": a.query, "scope": "public", "limit": a.limit})
        data = json.loads(fetch(f"/api/v1/components/search?{qs}", accept="application/json"))
        for r in data.get("results", []):
            print(json.dumps(r)[:300])
        return
    # Keyless fallback: rank titles from relevant category listings.
    tags = a.tags.split(",") if a.tags else CATEGORIES[:12] + ["shader", "animation"]
    q = _words(a.query)
    seen, hits = set(), []
    for t in tags:
        try:
            items = parse_list(fetch(f"/community/components/s/{t.strip()}.md"))
        except SystemExit:
            continue
        for i in items:
            if i["path"] in seen:
                continue
            seen.add(i["path"])
            score = len(q & _words(i["title"] + " " + i["path"]))
            if score:
                hits.append((score, t, i))
    hits.sort(key=lambda h: -h[0])
    print(f"# keyless title search over {len(seen)} components in {len(tags)} categories"
          " (set API_KEY_21ST for full-text search)")
    for score, t, i in hits[: a.limit]:
        print(f"  [{t}] {i['path']:<66} {i['title']}")
    if not hits:
        print("  no title matches; try `browse <category>` or broader words")


def cmd_inspire(a):
    tags = INSPIRE.get(a.mode, INSPIRE["any"])
    for t in tags:
        items = parse_list(fetch(f"/community/components/s/{t}.md"))[: a.limit]
        print(f"## {t}")
        for i in items:
            print(f"  {i['path']:<70} {i['title']}")
    print("\nRead any of these with `show <path>` for its description, deps and technique."
          " Treat them as technique references: restyle, recombine and reinvent, never copy.")


def cmd_install(a):
    ref = norm_path(a.ref)
    m = re.match(r"^/@([^/]+)/components/(.+)$", ref)
    if not m:
        sys.exit("components21: expected author/slug or /@author/components/slug")
    url = f"{BASE}/r/{m.group(1)}/{m.group(2)}?api_key=$API_KEY_21ST"
    cmd = f'npx shadcn@latest add "{url}"'
    if not os.environ.get("API_KEY_21ST"):
        print("API_KEY_21ST is not set. Create a key at https://21st.dev/mcp, then run:")
        print("  export API_KEY_21ST=21st_sk_...")
    print(cmd)
    if a.run:
        if not os.environ.get("API_KEY_21ST"):
            sys.exit(1)
        sys.exit(subprocess.call(shlex.split(cmd.replace("$API_KEY_21ST", os.environ["API_KEY_21ST"]))))


def cmd_mcp(a):
    print("""21st MCP (formerly Magic MCP) for Claude Code:

  npx @21st-dev/cli@latest init --client claude --write

Then paste a key from https://21st.dev/mcp. Endpoint: https://21st.dev/api/mcp
(read only: https://21st.dev/api/mcp/readonly). Tools include search, get_component,
get_inspiration, search_logo and generate. search and search_logo are free.

Icons need none of this: scripts/icons21.py talks to the free icon catalogue directly.""")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("categories").set_defaults(fn=cmd_categories)
    p = sub.add_parser("browse"); p.add_argument("tag"); p.add_argument("--limit", type=int, default=30); p.set_defaults(fn=cmd_browse)
    p = sub.add_parser("show"); p.add_argument("ref"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("library"); p.add_argument("ref"); p.set_defaults(fn=cmd_library)
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("--tags"); p.add_argument("--limit", type=int, default=20); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("inspire"); p.add_argument("mode", nargs="?", default="any", choices=list(INSPIRE)); p.add_argument("--limit", type=int, default=8); p.set_defaults(fn=cmd_inspire)
    p = sub.add_parser("install"); p.add_argument("ref"); p.add_argument("--run", action="store_true"); p.set_defaults(fn=cmd_install)
    sub.add_parser("mcp").set_defaults(fn=cmd_mcp)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
