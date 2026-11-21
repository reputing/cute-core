# kuro.rip (the target site)

What is known from the public site (dissected Nov 2026). When working inside the
kuro.rip codebase, read its code first; this file is orientation, the repo is truth.

## What it is

A page builder: "your world, your kuro". People claim `kuro.rip/<name>` and get a
page with a song that plays when someone opens it (upload, link, or catalogue
with timed lyrics), a guestbook (owner chooses who can sign), chat (DMs, groups,
public channels with images, gifs, voice), themes (colours, fonts, wallpapers,
video backgrounds, custom CSS), frames, nameplates, badges, sticker packs, a
discover page, leaderboard, page of the week, guides, pricing.

So "add it as a feature/layout on kuro.rip" means one of:
- a **page layout/template** a user can pick for their profile page,
- a **widget/feature block** that can sit on any page (guestbook style, now
  playing card, stamp wall, bento),
- a **site surface** of kuro itself (landing, discover, guides).

Ask which one if the request is ambiguous; the answer changes where code goes.

## Stack and design language observed

- Next.js (app router), React. API routes under `/api/*`: `live`, `potw`, `page`,
  `stats`, `config`, `discord`, `badges`, `social`, `roblox`, `valorant`.
- Fonts: Figtree (UI), Nunito (body), Fredoka, Mali (handwritten italic),
  Darumadrop One (display, the hero "your world, your kuro"), Silkscreen (pixel labels).
- Default look is **midnight cutecore**: deep violet night room (`#0f0a1c`,
  `#1d0b2b`, `#2a1140`) with pink and lilac light (`#ff6fb0`, `#ff8fc8`,
  `#f7a6de`, `#c8a4ff`, `#9a70e6`), neon handwritten doodles (hearts, stars,
  moon), string lights, polaroids taped to the wall, a sleepy plush mascot,
  bow and butterfly line ornaments framing the viewport, dock of round icon
  buttons, avatar stack with counts.
- Surfaces: `--surf-bg: color-mix(in srgb, var(--panel) 42%, transparent)`,
  `--surf-blur: blur(22px) saturate(1.5)`, gloss `inset 0 1px 0` 9% ink,
  lift `0 24px 56px -28px rgba(0,0,0,.7)`, three shadow steps `--k-sh-1..3`.
- 60+ keyframes: blinkies (`blinkieShine`, `blinkiePulse`), `twinkle`, `rainfall`,
  `lanternglow`, `firefly`, `mascotFloat`, `mascotBob`, `tapedrift`, `stickyin`,
  `ransomin`, `neonflicker`, `upvotePop`, `decoPop`, curtains (`kopCurtainL/R`).

## Brand lock (what every kuro redesign keeps)

Run `brand.py extract` on a fresh dissect to refresh these; as of Nov 2026:

- **Mood**: dark, a violet night (`#170d27`, `#2b0c2e`) with lavender-white ink
  (`#f5ecff`), muted ink `#7a7188` / `#b0a6c0`.
- **Light**: pink `#ffb5df` / `#f58bc8` and lilac `#e6b4ff` / `#eeb5ee` used as
  *glow*, not as flat fills: neon text shadows (`0 0 6px accent, 0 0 14px accent`),
  glowing drop-shadow doodles (`drop-shadow(0 0 3px rgba(230,180,255,.95))`).
- **Primary buttons**: candy pink gradient pills
  (`linear-gradient(#ffd9f3, #f7b3e3 55%, #ec9ad8)`) with dark ink.
- **Type**: Darumadrop One for big display words (with a 3px dark offset
  `0 3px 0 #3d1a52` plus glow), Figtree for UI, Mali italic for handwritten
  lines, Silkscreen for tiny pixel labels, Fredoka as a secondary rounded face.
- **Art** (reuse, never replace): `landing-room.webp` (the illustrated night
  bedroom with window, moon, string lights, curtains, sofa, plush),
  `brand-cat.png`, `mascot/loving.png` (the cream plush with heart eyes),
  `sparkle-*.webp`, `heart-outline.webp`, `vine-long.webp`, `butterfly-*.webp`,
  `scroll-pill.webp`, `shine.png`, neon "kuro" sign, polaroids, bow ornaments.
- **Texture**: a rough hand-drawn SVG filter (`#kwRough`, `#kwRough2`) on doodles.
- **Shapes**: lots of circles (round dock icon buttons), pills, small 2 to 5px
  radii on pixel bits, `50% 50% 45% 45%` blob avatars.
- **Motion**: twinkles, fireflies, lantern flicker, mascot float/bob, tape drift,
  neon flicker, pop-ins. Soft and ambient, never bouncy SaaS slide-ins.

## How the house style lands on kuro

The house style does not repaint kuro; it brings craft. Load `brand.css` (from
brand.py) after `cute-tokens.css` so stickers, stamps, cards and fields come out
in kuro's own colours, glow and type. What the house style adds: complete
interaction states, the sticker press physics, stamp/postcard/tape primitives
for guestbook and profile features, invented layouts, the mascot behaviours on
kuro's own mascot art (`createMascot({ image: "/mascot/loving.png" })`), and
the anti-slop and feature gates.

A strong kuro variant still shows the illustrated room (or a new scene in the
same art style) on the landing, glowing handwritten display type, candy pills,
and the plush mascot. A variant that is flat panels in a muted palette is a
downgrade and gets thrown away (SKILL.md step 6).

For the dashboard/editor: keep it a calm tool (dense, readable, Figtree), and
bring the brand in through the frame: night velvet panels with a 1px lilac
hairline and soft inner glow, candy pills for primary actions, Darumadrop only
for page titles, the plush peeking from the preview pane, sparkles at the edges
not behind text.

A user page layout must:
- read the user's theme variables (colours, font, wallpaper) instead of hardcoding,
- render every existing block the user has (song, guestbook, chat button, badges,
  socials) even if the layout does not feature it prominently,
- work with custom CSS overrides (stable class names, no `!important` in base styles),
- respect the motion toggle and `prefers-reduced-motion`,
- stay fast: WebGL (mascot, shaders) lazy-loads after first paint and pauses off screen.
