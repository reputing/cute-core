# Style modes

The house style is the base. These modes change the material while keeping the
tokens, rims and motion rules. Pick by the request or by `variants.py plan`.

Contents: [Candy glass](#candy-glass) · [Jelly liquid glass](#jelly-liquid-glass) ·
[Retro](#retro) · [Doodle](#doodle) · [Midnight](#midnight)

## Candy glass

Our spin on the 21st "glassy dashboard" (automateflows): a dashboard with view
switching, animated charts, workflows and CSV export, light and dark. Keep every
one of those features; change the material from cold glass to hard candy.

- Panels: `background: color-mix(in srgb, var(--paper) 78%, transparent)` with
  `backdrop-filter: blur(10px) saturate(1.4)` only on the outer shell; inner
  tiles are opaque paper with rims. Glass is a frame, never the content surface.
- A 1px inner highlight `inset 0 1px 0 #ffffffb0` and a coloured drop
  `0 3px 0 var(--sticker-shadow)` instead of a grey blur shadow.
- Tiles in M3 shapes for stats (`bento.py shapes`), numbers in Fredoka with
  `font-variant-numeric: tabular-nums`, sparkline strokes 2.5px with round caps.
- View switcher: folder tabs or a segmented jelly pill whose thumb squashes
  between options (`--ease-jelly`).
- Charts: candy bars with rounded tops and a highlight stripe, donut as a
  sliced macaron, line chart with lollipop points; tooltips are stickers.
- Export button is a lit sticker that prints a tiny receipt animation.

## Jelly liquid glass

Our spin on liquid glass UI (gughigug's Nimbus: WebGL water engine, navbar,
toggle, accordion, checkout; "Frutiger Aero meets Apple glass"). Ours is cuter
and less glassy: gummy, milky, squishy.

- Material: milk-tinted translucent (opacity .7 to .85), pastel tint per
  flavour, thick 3px white rim, inner glow at the top edge, soft coloured
  shadow beneath like light through gummy candy.
- Refraction is subtle and only on edges: `jelly-blobs` shader or an SVG
  `feDisplacementMap` with small scale (4 to 8) on the rim area.
- Interaction is the point: press squashes (scale 1.06 .92), release wobbles
  with `cc-jelly`; toggles have a gummy thumb that stretches toward the target
  then snaps; navbars have a blob indicator that oozes between items (two
  circles joined with a goo filter: `feGaussianBlur stdDeviation 6` +
  `feColorMatrix` alpha `0 0 0 18 -7`).
- Never put body text on refractive glass. Text sits on milk.

## Retro

Pick one era and commit; mixing eras reads as noise.
- **Y2K desktop**: pastel Windows 98 chrome (2px bevels in pink/lilac), title
  bars with pixel icons from 21st (`--set pixel`-like via tabler/line-md at 16px,
  `image-rendering: pixelated` on rasters), Silkscreen labels, 88x31 button belts,
  blinkies, a visitor counter with sprite digits.
- **Tamagotchi LCD**: egg-shaped device frame, `pixel-hearts` shader at
  `pixel: 4`, a 1-bit mascot (render `mascot.js` to a small canvas and upscale
  with nearest neighbour), three round buttons.
- **Pixel room**: see `shaders.md#pixel-room`.
- **Dither print**: `dither-dream` shader, riso misregistration (two copies of
  a heading offset 1px in pink and blue with `mix-blend-mode: multiply`).
- Motion runs at 8 to 12 fps (`steps()` easing) so it feels like old hardware.

## Doodle

Hand drawn without hand drawing icons (21st doodle-crew-footer energy: brand in
dry-brush ink, a crew of characters on the letters, doodles drifting down).
- Icons: `icons21.py get <set>/<slug> --doodle` adds a line boil to the real
  21st icon (animated turbulence displacement).
- Lines, underlines, arrows, circles around words: SVG paths drawn on with
  `stroke-dasharray`/`dashoffset` and the same boil filter; mark them
  `data-cutecore="doodle"` so deslop knows they are illustration, not icons.
- Rough boxes: CSS `border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px`
  for a wobbly card, plus the boil filter on the border only.
- Type: Mali or Patrick Hand for notes, Darumadrop for big ink words, with a
  `filter: url(#boil)` on display text if it should feel brushed.
- Characters on letters: the WebGL mascot (or several, different species)
  perched on a giant wordmark via `createMascot({ behavior: "perch", perch: el })`.

## Midnight

kuro.rip default. Deep violet paper, pink and lilac light, stars and twinkles
on, stickers glow instead of drop, neon doodles (`text-shadow` 0 0 8px glow),
string lights and lanterns as slow `lanternglow` pulses.
