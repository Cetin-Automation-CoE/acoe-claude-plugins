# Phase 2 — multi-entity model-driven app generator

**Date:** 2026-09-07
**Status:** approved design, ready for implementation planning
**Skill:** `plugins/acoe-skills/skills/formulas-first-canvas-app/` (at v0.8.0 after Phase 1)
**Phase 1 spec:** `docs/superpowers/specs/2026-09-07-formulas-first-model-driven-design.md`

## What the user asked for

> The skill should ask for the user's data model. If provided, create the app from scratch in the
> design and complexity we have defined. If not provided, create it from scratch with mock data.
> If the model has more tables, more screens with list views/tables.

## The core insight

**Both branches produce the same artifact.** The app is always generated with mock data; the only
difference is whether the *schema* was supplied or inferred. There is one generation path and two
ways to reach it. "Model provided" is the easier case, not the harder one, because nothing has to
be invented.

`App.pa.yaml` already carries the switch-day seam — a working mock `ClearCollect` above, the real
data-source binding commented out below. The generator fills in both, so a generated app runs
immediately and is one uncomment away from real data.

## What already exists (do not rebuild)

The list screen already has sortable filter headers, a search box, a data grid, filter chips and
footer aggregates. The form screen already has validation, save/delete and a dirty check. Eight
components are wired. What is hardcoded is only that the entity has exactly three fields called
`Title`, `Status` and `Amount`.

The architecture is **already multi-entity ready**, which is the single most important fact for
scoping this phase:

- `enumEntity` ships with two entries (`Items`, `Contacts`)
- `constScreens` is a registry of rows carrying `Screen`, `DisplayName`, `Icon`, `Entity`, `Type`,
  `Group`, `BackLabel` — "adding a screen is a ROW here, not a new Switch arm elsewhere"
- `cmp_Navigation` takes the registry as an input and iterates it, so N entities populate the
  navigation rail automatically with no extra work

Phase 2 therefore parameterises existing shapes and adds rows to an existing registry. It does not
introduce a new architecture.

## Decisions taken

| Decision | Choice |
|---|---|
| Screens per model | N tables → N list screens + N form screens. Nav populates from the registry. |
| Relationships | Tables are **independent**. No lookups between them in this phase. |
| Generated identifiers | Entity-derived: `colAssets`, `funcLoadAssets`, `funcSaveAsset`, `locAsset`. Templates and docs stay generic (`colItems`). |
| Model input format | The agent normalises **anything** the user pastes — prose, CSV headers, a SharePoint column list, a Dataverse schema — into `model.yaml`, then shows a field table for one confirmation. |
| Grid width | Fields marked `grid: hidden`, and any beyond ~7 columns, are form-only. |
| Mock rows | `--rows N`, default 16. |

### The naming decision, and why it overrides a standing preference

A recorded preference (2026-09-03) required scaffolder output to use generic identifiers. Three
tables cannot each be `colItems`. The preference's stated rationale — "the scaffold is a pattern to
copy once per entity" — stops applying once the generator does that copying. Resolution, confirmed
with the user: templates and documentation keep generic names; generated output derives names from
the model. The saved memory has been updated to record the split.

## The workflow the skill must perform

This is the deliverable the user actually asked for, and it belongs in `SKILL.md` as a required
sequence, not a suggestion.

```
1. ASK — "Do you have a data model? Paste it in any form. If not, say so and I'll draft one."
2a. PROVIDED  → normalise whatever arrived into model.yaml (agent judgement)
2b. NOT       → infer 8-12 fields per table from the domain sentence, with plausible
                vocab lists and 3-5 realistic samples per text field (agent judgement)
3. CONFIRM — show a compact field table. One round trip maximum; accept "just go".
4. WRITE   — model.yaml next to the source tree. It is the app's spec; commit it.
5. GENERATE— new_app.py --model model.yaml --out ./Src   (deterministic; script's job)
6. VERIFY  — the script runs all guards on its own output and exits non-zero on failure.
```

