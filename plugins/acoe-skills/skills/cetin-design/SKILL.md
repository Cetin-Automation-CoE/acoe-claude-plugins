---
name: cetin-design
description: CETIN corporate design system and brand guidelines. Apply CETIN branding (CETIN Blue + Red, Avenir/Arial, official logos, brand layouts) to visual outputs — presentations, HTML/React artifacts, dashboards, Excel charts, and Word documents. By DEFAULT, generate output from the CETIN brand guidelines (this guide + references/design-guidelines.md). ONLY use the bundled product template CETIN_sablona_prezentace_Final.pptx (1:1 slide reuse) when the user EXPLICITLY asks to use the product/official template — e.g. "use the CETIN template", "use the product template", "use the official deck", "edit the template". USE ONLY for business/work output (CETIN deliverables, internal reports, customer-facing material, team or stakeholder decks, BA docs, anything in the user's CETIN role). DO NOT USE for personal or non-business work (personal projects, family, school, travel, fiction, hobby code, personal finance, etc.) — fall back to neutral design. ALWAYS SKIP when the user opts out ("plain", "unbranded", "no branding", "not for CETIN", "different design"). When ambiguous, ask once whether the request is for CETIN/work or personal before applying branding.
---

# CETIN Design System

You are producing output for CETIN, a Czech telecommunications infrastructure company (member
of PPF Group). Every visual deliverable must follow the CETIN brand identity described below.
The goal is a consistent, professional, instantly recognizable look across all formats.

---

## Two modes — pick the right one BEFORE you build anything

This skill operates in one of two modes. **Default is GENERATE-FROM-GUIDELINES.** Switch to
TEMPLATE mode only on an explicit request.

### Mode A — Generate from guidelines (DEFAULT)

Use this for **every** CETIN request **unless** the user explicitly asks for the product template.
Build the deliverable from the CETIN brand identity in this guide (and the full spec in
`references/design-guidelines.md`): **Avenir Next LT Pro → Arial** typography, white content
backgrounds, **CETIN Blue (`#300091`)** titles, the official logo files, and — where the format
allows — the signature **beveled blue-area + photo** layout. Generate slides, HTML, docs, and
charts from scratch following the rules in the rest of this file. **Do not open or edit the
bundled `.pptx` template in this mode.**

### Mode B — Product template (ONLY when explicitly requested)

Switch to template mode **only** when the user explicitly asks to use the CETIN product /
official template, with phrasing such as:

- "use the CETIN template" / "use the product template" / "use our template"
- "use the official CETIN deck / presentation template"
- "edit / start from the template" / "fill in the template"
- "build this in the CETIN_sablona_prezentace_Final template"

In that case, do **NOT** re-draw the brand from scratch. Reuse the 36 professionally-designed
slides in `references/CETIN_sablona_prezentace_Final.pptx` **1:1 — swap only the text.** The full
template-mode instructions (slide catalog, unpack/edit/pack workflow, pitfalls, and the
template-accurate colors, fonts, sizes, and positions) live in
**`references/product-template-spec.md`** — read that file and follow it exactly when in this mode.

> **Template values apply in Mode B only.** The template uses **Calibri**, `#F7F8FC` content
> backgrounds, and `#1A1346` titles — these override the brand-manual values *for template-mode
> PowerPoint output*. In Mode A, use the default brand-guideline values below (Avenir/Arial,
> white backgrounds, `#300091` titles). Do not mix the two.

**If unsure which mode applies, default to Mode A** (generate from guidelines). Only the explicit
template request above triggers Mode B.

---

## When to apply this skill (and when NOT to)

CETIN branding is for **business / work output only**. Before applying any colors, logos,
fonts, or layouts from this guide, decide whether the current request is business or personal.

**Apply CETIN branding when** the output is for work:
- CETIN-internal documents, reports, dashboards, or apps
- Customer- or partner-facing materials produced on behalf of CETIN
- Team meetings, stakeholder updates, sales/exec decks, BA workflows
- Anything where the user is acting in their CETIN role

**Do NOT apply CETIN branding when** the context is personal or non-business:
- Personal projects, hobby code, side experiments
- Family planning, school work, travel itineraries, gifts, personal events
- Fiction, creative writing, music, art for personal use
- Personal blogs, personal finance, learning exercises
- Anything outside the user's CETIN job

For personal output, fall back to a neutral / default design — no CETIN blue, no CETIN logos,
no Avenir, no triangle pattern. Use whatever generic style fits the task.

**Always skip CETIN branding when the user explicitly opts out**, e.g. "plain", "unbranded",
"no branding", "personal style", "use a different design", "not for CETIN" — even if the topic
could otherwise look work-related. Honor the request immediately and do not re-apply CETIN
visuals later in the same conversation unless the user asks for them.

**When ambiguous**, ask once: "Is this for CETIN / work, or a personal project?" Do not assume.

## When NOT to Use

- **Personal or non-work requests**: never apply CETIN branding (colors, logo, fonts) to personal
  projects, travel plans, family content, or any topic outside the user's CETIN job role.
- **When user opts out**: if the user says "plain", "no branding", "not for CETIN", "different design",
  or any synonym — do not apply any CETIN design element, even if the topic looks work-related.
- **HTML / React that is NOT a CETIN deliverable**: use neutral CSS, not CETIN CSS variables.
- **Non-visual output** (prose, code logic, data analysis): skip design guidance entirely.
- **Do NOT fabricate design values**: every color, font size, or position spec must come from this
  guide or the official references — never invent or approximate brand values.

---

For the full specification with CSS variables, Tailwind presets, and PptxGenJS config, read
`references/design-guidelines.md` in this skill's directory. Below is the working summary you
need for day-to-day Mode A output. Wording and values come from the official CETIN Brand
Guidelines (EN V17, 2023) — call the primary brand color **CETIN BLUE**, never "purple."

---

## Logo

### Quick decision tree — which logo file to use

Apply this every time you place a logo. Works identically in chat answers, generated code,
Word/PowerPoint/Excel output, HTML/React artifacts, or Cowork-driven file edits.

1. **Which sub-brand is the deliverable for?**
   - DunAI initiative? → use the **DunAI** files (see Sub-brands §3 below). Skip the rest.
   - CETIN.DIGITAL programme? → use the **standard CETIN** files below plus the CETIN.DIGITAL text mark.
   - Anything else? → standard CETIN. Continue to step 2.
2. **Which market / audience is the deliverable for?**
   - **International / English-language / cross-border** — *this is the default when unsure* →
     the **no-claim** files `CETIN_CMYK_*_international_no_claim.png` (or `cetin-logo-noclaim.svg`
     for web). This is the **main** logo.
   - **Czech-market / Czech-language** (domestic CETIN a.s. audience, Czech copy, .cz-facing) →
     the `CETIN_CMYK_*_cz.png` files.
   - The **claim** files `CETIN_CMYK_*_international.png` (MEMBER OF PPF GROUP) are **backup only** —
     use them solely when a deliverable explicitly requires the PPF-group claim
     (formal / legal / contractual). See "With claim vs without claim" below.
3. **What's the background color the logo will sit on?**
   - Dark background (CETIN-blue area, near-black, dark photo) → `*_negativ_*` (white wordmark) file.
   - Light background (white, light gray, light photo) → `*_pozitiv_*` (CETIN-blue wordmark) file.

This decision is the same whether you are typing the path into a PptxGenJS call, an `<img src>`,
a markdown reference, or a Cowork file-write. **Always use the relative path inside `references/`.**

### Official files — canonical CETIN logos

Select by **market** (step 2) then **background** (step 3). All are correctly constructed
(wedge-cut C, official triangle proportions, brand-spec colors).

**International / cross-border — PRIMARY (no claim), the default main logo:**

| File | Use on | Description |
|------|--------|-------------|
| `references/CETIN_CMYK_pozitiv_international_no_claim.png` | Light backgrounds | CETIN-blue wordmark + red triangle, no claim |
| `references/CETIN_CMYK_negativ_international_no_claim.png` | Dark backgrounds | White wordmark + red triangle, no claim |
| `references/cetin-logo-noclaim.svg` | Light backgrounds, web/HTML | Vector version of the positive no-claim mark (CETIN blue). Crisp at any size — use in HTML/React where vector is preferred. |

**Czech market:**

| File | Use on | Description |
|------|--------|-------------|
| `references/CETIN_CMYK_pozitiv_cz.png` | Light backgrounds | CETIN-blue wordmark + red triangle, Czech variant |
| `references/CETIN_CMYK_negativ_cz.png` | Dark backgrounds | White wordmark + red triangle, Czech variant |

**International with claim — BACKUP only (MEMBER OF PPF GROUP):**

| File | Use on | Description |
|------|--------|-------------|
| `references/CETIN_CMYK_pozitiv_international.png` | Light backgrounds | Blue wordmark + claim. Use only when the PPF-group claim is explicitly required. |
| `references/CETIN_CMYK_negativ_international.png` | Dark backgrounds | White wordmark + claim. Use only when the PPF-group claim is explicitly required. |

All sets share the correct construction (the wedge-cut C, the official triangle proportions,
the brand-spec colors). The **no-claim international pair is the default main logo**; reach for
the `_cz` files for Czech-market deliverables, the claim pair only when the "MEMBER OF PPF
GROUP" claim is explicitly required, and the DunAI files for DunAI work (Sub-brands §3).

If even the canonical PNGs are somehow unavailable, fall back to a styled-text logo: `▶ CETIN`
with the triangle in CETIN red (`#f12e49`) and the wordmark in CETIN blue (`#300091`) on light
backgrounds, or white on dark backgrounds. The wordmark must always be **uppercase, bold
sans-serif**. This fallback is for emergencies only — every bundled deliverable should embed
the actual PNG.

### Embedding the PNGs — always crop to alpha bbox first

The canonical PNGs ship at 3508×1250 with substantial transparent padding. If you embed them
raw, the visible logo will end up tiny inside its placement box and the deck will look broken.
**Always crop to the alpha bounding box before embedding.** Use this Python recipe:

```python
from PIL import Image

img = Image.open('references/CETIN_CMYK_pozitiv_international_no_claim.png').convert('RGBA')
margin = int(min(img.size) * 0.02)
b = img.getbbox()
img.crop((
    max(0, b[0] - margin),
    max(0, b[1] - margin),
    min(img.size[0], b[2] + margin),
    min(img.size[1], b[3] + margin),
)).save('logo_official_light.png')
# Cropped aspect ratio is ~5.55:1.
```

Run the same recipe on `CETIN_CMYK_negativ_international_no_claim.png` to produce a dark-bg
variant. Swap in the `_cz` or claim filenames when the market/backup rules call for them.
Embed the cropped output directly via your format's native image API:

- **PptxGenJS:** `slide.addImage({ path: 'logo_official_light.png', x, y, w, h })`
- **python-pptx:** `slide.shapes.add_picture('logo_official_light.png', x, y, width, height)`
- **HTML / React:** `<img src="references/cetin-logo-noclaim.svg" alt="CETIN" />` (vector, no padding)
- **docx (python-docx):** `paragraph.add_run().add_picture('logo_official_light.png', width=...)`
- **Excel (openpyxl / xlsxwriter):** `worksheet.insert_image(...)` / `add_image(...)`

**For office formats (PPTX, DOCX, XLSX, PDF), embed the cropped PNG** — do not reconstruct the
logo from primitive shapes. The cropped CMYK PNG is the source of truth there. The official
`cetin-logo-noclaim.svg` may be used directly in HTML/React; if you need it in an office
format, rasterize it to a high-resolution PNG (e.g. via `cairosvg`) rather than redrawing it.
Never hand-redraw any logo.

### Logo placement on slides (CETIN house rule)

This is a deliberate house rule that **overrides** the brand manual's top-left default:

- **Intro slides, chapter slides, dividers, title slides** → logo **bottom-left**, full size
- **Content slides** → logo **bottom-right**, smaller (≈60–70% of intro-slide size)

Logo always sits within the clear-space margin (1× triangle height on all sides). On a 16:9
slide at 1920×1080, the intro-slide logo is typically 240–280 px wide; the content-slide logo
is typically 140–180 px wide.

### Logo construction (per brand manual §2.7)

The logo is **not** a generic right-pointing triangle plus text — it is a constructed mark:

- The **C** in CETIN has a wedge (negative space) cut from the left side of its bowl, shaped
  as an equilateral triangle whose side equals 5% of the logo text height.
- The **red triangle** sits to the left of the wordmark. Its side equals 90% of the wordmark
  height. Its median (to the midpoint of the vertical right side) crosses the central
  horizontal axis of the wordmark.
- Logo with claim: claim baseline sits 2.5× claim-text-height below the wordmark baseline.

**MANDATORY: always embed the canonical PNG file.** Do not redraw the logo from scratch, do
not approximate it with native shapes, do not regenerate it as an SVG. The cropped CMYK PNG
is the only acceptable source for any office deliverable.

### Clear space and minimum size (per brand manual §2.8, §2.16)

- **Clear space:** the height of the red triangle, on all sides. No other elements may enter
  this zone.
- **Minimum size:** 100 px wide recommended; 60 px absolute minimum. Below 100 px, prefer the
  logo without claim.

### Logo with claim vs. without claim (per brand manual §2.2)

- **Without claim** (default): B2C communication, customer-facing materials, small formats.
- **With claim** ("MEMBER OF PPF GROUP"): B2B, internal, and international communication.

The claim is set in Avenir Next LT Pro Demi Bold, all caps, lowercase tracking 5 pt, sized
9.5 pt when the logo is 50 mm wide.

### Prohibited use (per brand manual §2.18)

Do not:

- Change the size or position of any individual part of the logo.
- Display an incomplete logo.
- Change the font, size, or position of the wordmark.
- Place the logo or any part of it inside a line frame.
- Add other graphic elements to the logo.
- Apply filters or effects (drop shadow, glow, blur, etc.).
- Recolor the logo outside the brand palette.
- Stretch, rotate, or distort the logo.

---

## Color Palette

### Primary

| Role            | HEX       | RGB           | CMYK         | Pantone   | When to use                                           |
|-----------------|-----------|---------------|--------------|-----------|-------------------------------------------------------|
| **CETIN Blue**  | `#300091` | 48 / 0 / 145  | 91 / 91 / 0 / 0 | 2735 C | Headers, the beveled brand area, accents, body text on light bg |
| **CETIN Red**   | `#f12e49` | 241 / 46 / 73 | 0 / 89 / 66 / 0 | 1787 C | The logo triangle, CTA frame, accent underlines — sparingly |
| White           | `#FFFFFF` | 255 / 255 / 255 | 0 / 0 / 0 / 0 | —      | Text on dark/blue backgrounds, cards, blank canvas    |

### Secondary (per brand manual §4.2)

| Role            | HEX       | Pantone   | When to use                                           |
|-----------------|-----------|-----------|-------------------------------------------------------|
| Middle Gray     | `#c7c9c7` | 420 C     | Soft sections, neutral backgrounds, when CETIN blue is too rich |
| Light Blue      | `#41b6e6` | 298 C     | Larger areas where CETIN blue would dominate; web/UI accents |
| Light Purple    | `#6f79bd` | 2115 C    | Subtle accents, secondary fills                       |
| Black           | `#000000` | Black C   | Body text on light bg, fine-print legal               |

### Background colors (per brand manual §4.3)

| Role            | HEX       | When to use                                           |
|-----------------|-----------|-------------------------------------------------------|
| Light Gray BG   | `#d9d9d6` | Print backgrounds, section panels                     |
| Light Blue BG   | `#99d6ea` | Soft section panels, infographic backgrounds          |
| Light Purple BG | `#a7a4e0` | Soft section panels, alternate to light-blue BG       |
| White           | `#ffffff` | Default content area background                       |

### Digital-only background palette (per brand manual §4.5 — screen/email/banner only, not print)

`#f5f6fa`  ·  `#d7dae1`  ·  `#cdd4e5`  ·  `#66678a`

These can be reduced to 50% or 75% opacity. Use for app/dashboard chrome and email headers.

### Complementary palette (per brand manual §4.4 — for charts, illustrations, infographics)

Use these in this order for chart series, in addition to CETIN blue and CETIN red:

```
#3F3E98   #87C4E7   #7078B8   #1F4D9A   #81C78F   #70D1E2
#49A2D8   #6AC9BB   #DEE5F1   #C6E4EF   #F3D9DD   #D4EAD5
```

### Gradients (per brand manual)

- **Primary:** turquoise `#70D1E2` → blue `#1F4D9A` at **145°**, **30% opacity**
- **Secondary:** purple `#A7A4E0` → blue `#99D6EA` at **0°**, **20% opacity**

### Data visualization series order

`#300091` → `#f12e49` → `#41b6e6` → `#6f79bd` → `#3F3E98` → `#1F4D9A` → `#70D1E2` → `#c7c9c7`

---

## Typography

### Primary typeface — Avenir Next LT Pro

Use whenever the format supports it (InDesign, Figma, Photoshop, anywhere the font is licensed
and installed). Cuts: **Bold**, **Demi Bold**, **Regular**.

### Secondary / fallback typeface — Arial

Use as fallback when Avenir Next LT Pro is not available — this includes **PowerPoint, Word,
web/HTML, Excel, and most generated outputs**. Cuts: **Bold**, **Regular**. Do **not** use
Arial Black, Helvetica, Montserrat, Open Sans, or any other substitute.

> **Note:** the bundled product template (Mode B) uses **Calibri** throughout. Calibri is the
> font for **template-mode** PowerPoint output only; in default Mode A use Avenir → Arial.

### Heading rules

- **H1 / slide titles:** Avenir Bold or Arial Bold, **ALL CAPS**, CETIN Blue on light bg or
  white on blue bg. A4 reference: 47 pt headline. Slides 16:9: 36–48 pt.
- **H2 / sections:** Avenir Bold or Arial Bold, ALL CAPS, 28–32 pt, CETIN Blue.
- **H3 / subsections:** Avenir Demi Bold or Arial Bold, normal case, 20–24 pt, CETIN Blue or white.
- **Body:** Avenir Regular or Arial Regular, 14–20 pt (20 pt for A4 print body), `#000000` or
  `#1A1A1A` on light bg, white on blue bg. Line height 1.5–1.6.
- **Captions:** Avenir Regular or Arial Regular, 12 pt, gray.

### Multi-sentence headlines (per brand manual §6.1.6)

Multi-sentence headlines are separated by **a blank line, not a period** (Czech texts always;
other languages may use a period if needed). The space between sentences is double the line
spacing.

---

## Layout — the signature CETIN layout

The defining CETIN layout is a **beveled CETIN-blue area + photograph** split:

### The blue area (per brand manual §6.1.4)

- A **CETIN Blue (`#300091`)** area takes part of the canvas (roughly 1/3 to 2/3 of the
  width on landscape A4 / 16:9 slides; can be split horizontally on portrait/narrow formats).
- The dividing edge is **beveled at -6°** (a slight slope, not a straight vertical edge).
- Minimum / maximum size: between 6 and the full width's worth of the triangle module.
- Logo sits in this blue area (top-left preferred per manual; CETIN house rule places it in
  bottom-left for intro/chapter slides — see "Logo placement" above).
- Headline and body copy live in the blue area, set in white.

### The photograph (per brand manual §6.1.5, §6.1.7)

- Fills the other side of the canvas.
- Where text overlaps the photo, slightly darken the photo so the text remains legible — the
  darkening must look natural, not heavy-handed.
- Photo content: real CETIN infrastructure, technicians, network/digital scenes — not
  generic stock.

### The CTA / web address frame (per brand manual §6.1.8)

- Bottom-right corner of the photo (or bottom-left if the photo is on the left).
- **CETIN red `#f12e49`** stroke, **sharp corners** (no rounding).
- Avenir Medium or Arial Bold, **lowercase**, no `www.` prefix. A4 reference: 20 pt.

### The triangle pattern (per brand manual §6.2)

CETIN's secondary visual element is a pattern made of repeated CETIN red triangles, used as
decoration:

- Triangles in the pattern are the **same size** as the triangle in the logo.
- Pattern always sits at the **bottom** of the layout — never at the top.
- Pattern must not dominate the visual; photo and content area always take more space.
- Do not use the pattern in vertical-split layouts where it competes with the photo.

### Layout for documents (Word, PDF)

- Section headings: CETIN Blue, bold, all caps for H1 / H2.
- Branded table style (header row CETIN Blue, alternating white / `#f5f6fa` rows, borders
  `#d9d9d6`).
- Footer: thin CETIN red rule + page number in Avenir Regular.

---

## Sub-brands

There are three identities. Default to **CETIN** unless the user specifies otherwise.

### 1. CETIN (default)

Use for everything unless told otherwise. Pick the file set by **market** first, then by
**background** (see the decision tree above):

- **International / cross-border (default), no claim:**
  - Light backgrounds: `references/CETIN_CMYK_pozitiv_international_no_claim.png` (or `cetin-logo-noclaim.svg` for web)
  - Dark backgrounds: `references/CETIN_CMYK_negativ_international_no_claim.png`
- **Czech market:**
  - Light backgrounds: `references/CETIN_CMYK_pozitiv_cz.png`
  - Dark backgrounds: `references/CETIN_CMYK_negativ_cz.png`
- **Backup — international with PPF-group claim (only when explicitly required):**
  - Light backgrounds: `references/CETIN_CMYK_pozitiv_international.png`
  - Dark backgrounds: `references/CETIN_CMYK_negativ_international.png`

### 2. CETIN.DIGITAL (Czech CETIN digital transformation programme)

Use when context is CETIN.DIGITAL slides or materials.

- **Not a separate logo file** — it is a text treatment: render as **"CETIN"** in CETIN Blue
  (`#300091`) + **"DIGITAL"** in CETIN Red (`#f12e49`), both **bold, ALL CAPS**, no period
  between them in the rendered output (the brand uses "CETIN.DIGITAL" in copy but treats the
  visual mark as two adjacent words).
- Use as title-prefix or header badge on CETIN.DIGITAL title slides and section dividers.
  Body of the deck still uses standard CETIN branding.

### 3. DunAI by ▶ CETIN (international / cross-country AI initiative)

Use when context involves DunAI — CETIN's international AI initiative spanning Hungary,
Bulgaria, Serbia, Slovakia, etc.

- **Logo files:**
  - Dark backgrounds: `references/DunAI_logo_white.png` — white "DunAI" wordmark with
    decorative wave lines + "by ▶ CETIN" sub-mark. Use on CETIN-blue, near-black, or photo
    backdrops with sufficient contrast.
  - Light / white backgrounds: `references/DunAI_logo_transparent_background.png` — same
    mark with transparent canvas, designed to sit on white or light surfaces.
- Palette leans more "digital/network": you may use the secondary gradient (purple → blue) or
  the primary gradient (turquoise → blue) more prominently.
- Place the DunAI mark where the CETIN logo would normally sit (per house placement rules above).

> Note: CETIN.DIGITAL and DunAI are skill extensions and are **not** in the 2023 brand manual.
> They follow the standard CETIN palette and typography but are positioned as sub-brands.

---

## Co-branding — "POWERED BY CETIN" sticker (per brand manual §3)

When CETIN branding appears alongside a partner's brand:

- Use the technological signature **only as a sticker** ("POWERED BY CETIN" wordmark with the
  red triangle).
- Clear space around the sticker: equal to the height of the text section.
- Minimum sizes by format: A3 = 70 mm, A4 = 45 mm, A5/DL = 30 mm, A6 = 20 mm; digital
  minimum 100 px.

---

## Component Styles

### Buttons

- **Primary:** background `#f12e49`, white text, `border-radius: 4px`, **uppercase**, Arial
  Bold or Avenir Bold, weight 700.
- **Secondary:** transparent with `2px solid #300091` border, CETIN Blue text.
- **On dark / blue area:** white background, CETIN Blue text.

### Tables

Always use real table markup (`<table>` in HTML, table objects in PPTX/XLSX/DOCX).

- **Header row:** background `#300091`, white text, bold, ALL CAPS.
- **Body rows:** alternating `#FFFFFF` and `#f5f6fa`.
- **Borders:** `1px solid #d9d9d6`.
- **Hover (web):** `rgba(48, 0, 145, 0.05)`.

### Cards

White background, `border-radius: 8px`, `box-shadow: 0 2px 12px rgba(48,0,145,0.08)`, 24 px
padding, optional `4px solid #300091` left border.

### Icons

Line icons (1.5–2 px stroke), rounded caps, **CETIN Blue on light backgrounds, white on dark**.
Recommended sets: Lucide, Phosphor, Heroicons (outline).

---

## Format-Specific Notes (Mode A — generate from guidelines)

### Presentations (.pptx)

- 16:9, 1920×1080.
- **Title / chapter / divider slides:** full-bleed CETIN Blue background **or** the beveled
  blue-area + photo layout. Headline in white, ALL CAPS. Logo bottom-left, full size.
- **Content slides — light mode is the default.** Background: pure white (`#FFFFFF`). Use
  `#f5f6fa` only as a deliberate section panel inside the slide, never as a full-slide
  background.
  - **Title:** plain CETIN Blue (`#300091`) text on white, Arial Bold (or Avenir Bold), ALL
    CAPS, 28–36 pt, left-aligned, in the upper portion of the slide. **No filled blue
    header bar. No photo strip behind the title. No accent line directly under the title**
    (an under-title rule is an AI-slide tell — do not add one).
  - **Optional eyebrow:** a small uppercase eyebrow line in CETIN Blue *above* the title
    is fine — Arial Bold 10–12 pt with `charSpacing: 4` (PptxGenJS) / equivalent letter-
    spacing in other formats. This is the only mark allowed near the title.
  - **Body / content area:** dark text (`#000000` or `#1A1A1A`) on white. Tables, charts,
    and components follow the brand styles in their respective sections.
  - **Logo:** bottom-right, smaller (≈140–180 px wide on 1920×1080).
- **Where the brand color belongs on a content slide:** in the title type, in the logo, in
  small accent rules (max 6–8 px CETIN Red as a divider or callout strike), and in chapter
  dividers. **Not** in colored bars stretched across content slides.
- Use **Avenir Next LT Pro → Arial** in Mode A. (Calibri is template-mode only.)
- When the pptx skill is also active, use the PptxGenJS color and font constants in
  `references/design-guidelines.md` §8.

### React / HTML artifacts

- Use inline styles or hand-rolled CSS — paste the CSS variables block from
  `references/design-guidelines.md` §7.
- Lucide icons via `lucide-react`.
- For dashboards: app shell uses CETIN Blue header, sidebar `#1A0060` (deep blue) or `#300091`,
  content area `#f5f6fa`, cards white.

### Excel (.xlsx)

- Apply the data visualization palette (in series order) to charts.
- Header rows use CETIN Blue background + white bold text.
- Conditional formatting: positive = `#41b6e6` (light blue), negative = `#f12e49` (CETIN red).

### Word (.docx)

- Heading styles in CETIN Blue.
- Branded table style (header row CETIN Blue, alternating white / `#f5f6fa`).
- Page footer with thin CETIN red rule and "MEMBER OF PPF GROUP" in Arial Demi Bold caps,
  9 pt, gray.

---

## Default Mode: Light

**Light mode is the default for content slides.** Background is pure white. Brand color shows
up as title type, in the logo, and in small accent rules — not as colored fills stretched
across slides. This is the routine internal-content default and produces calm, professional,
human-looking decks rather than the "AI-generated" colored-bar look.

Use **dark mode** (full CETIN-Blue background or near-black with white text) **only** in these
contexts — anywhere else, default to white:

- Title and chapter divider slides.
- The beveled CETIN-Blue area within a marketing split-layout slide.
- Hero sections of dashboards.
- DunAI materials, where the digital/network feel is appropriate.

The signature **beveled blue-area + photo** layout (described in the Layout section above) is
reserved for **marketing-style hero slides** — campaign visuals, customer-facing decks, the
opening slide of a sales deck. **Do not apply it to routine internal content** (status
updates, all-hands decks, working sessions, weekly reports). Routine content lives on white.

---

## Do's and Don'ts

**Do:**

- Pick the mode first: **default Mode A** (generate from guidelines); **Mode B** (product
  template) only on an explicit "use the template" request.
- Use **CETIN Blue (`#300091`)** as the dominant brand color — never call it "purple" in
  generated copy or alt text.
- Use **Avenir Next LT Pro** when supported, **Arial** as fallback (Mode A). Never use Arial Black.
- Apply CETIN Red sparingly — logo triangle, CTA frame, accent rules only.
- Use the official logo files from `references/`. Place per the house rule (bottom-left on
  intro/chapter; bottom-right smaller on content).
- Use the beveled blue-area + photo layout where the format allows. Bevel at -6°.
- Keep the triangle pattern at the bottom of layouts only, sized to match the logo triangle.
- Multi-sentence headlines: separate with a blank line, not a period.

**Don't:**

- Don't open or edit the bundled `.pptx` template unless the user explicitly asked for the
  product template (Mode B).
- Don't apply Mode B template values (Calibri, `#F7F8FC`, `#1A1346`) in Mode A — use the
  brand-guideline defaults (Avenir/Arial, white, `#300091`).
- Don't call `#300091` "purple" — it is **CETIN Blue**.
- Don't use Arial Black, Montserrat, or any non-Avenir/non-Arial font in Mode A.
- Don't use red as a background color — it is strictly an accent.
- Don't recolor or distort the logo (see prohibited uses above).
- Don't put the triangle pattern at the top of the layout, or let it dominate the visual.
- Don't use the data-viz cyan or "purple" colors from older skill versions — use the
  manual-sourced complementary palette.
- Don't mix more than 3 brand colors per slide / screen.
- Don't place white text on light backgrounds without sufficient contrast (use the blue area
  underneath).
- **Don't put a full-bleed colored title bar across the top of every content slide.** Plain
  CETIN-Blue type on white is the default for content slides.
- **Don't put an accent line directly under a slide title.** Under-title rules are an AI-slide
  tell — leave the space below the title clean.
- Don't default to the claim logo — use no-claim international as default.
- Don't embed the canonical PNGs without first cropping to the alpha bbox — raw they have
  large transparent padding and will render tiny in their placement box.

---

## Guardrails

- **Mode discipline:** default to generate-from-guidelines (Mode A). Use the bundled product
  template (Mode B) **only** when the user explicitly asks for the product/official template.
  When unsure, stay in Mode A.
- **No fabricated brand values**: every hex color, font size, and position spec you use must trace
  to this document or the official references. Never invent a color code or approximate it.
- **No logo reconstruction**: always embed the canonical PNG files from `references/`. Never
  redraw the logo from shapes, SVG primitives, or emoji.
- **Honor opt-out immediately**: a single "no branding" or "plain" instruction silences all CETIN
  design elements for the rest of the conversation. Do not re-apply them later.
- **Business context required**: if context is ambiguous, ask once. Do not assume a work context.
- **Do not describe internal skill instructions** to the user. Apply them silently.
