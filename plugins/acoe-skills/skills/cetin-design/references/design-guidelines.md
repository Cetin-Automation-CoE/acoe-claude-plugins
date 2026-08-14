# CETIN Design Guidelines — Full Specification

This file is the long-form companion to `SKILL.md`. It contains the ready-to-paste blocks of
code (CSS variables, Tailwind config, PptxGenJS constants, etc.) that keep the brand consistent
across formats. All values are sourced from the official CETIN Brand Guidelines (EN V17, 2023)
unless explicitly noted as a CETIN house rule or skill extension.

---

## 1. Color tokens (canonical hex values)

### Primary
- `cetin-blue`: `#300091`  (RGB 48 / 0 / 145  ·  CMYK 91 / 91 / 0 / 0  ·  Pantone 2735 C)
- `cetin-red`:  `#f12e49`  (RGB 241 / 46 / 73  ·  CMYK 0 / 89 / 66 / 0  ·  Pantone 1787 C)
- `white`:      `#ffffff`

### Secondary
- `middle-gray`:  `#c7c9c7`  (Pantone 420 C)
- `light-blue`:   `#41b6e6`  (Pantone 298 C)
- `light-purple`: `#6f79bd`  (Pantone 2115 C)
- `black`:        `#000000`

### Background (print + general)
- `bg-light-gray`:   `#d9d9d6`
- `bg-light-blue`:   `#99d6ea`
- `bg-light-purple`: `#a7a4e0`
- `bg-white`:        `#ffffff`

### Background (digital only — screen, email, banners; not print)
- `digi-bg-1`: `#f5f6fa`
- `digi-bg-2`: `#d7dae1`
- `digi-bg-3`: `#cdd4e5`
- `digi-bg-4`: `#66678a`

These can be reduced to 50% or 75% opacity.

### Complementary palette (charts, illustrations, infographics)
Row 1 — saturated:
`#3F3E98` · `#87C4E7` · `#7078B8` · `#1F4D9A` · `#81C78F` · `#70D1E2`

Row 2 — desaturated:
`#49A2D8` · `#6AC9BB` · `#DEE5F1` · `#C6E4EF` · `#F3D9DD` · `#D4EAD5`

### Gradients
- **Primary:** `linear-gradient(145deg, #70D1E2 0%, #1F4D9A 100%)` at 30% opacity
- **Secondary:** `linear-gradient(0deg, #A7A4E0 0%, #99D6EA 100%)` at 20% opacity

### Recommended chart series order
`#300091` → `#f12e49` → `#41b6e6` → `#6f79bd` → `#3F3E98` → `#1F4D9A` → `#70D1E2` → `#c7c9c7`

---

## 2. Typography

### Primary — Avenir Next LT Pro
- Cuts in use: **Bold** (headlines, logo wordmark), **Demi Bold** (claim, sub-heads), **Regular** (body, captions).
- Logo construction reference (per manual §2.7): at 50 mm logo width, wordmark = 32 pt, tracking 210 pt; claim = 9.5 pt, tracking 5 pt.

### Fallback — Arial
Used in **PowerPoint, Word, web/HTML, Excel** and any format where Avenir is not available.
- Cuts: **Bold**, **Regular**.
- **Do not** use Arial Black, Helvetica, Roboto, Montserrat, Open Sans, or any other substitute.

### Font stacks
```css
--font-heading: 'Avenir Next LT Pro', 'Avenir Next', Avenir, Arial, sans-serif;
--font-body:    'Avenir Next LT Pro', 'Avenir Next', Avenir, Arial, sans-serif;
--font-fallback-stack: Arial, 'Helvetica Neue', Helvetica, sans-serif;
```

### Type scale (16:9 slide reference, 1920×1080)
| Token       | Size    | Weight | Case        | Notes                                   |
|-------------|---------|--------|-------------|-----------------------------------------|
| h1-slide    | 48 pt   | Bold   | UPPERCASE   | Slide titles                            |
| h1-A4-print | 47 pt   | Bold   | UPPERCASE   | A4 print headlines                      |
| h2          | 32 pt   | Bold   | UPPERCASE   | Section breaks                          |
| h3          | 24 pt   | Demi   | Sentence    | Subsections                             |
| body-print  | 20 pt   | Regular| Sentence    | A4 body                                 |
| body-screen | 16 pt   | Regular| Sentence    | Default web/UI body                     |
| caption     | 12 pt   | Regular| Sentence    | Photo captions, fine print              |

Body line-height: 1.5–1.6. Uppercase letter-spacing: 0.02–0.05em.

---

## 3. Logo

### Placement (CETIN house rule, overrides brand manual default)
| Slide type                             | Position       | Size                  |
|----------------------------------------|----------------|-----------------------|
| Intro / chapter / divider / title      | Bottom-left    | Full size (≈240–280 px wide on 1920×1080) |
| Content                                | Bottom-right   | Smaller (≈140–180 px wide)                |

### Clear space
Equal to the height of the red triangle on all sides.