The division of labour is the whole point: **the agent supplies domain judgement** — which fields,
which vocabulary values, realistic sample strings. **The script supplies correctness** —
guard-clean YAML, spread across vocabularies, dates relative to today, dependency-ordered
formulas. Neither should do the other's job.

## Model schema

```yaml
app_name: Site Equipment Register
brand: "#300091"
frame: headermainfooter          # headermain | headermainfooter | headerrailmain
entities:
  - entity: Asset
    plural: Assets
    icon: AppsListDetail
    group: Operations            # nav grouping in constScreens
    key: composite               # composite = "<prefix>|<id>", or: single
    fields:
      - {name: Tag,         type: text,   required: true, grid: 100,  label: TAG, samples: [EQ-10041, EQ-10042]}
      - {name: Title,       type: text,   required: true, grid: flex, label: EQUIPMENT, search: true}
      - {name: Category,    type: choice, required: true, grid: 130,  filter: true, vocab: [Antenna, Radio Unit, Router]}
      - {name: Status,      type: choice, required: true, grid: 120,  filter: true, vocab: [In Service, Faulty]}
      - {name: Health,      type: choice, grid: 118, filter: chips, vocab: [green, amber, red], semantics: semafor}
      - {name: Amount,      type: number, grid: 118, money: true, currency: EUR, min: 0}
      - {name: ServiceDate, type: date,   grid: 112, semantics: due, warn_days: 45}
      - {name: Owner,       type: text,   search: true, grid: hidden}
  - entity: Site
    plural: Sites
    ...
```

Archetypes: `text`, `longtext`, `choice`, `number`, `date`, `boolean`.
Modifiers: `required`, `search`, `filter` (`true` | `chips`), `grid` (px | `flex` | `hidden`),
`money`, `min`/`max`, `semantics` (`semafor` | `due` | `none`), `vocab`, `samples`.

A single-table model is the same schema with one entry under `entities:`.

## Architecture — hybrid emitter

Static chrome (the `App.Formulas` scaffold, the three frames, the eight components) stays as
readable template files with splice markers, so the guards can check them standalone and the two
deliberate warts survive. The **repeating** shapes become Python emitter functions driven by the
model.

**The emitter reads `references/control-contracts.yaml`** — the same file `check_control_props.py`
validates against. This is what Phase 1 bought: the generator cannot emit a property the guard
would reject, because both read one table.

### The shapes to generate, per entity

| Shape | Today | Generated |
|---|---|---|
| Grid column header | 3 hardcoded `cmp_FilterButton` instances | one per non-hidden `grid:` field |
| Grid row cell | 3 hardcoded cells | one per non-hidden field; control chosen by archetype |
| Form field | 3 hardcoded blocks | one per field, using `cmp_Field*` |
| Mock rows | 1 row, then deleted | ~16 rows per entity |
| `App.Formulas` data layer | fixed `funcSaveItem(key,title,status,amount)` | per-entity collection, load/save/delete UDFs, choices tables |
| `constScreens` | 2 hardcoded rows | 2 rows per entity |
| `enumEntity` | 2 hardcoded members | one per entity |

### Mock data rules

- **Never a bare `Clear()` on an entity collection.** Seed-then-clear stays only for the framework
  collections (`colFilters`, `colSorts`, `colBack`, `colNotifications`), where a typed schema with
  no rows is genuinely wanted. Phase 1's `check_bare_clear` enforces this.
- At least one row per `vocab` value of every `choice` field, so every filter demonstrably does
  something and no dropdown option yields an empty grid.
- `date` fields with `semantics: due`: ~30% in the past relative to `Today()`, so overdue styling
  and counters are visible on first run.
- `number` fields spread across two orders of magnitude, respecting `min`/`max`.
- Text fields cycle their `samples` so rows read as distinct real records, never "Item 1, Item 2".
- Composite keys `"<PREFIX>|<n>"`, prefix derived from a grouping field.
- Dates as `Date(y, m, d)` literals, never strings.

### Declaration order

`App.Formulas` must be strictly dependency-ordered — the studio binder cannot forward-reference
between named formulas, and one unresolved name drops the entire `Formulas` blob. With N entities
this stops being trivial, so the generator needs a real topological sort over the emitted names.

