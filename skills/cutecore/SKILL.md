---
name: cutecore
description: Cutecore design engine for web UI. Builds pastel pink, purple and blue interfaces in a sticker-postcard house style (modelled on chessie.cat, pushed further), uses real 21st.dev icons instead of drawn SVGs, cutecore-ifies every 21st.dev category (candy glass dashboards, jelly glass, doodle, retro, feature trails, invented bentos), ships WebGL shaders and a WebGL mascot that follows the cursor or walks the page, reverse engineers sites into 1:1 rebuilds, and lints its output for em dashes, serif fonts, generic SaaS layouts and removed features. Asks how far to deviate (1 to 10), makes up to 5 variants, remembers the pick. Use whenever the user wants cute, kawaii, pastel, y2k, cozy or cutecore UI; works on kuro.rip, guestbooks, profile or link-in-bio pages, mascots, cute shaders or 21st.dev components; wants to recreate a site like chessie.cat, blushie.gg or ivy.rest; or wants a page less generic or less AI looking, even without saying cutecore.
---

# cutecore

Make interfaces that feel like a pastel stationery drawer: paper, stickers,
stamps, tape, postcards and a little creature that notices you. Every result
should look like a person with taste made it by hand, for this site only.

The scripts live in this skill's directory (the "Base directory" shown when the
skill loads). Below, `$CC` means that directory.

## 0. Should this skill drive the work?

- **Yes, fully**: the user asks for cute / kawaii / pastel / cutecore / y2k /
  cozy UI, works on kuro.rip or a profile, guestbook, link-in-bio page, wants a
  mascot, cute shader, or a 21st.dev component made cute, or names one of the
  curated sites.
- **Yes, partly**: the user wants a UI to look less generic or less AI-made but
  not cute. Use the anti-slop gates (step 6), the variant + memory loop and the
  feature guard; skip the pastel house style unless they want it.
