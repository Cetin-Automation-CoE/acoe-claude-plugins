# Onboarding — learning the company's brand

This is the one-time setup. The goal is to end with a filled-in `brand-profile.md` that
captures the company's real colors, fonts, and logos accurately enough that every future
deliverable looks genuinely on-brand.

It runs in five steps: **collect → extract → validate → propose → save**. Don't skip the
propose step — the user confirms before anything is written, because a wrong brand applied
silently to dozens of future documents is worse than no brand at all.

Work in the outputs / working directory for any temporary files. Only the final profile and
the chosen logo files get written into the skill.

---

## The firm rule: never invent a brand

Every value written into the profile must trace back to something real — a file the user
gave you, or a page you actually retrieved and read. The skill must **not** fall back on
what it happens to know about a company from training. A profile built from memory looks
plausible and is therefore dangerous: it will be subtly wrong, and then applied — unquestioned
— to every future deliverable.

So if you reach the end of collection and extraction with **no real source data in hand**
(the website returned an empty shell, no logo or brand guide was provided, no usable visual
was shared) and there is no way to get more — then **stop**. Do not write the profile, do
not guess. Leave `status: unconfigured`, and tell the user plainly what you tried and what
you need from them: a logo file, a brand-guidelines PDF, a screenshot of their site, or the
specific hex codes and font names. An honest "I couldn't read your brand yet, here's what I
need" is always better than a confident guess that quietly mis-brands everything later.

This rule outranks any instinct to be helpful by filling in the blanks. The skill stays
unconfigured until it has been given a real brand to learn from.

---

## Step 1 — Collect brand sources

Ask the user where their brand lives. They rarely have everything; any one of these is
enough to start, and more is better. Offer the choices explicitly:

- **Company website** — a URL. The fastest source; the live site usually shows the real
  colors, fonts, and logo in use.
- **Logo files** — uploaded image files (PNG/SVG/JPG). The most reliable source for the
  logo itself and often for the primary color.
- **Brand guidelines** — an uploaded brand manual / style guide (PDF or doc). The gold
  standard when it exists: it states exact hex codes, fonts, and rules.
- **Any branded visual** — an existing slide, a screenshot, a one-pager, a business card.
  Useful as a fallback or a cross-check.

Use the `AskUserQuestion` tool to ask which of these they can provide (multi-select). If
they give nothing usable, you cannot invent a brand — explain that you need at least one
source, and offer to proceed unbranded for now and set up later.

Also capture the **company name** and a one-line description of what the company does — ask
if it isn't obvious from the sources.

---

## Step 2 — Extract candidate values

Pull a first draft of the brand from whatever sources the user gave. Gather candidates;
don't finalize anything yet.

### From a website

Fetch the homepage with the `web_fetch` tool (this is the only approved way to retrieve a
URL — never fetch with bash, curl, or Python). From the returned HTML/CSS look for:

- **Colors** — hex/rgb values in inline styles, `<style>` blocks, and linked CSS;
  `theme-color` meta tags; CSS custom properties (`--brand`, `--primary`, etc.).
- **Fonts** — `font-family` declarations and Google Fonts / Adobe Fonts `<link>` tags.
- **Logo** — `<img>` or SVG in the header, `og:image`, favicon / `apple-touch-icon`.

If the page is client-rendered and `web_fetch` returns an empty shell, switch to the
Claude-in-Chrome tools: navigate to the site and read the rendered page / computed styles.
If that's also unavailable, ask the user to upload a screenshot of their homepage instead.
If none of that yields real data — the fetch was empty, no browser is available, and the
user has no screenshot or other source to give — treat the website as a dead end and apply
the "never invent a brand" rule above. Do **not** reconstruct the brand from general
knowledge of the company, even a well-known one; an empty fetch means you have nothing.

### From logo or visual image files

Read the image, then run the bundled color script on it:

```
python scripts/extract_colors.py <path-to-image>
```

It reports the dominant colors as hex with rough proportions. Treat large saturated regions
as brand-color candidates; treat near-white and near-black as neutrals/background.

### From a brand guidelines PDF

