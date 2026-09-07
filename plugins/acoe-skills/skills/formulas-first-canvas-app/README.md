# Formulas-First Canvas Apps — user manual

A Claude Code skill for building and maintaining Power Apps Canvas Apps that stay
maintainable past the third screen. The idea in one line: **`App.Formulas` is the app,
screens only display it.** Every colour, size, business rule and data-source name lives
in exactly one place, and scripts check that it stays there.

This file is for people. The file Claude reads is `SKILL.md`.

---

## What you need

| Requirement | Why |
|---|---|
| Claude Code with the `acoe-skills` plugin installed | The skill loads automatically when you talk about canvas apps |
| Python 3.9 or newer | The scaffolder, `inventory.py` and the five `check_*.py` guard scripts are Python, no packages needed |
| The `canvas-apps` plugin (Canvas Authoring MCP) | The only way to compile and push `.pa.yaml` source into a live app |
| Power Apps Studio access | You create the blank app and keep its tab open while Claude pushes |

You never need `pac canvas pack` or `pac canvas validate`. Both are broken for current
apps and the skill tells Claude not to use them.

---

## How you use it

You do not invoke the skill. Talk to Claude about a canvas app and it loads by itself.
Any of these will do:

- "Create a new canvas app for tracking vendor contracts." (Claude will ask for
  your data model before generating anything — see below.)
- "Add a Contacts screen to this app."
- "Why does my app show forty 'unknown name' errors after I edited App.Formulas?"
- "Review this canvas app before we hand it over."
- "This app is a mess, help me refactor it without breaking it."
- "Rebrand this app to the new colours."

What Claude does next depends on which of the situations below you are in.

---

## 1. Start a new app

**Claude asks for your data model first.** Paste one in any form — a table, a
SharePoint list, a Dataverse table, CSV headers, or just a list of field names — or
say you don't have one and Claude drafts one from your description of the app. Either
way you get one confirmation round trip (a compact field table; "just go" accepts it
as drafted) before anything is generated — not a long interview.

**What you get:** a complete app on disk sized to your model — one list screen and one
form screen **per entity**, the design tokens, eight reusable components, mock data
that renders on first run, and a navigation registry covering every entity — all
passing the local guard scripts.

**What happens**

1. Claude writes your confirmed model to `model.yaml` beside the source tree (schema:
   `templates/model.example.yaml`). This file is the app's spec — commit it.

2. Claude runs the generator:

   ```bash
   python3 scripts/new_app.py --model model.yaml --out ./Src
   ```

   (No model at all, even after being asked, falls back to the generic one-entity
   pattern: `python3 scripts/new_app.py --name "Vendor Register" --brand "#0F6CBD" --out ./Src`.)

3. You create a **blank tablet app** in Power Apps Studio with the same name and leave
   the tab open.

4. Claude connects the Canvas Authoring MCP to it and pushes the `Src` folder with
   `compile_canvas`. That push is also the first compile — the generator's output has
   not yet been validated against a live session, and the components were ported from a
   production app but have never been through the strict compiler in this exact form.
   Expect a round of fixes; `references/compile-error-playbook.md` maps the error text
   you see to a cause and a fix.

5. Commit the moment it compiles green.

**What is in the generated tree** (shown for a two-entity model; N entities produce N
of the per-entity rows)

| File | Contents |
|---|---|
| `App.pa.yaml` | Design tokens, vocabularies, enums, helper functions, a mock data-access layer with one region per entity, the screen registry, navigation stack, notification helpers |
| `<Entity>sListScreen.pa.yaml` (one per entity) | Header, collapsible navigation rail, search, status filter, command bar, sortable and filterable column headers, a gallery with status colours and right-aligned money, footer aggregates, empty state, toasts, spinner |
| `<Entity>FormScreen.pa.yaml` (one per entity) | Header with back button, a card with the entity's fields, one validation formula shared by the error label and the Save button, Save, Cancel, Delete behind a confirm dialog |
| `Components/` | The eight components below |
| `_EditorState.pa.yaml` | Screen and component order for Studio |

