---
name: formulas-first-canvas-app
description: Use when building, editing, reviewing or refactoring a Power Apps Canvas App — .pa.yaml source, App.Formulas, Power Fx named formulas, user-defined functions, canvas components, msapp unpack — or when a canvas app has duplicated colour literals, magic numbers, data source names on screens, copy-pasted screen logic, Switch arms that keep growing, or a UI that drifted from its design tokens.
---

# Formulas-First Canvas Apps

## Overview

**`App.Formulas` is the app. Screens are a thin projection of it.**

A screen holds layout and bindings. It holds no values, no business logic, and no
data-source names. Everything a screen needs already exists as a named formula, a
user-defined function, a registry row, or a component — and if it doesn't, it gets
created there first and consumed second.

This is not style. Canvas apps have no module system, no imports and no compiler that
catches duplication; the only thing standing between an app and 10,000 lines of
copy-paste is the discipline of putting every value and every behaviour in exactly one
place. Apps that skip it become unmaintainable at roughly the third screen.

## Entry paths

| Situation | Path |
|---|---|
| **New app** | `python3 scripts/new_app.py --name "…" --out ./Src` — see below. |
| New screen in a conforming app | Copy a screen out of `templates/`; it already consumes the components. |
| Existing app that does not follow this | **`references/refactoring-legacy-apps.md`.** Rungs 1–2 are read-only and end in a human sign-off gate. Do not edit first. |
| Unsure which | Run `scripts/inventory.py` over the source. Its literal counts answer it in ten seconds. |

## Starting a new app

```bash
python3 scripts/new_app.py --name "Vendor Register" --brand "#0F6CBD" --out ./Src
```

Writes a complete tree: `App.pa.yaml` with the design tokens **inlined at the
top** (so they cannot land below their first use), both screens already wired to
the components, `Components/`, and `_EditorState.pa.yaml`. It then runs every guard
against what it just wrote and exits non-zero rather than leaving a broken tree behind.

**Identifiers stay generic** — `colItems`, `funcLoadItems`, `funcSaveItem`, `locItem`,
`gal_List_Items`, `enumEntity.Items`. Only the header title takes the app name. The
scaffold is the pattern you copy once per entity; a second entity is a second
`col*` / `funcLoad*` / `funcSave*` / `funcDelete*` set, a registry row and a copy of
the two screens, named for that entity in its own commit.

`--components none` scaffolds the formula layer alone, for when you will write
your own screens.

**There is no local path to an importable `.msapp`.** `pac canvas pack` is
deprecated and crashes on real apps; `pac canvas validate` reports every file of
a *working published* app as invalid. So: create a blank tablet app in studio,
`connect`, then `compile_canvas` to push the tree — which is also its first real
compile. The command prints these steps with your paths filled in.

## The six rules

**1. Nothing is authored twice.**
A value used twice is a `const*`. A behaviour used twice is a `func*`. A shape used
twice is a component. First duplicate is the trigger — not the third, not "when it
gets messy". Retrofitting is 10× the cost of extracting on the spot.
Eight are already written — header, navigation, command bar, filter button,
notification toast, dialog, empty state, spinner. Use them before writing chrome
by hand: `references/component-library.md`.

**2. Screens carry no literals and no data-source names.**
No `RGBA(...)`, no `#hex`, no font sizes, no padding numbers, no list or table names.
Screens read `constStyle.*` / `const*Color` and call `func*`. A screen that names a
data source has welded the app to that backend; changing backends then means editing
every screen instead of one region. `scripts/check_tokens.py` enforces colours, font
sizes and radii; `scripts/check_data_layer.py` enforces data-source names. Spacing
literals are only *reported*, by `scripts/inventory.py`.

**3. Named formula vs UDF is decided by type limits, not taste.** See the table below.

**4. One data-access region owns every data-source reference.**
All reads, writes and shape translation (choice wrappers, lookup records, claims,
per-entity physical resolution) happen inside banner comments in `App.Formulas`.
Screens see flat scalar collections and call `funcSaveX` / `funcDeleteX`. See
`references/data-access-layer.md`.

