# CETIN Product Template — Accurate Specification

**This file is consulted ONLY in product-template mode** — i.e. when the user explicitly asks
to use the CETIN product template / "use the template" / "use the official deck". In the
default generate-from-guidelines mode, ignore this file and follow `SKILL.md` + `design-guidelines.md`.

All measurements, colors, and font sizes below are extracted directly from the bundled file
`references/CETIN_sablona_prezentace_Final.pptx`. **When these template values conflict with the
2023 brand manual, the template wins for PowerPoint / presentation output produced in template
mode.** (The brand manual still governs print, HTML, and Word.)

---

## Template-first workflow (reuse the real slides 1:1)

When the user asks to build a CETIN deck **with the product template**, do **NOT** re-draw the
brand from primitive shapes. Re-drawing approximations of the CETIN components (rectangles, fake
KPI cards, hand-built tables) always looks worse than the real thing and is the #1 quality failure.

The bundled file `references/CETIN_sablona_prezentace_Final.pptx` contains 36 professionally-designed
slides. Reuse the real slides 1:1 — every shape, gradient, the official CETIN logo, the
"Member of PPF Group" mark, table styling, Gantt bars, and step nodes stay exactly as the
designer built them. **Swap only the text.**

### Template slide catalog (pick the slide whose component matches the need)

| Need | Source slide | Component it provides |
|------|-------------|------------------------|
| Cover / title | `slide1.xml` | Dark `#300091` cover, geometric/network cluster, logo, eyebrow + title + author |
| Section divider (dark) | `slide5.xml` | Full-blue divider, 104pt chapter number, title |
| Section divider (light) | `slide6.xml` | Light divider with blue right band |
| Text + bullet list | `slide7.xml` | Left body copy + 3 right cards |
| KPI dashboard | `slide8.xml` | 4 KPI cards (value/label/delta chip) + workstream progress bars |
| Single-metric / gauge cards | `slide9.xml` | Large % circles + team comparison bars |
| Charts (bar + line) | `slide10.xml` | Column + line chart frames |
| Charts (donut + stacked) | `slide11.xml` | Donut + stacked chart frames |
| Status table | `slide12.xml` | Table with status chips (green/blue/red) + trend arrows |
| Scoring / comparison | `slide13.xml` | Dot-rating comparison matrix |
| Roadmap — horizontal timeline | `slide15.xml` | Quarter milestone markers on a line |
| Roadmap — vertical timeline | `slide16.xml` | Year-by-year milestone cards |
| Roadmap — Gantt / phase plan | `slide17.xml` | Q-coloured Gantt bars on a quarter grid |
| Roadmap — quarterly cards | `slide18.xml` | 4 quarter columns with task + status badges |
| Roadmap — 12-month plan | `slide19.xml` | 12 month nodes, quarter-coded |
| Process steps | `slide20.xml` | 4 numbered step nodes (Q-coloured) + arrows |
| Org / tribe structure | `slide21.xml` | Tribe lead + 5 team cards |
| Teams & roles | `slide22.xml` | 5 role-list columns |
| Mind map (radial) | `slide23.xml` | Central node + 5 Q-coloured branches |
| Mind map (tree) | `slide24.xml` / `slide25.xml` | Horizontal / vertical tree |

> Confirm the actual title of any candidate slide before using it — grep its `<a:t>` runs. The
> filename order is the deck order; titles are in Czech (e.g. "Fázový plán (Gantt)" = slide17).

### Template-edit workflow (use the `pptx` skill's unpack/pack scripts)

