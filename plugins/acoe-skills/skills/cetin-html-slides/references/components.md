# Component library

Append the CSS of whatever you use to the `COMPONENT_CSS` marker in `deck-shell.html`.
Pick components to fit the content; do not use all of them in one deck.

---

## Slide archetypes

### Title slide — beveled CETIN-blue area (bevel at -6°)
Marketing-style hero. Logo bottom-left, full size, negative (white) variant.
```css
.bevel-area { position:absolute; left:0; top:0; bottom:0; width:1180px; background:var(--cetin-blue);
  clip-path:polygon(0 0,100% 0,calc(100% - 114px) 100%,0 100%); }
.bevel-area::after { content:''; position:absolute; inset:0;
  background:linear-gradient(145deg,#70D1E2,#1F4D9A); opacity:.10; mix-blend-mode:screen; }
```
Keep the gradient at ~10%. Higher and `#300091` stops reading as CETIN Blue.

### Chapter divider — dark mode is allowed here
Ghost chapter number, agenda list right-aligned, logo bottom-left.
```css
.divider { background:var(--cetin-blue); }
.divider::before { content:''; position:absolute; inset:0;
  background:linear-gradient(145deg,#70D1E2,#1F4D9A); opacity:.10; mix-blend-mode:screen; }
.div-num { position:absolute; right:118px; top:152px; font-size:290px; font-weight:700;
  line-height:1; color:rgba(255,255,255,.1); letter-spacing:-10px; }
.div-agenda .ag { font-size:22px; color:#c8cfff; padding:11px 0; width:470px;
  border-top:1px solid rgba(255,255,255,.2); text-align:right; }
```

### Content slide — light mode, the default
`.pad` + `.eyebrow` + `h1.title` + content. No header bar, no rule under the title.

### Activity / statement slide
```css
.activity { flex:1; display:flex; flex-direction:column; align-items:center;
  justify-content:center; text-align:center; gap:30px; }
.activity .abig { font-size:112px; font-weight:700; text-transform:uppercase;
  color:var(--cetin-blue); line-height:1.02; letter-spacing:-1.5px; }
.activity .arule { width:150px; height:7px; background:var(--cetin-red); }
.activity .asub { font-size:30px; line-height:1.45; color:#34344a; max-width:1200px; }
```

### Full-bleed artwork / video
```css
.artwrap { flex:1; min-height:0; display:flex; align-items:center; justify-content:center; margin-top:18px; }
.artwrap img { max-width:100%; max-height:100%; width:auto; height:auto; display:block; }
.artwrap.framed img { border:1px solid var(--rule); border-radius:10px;
  box-shadow:0 10px 30px rgba(48,0,145,.1); }
.videowrap { flex:1; min-height:0; display:flex; align-items:center; justify-content:center; margin-top:14px; }
.videowrap video { aspect-ratio:16/9; height:100%; width:auto; max-width:100%; object-fit:contain;
  border-radius:10px; background:#000; box-shadow:0 20px 56px rgba(48,0,145,.26); }
```
Audio on for room playback: `controls preload="metadata" playsinline`, **not** `muted`.

---

## Text components

### Bullets — red triangle marker, CETIN-blue lead-in
```css
.bullets { list-style:none; margin:0; padding:0; }
.bullets li { position:relative; padding-left:42px; margin-bottom:22px; font-size:25px;
  line-height:1.48; color:var(--ink); }
.bullets li::before { content:''; position:absolute; left:0; top:12px; width:0; height:0;
  border-left:13px solid var(--cetin-red); border-top:9px solid transparent;
  border-bottom:9px solid transparent; }
.bullets .lead { color:var(--cetin-blue); font-weight:700; }
.bullets b { color:var(--cetin-blue); font-weight:700; }
.bullets.tight li { margin-bottom:16px; font-size:24px; }
```

### Cited definition / quote
```css
.defquote { border-left:6px solid var(--cetin-red); background:var(--panel);
  border-radius:0 8px 8px 0; padding:22px 30px; font-size:26px; line-height:1.45;
  color:var(--cetin-blue); font-weight:700; }
```

### Callout — the "so what" line
```css
.callout { background:var(--panel); border-left:6px solid var(--cetin-red); border-radius:8px;
  padding:24px 32px; font-size:25px; line-height:1.45; color:var(--ink); }
.callout b { color:var(--cetin-blue); }
```

### Statement band — loud and quiet variants
```css
.statement { background:var(--cetin-blue); color:#fff; border-radius:10px; padding:26px 34px;
  font-size:26px; line-height:1.45; position:relative; overflow:hidden; }
.statement::after { content:''; position:absolute; inset:0;
  background:linear-gradient(145deg,#70D1E2,#1F4D9A); opacity:.10; mix-blend-mode:screen; }
.statement > * { position:relative; z-index:2; }
/* aside, not headline */
.statement.quiet { background:none; color:var(--gray-text); border-left:4px solid var(--rule);
  border-radius:0; padding:6px 0 6px 26px; }
.statement.quiet::after { display:none; }
```

### Pending-content note — say what is missing, don't fake it
```css
.pending-note { border:2px dashed var(--bg-light-gray); background:var(--panel);
  border-radius:10px; padding:20px 26px; font-size:19px; line-height:1.5; color:var(--gray-text); }
.pending-note b { color:var(--cetin-red); }
```