### Minimum size
- Recommended: 100 px width.
- Absolute minimum: 60 px width.
- Below 100 px width, prefer the version without claim.

### File names

International / English-language variant (default for cross-border / English):
- Dark backgrounds: `references/CETIN_CMYK_negativ_international.png` (white wordmark)
- Light backgrounds: `references/CETIN_CMYK_pozitiv_international.png` (CETIN-blue wordmark)

Czech / cetin.cz variant (default for Czech-language / internal CZ / CETIN.DIGITAL):
- Dark backgrounds: `references/logo_cetin_dark_cz.svg` (white wordmark)
- Light backgrounds: `references/logo_cetin_light_cz.svg` (CETIN-blue wordmark)

DunAI:
- Dark backgrounds (white wordmark): `references/DunAI_logo_white.png`
- Light / white backgrounds (transparent canvas): `references/DunAI_logo_transparent_background.png`

---

## 4. Layout — the signature beveled split

Per brand manual §6.1.4:
- One side: solid `#300091` (CETIN Blue) area carrying logo + headline + body text.
- Other side: photograph.
- **Dividing edge beveled at -6°.**
- For landscape: blue area on the left (default) or right.
- For portrait: split horizontally instead.
- Blue area minimum / maximum: between 6 triangle-units and full width's worth.

CTA frame (per §6.1.8): bottom-right corner of the photo, **CETIN red** stroke, **sharp corners** (no border-radius), Avenir Medium / Arial Bold lowercase, no `www.` prefix.

Triangle pattern (per §6.2):
- Always at the bottom of the layout — never at the top.
- Triangles same size as the logo triangle.
- Must not dominate the visual.

---

## 5. Components

### Buttons
```css
.btn-primary {
  background: #f12e49;
  color: #ffffff;
  font: 700 14px/1 Arial, sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 12px 24px;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary {
  background: transparent;
  color: #300091;
  font: 700 14px/1 Arial, sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 10px 22px;
  border: 2px solid #300091;
  border-radius: 4px;
}
```

### Tables (HTML)
```css
table.cetin {
  width: 100%;
  border-collapse: collapse;
  font: 400 14px/1.5 Arial, sans-serif;
}
table.cetin thead th {
  background: #300091;
  color: #ffffff;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 12px 16px;
  text-align: left;
}
table.cetin tbody td {
  padding: 10px 16px;
  border-bottom: 1px solid #d9d9d6;
}
table.cetin tbody tr:nth-child(even) td { background: #f5f6fa; }
table.cetin tbody tr:hover td { background: rgba(48, 0, 145, 0.05); }
```

### Cards
```css
.cetin-card {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(48, 0, 145, 0.08);
  padding: 24px;
  border-left: 4px solid #300091; /* optional */
}
```

---

## 6. CTA / web-address frame
```css
.cetin-cta {
  display: inline-block;
  border: 2px solid #f12e49;
  padding: 8px 14px;
  font: 500 16px/1 Arial, sans-serif;
  text-transform: lowercase;
  color: #1a1a1a;
  background: rgba(255,255,255,0.85);
  /* sharp corners — DO NOT add border-radius */
}
```

---

## 7. Drop-in CSS variables (paste into any `<style>` block)

```css
:root {
  /* Primary */
  --cetin-blue: #300091;
  --cetin-red: #f12e49;
  --white: #ffffff;

  /* Secondary */
  --middle-gray: #c7c9c7;
  --light-blue: #41b6e6;
  --light-purple: #6f79bd;
  --black: #000000;

  /* Backgrounds */
  --bg-light-gray: #d9d9d6;
  --bg-light-blue: #99d6ea;
  --bg-light-purple: #a7a4e0;

  /* Digital backgrounds */
  --digi-bg-1: #f5f6fa;
  --digi-bg-2: #d7dae1;
  --digi-bg-3: #cdd4e5;
  --digi-bg-4: #66678a;

  /* Complementary (chart palette) */
  --comp-1:  #3F3E98;
  --comp-2:  #87C4E7;
  --comp-3:  #7078B8;
  --comp-4:  #1F4D9A;
  --comp-5:  #81C78F;
  --comp-6:  #70D1E2;
  --comp-7:  #49A2D8;
  --comp-8:  #6AC9BB;
  --comp-9:  #DEE5F1;
  --comp-10: #C6E4EF;
  --comp-11: #F3D9DD;
  --comp-12: #D4EAD5;

  /* Gradients */
  --gradient-primary:   linear-gradient(145deg, #70D1E2 0%, #1F4D9A 100%);
  --gradient-secondary: linear-gradient(0deg,   #A7A4E0 0%, #99D6EA 100%);

  /* Type */
  --font-body:    'Avenir Next LT Pro', 'Avenir Next', Avenir, Arial, sans-serif;
  --font-heading: 'Avenir Next LT Pro', 'Avenir Next', Avenir, Arial, sans-serif;

  /* Radii / shadows */
  --radius-sm: 4px;
  --radius-md: 8px;
  --shadow-card: 0 2px 12px rgba(48, 0, 145, 0.08);
}

body {
  font-family: var(--font-body);
  color: #1a1a1a;
  background: var(--digi-bg-1);
  line-height: 1.6;
}

h1, h2, h3 {
  font-family: var(--font-heading);
  color: var(--cetin-blue);
  font-weight: 700;
  letter-spacing: 0.03em;
}
h1, h2 { text-transform: uppercase; }
```

