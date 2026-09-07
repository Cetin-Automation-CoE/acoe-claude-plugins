# Compile-error playbook

Keyed by the error text `compile_canvas` (or `get_appchecker_errors`) puts in
front of you, not by the underlying cause — you have the error first, this
table gets you to the cause and the fix without re-deriving either from
scratch. `references/powerfx-limits.md` and `references/control-dialects.md`
have the fuller prose; this file exists so an agent can go
**push → read error → look it up here → fix → repush** without a detour into
either.

## How precisely each row is sourced

There is no offline compile for Canvas Apps. This generator's own output was
first pushed through a live `compile_canvas` session on 2026-09-07 — a
two-entity app that passed all six static guards and 226 tests came back with
59 errors, all attributable to exactly two root causes (see the two **LIVE
2026-09-07** entries below). So the rows below split into three kinds, marked
in the **Sourcing** column:

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