1. **Unpack:** `python scripts/office/unpack.py references/CETIN_sablona_prezentace_Final.pptx unpacked/`
2. **Select slides:** rewrite `<p:sldIdLst>` in `ppt/presentation.xml` to keep ONLY the slides you
   need, in the desired order (map each kept slide's `r:id` via `ppt/_rels/presentation.xml.rels`),
   then `python scripts/clean.py unpacked/` to drop the rest.
3. **Edit text only:** in each kept `slideN.xml`, replace the placeholder text inside `<a:t>…</a:t>`
   runs (Lorem ipsum, Czech demo text, "Jméno Příjmení") with the real content. **Do not touch
   shapes, colours, positions, or `rPr` formatting.** Parallel subagents (one per slide) work well.
4. **Pack:** `python scripts/office/pack.py unpacked/ output/<name>.pptx --original references/CETIN_sablona_prezentace_Final.pptx`
5. **QA:** render to images (`soffice` → `pdftoppm`) and eyeball every slide.

### Template-edit pitfalls (all learned the hard way — check every time)

- **Escape ampersands:** text like "Discovery & Assessment" must be written `&amp;` in XML, or the
  pack validator fails (`xmlParseEntityRef`). Sweep edited slides for bare `&` before packing.
- **Fix the page numbers:** reused slides carry the template's ORIGINAL page numbers (9, 18, …).
  Renumber them to the new deck order.
- **Translate leftover Czech:** demo content may include Czech words (status chips "Aktivní /
  Plán / Riziko", month abbreviations). Translate any that would show in an English deck.
- **Status-chip colour ≠ severity:** the table/badge chip COLOURS are the template's demo pattern,
  not your data's real status. If colour must convey true status (e.g. a high risk should read
  red, not green), recolour the chip + trend-arrow shapes to match — and tell the user you did.
- **Match counts to slots:** if your data has fewer items than the template slot count, delete the
  extra shape group entirely (don't leave an empty card); if more, paginate to a second slide.

### When the template can't supply a slide

Even in template mode, **no template slide fits** some content — most often **text-heavy /
narrative** slides (long prose, detailed write-ups) for which the template has no component. For
those few slides, generate a fresh slide that applies every template value below verbatim
(Calibri, `#F7F8FC` background, `#1A1346` title, red-dot eyebrow, white cards, the Q-colour
sequence, the official logo). A generated slide must sit visually alongside the template slides
without looking foreign. Prefer **mixing**: reuse template slides for every component that
exists, and generate only the few slides the template can't supply.

---

## Template colors (override the brand manual for template-mode PPTX)

**Backgrounds:**

| Role                           | HEX       | Use                                          |
|-------------------------------|-----------|----------------------------------------------|
| Dark slide BG (cover/dividers) | `#300091` | Cover slide, section dividers (full bleed)   |
| Content slide BG               | `#F7F8FC` | All standard content slides (NOT white)      |
| Card / panel BG                | `#FFFFFF` | Individual content cards on #F7F8FC bg       |
| Alt row / inner card BG        | `#F1F2FA` | Alternating table rows, inner card panels    |
| Very light panel               | `#EDEEF8` | Scoring panels, progress bar backgrounds     |
| Chip bg (indigo)               | `#ECEAF7` | "In progress" status badge background        |
| Border / divider               | `#E7E8F2` | Table row separators, timeline connectors    |
| Mind-map connector             | `#C7C9D6` | Tree/mind-map connecting lines               |

**Text:**

| Role                     | HEX       | Use                                                |
|--------------------------|-----------|-----------------------------------------------------|
| Content slide title      | `#1A1346` | Main title on content slides (30pt bold Calibri)    |
| Dark decorative bg       | `#3A1AA0` | Geometric decorative shapes on cover/divider right  |
| Body text primary        | `#5A5478` | Regular body copy, table data cells, bullet text    |
| Body text muted          | `#8E8AA8` | Page numbers, secondary labels, "out" row text      |
| Subtitle on dark BG      | `#C9C4E6` | Subtitle line on cover/divider slides               |
| Subtitle alt on dark BG  | `#D9D6EE` | Alt subtitle on dark slides                         |

**Quarter / sequential accent palette (Q-colors)** — use in strict order for timelines,
roadmaps, process steps, org charts, and chart series:

| Role   | HEX       | Use                                       |
|--------|-----------|-------------------------------------------|
| Q1     | `#300091` | First quarter, first step, first team     |
| Q2     | `#F12E49` | Second quarter / step / team              |
| Q3     | `#49A2D8` | Third quarter / step / team               |
| Q4     | `#81C78F` | Fourth quarter / step / team              |
| Q4 alt | `#3F3E98` | Fourth slot (dark indigo variant, annual Q4 in some slides) |

Decorative-only accents seen in the template:
`#4A2BB5` · `#6B53D0` · `#8E84E0` · `#6F79BD` (geometric shapes, decorative only)

**Status chip palette:**

| Status    | Background | Text / icon    | Use                                   |
|-----------|------------|---------------|---------------------------------------|
| Active / Done (green) | `#E8F4EA` | `#2E7D4F`  | Positive status, on-track, done       |
| In Plan (blue)        | `#E4F1FA` | `#1F4D9A`  | Planned, in-progress (blue)           |
| Risk / Alert (red)    | `#FDE7EB` | `#C0233B`  | At-risk, overdue, negative            |
| Neutral / Inactive    | `#F1F2FA` | `#8E8AA8`  | Planned but not started               |

Trend arrow colors: `#81C78F` (up ▲), `#F12E49` (down ▼), `#8E8AA8` (flat ▬)

**Data visualization series order (template mode):**
`#300091` → `#f12e49` → `#49A2D8` → `#81C78F` → `#3F3E98` → `#1F4D9A` → `#70D1E2` → `#c7c9c7`

---

## Template typography — Calibri

The official template uses **Calibri** throughout all slides. Use Calibri for all template-mode
PowerPoint output. (Avenir Next LT Pro is the brand-manual typeface for print/design tools and
the default-mode font; Arial is the wider fallback.)

### Template font size scale

| Element                          | Size     | Weight | Color     | Font     |
|----------------------------------|----------|--------|-----------|----------|
| Presentation cover title         | 44pt     | Bold   | `#FFFFFF` | Calibri  |
| Chapter/section divider title    | 42pt     | Bold   | `#FFFFFF` / `#1A1346` | Calibri |
| Chapter number (section divider) | 104pt    | Bold   | `#F12E49` | Calibri  |
| Content slide title              | 30pt     | Bold   | `#1A1346` | Calibri  |
| KPI value / large metric         | 42pt     | Bold   | Q-color   | Calibri  |
| Org chart team name / step number| 22–24pt  | Bold   | `#FFFFFF` | Calibri  |
| Card heading / sub-title (light) | 15–17pt  | Bold   | `#1A1346` | Calibri  |
| Body text / list items           | 11–12pt  | Regular| `#5A5478` | Calibri  |
| Table header cells               | 12.5pt   | Bold   | `#FFFFFF` | Calibri  |
| Table data cells                 | 12.5pt   | Regular| `#5A5478` | Calibri  |
| Eyebrow / section label          | 12pt     | Bold   | `#F12E49` | Calibri  |
| Status chip text                 | 11–11.5pt| Bold   | varies    | Calibri  |
| Delta / badge value              | 11pt     | Regular| varies    | Calibri  |
| Slide subtitle / cover subtitle  | 14–16pt  | Regular| `#C9C4E6` | Calibri  |
| Cover author / date line         | 13pt     | Bold   | `#FFFFFF` | Calibri  |
| Page number (bottom-right)       | 9pt      | Regular| `#8E8AA8` | Calibri  |
| Annotations / tip text           | 10–10.5pt| Regular| `#8E8AA8` | Calibri  |

---

## Slide dimensions

- **33.87 × 19.05 cm** (13.33" × 7.5") — standard 16:9 widescreen, equivalent to 1280×720 px at 96 dpi.
- PptxGenJS: `layout: 'LAYOUT_WIDE'`; python-pptx: `prs.slide_width = Inches(13.33); prs.slide_height = Inches(7.5)`.

## Template logo placement (PPTX)

- **Position (section dividers / cover):** x=2.16cm, y=2.16cm, w=6.86cm, h=2.64cm (top-left).
- On **cover** and **dark section dividers**: negativ (white) logo variant.
- On **light section dividers**: pozitiv (blue) logo variant.
- **Content slides**: no logo in header — omit, or place bottom-right at ≈3cm wide.

---

## Template slide-type catalog (exact layouts, colors, positions)

### 1. Cover / Title Slide

**Background:** `#300091` (full bleed)
**Decorative element (right):** Overlapping squares in `#3A1AA0`, `#4A2BB5`, `#6B53D0`, with
accent dots in `#49A2D8`, `#8E84E0`, `#81C78F` — positioned in the right third (x>24cm)
**Logo:** x=2.16cm, y=2.16cm, w=6.86cm, h=2.64cm — negativ (white) logo variant

| Element               | Position (x, y)  | Size (w × h)      | Style                                   |
|-----------------------|-----------------|-------------------|-----------------------------------------|
| Red accent line       | 2.16, 7.37      | 1.27 × 0.18 cm    | `#F12E49` solid fill                    |
| Category / year label | 2.16, 7.75      | 15.24 × 0.76 cm   | 12pt bold Calibri, `#F12E49`, ALL CAPS  |
| Main title            | 2.16, 8.89      | 21.34 × 4.83 cm   | 44pt bold Calibri, `#FFFFFF`            |
| Subtitle / tagline    | 2.16, 13.84     | 17.78 × 1.52 cm   | 16pt regular Calibri, `#C9C4E6`         |
| Author / date line    | 2.16, 16.26     | 15.24 × 1.78 cm   | 13pt bold Calibri, `#FFFFFF`            |

**Eyebrow label format:** "PREZENTACE 2026" — uppercase, category followed by year.

### 2. Section Divider — Dark Variant

**Background:** `#300091` (full bleed)
**Decorative:** Right side geometric blocks `#3A1AA0`, red panel `#F12E49`
**Logo:** x=2.16cm, y=2.16cm, w=6.86cm, h=2.64cm — negativ logo

| Element           | Position (x, y) | Size (w × h)      | Style                                   |
|-------------------|----------------|-------------------|-----------------------------------------|
| Chapter number    | 2.08, 6.60     | 10.16 × 3.81 cm   | 104pt bold Calibri, `#F12E49`           |
| Chapter title     | 2.16, 10.79    | 21.59 × 3.56 cm   | 42pt bold Calibri, `#FFFFFF`            |
| Red accent line   | 2.29, 14.48    | 1.52 × 0.15 cm    | `#F12E49` solid                         |
| Subtitle          | 2.16, 14.99    | 19.05 × 1.27 cm   | 14pt regular Calibri, `#C9C4E6`         |

### 3. Section Divider — Light Variant

**Background:** `#F7F8FC` left / `#300091` right band (x≥23.11cm)
**Decorative right:** `#3A1AA0` square, `#F12E49` accent block, `#49A2D8` dot
**Logo:** x=2.16cm, y=2.16cm, w=6.86cm, h=2.64cm — pozitiv logo (on light left)

| Element           | Position (x, y) | Size (w × h)      | Style                                    |
|-------------------|----------------|-------------------|------------------------------------------|
| Chapter number    | 2.08, 6.35     | 10.16 × 4.06 cm   | 104pt bold Calibri, `#F12E49`            |
| Chapter title     | 2.16, 10.67    | 19.30 × 3.56 cm   | 42pt bold Calibri, `#1A1346`             |
| Red accent line   | 2.29, 14.35    | 1.52 × 0.15 cm    | `#F12E49` solid                          |
| Subtitle          | 2.16, 14.86    | 19.05 × 1.27 cm   | 14pt regular Calibri, `#5A5478`          |

### 4. Standard Content Slide (header anatomy — applies to ALL content slides)

**Background:** `#F7F8FC`
**Page number:** x=30.94cm, y=17.48cm, 9pt regular Calibri, `#8E8AA8`

| Element               | Position (x, y) | Size (w × h)      | Style                                    |
|-----------------------|----------------|-------------------|------------------------------------------|
| Red triangle accent   | 2.16, 1.85     | 0.38 × 0.44 cm    | `#F12E49` solid (small decorative dot)   |
| Eyebrow / category    | 2.82, 1.68     | 17.78 × 0.76 cm   | 12pt bold Calibri, `#F12E49`, ALL CAPS   |
| Slide title           | 2.08, 2.67     | 29.97 × 2.03 cm   | 30pt bold Calibri, `#1A1346`             |
| Content area starts   | —, ~5.46–6.22  | full width        | White cards on `#F7F8FC` background      |

Content area uses white panels (`#FFFFFF`) placed on the `#F7F8FC` slide background. Never use a
full-bleed colored bar behind the title on content slides.

### 5. KPI / Data Cards Slide

4 equal KPI cards side by side on `#F7F8FC` background.

| Element               | Per-card spec                                                   |
|-----------------------|-----------------------------------------------------------------|
| Card background       | `#FFFFFF`, no border                                            |
| Icon square (top-left)| 1.4×1.4cm, Q-color fill; white center 0.53×0.53cm              |
| Main value            | 42pt bold Calibri, Q-color (e.g. `#300091`, `#F12E49`, `#49A2D8`, `#81C78F`) |
| Label                 | 13pt regular Calibri, `#5A5478`                                 |
| Delta badge           | Small chip (2.79×0.76cm), Q-color bg family + colored text     |
| Progress bar (optional)| Thin bar: `#E7E8F2` bg, colored fill to percentage            |

Card widths: 4 cards of 7.24cm each, x=2.16, 10.16, 18.16, 26.16cm; y=6.10cm, h=6.35cm.

### 6. Table Slide

| Element              | Style                                                           |
|----------------------|-----------------------------------------------------------------|
| Header row           | `#300091` fill, 12.5pt bold Calibri, `#FFFFFF` text            |
| Odd body rows        | `#FFFFFF` fill                                                  |
| Even body rows       | `#F1F2FA` fill                                                  |
| Row separators       | `#E7E8F2` (thin horizontal lines)                               |
| Row label text       | 12.5pt bold Calibri, `#1A1346`                                  |
| Data cell text       | 12.5pt regular Calibri, `#5A5478`                               |
| Status chip          | See Status chip palette above                                   |
| Trend arrow          | 13pt bold, `#81C78F` (▲ up), `#F12E49` (▼ down), `#8E8AA8` (▬ flat) |

### 7. Process Steps Slide

N horizontal step cards (4 shown in template), each with a colored step number badge.
Steps use Q-colors in sequence: Step 1 = `#300091`, Step 2 = `#F12E49`, Step 3 = `#49A2D8`, Step 4 = `#81C78F`.

| Element                | Style                                                           |
|------------------------|-----------------------------------------------------------------|
| Step card              | `#FFFFFF` bg                                                    |
| Number badge           | 2.03×2.03cm square, Q-color fill, 24pt bold Calibri white       |
| Step heading           | 16pt bold Calibri, `#1A1346`                                    |
| Step description       | 11.5pt regular Calibri, `#5A5478`                               |
| Arrow connector        | Small `#F12E49` arrow between cards (right side of each card)   |

### 8. Org Chart — Tree Structure

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Root box (Tribe Lead)| `#300091` fill, 16pt bold Calibri white, centered              |
| Team header bars    | Q-color fill, 22pt bold Calibri white initial letter            |
| Team card           | `#FFFFFF` bg, thin Q-color top bar (0.30cm)                    |
| Role bullets        | 0.33×0.33cm Q-color squares + 11.5pt regular Calibri `#1A1346` |
| Count badge         | `#F1F2FA` bg, 11pt Calibri, Q-color text                       |
| Connectors          | `#E7E8F2` horizontal/vertical lines                             |

### 9. Roadmap — Horizontal Timeline (variant A)

Quarter milestone markers alternating above/below a horizontal `#E7E8F2` line.
Marker colors: Q1=`#300091`, Q2=`#F12E49`, Q3=`#49A2D8`, Q4=`#81C78F`.

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Timeline line       | Horizontal, `#E7E8F2`, full width                               |
| Milestone dot       | 0.81×0.81cm circle, Q-color fill                                |
| Quarter badge       | 1.78×0.86cm, Q-color fill, 11pt regular Calibri white, centered |
| Milestone heading   | 13.5pt bold Calibri, `#1A1346`                                  |
| Milestone detail    | 10.5pt regular Calibri, `#5A5478`                               |
| Card bg             | `#FFFFFF`                                                       |

### 10. Roadmap — Vertical Timeline (variant B)

Year labels on left, milestone cards on right.

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Year label          | 3.30×1.27cm, 18pt bold Calibri, Q-color text                   |
| Connector dot       | 0.76×0.76cm, Q-color fill                                       |
| Vertical timeline   | `#E7E8F2` line                                                  |
| Left color bar      | 0.25cm wide Q-color bar at card left edge                       |
| Card bg             | `#FFFFFF`                                                       |
| Card heading        | 15pt bold Calibri, `#1A1346`                                    |
| Card detail         | 12pt regular Calibri, `#5A5478`                                 |

### 11. Roadmap — Gantt / Phase Plan (variant C)

Horizontal Gantt bars in Q-colors on `#F7F8FC` grid.

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Quarter columns     | Headers: 13pt bold Calibri, `#5A5478`; vertical separators `#E7E8F2` |
| Row labels          | 12.5pt regular Calibri, `#1A1346`                               |
| Gantt bar           | Q-color fill, h=1.12cm, 10.5pt regular Calibri white duration label |

### 12. Roadmap — Quarterly Cards (variant D)

4 column cards, each headed by Q-color header + white quarter label.

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Card bg             | `#FFFFFF`, w=7.24cm each                                        |
| Quarter header      | 1.78cm tall, Q-color fill + 20pt bold Calibri white "Q1"/"Q2"… |
| Task item           | `#F1F2FA` inner card, 12pt regular Calibri `#1A1346` label     |
| Status badge        | See Status chip palette above                                   |

### 13. Scoring / Comparison Table

Column headers in Q-colors; rows with dot-rating system.

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Column header       | 7.06×1.78cm, Q-color fill, 16pt bold Calibri white             |
| Row category label  | 5.59×1.73cm, 14.5pt bold Calibri `#1A1346`; left color bar `#F12E49` |
| Row bg (alt)        | `#F1F2FA` every other row                                       |
| Filled dot          | 0.33×0.33cm Q-color square                                      |
| Empty dot           | 0.33×0.33cm `#E7E8F2` square                                    |

### 14. Mind Map — Radial

Central box in `#300091`; 5 branch nodes in Q-colors + `#3F3E98`; connectors `#C7C9D6`.

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Central node        | 4.32×4.32cm, `#300091` fill, 16pt bold Calibri white           |
| Branch node         | 5.08×1.83cm, Q-color fill, 14pt bold Calibri white             |
| Connector           | `#C7C9D6` line                                                  |

### 15. Mind Map — Tree (horizontal / vertical)

| Element             | Style                                                           |
|---------------------|-----------------------------------------------------------------|
| Root box            | `#300091` fill, 15–16pt bold Calibri white                     |
| Level-1 nodes       | `#FFFFFF` card, left color bar 0.23cm wide in Q-color, 14pt bold `#1A1346` |
| Level-2 leaves      | `#F1F2FA` small chip, 0.36×0.36cm Q-color dot, 11.5pt regular `#1A1346` |
| Connectors          | `#E7E8F2` lines                                                 |

### 16. Text + Bullet List Layout

Left: large body text area (15.5pt regular Calibri `#5A5478`).
Right: 3 white cards, each with a Q-color 1.52×1.52cm square icon, heading (15pt bold `#1A1346`), detail (11.5pt regular `#5A5478`).

### 17. Monthly Timeline (12 milestones)

12 month nodes alternating above/below a horizontal timeline, color-coded by quarter:
Q1 nodes=`#300091`, Q2=`#49A2D8`, Q3=`#81C78F`, Q4=`#3F3E98`.

Quarter header bars span 3 months each; node cards show month abbreviation (14pt bold `#1A1346`) + month label (10pt regular `#8E8AA8`).
