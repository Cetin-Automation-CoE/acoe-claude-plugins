# The slide frame — why slides stop jumping

The complaint that costs the most rebuilds is *"the layout jumps when I page through"*. It is
always the same cause: each slide sized itself around its own content. Fix it by giving every
repeating slide type a **frame** — the same absolute box on every slide — and letting content
fit inside it.

## 1. One content frame for every block slide

```css
/* everything between the title and the footer band lives here, on every slide */
.gridblock,
.advgrid.fixed,
.contentframe   { position:absolute; left:120px; right:120px; top:250px; bottom:248px; }

/* the footer band, identical position on every slide that has one */
.footnote       { position:absolute; left:304px; right:120px; bottom:124px; }
.footnote.full  { left:120px; }          /* when the slide has no legend column */
```

- `top:250px` assumes eyebrow + one-line title. Keep titles to one line, or set the title size
  per slide so the frame start never moves.
- `left:304px` on the footer aligns it with the first content column when a legend column is
  present — a full-width band under a legend column looks misaligned.
- Never size a frame with `flex:1` + `margin-top:auto`. That is what produces a block pinned to
  the floor with a hole above it.

## 2. Repeating row labels go in a legend column

When five product columns each repeat *What it is / When to use / Best for*, the labels are
noise. Put them once, in a slim left column, as tiles that echo the column headers:

```css
.gridblock      { display:grid; grid-template-columns:170px repeat(var(--n), minmax(0,1fr));
                  column-gap:14px; }
.gl.lab         { display:grid; align-content:center; padding:0 14px 0 0; }
.gl.lab span    { display:grid; align-content:center; height:62px; box-sizing:border-box;
                  background:var(--cetin-blue); color:#fff; font-weight:700; font-size:14.5px;
                  letter-spacing:1.6px; text-transform:uppercase; text-align:center;
                  border-radius:9px; padding:6px 10px; }
```

**One fixed tile height (two lines) for every label.** Sizing tiles by their own text makes
"Best for" and "Way of building" different heights and the whole column looks misaligned.

## 3. Rows share a height; cells centre vertically

```css
grid-template-rows: auto repeat(var(--rows), 1fr);   /* header + equal content rows */
.gb { display:grid; align-content:center; min-width:0; overflow-wrap:break-word; }
```

`1fr` rows, not `auto` — otherwise a wordy row in one column drags every column's rows out of
line. `display:grid; align-content:center` (not flex) keeps inline `<b>`/`<i>` on the same line
— see gotcha 1.

## 4. Demo slides: one template, fixed text column

Every demo/case-study slide in a deck must use the same skeleton, or images and tables shift as
you page:

```
eyebrow
title  +  level badge  +  presenter
tech chips  ·  slot minutes  ·  dev time  ·  users        ← only fields that have real values
┌─ text column (FIXED 780px) ─┬─ media column (the rest) ─┐
│  Before / Now / Benefits    │  one of the media         │
│  three boxes, same order    │  patterns, right-aligned  │
└─────────────────────────────┴───────────────────────────┘
what you will learn (footer band)
```

```css
.demo-top             { display:flex; gap:20px; flex:1; min-height:0; min-width:0; }
.demo-left            { flex:0 0 780px; min-width:0; display:flex; flex-direction:column;
                        gap:14px; justify-content:center; }
.demo-right           { flex:1 1 auto; min-width:0; display:flex; flex-direction:column;
                        justify-content:center; }
.demo-top .shotwrap   { justify-content:flex-end; }   /* media hugs the right edge */
```

A fixed 780px text column means the Before/Now/Benefits boxes land in exactly the same place on
every demo slide in the deck. That is the whole trick.

**Meta fields.** Render `presenter`, `slot minutes`, `dev time`, `users` only when a real value
exists. A row of "to be supplied" placeholders reads as an unfinished deck; an absent field reads
as a deliberate one.

## 5. Scope every change to the slide that asked for it

**When the user asks to change one slide, add a modifier class. Never edit a shared rule.**

```css
/* WRONG — "make the images on slide 2.3 bigger" silently resized four other slides */
.shotwrap.two img:first-child { max-width:72%; }

/* RIGHT */
.demo-top.media-wide .shotwrap.two img:first-child { max-width:72%; }
```

Before shipping a layout change, list which slides the selector matches. If that list is longer
than the request, narrow the selector.

## 6. Divider agendas are generated, never typed

The chapter divider lists its own slides. Hand-typing that list guarantees it will one day name a
slide that was deleted, or number one that moved. Derive it from the same slide list the build
uses, and give each row the slide's key so the switch layer can prune it
(`references/slide-switches.md`).
