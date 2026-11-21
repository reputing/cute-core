# 21st.dev as a source

## Icons (free, no key): `scripts/icons21.py`

The 21st icon catalogue (~29k icons) is served by a public endpoint the script
calls directly. Sets: `lucide`, `phosphor` (9k, styles outline/fill/duotone/bold/thin/light),
`tabler`, `hugeicons`, `remix-icon`, `heroicons`, `line-md` (animated SVG),
`lucide-animated`, `animateicons-lucide`, `heroicons-animated`, `animateicons-hugeicons`.

```bash
python3 scripts/icons21.py search "bunny" --limit 8
python3 scripts/icons21.py get phosphor/heart --style duotone --format react --animate jelly --out src/icons/Heart.tsx
python3 scripts/icons21.py pack heart,star,cloud,moon,paw,bow --set phosphor --style fill --format react --out src/icons
python3 scripts/icons21.py cute-pack --format react --style duotone --out src/icons      # 40 cute essentials
python3 scripts/icons21.py get line-md/heart --doodle --sticker --format svg               # hand drawn + die cut
```

Cute defaults: phosphor `fill` or `duotone` for stickers and nav (round,
friendly); line-md for draw-on animation; lucide when the project already uses
lucide-react (keep the family, add our animation classes). Every output carries
`data-21st="set/slug"` so `deslop.py` can tell fetched icons from hand drawn ones.
Formats: `svg`, `react` (TSX, typed, `size`/`title` props), `vue`, `html`, `dataurl`
(for CSS `background` / `mask`).

Treatments layered on the real geometry: `--animate wiggle|bounce|pop|float|spin|draw|heartbeat|jelly`
(classes in `cute-tokens.css`, triggered by hovering the icon or its parent link/button),
`--doodle` (line boil), `--sticker` (white rim and pink drop).

## Components: `scripts/components21.py`

Markdown twins of every page are free; code and installs need `API_KEY_21ST`
(free tier: 2 retrievals a day; paid: unlimited).

```bash
python3 scripts/components21.py browse dashboard
python3 scripts/components21.py show automateflows/glassy-dashboard     # description, deps, install
python3 scripts/components21.py library @gughigug/library/liquid-glass-ui
python3 scripts/components21.py search "doodle footer"                   # keyless title search
python3 scripts/components21.py inspire candy-glass                      # categories to mine per mode
python3 scripts/components21.py install kedhareswer/ink-orbit-features   # prints the shadcn command
```

Use components as technique references: read what they do, then build our own
spin. Install one only when the user asks for that exact component.

## 21st MCP (optional)

`npx @21st-dev/cli@latest init --client claude --write`, then a key from
https://21st.dev/mcp. Tools: `search` (free), `get_inspiration`, `get_component`,
`search_logo` (free brand SVGs), `generate`. If the MCP is connected, prefer
`search_logo` for brand marks (Discord, Spotify, Twitch) and `get_inspiration`
for technique research.

## Reference components the user pointed at

| component | what to take |
|---|---|
| automateflows/glassy-dashboard | 4 workspace views, animated charts (gsap), workflows, CSV export, light/dark. Our version: `styles.md#candy-glass`. |
| kedhareswer/doodle-crew-footer | Sketchbook last page, dry-brush brand word, crew on the letters, doodles drifting. Ours: `styles.md#doodle` + perched mascots. |
| collabxconstruct/penelope | Paper Shaders dithering background, 4 colour palette, cursor repel. Ours: `dither-dream` preset. |
| gughigug/library/liquid-glass-ui | WebGL water engine navbar/toggle/accordion/checkout. Ours: `styles.md#jelly-liquid-glass`. |
| kedhareswer/ink-orbit-features | Bento with live diagrams (edits flowing to a hub, integrations syncing, scrubbable forecast). Ours: invented bento + feature trail with live miniatures. |
