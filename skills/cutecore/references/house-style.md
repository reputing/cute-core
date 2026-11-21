# House style: sticker postcard

Scope: this is the default look for new or unbranded work. When a site already
has an art direction (kuro.rip, the user's own project), run `brand.py` first
(SKILL.md step 2b): the brand keeps its palette, type, art and mascot, and this
house style contributes its craft (states, press physics, primitives, motion
rules) wearing the brand's colours via `brand.css`.

The default look of everything this skill makes. It follows chessie.cat's
guestbook closely (the user's chosen anchor) and expands it with flavours,
mascots, shaders and the patterns from the other curated sites. The tokens and
primitives are implemented in `assets/cute-tokens.css`; link or inline it.

The feeling: a pastel stationery drawer. Paper, stickers, stamps, tape,
postcards, a cat that peeks. Everything has a rim and a little drop, everything
answers a press. Nothing is glass unless asked; nothing is flat.

## 1. Tokens

Every colour is a role, defined twice (light and dark). Never hardcode a hex in
a component; add a role instead.

| role | strawberry light | dark | use |
|---|---|---|---|
| `--bg` | `#fff6f8` | `#241a2c` | page paper |
| `--surface` | `#ffeaf0` | `#31233c` | raised areas |
| `--paper` | `#fffafc` | `#2b2034` | cards |
| `--border` | `#f7c6d5` | `#4e3a5f` | 2px card borders, dotted dividers |
| `--text` / `--text-muted` | `#3d2230` / `#6f4a5b` | `#eadcef` / `#b9a3c4` | ink |
| `--accent` / `--accent-press` | `#b8335f` / `#8f003e` | `#f4afc6` / `#cc8aa0` | primary, its pressed edge |
| `--accent-soft` / `--accent-bright` | `#ffd0df` / `#f47fa6` | `#5c3d58` / `#f59ab9` | fills, lines |
| `--alt` / `--alt-2` | lilac / baby blue | | second and third flavour, stamps, tags |
| `--sticker-rim` / `--sticker-shadow` | `#fff` / `#eea3bb` | `#8a5f8a` / `#150e1b` | die-cut rim and candy drop |
| `--glow`, `--star` | transparent | `#f59ab9`, `#f8d8e3` | only dark mode glows and has stars |

Flavours swap the whole set: `data-flavor="strawberry | grape | blueberry | cotton"`.
`cotton` is the pink + purple + blue triad on one page. Theme: `data-theme="light|dark"`.
Contrast: body text on `--bg` must stay above 7:1, muted text above 4.5:1 (all
shipped pairs pass; check new ones with `scripts/palette.py check`).

Type: Fredoka (display, 600 to 700) over Nunito (body, 400 to 600). Display
headings are `--display` coloured. Rounded only; no serif, ever, unless the user
asks. Alternatives with the same soul: Darumadrop One (very round), Mali or
Patrick Hand (handwritten notes), Silkscreen / Pixelify Sans (retro labels),
Zen Maru Gothic / M PLUS Rounded 1c (Japanese).

Radii: 7 / 14 / 22 / pill. Rims: 3px white. Card borders: 2px `--border`.
Spacing rhythm: 4px base; cards pad 24 to 28px; generous air around headings.

Motion (one system, two families, from chessie + ivy.rest):

- spatial (move, size, shape) springs: `--ease-snappy cubic-bezier(.23,1,.32,1)` 200ms,
  `--ease-jelly cubic-bezier(.34,1.56,.64,1)` for anything squishy.
- effects (colour, opacity) never overshoot: plain ease 150 to 200ms.
- drawing (strokes, unrolls): `--ease-draw cubic-bezier(.77,0,.175,1)`.
- Hover lifts 2px and the drop grows 2px to 4px; press sinks 2px, scales .97,
  and the drop becomes an inset. Pressed transitions run at 100ms.
- Every looping animation pauses under `data-motion="off"` and
  `prefers-reduced-motion`. Ship the toggle ("Pause animation" link in the
  footer) on every page.

## 2. Primitives (class names in cute-tokens.css)

- **Awning header** `.cc-awning`: `--accent-soft` with a white halftone dot
  pattern (`radial-gradient(var(--halftone) 1.6px, transparent 2px) / 14px`),
  a scalloped bottom edge made from a repeating radial gradient (2.25rem
  scallops), and a drop-shadow filter in `--sticker-shadow`. On first load it
  unrolls (`clip-path: inset(0 0 100%)` to `inset(0 0 -48px)`), then nav
  stickers press in with a 28ms stagger.
- **Wordmark** `.cc-wordmark`: display font, rotated -3deg, text stroke .26em
  in the rim colour with `paint-order: stroke fill`, a tag pill in `--accent`
  with a paw (fetch the paw from 21st: `icons21.py get phosphor/paw-print --style fill`).
- **Sticker button** `.cc-sticker` / lit `.cc-sticker-lit`: 3px white rim,
  14px radius, `0 2px 0` drop. Nav items are stickers with a 21st icon at the
  left; the current page is lit.
- **Folder tabs + card** `.cc-tabs .cc-tab .cc-card`: tabs sit on the card's top
  edge, the selected tab merges into the card (same fill, no bottom border).
- **Note chip** `.cc-note`: pill in `--accent-soft` with an eye/heart icon, for
  "Chessie reads every postcard"-style reassurances.
- **Lined fields** `.cc-lined` (textarea with ruled lines that scroll with the
  text via `background-attachment: local`) and `.cc-input` (single underline).
  Labels in 600, counters and "optional" in small muted text on the right.
- **Dividers**: vertical 2px dashed between form columns, horizontal 2px dotted
  between list items. Never solid grey lines.
- **Stamp** `.cc-stamp`: perforated edge via a radial-gradient mask, letter or
  icon inside, `data-tilt` rotates it and switches to the alt flavour. Used for
  avatars without photos, the postage corner of forms, song tiles.
- **Reactions + replies**: `.cc-reaction` (round sticker with an icon that pops
  on click: rotate -12deg scale .6, overshoot to 1.3, settle) and `.cc-reply`
  (soft bubble with a nub and a bold "replied" label with a paw).
- **Wave underline** `.cc-wave`: a squiggle under page titles and section
  headings, drawn on first load (`stroke-dasharray` + `--ease-draw`).
- **Backdrop** `.cc-backdrop`: four layers, all fixed and non-interactive: a slow
  115deg sky gradient that drifts, halftone dots only at the page edges (masked
  out of the reading column), 4-point sparkles wandering on 9 to 13 s loops,
  and grain. In dark mode add 2px twinkling stars and a top light.
- **EQ bars** `.cc-eq`: three 3px bars for now-playing indicators.
- **Peeking mascot**: during focused moments (reading lyrics, sending a
  postcard), the mascot's head rises from behind a card edge and its paws grip
  the edge; it nods left/right in time with content and blinks every few
  seconds (`cc-blink`, `cc-tail`, `cc-peek`). WebGL version: `mascot.md`.

## 3. Page skeleton (the guestbook, as the canonical example)

1. Awning header: wordmark left; nav stickers centre (About, Music, Guestbook,
   Friends, Now, More); right cluster of language pills, theme toggle (sun/moon
   in a two-cell sticker), search sticker.
2. Reading column `max-width: 65ch`, centred, left aligned text.
3. Title block: square stamp-icon tile + display title + wave underline; one
   sentence intro ("Leave a hello or anything you like.").
4. Folder tabs (Postcard / Song) on a card. Card: heading, reassurance chip,
   postage stamp top right, two columns (lined message with 0/500 counter |
   name + optional website), lit send button bottom right ("Send to <name>"),
   dotted divider, "What's kept" disclosure.
5. List heading with count in small type and a mini wave. Entries: stamp avatar
   (initial letter or song icon) | name (600), date (muted), website as an
   underlined small link | message | reaction row ("<owner> reacted") | optional
   reply bubble. Song entries show title, artist and "From <name>".
6. Footer: heart line ("Thanks for poking around."), then © · Colophon ·
   Privacy · Back to top, and "Pause animation" on the right.

Interaction details that make it feel finished: entries arrive with a 4px rise
(`cc-arrive`), sent postcards play a postmark draw, the song tab plays a
cassette reel spin, language switch slides, page changes use the View
Transitions API (`pageswap` / `pagereveal`), every state has a skeleton.

## 4. Expansions (where this skill goes further than the anchor)

Pick by deviation level (SKILL.md). Each must keep every existing feature.

- **Flavour switcher** sticker (strawberry, grape, blueberry, cotton) next to the
  theme toggle, persisted per visitor.
- **WebGL mascot** that lives on the page: sits on the card's top edge, looks
  at the cursor, walks to a postcard when it is hovered, celebrates a send.
- **Shader sky** replacing the CSS gradient (`shader-canvas.js` preset
  `cotton-sky`), still masked away from the text column.
- **Feature trail** from blushie for any multi-section page: numbered scallop
  badges that morph on hover, a doodled wavy spine, a live miniature in every card.
- **Postcard rail** view toggle: entries as tilted postcards in a horizontal
  snap rail (chessie's `.postcard-rail`), stamps alternating flavours.
- **Sticker reactions** from a 21st icon pack with doodle boil (`--doodle`).
- **Device frame** from lwsg / ivy for profile pages: bezel, cat-ear notch,
  widget tiles in M3 cookie shapes.
- **Guestbook extras**: drawn doodles as signatures (canvas with a 4-colour
  crayon), mood stamps, "visited from" postmarks with the visitor's local time.

## 5. Things that break the style

Glassmorphism by default, gradients on text, neon on light mode, drop shadows
that are blurry instead of solid drops, grey hairlines, serif type, em dashes,
Inter, icons drawn by hand instead of fetched from 21st, three identical cards
in a row, centred everything, SaaS copy. `scripts/deslop.py` catches most of these.
