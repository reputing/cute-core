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

## How the house style lands on kuro

kuro is dark first, chessie is light first. Use the house primitives with the
`data-theme="dark"` token set (`cute-tokens.css`), tuned toward kuro's violets:
`--bg #1d0b2b`, `--paper #2a1140`, `--accent #ff8fc8`, `--alt #c8a4ff`,
`--glow #ff6fb0`. Stickers keep their rim but the rim becomes a lilac line and
the drop becomes a glow. Keep kuro's own fonts (Figtree UI, Darumadrop display)
unless the layout is a user page template, where the user picks.

A user page layout must:
- read the user's theme variables (colours, font, wallpaper) instead of hardcoding,
- render every existing block the user has (song, guestbook, chat button, badges,
  socials) even if the layout does not feature it prominently,
- work with custom CSS overrides (stable class names, no `!important` in base styles),
- respect the motion toggle and `prefers-reduced-motion`,
- stay fast: WebGL (mascot, shaders) lazy-loads after first paint and pauses off screen.
