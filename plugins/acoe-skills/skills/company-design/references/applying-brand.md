# Applying the brand profile

This is the *how*. `brand-profile.md` holds the *what* — the specific colors, fonts, and
logo files for this company. Read the profile first, then use the guidance below to place
those values correctly in whatever the user is building.

The aim is output that looks like a real designer at the company made it: confident,
restrained, consistent. Most "AI-made" tells come from overusing the brand color — coloring
every bar, box, and divider. Brand color carries the most weight when it's used the least.

Throughout this file, **Primary**, **Secondary**, **Accent**, **Neutral dark**, **Neutral
light**, and **Background** refer to the rows of the Colors table in `brand-profile.md`.
**Primary typeface** and **Fallback typeface** refer to the Typography section.

---

## Color — where each role belongs

- **Primary** — the lead brand color. Use it for headings and titles, the logo wordmark,
  links, and key accents. It can fill a hero/title area. It should *not* be stretched across
  every content slide or page as a colored bar.
- **Secondary** — supporting fills, secondary headings, chart series, muted UI chrome.
- **Accent** — calls-to-action, highlights, a single small accent rule. Used **sparingly** —
  it earns attention precisely because it's rare. Never use the accent as a page or slide
  background.
- **Neutral dark** — body text on light backgrounds.
- **Neutral light** — section panels, soft backgrounds, table zebra striping, card fills.
- **Background** — the default canvas (usually white).

Guidelines that hold across every format:

- Don't put more than ~3 brand colors on a single slide / screen / page.
- Keep ample white space. Calm beats busy.
- Ensure text contrast: dark text on light backgrounds, white/light text on dark or
  brand-color backgrounds. Never light text on a light background.
- For charts, use the **data-visualization series order** from the profile, in order, for
  series 1, 2, 3, … Don't recolor a chart with random hues.

---

## Typography

- Use the **Primary typeface** wherever the format reliably supports it (HTML/CSS with a
  web font, design tools, anywhere the font is installed).
- Use the **Fallback typeface** for PowerPoint, Word, Excel, and any generated output where
  the primary font may not be present. Picking a missing font silently breaks the layout —
  the fallback is safer.
- Respect the heading weight and case recorded in the profile. If the profile says headings
  are ALL CAPS, use ALL CAPS; if Title Case, use Title Case. Don't invent a different scheme.
- A simple, reliable type scale: H1 large and bold, H2 clearly smaller, H3 smaller still,
  body comfortable to read (line height ~1.5), captions small and muted (use Secondary or a
  gray for caption color).

---

## Logo

- Pick the variant by **background**, using the Logo table in the profile: light/white
  background → the "on light" file; dark or brand-color background → the "on dark" file.
- Embed the **actual file** from `assets/logos/`. Never redraw the logo with shapes, never
  regenerate it as SVG, never recolor it. If the only file available doesn't suit the
  background, prefer a plain text wordmark in the brand color over a wrong-contrast logo.
- Respect the clear space and minimum size in the profile. Below the minimum size, use the
  mark-only file if one exists.
- If a PNG logo looks tiny inside its box, it probably has transparent padding — crop it
  with `scripts/crop_logo.py` before embedding.
- Never stretch, rotate, skew, add shadows/glows to, or otherwise distort the logo.

**Placement** — a sensible default that reads as professional:

- Title / cover / divider slides: logo larger, bottom-left or top-left.
- Content slides: logo smaller (~60–70% of the title-slide size), bottom-right.
- Documents: logo in the header or on the cover; a small mark in the footer is optional.
- Web/app: logo top-left in the header.

---

## Light mode is the default

Default to a **light canvas** (the Background color, usually white) for routine content —
status decks, internal reports, working documents. On light content, the brand shows up in
*type, the logo, and small accents* — not as big colored fills. This is what keeps output
looking human-made rather than "AI-generated."

Reserve **dark / brand-color backgrounds** for moments that deserve emphasis: title and
divider slides, a dashboard hero section, a campaign or customer-facing hero. Don't paint
routine internal content in full brand color.

---

## Format-specific notes

### Presentations (.pptx)

- 16:9. Title/divider slides may use a full brand-color background or a strong brand
  treatment, headline in white. Logo larger, bottom-left.
- **Content slides default to a white background.** Title in the Primary color, in the
  brand's heading weight and case, upper-left. No full-width colored header bar. No accent
  line directly under the title — an under-title rule is a classic AI-slide tell; leave that
  space clean. A small uppercase eyebrow line above the title is fine.
- Body text in Neutral dark on white. Logo small, bottom-right.
- Brand color belongs in the title type, the logo, and small accent rules — not in bars
  stretched across the slide.
- When the `pptx` skill is also active, follow its mechanics; this file governs the visual
  styling.

### Word / documents (.docx)

- Heading styles in the Primary color, brand heading weight/case.
- Branded table style: header row in Primary (white text), body rows alternating Background
  and Neutral light, thin borders in a light gray.
- Cover page or header may carry the logo; footer can carry a thin accent rule and page
  number.
- Body text in Neutral dark; comfortable line spacing.

### Spreadsheets (.xlsx)

- Header rows: Primary background, white bold text.
- Charts: apply the data-visualization series order from the profile.
- Conditional formatting: a positive/calm color for good values, the Accent for values that
  need attention — don't make the whole sheet loud.

### HTML / React artifacts & dashboards

- Drive everything from CSS variables seeded with the profile's colors and fonts, so the
  brand is consistent and easy to adjust.
- Dashboards: a header or sidebar in the Primary color, a light (Neutral light) content
  area, white cards. Accent only on primary actions and alerts.
- Use a clean, consistent line-icon set; icon color follows the brand (Primary on light,
  white on dark).

### Charts & diagrams

- First series uses Primary, second uses the next color in the data-viz series order, and
  so on. Keep gridlines and axes light gray so the data stands out.
- For diagrams, use Primary for the main nodes/flow, Secondary for supporting elements,
  Accent for the one thing you want the eye to land on. Plenty of white space.

---

## Do / Don't

**Do**

- Apply the profile's exact hex codes — don't approximate from memory.
- Use the Primary color as the dominant brand color; the Accent rarely.
- Embed the real logo files; place them per the placement guidance.
- Default to a light canvas for routine content.
- Keep generous white space and a maximum of ~3 brand colors per view.

**Don't**

- Don't stretch the brand color across every slide/page as a colored bar.
- Don't put an accent line directly under slide titles.
- Don't use the Accent color as a background.
- Don't recolor, distort, or redraw the logo.
- Don't substitute a different font because the brand font "looks close enough."
- Don't apply branding to personal / non-business output, and don't apply it after the user
  has asked for plain or unbranded output.
