# Live-compile fix report — 2026-09-07

> **Superseded 2026-09-07:** this report's fourth-run conclusion — `=constScreens` is correct on `cmp_Navigation.Screens`, and the `Navigation.Screens` errors were a cascade from `cmp_FilterButton` — did not hold on a cold coauthoring session.
> See the fifth-run correction in `plugins/acoe-skills/skills/formulas-first-canvas-app/references/compile-error-playbook.md` (written by Phase 3 Task 8) for what actually fixed it.

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

# Third live compile fix (2026-09-07, third run — first with a genuine coauthoring session)

## Reframing: sessionless validation is not trustworthy

The first two live runs both warned "No active coauthoring canvas designer
session detected. Validation results may be inaccurate." Both were still
treated as usable, and both found real defects (first run: 59 errors, two
root causes; second run: 34 errors, four root causes). That created a false
sense that the warning was cosmetic.

This third round pushed the *identical* tree twice: once with no active
session (0 errors reported) and immediately after with a live coauthoring
session open in Power Apps Studio (7 errors, all real, on defects that had
been sitting in the tree unchanged). A clean sessionless result is therefore
**not evidence of anything** — it can silently pass code a live session
hard-fails. Documented prominently at the top of
`references/compile-error-playbook.md` and folded into `SKILL.md`'s push/
validate-loop sections as a precondition, not a footnote.

## The 7 errors, one root cause

```
error: [Control 'cmp_AssetsList_HeadCategory', Property 'Choices'] The table passed in has none of
the expected columns: SampleBooleanField, SampleNumberField, SampleStringField.
error: [Control 'cmp_AssetsList_Navigation', Property 'Screens'] (same)
```

5 errors on `cmp_*_Head*.Choices` (all `cmp_FilterButton` instances), 2 on
`cmp_*_Navigation.Screens` (`cmp_Navigation` instances). Same defect class
already fixed once this project (`cmp_FieldChoice.Choices`, second run): a
`DataType: Table` component input whose `Default` does not establish a
concrete schema falls back to the Studio's placeholder schema
(`SampleBooleanField`/`SampleNumberField`/`SampleStringField`); a caller
passing a real table with different columns then fails to type-match it.

Two distinct bad shapes, both now confirmed live:

- **Blank** (`Default: =`, nothing after the `=`) — `cmp_FilterButton.Choices`.
- **Bare app-scope name reference** (`Default: =constScreens`) —
  `cmp_Navigation.Screens`. Not resolvable at component-declaration time,
  unlike a blank default this is a NEW bad shape not previously documented.

### Fixes

`components/cmp_FilterButton.pa.yaml`, `Choices`:

```yaml
Default: |-
  =Table({Value: ""})
```

`components/cmp_Navigation.pa.yaml`, `Screens`:

```yaml
Default: |-
  =Table(
      {
          Screen: App.ActiveScreen,
          DisplayName: "",
          Icon: "",
          Entity: "",
          Type: "",
          Group: "",
          BackLabel: ""
      }
  )
```

The awkward column was `Screen` — a screen reference, not text. Confirmed
(via `scripts/emit_formulas.py`) that `enumScreenType`/`enumEntity` are
named-formula **records of string literals** (`{List: "list", Form: "form"}`),
not real Power Fx enum/optionset types, so `Entity`/`Type`/`Group`/
`BackLabel`/`DisplayName`/`Icon` are all plain `Text` at runtime — blank
string literals type-match them. Only `Screen` needed a real screen-typed
placeholder; used `App.ActiveScreen` per the task's suggestion (always
available at runtime, carries no app-specific meaning, and this component
library is generic across apps so it cannot reference a fixed screen name
like `ListScreen`). **Not independently re-verified against a live
`compile_canvas` push** — the task author holds the only live session and
will re-push after this report. Flag if the next push disagrees.

### Sweep of every `DataType: Table` custom property in `components/`

| Component.Property | Default before | Action |
|---|---|---|
| `cmp_FieldChoice.Choices` | `=Table({Value: ""})` | Already typed (prior round) — comment corrected (see below), no functional change |
| `cmp_FilterButton.Choices` | `=` (blank) | **Fixed** — `=Table({Value: ""})` |
| `cmp_FilterButton.Items` | `=` (blank) | **Fixed pre-emptively** — `=Table({Value: ""})`. Same blank-default defect, same `Value` output record (`Items: Self.Items`) as `Choices`; no template currently sets `Items` on a real instance so it has not yet errored live, but the next caller to set it would hit the identical failure. |
| `cmp_Navigation.Screens` | `=constScreens` (bare reference) | **Fixed** — inline typed `Table(...)` literal, see above |
| `cmp_Notification.Notifications` | `=[ {Title: "Title", …} ]` (typed bracket literal) | Already typed — no change |