- **No**: backend work, data plumbing, or a design system that must stay
  corporate (a bank's admin panel, a government form) unless the user asks to
  cute it up. Say in one line that cutecore would fight the brief and offer it anyway.

## 1. Load taste first

```bash
python3 $CC/scripts/memory.py show --project <site or repo name>
```

Respect standing preferences and avoid what the user disliked before. If memory
is empty, that is fine.

## 2. Always ask how far to deviate

Before designing, ask the deviation level (1 to 10) and how many variants (1
to 5) with AskUserQuestion, unless the user already gave both in this request.
Offer these anchors; the user can type any number in "Other":

| level | meaning |
|---|---|
| 1 to 2 | re-skin: tokens, type, icons. Structure untouched |
| 3 to 4 | restyle with house primitives, motifs, one signature moment |
| 5 to 6 | recompose the layout, same features; mascot or shader expected |
| 7 to 8 | invented layout and an unexpected page metaphor |
| 9 to 10 | something that has never been done, still keeping every feature |

Deviation changes **form, never function**. At level 10 every button, field,
link, route, data source and piece of content from the original is still there
and still works. Nothing gets removed or simplified unless the user explicitly
asked for that removal. That is the rule the user cares about most.

## 2b. Lock the brand when the site already has one

If you are redesigning an existing site or app (kuro.rip, the user's own
project), its art direction is not yours to replace. Before any variant:

```bash
node $CC/scripts/dissect.cjs <live url> --interact            # look at desktop-fold.png first
python3 $CC/scripts/brand.py extract .cutecore/dissect/<host>/blueprint.json --repo . --out .cutecore/brand
```

Read `.cutecore/brand/brand.md` and load `brand.css` after `cute-tokens.css`.
From then on the **brand owns** palette, type, mood (dark/light), illustration,
ornaments and mascot; the **house style owns** craft: states, motion
discipline, primitives, layout invention, anti-slop. Concretely:
- never introduce a palette the site does not have (no "dusk rose", no
  strawberry paper on a violet night site); derive tints with `color-mix` from
  the brand colours,
- keep the display, UI and handwriting faces it uses,
- reuse its illustrations, ornaments and textures; never swap them for generic
  shapes, and never put the generic SDF mascot on a site that has its own:
  `createMascot({ image: "<their mascot png>" })` gives their character the behaviours,
- a redesign must be at least as rich as what is live: if the current site has
  an illustrated scene, neon doodles and string lights, a variant made of flat
  boxes is a downgrade, whatever its layout.

Only deviation 8+ AND an explicit "the identity can change too" from the user
unlocks palette or art direction.

## 3. Understand the job

Pick the path, then read only the references it needs:

| job | read |
|---|---|
| new page or component in the house style | `references/house-style.md`, `references/operations.md` |
| restyle existing code | the code first, then `house-style.md`; snapshot features (step 4) |
| recreate / borrow from a site ("1:1", "like this") | `references/replicate.md`, `references/curated-sites.md` |
| add a layout or feature to kuro.rip | `references/kuro-rip.md` plus the above |
| dashboard, liquid glass, retro, doodle, midnight | `references/styles.md` |
| shader background, pixel room, mascot | `references/webgl.md` |
| icons or a 21st.dev component | `references/sources-21st.md` |
| a novel bento or a feature trail | `operations.md#special-patterns`, `scripts/bento.py` |

Research tools:
```bash
node $CC/scripts/dissect.cjs <url> --interact            # full teardown + screenshots of one site
python3 $CC/scripts/cute_scrape.py crawl --max-sites 60  # discover more cutecore sites from the curated seeds
python3 $CC/scripts/cute_scrape.py report                # palette/font/motion stats from the corpus
python3 $CC/scripts/components21.py inspire candy-glass  # 21st references for a mode
```
The curated seed list is `data/sites.json`; chessie.cat/guestbook is the anchor.

## 4. Protect what exists

If there is existing UI, snapshot it before touching anything:
```bash
python3 $CC/scripts/feature_guard.py snapshot src --out .cutecore/features.before.json
```
For a site rebuild, snapshot from its blueprint (`snapshot-url`).

## 5. Make the variants

```bash
python3 $CC/scripts/variants.py plan --deviation <n> --count <k> --project <name> [--brand .cutecore/brand/brand.json]
```
With `--brand`, materials are limited to ones that fit the brand and identity stays locked.
This gives each variant a different layout model, material, motion personality
and signature moment, so five results are five ideas. Build each variant as its
own file or route (`.cutecore/variants/v1/...`). With the Agent tool available,
build variants in parallel subagents, each given the plan line, the house style
reference and the gates in step 6; otherwise build them one after another.

**What a variant is.** A variant is a real screen of the product, built with
real content, never a component spec sheet, swatch board or kitchen-sink page.
Users judge designs by looking at their own pages; a grid of tiny buttons and
inputs tells them nothing and looks generic at gallery size. For a design
system or a whole-site redesign, each variant is the same two or three real
screens (for kuro: the landing hero and the dashboard/editor, plus one inner
page), each rendered in that variant's system. The component inventory comes
later, extracted from the variant the user picks.

Building rules for every variant:
- Tokens from `assets/cute-tokens.css` (copy it into the project, or map its
  variables into the project's theme), plus `brand.css` when the site has a
  brand (step 2b). Without a brand: pink, purple and blue flavours; light and
  dark; motion toggle.
- Icons only from 21st: `python3 $CC/scripts/icons21.py get|pack|cute-pack ...`.
  Never hand write an icon path. Illustrations and doodles you draw are fine:
  mark them `data-cutecore="doodle"`.
- Shapes from `bento.py shapes`, layouts from `bento.py invent` when a bento or
  trail fits, shaders from `assets/shader-canvas.js`, the mascot from
  `assets/mascot.js` (match it to the site's own mascot, `webgl.md#mascot-from-a-brand`).
- Copy is specific and human: numbers instead of adjectives, the site's own
  voice, kaomoji and sparkle glyphs only where the site already talks that way.
- Every interactive state exists: hover, press, focus-visible, disabled,
  loading skeleton, empty, error.
- Mobile at 390px works, with no horizontal scroll.

## 6. Gate every variant before the user sees it

```bash
python3 $CC/scripts/deslop.py <variant files>           # em dashes, serif, SaaS layout/copy, hand-made icons, lorem
python3 $CC/scripts/feature_guard.py compare <variant files> --before .cutecore/features.before.json
python3 $CC/scripts/palette.py audit <tokens css>        # text contrast AA or better
```
Fix every error. Then screenshot each variant at 1440 and 390
(`variants.py shots`, needs a local server for module pages) and look at the
images yourself: if two variants look alike, change one.

**Never downgrade.** Put each variant's screenshot next to the current live
screen at the same width. Throw a variant away and rebuild it if, compared
with what is live, it is: flatter (lost illustration, glow, texture or depth),
murkier (muddier or lower contrast colours), more generic (boxes in a grid
where the site had a scene), smaller in personality (lost the mascot, the
handwritten type, the ornaments), or harder to read at gallery size. The user
should look at every variant and think it beats the current site.

Uniqueness check, in your head, for each variant: could this be mistaken for a
template, a SaaS landing page, or one of the curated sites with the colours
swapped? If yes, push the metaphor further at the level the user allowed.

## 7. Let the user pick

```bash
python3 $CC/scripts/variants.py gallery .cutecore/variants/v*/index.html --labels "..." \
  --before .cutecore/dissect/<host>/desktop-fold.png --out .cutecore/variants/index.html
```
The current site goes first as "0, the bar to beat". In chat, show each variant's
screenshot large (one image per variant, desktop only), not a grid of thumbnails,
and say in one line what is different about it. Show the gallery (or the screenshots) and ask which number wins, plus what they
love or hate in the others. AskUserQuestion holds four options; with five
variants, list all five in your message and let the user answer with a number.

## 8. Apply and remember

Apply the chosen variant to the real code paths, remove the variant scaffolding,
re-run the gates, then save the taste:
```bash
python3 $CC/scripts/memory.py record --project <name> --task "<what>" --deviation <n> --picked <k> \
  --variants "1:<label>,2:<label>,..." --loved "<...>" --disliked "<...>" --layout <bento signature if any>
```
Also save a one line summary to your own memory (memory tool, or the
project's CLAUDE.md if that is how this user keeps memory), for example:
`cutecore: kuro.rip guestbook, picked feature trail + peeking cat at deviation 6; dislikes glass`.

## House rules (the short version)

- No em dashes or en dashes anywhere, including your own chat replies.
- No serif type. Rounded faces: Fredoka, Nunito, Darumadrop One, Mali, Silkscreen.
- No generic SaaS skeleton (hero + two buttons + logo cloud + 3 feature cards +
  3 tier pricing + FAQ), no indigo-to-purple gradient text, no stock phrases.
- Solid candy drops, not blurry grey shadows. Rims, stamps, tape, scallops.
- Glass only as a frame; content sits on paper or milk.
- One signature moment per page; everything else is small and quick.
- Motion pauses for `prefers-reduced-motion` and the visible toggle.
- Never remove or simplify a feature that was not asked to go.
- Rebuilds of other people's sites keep the recipe, never their art, words,
  names or personal data.
