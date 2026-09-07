# Live-compile fix report — 2026-09-07

First real `compile_canvas` push of this generator's output returned 59 errors
against a live environment, all attributable to exactly two root causes. Both
fixed, both guarded against regression.

## Root cause 1 — `TabIndex` is not a valid property (52/59 errors)

`TabIndex` was seeded into `references/control-contracts.yaml` from a
documentation source and never corpus-verified against the compiled reference
app — it appears zero times there. The live compiler confirmed it is unknown
on `ModernTextInput`, `ModernCombobox`, `ModernDatePicker`, and `Button`.

**Checked for a legitimate custom-property escape hatch first** — inspected
every `components/cmp_*.pa.yaml`'s `CustomProperties:` block. None declares
`TabIndex` as its own input; every hit was a plain control-property
assignment (`TabIndex: =0`). No exception found — all removed.

Fixed:
- `references/control-contracts.yaml`: removed `TabIndex` from the
  `properties` list of all 8 controls that carried it (ModernText, Text,
  ModernTextInput, ModernCombobox, ModernDatePicker, Button,
  ModernButton@1.0.0, Gallery) and curated it as a hard-error `absent` entry
  on each, so a reintroduction fails the guard instead of only warning. Added
  a dated provenance comment recording the live-compile evidence.
- `scripts/emit_screens.py`: removed all 11 `("TabIndex", "=0")` emissions.
- 12 hand-authored files (`components/cmp_Notification.pa.yaml`,
  `cmp_Dialog.pa.yaml`, `cmp_FilterButton.pa.yaml`, `cmp_Navigation.pa.yaml`,
  `cmp_FieldText.pa.yaml`, `cmp_FieldDate.pa.yaml`, `cmp_FieldNumber.pa.yaml`,
  `cmp_FieldChoice.pa.yaml`, `cmp_CommandBar.pa.yaml`, `cmp_Header.pa.yaml`,
  `templates/FormScreen.pa.yaml`, `templates/ListScreen.pa.yaml`): removed
  every `TabIndex: =0` line (28 lines total). No substitute property added —
  tab order reverts to document order.
- `scripts/check_control_props.py`'s `UNIVERSAL_INSTANCE_PROPS` (the
  fallback allowlist for properties every `CanvasComponent` instance carries
  regardless of its own declared inputs) also carried `TabIndex` on the same
  unverified basis. Removed it there too, with a comment explaining why —
  leaving it would have silently waved the same invalid property through on
  a component instance instead of catching it.
- `references/design-system.md` and `references/component-library.md`:
  corrected prose that had recommended `TabIndex` as deliberate practice.

Remaining `TabIndex` hits after the fix (verified via
`grep -rn "TabIndex" templates/ components/ scripts/ references/`): only
provenance comments, the curated `absent: [...]` entries in
`control-contracts.yaml`, and corrected prose explaining the removal. None is
a control-property assignment. `tests/test_control_props_direct.py` still
uses the literal string `TabIndex` once as an arbitrary property name in a
low-level parser test (`iter_properties`, not contract validity) — untouched,
since it doesn't assert `TabIndex` is a valid property.

## Root cause 2 — control names must be globally unique (7/59 errors)

Power Apps control names are unique across the **whole app**, not scoped to
their own screen or component — a real constraint no guard in this repo knew
about. All four field components (`cmp_FieldText`, `cmp_FieldChoice`,
`cmp_FieldDate`, `cmp_FieldNumber`) declared the same inner names (`con_Field`,
`lbl_Field_Label`, and `txt_Field_Input` shared by Text and Number).

Fixed: renamed each component's inner controls to be unique, consistent with
the task's suggested pattern:

| Component | Container | Label | Input |
|---|---|---|---|
| cmp_FieldText | `con_FieldText` | `lbl_FieldText_Label` | `txt_FieldText_Input` |
| cmp_FieldChoice | `con_FieldChoice` | `lbl_FieldChoice_Label` | `com_FieldChoice_Input` |
| cmp_FieldDate | `con_FieldDate` | `lbl_FieldDate_Label` | `dp_FieldDate_Input` |
| cmp_FieldNumber | `con_FieldNumber` | `lbl_FieldNumber_Label` | `txt_FieldNumber_Input` |

All internal references (formulas, `Output:` bindings, doc comments) were
updated to match.

**Checked the rest of the tree** by walking every `*.pa.yaml` file's control
declarations (the same `RE_ITEM` pattern `iter_properties` already uses) and
diffing names across files:

- `scripts/emit_screens.py`'s generated screens are safe by construction —
  every screen-level control name is entity-derived (`"con_%sList_Main" %
  entity.plural`, etc.), confirmed by generating two apps and scanning their
  full output for duplicates (zero found in both).
