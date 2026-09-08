# formulas-first-canvas-app → model-driven app generator

**Date:** 2026-09-07
**Status:** approved design, ready for implementation planning
**Skill:** `plugins/acoe-skills/skills/formulas-first-canvas-app/`

## Problem

The skill scaffolds a skeleton a human then fills in by hand. It should generate a complete,
working, well-designed app — list screen with a data table, filtering, sorting, an edit form —
from either a data model or a one-line domain description, safely and unattended.

Today it cannot be trusted to do that. `new_app.py` emits ~1,000 lines that pass all four
guards while containing real compile errors, prints "All checks pass", then prints push
instructions. A scaffolded app was pushed to a live environment and rendered as an empty grid
with two component errors and no data.

There is no offline compile for Canvas Apps. `pac canvas pack` is deprecated and crashes;
`pac canvas validate` rejects every file of a working published app. The only true validator is
`compile_canvas` against a live coauthoring session. Local static checks are therefore the only
thing that can make generation trustworthy, and they must cover **control contracts**, not just
architecture — which is all they cover today.

## Findings from investigation

These were measured against the repo tree, the installed copy, and the provably-compiled app at
`/Users/krystofpe/powerapps-work/canvas-src`. They change the design and are not re-litigated
below.

### F1 — Drift is bidirectional across 18 files, not one

The brief anticipated `SKILL.md` differing. In fact 18 files differ and **neither copy is a
superset**.

Repo ahead: `Value: ="Value"` removed from the ModernCombobox; `FontColor:`→`Color:` on
ModernText row cells; `Align: ="Right"` correctly passed as a string to `cmp_FilterButton`,
which declares `Align` as `DataType: Text` (the installed copy passes the enum `=Align.Right`
into a text input).

Installed ahead: `cmp_Header.pa.yaml` `lbl_Header_Badge` is a `ModernText` and installed has
`Align: ='TextCanvas.Align'.Center`; the repo regressed it to `Align: =Align.Center`.

### F2 — The repo's own SKILL.md documents the wrong contract, and that is the root cause

`SKILL.md` currently states:

> `Control: Text` takes `FontColor` / `Weight` / `'TextCanvas.Align'.Start`; `Control: ModernText`
> takes `Color` / `FontWeight` / `Align.Left`.

The `ModernText` half is wrong. Ground truth shows **both** text controls take
`'TextCanvas.Align'.*`. A recent "Fix:" commit added this rule and then applied it, which is
precisely how `cmp_Header.pa.yaml` and `design-tokens.pa.yaml` acquired bad `Align` values. The
drift is not random; the documentation is actively teaching the defect. Correcting the doc is a
prerequisite — otherwise any future edit reintroduces it.

### F3 — Four of the seven listed defects are still live in the repo baseline

| Defect | Repo status |
|---|---|
| `FontColor` on `ModernText` | fixed |
| `Weight:` on `ModernText` | never wrong — only ever on prev-gen `Text`, with `'TextCanvas.Weight'` |
| `Value:` on `ModernCombobox` | fixed |
| `HintText` on `ModernTextInput` | **live** — `templates/ListScreen.pa.yaml:103` |
| `Format: =TextFormat.Number` | **live** — `templates/FormScreen.pa.yaml:117` |
| Gallery without `FillPortions` | **live** — `templates/ListScreen.pa.yaml:188` |
| `Clear(colItems)` after seeding | **live** — `templates/App.pa.yaml:90` |

### F4 — An eighth defect, hidden by the token layer

`templates/design-tokens.pa.yaml:140` defines `Align: Align.Right`. `lbl_Row_Amount`, a
`ModernText`, consumes it via `constStyle.Label.NumberInput.Align`. The wrong-namespace enum is
laundered through a design token, so a line-oriented scan of the screen never sees it.

The token architecture — the thing that makes the rest of the skill work — is also a blind spot
for a naive contract checker. **A guard that does not resolve token indirection will catch the
easy cases and miss the real ones.**

### F5 — Flat namespace enforcement produces a false positive against shipping code

In the compiled app, every text control uses `'TextCanvas.Align'.*` except
`Vendors.pa.yaml:133`, a `ModernText` with `Align: =Align.Center`, in an app that provably
compiled.

