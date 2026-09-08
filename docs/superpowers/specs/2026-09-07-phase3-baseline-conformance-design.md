# Phase 3 — baseline conformance, dashboard, discovery

**Date:** 2026-09-07
**Status:** approved in chat, ready for implementation planning
**Skill:** `plugins/acoe-skills/skills/formulas-first-canvas-app/` (v0.9.0 after Phase 2)
**Prior specs:** Phase 1 `2026-09-07-formulas-first-model-driven-design.md`, Phase 2 `2026-09-07-phase2-model-driven-generator-design.md`

## The baseline

The user stated: generated apps "should basically look like the app in this directory":

```
/Users/krystofpe/Documents/DEVOPS/CETIN-IT-Platforms/ACOE/acoe-3688-regional-procurement-plan
  canvasapps/…/Src/            ← the app source (Activities.pa.yaml is the canonical list screen)
  docs/design/direction.md     ← chosen design direction + token layer
  docs/data-model/*.dbml       ← the app's real data model
```

**The older copy at `/Users/krystofpe/powerapps-work/canvas-src` is stale** (Dashboard 183 vs 376
lines, App.pa.yaml 813 vs 2498). Phase 1's `control-contracts.yaml` was corpus-verified against the
stale copy. Where the two disagree, the baseline wins.

## What the first live render showed

Phase 2's output compiled with zero errors and rendered broken. Two screenshots (Studio canvas and
Play mode) established:

| Symptom (Play mode) | Root cause | Evidence |
|---|---|---|
| **"Showing 0 of 16"** — grid empty though 16 rows loaded | An untouched `ModernCombobox` has no defined selection state, so `IsEmpty(SelectedItems)` never returns true and every `IsEmpty(...) Or Field in ...` clause is false | The baseline documents this in a comment on its own filter comboboxes and works around it with `DefaultSelectedItems: =FirstN(<choices>, 0)` — an empty but **typed** table. Hand-patching that onto the live app compiled clean (pending visual confirmation). |
| Nav rail takes ~half the screen | Nav wrapped in a horizontal auto-layout container with no `Width`, so it flexes 50/50 with the body | Baseline: nav and list are **direct screen children, absolutely positioned** — nav `Width: =If(cmp_X_Navigation.Navigation, 250, 60)`, list `X: =Nav.Width + 10`, `Width: =Parent.Width - Nav.Width - …` |
| Header band empty | My `cmp_Header` root sets `Width: =App.Width`; the baseline's root sets no `Width` | Unverified until pushed — the fix is to match the baseline and observe |
| "Find items" in every combobox | `InputTextPlaceholder` never emitted — the factory default the original brief warned about | Baseline: `InputTextPlaceholder: ="Status"` |
| "AMOUNT:" blank | `Sum()` over zero rows is `Blank()` | `Coalesce(Sum(…), 0)` |
| Only 2 of 7 headers (Studio canvas only) | Flex `FillPortions: =1` column crushes fixed siblings when the viewport is narrow. **Renders correctly in Play at full width** — this is robustness, not a bug | Baseline: no flex column. Fixed `Width` + `LayoutMinWidth` per header, row `LayoutMinWidth` = sum, table `LayoutOverflowX: Scroll` |
| Black bar under headers (Studio canvas only) | The designer's empty-gallery placeholder | Gone in Play. No action. |

Two earlier diagnoses were wrong and are recorded so they are not repeated: "colSorts is empty
because OnVisible did not run" (Play mode runs OnVisible; the count still read 0) and "the flex
column is a bug" (it renders fine at full width).

## Part 1 — Rendering: adopt the baseline skeleton

`emit_screens.py` changes to mirror `Activities.pa.yaml`:

1. **Screen composition.** Drop the `con_<Plural>List_Main` horizontal wrapper. Emit
   `cmp_<Plural>List_Header`, `cmp_<Plural>List_Navigation` and `con_<Plural>List_List` as direct
   screen children with the baseline's absolute-position formulas. The nav's width is a formula on
   its own expanded state; the list container derives `X` and `Width` from it.
2. **Filter comboboxes** get `DefaultSelectedItems: =FirstN(<choicesTable>, 0)` and
   `InputTextPlaceholder: ="<Label>"`. The `FirstN` idiom gets a code comment carrying the
   translated baseline rationale, because it looks redundant and will otherwise be "cleaned up".
