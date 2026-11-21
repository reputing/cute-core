# Reverse engineer and rebuild

When the user points at a site and says "recreate this", "make this a layout on
kuro.rip", or "1:1", this is the workflow. The goal is a rebuild that behaves and
feels identical, written fresh, wearing the target project's own content.

## What 1:1 means here

Match exactly: structure, proportions, spacing rhythm, type scale, colour roles,
radii, shadows, motion (keyframes, easing, durations, staggers), interaction
states, responsive behaviour, live data wiring, accessibility affordances.

Replace, always: the person's name, handle, wordmark, bio, messages, photos,
illustrations, mascot art, music, and any personal data. Those belong to someone
else. Use the target site's own content, the user's art, or tasteful
placeholders (a generic mascot from `mascot.js`, 21st icons, shader art).
Write the code yourself from the blueprint; do not paste the source's bundles.
If the user asks to copy someone's actual art or personal content, say why not
in one line and offer the swap.

## Steps

1. **Dissect.** `node scripts/dissect.cjs <url> --interact` (add `--wait 8000` for
   slow boots). Look at `desktop.png`, `desktop-fold.png`, `mobile.png` and the
   `hover-*.png` crops first, then read `blueprint.md`. For a multi page site,
   dissect each page you need.
2. **Read the source for recipes.** `source/` holds every stylesheet and script.
   Grep for the component classes you saw (`grep -o "\.sticker[^{]*{[^}]*}"`),
   the custom properties, and `@keyframes`. Note the exact values.
3. **Write a spec before code.** In `.cutecore/replica/<host>.md`:
   - layout tree with measured sizes (from the box tree),
   - token table (from Tokens + CSS custom properties, light and dark),
   - component list with every state (idle, hover, active, focus, disabled, loading, empty, error),
   - motion list (name, trigger, property, duration, easing, delay, stagger),
   - data list (each API / websocket from the blueprint and what UI it feeds),
   - feature inventory: `python3 scripts/feature_guard.py snapshot-url blueprint.json --out .cutecore/replica/<host>.features.json`.
4. **Map onto the target project.** Detect its stack and conventions before writing
   (framework, styling system, component folder, how themes/layouts are
   registered, how user data is fetched). Reuse its primitives; add the house
   tokens only where it has none. For kuro.rip see `kuro-rip.md`.
5. **Rebuild.** Tokens first, then layout skeleton, then components with all
   states, then motion, then live data. Icons via `icons21.py` (match the source
   icon family if it uses lucide/phosphor/tabler; the same glyphs exist on 21st).
6. **Verify side by side.** Screenshot your build at the same widths (1440, 390)
   and compare with the source shots. Check: column widths within 4px, type
   sizes equal, colours equal (sample with the blueprint values), every hover
   and press state, every animation timing. Fix and repeat until a glance at
   both can't tell structure apart.
7. **Prove features.** `feature_guard.py compare` against the spec inventory,
   mapped to the target's data (a guestbook post button must still post).
8. **De-slop.** `deslop.py` on the new files. If the source itself uses a serif
   or em dashes, keep fidelity only if the user said "exactly"; otherwise use
   the rounded alternative and mention it.

## Expanding beyond 1:1

"Resemble closely but make it better" (the chessie anchor) means: keep every
recipe from the spec, then layer expansions from `house-style.md#4` according to
the deviation level the user chose. Name each expansion in the summary so the
user can veto it.
