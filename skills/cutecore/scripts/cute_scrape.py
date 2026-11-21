#!/usr/bin/env python3
"""cute_scrape: discover cutecore websites and distil them into a design corpus.

  cute_scrape.py crawl [--seeds data/sites.json] [--max-sites 60] [--depth 2]
                       [--min-score 35] [--out .cutecore/corpus.json]
  cute_scrape.py site https://example.cute [--json]     # score + tokens for one site
  cute_scrape.py report [--corpus .cutecore/corpus.json] # palette/font/motif stats

How discovery works: start from the curated seeds, fetch each home page and its
stylesheets, score how cutecore it is (pastel pink/purple/blue share, rounded
display fonts, kaomoji and sparkle glyphs, cute keyframe names, 88x31 buttons,
guestbooks, webrings, oneko and friends). Outbound links from sites that score
well are queued, because cute sites link to cute sites (friends pages, button
walls, webrings). Big platforms are skipped.

What is stored: design tokens only (colour counts, fonts, radii, keyframe names,
glyph counts, detected features). No names, handles, emails, message text or
images are kept, so the corpus is safe to commit and share.

robots.txt is honoured, one request per second per host, stdlib only.
For a full visual teardown of one site use dissect.cjs instead.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter, deque

UA = "cutecore-skill/1.0 (+design-research; respects robots.txt)"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SEEDS = os.path.join(HERE, "..", "data", "sites.json")
SKIP_HOSTS = re.compile(r"(^|\.)(twitter|x|instagram|tiktok|youtube|youtu|facebook|discord(app)?|spotify|apple|google(apis|usercontent)?|gstatic|github(usercontent)?|gitlab|reddit|twitch|snapchat|telegram|t|throne|ko-fi|patreon|paypal|cash|venmo|amazon|steam(community|powered)?|last|stats|linktr|carrd|cloudflare(insights)?|jsdelivr|unpkg|cdnjs|esm|vercel|netlify|supabase|lanyard|wikipedia|pinterest|tumblr|bsky|threads|soundcloud|bandcamp|roblox|valorant|riotgames|w3|schema|mozilla|archive|fonts|cdn|imgur|giphy|tenor)\.(com|net|org|io|tv|gg|app|me|so|cc|rest|fm|co|ee|social|be|dev|sh)$", re.I)
CUTE_WORDS = re.compile(r"\b(guestbook|webring|kawaii|cute(?:core)?|pastel|sparkle|bunny|kitty|meow|nyaa?|uwu|owo|plushie|sanrio|hello ?kitty|my ?melody|kuromi|cinnamoroll|pompompurin|y2k|blinkie|stamp|88x31|oneko|shrine|neocities|dollz?|mascot|cozy|doodle)\b", re.I)
CUTE_KF = re.compile(r"@keyframes\s+([\w-]*(?:sparkle|twinkle|float|bob|wiggle|bounce|heart|paw|blink|jelly|squish|pop|glitter|bubble|boil|sway|peek|tail|wobble|drift|fairy|glow)[\w-]*)", re.I)
GLYPHS = re.compile("[♡-♥✦-❋⋆˚˖இා❀✿♪-♬【-ヿฅᴗ⸜⸝\U0001F380\U0001F496-\U0001F49F\U0001F338\U0001F33C\U0001F431\U0001F430\U0001F43E\U0001F98B\U0001F380\U0001F9F8\U0001F31F\U0001F319\U00010000-\U0001FFFF]")
KAOMOJI = re.compile(r"[\(\[][^\)\]\n]{0,6}[つづ・•˘ωᴗ´`๑≧≦ʘ◕][^\)\]\n]{0,6}[\)\]]|[:;]3|\^-?\^|>_<|uwu|owo|:D", re.I)
HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB = re.compile(r"rgba?\(\s*(\d{1,3})[ ,]+(\d{1,3})[ ,]+(\d{1,3})")
FONT = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
GFONT = re.compile(r"fonts\.googleapis\.com/css2?\?([^\"' )]+)")
RADIUS = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.I)
ROUNDED_FACES = re.compile(r"nunito|fredoka|quicksand|varela round|baloo|mochiy|zen maru|kosugi maru|m plus rounded|comfortaa|darumadrop|mali|patrick hand|gaegu|grandstander|chewy|sniglet|dynapuff|cherry bomb|pixelify|silkscreen|press start|vt323|dotgothic|outfit|figtree|delius|sour gummy|kiwi maru|hachi maru|yomogi|sniglet|coming soon|comic", re.I)


def norm_hex(h):
    h = h.lower()
    return "#" + ("".join(c * 2 for c in h) if len(h) == 3 else h)


class Fetcher:
    def __init__(self, delay=1.0):
        self.delay, self.last, self.robots = delay, {}, {}

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=10) as r:
                    rp.parse(r.read().decode("utf-8", "replace").splitlines())
            except Exception:
                rp.parse([])  # no robots.txt: allowed
            self.robots[base] = rp
        return self.robots[base].can_fetch(UA, url)

    def get(self, url, limit=1_500_000):
        if not self.allowed(url):
            return None, "robots"
        host = urllib.parse.urlsplit(url).netloc
        wait = self.delay - (time.time() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.last[host] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,text/css,*/*;q=0.5"})
            with urllib.request.urlopen(req, timeout=20) as r:
                ctype = r.headers.get("content-type", "")
                return r.read(limit).decode("utf-8", "replace"), ctype
        except Exception as e:
            return None, str(e)[:120]


def hue_bucket(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h *= 360
    if s < 0.18:
        return "neutral-dark" if l < 0.3 else "neutral-light" if l > 0.85 else "neutral"
    tone = "pastel" if l > 0.72 else "deep" if l < 0.3 else "mid"
    fam = ("pink" if h >= 300 or h < 15 else "red-orange" if h < 45 else "yellow" if h < 70 else "green" if h < 160
           else "aqua" if h < 195 else "blue" if h < 245 else "purple")
    return f"{tone}-{fam}"


def analyse(url, html, css):
    text = html + "\n" + css
    colors = Counter(norm_hex(h) for h in HEX.findall(text))
    for r, g, b in RGB.findall(text):
        try:
            colors["#%02x%02x%02x" % (int(r), int(g), int(b))] += 1
        except ValueError:
            pass
    buckets = Counter()
    for c, n in colors.items():
        buckets[hue_bucket(c)] += n
    total = sum(buckets.values()) or 1
    cute_hues = sum(n for k, n in buckets.items() if any(f in k for f in ("pink", "purple", "blue", "aqua")) and not k.startswith("deep-red"))
    pastel = sum(n for k, n in buckets.items() if k.startswith("pastel"))
    fonts = Counter()
    for fam in FONT.findall(css + html):
        for part in fam.split(","):
            part = part.strip().strip("'\"")
            if part and not part.startswith(("var(", "inherit", "initial", "-apple", "ui-", "system")):
                fonts[part] += 1
                break
    for q in GFONT.findall(html):
        for fam in re.findall(r"family=([^&:]+)", urllib.parse.unquote(q)):
            fonts[fam.replace("+", " ")] += 3
    radii = Counter(r.strip() for r in RADIUS.findall(css + html))
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    visible = re.sub(r"<[^>]+>", " ", body)
    glyphs = Counter(GLYPHS.findall(visible))
    kaomoji = len(KAOMOJI.findall(visible))
    words = Counter(w.lower() for w in CUTE_WORDS.findall(text))
    kf = sorted(set(k.lower() for k in CUTE_KF.findall(css + html)))
    features = {
        "88x31_buttons": bool(re.search(r'width=["\']?88["\']?[^>]*height=["\']?31|88x31', html, re.I)),
        "guestbook": "guestbook" in text.lower(),
        "webring": "webring" in text.lower(),
        "custom_cursor": bool(re.search(r"cursor\s*:\s*url\(", text, re.I)),
        "oneko_or_pet": bool(re.search(r"oneko|shimeji|desktop ?pet|tamagotchi", text, re.I)),
        "webgl": bool(re.search(r"webgl|three(\.module)?\.js|THREE\.|ogl|regl|shader", text)),
        "music_player": bool(re.search(r"lanyard|stats\.fm|last\.fm|now ?playing|spotify", text, re.I)),
        "pixel_font": bool(re.search(r"pixel|silkscreen|press start|vt323|minecraft|dotgothic", text, re.I)),
        "image_rendering_pixelated": "pixelated" in text,
        "view_transitions": "view-transition" in text or "pagereveal" in text,
        "reduced_motion": "prefers-reduced-motion" in text,
        "dark_mode": "prefers-color-scheme: dark" in text or "data-theme" in text,
    }
    rounded = sum(n for f, n in fonts.items() if ROUNDED_FACES.search(f))
    big_radius = sum(n for r, n in radii.items() if re.search(r"999|9999|50%|1rem|1\.\d+rem|\b(1[2-9]|[2-9]\d)px", r))
    score = (
        min(30, 30 * cute_hues / total) + min(15, 15 * pastel / total) + min(10, rounded * 2) + min(8, big_radius / 3)
        + min(10, sum(glyphs.values()) / 3) + min(6, kaomoji * 2) + min(10, sum(words.values())) + min(6, len(kf) * 1.5)
        + 3 * sum(features[k] for k in ("88x31_buttons", "guestbook", "webring", "custom_cursor", "oneko_or_pet"))
    )
    return {
        "url": url, "score": round(min(100, score), 1),
        "palette": [c for c, _ in colors.most_common(18)], "hue_mix": dict(buckets.most_common(8)),
        "fonts": [f for f, _ in fonts.most_common(8)], "radii": [r for r, _ in radii.most_common(6)],
        "glyphs": "".join(g for g, _ in glyphs.most_common(24)), "kaomoji_count": kaomoji,
        "cute_keyframes": kf[:30], "cute_words": dict(words.most_common(10)), "features": {k: v for k, v in features.items() if v},
    }


def outbound(base, html):
    out = set()
    bhost = urllib.parse.urlsplit(base).netloc.lower().removeprefix("www.")
    for href in re.findall(r'href=["\']([^"\'#]+)', html, re.I):
        u = urllib.parse.urljoin(base, href.strip())
        p = urllib.parse.urlsplit(u)
        if p.scheme not in ("http", "https"):
            continue
        host = p.netloc.lower().split(":")[0].removeprefix("www.")
        if not host or host == bhost or SKIP_HOSTS.search(host) or re.search(r"\.(png|jpe?g|gif|webp|mp3|mp4|pdf|zip)$", p.path, re.I):
            continue
        out.add(f"{p.scheme}://{p.netloc}/")
    return out


def fetch_site(f, url):
    html, ctype = f.get(url)
    if not html or "html" not in (ctype or "html"):
        return None, None
    css = []
    for href in re.findall(r'<link[^>]+rel=["\']?stylesheet["\']?[^>]*href=["\']([^"\']+)|<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\'][^>]*>', html, re.I)[:8]:
        h = href[0] or href[1]
        u = urllib.parse.urljoin(url, h)
        if "fonts.googleapis" in u:
            continue
        body, _ = f.get(u, limit=800_000)
        if body:
            css.append(body)
    return html, "\n".join(css)


def load_seeds(path):
    with open(path) as fh:
        data = json.load(fh)
    return [s["url"] for s in data.get("sites", [])] + data.get("extra_seeds", [])


def cmd_crawl(a):
    f = Fetcher(a.delay)
    seeds = load_seeds(a.seeds) + (a.add or [])
    queue = deque((u, 0) for u in seeds)
    seen, results = set(), []
    while queue and len(results) < a.max_sites:
        url, depth = queue.popleft()
        key = urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.") + urllib.parse.urlsplit(url).path
        if key in seen:
            continue
        seen.add(key)
        html, css = fetch_site(f, url)
        if html is None:
            continue
        res = analyse(url, html, css)
        res["depth"] = depth
        is_seed = depth == 0
        if is_seed or res["score"] >= a.min_score:
            results.append(res)
            print(f"{res['score']:5.1f}  d{depth}  {url}", file=sys.stderr)
            if depth < a.depth:
                for u in sorted(outbound(url, html))[:40]:
                    queue.append((u, depth + 1))
    results.sort(key=lambda r: -r["score"])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sites": results}, fh, indent=2, ensure_ascii=False)
    print(f"{len(results)} sites -> {a.out}")


def cmd_site(a):
    html, css = fetch_site(Fetcher(0), a.url)
    if html is None:
        sys.exit("could not fetch (blocked, robots.txt or not html)")
    res = analyse(a.url, html, css)
    print(json.dumps(res, indent=2, ensure_ascii=False) if a.json else
          f"score {res['score']}  palette {' '.join(res['palette'][:10])}\nfonts {res['fonts']}\nglyphs {res['glyphs']}\n"
          f"keyframes {res['cute_keyframes']}\nfeatures {list(res['features'])}")


def cmd_report(a):
    data = json.load(open(a.corpus))
    sites = data["sites"]
    pal, fonts, kf, feats, glyphs = Counter(), Counter(), Counter(), Counter(), Counter()
    for s in sites:
        pal.update(s["palette"][:10]); fonts.update(s["fonts"][:4]); kf.update(s["cute_keyframes"]); feats.update(s["features"]); glyphs.update(s["glyphs"])
    print(f"# corpus: {len(sites)} sites\n")
    print("top palette:", " ".join(c for c, _ in pal.most_common(24)))
    print("top fonts:", ", ".join(f"{f} ({n})" for f, n in fonts.most_common(14)))
    print("motion vocabulary:", ", ".join(k for k, _ in kf.most_common(30)))
    print("features:", ", ".join(f"{k} {n}" for k, n in feats.most_common()))
    print("glyphs:", "".join(g for g, _ in glyphs.most_common(30)))
    print("\nhighest scoring:")
    for s in sites[:15]:
        print(f"  {s['score']:5.1f} {s['url']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("crawl")
    p.add_argument("--seeds", default=DEFAULT_SEEDS); p.add_argument("--add", nargs="*", help="extra seed urls")
    p.add_argument("--max-sites", type=int, default=60); p.add_argument("--depth", type=int, default=2)
    p.add_argument("--min-score", type=float, default=35); p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--out", default=".cutecore/corpus.json"); p.set_defaults(fn=cmd_crawl)
    p = sub.add_parser("site"); p.add_argument("url"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_site)
    p = sub.add_parser("report"); p.add_argument("--corpus", default=".cutecore/corpus.json"); p.set_defaults(fn=cmd_report)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    main()
