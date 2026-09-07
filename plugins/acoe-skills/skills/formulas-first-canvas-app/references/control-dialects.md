# Control dialects

Two generations of modern controls coexist in Canvas Apps. Both are valid. They are
**different controls**, not a versioning mistake, and they take different property
names and different enum namespaces.

## The operative rule

> **Determine the dialect from the target app's existing YAML, never from the docs
> alone, and keep the whole tree internally consistent.**

A tree that is uniformly one dialect can be converted by one mechanical rename sweep.
A mixed tree cannot — each site has to be read individually to know which vocabulary
applies.

## The trap: `Align` splits by control family, not by generation

| Control | `Align` namespace | Members |
|---|---|---|
| `ModernText` | `'TextCanvas.Align'` | Start, Center, End |
| `Text` (previous generation) | `'TextCanvas.Align'` | Start, Center, End |
| `ModernTextInput` | `'TextCanvas.Align'` | Start, Center, End |
| `Button` (previous generation) | `Align` | Left, Center, Right |

Both **text** generations share `'TextCanvas.Align'`. Buttons take the plain `Align`
enum. `Center` is the only member the two namespaces share, which is why
`Align.Center` on a `ModernText` compiles while `Align.Right` on the same control
does not — there is no `Right` in `'TextCanvas.Align'`; the member is `End`.

An earlier version of this skill's `SKILL.md` claimed `ModernText` takes `Align.Left`.
That was wrong, and it propagated into `cmp_Header.pa.yaml` and
`templates/design-tokens.pa.yaml` before being caught. Trust
`references/control-contracts.yaml`, which is checked against a compiled app.

## Property vocabularies

### Text

| Concept | `ModernText` | `Text` (previous generation) |
|---|---|---|
| colour | `Color` | `FontColor` |
| size | `Size` | `Size` |
| weight | `FontWeight: =FontWeight.{Bold\|Semibold\|Normal\|Lighter}` | `Weight: ='TextCanvas.Weight'.{Bold\|Regular}` |
| alignment | `Align: ='TextCanvas.Align'.*` | `Align: ='TextCanvas.Align'.*` |
| vertical | — | `VerticalAlign` |

`ModernText` renames: `FontColor`→`Color`, `FontSize`→`Size`, `Weight`→`FontWeight`,
`FontItalic`→`Italic`, `FontUnderline`→`Underline`, `FontStrikethrough`→`Strikethrough`,
`BorderRadius`→`Radius{TopLeft,TopRight,BottomLeft,BottomRight}`. `DisplayMode` is removed.

### Inputs

`ModernTextInput` takes `Placeholder`, **not** `HintText` — `HintText` is the classic
`TextInput`. It has **no `Format` property**; that is also classic. For numeric entry,
keep it a text input, right-align via the token, and parse with `Value()`.
`OnChange` fires **on blur**, not per keystroke.

`ModernCombobox` has **no `Value` property**. `Fields`→`ItemDisplayText`,
`TriggerOutput`→`DelayOutput`. `SelectMultiple` **defaults to true** and must be set
`false` explicitly for single-select. `InputTextPlaceholder`'s factory default is the
literal string `"Find items"` — seeing that in a running app means nobody set it.

### Buttons

The eight bundled components use the previous-generation `Button`:
`'ButtonCanvas.Appearance'`, `'ButtonCanvas.Layout'`, `'ButtonCanvas.IconStyle'`,
`FontColor`, `BorderRadius`, and the plain `Align` enum. It has **no `Color`** and
**no `Fill`**. The updated generation is a different control, `ModernButton@1.0.0`,
taking `Color`, `Size`, `Radius*`, `ButtonAppearance.*`, `ButtonLayout.*`, `Tooltip`.

### Gallery

`Gallery` is a **leaf control**: inside an auto-layout container it defaults to
`FillPortions: =0` and collapses to the ~200px control default. It always needs an
explicit `FillPortions: =1` or an explicit `Height`. It has **no `ShowScrollbar`** —
that is classic-only.

## Design tokens carrying enum values

A single token field cannot serve both dialects. Tokens holding alignment carry
explicit per-dialect fields:

```
NumberInput: {
    AlignModern: 'TextCanvas.Align'.End,
    AlignLegacy: Align.Right,
    ...
}
```

`scripts/check_control_props.py` resolves the token reference and checks the resolved
value against the consuming control's namespace, so consuming the wrong field is
caught.