`Align` = {Left, Center, Right, Justify}. `'TextCanvas.Align'` = {Start, Center, End}. `Center`
is the sole shared member. The evidence supports a **graded** rule, not a flat one.

### F6 — `CanvasComponent` instance properties are not control properties

The compiled app has `cmp_Filter_*` instances carrying `Align: =Align.Left`. These are custom
component inputs, not control properties. A guard that treats them as control properties
false-positives on shipping code.

### F7 — `new_app.py` is a template copier, not a generator

207 lines of marker substitution over `templates/`. Model-driven output means templates become
parameterized fragments. This is the bulk of Phase 2's work.

### F8 — The model's `entity:` conflicts with a standing preference

The brief's model schema specifies `entity: Asset` / `plural: Assets`. Recorded user feedback
(2026-09-03) requires scaffolder identifiers to stay generic; the `--entity` rename flag was
removed for exactly this reason.

**Resolution:** `entity` and `plural` drive **display text and mock-data realism only** — app
title, header, grid column labels, empty-state copy, sample values. Power Fx identifiers stay
generic: `colItems`, `funcLoadItems`, `funcSaveItem`, `locItem`, `gal_List_Items`.

## Decisions taken

| Decision | Choice |
|---|---|
| Drift reconciliation | Repo canonical; cherry-pick installed-side wins after verifying each against the compiled app; overwrite installed from repo at the end |
| Sequencing | Phase 1 (guards) ships alone and first; Phase 2 (generator) builds on it |
| Token dialect collision | Dialect-neutral token names — `AlignModern` / `AlignLegacy` fields resolved per dialect |

## Architecture

### The central bet: one contract file, two consumers

`references/control-contracts.yaml` is read by **both** `check_control_props.py` and, in Phase 2,
the generator's emitter. This is what makes "guard-clean by construction" real rather than
aspirational: the emitter cannot invent a property name the guard would reject, because both
read the same table.

Shape, per control name:

```yaml
ModernText:
  generation: modern
  properties: [Color, Size, FontWeight, Align, Wrap, AutoHeight, Text, Visible, OnSelect, ...]
  enums:
    FontWeight: FontWeight            # FontWeight.{Bold|Semibold|Normal|Lighter}
    Align: "TextCanvas.Align"         # {Start|Center|End}
  renamed_from:
    FontColor: Color
    FontSize: Size
    Weight: FontWeight
    BorderRadius: [RadiusTopLeft, RadiusTopRight, RadiusBottomLeft, RadiusBottomRight]
  removed: [DisplayMode]
```

Contract data is seeded from the brief's verified table, then reconciled against the compiled
app. **Where the two disagree the compiled app wins, and the disagreement is reported rather
than silently resolved.**

Controls covered in Phase 1: `ModernText`, `Text`, `ModernTextInput`, `ModernCombobox`,
`ModernDatePicker`, `Button`, `ModernButton@1.0.0`, `Gallery`.

### `scripts/check_control_props.py` — three resolution layers

**Layer 1 — direct.** Walk every `*.pa.yaml`, track the enclosing `Control:` by indentation, and
check each property line. Fails on unknown properties, on the *old* name of a rename, and on
enum values from the wrong namespace.