This is the best source — use it over guesses from other sources. Read the PDF (use the
`pdf` skill if needed) and pull the explicitly stated hex codes, Pantone/CMYK values, font
names, and any logo-usage or layout rules. Brand manuals usually name a "primary",
"secondary", and "accent" palette directly — use their labels.

### Prepare the logo files

For each logo the user provides, decide which background it belongs on (a logo with a
light/white wordmark → dark backgrounds; a dark/colored wordmark → light backgrounds). If a
PNG has large transparent padding, crop it so it doesn't render tiny later:

```
python scripts/crop_logo.py <input.png> <output.png>
```

Note any gap — e.g. the user gave only a light-background logo and no dark-background
variant. You'll surface that in Step 4.

---

## Step 3 — Validate

Sanity-check the candidates before showing them to the user. Catch problems now, not after
the brand is applied everywhere.

- **Valid colors** — every value is a proper hex code.
- **Readable text** — the color you intend for body text has enough contrast against the
  background color (aim for WCAG AA, contrast ratio ≥ 4.5:1 for normal text). If the
  primary brand color is too light to read as text on white, keep it as an accent and pick
  a dark neutral for body text.
- **De-duplicate** — collapse near-identical colors (a website often has 5 shades of one
  blue); keep one representative per role.
- **Role coverage** — you want at least a primary, a usable dark text color, and a light
  background. Secondary and accent are nice-to-have; don't force them if the brand is
  genuinely minimal.
- **Font fallback** — the primary typeface may be a custom or paid font. Make sure a
  web-safe fallback (Arial, Helvetica, Georgia, etc.) is chosen, since PowerPoint/Word/Excel
  and generated HTML often won't have the custom font.
- **Logo coverage** — ideally one logo variant for light backgrounds and one for dark. If
  one is missing, note it; don't fabricate it.

Track a confidence level for each item. Anything you guessed (rather than read from a brand
manual) should be flagged so the user pays attention to it in the next step.

---

## Step 4 — Propose and confirm

Show the user what you found and let them correct it. This is the most important step — it's
their brand, not yours.

Present a clear, scannable summary:

- Company name and description.
- Each color: role, name, hex code. Describe the color in words too ("a deep navy blue") so
  the user can sanity-check without a color picker.
- Primary typeface and the fallback.
- The logo files and which background each is for.
- Explicitly call out anything low-confidence or missing ("I couldn't find a dark-background
  logo — slides with dark title sections will use a text logo unless you upload one").

Ask the user to confirm or correct. If they want changes, apply them and re-show the
summary. Only proceed once they're happy. If a `show_widget` / visual-preview tool is
available, a small swatch preview of the palette is a nice touch — but a clear text summary
is sufficient.

---

## Step 5 — Save the profile

Before saving, do a final provenance check: every color, font, and logo file about to be
written must trace to a real source you actually saw. If any core value was guessed from
general knowledge rather than read from a source, do **not** save — return to Step 1 and
follow the "never invent a brand" rule. `status: configured` is a promise that the brand is
real.

Once the user confirms:

1. **Copy the logo files** into `assets/logos/` in this skill's directory. Use clear,
   stable names: `logo-on-light.png`, `logo-on-dark.png`, `mark.png`. Use the cropped
   versions from Step 2.
2. **Overwrite `references/brand-profile.md`** with the confirmed values. Set the
   frontmatter to `status: configured`, fill in `company_name`, `configured_on` (today's
   date), and `sources_used`. Fill every section: Company, Colors (including the
   data-visualization series order), Typography, Logo (the table of variant → file →
   background), Layout & voice notes, and Provenance (including confidence notes for
   anything that was guessed). The commented template inside `brand-profile.md` shows the
   exact structure — match its headings so `applying-brand.md` can rely on them.
3. If writing to `references/brand-profile.md` fails because the skill is installed in a
   read-only location, tell the user and ask where to save it instead — don't discard the
   values they just confirmed.

Then confirm setup is complete in one or two sentences, and continue with whatever the user
originally asked for — now on-brand. From here on, every trigger of this skill will see
`status: configured` and skip straight to applying the brand.