**5. Registries over branches.**
Screens, entities and navigation live in tables (`constScreens`, `constEntities`,
`constNavigation`) that components iterate. Adding an entity is a row, not a new
`Switch` arm in six places. A `Switch` whose arms grow with the data model is a
registry that hasn't been written yet.

**6. A green compile is not a correct app.**
`compile_canvas` does not type-check columns referenced off a collection: a gallery
reading `ThisItem.Year` from a collection with no `Year` column compiles clean and
fails at runtime. `SortByColumns("Year", ...)` string names are never validated
either. Run the guard scripts alongside every compile.

## Naming

| Prefix | Means | Lives in |
|---|---|---|
| `const*` | Named formula — value, token, view, registry | `App.Formulas` |
| `enum*` | Closed vocabulary record (`enumEntity.Activities`) | `App.Formulas` |
| `func*` | User-defined function | `App.Formulas` |
| `gl*` | Global set with `Set()` | `App.OnStart`, mutated anywhere |
| `loc*` | Screen context variable | `UpdateContext` on one screen |
| `col*` | Collection — **only** if genuinely mutated | data-access region |
| `cmp_*` | Canvas component | `Src/Components/` |
| `con_*` | Layout container | screens |

A table that is never mutated is a named formula, not a collection. The app checker
flags this as `CollectingReadOnlyTable` and it is right: collections cost startup time
and lose their type at the boundary.

## Named formula vs UDF

| Need | Use | Why |
|---|---|---|
| Return a table | **Named formula** | UDFs cannot declare `Table` as a return type. `funcX(): Table = …` fails with `Unknown type Table`, and every *call site* then reports `'funcX' is an unknown or unsupported function` — which sends you hunting the call instead of the declaration. |
| Read a `Set()` global | **Named formula** | Named formulas can read globals. This is the supported way to make a derived view react to app state. |
| Take a record parameter | **Neither — stage it** | Record params on UDFs are unreliable. Put the record in a global (`glFormDraft`) that the UDF reads. The global must be `Set()` to a fully typed record at `OnStart`; Power Fx cannot infer a record type from `Blank()`. |
| Scalar in, scalar out | **UDF** | Fine, including many parameters. |
| Side effects (`Patch`, `Collect`, `Notify`) | **UDF returning `Void`** | Named formulas are pure and cannot mutate. |

Full list with the error text each limit produces: `references/powerfx-limits.md`.

## Ordering inside App.Formulas

Order matters more than it should. The studio's document-server binder — unlike the
compile service — **cannot resolve a forward reference from one named formula to
another**, and failing to resolve one drops the entire `Formulas` blob, producing
dozens of unrelated "unknown name" errors on screens.

Declare in dependency order: tokens → vocabularies → pure helper UDFs → derived
values → data-access region → registries and navigation that read it. Canonical layout
with section banners: `references/app-formulas-layout.md`.

## Guard scripts

Copy `scripts/` into the target repo and run all five alongside every compile. The
four `check_*` scripts and `inventory.py` are standalone; `new_app.py` reads
`templates/` and `components/` relative to itself, so run it from the skill tree.

```bash
python3 scripts/inventory.py           --src <Src/>   # read-only census (rung 1)
python3 scripts/check_tokens.py        --src <Src/>   # no literals outside the token region
python3 scripts/check_data_layer.py    --src <Src/> --datasource-pattern 'PP_[A-Za-z]'
python3 scripts/check_collection_columns.py --src <Src/>
python3 scripts/check_references.py    --src <Src/>   # names resolve; declaration order is safe
```

`new_app.py` runs all four on its own output, so a fresh scaffold starts clean.

Each takes `--help`. `check_*` exit non-zero on violation, so they drop straight into
CI or a pre-commit hook.

**Write the guard before the sweep it protects.** A convention with no script rots back
within two sprints, and the second time it rots nobody notices.

## Traps that cost real days

