# Curated reference sites

Hand-picked by the user. Each entry says what the site does well and the recipe
behind it, measured with `scripts/dissect.cjs` (Nov 2026). Sites change, so
re-run dissect before a faithful rebuild: `node scripts/dissect.cjs <url> --interact`.

Use these as a technique library. Rebuilds use the target project's own content,
art, names and mascot (see `replicate.md`); never ship another person's images,
text, wordmark or personal details.

Contents: [chessie.cat](#chessiecatguestbook) · [blushie.gg](#blushiegg) ·
[ivy.rest](#ivyrestv2) · [schuh.wtf](#schuhwtf) · [rot.kim](#rotkim) ·
[lwsg.space](#lwsgspace) · [milproject.xyz](#milprojectxyz) · [doll.gg](#dollgg) ·
[kuro.rip (target)](kuro-rip.md)

---

## chessie.cat/guestbook

**The anchor.** Full teardown in `house-style.md`. In one line: Astro + Tailwind
4, Fredoka display over Nunito body, a pink halftone awning with a scalloped
edge, die-cut sticker buttons with a 2px candy drop, stamp-perforated letter
avatars, lined-paper fields, postcard/cassette tabs, reaction pops, reply
bubbles, slow sparkle backdrop with grain, peeking cat during lyrics, a boot
"unroll" sequence, View Transitions between pages, live `now` websocket, motion
toggle and complete light/dark token pairs. 27 named keyframes, every one tiny
and purposeful.

---

## blushie.gg

**Concept to steal: the curated feature trail.** A product page where every
feature card *is a working miniature of the feature*, not a picture of it.

- Palette: pink paper `#fae5f6`, navy ink `#1f2a4d`, periwinkle `#4a6ab5`,
  cotton pink `#f4c8eb`, sky `#e3e9f6`, white. Each card takes one flavour
  (sky / navy / pink / white / blue) so the column alternates temperature.
- Type: Google Sans Flex with the `ROND` axis at 100 (rounded terminals) at
  weight 800 for headings, tight `line-height: 1.06`. Headings highlight one
  word on a pink pill: "What it **does**", "Good **questions**".
- Layout: hero, then a two column staggered trail of numbered cards
  (`grid-template-columns: 1.42fr 1fr` inside cards). A hand-drawn wavy SVG
  "spine" runs down the centre between the columns (`.spine`: absolute, 60px
  wide, `left:50%`, from the first card to the last). Cards sit alternately left
  and right of it and overlap it slightly, so the page reads as a path you walk.
- Number badges: 54px, `clip-path` set to a scallop/cookie polygon; on card
  hover the clip-path morphs to another polygon and rotates 90deg on a spring
  `cubic-bezier(.3,1.5,.55,1)` over .8s. The card radius also springs (.6s).
- Live demos inside cards: real keycaps you can press (F8/F9/F10) that drop a
  clip into a list; a match timeline whose markers pop in; an editor with
  tracks and an export progress bar; a mini profile page with follow button;
  a "40 to 80 MB" stat with check chips. A cursor sprite (navy fill, white 1.6px
  stroke) acts out the demo.
- Keycap: `box-shadow: inset 0 0 0 1.5px #d9dff0, 0 6px 0 #d9dff0`; pressed
  state translates 5px down and the bottom shadow collapses.
- Mascot: a pink blob with blue eyes and a bow peeks over the top edge of the
  first card.
- Copy: plain, specific, numbers instead of adjectives ("About 40 to 80 MB of
  memory while it records"). FAQ titled "Good questions". Footer is a bento of
  rounded panels with pill buttons.
- Motion vocabulary: `vb-pop` (rotate -60deg from scale 0), `vb-wiggle`,
  `vb-nudge` (error shake), letter-by-letter rise for headings, blur-in for
  swapped text (`track-in`/`track-out` with `filter: blur(.14em)`).

**How the skill uses it:** the "feature trail" layout pattern (see
`operations.md#feature-trail`) and the rule *demo, don't describe*: any feature
section should contain a small interactive version of the thing.

---

## ivy.rest/v2

**Concept: the page is a device.** A Material 3 Expressive "lock screen" floating
over a wallpaper: weather tile, a giant condensed two-tone clock (hours in sky
blue, minutes stacked with AM/PM chip), a `fetch.sh` terminal tile with colour
swatches, a media tile, login in the centre, notifications column on the right,
and CPU/RAM/disk stats inside shaped badges.

- Shapes: avatar in a rounded hexagon, stats in pentagon / rounded square /
  hexagon, empty-state bell inside a 12-point cookie. Shapes are M3 Expressive
  polygons (`clip-path` or SVG), and morph between each other on interaction.
- Motion tokens, worth copying wholesale as a system:
  `--e-emphasized-decel: cubic-bezier(.05,.7,.1,1)`,
  `--e-emphasized-accel: cubic-bezier(.3,0,.8,.15)`,
  `--e-fast-spatial: cubic-bezier(.42,1.67,.21,.9)` .35s,
  `--e-spatial: cubic-bezier(.38,1.21,.22,1)` .5s,
  `--e-slow-spatial: cubic-bezier(.39,1.29,.35,.98)` .65s,
  `--e-effects: cubic-bezier(.34,.8,.34,1)` .2s.
  Spatial (position, size, shape) gets overshoot; effects (colour, opacity) never do.
- Glass tokens: `--glass: #0d0d0d8c`, `--glass-strong: #0a0a0acc`, hairlines
  `#ffffff13` / `#ffffff24`, inset highlight `0 1px 0 #ffffff0d inset`.
- Type: Google Sans Flex, Montserrat 700 for the clock, Material Symbols
  Rounded for glyphs, a mono for the terminal tile.
- Wallpapers from a JSON index, rendered with OGL; boot animation on the
  wallpaper then tiles (`v2-boot-wall`, `v2-boot-in`).

**How the skill uses it:** the "OS widget board" layout, the shape library in
`bento.py --shapes`, and the spatial/effects motion split in `house-style.md`.
Cutecore spin: pastel tiles instead of near-black, cookie shapes in pink,
clock digits in Fredoka with a sticker outline.

---

## schuh.wtf

**Concept: dark profile dashboard with a character who lives on the cards.**

- Grid: `.top-grid` 502px + 718px (profile, now playing), `.bottom-grid` 610 + 610
  (about, recent streams). Cards are dark navy panels with 1px hairline borders.
- A large anime character illustration *lies across the top edge* of the
  recent streams card (absolute, overflowing upward, z above the card), so the
  grid stops feeling like a grid. Same idea as blushie's peeking blob.
- Profile card: banner art faded into the card, round avatar with a status
  badge, name with small superscript decorations, local time chip with
  "6h ahead of you" computed from the visitor's timezone.
- About card: inline rainbow animated name (`rainbow-scroll`), a 4 x 3 wall of
  88x31 buttons (`.stamp-grid` 88px columns, pixelated), anime digit view
  counter sprites ("VIEWS").
- Live data: stats.fm recent streams, Lanyard websocket presence, a view
  counter POST. Recent streams list has search and refresh, Spotify and Apple
  Music badges per row.
- Motion: `entrance` (.8s, cubic-bezier(.2,.8,.2,1)), floating hearts, dot wave
  loader, content change flash.
- robots.txt disallows crawlers; use dissect for one-off study only.

---

## rot.kim

**Concept: art first, words whisper.** A full-viewport illustration, dimmed,
with a narrow (~520px) column floating slightly left of centre.

- Column: avatar with status dot, display name + handle with a small badge,
  two lines of bio, a Discord activity row (game art, title, state, "playing"
  label right aligned), a "music >" tab, "recent plays" list with album art,
  artist in muted grey, relative time right aligned, footer with handle and
  two tiny icons.
- Type: Karla body, DM Mono for numbers, Newsreader and Shippori Mincho for
  display (serif; in a cutecore rebuild swap to Zen Maru Gothic / M PLUS Rounded
  1c, see deslop rules, unless the user asks to keep it).
- Data: Lanyard REST + websocket, stats.fm current/recent/stats, Discord
  invites.
- Motion: username gradient sweep, lyric float, disc spin, star drift A/B/C,
  rail twinkle, row slide-in with stagger, tab fade.

---

## lwsg.space

**Concept: the screen inside a screen.** The page is framed as a device: a
rounded inner screen (`border-radius: 30px`) inset 14px from a black bezel,
with a notch tab at the top centre (`border-radius: 0 0 15px 15px`) that holds
the nav. An animated mesh-gradient `canvas.gradient-bg` fills the screen.

- Content is a single small block, IBM Plex Mono throughout, name + handle,
  three line bio in muted grey, "my team:" overlapping avatar stack with
  tooltips (`avatar-tooltip-in`), link row with icons and a live view count.
- Nav: `home | music | skills | projects | workspace | contact` as plain text
  tabs; sections swap with `view-in`.
- Easing: `--ease-spring: cubic-bezier(.32,.72,0,1)`, `--ease-out: cubic-bezier(.16,1,.3,1)`.

Cutecore spin: bezel in milk pink, notch shaped like cat ears, mesh gradient
in the pink/purple/blue triad via `shader-canvas.js` preset `cotton-mesh`.

---

## milproject.xyz

**Concept: walk into the page.** The whole site is a WebGL room built from
16px pixel textures (stone brick walls, wooden beams), a first person camera
with free look, arrow buttons to turn between walls, a wooden sign whose text
is the bio in a pixel font, a `.glb` model, Lanyard now-playing with a rainbow
animation, and a guestbook with a warning pulse.

- Key settings: `image-rendering: pixelated`, nearest filtering on textures,
  low resolution render target scaled up, Minecraft-style font.
- Cutecore spin: a pastel pixel bedroom (pink wool, lavender planks, cloud
  wallpaper), signs become sticky notes, the mascot sits on the bed. See
  `shaders.md#pixel-room`.

---

## doll.gg

**Concept: everything pops.** Pastel pink link-in-bio with a personality loader
("ur wifi must suck... jus hold on ♡"), bubbles that are born, float and pop
into burst particles and fragments, a fairy trail behind the cursor, glitter
hearts, soft idle icon motion, a guided tour with hand-drawn arrows and a
breathing highlight, an anonymous note box with a 0/200 counter.

- Palette: `#ffeef6 #fff1f7 #fce2ef #f7dce9 #f6c8de #edb5d3`, pink tinted
  shadows `rgba(255,145,198,.12)`.
- Type: hand fonts (Noteworthy, Chalkboard SE, Bradley Hand, Segoe Print)
  for notes, kaomoji and unicode sparkle glyphs in copy (`⋆౨ৎ˚⟡`, `𓏲ּ𝄢`).
- 40+ keyframes, all small: `entryBubbleBorn/Float/Pop/BurstRing/BurstParticle`,
  `fairyTrailLoop`, `pinkGlitterHeart`, `tourArrowDraw`, `softIconIdle`.