---

## Data components

### Branded table
Header row CETIN Blue, alternating white / `--panel`, `1px solid var(--bg-light-gray)` borders.
```css
table.brand { width:100%; border-collapse:collapse; font-size:22px; }
table.brand thead th { background:var(--cetin-blue); color:#fff; font-weight:700;
  text-transform:uppercase; letter-spacing:2px; font-size:16px; text-align:left;
  padding:15px 20px; border:1px solid var(--cetin-blue); }
table.brand tbody td { border:1px solid var(--bg-light-gray); padding:13px 20px; line-height:1.35; }
table.brand tbody tr:nth-child(even) td { background:var(--panel); }
table.brand tbody tr:nth-child(odd) td { background:#fff; }
table.brand td.yr { font-weight:700; color:var(--cetin-blue); white-space:nowrap;
  border-left:7px solid var(--mid-gray); }   /* colour spine for grouping */
table.brand td.num { text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }
```

### Comparison table with logo column heads
For "A vs B vs C". Add a `.dim` variant to grey every column but one when you re-show it later.
```css
table.cmp thead th.col { padding:0 0 12px; border:none; background:none; vertical-align:bottom;
  text-align:center; }
table.cmp thead th.col img { height:54px; width:auto; display:block; margin:0 auto 10px; }
table.cmp thead th.col .cname { display:block; color:#fff; font-size:21px; font-weight:700;
  padding:12px 10px; border-radius:6px 6px 0 0; }
table.cmp.dim tbody td:nth-child(2), table.cmp.dim tbody td:nth-child(3) { color:#9a9cae; }
table.cmp.dim thead th.c1 .cname, table.cmp.dim thead th.c2 .cname {
  background:var(--mid-gray); color:#6b6d6b; }
table.cmp.dim thead th.c1 img, table.cmp.dim thead th.c2 img { filter:grayscale(1); opacity:.45; }
table.cmp.dim tbody td:nth-child(4) { background:#fdeff1 !important;
  border-left:3px solid var(--cetin-red); border-right:3px solid var(--cetin-red); }
```

### Card rows — chips, app cards, demo cards, stat cards, tier cards
All the same idea: a flex row of equal cards, one accent colour per role.
```css
.chips { display:flex; gap:20px; }
.chip { flex:1; background:#fff; border:2px solid var(--rule); border-radius:10px; padding:22px 26px;
  box-shadow:0 2px 12px rgba(48,0,145,.06); }
.chip .ci { font-size:15px; font-weight:700; letter-spacing:2.6px; text-transform:uppercase;
  color:var(--cetin-red); margin-bottom:9px; }
.chip .ch { font-size:27px; font-weight:700; color:var(--cetin-blue); }
.stat { flex:1; background:var(--panel); border-left:5px solid var(--cetin-blue);
  border-radius:8px; padding:22px 26px; }
.stat.accent { border-left-color:var(--cetin-red); }
.tier3 { flex:1; border-radius:12px; padding:26px 30px; color:#fff; }
.tier3.t-free { background:var(--light-blue); color:#0d3b52; }
.tier3.t-seat { background:var(--cetin-blue); }
.tier3.t-use  { background:var(--cetin-red); }
```

### Horizontal progression band — chevrons, kept quiet
For eras/phases under a table. Pale tints with a coloured underline read as a legend; saturated
filled chevrons read as the main content and fight the table.
```css
.flow { display:flex; width:100%; align-items:stretch; }
.flow-seg { position:relative; padding:13px 26px 12px 40px; color:#34344a;
  display:flex; flex-direction:column; justify-content:center; margin-left:-20px;
  clip-path:polygon(0 0,calc(100% - 20px) 0,100% 50%,calc(100% - 20px) 100%,0 100%,20px 50%); }
.flow-seg:first-child { margin-left:0; padding-left:26px;
  clip-path:polygon(0 0,calc(100% - 20px) 0,100% 50%,calc(100% - 20px) 100%,0 100%); }
.flow-seg::after { content:''; position:absolute; left:0; right:0; bottom:0; height:3px; }
.flow-seg.f1 { background:#f1f1ef; } .flow-seg.f1::after { background:var(--mid-gray); }
.flow-seg.f4 { background:#fdeff1; } .flow-seg.f4::after { background:var(--cetin-red); }
```

### Bar rows
```css
.bar-row { display:flex; align-items:center; margin-bottom:26px; }
.bar-name { flex:0 0 230px; font-size:27px; font-weight:700; color:var(--cetin-blue); }
.bar-track { flex:1; height:62px; background:var(--panel); border-radius:6px; position:relative;
  overflow:hidden; }
.bar-fill { position:absolute; left:0; top:0; bottom:0; border-radius:6px; box-sizing:border-box;
  transform-origin:left center; }
.bar-val { flex:0 0 300px; padding-left:28px; text-align:right; font-size:30px; font-weight:700; }
```
Animate a bar with `class="anim a-fade" style="width:30%;animation-name:growW"`.

### Inline SVG chart (no libraries)
Compute geometry in the build step. Dual axis pattern: bars on the left scale, `<polyline>` on the
right scale, `<text>` labels for both, category labels under a baseline. Series colours in order:
`--cetin-blue → --cetin-red → --light-blue → --light-purple → --c1 → --c4 → --c6 → --mid-gray`.