- **A missing token reference takes the whole app down, not one control.** An
  unresolved name in `App.Formulas` drops the entire `Formulas` blob in the studio
  binder, so the symptom is dozens of "unknown name" errors on screens you never
  touched. `check_references.py` finds the one real cause.
- **Component scope.** A component *without* `AccessAppScope: true` that does
  `Set(glX, …)` gets its own component-scoped `glX`, disjoint from the app global of
  the same name. Every app-side write to it is silently dead. Such a component also
  cannot see `constStyle` — so either set `AccessAppScope: true` or pass tokens in as
  input properties. It must not keep private literals.
- **Whole-record output resolution.** The strict engine resolves a component's Record
  output *as a whole*. Reading one field bare (`flt.List`) forces resolution of every
  sibling field; if any sibling reaches back into the collection being defined, that is
  a type cycle and the collection collapses to `Error` — cascading into hundreds of
  unrelated errors. Fix: anchor each field with a fixed-return projection —
  `Text(flt.X)`, `Value(flt.X)`, and for tables
  `ForAll(flt.List As l, {Value: Substitute(JSON(l.Value), Char(34), "")})`.
  `JSON()` accepts the unresolved lambda value; `Text(l.Value)` inside the lambda does
  not.
- **Auto-layout flex defaults.** `GroupContainer` children default to `FillPortions: 1`
  (flexible — `Width`/`Height` then ignored); leaf controls default to `0`. A fixed
  child (`FillPortions: 0`) **must** carry an explicit `Height` — `LayoutMinHeight` is
  ignored for it and the ~200px control default wrecks the layout.
- **Two text generations, two property vocabularies.** `Control: Text` takes
  `FontColor` / `Weight: ='TextCanvas.Weight'.*`; `Control: ModernText` takes
  `Color` / `FontWeight: =FontWeight.*`. **Both take `Align: ='TextCanvas.Align'.*`**
  (Start/Center/End) — only `Button` takes the plain `Align.*` enum (Left/Center/Right).
  Mixing them is a compile error. See `references/control-dialects.md`, and let
  `scripts/check_control_props.py` enforce it rather than trusting memory.
- **`Ungroup(t, Rows)` takes an identifier, not `"Rows"`.** The quoted form fails with
  `Expected identifier name`. (`SortByColumns` still takes quoted strings — the
  inconsistency is real.)
- **`//` is Power Fx comment syntax, valid only inside a `|-` block scalar.** A `//`
  line at YAML mapping level is a parse error.
- **Studio Save round-trips the YAML** — strips comments, alphabetizes properties,
  elides default-valued ones. Commit that normalization diff on its own as `chore:`,
  never mixed with a semantic change.

## Red flags — stop and fix the formula layer instead

- Writing `RGBA(`, a hex string, or a font size into a screen file
- Writing a data-source name anywhere outside the data-access region
- Copy-pasting a control block "just for now"
- Adding a `Switch` arm alongside five existing ones for the same dimension
- Declaring a UDF whose return type is `Table`
- `Collect`ing a table that nothing ever mutates
- Editing a legacy app before completing rungs 1–2 of the refactor ladder
- Committing a semantic change and a studio round-trip in one commit

## References

| File | Contents |
|---|---|
| `references/app-formulas-layout.md` | Canonical section order and banners |
| `references/powerfx-limits.md` | Type limits, engine differences, exact error text |
| `references/data-access-layer.md` | Boundary pattern, backend-switch procedure |
| `references/design-system.md` | Token layer, AA contrast, type scale, spacing grid |
| `references/component-library.md` | The eight components: contracts, what changed, what is missing |
| `references/refactoring-legacy-apps.md` | **Brownfield ladder — six rungs with gates** |

**Visual spec sheet** — swatches, live-computed contrast, type scale and control specs,
rendered: https://claude.ai/code/artifact/cdff9a80-7b84-4f56-9ce2-beaa4152424d
(Shared link; if it does not open, ask in `#claude-skills`. `references/design-system.md`
carries the same values and is the source of truth.)