- One other cross-file name match exists in the tree:
  `templates/frame-headermainfooter.pa.yaml` and
  `templates/frame-headerrailmain.pa.yaml` both declare `con_Frame_Header`
  and `con_Frame_Main`. **Not a real collision** — these are mutually
  exclusive reference layouts; `scripts/new_app.py`'s `write_frame` copies
  exactly one of them into any given generated app as `Frame.pa.yaml`, so
  they never coexist in one app's tree.
- No same-file duplicate declarations exist anywhere in `components/` or
  `templates/`.

## New guard: duplicate control names

Added `find_duplicate_controls()` to `scripts/check_control_props.py`,
wired into `main()`. It walks every file under `--src` (reusing `RE_ITEM`,
the same declaration-line pattern `iter_properties` already relies on),
tracks the first declaration site of every control name, and emits a hard
error naming both definition sites — matching the compiler's own wording —
on any second declaration anywhere in the app (same file or a different one).

Deliberately scoped to `--src` only (one generated app's tree), not the
skill's own `templates/` library as a whole, because the two frame templates
are legitimate alternatives that are never both part of one app.

Tests added to `tests/test_defect_regression.py`
(`TestDuplicateControlNamesAcrossFiles`, 6 tests): a genuine cross-file
duplicate fails; a genuine same-file duplicate fails; a synthetic
reproduction of the exact pre-fix four-field-component collision fails with
one error per redeclaration; a control name appearing only as a **formula
reference** (`=con_Header.Height`) in another file is correctly NOT flagged
(RE_ITEM only matches declaration lines, never a formula value); the two
alternative frame templates each pass on their own (real usage); and the
shipped, renamed field components have zero cross-file collisions.

Also added `test_tabindex_is_absent_everywhere_live_compile_2026_09_07` to
`tests/test_contracts_wellformed.py` guarding the TabIndex fix.

## Playbook

`references/compile-error-playbook.md`: added a **LIVE (2026-09-07)** row to
the renamed-property table for the exact `TabIndex` error text, and a new
"Duplicate control names" section with the exact `An entity with name ...
already exists` error text — both marked with the real transcript wording
and dated, upgrading the file's sourcing legend to include a `LIVE` tier
above `EXACT`/`PATTERN`.

## Verification

1. `grep -rn "TabIndex" templates/ components/ scripts/ references/` — every
   hit is a comment, curated `absent:` entry, or corrected prose; zero
   control-property assignments remain.
2. `python3 -m unittest discover -s tests` — **233 tests, all green** (226
   baseline + 7 new: 6 duplicate-control-name tests, 1 TabIndex-contract
   test).
3. `python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/live2`
   — exit 0, all 6 local guards PASS.
4. `python3 scripts/new_app.py --name "Legacy" --brand "#300091" --out /tmp/live3`
   — exit 0, all 6 local guards PASS.
5. Confirmed zero `TabIndex` and zero duplicate control names in both
   generated trees (`find_duplicate_controls()` run directly against each
   output, and `check_control_props.py --src` run directly against each —
   both PASS).

No guard was weakened. Two were strengthened: `TabIndex` moved from
"unverified" (warning-only) to a curated `absent` hard error on 8 controls,
and a brand-new cross-file duplicate-control-name check was added where none
existed before.

# Second live compile run — 2026-09-07

After both root causes above were fixed, a second `compile_canvas` push of
the same generator's output (233 tests, all six local guards green) returned
34 errors and 2 warnings against a live environment, attributable to exactly
four root causes. All four fixed; one is guardable statically and is now
guarded, one is an intentionally un-guardable class (documented as such,
not worked around), and two are component-authoring defects fixed at the
source.

## Root cause A — Void UDFs must be behavior UDFs with braces (16/34 errors)

`templates/App.pa.yaml`'s `funcStartLoading` and `funcStopLoading` were
declared as one-line bare-expression bodies:

```
funcStartLoading(): Void = Set(glBoolIsLoading, true);
funcStopLoading(): Void = Set(glBoolIsLoading, false);
```

A `Void`-returning UDF is only valid as a **behavior** UDF, and a behavior
UDF requires the body wrapped in `{ }` — even for one statement. Every other
`Void` UDF in the same file (`funcLoadItems`, `funcSaveItem`, `funcNotify`,
`funcNotifySuccess`, `funcNotifyError`, `funcAddBack`, `funcGoBack`,
`funcDeleteItem`) already used the brace form and compiled fine; only this
one hand-authored pair, present since Phase 1, lacked it. The declaration
failure cascaded into 14 "unknown function" errors at every call site
across `App.OnStart` and every screen/component that calls either function.

Fixed: wrapped both bodies in braces.

```
funcStartLoading(): Void =
{
    Set(glBoolIsLoading, true);
};
funcStopLoading(): Void =
{
    Set(glBoolIsLoading, false);
};
```

**Swept the whole tree for the same pattern.** Checked every `: Void =`
declaration in `templates/`, `components/`, `scripts/emit_formulas.py`'s
generated text, and the test fixtures: `templates/App.pa.yaml` lines 61–62
were the *only* two missing braces anywhere. `emit_formulas.py`'s three
`Void`-UDF templates (load/save/delete) already emit the brace form.

## Root cause B — every ModernCombobox must set ItemDisplayText (11/34 errors)

`scripts/emit_screens.py` emitted no `ItemDisplayText` property at all on
any generated `ModernCombobox` — grepping the generated tree confirmed the
property appeared nowhere. Left unset, the control's own factory default
apparently references a `Value1` column that does not exist on this app's
choices tables, so the control's *default* failed to resolve on all 11
comboboxes across both screens and both entities. The reference app
(`/Users/krystofpe/powerapps-work/canvas-src`) sets `ItemDisplayText:
=ThisItem.Value` explicitly on every combobox it has.

Fixed — added `ItemDisplayText: =ThisItem.Value` to:
- `scripts/emit_screens.py`: all three `ModernCombobox` emission sites (the
  list-toolbar filter combobox, the boolean Yes/No form field, and the
  choice-field form input).
- `templates/FormScreen.pa.yaml` and `templates/ListScreen.pa.yaml`: the
  hand-authored equivalents had the identical omission.
- `components/cmp_FieldChoice.pa.yaml`: same omission on its inner
  `com_FieldChoice_Input` combobox.

**This is a defect class no static guard in this repo can catch.** An
omitted property is not a wrong value `check_control_props.py` can compare
against `control-contracts.yaml` — the property simply never appears in the
emitted text for the guard to check. Catching this class statically would
need a list of mandatory properties per control (which properties MUST be
present, not just which ARE valid if present) — a materially bigger design
question than this fix, and not authorized as part of this task. No guard
was added for this root cause; `references/compile-error-playbook.md`'s new
"Omitted-property errors" section says so explicitly.

## Root cause C — undeclared DisplayMode input on four field components (4/34 errors)

`components/cmp_FieldText.pa.yaml`, `cmp_FieldChoice.pa.yaml`,
`cmp_FieldDate.pa.yaml`, and `cmp_FieldNumber.pa.yaml` each wrote
`DisplayMode: =cmp_FieldX.DisplayMode` on their inner input control, but
none of the four declared `DisplayMode` as a `CustomProperties` input on the
component itself — an unresolved reference on all four.

Checked the reference app for how it types a caller-controlled display-mode
input before deciding whether to declare it or drop it, per the task's
instruction. Every `DisplayMode` usage in the reference corpus
(`Activities.pa.yaml`, `Activity Form.pa.yaml`,
`Components/cmp_Filter.pa.yaml`, `cmp_FilterButton.pa.yaml`,
`cmp_Header.pa.yaml`) is an inline `If(glX, DisplayMode.Edit,
DisplayMode.View)` expression assigned directly to a control's own
`DisplayMode` property — no component anywhere in that app, or in this
skill's own components, declares `DisplayMode` (or any enum-flavored value)
as a `CustomProperties` `DataType`. The only `DataType`s used for custom
properties across both corpora are `Text`, `Number`, `Boolean`,
`DateAndTime`, `Color`, `Table`, `Record`, `Screen` — no enum type exists to
type it correctly. With no corpus precedent, dropped the `DisplayMode:` line
from all four components rather than inventing a `DataType` no evidence
supports. A caller who genuinely needs one of these fields read-only can
still set `DisplayMode` on the component *instance* at the call site, the
same way the reference app gates its own controls.

## Root cause D — cmp_FieldChoice's combobox has no schema (3/34 errors)

`cmp_FieldChoice`'s `Choices` custom property (a `Table`-typed input) had a
blank `Default: =`. With no default row, the `ModernCombobox` built from
`Items: =cmp_FieldChoice.Choices` has no column schema, so `Output`
(`=com_FieldChoice_Input.Selected.Value`) and `DefaultSelectedItems`'s
`Value = …` filter cannot resolve a `Value` column — the third error
(`Incompatible types for comparison: Error, Text`) is the same unresolved
column cascading into a comparison against an `Error` value.

Checked `cmp_FilterButton`'s identical-looking blank `Choices`/`Items`
defaults first — those match the reference app exactly and are fine,
because that component never resolves `Choices` into a typed output. The
difference is in consumption, not a blanket rule against blank `Table`
defaults, so only `cmp_FieldChoice` needed a fix.

Fixed: gave `Choices` a typed default with the right column —
`Default: =Table({Value: ""})`, wrapped in the file's usual `|-` block
scalar form since the value contains a colon (`Value: ""`). Verified this
affects only the standalone `cmp_FieldChoice` component; the generated
screens build their own typed `constXChoices` tables directly wherever a
choice field appears and were never affected.

## Expected warnings — left as is

Both warnings in this run:

```
warning: [App, Formulas] This predicate is a literal value and does not reference the input table.
```

are the `Filter(colX, true)` scope-formula placeholder (Ruling 6) — the
generic model has no scope concept yet, so the predicate is a literal `true`
until a real per-entity scope condition exists. Confirmed a **warning**, not
an error; the push still succeeds. Left the code exactly as written, and
recorded the reasoning in the playbook so a future run does not "fix" it.

## New guard: Void UDF without a brace body

Root cause A is statically detectable, so it is now guarded.
`scripts/check_references.py` already parses every `App.Formulas`
declaration for its forward-reference check, so the new check rides the
same pass rather than a second parser:

- `VOID_UDF_PATTERN`: matches `func*(params): Void = <first-non-whitespace-char>`.
- `find_braceless_void_udfs(block)`: returns every `func*` name whose
  captured first character is not `{` — i.e. a `Void` UDF whose body is a
  bare expression instead of a behavior UDF's `{ ... }` block.
- Wired into `main()`: a non-empty result is a hard `FAIL`, printed with the
  exact remedy (`funcX(): Void = { <statement>; };`) and the explanation
  that the declaration failure is what makes every call site look broken,
  matching this file's existing convention for the forward-reference and
  duplicate-component checks.

Tests added in `tests/test_check_references_void_udf.py` (8 tests, both
directions): a single-line bare-expression body is caught; a multi-line
bare-expression body (the `=` and body's first token on different lines) is
also caught, so the check isn't fooled by a line break; a non-`Void` UDF is
never flagged; single-line, multi-line, and multi-parameter brace bodies all
pass; the real fixed `templates/App.pa.yaml` has zero braceless `Void` UDFs;
and `check_references.py` run as a subprocess against a freshly generated
`--name`-only scaffold exits 0.

No guard was added for root causes B, C, or D: B is the documented
un-guardable class above; C and D are component-authoring defects in
hand-written `.pa.yaml`, not systematic generator output the way A's pattern
could recur across any future `Void` UDF anyone adds to a template.

## Playbook

`references/compile-error-playbook.md`: updated the sourcing intro to
mention the second run's 34 errors and four root causes; added a new row to
the "User-defined function declaration limits" table for root cause A's
exact error text; added three new sections — "Omitted-property errors (a
defect class no static guard can catch)" for root cause B, "Undeclared
component custom-property references" for root cause C, and "Component
input with no typed schema (Table-typed custom property, blank default)"
for root cause D; and a new "Expected warnings (not errors — leave the code
as is)" section for the two literal-predicate warnings. All five entries are
marked `LIVE (2026-09-07, second run)` with the exact error/warning text
quoted verbatim from the task's transcript.

## Verification

1. `python3 -m unittest discover -s tests` — **241 tests, all green** (233
   baseline + 8 new, all in `test_check_references_void_udf.py`).
2. `python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/live4`
   — exit 0, all 6 local guards PASS.
3. `python3 scripts/new_app.py --name "Legacy" --brand "#300091" --out /tmp/live5`
   — exit 0, all 6 local guards PASS.
4. Grepped both generated trees: every `ModernCombobox` block has exactly
   one `ItemDisplayText` (counts matched control-for-control in every
   screen and in `cmp_FieldChoice.pa.yaml`); every `: Void =` declaration in
   both `App.pa.yaml`s is immediately followed by a `{` on the next line;
   zero `cmp_Field*.DisplayMode` references remain anywhere in either tree;
   `check_references.py` run directly against both trees reports PASS with
   no `Void`-UDF failures.

No guard was weakened. One was strengthened — `check_references.py` gained
the brace-body check for `Void` UDFs, backed by 8 new regression tests — and
`references/control-contracts.yaml` was **not** touched: nothing in this
run's evidence required it (root causes A, C, and D are UDF-declaration and
component-authoring defects; root cause B is an omission the contract file
has no mechanism to express, by design, per the task's constraint).