No other `DataType: Table` custom properties exist in `components/` (checked
all 12 shipped `cmp_*.pa.yaml` files with a script scan for `DataType:
Table` under `CustomProperties`).

### Correction to a prior claim

`cmp_FieldChoice.pa.yaml`'s `Choices` comment (written during the second-run
fix) asserted that `cmp_FilterButton`'s blank `Table` default was "fine"
because that component's `Choices` is "never resolved into an output." That
claim was wrong — `Self.Choices` (and `Self.Items`) flow directly into
`cmp_FilterButton`'s own `Value` output record — and this round's 5 errors
prove it. The comment is corrected in place; the matching stale claim in
`references/compile-error-playbook.md`'s existing `cmp_FieldChoice` row is
struck through and annotated rather than silently rewritten, so the
correction itself stays visible history rather than looking like it was
always right.

## Guard added

`scripts/check_control_props.py` gained `find_bad_table_defaults()` (plus
its own parser, `parse_component_table_defaults()`, extending the
`ComponentDefinitions` walk `parse_component_defs_text()` already does to
additionally capture each property's `PropertyKind` and `Default`). It flags
exactly the two proven-bad shapes on any Input property typed `DataType:
Table`:

- blank (`Default: =` or empty after stripping the leading `=`), and
- a bare identifier/dotted-name reference (`=constScreens`, `=App.Foo`) —
  not a literal `Table(...)`/`[...]` construction.

Anything else (any literal `Table(...)` or `[...]` construction, regardless
of row count or column shape) passes unchecked — this guard does not
type-check columns, only whether the Default is a literal at all, matching
`check_control_props.py`'s existing "absence is not evidence of validity"
stance. Wired into `main()` alongside the existing per-file checks, so it
runs automatically under every `check_control_props.py --src <tree>`
invocation, including the six-guard sweep `new_app.py` runs on its own
output (which copies `components/*.pa.yaml` into every generated
`Components/` directory).

Tests: `tests/test_table_default_guard.py`, 11 new tests — both directions
(blank and bare-reference are caught; single-line, block-scalar, bracket,
and multi-row literal defaults all pass), non-Table and non-Input properties
are never checked, and a standing assertion that every shipped
`components/cmp_*.pa.yaml` passes the guard clean (the regression proof that
this round's fixes stuck).

## Playbook and SKILL.md

`references/compile-error-playbook.md`:
- New section at the very top: sessionless `compile_canvas` results are not
  trustworthy, with the concrete 0-errors-vs-7-errors evidence.
- "How precisely each row is sourced" now describes the third run and its
  single root cause.
- "Component input with no typed schema" section: added two new rows for
  this run's exact error text (`cmp_FilterButton.Choices` /
  `cmp_Navigation.Screens`), both marked `LIVE (2026-09-07, third run)`; the
  existing second-run `cmp_FieldChoice` row has its now-false claim about
  `cmp_FilterButton` struck through and corrected in place; and a closing
  note documents the new static guard and what it can/cannot catch.

`SKILL.md`: the "no local path to an importable `.msapp`" paragraph and the
"verification loop" section both now state the coauthoring-session
precondition explicitly — an app open in Power Apps Studio with coauthoring
enabled, not just a successful `connect()` — and that a sessionless clean
result must not be believed, with the same concrete evidence. The previously
stale "the generator's own output has not yet been validated" line (already
false after the first two rounds) was also corrected while in the area.

## Verification

1. `python3 -m unittest discover -s tests` — **252 tests, all green** (241
   baseline + 11 new, all in `test_table_default_guard.py`).
2. `python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/live6`
   — exit 0, all 6 local guards PASS.
3. `python3 scripts/new_app.py --name "Legacy" --brand "#300091" --out /tmp/live7`
   — exit 0, all 6 local guards PASS.
4. Manually ran the new `find_bad_table_defaults()` against every shipped
   `components/cmp_*.pa.yaml`: 0 findings after the fixes (confirmed 2 before,
   on `cmp_FilterButton.Choices`/`.Items` and `cmp_Navigation.Screens`
   respectively — 3 total flagged pre-fix across the two files).

No guard was weakened. One was strengthened — `check_control_props.py`
gained `find_bad_table_defaults()`, backed by 11 new regression tests — and
`references/control-contracts.yaml` was **not** touched: nothing in this
run's evidence concerned control property names/contracts, only component
custom-property defaults, which that file does not model.

**Unverified**: the two fixes above have not been re-pushed against a live
`compile_canvas` session by this agent — the task author holds the only live
coauthoring session and will re-push after reading this report. The
`cmp_Navigation.Screens` fix in particular rests on reasoning
(`enumScreenType`/`enumEntity` being plain string-valued records, not real
enum types, verified by reading `scripts/emit_formulas.py`'s generation
code) rather than a live compile confirming it — flagged explicitly per the
task's instruction to report exactly what was tried rather than assume it
works.

---

# Fourth run — 2026-09-07: revert a validator crash, correct a wrong diagnosis, close the loop with app-checker

The live-compile loop had closed: the generated app validated with zero
errors and landed in a real environment (19 files, 34 mock rows, both
entities). Then a follow-up push of an **unverified** change — replacing
`cmp_Navigation.Screens`'s `Default: =constScreens` with a literal
`Table({Screen: App.ActiveScreen, …})` — came back:

```
✗ Validation FAILED with no diagnostics — the server likely hit an
unhandled exception.
```

The task author bisected it: reverting only that one line back to
`=constScreens` (keeping every `cmp_FilterButton` fix from the third round)
produced **zero errors** on the same tree.

## Root cause — `App.ActiveScreen` inside a component custom-property `Default` crashes the validator

A component custom-property `Default` is evaluated in isolated component
scope. `App.ActiveScreen` — any app-scope reference — used inside that
default is not an ordinary type error; it crashes the validator outright
with **no attributable diagnostic**, which is why the second push named no
file or control at all. This is a strictly worse failure mode than the
"table passed in has none of the expected columns" errors elsewhere in this
skill's playbook: those at least point at a control.

## The third run's diagnosis was wrong, and is corrected in place

The third run had claimed `cmp_Navigation.Screens`'s bare `=constScreens`
default was independently bad — "not resolvable at component-declaration
time" — alongside `cmp_FilterButton.Choices`'s genuinely-blank default,
and "fixed" it with the literal that went on to crash the validator this
round. The fourth run's bisection disproves that claim directly: reverting
*only* `cmp_Navigation.Screens` while keeping `cmp_FilterButton`'s fix
produced zero errors, meaning the third run's 2 `cmp_*_Navigation.Screens`
errors were a **cascade** from `cmp_FilterButton.Choices`'s blank default in
that same push, not an independent defect of the bare-reference shape.
`references/compile-error-playbook.md`'s third-run row for this error is
corrected in place (struck through, not silently rewritten) rather than
left standing with a cause now known to be false.

## Fix

`components/cmp_Navigation.pa.yaml`, `Screens`:

```yaml
Default: =constScreens
```

reverted from the crashing literal, with the explanatory comment rewritten
to record: `=constScreens` is correct and proven live; the earlier errors
attributed to it were a cascade from `cmp_FilterButton`; and a literal
containing `App.ActiveScreen` crashes the validator with no diagnostic — do
not "fix" this again the same way.

`cmp_FilterButton`'s `Choices`/`Items` fixes (typed `Table({Value: ""})`
literal defaults) are untouched — those are proven correct and were never
in question.

