# Media patterns — how screenshots sit on a slide

Pick a pattern by name. Do not invent a one-off layout per slide: the whole point is that
paging through a run of demo slides shows images in the same places at the same sizes, so
nothing jumps.

Every pattern obeys the same two rules:

- **Only ever constrain one axis per image.** `width:auto; height:auto` plus `max-width` /
  `max-height`. Setting `height:52%` *and* `max-width:30%` stretches the picture — see gotcha 23.
- **Sizes are pattern constants, not per-slide tuning.** If a slide needs different numbers,
  crop the source image (`scripts/prep_screenshots.py`), don't add a per-slide override.

## The patterns

| Pattern | Use for | Shape |
|---|---|---|
| `single` | one screenshot | fills the media column, centred |
| `two-up` | a desktop view **and** a phone view of the same app | side by side, right-aligned |
| `overlap` | a main screen with a small secondary one (an assistant panel, a sub-form) | inset over the bottom-right corner |
| `stack` | 2–3 **wide** screens that tell a sequence | stepping down and right |
| `cascade` | 3 **portrait** screens, or a mixed set | stepping down and right, taller |

```css
/* ---------- shared ---------- */
.shotwrap        { flex:0 1 auto; min-height:0; display:flex; align-items:center;
                   justify-content:center; min-width:0; }
.shotwrap img    { max-width:100%; max-height:100%; width:auto; height:auto;
                   border:1px solid var(--rule); border-radius:10px;
                   box-shadow:0 16px 44px rgba(26,0,96,.30), 0 4px 12px rgba(26,0,96,.16); }

/* ---------- two-up: wide + phone ---------- */
.shotwrap.two                     { gap:16px; }
.shotwrap.two img:first-child     { max-width:70%; }
.shotwrap.two img:last-child      { max-width:25%; }

/* ---------- overlap: small screen over the corner of a big one ---------- */
.shotwrap.overlap                 { position:relative; display:block; height:100%; }
.shotwrap.overlap .main           { position:absolute; left:0; top:0; max-width:88%; max-height:88%; }
.shotwrap.overlap .inset          { position:absolute; right:2%; bottom:9%; width:46%;
                                    box-shadow:0 18px 46px rgba(26,0,96,.38); }

/* ---------- stack: 2–3 wide screens ---------- */
.shotwrap.stack                   { position:relative; display:block; height:100%; }
.shotwrap.stack img               { position:absolute; width:68%; max-width:none; }
.shotwrap.stack img:nth-child(1)  { left:0;   top:2%; }
.shotwrap.stack img:nth-child(2)  { left:22%; top:38%; }
.shotwrap.stack.three img              { width:62%; }
.shotwrap.stack.three img:nth-child(1) { left:0;   top:0; }
.shotwrap.stack.three img:nth-child(2) { left:15%; top:22%; }
.shotwrap.stack.three img:nth-child(3) { left:30%; top:44%; }

/* ---------- cascade: 3 portrait screens ---------- */
.shotwrap.cascade                     { position:relative; display:block; height:100%; }
.shotwrap.cascade img                 { position:absolute; height:78%; width:auto; max-width:none; }
.shotwrap.cascade img:nth-child(1)    { left:0;   top:0; }
.shotwrap.cascade img:nth-child(2)    { left:26%; top:11%; }
.shotwrap.cascade img:nth-child(3)    { left:52%; top:22%; }

/* mixed orientations inside a cascade — BOTH caps on the tall one, never a fixed height */
.shotwrap.cascade.mixed img.wide      { height:52%; }
.shotwrap.cascade.mixed img.tall      { height:auto; width:auto; max-height:80%; max-width:30%; }
.shotwrap.cascade.mixed img:nth-child(1) { left:0;   top:2%; }
.shotwrap.cascade.mixed img:nth-child(2) { left:14%; top:34%; }
.shotwrap.cascade.mixed img:nth-child(3) { left:66%; top:6%; }
```

## Paired images must share an aspect ratio

Two screenshots in `two-up` only render at the same height if their aspect ratios match.
Fix that in the **image**, not the CSS:

```bash
python3 scripts/prep_screenshots.py in.png out.jpg --match assets/other_desktop.jpg
python3 scripts/prep_screenshots.py phone.png out.jpg --aspect 0.462 --trim right
```

Cropping loses a few rows; squashing loses credibility. Always crop, and say which edge you
trimmed so the owner can re-capture if it mattered.

## Order the images by the story, not by upload order

Three screenshots on one slide should read left→right as the process runs: request form →
record → report. It turns a pile of pictures into the slide's argument.

## Placeholders

If a screenshot is expected but not supplied, render the labelled box — never leave the
column empty and never quietly re-balance the slide so the gap doesn't show:

```html
<div class="shotbox"><span>Procurement app &mdash; screenshot</span></div>
```