## New components

`cmp_FieldText`, `cmp_FieldChoice`, `cmp_FieldDate`, `cmp_FieldNumber` — **separate per type on
purpose**. Each then has one scalar output of a known type, which structurally avoids the
whole-record type-cycle cascade documented in `references/powerfx-limits.md`. A single generic
`cmp_Field` switching over four control types and returning a Record is exactly the construct that
caused a 247-error cascade. Do not build it.

`cmp_FilterButton` is resolved by dropping its `Value` metadata-record output and making it an
honest sort header, since the skill deliberately does not ship the filter dialog it was built for.

## Frames and the layout guard

`--frame headermain | headermainfooter | headerrailmain`, with header and footer pinned at explicit
heights and main sized `Parent.Height - header - footer`.

`scripts/check_layout.py` enforces:
- every `FillPortions: =0` child of an auto-layout container carries an explicit `Width`
  (horizontal parent) or `Height` (vertical parent) — `LayoutMinHeight` is ignored for fixed children
- every auto-layout container has at least one flexible child or an explicit size
- a leaf control with neither `FillPortions` nor an explicit size is flagged
- `Visible:` on a flexible spacer is flagged — **an invisible child is dropped from auto-layout
  entirely**, so the gap collapses and the layout shifts with the data. Correct pattern: keep it
  visible and blank its `Text`.

## Silent-failure guards

- **UDF parameter / column case collision.** `UpdateIf`, `RemoveIf`, `LookUp` and `Filter` open the
  target collection's row scope over both the condition and the change record. A parameter named
  `tag` sits one case-fold from the column `Tag`, so `{Tag: tag}` can resolve to `Tag: Tag` — a
  save that writes nothing and reports success. Enforce a `p` prefix for any UDF parameter used
  inside an open row scope, and generate code that way.
- **`With()` wrapping behaviour functions** is unreliable. Flag `With(` whose body contains
  `Set|Collect|Patch|Remove|Update|Clear|Notify|Navigate`. Prefer `UpdateIf`, whose change record is
  evaluated against the original row.
- **`SortByColumns` strings** checked against the columns of the specific collection being sorted.

## Closing the loop

`references/compile-error-playbook.md`: a lookup table keyed by the exact error text
`compile_canvas` returns → cause → remedy, seeded from `references/powerfx-limits.md`. This is what
lets an agent iterate `push → read errors → fix → repush` unattended.

`SKILL.md` documents the loop:
`ask → draft model → generate → local guards → push → parse errors → auto-fix → repeat`.

## Constraints carried from Phase 1

- Do not weaken the five guards or the six architectural rules.
- Generated output stays guard-clean by construction: no colour/font-size/radius literals outside
  the token region; no data-source name outside the data-access banners.
- Preserve the two deliberate warts: `cmp_Notification`'s repeated `First(SortByColumns(…))`, and
  any recorded `// token-exempt:` literal.
- `new_app.py` runs **all** guards on its own output and exits non-zero rather than leaving a broken
  tree behind.

## Two parked questions from Phase 1

Neither blocks this phase, but both should be settled against a live `compile_canvas` before the
generator is used widely:

1. Defect class 9 — a bare enum into a `DataType: Text` component input — may not be a real error.
   The compiled reference app does it self-consistently and ships.
2. `requires_one_of` on `Gallery` may need to accept `AlignInContainer: SetByContainer`.

## Definition of done

1. `--domain "<sentence>"` and `--model model.yaml` both work end to end, documented in `SKILL.md`.
2. The ask-for-model workflow is written in `SKILL.md` such that the agent performs it.
3. A single-table model generates a list screen with a real data table (sortable headers, filter
   toolbar, footer aggregates), an edit form with validation, all eight components wired, and
   **visible mock rows on first run**.
4. A three-table model generates three list screens and three forms, with the navigation rail
   populated from `constScreens` and no hand-editing.
5. All guards pass on generated output for both cases, and `new_app.py` exits non-zero if not.
6. `check_layout.py` and the field components ship; `SKILL.md` and `README.md` updated; version
   bumped.