## Guard correction — `find_bad_table_defaults()` no longer flags a bare app-scope reference

The guard added in the third round flagged two shapes as bad: a blank
`Default: =`, and a bare name/dotted reference (`=constScreens`,
`=App.Foo`). The second shape is now proven **correct** by the live
compiler, so a guard that still flagged it would reject the exact thing the
compiler accepts — contradicting live evidence is worse than having no
guard at all.

`scripts/check_control_props.py`'s `_table_default_is_bad()` is narrowed to
flag only a genuinely blank Default (nothing after stripping a leading `=`)
— the one shape that actually caused live errors (`cmp_FieldChoice.Choices`
before its fix, `cmp_FilterButton.Choices`/`.Items`). The now-dead
`RE_BARE_REFERENCE` regex was removed along with the check that used it.

`tests/test_table_default_guard.py` updated to match: the two former
"is an error" tests for bare references (`test_bare_app_scope_name_
reference_is_an_error`, `test_dotted_bare_reference_is_also_an_error`) are
now `TestBareReferencesAreNotFlagged`, asserting the guard does **not** flag
`=constScreens` or `=App.SomeGlobal`. The blank-default test and the
standing "every shipped component passes the guard" regression test are
unchanged in intent (still pass, now against the reverted
`cmp_Navigation.Screens`).

No other guard was touched or weakened.

## Playbook and SKILL.md