**Layer 2 — token-resolving.** Two-pass. Parse `design-tokens.pa.yaml` (and the equivalent
region of a target app's `App.pa.yaml`) into a symbol table of dotted path → literal value. When
a property value is a `constStyle.X.Y` reference, resolve it before checking. Without this the
guard misses F4 entirely.

Values that cannot be resolved — an `If()` or `Switch()` body, a component input, a `ThisItem`
expression — are **counted and reported as unchecked**, never counted as passing.

**Layer 3 — component-instance aware.** For a child whose `Control:` is `CanvasComponent`, parse
the named component's `CustomProperties` block from `components/cmp_*.pa.yaml` and validate the
instance's properties against the declared names and `DataType`. This addresses F6, and catches
the installed copy's enum-into-a-`DataType: Text` bug as a bonus.

**Graded severity**, per F5:

- **error** — the enum member does not exist in the target namespace (`Align.Right` on a
  `ModernText`; the correct member is `'TextCanvas.Align'.End`)
- **warn** — the member exists in both namespaces (`Align.Center`), so it compiles but is
  dialect-inconsistent
- **error** — unknown property, renamed-from property, removed property

### Design tokens: dialect-neutral names

A single `Align` token cannot serve both dialects. Tokens carrying enum values that differ by
generation get explicit per-dialect fields:

```
NumberInput: {
    AlignModern: 'TextCanvas.Align'.End,
    AlignLegacy: Align.Right,
    ...
}
```

The contract file records which field a control of each generation may consume, so Layer 2 can
check the resolved value against the consuming control's namespace.

### `references/control-dialects.md`

Documents the two coexisting generations as *different controls*, not a versioning mistake, with
the operative rule:

> Determine the dialect from the target app's existing YAML, never from the docs alone, and keep
> the whole tree internally consistent. A tree that is uniformly one dialect can be converted by
> one mechanical rename sweep; a mixed tree cannot.

Supersedes and corrects the wrong rule identified in F2.

## Phase 1 — scope

Ships independently. On completion the existing tree is verified, the eight defects are gone,
and no generator work has started.

1. **Reconcile drift.** Repo canonical. Verify each of the 18 files' hunks against the compiled
   app. Produce a reconciliation table: file → hunk → winning side → evidence. Overwrite the
   installed copy from repo at the end so the two cannot diverge silently again.
2. **Correct `SKILL.md`'s dialect rule** (F2) before anything else, since it is the defect
   source.
3. **Fix the six live defects** — the four from F3 (`HintText`, `Format: =TextFormat.Number`,
   Gallery without `FillPortions`, `Clear(colItems)`), the token `Align.Right` from F4, and the
   `cmp_Header` `Align.Center` regression from F1. Done before the guard exists, so the guard's
   first run on a clean tree is a real test rather than a wall of pre-existing noise.

   Note the distinction that governs the test fixtures: **six defects are live in the tree**,
   but the guard must catch **nine defect classes** — the brief's seven, plus the two discovered
   here (F4, a wrong-namespace enum laundered through a design token; F6/F1, an enum passed into
   a component input declared `DataType: Text`). Three of the nine are already fixed in the repo
   and must be reintroduced synthetically to test the guard.
4. **`references/control-contracts.yaml`** — seeded, reconciled, disagreements reported.
5. **`scripts/check_control_props.py`** — three layers, graded severity.
6. **`references/control-dialects.md`.**
7. **Defect-reintroduction test.** One fixture per defect *class* — nine, not six — each
   asserting the guard exits non-zero with the expected message. Definition of Done item 4
   requires verification, not assumption.
8. **Coverage-limit messages** on every guard's PASS line, including the four existing ones.
   Replaces the misleading bare "All checks pass".

### Coverage limits the new guard must state

- values it could not resolve statically (count reported)
- controls absent from the contract file
- property *values* beyond enum-namespace checking — type correctness, formula validity
- anything only a live `compile_canvas` can catch

## Phase 2 — scope (outline)

Planned separately after Phase 1 lands.

**Generator architecture — hybrid emitter.** Static chrome (the `App.Formulas` scaffold, the
three frames) stays as readable template files with splice markers, so guards can check them
standalone and the two deliberate warts survive untouched. The repeating shapes — grid columns,
form fields, filter chips, mock rows — become Python emitter functions driven by the model and
the contract file. `--dialect legacy|modern` then selects a property-name map rather than
maintaining a parallel tree.

**Task 1 — two entry paths.** `--model model.yaml` with the archetype schema (`text`, `longtext`,
`choice`, `number`, `date`, `boolean`; modifiers `required`, `search`, `filter`, `grid`, `money`,
`min`/`max`, `semantics`, `vocab`, `samples`). The no-model path is first-class and encoded in
`SKILL.md` as a required workflow: the agent infers the model from a domain sentence, shows a
compact field table, takes one confirmation round trip maximum, writes `model.yaml`, then the
script generates. The division of labour is the point — **agent supplies domain judgement,
script supplies correctness**. Subject to F8: `entity` drives display text, never identifiers.

**Task 1c — mock data.** Never a bare `Clear()` on the entity collection; seed-then-clear stays
only for `colFilters`/`colSorts`/`colBack`/`colNotifications`. At least one row per `vocab`
value; ~30% of `semantics: due` dates in the past relative to `Today()`; numbers spread across
two orders of magnitude; text cycling `samples` so rows read as distinct real records; composite
keys `"<PREFIX>|<n>"`; dates as `Date(y, m, d)` literals, never strings.

**Task 4 — the two repeating shapes.** `cmp_FieldText`, `cmp_FieldChoice`, `cmp_FieldDate`,
`cmp_FieldNumber` as **separate per-type components on purpose** — each has one scalar output of
a known type, structurally avoiding the whole-record type-cycle cascade documented in
`references/powerfx-limits.md`. A single generic `cmp_Field` returning a Record is the construct
that caused a 247-error cascade and must not be built. Plus `cmp_GridRow` or a documented
generated row shape.

`cmp_FilterButton` is resolved by **dropping the `Value` metadata-record output** and making it
an honest sort header, since the skill deliberately does not ship the filter dialog it was
intended for.

**Task 5 — frames and layout guard.** `--frame headermain|headermainfooter|headerrailmain`, with
header and footer pinned at explicit heights and main sized `Parent.Height - header - footer`.
`scripts/check_layout.py` enforces: every `FillPortions: =0` child of an auto-layout container
carries an explicit `Width`/`Height` per parent direction (`LayoutMinHeight` is ignored for
fixed children); every auto-layout container has a flexible child or explicit size; leaf
controls — Gallery especially — have `FillPortions` or explicit size; and `Visible:` on a
flexible spacer is flagged, because **an invisible child is dropped from auto-layout entirely**
(correct pattern: keep it visible, blank its `Text`).

**Task 6 — silent-failure guards.** UDF parameter/column case collision (`UpdateIf`, `RemoveIf`,
`LookUp`, `Filter` open row scope over both condition and change record, so a parameter `tag`
one case-fold from column `Tag` makes `{Tag: tag}` resolve to `Tag: Tag` — a save that writes
nothing and reports success); enforce a `p` prefix convention and generate accordingly. Flag
`With(` whose body contains a behaviour function. Check `SortByColumns` strings against the
columns of *the specific collection being sorted*.

**Task 7 — close the loop.** `references/compile-error-playbook.md`, keyed by the exact error
text `compile_canvas` returns → cause → remedy, seeded from `references/powerfx-limits.md`.
`SKILL.md` documents the loop: draft model → generate → local guards → push → parse errors →
auto-fix → repeat.

## Constraints (carried, not re-litigated)

- Do not weaken the four existing guards or the six architectural rules. This adds a
  verification layer and a generation layer; it does not replace the architecture.
- Generated output stays guard-clean by construction: no colour/font-size/radius literals
  outside `App.pa.yaml`; no data-source name outside the data-access banners; `App.Formulas`
  declaration order strictly dependency-ordered — the studio binder cannot forward-reference
  between named formulas, and one unresolved name drops the entire `Formulas` blob, so the
  generator needs a real topological sort.
- Preserve the two deliberate warts and their rationale: `cmp_Notification`'s repeated
  `First(SortByColumns(…))`, and any recorded `// token-exempt:` literal.
- `new_app.py` runs **all** guards including the new ones on its own output and exits non-zero
  rather than leaving a broken tree behind.

## Definition of done

Phase 1:

1. Drift reconciled and reported; installed copy matches repo.
2. All six live defects fixed; `SKILL.md`'s dialect rule corrected.
3. `check_control_props.py` fails when any of the nine defect classes is deliberately
   reintroduced, verified by test fixtures.
4. Every guard states its coverage limits on PASS.
5. Version bumped; `SKILL.md` and `README.md` updated.

Phase 2:

6. `--domain "<sentence>" --out ./Tmp` documented in `SKILL.md`; `--model model.yaml --out ./Tmp`
   works end to end.
7. Generated app has a list screen with a real data table (sortable headers, filter toolbar,
   footer aggregates), an edit form with validation, all eight components wired, and **visible
   mock rows on first run**.
8. All guards pass on generated output.