**Generated identifiers are entity-derived, not generic.** A model with an `Asset`
entity produces `colAssets`, `funcSaveAsset`, `AssetsListScreen.pa.yaml`. This is
different from the skeleton `templates/` and `components/` ship with, and from what the
generic `--name`-only path writes — both of those stay deliberately generic
(`colItems`, `funcLoadItems`, `funcSaveItem`, `locItem`) because they are the pattern to
copy once per entity, not a finished domain app.

---

## 2. Connect real data

The skeleton runs against a seeded mock collection. Wiring the real backend is a source
edit, not a runtime switch, because Power Fx cannot compile a reference to a data
source the app does not have yet.

1. Add the SharePoint list, Dataverse table or connector in Studio.
2. Everything to change sits between the two `DATA ACCESS LAYER` banners in
   `App.pa.yaml`. Each `funcLoadX` has the real body already written underneath the
   mock, commented and marked `// SWITCH DAY:`. Claude deletes the mock and uncomments.
3. Choice fields, lookup records and composite keys are unwrapped there and nowhere
   else. Screens keep reading flat scalar collections and never change.
4. Run the guards, compile, commit.

Ask Claude: *"Switch the vendor data layer from the mock to the `PP_Vendors` SharePoint
list."*

---

## 3. Add an entity or a screen

If the app has a `model.yaml`, add a new entry under `entities:` and re-run
`python3 scripts/new_app.py --model model.yaml --out ./Src`. That regenerates the new
entity's collection, `funcLoad*`/`funcSave*`/`funcDelete*` set, registry row and screen
pair — the navigation rail reads the registry, so the new screen appears in the menu
without touching the rail, and there is no `Switch` to extend anywhere. Re-run the
guards and re-push before trusting it.

For an app built on the generic `--name`-only skeleton (no `model.yaml`), it is a
manual recipe instead: a new collection plus `funcLoad*` / `funcSave*` / `funcDelete*`
inside the data-access region, a row in the `constScreens` registry, and a copy of the
list and form templates renamed for the new entity.

Ask Claude: *"Add a Contracts entity with a list and a form screen."*

---

## 4. Check an app's health

Six scripts, all read-only except that the five `check_*.py` guards exit non-zero
when they find a violation, so they drop straight into a pre-commit hook or CI.

```bash
python3 scripts/inventory.py                --src Src/                 # census, never fails
python3 scripts/check_tokens.py             --src Src/                 # no colour / size / radius literal on screens
python3 scripts/check_data_layer.py         --src Src/ --datasource-pattern 'PP_[A-Za-z]'
python3 scripts/check_collection_columns.py --src Src/                 # every column you read exists
python3 scripts/check_references.py         --src Src/                 # every name resolves, in a safe order
python3 scripts/check_control_props.py      --src Src/ --tokens-file Src/App.pa.yaml  # control properties match their control's contract
```

**Why bother when the app compiles?** The compiler does not check column names on
collections, does not validate the string column names in `SortByColumns`, and the
Studio binder rejects forward references that the compile service accepts. Each of
those fails at runtime or shows up as dozens of unrelated errors. `check_control_props.py`
adds a fourth class: a property name that belongs to the *other* control generation,
or a design-token value from the wrong dialect, both of which read fine in the YAML
and fail only at compile. None of the six scripts replaces a live compile — they
narrow what a `compile_canvas` push still needs to catch. When a push does fail,
`references/compile-error-playbook.md` maps the error text to a cause and a fix.

Ask Claude: *"Run the guards on this app and tell me what is off."*

---

## 5. Refactor an existing app

For an app that was not built this way, the skill switches to a six-rung ladder. The
app compiles and is committable at the top of every rung, so you can stop anywhere.

| Rung | What happens | You are asked to |
|---|---|---|
| 0 | Unpack to YAML and commit the untouched baseline | Provide the solution or app |
| 1 | `inventory.py` census, read-only | Nothing |
| 2 | Written findings with IDs, severities and proposed fixes, read-only | **Sign off the findings list.** Nothing is edited before you do. Ambiguous business rules come back to you as numbered questions, never guessed |
| 3 | Real defects fixed first, one per commit | Review small commits |
| 4 | Data-source access moved into one guarded region | Review |
| 5 | Design tokens defined in one commit, screens repointed in the next | Review two commits that stay bisectable |
| 6 | Duplicated blocks turned into registries and components | Review |

