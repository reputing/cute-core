# WebGL: shaders and mascots

Contents: [Shader presets](#shader-presets) · [Custom shaders](#custom-shaders) ·
[Pixel room](#pixel-room) · [Mascot](#mascot) · [Mascot from a brand](#mascot-from-a-brand) ·
[Performance rules](#performance-rules)

## Shader presets

`assets/shader-canvas.js`, zero dependencies, ~8 KB. Copy it into the project
(e.g. `src/lib/cute/shader-canvas.js`) and mount:

```js
import { mountShader } from "./shader-canvas.js";
mountShader("#hero", { preset: "cotton-sky" });              // reads colours from CSS tokens
mountShader(el, { preset: "pixel-hearts", pixel: 4 });       // chunky retro
```

| preset | look | good for |
|---|---|---|
| cotton-sky | domain warped pastel clouds with grain | page backdrop, hero |
| jelly-blobs | gummy metaballs, one follows the cursor | candy glass, playful heroes |
| sparkle-field | 4 point sparkles in three parallax layers | dark mode, empty states |
| dither-dream | Bayer dithered waves, cursor repels | retro, print looks |
| holo-foil | iridescent sticker foil that tilts with the cursor | cards, badges, special tiles |
| cotton-mesh | slow mesh gradient (lwsg style) | device screens, quiet pages |
| pixel-hearts | scrolling pixel hearts, tamagotchi LCD | retro, loaders |

React: mount in `useEffect` and return `s.destroy`. Svelte/Vue/Astro: same in
`onMount`. 21st has more shader references: `components21.py browse shader`
(e.g. Penelope, a Paper Shaders dithering background with cursor repel).

## Custom shaders

Pass `fragment` with a `vec4 shade(vec2 uv, vec2 px)` body. Available: `uRes`,
`uTime`, `uMouse` (0..1, eased), `uIntensity`, palette `uC0..uC3`, helpers
`hash`, `noise`, `fbm`, `pal4(t)` (loops the four colours), `sparkle(p, r)`.
Keep pastel: mix toward `uC3` (the bg) rather than toward black; grain at 2 to
3 percent; no pure white blowouts over text areas.

## Pixel room

milproject-style walk-in page, cutecore version. Build with three.js (`npm i three`)
or OGL: a box room with 16x16 textures drawn on a canvas at runtime (pink wool,
lavender planks, cloud wallpaper) using `NearestFilter`, render at 1/3
resolution into a target and upscale (`image-rendering: pixelated`), camera on
a yaw rail with arrow buttons and drag to look, signs as planes with canvas text
in Silkscreen, the mascot as a billboard sprite rendered from `mascot.js`
into an offscreen canvas. Keep a plain HTML fallback of the same content for
screen readers and no-WebGL.

## Mascot

`assets/mascot.js`: a ray marched character with toon light, sticker outline,
bead eyes that follow the cursor, blush, blinking, walk cycle, jump with
squash, happy face on click, heart burst, speech bubble.

```js
import { createMascot } from "./mascot.js";
const m = createMascot({
  species: "cat",                 // cat | bunny | bear | ghost | blob | frog
  accessory: "bow",               // none | bow | flower | sprout | star
  behavior: "wander",             // follow | wander | perch | peek
  perch: ".guestbook-card",       // element to stand on (wander along it, perch, or peek over it)
  size: 120,
  colors: { body: "#fff7fb", belly: "#fff1f7", ear: "#ffc4da", blush: "#ff9dc4", ink: "#3d2230", accessory: "#f47fa6" },
});
form.addEventListener("submit", () => { m.celebrate(); m.say("got it!"); });
```

Behaviours: `follow` walks after the cursor at a polite distance; `wander`
strolls the bottom of the viewport or the top of `perch`, idling between walks;
`perch` sits on an element and watches; `peek` hides behind an element's top
edge and rises when it is hovered (chessie's lyric peek, blushie's blob).
Hook it to the page's real moments: celebrate on send, peek during reading,
look at new entries as they arrive, sleep (`setBehavior("perch")` + no look)
when the tab has been idle.

## Mascot from a brand

When the site has a mascot or logo animal, map it instead of inventing one:
1. Find it: favicon, logo, hero art, the name (kuro = black cat; chessie = cat;
   blushie = pink blob with a bow).
2. Pick the nearest species and accessory; sample its colours into `colors`
   (body = main fill, ink = outline, ear = inner ear or secondary, accessory =
   brand accent). A black cat: `body #2b2233, belly #3a2d44, ear #ff8fc8,
   blush #ff6fb0, ink #120a18`.
3. If the mascot is too specific for the SDF kit (a detailed plush, a
   character with clothes), use three.js with a GLB the user supplies, keep the
   same behaviour controller API (copy the state machine from mascot.js), and
   say so.

## Performance rules

- Lazy start after first paint (`requestIdleCallback` or after `load`).
- Pause when off screen or the tab is hidden (both assets do this).
- Cap DPR at 1.5 for backgrounds, 2 for the mascot; mascot canvas is small.
- One shader background per page. Never stack two full screen canvases.
- Under reduced motion: one still frame for shaders; mascot stays put but
  still looks and blinks.
