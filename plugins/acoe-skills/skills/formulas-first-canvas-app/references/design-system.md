# The token layer

## Principle

**Every visual value is named by its role, defined once, and referenced everywhere.**

Role, not appearance: `constInkColor`, not `constDarkGrey`. When the body text colour
changes from black to near-black, a role name still reads true and a value name becomes
a lie — and the lie is what makes the next person inline a literal instead.

Paste-ready block: `templates/design-tokens.pa.yaml`.
Rendered spec sheet (swatches, live contrast, type scale, control specs), if you have
access: https://claude.ai/code/artifact/cdff9a80-7b84-4f56-9ce2-beaa4152424d
The values below are authoritative either way.

## Structure

Two levels, and no more. Flat scalars for brand and semantic colours; one nested
`constStyle` object for control specs.

```
constPrimaryColor   = {RGBA: …, HEX: "#300091"};   // both forms — see below
constStyle = {
    BasicStyle: { Font, FontSize: {Large, Medium, Small}, Border, FontColor },
    Label:      { Height: {Large, Medium, Small}, TextInput: {…}, NumberInput: {…} },
    Button:     { Height: {Medium, Small}, BorderRadius, FontWeight, … },
    …
};
```

**Carry both `RGBA` and `HEX`.** Canvas properties need the `Color` value; `HEX` is what
you paste into a design tool, quote in a spec, and diff in review. Two fields cost
nothing and remove a whole class of transcription error.

Three levels of nesting is where it stops paying: `constStyle.Form.NestedList.Unrelate.Icon`
is a value nobody will find by browsing, and a component input property would have
served better.

## Contrast — the failure to design out first

Status colour used as small text on white is the most common accessibility failure in
business canvas apps, and it fails badly. Measured against `#FFFFFF` (WCAG 2.x; AA needs
**4.5:1** for body text, **3.0:1** for large text and UI components):

| Colour | Ratio | Verdict |
|---|---|---|
| `#300091` brand | **13.68** | passes everything |
| `#1A1A1F` ink | **17.33** | passes everything |
| `#B80000` error | **6.91** | passes |
| `#f12e49` accent | **4.02** | **fails body text**; large text and UI only |
| `#36B04B` green | **2.81** | **fails as text** |
| `#FFBF00` amber | **1.65** | **fails everywhere as text** |

The fix is not to abandon the status palette — a red/amber/green traffic light is often
a stated business requirement. It is to **split fill from text**:

| Role | Token | Ratio | Used for |
|---|---|---|---|
| Positive text | `constGainTextColor` `#1F7A33` | **5.40** | savings figures, "Finished" |
| In-progress text | `constHoldTextColor` `#8A6400` | **5.38** | "In Progress", "On hold" |
| Negative text | `constLossTextColor` `#B80000` | **6.91** | losses, "Cancelled" |
| Fills and dots | `constSemaforColors.*` | — | keeps the literal traffic-light hues |

Dots, chips and fills keep the vivid colours. Text takes the dark variants. Route it
through one function — `funcStatusTextColor(status)`, `funcMoneyTextColor(value)` — so a
future palette change is one edit, not a sweep.

## Semantic overload of red

Watch for one colour meaning four things: brand accent, error, warning, and "look here"
badges. When red means everything it means nothing, and users stop reading it as
urgency. Give the brand accent a non-alarm job, or give alarms their own token.

## Type scale

Pick five sizes and refuse the sixth.

```
28  KPI figures only
20  screen and section titles
14  body — the default
12  secondary, table headers
11  captions, chips
```

The failure mode is accumulation, not bad choices: tokens define 20/14/12 and then
literals add 10, 10.5, 11, 13, 16, 18, 36 one screen at a time. The result is three
*nearly* identical small sizes on one screen — visible as sloppiness without being
identifiable. `scripts/inventory.py` lists font sizes by frequency; anything outside the
scale with a count of one or two is drift.

## Spacing

**One grid.** 4px: 4 / 8 / 12 / 16 / 24 / 32.

Two grids at war — 4px and 5px — is a real and common state, and it reads as slightly
uneven padding everywhere without any single instance looking wrong. Pick one, and put
`constTabPadding`-style values on it.

Radius: one value (`constBorderRadius = 10`), applied to cards, inputs and buttons
alike.

## Numerals

For any app whose audience reads figures all day:

- **Right-align money and quantities**, in cells *and* headers. Left-aligned currency in
  a grid is the single worst typographic error in a business app — it destroys the
  vertical scan that makes a column of numbers comparable at a glance.
- The `NumberInput` token carries `Align.End`. Grid cells are labels, not inputs, so
  they do not inherit it. Set it explicitly.
- Format with an explicit locale: `Text(v, "[$-en-US]#,##0")`. Locale-default formats
  render decimals inconsistently.
- Power Fx treats `%` in a format string as a **literal** — no ×100. Multiply
  explicitly.

## Accessibility beyond contrast

Canvas apps are usually fixed-frame, so responsive rules do not apply, but these do:

- **`AccessibleLabel` on every icon-only button.** This is normally the largest single
  finding count in the app checker, and it is mechanical to fix — a sweep can take a
  finding count from the hundreds to single digits in one pass.
- **`TabIndex`** deliberate on interactive controls; `-1` on decorative ones.
- **Never colour alone** for state. Pair the dot with a word.
- Re-run `get_appchecker_errors` after the sweep — it uses a laxer engine than compile
  and is the only place these findings surface.

## Components and tokens

A component without `AccessAppScope: true` **cannot see app tokens**. Three honest
options, in order of preference:

1. Set `AccessAppScope: true`.
2. Pass the tokens in as input properties (correct when the component is genuinely
   reusable across apps).
3. Leave the literals and **record the exemption in the inventory**.

What is not an option is leaving them unrecorded. An undocumented exemption is
indistinguishable from rot, and the next person to run the guard script will either
"fix" it wrongly or add a suppression.