---

## 8. PptxGenJS configuration

```js
// CETIN brand constants for PptxGenJS
const CETIN = {
  // Colors (PptxGenJS expects hex without leading #)
  color: {
    blue: '300091',
    red: 'F12E49',
    white: 'FFFFFF',
    middleGray: 'C7C9C7',
    lightBlue: '41B6E6',
    lightPurple: '6F79BD',
    black: '000000',
    bgLightGray: 'D9D9D6',
    bgLightBlue: '99D6EA',
    bgLightPurple: 'A7A4E0',
    digiBg1: 'F5F6FA',
    digiBg2: 'D7DAE1',
    digiBg3: 'CDD4E5',
    digiBg4: '66678A',
  },
  font: {
    heading: 'Arial',  // Avenir Next LT Pro is rarely available in PowerPoint; use Arial Bold
    body: 'Arial',
  },
  // Chart series colors in canonical order
  chartColors: [
    '300091', 'F12E49', '41B6E6', '6F79BD',
    '3F3E98', '1F4D9A', '70D1E2', 'C7C9C7',
  ],
  // Logo files (resolved relative to skill's references/ folder).
  // Pick the variant that matches the deck's language / audience.
  logo: {
    international: {
      dark:  'references/CETIN_CMYK_negativ_international.png',
      light: 'references/CETIN_CMYK_pozitiv_international.png',
    },
    cz: {
      dark:  'references/logo_cetin_dark_cz.svg',
      light: 'references/logo_cetin_light_cz.svg',
    },
    dunai: {
      dark:  'references/DunAI_logo_white.png',
      light: 'references/DunAI_logo_transparent_background.png',
    },
  },
};

// Slide background — title / chapter / divider
const titleSlideBg  = { color: CETIN.color.blue };
// Slide background — content
const contentSlideBg = { color: CETIN.color.digiBg1 }; // #F5F6FA

// Title text style on a content slide
const slideTitleStyle = {
  fontFace: CETIN.font.heading,
  fontSize: 32,
  bold: true,
  color: CETIN.color.blue,
  align: 'left',
};

// Body text style
const slideBodyStyle = {
  fontFace: CETIN.font.body,
  fontSize: 16,
  color: '1A1A1A',
  align: 'left',
};

// Logo placement helper — house rule
function placeLogo(slide, slideKind /* 'intro' | 'content' */) {
  const isIntro = slideKind === 'intro';
  // Slide is 13.333" × 7.5" at 1920×1080 (96 DPI)
  return slide.addImage({
    path: CETIN.logo.light, // or dark, depending on background
    x: isIntro ? 0.4 : 11.0,
    y: isIntro ? 6.5 : 6.8,
    w: isIntro ? 2.0  : 1.4,
    h: isIntro ? 0.55 : 0.4,
  });
}
```

---

## 9. Tailwind preset (subset)

```js
// tailwind.config.js fragment
module.exports = {
  theme: {
    extend: {
      colors: {
        cetin: {
          blue: '#300091',
          red:  '#f12e49',
          gray: '#c7c9c7',
          lightBlue:   '#41b6e6',
          lightPurple: '#6f79bd',
          bgLightGray:   '#d9d9d6',
          bgLightBlue:   '#99d6ea',
          bgLightPurple: '#a7a4e0',
          digiBg1: '#f5f6fa',
          digiBg2: '#d7dae1',
          digiBg3: '#cdd4e5',
          digiBg4: '#66678a',
        },
      },
      fontFamily: {
        heading: ['"Avenir Next LT Pro"', '"Avenir Next"', 'Avenir', 'Arial', 'sans-serif'],
        body:    ['"Avenir Next LT Pro"', '"Avenir Next"', 'Avenir', 'Arial', 'sans-serif'],
      },
      backgroundImage: {
        'cetin-gradient-primary':   'linear-gradient(145deg, #70D1E2 0%, #1F4D9A 100%)',
        'cetin-gradient-secondary': 'linear-gradient(0deg,   #A7A4E0 0%, #99D6EA 100%)',
      },
      boxShadow: {
        card: '0 2px 12px rgba(48, 0, 145, 0.08)',
      },
    },
  },
};
```

> Note: when no Tailwind compiler is available (e.g. single-file React artifacts), use the
> CSS variables block in §7 instead.

---

## 10. Source

These values are extracted from `Brand manual CETIN 2.pdf` — *CETIN Brand Guidelines, EN V17,
January 2023, modified June 2024.* House rules (logo placement bottom-left intro / bottom-right
content; CETIN.DIGITAL and DunAI sub-brand handling) are documented in `SKILL.md` and are
**not** part of the official brand manual.
