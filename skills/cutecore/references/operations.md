# Operations: every 21st.dev category, cutecore-ified

21st.dev groups its catalogue into the categories below. For each, this is the
cutecore spin the skill builds by default (house style, then the twist).
Research technique with `components21.py browse <category>` or `inspire <mode>`;
then build our own version. Icons always come from `icons21.py`.

Contents: [Page sections](#page-sections) · [Controls](#controls) · [Data](#data) ·
[Motion and backgrounds](#motion-and-backgrounds) · [Special patterns](#special-patterns)

## Page sections

| 21st category | cutecore version |
|---|---|
| hero | Title in display font with one word on a soft pill, wave underline drawn on load, mascot sitting on the CTA, shader sky behind (masked from text). Never two CTAs + screenshot. |
| features | **Feature trail** (below) or an invented bento. Each feature shows a working miniature, not an icon grid. |
| cta | A postcard you "send": lit sticker button, stamp in the corner, postmark draws on click. |
| pricing-section | Price tags on string, or a sticker sheet where each plan is a die-cut sticker; the recommended one is lifted and lit. No three identical columns. |
| testimonials | Guestbook entries: stamp avatars, dates, reactions, owner replies. |
| navigation | Awning header with sticker nav, current page lit, scalloped edge, boot unroll. Mobile: a drawer that drops like a pull-down blind. |
| footer | Heart line, small links, "Pause animation", plus a doodle crew strip (doodle style) or a bento of rounded panels (blushie). |
| login | A lined index card with a paw stamp; social buttons as stickers; mascot covers its eyes while you type the password. |
| landing-page | Compose from the above with one metaphor carried through (stationery drawer, bedroom, device, sketchbook). |
| sidebar | Folder tabs down the side, or a binder with ring holes; active item is a tab pulled out. |

## Controls

| 21st category | cutecore version |
|---|---|
| button | `.cc-sticker` / `.cc-sticker-lit`: rim, 2px drop, lift on hover, sink on press. Variants: keycap (blushie), jelly pill (squash on press), pixel button (2px stepped border). |
| dialog | Note card that drops in with a slight tilt, tape on top, backdrop blur 6px with paper tint; mascot peeks over its edge. |
| form | Lined paper fields, dashed column dividers, counters in the label row, a stamp in the corner, friendly reassurance chip. |
| tabs | Folder tabs that merge into the card. |
| tooltip | Speech bubble with nub, rim and drop, pops with jelly. |
| accordion | Disclosure with a rotating paw or chevron, content unfolds (`::details-content` transition). Titled like "Good questions". |
| search | Sticker search button opening a dialog; results as small stamped rows; ctrl K chip. |
| badge | Tiny stamp or pill sticker; status dots that breathe. |
| avatar | Stamp with perforated edge (initial letter), or a photo in a cookie/scallop shape; stacks overlap with rims. |
| notification | Toast as a sticky note sliding in from the corner, reaction pop icon, auto dismiss with a little wave. |
| carousel | Postcard rail: tilted cards in a snap scroller, arrow stickers, dots as paw prints. |
| marquee | Ribbon banner with ruffled edges, or an 88x31 button belt. |

## Data

| 21st category | cutecore version |
|---|---|
| dashboard | **Candy dashboard** (see `styles.md#candy-glass`): an ivy.rest style widget board with tiles in cookie/hex shapes, big Fredoka clock, cute charts. |
| chart | Rounded bar caps, lollipop dots, area fills with a dotted halftone, axis labels in muted ink, tooltips as stickers. Palette from tokens, max four hues. |
| table | Ruled notebook page: dotted row lines, sticky header as a tab, row hover tints soft, sort chips as stickers. |
| ai-chat | Bubbles as note cards, typing indicator as three bouncing paws, mascot avatar that reacts to messages. |

## Motion and backgrounds

| 21st category | cutecore version |
|---|---|
| animated / animation | Small purposeful motion only: arrive (4px rise), press, pop, peek, boil. One signature moment per page. |
| text-animation | Letters rise one by one with a jelly overshoot; highlighted word gets a pill that wipes in; handwritten notes write on with `stroke-dashoffset`. |
| background | Backdrop stack (sky, edge dots, sparkles, grain) or a shader preset; always masked away from the reading column. |
| shader | `shader-canvas.js` presets: cotton-sky, jelly-blobs, sparkle-field, dither-dream, holo-foil, cotton-mesh, pixel-hearts. Custom ones follow `shaders.md`. |

## Special patterns

### Feature trail
From blushie.gg. Numbered cards alternate left and right along a doodled wavy
spine; each card takes a different flavour (sky, ink, pink, paper, blue); the
number sits in a scallop/cookie badge that morphs shape and turns 90deg on hover
(same point count clip-paths, spring easing); every card holds a live
miniature of the feature. Generate the skeleton with
`bento.py invent --style trail --tiles "a,b,c,d,e" --html preview.html`.

### Invented bento
`bento.py invent --tiles "name:weight,..." --style sticker|device|scatter`. It
refuses cliché grids and layouts already in taste memory, then adds tilt,
tape, a tile that breaks the grid edge, and one shaped tile. Bento rule of
thumb: one hero tile, one tall, one wide, the rest small, and a character or
sticker that overlaps two tiles (schuh's girl lying on the card).

### Device frame
lwsg.space / ivy.rest. Bezel with a notch (cat ears in cutecore), screen with a
shader wallpaper, widget tiles in M3 shapes (`bento.py shapes`), clock in
display type, status chips.

### Guestbook
The anchor (`house-style.md`). Postcard and song tabs, moderated note, stamp
avatars, reactions, owner replies, postcard rail view.

### Link-in-bio
doll.gg / rot.kim. Quiet column over art or sky, loader with personality,
links as sticker rows with 21st brand icons (`icons21.py search discord --set remix-icon`),
now playing with EQ bars, pop-able bubbles.

### Walk-in room
milproject.xyz. WebGL pixel room (see `shaders.md#pixel-room`), arrows to turn,
signs as sticky notes, mascot on the bed.
