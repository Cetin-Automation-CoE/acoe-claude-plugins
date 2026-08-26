# CETIN brand tokens for intake deliverables

Source: CETIN Brand Guidelines (EN V17, 2023), as captured in the `cetin-design` skill in
the ACoE plugin repo (`plugins/acoe-skills/skills/cetin-design/references/design-guidelines.md`).
If that skill is installed alongside this one, prefer it as the source of truth and follow
its Mode A ("generate from guidelines"). The values below are duplicated here so intake
deliverables stay on-brand even when it isn't.

Apply branding to **work output**, which an automation intake always is. Skip it if the
user asks for plain or unbranded output.

## Colours

| Role | Token | Hex | Use for |
|---|---|---|---|
| Primary | CETIN Blue | `#300091` | Headings, BPMN pool/lane headers, table header rows, key accents |
| Primary | CETIN Red | `#f12e49` | Blockers, "red" RAG, PK markers, alerts — sparingly |
| Neutral | White | `#ffffff` | Canvas |
| Secondary | Middle grey | `#c7c9c7` | Rules, borders, connectors |
| Secondary | Light blue | `#41b6e6` | "Amber-alternative" accents, FK markers, links |
| Secondary | Light purple | `#6f79bd` | Supporting fills, muted headings |
| Digital bg | — | `#f5f6fa` | Page background, zebra striping |
| Digital bg | — | `#d7dae1` | Panel fills |
| Digital bg | — | `#cdd4e5` | Stronger panel fills |
| Digital bg | — | `#66678a` | Muted body text on light |
| Ink | — | `#1a1346` | Body text (template-accurate dark) |

Chart/series order: `#300091` → `#f12e49` → `#41b6e6` → `#6f79bd` → `#3F3E98` → `#1F4D9A` → `#70D1E2` → `#c7c9c7`

### RAG mapping for this skill

The intake deliverables need a four-way status scale, which the brand palette does not
supply directly. Use these, which sit inside the brand family and stay legible in both themes:

| Status | Light hex | Dark hex | Meaning |
|---|---|---|---|
| Green — automatable as-is | `#12694a` | `#6fd3a4` | deterministic |
| Amber — needs an agreed rule | `#8a5a00` | `#e8bd6a` | logic exists but undocumented |
| Red — blocked / manual | `#9c2b2b` (headline `#f12e49`) | `#f0908f` | blocked or judgement |
| Decision / handover | `#300091` | `#9dbde6` | needs a decision |

Green and amber are deliberately outside the brand palette: CETIN Blue and Red carry no
"safe/at-risk" meaning, and inventing one from brand colours alone produces a chart nobody
can read. Keep blue and red for their brand roles and treat the RAG scale as functional.

## Typography

- Primary: **Avenir Next LT Pro** (Bold headlines, Demi sub-heads, Regular body)
- Fallback: **Arial** — for HTML, Office, and anything where Avenir isn't licensed.
  Do **not** substitute Helvetica, Roboto, Montserrat, Open Sans or Arial Black.

```css
--font-heading: 'Avenir Next LT Pro', 'Avenir Next', Avenir, Arial, sans-serif;
--font-body:    'Avenir Next LT Pro', 'Avenir Next', Avenir, Arial, sans-serif;
```

Headings in the brand are frequently UPPERCASE with 0.02–0.05em tracking; body line-height
1.5–1.6. In a dense analytical one-pager use uppercase only for small section eyebrows —
uppercase running text hurts readability, which defeats the deliverable's purpose.

## Logo

Files live in the `cetin-design` skill at `references/`:
`cetin-logo-noclaim.svg`, `CETIN_CMYK_pozitiv_cz.png` (light backgrounds),
`CETIN_CMYK_negativ_cz.png` (dark backgrounds).

Embed the actual file; never redraw or recolour it. Keep clear space around it roughly equal
to the height of the logo mark. For an HTML deliverable, inline the SVG or embed the PNG as a
data URI so the page stays self-contained.

A logo is optional on internal working documents. It matters on anything that leaves the
team — a steering pack, a demand submission, a business case.

## CSS token block

The one-pager template (`assets/visual_template.html`) already carries these. Reuse rather
than re-deriving them, so every intake output looks like the same system.

```css
:root{
  --brand:#300091; --brand-red:#f12e49; --brand-lightblue:#41b6e6; --brand-purple:#6f79bd;
  --ink:#1a1346; --ink2:#39414b; --muted:#66678a; --rule:#cdd4e5;
  --bg:#f5f6fa; --card:#ffffff;
  --g:#12694a; --gbg:#e7f3ec; --gbd:#a8d4bd;
  --a:#8a5a00; --abg:#fbf1de; --abd:#e3c68a;
  --r:#9c2b2b; --rbg:#fbeaea; --rbd:#e0aeae;
  --n:#300091; --nbg:#eaeaf6; --nbd:#bcbce0;
}
```