`references/compile-error-playbook.md`:
- New top section, "A no-diagnostic crash means malformed input, not '0
  errors'": the exact crash text, its cause (app-scope reference inside a
  component custom-property `Default`), the remedy, and the bisection
  method for a no-diagnostic failure.
- The third-run `cmp_Navigation.Screens` row is corrected in place (struck
  through original claim, annotated with the real cascade cause and a
  pointer to the fourth-run correction) rather than deleted.
- The paragraph under that table describing what `find_bad_table_defaults()`
  catches is updated to say "blank only," matching the guard change.
- New section, "The verification loop has three stages, not two": documents
  `get_appchecker_errors` as a required third stage after a clean
  `compile_canvas`, plus the three app-checker findings from this run's live
  app (`App.glScopeFilter`, `AssetFormScreen.locConfirmDelete`,
  `SiteFormScreen.locConfirmDelete`) and the decision/finding for each (see
  below).

`SKILL.md`: the verification-loop diagram now ends in `get_appchecker_errors`
after `compile_canvas`, with a short paragraph stating a clean compile is not
the end of the loop and pointing at the playbook's worked example.

## App-checker findings (`get_appchecker_errors`, zero errors, 3 Medium/Performance)

```
App.glScopeFilter: Unused variable
AssetFormScreen.locConfirmDelete: Unused variable
SiteFormScreen.locConfirmDelete: Unused variable
```

**`App.glScopeFilter`** — expected, and a direct consequence of Ruling 6:
the generated per-entity scope formula (`scripts/emit_formulas.py`,
`_scope_spec`) is a literal `Filter(col, true)` because the model has no
scope concept yet — the same deliberate wart already documented as an
"expected warning" (`warning: […] This predicate is a literal value…`).
`templates/App.pa.yaml`'s `OnStart` still unconditionally `Set(glScopeFilter,
"")`s the global (untouched by the `--model` splice), but no generated scope
formula reads it any more, so it is genuinely dead in `--model` output.
**Decision: keep it.** It is the documented seam a real per-entity scope
condition will read the moment the model has one (`Owner = glScopeFilter`
is literally the pattern already used in the hand-written `--name` scaffold
template); removing it now would mean re-adding both the global and its
`OnStart` line later, and would leave the two deliberate warts
inconsistent with each other for no present benefit. Left as an accepted
Medium/Performance finding, not fixed.

**`AssetFormScreen.locConfirmDelete` / `SiteFormScreen.locConfirmDelete`** —
investigated whether the delete-confirmation dialog is actually wired to it,
per the task's instruction to check before deciding. Traced every
read/write site in `scripts/emit_screens.py` (and the matching hand-written
`templates/FormScreen.pa.yaml`):

- `OnVisible` sets `locConfirmDelete: false` (screen load).
- `btn_*Form_Delete`'s `OnSelect` sets it `true` (open the dialog).
- `cmp_*Form_Dialog` (`ComponentName: cmp_Dialog`) binds its own built-in
  `Visible` property — `Visible` is a universal instance property on any
  control/component (`UNIVERSAL_INSTANCE_PROPS` in
  `check_control_props.py`), not something `cmp_Dialog` declares itself —
  to `=locConfirmDelete`. This is what actually shows/hides the dialog.
- `OnCancel` and `OnSubmit` both reset it to `false` (close the dialog).

**Conclusion: this is a false positive, not a functional gap.** The dialog
is fully and correctly wired to the context variable in both directions.
No code change made. Best guess at why the checker still flags it: it may
have a blind spot for a context variable whose only *read* is inside a
child canvas-component instance's built-in property binding, as opposed to
a top-level screen control's — plausible but not independently confirmed
against Microsoft's checker internals. Recorded in the playbook so a future
run does not "fix" a dialog that already works.

## Verification

1. `python3 -m unittest discover -s tests` — **252 tests, all green**
   (unchanged count from the third round: 2 tests renamed/repurposed in
   place, none added or removed).
2. `python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/live8`
   — exit 0, all 6 local guards PASS.
3. `grep -rn "ActiveScreen" components/` — every hit is a runtime usage
   inside a control property expression (`cmp_Navigation`'s `Appearance`/
   `FontColor` `If(...)` comparisons) or inside a comment; none inside a
   `CustomProperties.*.Default`. Confirmed identically in the freshly
   generated `/tmp/live8/Components/cmp_Navigation.pa.yaml`.
4. Reverted default, pasted above: `Default: =constScreens`.

**Unverified**: this fix has not yet been re-pushed against a live
`compile_canvas` session by this agent — the task author holds the only live
session and will re-push to confirm. Per this run's own lesson, treat that
confirmation as required before calling the crash closed, not optional.