3. **Column headers.** Fixed `Width` from the model's `grid:` px, `LayoutMinWidth` = the same, on
   both the header instance and its row cell. `grid: flex` becomes a wide fixed column (240px) with
   `LayoutMinWidth`. The header row and the gallery carry `LayoutMinWidth` = sum of widths; the table
   container carries `LayoutOverflowX: =LayoutOverflow.Scroll`.
   Erratum (2026-09-08, final review I2): LayoutMinWidth = sum of widths + inter-child gaps + the
   row's Open button. "Sum of widths" alone under-counted the row's own `LayoutGap` between every
   child and the gallery row's 8th child (`btn_<Plural>Row_Open`, previously unwidthed) — below
   ~1050px this clipped the trailing column and the Open button. The header row also gained a
   trailing spacer cell of the same width so its own child/gap count matches the gallery row's.
4. **Sort** goes through two emitted UDFs, `funcTableSortColumn(pEntity)` and
   `funcTableSortOrder(pEntity)`, each `Coalesce`-defaulting to the first grid field / `"asc"`, so
   no state of `colSorts` can blank the grid. Matches the baseline's names.
5. **Footer** `Sum` wrapped in `Coalesce(…, 0)`.
6. **`cmp_Header`** root: remove `Width: =App.Width` to match the baseline. Verified only by the
   next push.

`check_layout.py` drops its CanvasComponent exemption — the nav defect proved it wrong — and gains a
rule: a `CanvasComponent` child of an auto-layout container needs `Width`/`Height` like any other
fixed child.

## Part 2 — Dashboard, revised against the real baseline

The design approved earlier was based on the stale 183-line Dashboard. The baseline's 376-line one
has five regions. Generalisation:

| Baseline region | Generalises to | Scope |
|---|---|---|
| Band — KPI tiles (code · value · unit), "Savings by country (EUR)" | A `money` field **summed by** a `choice` field of the same entity; one tile per vocab value. Emitted only when the model has both. | conditional |
| Pipeline — status chips `{S} · CountRows(Filter(scope, Status = S))` | One chip per vocab value of the entity's primary status field (`role: status`, else the first `filter: true` choice field) | yes |
| Gates — domain prose | Not generalisable | skip |
| Navigation tiles — `constDashboardNavigation` rows `{Screen, DisplayName, Icon, Count}` | Entity totals, then one "Overdue" per `semantics: due` field, then status slices; cap 8; each navigates to its list screen without pre-filtering (faithful to baseline; pre-filter is a follow-up) | yes |
| Trademark | as-is | yes |

Section titles and captions use the baseline's `lbl_Dash_*Title` / `*Caption` `ModernText` pattern;
the earlier "HTML message board" is dropped. Tile sizing, radius and padding go into a
`constStyle.Dashboard` token group — the baseline hardcodes `15`, `140`, `20`, `200` and
`check_tokens.py` rightly rejects those on a screen.

`dashboard: true|false` in the model, default **on when entities > 1**, off for one. When on,
`DashboardScreen` is `StartScreen` and the first `constScreens` row (Type `enumScreenType.Dashboard`,
a new enum member). `constDashboardNavigation` and the pipeline/band sources are named formulas in
the data-access layer, so the topological sort orders them after the collections they count.

## Part 3 — Discovery: one round, richer round

`SKILL.md` step 3 changes from "show the table, confirm" to "show the table **and**, in the same
message, ask only what the sentence left ambiguous". Each answer lands in a model field:

| Question | Lands in |
|---|---|
| Which field identifies a record? | `role: title` |
| Which status matters most? | `role: status` — drives pipeline chips, semafor colour, default sort |
| Is there a deadline date? | `semantics: due` |
| Want a dashboard? | `dashboard:` |

Two new field modifiers, `role: title` and `role: status`. Still one round trip; still accepts
"just go".

## Order of work

1. Rendering (Part 1) → push → **user screenshots Play mode**. Nothing else is built on a broken
   skeleton; the dashboard inherits the same nav/header conventions.
2. Dashboard + discovery (Parts 2–3) → push → screenshot.
3. Validation: generate from a subset of the baseline's `docs/data-model/procurement-plan.dbml`
   (Shared + Regional core — it has lookups, which remain deferred) and compare to the real app.

## Constraints carried

- Python 3.9.6; stdlib `unittest`; no pytest.
- Do not weaken the six guards or the six architectural rules.
- Templates keep generic identifiers; generated output uses entity-derived ones.
- Preserve the two deliberate warts.
- `references/control-contracts.yaml` changes only on live-compiler or baseline evidence, stated.
- Every live push runs against an active coauthoring session; sessionless results are not trusted.

## Definition of done

1. Play-mode screenshot shows: nav rail 60px collapsed, header with title and buttons, all grid
   columns with rows visible, real placeholders, footer count and total populated.
2. A three-entity model with a money+choice pair produces a Dashboard with band, pipeline, tiles and
   trademark; `StartScreen` is the dashboard; nav lists it first.
3. `SKILL.md` discovery step asks the four questions in one message and `role:` lands them.
4. All guards pass; live compile zero errors; app checker no errors; installed copy synced.