Two rules Claude will hold to: one axis per pass (colour, or layout, or logic, never
two), and Studio's own save-normalisation lands as its own `chore:` commit so it never
hides a real change.

Ask Claude: *"Refactor this app onto the formulas-first pattern. Start with the
inventory."*

---

## 6. Rebrand

The token block at the top of `App.Formulas` has nine values marked **TO REBRAND**.
Change those and nothing else; every screen and component follows. The design-system
reference carries the measured contrast ratios, so Claude re-checks that status text
still passes WCAG AA on white after the change.

Ask Claude: *"Change the brand colour to #005EB8 and check contrast."*

---

## 7. Use the components in your own app

You can lift the components without the rest. Copy the files from `components/` into
your `Src/Components/`, paste `templates/design-tokens.pa.yaml` at the top of your
`App.Formulas`, and run `check_references.py` to confirm nothing is missing.

| Component | What it is |
|---|---|
| `cmp_Header` | App chrome: back or menu button, title, refresh, notifications badge, help, loading bar |
| `cmp_Navigation` | Icon rail that expands to a labelled menu, driven by the screen registry |
| `cmp_CommandBar` | Row of round action buttons, each shown or hidden by a `Can*` input |
| `cmp_FilterButton` | Column header that is also the sort and filter affordance |
| `cmp_Notification` | Toast stack with countdown bar |
| `cmp_Dialog` | Modal confirm dialog, optional date field |
| `cmp_Empty` | Empty-state row for a gallery that returned nothing |
| `cmp_Spinner` | Full-screen blocking overlay |

Every component reads the app's tokens directly, so none of them carries its own
colours or sizes.

---

## Known limits

- **Nothing compiles offline.** The only validator that reflects reality is
  `compile_canvas` in a live coauthoring session. That is what the guard scripts exist
  to compensate for.
- **The `--model` generator's output has not yet been validated against a live
  `compile_canvas` run.** The five local guards prove the emitted YAML is
  structurally sound, contract-clean and internally consistent — they do not prove
  Power Apps accepts it. Treat the first push as a debugging session, not a formality,
  and expect `references/compile-error-playbook.md` to be consulted.
- **The components have not been compiled in this form.** Same caveat as above —
  they were ported from a production app but never through the strict compiler in
  this exact shape.
- **The filter dialog is not included.** Column headers raise `OnSelect` with a metadata
  record; you connect whatever filter UI you have, or start with sort only.
- **The generic `--name`-only skeleton is a starting point, not a finished app.** Two
  screens, one entity, three fields, mock data. A `--model` build scales this to as
  many entities and fields as the model declares.

---

## Folder map

```
formulas-first-canvas-app/
  SKILL.md              what Claude reads: the ask-for-model workflow, the six rules,
                        naming, traps, references
  README.md             this file
  scripts/              new_app.py generator (--model or the generic --name path),
                        model.py (schema + validation + derived names),
                        emit_mock.py / emit_formulas.py / emit_screens.py
                        (the --model emitters), inventory.py, and five
                        check_*.py guards including check_control_props.py
  templates/            App.pa.yaml, design-tokens.pa.yaml, ListScreen, FormScreen,
                        model.example.yaml (the model.yaml schema, two worked
                        entities), inventory.md and findings.csv report templates
  components/           the eight cmp_*.pa.yaml files
  references/           layout order, Power Fx limits, data layer, design system,
                        component library, the refactoring ladder, control dialects
                        (control-dialects.md), the machine-readable contracts
                        check_control_props.py checks against (control-contracts.yaml),
                        and the compile-error playbook keyed by compile_canvas's own
                        error text (compile-error-playbook.md)
  tests/                unittest suite for the guards and the generator — run with
                        `python3 -m unittest discover -s tests`
```
