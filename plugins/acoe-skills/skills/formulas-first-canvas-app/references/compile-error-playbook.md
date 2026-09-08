# Compile-error playbook

## A sessionless `compile_canvas` result is not trustworthy — read this first

**"No active coauthoring canvas designer session detected. Validation
results may be inaccurate." means exactly what it says: do not believe a
clean result that came with that warning attached.**

Concrete evidence, 2026-09-07: the identical generated tree was pushed twice.
The first push ran with no active coauthoring session and carried that
warning; it reported **0 errors**. The very next push — same tree, unchanged
— ran against a genuine coauthoring session (the app open in Power Apps
Studio, coauthoring live) and reported **7 errors**, all real, all on
defects that had been sitting in the tree the whole time (see the "Component
input with no typed schema" section below, third-run rows). A sessionless
run is not a weaker signal on the same defects — it can silently pass code
that a live session hard-fails.

Two earlier live runs (also 2026-09-07) *did* have an active session and
found genuine defects both times, so a live-session result — clean or not —
is real evidence. The failure mode is specific: **skip the "app open in
Studio with coauthoring enabled" precondition, and a clean result tells you
nothing.** Before treating any `compile_canvas` PASS as evidence the app
compiles, confirm the session was active. If it was not, the push has not
actually been validated — re-run it with a live session before believing
either a pass or a fail.

**A clean push does not mean the maker can see it yet.** `compile_canvas`
lands in the live coauthoring session, not the saved app — the maker must
**Save (Ctrl+S) in Studio before any refresh or Play**; a refresh without
Save shows a blank/grey app, not the pushed content. `sync_canvas` returning
files back is not evidence the app is visible either — it confirms the
session has them, nothing about what Studio has rendered or saved. Only a
Play-mode screenshot or a confirmed Save counts as evidence.

Keyed by the error text `compile_canvas` (or `get_appchecker_errors`) puts in
front of you, not by the underlying cause — you have the error first, this
table gets you to the cause and the fix without re-deriving either from
scratch. `references/powerfx-limits.md` and `references/control-dialects.md`
have the fuller prose; this file exists so an agent can go
**push → read error → look it up here → fix → repush** without a detour into
either.

## A no-diagnostic crash means malformed input, not "0 errors"

**`Validation FAILED with no diagnostics — the server likely hit an
unhandled exception. This usually indicates malformed input the validator
could not attribute to a file.` is not a pass, and it is not an ordinary
failure either — it means the validator itself broke before it could
attribute any diagnostic to any file.** Treat it as a signal to bisect
recent changes, not to re-read the last error list for a clue: there may be
no diagnostic pointing at the actual cause at all.

LIVE 2026-09-07 (fourth run): this exact text came back after pushing a
change to `cmp_Navigation.Screens`'s `Default` — an unverified fourth-round
draft that replaced the (correct) `=constScreens` reference with a literal
`Table({Screen: App.ActiveScreen, DisplayName: "", …})`. Bisecting by
reverting only that one line back to `=constScreens` (keeping every other
change from that round, including the `cmp_FilterButton` fixes) produced
**zero errors** on the very same tree.

- **Cause**: `App.ActiveScreen` — or any app-scope reference — used inside a
  component custom-property `Default`. A component's property default is
  evaluated in **isolated component scope**; app scope is not merely
  unavailable there in the ordinary "unknown name" sense, reaching into it
  crashes the validator outright with no attributable diagnostic. This is a
  different, worse failure mode than the ordinary "table passed in has none
  of the expected columns" schema-mismatch errors elsewhere in this file —
  those at least name a control and property. This does not.
- **Remedy**: never reference app scope (`App.*`, a named formula/global
  declared at app level, etc.) inside a `CustomProperties.*.Default` in a
  component definition. If a property genuinely needs an app-scope-typed
  placeholder value, accept it as an instance-level override at the call
  site instead of trying to default it inside the component. A bare
  reference to another **named formula** in the SAME scope (e.g.
  `cmp_Navigation.Screens`'s `Default: =constScreens`, where `constScreens`
  is itself an app-level named formula the component is allowed to read
  because the property is later populated from app scope by its caller) is
  a different, proven-safe shape — see the corrected third-run entry above.
  The crash is specifically about a literal expression that itself REACHES
  into app scope from inside the default (`App.ActiveScreen` nested in a
  `Table({...})` literal), not about naming an app-scope identifier at all.
- **Diagnosis method**: when a push comes back with no diagnostics at all,
  do not trust the most recent error list to still be relevant — it may not
  exist this time. Bisect: revert the most recently changed file(s) one at a
  time (or in small groups) and re-push until the crash disappears. The
  reverted change is the cause, even if you cannot articulate why from the
  (absent) error text alone.
- **CORRECTED 2026-09-07 (fifth run)**: the Remedy above calls a bare
  `cmp_Navigation.Screens` reference to another named formula (`Default:
  =constScreens`) "a different, proven-safe shape" — a cold coauthoring
  session disproved that as a general claim. Retested on its own, with no
  `cmp_FilterButton` blank default left in the same push to blame:
  `Default: =constScreens` → **2 errors** ("the table passed in has none of
  the expected columns" on every `cmp_*_Navigation` instance — the same
  shape the third run saw, not a cascade); `Table({…})` with no `Screen`
  column → **10 errors**; `Table({Screen: App.ActiveScreen, …})` → the
  crash this entry documents (unchanged finding); `Table({Screen: <a real
  screen the app defines>, DisplayName: "", Icon: "", Entity: "", Type: "",
  Group: "", BackLabel: ""})` → **0 errors**. The safe remedy is that last
  shape — a typed literal naming a REAL screen, never `App.ActiveScreen` —
  baked in by the generator so a `--model` build's copy always names its
  own real first screen (`scripts/new_app.py`, Ruling 18, Phase 3 Task 8).
  `components/cmp_Navigation.pa.yaml` ships exactly this shape now.

## How precisely each row is sourced

There is no offline compile for Canvas Apps. This generator's own output was
first pushed through a live `compile_canvas` session on 2026-09-07 — a
two-entity app that passed all six static guards and 226 tests came back with
59 errors, all attributable to exactly two root causes (see the two **LIVE
2026-09-07** entries below). After both were fixed, a **second** live push
against the same app (233 tests, guards still green) came back with 34
errors and two warnings, attributable to four further root causes — see the
**LIVE 2026-09-07 (second run)** entries below. Both of those pushes had an
active coauthoring session and are trustworthy on their own terms. A
**third** push of the same tree, this time run twice — once **without** an
active session (0 errors reported) and immediately after **with** one (7
errors, same tree, unchanged) — is what proved a sessionless result cannot
be believed at all (see the note at the top of this file); its 7 errors are
the **LIVE 2026-09-07 (third run)** entries below, all one root cause. So the
rows below split into three kinds, marked in the **Sourcing** column:

- **LIVE (date)** — the quoted text is reproduced verbatim from an actual
  `compile_canvas` transcript against a real pushed app, on the date given.
  The highest-confidence sourcing this file can carry.
- **EXACT** — the quoted text is reproduced from `references/powerfx-limits.md`,
  which states it was "confirmed against the strict Power Fx engine in the
  Canvas Authoring coauthoring service." Match on it directly.
- **PATTERN / not yet captured live** — no session log in this repo has the
  literal string. The row describes the *shape* of what you will see (which
  control, which property, which class of message), sourced from
  `references/control-dialects.md`'s documented renames or from this
  project's guard tests, not from a captured compile transcript. If you hit
  one of these for real, **paste the exact text back into this row** — that
  correction is more valuable than anything else you could do with the
  finding.

Several rows are guard-catchable: `scripts/check_control_props.py` rejects
the renamed-property class before a generated app ever reaches
`compile_canvas`, which is *why* no exact transcript exists for those rows in
this repo — the guard's own test suite (`tests/test_defect_regression.py`)
proves the pattern is real, just not compile_canvas's literal wording for it.
They stay in this table for the case that matters most: a hand-authored
screen that bypassed the guard, or a guard that was skipped before pushing.

## User-defined function declaration limits

| Error text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `Unknown type Table` | EXACT (`powerfx-limits.md`) | A UDF declared `funcX(): Table = …`. UDFs cannot declare `Table` as a return type. | Rewrite as a named formula: `funcX = …;` in `App.Formulas`. Named formulas return tables fine. |
| `'funcX' is an unknown or unsupported function` (one report per call site) | EXACT shape, `funcX` is a placeholder (`powerfx-limits.md`) | The knock-on effect of the row above: once the declaration fails, every screen that calls `funcX` reports it as unknown. Reading the call sites first sends you hunting the wrong place. | Go to the **declaration**, not the calls. Fix the return type there; every call-site error clears in the same push. |
| `Behavior function in a non-behavior property` | EXACT (`powerfx-limits.md`) | A UDF or named formula contains a side effect (`Set`, `Collect`, `Patch`, `Remove`, `Notify`) but was not declared to return `Void`. | Declare `funcX(): Void = { … };` and wrap the body in braces. Named formulas are pure — side effects only ever belong in a `Void` UDF. |
| A resolution failure at a UDF call site that takes a record parameter (message varies) | PATTERN (`powerfx-limits.md`, "varies; often a resolution failure at the call") | Record parameters on UDFs are unreliable in this engine. | Stage the record in a global instead: `Set(glFormDraft, {…})` at `OnStart` with every field's type filled in, then have the UDF read `glFormDraft`. `Set(glFormDraft, Blank())` gives it no type at all — never seed a record global with `Blank()`. |
| A "no type found" style failure on a named formula or UDF built over a collection | PATTERN, wording paraphrased (`powerfx-limits.md`) | The collection it reads was never seeded with a typed row — Power Fx cannot infer a schema from an empty collection. | Seed with one fully typed row, then clear it: `ClearCollect(colX, Table({Col: "", …})); Clear(colX);`. Same rule for any global a UDF reads via `Set()`. |
| `[App, Formulas] Void return type is only supported with behavior user-defined functions.` (x2 in this run), cascading into `[App, OnStart] 'funcStartLoading' is an unknown or unsupported function.`, `[btn_AssetForm_Save, OnSelect] 'funcStartLoading' is an unknown or unsupported function.`, and 12 more of the same shape across screens and components (16 of 34 errors total) | LIVE (2026-09-07, second run) | `templates/App.pa.yaml`'s `funcStartLoading(): Void = Set(glBoolIsLoading, true);` and `funcStopLoading(): Void = Set(glBoolIsLoading, false);` were single-expression bodies, not brace-wrapped. A `Void`-returning UDF is only valid as a **behavior** UDF, and a behavior UDF requires the `{ … }` body form — a bare expression body is rejected even though every other `Void` UDF in the same file (`funcLoadItems`, `funcSaveItem`, `funcNotify`, …) already used braces and compiled fine. The declaration failure then cascades: every call site reports the function as unknown, exactly like the `Unknown type Table` row above. | Wrap the body in braces: `funcStartLoading(): Void = { Set(glBoolIsLoading, true); };` (and the `Stop` equivalent). These two were the *only* `: Void =` UDFs in the whole skill tree missing braces — swept `templates/`, `components/`, and `scripts/emit_formulas.py`'s generated text and found no other instance. `scripts/check_references.py` now statically flags a brace-less `: Void =` declaration (see "Consider a guard" in the skill's task notes) so this exact hand-authored defect cannot recur silently. |

## Function-signature errors

| Error text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `Expected identifier name` (paired with `Ungroup has some invalid arguments`) | EXACT (`powerfx-limits.md`) | `Ungroup(t, "Rows")` — the second argument was quoted. `Ungroup`'s column argument is an **identifier**, not a string. | Use `Ungroup(t, Rows)` unquoted. `SortByColumns` is the opposite convention — it still takes quoted strings — so do not "fix" that one by removing the quotes. |

## Renamed-property errors (unknown property on a control)

Each of these is a property that existed on the previous-generation control
and was renamed (or removed) on the modern equivalent. `check_control_props.py`
rejects every one of these against `references/control-contracts.yaml` before
generated output ever reaches `compile_canvas` — the nine defect classes in
`tests/test_defect_regression.py` are the guard's own regression proof. If one
still reaches a live push (a hand-authored screen, a skipped guard run), expect
an unknown/unrecognized-property error naming the control and the old property;
the exact wording is not yet captured here — paste it in on first sighting.

| Old property (previous-generation control) | Correct property (modern control) | Control | Sourcing |
|---|---|---|---|
| `FontColor` | `Color` | `ModernText` | PATTERN (`control-dialects.md`; guard-caught in `test_1_fontcolor_on_moderntext`) |
| `Weight: ='TextCanvas.Weight'.*` | `FontWeight: =FontWeight.*` | `ModernText` | PATTERN (`control-dialects.md`; guard-caught in `test_2_weight_on_moderntext`) |
| `HintText` | `Placeholder` | `ModernTextInput` (`HintText` is the classic `TextInput`'s property) | PATTERN (`control-dialects.md`; guard-caught in `test_3_hinttext_on_moderntextinput`) |
| `Fields` | `ItemDisplayText` | `ModernCombobox` | PATTERN (`control-dialects.md`) |
| `TriggerOutput` | `DelayOutput` | `ModernCombobox` | PATTERN (`control-dialects.md`) |
| `Format` | *(no replacement — omit it)* | `ModernTextInput` has no `Format` property; that is classic-only | PATTERN (`control-dialects.md`; guard-caught in `test_4_format_on_moderntextinput`) |
| `Value` | *(no replacement — read via the selected item)* | `ModernCombobox` has no `Value` property | PATTERN (`control-dialects.md`; guard-caught in `test_5_value_on_moderncombobox`) |
| `ShowScrollbar` | *(no replacement — omit it)* | `Gallery` has no `ShowScrollbar`; that is classic-only | PATTERN (`control-dialects.md`) |
| Any `Align` enum literal from the wrong namespace (`Align.Right` on a `ModernText`) | Use `'TextCanvas.Align'.{Start\|Center\|End}` on both text generations; only `Button` takes the plain `Align.{Left\|Center\|Right}` | `ModernText`, `Text`, `ModernTextInput` vs `Button` | PATTERN (`control-dialects.md`; guard-caught in `test_direct_wrong_namespace_enum`, `test_8_wrong_namespace_via_token`) — `Align.Center` is the one member both namespaces share, so it compiles while `Align.Right`/`Align.End` on the wrong control does not |
| A leaf `Gallery` with no explicit size, inside an auto-layout container | Add `FillPortions: =1` or an explicit `Height` | `Gallery` | PATTERN (`control-dialects.md`; guard-caught in `test_6_gallery_without_fillportions`) — `Gallery` is a leaf control and defaults to `FillPortions: =0`, collapsing to the ~200px control default |
| `Unknown property 'TabIndex' for control type 'ModernTextInput'.` (also seen for `'ModernCombobox'`, `'ModernDatePicker'`, `'Button'`) | `TabIndex` is **not** a rename target — it never existed on these controls. It was seeded into `references/control-contracts.yaml` from a documentation source and never corpus-verified; it appears ZERO times in the provably-compiled reference app. | LIVE (2026-09-07) — 52 of 59 errors in the first real `compile_canvas` run against this generator's output | Remove the `TabIndex: =0` line. Do not substitute another property — tab order reverts to document order, which is what the reference app relies on. `references/control-contracts.yaml` curates `TabIndex` as an `absent` (hard-error) property on all 8 controls that used to list it, so `check_control_props.py` now catches this before a push. |

## Duplicate control names (control names are global, not per-screen/component)

| Error text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `An entity with name 'con_Field' already exists. Other definition located at Components/cmp_FieldText.pa.yaml(73,9).` (also seen for `txt_Field_Input`, `Components/cmp_FieldNumber.pa.yaml(91,15)` vs `Components/cmp_FieldText.pa.yaml(90,15)`) | LIVE (2026-09-07) — 7 of 59 errors in the same run | **Control names are unique across the WHOLE APP**, not scoped to the screen or component that declares them — a real Power Apps constraint no guard in this repo knew about until this run. This skill's four field components (`cmp_FieldText`, `cmp_FieldChoice`, `cmp_FieldDate`, `cmp_FieldNumber`) all used the same generic inner names (`con_Field`, `lbl_Field_Label`, `txt_Field_Input`). | Give every control a name unique across the entire app — e.g. prefix inner field-component controls with the component's own name (`con_FieldText`, `lbl_FieldText_Label`, `txt_FieldText_Input`, and the equivalents for Choice/Date/Number). `check_control_props.py`'s `find_duplicate_controls()` now walks every `*.pa.yaml` file under `--src` and hard-errors on a name declared twice anywhere in the tree, naming both definition sites the way the compiler does (`tests/test_defect_regression.py`'s `TestDuplicateControlNamesAcrossFiles`). Two files sharing a name is fine ONLY when they are true alternatives that never ship together in the same app — e.g. this skill's `templates/frame-headermainfooter.pa.yaml` and `frame-headerrailmain.pa.yaml`, of which `scripts/new_app.py` copies exactly one into any given app. |

## Omitted-property errors (a defect class no static guard can catch)

| Error text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `[com_AssetsList_CategoryFilter, ItemDisplayText] Name isn't valid. 'Value1' isn't recognized.` (identical shape on all 11 `ModernCombobox` controls across both list and form screens, both entities, in this run — 11 of 34 errors) | LIVE (2026-09-07, second run) | `scripts/emit_screens.py` emitted no `ItemDisplayText` property at all on any generated `ModernCombobox` — grepping the generated tree confirmed the property appears nowhere. Left unset, the control's own factory default apparently references a `Value1` column that does not exist on this app's choices tables (`Table({Value: "…"})`), so the control's *default* fails to resolve — not something the generator wrote incorrectly, something it never wrote. | Set `ItemDisplayText: =ThisItem.Value` explicitly on every `ModernCombobox` — the emitted choices tables all use a `Value` column, matching the reference app's own comboboxes (`Activities.pa.yaml:148`, `:158`; `Activity Form.pa.yaml:358`). Fixed in `scripts/emit_screens.py` (all three emission sites — the list-toolbar filter combobox, the boolean Yes/No form field, and the choice-field form input) and in the hand-authored `templates/FormScreen.pa.yaml`, `templates/ListScreen.pa.yaml`, and `components/cmp_FieldChoice.pa.yaml`, which had the identical omission. **This is a defect class no static guard in this repo can catch**: `check_control_props.py` validates properties that ARE written against `control-contracts.yaml` — it has no way to notice a property that was silently never written, short of a per-control list of mandatory properties, which is a bigger design question than this fix and was not authorized here. |

## Undeclared component custom-property references

| Error text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `[txt_FieldText_Input, DisplayMode] Name isn't valid. 'DisplayMode' isn't recognized.` (identical shape on `com_FieldChoice_Input`, `dp_FieldDate_Input`, `txt_FieldNumber_Input` — 4 of 34 errors) | LIVE (2026-09-07, second run) | All four field components (`cmp_FieldText`, `cmp_FieldChoice`, `cmp_FieldDate`, `cmp_FieldNumber`) wrote `DisplayMode: =cmp_FieldX.DisplayMode` on their inner input control, but none of the four declared `DisplayMode` as a `CustomProperties` input on the component itself — so the reference resolves to nothing. | Checked the reference app for how it types a caller-controlled display-mode input before deciding: every `DisplayMode` usage there (`Activities.pa.yaml`, `Activity Form.pa.yaml`, `Components/cmp_Filter.pa.yaml`, `cmp_FilterButton.pa.yaml`, `cmp_Header.pa.yaml`) is an inline `If(glX, DisplayMode.Edit, DisplayMode.View)` expression assigned directly to a control's own `DisplayMode` property — no component anywhere in that app declares `DisplayMode`, or any enum-flavored value, as a `CustomProperties` `DataType`; the only `DataType`s used for custom properties across both corpora are `Text`, `Number`, `Boolean`, `DateAndTime`, `Color`, `Table`, `Record`, `Screen`. With no corpus precedent for typing an enum-valued input, the line was dropped from all four components rather than guessing at an invalid `DataType`. A caller who genuinely needs one of these fields read-only can still set `DisplayMode` on the *component instance* at the call site, the same way the reference app gates its own controls. |

## Component input with no typed schema (Table-typed custom property, blank or untyped default)

| Error text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `[cmp_FieldChoice, Output] Name isn't valid. 'Value' isn't recognized.` / `[com_FieldChoice_Input, DefaultSelectedItems] Name isn't valid. 'Value' isn't recognized.` / `[com_FieldChoice_Input, DefaultSelectedItems] Incompatible types for comparison: Error, Text.` (3 of 34 errors) | LIVE (2026-09-07, second run) | `cmp_FieldChoice`'s `Choices` custom property (a `Table`-typed input) had a blank `Default: =`. With no default row, the `ModernCombobox` built from `Items: =cmp_FieldChoice.Choices` has no column schema, so `.Selected.Value` in `Output` and the `Value = …` filter in `DefaultSelectedItems` cannot resolve a `Value` column at all — the third error is the same unresolved column cascading into a comparison against an `Error` value. ~~Note `cmp_FilterButton`'s `Choices`/`Items` inputs also ship a blank `Table` default and are fine … they are never resolved into a typed output the way `cmp_FieldChoice.Output` is~~ **CORRECTED by the third run below: this claim was wrong.** `cmp_FilterButton.Choices` *is* resolved into its own `Value` output record and hard-failed live the very next round. There is no known-safe blank-`Table`-default case in this component library. | Give `Choices` a typed default with the right column: `Default: =Table({Value: ""})`. That establishes the schema so `Output` and `DefaultSelectedItems` both resolve. Verified this affects only the standalone `cmp_FieldChoice` component — the generated screens build their own typed `constXChoices` tables directly wherever a choice field appears and were never affected by this. |
| `[Control 'cmp_AssetsList_HeadCategory', Property 'Choices'] The table passed in has none of the expected columns: SampleBooleanField, SampleNumberField, SampleStringField.` (identical shape on 4 more `cmp_*_Head*` instances — 5 of 7 errors) | LIVE (2026-09-07, third run — the first push against a genuine coauthoring session; see the note at the top of this file) | `cmp_FilterButton.Choices` (`Table`-typed Input) had a blank `Default: =` — the exact shape the row above wrongly claimed was safe for this component. `Self.Choices` flows into `cmp_FilterButton`'s own `Value` output record (`Choices: Self.Choices`), so it IS resolved into a typed output; with no schema to infer, the Studio fell back to its placeholder 3-column schema (`SampleBooleanField`/`SampleNumberField`/`SampleStringField`), and every caller passing a real choices table (e.g. `Choices: =constStatusChoices`, shape `Table({Value: "…"})`) failed to type-match it. | Give `Choices` a typed default matching the real column: `Default: |- \n  =Table({Value: ""})` (same fix, same shape, as `cmp_FieldChoice.Choices` above). Also fixed `cmp_FilterButton.Items` pre-emptively — identical blank default, same `Value` output record, no caller currently sets it live but the next one to would hit the same failure. |
| `[Control 'cmp_AssetsList_Navigation', Property 'Screens'] The table passed in has none of the expected columns: SampleBooleanField, SampleNumberField, SampleStringField.` (identical shape on 1 more `cmp_*_Navigation` instance — 2 of 7 errors) | LIVE (2026-09-07, third run) | **CORRECTED 2026-09-07 (fourth run) — this row's original cause claim was WRONG, kept below struck through as visible history, not silently rewritten.** ~~`cmp_Navigation.Screens` (`Table`-typed Input) defaulted to `=constScreens` — a bare app-scope named-formula reference. That is a DIFFERENT bad shape than blank: the reference is not resolvable at component-declaration time (the app scope containing `constScreens` isn't available yet), so it also fell back to the same placeholder 3-column schema, and the real `constScreens` registry table failed to type-match it.~~ **Actual cause: this was a CASCADE from the row above, not an independent defect.** The fourth run bisected a later crash by reverting only `cmp_Navigation.Screens` back to `=constScreens` while leaving `cmp_FilterButton.Choices`'s fix in place — that tree compiled with **zero errors**. `=constScreens` type-resolves fine on its own; it only produced the placeholder-schema error in the third run because `cmp_FilterButton.Choices` shipped a blank default *in that same push*, and something about that unrelated failure's fallout affected how `cmp_Navigation`'s own instances resolved too. A bare app-scope named-formula reference is not, by itself, a bad `Table` default. **CORRECTED 2026-09-07 (fifth run) — the cascade-only theory above does not hold as a general claim either.** A cold coauthoring session retested `cmp_Navigation.Screens`'s bare `=constScreens` default on its own, with no `cmp_FilterButton` blank default in the same push to blame this time, and it still produced this exact error (2 of 2 `cmp_*_Navigation` instances). The fourth run's bisection was real for that specific tree and session; it does not generalize to "a bare reference is always safe." | The row above's fix (`cmp_FilterButton.Choices`/`.Items` given typed literal defaults) was sufficient on its own. ~~`cmp_Navigation.Screens` needed **no change** — it was reverted back to `Default: =constScreens` in the fourth run and that is correct.~~ **CORRECTED 2026-09-07 (fifth run)**: `cmp_Navigation.Screens` no longer defaults to `=constScreens` at all — it ships a typed literal, `Table({Screen: ListScreen, DisplayName: "", Icon: "", Entity: "", Type: "", Group: "", BackLabel: ""})` (`ListScreen` being the legacy `--name` template's own real screen), which a cold session confirmed compiles with **0 errors**. A `--model` build's generator (`scripts/new_app.py`, Ruling 18, Phase 3 Task 8) rewrites the copy's `Screen` column to that build's own real first screen. Do not give it a literal `Table(...)` default naming `App.ActiveScreen` instead: see the "Validation FAILED with no diagnostics" entry above for what that attempt actually does. |

A `DataType: Table` custom property with an empty
default (`Default: =`, nothing after the `=`) is now caught **statically**,
before any push: `scripts/check_control_props.py`'s
`find_bad_table_defaults()` flags exactly that one proven-bad shape on any
Input property typed `Table` — `tests/test_table_default_guard.py` is its
regression proof, including a standing assertion that every shipped
`components/cmp_*.pa.yaml` passes it. A bare name/dotted reference
(`=constScreens`, `=App.Foo`) is deliberately **not** flagged — see the
correction above — nor is any literal `Table(...)`/`[...]` construction.
The guard cannot judge whether a literal's *columns* actually match what
callers pass (that is still `compile_canvas`'s job) — only whether the
Default is blank. That leniency is unchanged by the fifth-run correction
above: a bare reference is still not a *statically* bad shape, only the
live-compile risk that run exposed. `components/cmp_Navigation.pa.yaml`
itself no longer uses one, though — its `Screens` Default is now the typed
literal the fifth run confirmed compiles clean, not because this guard
required it.

## Expected warnings (not errors — leave the code as is)

| Warning text | Sourcing | Cause | Remedy |
|---|---|---|---|
| `warning: [App, Formulas] This predicate is a literal value and does not reference the input table.` (x2 in this run) | LIVE (2026-09-07, second run) | `Filter(colX, true)` — the deliberate scope-formula placeholder (Ruling 6): the generic model has no scope concept, so the scope filter's predicate is a literal `true` until a real per-entity scope condition exists to wire in. Power Fx correctly flags a predicate that never reads the table it filters — the tool is not wrong, the placeholder is intentional. | Confirmed a **warning**, not an error — the push still succeeds with these present. Leave the code exactly as written; do not silence it with a token comment or a dummy reference to the table. Replace `true` with a real condition (e.g. `Owner = glScopeFilter`, already the pattern used elsewhere in the data-access layer) only once the model actually has something to scope by. |

## Named-formula ordering (whole-blob failure)

| Symptom | Sourcing | Cause | Remedy |
|---|---|---|---|
| Dozens of unrelated `"unknown name"` errors across screens you never touched | PATTERN, quoted phrase from `app-formulas-layout.md` — not independently verified against a live transcript | A named formula in `App.Formulas` references another named formula declared **below** it. The studio's document-server binder (unlike the compile service, which tolerates this) cannot resolve a forward reference and drops the **entire** `Formulas` blob — every screen that reads *any* named formula then reports it as unresolved, which looks like unrelated damage everywhere. | Reorder to the canonical layer sequence in `references/app-formulas-layout.md`: tokens → style → vocabularies → scalar constants → pure helper UDFs → derived values → data-access region → registries/navigation → UI utility UDFs. Run `scripts/check_references.py` first — it validates the same ordering constraint statically and names the one real culprit instead of the dozens of symptoms. |

## Type-cycle cascade (component Record output)

| Symptom | Sourcing | Cause | Remedy |
|---|---|---|---|
| A collection collapses to `Error`, and hundreds of unrelated-looking errors cascade across every control that reads it | PATTERN, no single fixed string documented (`powerfx-limits.md`, `SKILL.md` "Whole-record output resolution") | The strict engine resolves a component's `Record`-typed output **as a whole**. Reading one field bare (`flt.List`) forces resolution of every sibling field on that record; if any sibling's formula reaches back into the collection currently being defined, that is a type cycle, and the collection it is part of collapses to `Error`. | Anchor every field of the component's output with a fixed-return projection so nothing needs whole-record resolution: `Text(flt.Title)`, `Value(flt.Count)`, `If(flt.Mode = "asc", SortOrder.Ascending, …)` for scalars; `ForAll(flt.List As l, {Value: Substitute(JSON(l.Value), Char(34), "")})` for tables — `JSON()` accepts the unresolved lambda value where `Text(l.Value)` inside the lambda does not. The reverse direction (reading the anchored collection back into the component) is then safe because resolution is acyclic. |

## Silent failures that are not compile errors at all

These two never produce a `compile_canvas` error message — the push reports
success — which is exactly why they belong in a playbook meant to be
consulted on *every* result, not only failing ones.

| What you will actually see | Sourcing | Cause | Remedy |
|---|---|---|---|
| A save/delete reports success but the row is unchanged | PATTERN (`docs/superpowers/specs/2026-09-07-phase2-model-driven-generator-design.md`, "Silent-failure guards") | `UpdateIf`, `RemoveIf`, `LookUp` and `Filter` open the target collection's **row scope** over both the condition and the change record. A UDF parameter named e.g. `tag` sits one case-fold from a column `Tag`, so `{Tag: tag}` can silently resolve to `{Tag: Tag}` — the row scope's own column shadows the parameter. | Prefix every UDF parameter used inside an open row scope with `p` (`pTag`, not `tag`), so it can never case-fold-collide with a column name. |
| A value written from the app side never reaches a component, or vice versa, with no error anywhere | EXACT description (`powerfx-limits.md`, `SKILL.md` "Component scope") | A component without `AccessAppScope: true` that calls `Set(glX, …)` creates its own **component-scoped** `glX`, disjoint from the app-level global of the same name. Both exist; neither sees the other; every app-side write to the app global is a dead store the component never reads (or vice versa). | Set `AccessAppScope: true` on the component, or stop relying on a shared global and pass tokens/values in as input properties instead. A component without app scope also cannot read `constStyle` — it must not keep private literals as a workaround. |

## Session mechanics that look like a compile failure but are not one

| Symptom | Sourcing | Cause | Remedy |
|---|---|---|---|
| `compile_canvas` hangs with no error for a very long time | EXACT description (`powerfx-limits.md`) | The Power Apps Studio tab is closed. The push does not fail fast — it waits out the full 1800s MCP idle timeout. | Keep the studio tab open for the whole push. A long silent stall is a closed tab, not broken auth. |
| Every tool reports success but the user's screenshots never change | EXACT description (`powerfx-limits.md`) | The studio tab was reloaded, which starts a *new* coauthoring session. The MCP connection is still talking to the orphaned old one. | `connect` again, then `compile_canvas`. Do **not** `sync_canvas` first — the new session holds the stale document and would overwrite local files with it. |
| `sync_canvas` pulls a diff that is exactly the last commit reversed | EXACT description (`powerfx-limits.md`) | A studio tab holding an older in-memory document wrote its stale state back over the push. | `git checkout` to recover, re-push, then have the user reload their tab before touching anything else. |

## The verification loop has three stages, not two

`compile_canvas` returning 0 errors is not the end of the loop —
`get_appchecker_errors` is a **third, separate stage** run against the same
live app, and it catches a different class of issue: `compile_canvas`
proves the formulas are syntactically and type-valid; `get_appchecker_errors`
runs Power Apps' own lint/perf/accessibility analysis over the app that
already compiled clean. The full loop is:

**local guards (`check_*.py`, offline) → `compile_canvas` (live, syntax/type
errors) → `get_appchecker_errors` (live, lint/perf/accessibility findings
on an app that already compiles)**

A clean `compile_canvas` result says nothing about whether
`get_appchecker_errors` will come back clean too — check both before calling
a live app finished. See `SKILL.md`'s loop diagram, which now names all
three stages.

### `get_appchecker_errors` findings, LIVE 2026-09-07 (fourth run, first check against the deployed app)

Three Medium/Performance findings, zero errors:

```
App.glScopeFilter: Unused variable
AssetFormScreen.locConfirmDelete: Unused variable
SiteFormScreen.locConfirmDelete: Unused variable
```

| Finding | Verdict | Reasoning |
|---|---|---|
| `App.glScopeFilter: Unused variable` | Expected, kept as-is | Ruling 6 made the generated per-entity scope formula a literal `Filter(col, true)` because the model has no scope concept yet — this is the SAME deliberate wart as the `warning: [App, Formulas] This predicate is a literal value…` row above. `templates/App.pa.yaml`'s `OnStart` still unconditionally `Set(glScopeFilter, "")`s the global (that line is not touched by the `--model` splice), but no `--model`-generated scope formula reads it any more, so the global is genuinely dead in generated output — not a bug, the direct consequence of the same documented seam. Decision: **keep the global**, do not remove it from the generated output. It is the seam a real per-entity scope condition (e.g. `Owner = glScopeFilter`) will read the moment the model gains one, exactly as the expected-warnings row already describes; removing it now would mean re-adding both the global and its `OnStart` initialization later, for no benefit today, and would split one documented seam into two half-consistent states across the codebase. Left as a Medium/Performance finding to accept, not fix. |
| `AssetFormScreen.locConfirmDelete` / `SiteFormScreen.locConfirmDelete: Unused variable` | **False positive — checked, the dialog IS wired** | Traced every read/write of `locConfirmDelete` in `scripts/emit_screens.py` (mirrored in `templates/FormScreen.pa.yaml`): `OnVisible` sets it `false`; `btn_*Form_Delete`'s `OnSelect` sets it `true`; the confirmation dialog (`cmp_*Form_Dialog`, `ComponentName: cmp_Dialog`) binds its own built-in `Visible` property to `=locConfirmDelete` (`Visible` is a universal instance property on any control/component, not a custom one — see `UNIVERSAL_INSTANCE_PROPS` in `check_control_props.py`); `OnCancel` and `OnSubmit` both reset it to `false`. That is a complete, correctly wired read/write cycle — the dialog only shows when the flag is true and only the flag controls it. No functional gap. This app-checker finding is treated as a checker limitation with context variables whose only *read* occurs inside a child canvas-component instance's built-in property binding rather than a top-level screen control's — plausible given it is the identical pattern (an instance-level property bound to a context variable) that a human author would also write, but not independently confirmed against Microsoft's checker internals. No code change made; recorded here so a future run does not "fix" a dialog that already works. |
