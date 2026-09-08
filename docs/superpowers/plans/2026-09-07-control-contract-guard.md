# Control Contract Guard (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `formulas-first-canvas-app` skill's output trustworthy by reconciling repo/installed drift, fixing six live control-contract defects, and adding a contract guard that catches nine defect classes the four existing guards miss.

**Architecture:** A single machine-readable `references/control-contracts.yaml` is the source of truth, read by `scripts/check_control_props.py` today and by the Phase 2 generator later. The guard resolves properties in three layers — direct line scanning with indentation-tracked control context, design-token indirection resolution, and component-instance custom-property validation — with graded severity so it does not false-positive against provably-compiled code.

**Tech Stack:** Python 3.9.6 (no `match`, no PEP 604 unions at runtime), PyYAML 6.0.3, stdlib `unittest` (pytest is NOT installed and must not be introduced — this repo has no dependency manifest).

**Spec:** `docs/superpowers/specs/2026-09-07-formulas-first-model-driven-design.md`

## Global Constraints

- Skill root for all relative paths: `plugins/acoe-skills/skills/formulas-first-canvas-app/`
- Python 3.9.6 compatible only. No `match` statements, no `int | None` annotations evaluated at runtime, no `functools.cache` (use `lru_cache`).
- Tests use stdlib `unittest`. Run with `python3 -m unittest discover -s tests -v` from the skill root.
- Do not weaken the four existing guards (`check_tokens.py`, `check_references.py`, `check_data_layer.py`, `check_collection_columns.py`) or the six architectural rules.
- Power Fx identifiers in templates stay generic: `colItems`, `funcLoadItems`, `funcSaveItem`, `locItem`, `gal_List_Items`. Never rename to a business entity.
- Preserve the two deliberate warts: `cmp_Notification`'s repeated `First(SortByColumns(…))`, and any `// token-exempt:` literal.
- New guard follows existing CLI convention: `--src <dir>`, argparse, prints `PASS:`/`FAIL:` on line 1, `sys.exit(1)` on violation.
- Ground-truth corpus for contract arbitration: `/Users/krystofpe/powerapps-work/canvas-src` (a provably-compiled app). Where it disagrees with documentation, it wins, and the disagreement is reported.

## Verified reference data

**Enum namespace members** (needed for graded severity):

| Namespace | Members |
|---|---|
| `Align` | Left, Center, Right, Justify |
| `'TextCanvas.Align'` | Start, Center, End |
| `FontWeight` | Bold, Semibold, Normal, Lighter |
| `'TextCanvas.Weight'` | Bold, Regular |
| `'ButtonCanvas.Appearance'` | Primary, Secondary, Outline, Subtle, Transparent |
| `'ButtonCanvas.Layout'` | IconBefore, IconAfter, IconOnly, TextOnly |
| `'ButtonCanvas.IconStyle'` | Filled, Regular |
| `TextInputType` | SingleLine, Multiline, Password, Search |
| `TriggerOutput` | Keypress, FocusOut, Delayed |
| `Appearance` | FilledDarker, FilledLighter, Outline |
| `VerticalAlign` | Top, Middle, Bottom |

`Center` is the ONLY member shared between `Align` and `'TextCanvas.Align'`. This is why severity is graded.

**The nine defect classes the guard must catch:**

| # | Defect | Live in tree? |
|---|---|---|
| 1 | `FontColor:` on `ModernText` | no — fixed, test synthetically |
| 2 | `Weight:` on `ModernText` | no — fixed, test synthetically |
| 3 | `HintText:` on `ModernTextInput` | yes — `templates/ListScreen.pa.yaml:103` |
| 4 | `Format: =TextFormat.Number` on `ModernTextInput` | yes — `templates/FormScreen.pa.yaml:117` |
| 5 | `Value:` on `ModernCombobox` | no — fixed, test synthetically |
| 6 | `Gallery` without `FillPortions` | yes — `templates/ListScreen.pa.yaml:188` |
| 7 | `Clear(colItems)` after seeding | yes — `templates/App.pa.yaml:90` |
| 8 | Wrong-namespace enum laundered through a token | yes — `templates/design-tokens.pa.yaml:140` |
| 9 | Enum passed into a component input declared `DataType: Text` | no — repo already fixed, test synthetically |

Defects 6 and 7 are not control-property defects. Defect 6 belongs to `check_layout.py` (Phase 2) — in Phase 1 `check_control_props.py` covers it with a narrow rule: a `Gallery` with no `FillPortions` and no explicit `Height`. Defect 7 belongs to a data-layer rule added to `check_data_layer.py` in Task 9.

---

### Task 1: Correct the dialect documentation (root cause)

The repo's `SKILL.md` and `references/powerfx-limits.md` both state that `ModernText` takes `Align.Left`. This is false — ground truth shows both text generations take `'TextCanvas.Align'.*`. A recent commit added this rule and then applied it, producing the `cmp_Header` and `design-tokens` defects. Fix the documentation before the code, or the next edit reintroduces the bug.

**Files:**
- Create: `references/control-dialects.md`
- Modify: `SKILL.md` (the "Two text generations" bullet, ~line 181)
- Modify: `references/powerfx-limits.md` (the "What compile catches" paragraph, ~line 95)

**Interfaces:**
- Consumes: nothing.
- Produces: `references/control-dialects.md`, cited by `SKILL.md` and by Task 4's contract file header.

- [ ] **Step 1: Verify the false claim is present**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
grep -n "Align.Left" SKILL.md references/powerfx-limits.md
```

Expected: two hits, both asserting `ModernText` takes `Align.Left`.

- [ ] **Step 2: Confirm ground truth contradicts it**

```bash
grep -rn "Align: =" /Users/krystofpe/powerapps-work/canvas-src --include='*.pa.yaml' \
  | grep -c "TextCanvas.Align"
grep -rn "Align: =Align\." /Users/krystofpe/powerapps-work/canvas-src --include='*.pa.yaml' | wc -l
```

Expected: `'TextCanvas.Align'` used on text controls throughout; the 17 plain-`Align.*` hits are on `Button` and `CanvasComponent`, with exactly one `ModernText` outlier (`Vendors.pa.yaml:133`, using the shared member `Center`).

- [ ] **Step 3: Write `references/control-dialects.md`**

````markdown
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
````

- [ ] **Step 4: Replace the false bullet in `SKILL.md`**

Find the bullet beginning `- **Two text generations, two property vocabularies.**` and replace the whole bullet with:

```markdown
- **Two text generations, two property vocabularies.** `Control: Text` takes
  `FontColor` / `Weight: ='TextCanvas.Weight'.*`; `Control: ModernText` takes
  `Color` / `FontWeight: =FontWeight.*`. **Both take `Align: ='TextCanvas.Align'.*`**
  (Start/Center/End) — only `Button` takes the plain `Align.*` enum (Left/Center/Right).
  Mixing them is a compile error. See `references/control-dialects.md`, and let
  `scripts/check_control_props.py` enforce it rather than trusting memory.
```

- [ ] **Step 5: Replace the false paragraph in `references/powerfx-limits.md`**

Replace the `**What compile catches:**` paragraph with:

```markdown
**What compile catches:** unknown control properties, unknown functions, bad UDF return
types. The commonest property trap is the two text generations: `Control: Text`
(previous-generation modern) takes `FontColor` and `Weight: ='TextCanvas.Weight'.Bold`;
`Control: ModernText` takes `Color` and `FontWeight: =FontWeight.Bold`. Both take
`Align: ='TextCanvas.Align'.{Start|Center|End}`. `Button` in this skill is the
previous-generation modern button (`'ButtonCanvas.*'` enums, `FontColor`, `BorderRadius`,
no `Fill`) and takes the plain `Align.{Left|Center|Right}` enum. Full table:
`references/control-dialects.md`.
```

- [ ] **Step 6: Verify no false claim survives**

```bash
grep -rn "ModernText.*Align.Left\|Align.Left.*ModernText" SKILL.md references/
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/SKILL.md \
        plugins/acoe-skills/skills/formulas-first-canvas-app/references/
git commit -m "docs: correct ModernText Align contract, add control-dialects reference

SKILL.md and powerfx-limits.md both claimed ModernText takes Align.Left.
Ground truth shows both text generations take 'TextCanvas.Align'.*; only
Button takes the plain Align enum. This false rule was the source of the
cmp_Header and design-tokens regressions."
```

---

### Task 2: Reconcile repo/installed drift and report

18 files differ bidirectionally. Repo is canonical; port the one installed-side win. Produce a reconciliation table as a durable artifact.

**Files:**
- Create: `docs/superpowers/notes/2026-09-07-drift-reconciliation.md`
- Modify: `components/cmp_Header.pa.yaml:216`

**Interfaces:**
- Consumes: Task 1's corrected dialect rule (justifies the `cmp_Header` verdict).
- Produces: a reconciled repo tree; the installed copy is synced in Task 10, not here.

- [ ] **Step 1: Capture the full diff for the record**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
diff -r ~/.claude/skills/formulas-first-canvas-app . > /tmp/drift.txt 2>&1
wc -l /tmp/drift.txt
```

- [ ] **Step 2: Write the reconciliation report**

Create `docs/superpowers/notes/2026-09-07-drift-reconciliation.md`:

```markdown
# Drift reconciliation: repo vs installed skill copy

Date: 2026-09-07. Repo declared canonical. Verified against the compiled app at
`/Users/krystofpe/powerapps-work/canvas-src` where the two disagreed.

18 files differed. Neither copy was a superset.

## Repo wins (kept as-is)

| File | Hunk | Why repo wins |
|---|---|---|
| `cmp_CommandBar`, `cmp_Dialog`, `cmp_Header`, `cmp_Navigation`, `cmp_Notification` | `Default: =` → `Default: =false` | `Default: =` is an empty value on a Boolean input |
| `cmp_FilterButton` | `Default: =Align.Center` → `="Center"` + `Switch` mapping | The input is `DataType: Text`; installed passed an enum into a text input. The inner control is a `Button`, so the Switch correctly maps to `Align.*` |
| `cmp_Navigation` | `ThisItem.LogicalName` → `ThisItem.Screen.Name` | The repo registry `constScreens` uses `Screen:` references, not `LogicalName:` strings. Installed's form would not resolve against this schema. (Ground truth uses a `LogicalName` string registry — a different, also-valid design; it does not arbitrate here.) |
| `cmp_Spinner` | Requires-comment drops `constPrimaryColor` | The component only references `constScrimColor` |
| `check_tokens.py` | `Radius\w*` → `\w*Radius\w*` | Strictly broader; now catches `BorderRadius` |
| `component-library.md` | `check_references.py` invocation examples | Repo documents both the inlined-token and separate-fragment cases |
| `FormScreen.pa.yaml` | `Weight:` → `FontWeight:` (×3) | Correct for `ModernText` |
| `FormScreen.pa.yaml` | `Value: ="Value"` removed | No `Value` property on `ModernCombobox` |
| `ListScreen.pa.yaml` | `Value: ="Value"` removed; `FontColor:` → `Color:` (×3) | Correct for `ModernCombobox` / `ModernText` |
| `ListScreen.pa.yaml` | `Align: =Align.Right` → `="Right"` | Passing to `cmp_FilterButton`, whose input is `DataType: Text` |
| `design-system.md` | `funcStatusColor` → `funcStatusTextColor` | Matches the actual function name in templates |
| `README.md` | 74 → 224 lines | Repo is a substantial expansion |

## Installed wins (ported to repo)

| File | Hunk | Why installed wins |
|---|---|---|
| `cmp_Header.pa.yaml:216` | `Align: =Align.Center` → `='TextCanvas.Align'.Center` | `lbl_Header_Badge` is a `ModernText`. Ground truth uses `'TextCanvas.Align'.*` on all text controls. The repo regressed this by applying the false SKILL.md rule corrected in Task 1. |

## Both wrong (rewritten in Task 1)

| File | Why |
|---|---|
| `SKILL.md` | Repo added a false rule (`ModernText` takes `Align.Left`); installed's older text was also imprecise |
| `references/powerfx-limits.md` | Same false rule |

## Note

`Align.Center` on a `ModernText` compiles — `Center` is the one member shared by both
namespaces — so the repo's regression was latent, not fatal. `Align.Right` on a text
control (see `design-tokens.pa.yaml`, fixed in Task 3) is a hard error, because
`'TextCanvas.Align'` has no `Right`.
```

- [ ] **Step 3: Port the one installed-side win**

In `components/cmp_Header.pa.yaml`, line 216, inside `lbl_Header_Badge` (`Control: ModernText`):

```yaml
                  Align: ='TextCanvas.Align'.Center
```

replacing `Align: =Align.Center`.

- [ ] **Step 4: Verify the port and that no other ModernText carries a plain Align**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
grep -n "Align:" components/cmp_Header.pa.yaml
```

Expected: `lbl_Header_Badge` shows `='TextCanvas.Align'.Center`; the `btn_Header_*` Button entries still show `=Align.Center` (correct for buttons).

- [ ] **Step 5: Run the existing four guards to confirm nothing regressed**

```bash
python3 scripts/check_references.py --src templates --tokens-file templates/design-tokens.pa.yaml --extra-dirs ../components 2>&1 | tail -3
python3 scripts/check_tokens.py --src templates 2>&1 | tail -3
```

Expected: both still behave as before this task (any pre-existing failures are unchanged — this task must not add new ones).

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/components/cmp_Header.pa.yaml \
        docs/superpowers/notes/2026-09-07-drift-reconciliation.md
git commit -m "fix: port ModernText Align from installed copy, document drift reconciliation

18 files differed bidirectionally between repo and installed skill copies.
Repo declared canonical; cmp_Header's lbl_Header_Badge was the single
installed-side win. Full verdict table with evidence in docs/superpowers/notes/."
```

---

### Task 3: Fix the five remaining live defects

Defect 3 (`HintText`), 4 (`Format`), 6 (Gallery `FillPortions`), 7 (`Clear(colItems)`), and 8 (token `Align.Right`). Fixed before the guard exists so its first clean run is a real signal.

**Files:**
- Modify: `templates/ListScreen.pa.yaml:103` (HintText), `:188` (Gallery), `:249` (token consumer)
- Modify: `templates/FormScreen.pa.yaml:115-117` (token consumer, Format)
- Modify: `templates/design-tokens.pa.yaml:119,127,140,151` (dual Align fields)
- Modify: `templates/App.pa.yaml:90` (Clear)

**Interfaces:**
- Consumes: Task 1's dialect table.
- Produces: `constStyle.Label.*.AlignModern` / `.AlignLegacy` token fields, consumed by Task 6's resolver tests.

- [ ] **Step 1: Fix `HintText` → `Placeholder`**

`templates/ListScreen.pa.yaml:103`, inside `txt_List_Search` (`Control: ModernTextInput`):

```yaml
                              Placeholder: ="Search"
```

- [ ] **Step 2: Add dual Align fields to the design tokens**

In `templates/design-tokens.pa.yaml`, replace each of the four `Align:` lines. `TextLabel` (line 119) and `TextInput` (line 127):

```
            AlignModern: 'TextCanvas.Align'.Start,
            AlignLegacy: Align.Left,
```

`NumberInput` (line 140):

```
            AlignModern: 'TextCanvas.Align'.End,
            AlignLegacy: Align.Right,
```

The group at line 151:

```
        AlignModern: 'TextCanvas.Align'.Center,
        AlignLegacy: Align.Center,
```

Add a comment above the `NumberInput` group explaining the split:

```
        // Alignment splits by control family: text controls take
        // 'TextCanvas.Align'.{Start|Center|End}, Buttons take Align.{Left|Center|Right}.
        // Two fields, because one token cannot serve both. See
        // references/control-dialects.md.
```

- [ ] **Step 3: Point both token consumers at the modern field**

`templates/ListScreen.pa.yaml:249` (`lbl_Row_Amount`, a `ModernText`) and `templates/FormScreen.pa.yaml:115` (a `ModernTextInput`):

```yaml
                                    Align: =constStyle.Label.NumberInput.AlignModern
```

- [ ] **Step 4: Remove the `Format` property**

Delete `templates/FormScreen.pa.yaml:117` entirely:

```yaml
                        Format: =TextFormat.Number
```

`ModernTextInput` has no `Format`. The field stays a text input, right-aligned by the token from Step 3, parsed with `Value()` at the save site. Add a comment in its place:

```yaml
                        # ModernTextInput has no Format property (that is the classic
                        # TextInput). Numeric entry stays a text input: right-aligned
                        # via the token above, parsed with Value() in funcSaveItem.
```

- [ ] **Step 5: Give the Gallery an explicit FillPortions**

`templates/ListScreen.pa.yaml`, in the `gal_List_Items` `Properties:` block (alphabetical order — after `BorderColor`, before `Items`):

```yaml
                        # Gallery is a leaf control: inside an auto-layout container it
                        # defaults to FillPortions 0 and collapses to the ~200px control
                        # default. This line is what makes the grid fill the screen.
                        FillPortions: =1
```

- [ ] **Step 6: Remove the bare Clear that empties every scaffolded app**

`templates/App.pa.yaml:90`. Delete the line `Clear(colItems);`. The `ClearCollect(colItems, Table({…}))` above it must remain — that seeded row is what makes the app render data on first run. Replace with a comment:

```
          // NOTE: no Clear() here. The seeded rows above are the mock data and
          // must survive: clearing them is what made every scaffolded app render
          // an empty grid. Seed-then-clear is correct ONLY for the framework
          // collections (colFilters, colSorts, colBack, colNotifications), where
          // a typed schema with no rows is genuinely wanted.
```

- [ ] **Step 7: Verify all five fixes landed and no defect text survives**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
echo "--- must be EMPTY ---"
grep -rn "HintText\|Format: =TextFormat\|Value: =\"Value\"" templates/ components/
grep -n "^          Clear(colItems);" templates/App.pa.yaml
grep -n "NumberInput.Align$" templates/ListScreen.pa.yaml templates/FormScreen.pa.yaml
echo "--- must be PRESENT ---"
grep -n "Placeholder: =\"Search\"" templates/ListScreen.pa.yaml
grep -n "FillPortions: =1" templates/ListScreen.pa.yaml
grep -n "AlignModern" templates/design-tokens.pa.yaml templates/ListScreen.pa.yaml templates/FormScreen.pa.yaml
```

Expected: first group prints nothing; second group prints hits in every listed file.

- [ ] **Step 8: Confirm the scaffolder still produces a guard-clean tree**

```bash
python3 scripts/new_app.py --name "Drift Check" --brand "#300091" --out /tmp/driftcheck
echo "exit=$?"
grep -n "Clear(colItems)" /tmp/driftcheck/App.pa.yaml || echo "OK: no bare Clear in output"
grep -n "FillPortions: =1" /tmp/driftcheck/ListScreen.pa.yaml
```

Expected: exit 0, all four guards PASS, no bare `Clear(colItems)`, Gallery has `FillPortions: =1`.

- [ ] **Step 9: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/templates/
git commit -m "fix: five live control-contract defects in scaffolder templates

- HintText -> Placeholder on ModernTextInput (HintText is classic-only)
- drop Format: =TextFormat.Number (no such property on ModernTextInput)
- Gallery gains FillPortions: =1 (leaf control, was collapsing to ~200px)
- drop Clear(colItems) after seeding — this rendered every scaffolded app empty
- design tokens split Align into AlignModern/AlignLegacy; a single field cannot
  serve both dialects, and Align.Right on a ModernText is a hard compile error"
```

---

### Task 4: Author `references/control-contracts.yaml`

**Files:**
- Create: `references/control-contracts.yaml`
- Create: `tests/test_contracts_wellformed.py`

**Interfaces:**
- Consumes: Task 1's dialect table.
- Produces: the contract file, loaded by `check_control_props.py` via `load_contracts(path) -> dict`. Top-level keys: `enums` (namespace → member list) and `controls` (control name → `{generation, properties, enums, renamed_from, removed, requires_one_of}`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_contracts_wellformed.py`:

```python
"""The contract file is data other code trusts. Verify its shape before trusting it."""
import pathlib
import unittest

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[1]
CONTRACTS = SKILL / "references" / "control-contracts.yaml"


class TestContractsWellFormed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CONTRACTS.open(encoding="utf-8") as fh:
            cls.data = yaml.safe_load(fh)

    def test_has_enums_and_controls(self):
        self.assertIn("enums", self.data)
        self.assertIn("controls", self.data)

    def test_expected_controls_present(self):
        for name in ("ModernText", "Text", "ModernTextInput", "ModernCombobox",
                     "ModernDatePicker", "Button", "Gallery"):
            self.assertIn(name, self.data["controls"], name)

    def test_every_enum_reference_resolves(self):
        """A control naming an enum namespace that isn't defined is a silent hole."""
        for control, spec in self.data["controls"].items():
            for prop, ns in (spec.get("enums") or {}).items():
                self.assertIn(ns, self.data["enums"],
                              "%s.%s -> undefined namespace %s" % (control, prop, ns))

    def test_enum_typed_properties_are_declared_properties(self):
        for control, spec in self.data["controls"].items():
            props = set(spec.get("properties") or [])
            for prop in (spec.get("enums") or {}):
                self.assertIn(prop, props,
                              "%s: enum-typed %s missing from properties" % (control, prop))

    def test_renamed_targets_are_valid_properties(self):
        for control, spec in self.data["controls"].items():
            props = set(spec.get("properties") or [])
            for old, new in (spec.get("renamed_from") or {}).items():
                targets = new if isinstance(new, list) else [new]
                for t in targets:
                    self.assertIn(t, props,
                                  "%s: %s renames to unknown %s" % (control, old, t))
                self.assertNotIn(old, props,
                                 "%s: %s is both renamed-away and valid" % (control, old))

    def test_align_namespaces_match_ground_truth(self):
        """Both text generations take 'TextCanvas.Align'; Button takes plain Align."""
        c = self.data["controls"]
        self.assertEqual(c["ModernText"]["enums"]["Align"], "TextCanvas.Align")
        self.assertEqual(c["Text"]["enums"]["Align"], "TextCanvas.Align")
        self.assertEqual(c["ModernTextInput"]["enums"]["Align"], "TextCanvas.Align")
        self.assertEqual(c["Button"]["enums"]["Align"], "Align")

    def test_center_is_the_only_shared_align_member(self):
        plain = set(self.data["enums"]["Align"])
        canvas = set(self.data["enums"]["TextCanvas.Align"])
        self.assertEqual(plain & canvas, {"Center"})

    def test_known_absent_properties_are_absent(self):
        c = self.data["controls"]
        self.assertNotIn("HintText", c["ModernTextInput"]["properties"])
        self.assertNotIn("Format", c["ModernTextInput"]["properties"])
        self.assertNotIn("Value", c["ModernCombobox"]["properties"])
        self.assertNotIn("ShowScrollbar", c["Gallery"]["properties"])
        self.assertNotIn("Color", c["Button"]["properties"])
        self.assertNotIn("Fill", c["Button"]["properties"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
python3 -m unittest tests.test_contracts_wellformed -v
```

Expected: FAIL — `references/control-contracts.yaml` does not exist.

- [ ] **Step 3: Write `references/control-contracts.yaml`**

Namespace keys are written without surrounding quotes in the `enums` map (`TextCanvas.Align`, not `'TextCanvas.Align'`); the guard strips quotes from YAML source before lookup.

```yaml
# Machine-readable control contracts. Read by scripts/check_control_props.py and,
# from Phase 2, by the generator's emitter — one source of truth, so generated
# output cannot contain a property the guard would reject.
#
# Prose version and the reasoning: references/control-dialects.md
#
# Provenance: seeded from Microsoft Learn, reconciled against the provably-compiled
# app at /Users/krystofpe/powerapps-work/canvas-src. Where they disagreed, the
# compiled app won.
#
# COVERAGE LIMIT: absence from this file means "not verified", not "invalid".
# check_control_props.py reports properties on unlisted controls as unchecked.

enums:
  Align: [Left, Center, Right, Justify]
  TextCanvas.Align: [Start, Center, End]
  FontWeight: [Bold, Semibold, Normal, Lighter]
  TextCanvas.Weight: [Bold, Regular]
  ButtonCanvas.Appearance: [Primary, Secondary, Outline, Subtle, Transparent]
  ButtonCanvas.Layout: [IconBefore, IconAfter, IconOnly, TextOnly]
  ButtonCanvas.IconStyle: [Filled, Regular]
  TextInputType: [SingleLine, Multiline, Password, Search]
  TriggerOutput: [Keypress, FocusOut, Delayed]
  Appearance: [FilledDarker, FilledLighter, Outline]
  VerticalAlign: [Top, Middle, Bottom]
  BorderStyle: [None, Solid, Dashed, Dotted]
  LayoutDirection: [Horizontal, Vertical]
  DisplayMode: [Edit, View, Disabled]

controls:

  ModernText:
    generation: modern
    properties:
      - Color, Size, FontWeight, Align, Wrap, AutoHeight, Text, Visible, OnSelect
      - Italic, Underline, Strikethrough
      - PaddingTop, PaddingBottom, PaddingLeft, PaddingRight
      - RadiusTopLeft, RadiusTopRight, RadiusBottomLeft, RadiusBottomRight
      - Fill, BorderColor, BorderThickness, BorderStyle
      - AlignInContainer, FillPortions, Height, Width, X, Y
      - AccessibleLabel, TabIndex, Live
    enums:
      FontWeight: FontWeight
      Align: TextCanvas.Align
      BorderStyle: BorderStyle
    renamed_from:
      FontColor: Color
      FontSize: Size
      Weight: FontWeight
      FontItalic: Italic
      FontUnderline: Underline
      FontStrikethrough: Strikethrough
      BorderRadius: [RadiusTopLeft, RadiusTopRight, RadiusBottomLeft, RadiusBottomRight]
    removed: [DisplayMode]

  Text:
    generation: previous
    note: >-
      Previous-generation modern text. Still valid, a DIFFERENT control from
      ModernText — not a version of it.
    properties:
      - FontColor, Size, Weight, Align, VerticalAlign, AutoHeight, Text, Visible, OnSelect
      - Fill, BorderColor, BorderThickness, BorderStyle
      - PaddingTop, PaddingBottom, PaddingLeft, PaddingRight
      - AlignInContainer, FillPortions, Height, Width, X, Y
      - AccessibleLabel, TabIndex, DisplayMode
    enums:
      Weight: TextCanvas.Weight
      Align: TextCanvas.Align
      VerticalAlign: VerticalAlign
      BorderStyle: BorderStyle
      DisplayMode: DisplayMode

  ModernTextInput:
    generation: modern
    note: >-
      No HintText (classic TextInput only) and no Format (also classic). For numeric
      entry keep it a text input, right-align via the token, parse with Value().
      OnChange fires on BLUR, not per keystroke.
    properties:
      - Placeholder, Default, Text, Type, TriggerOutput, MaxLength, Required
      - ValidationState, Appearance, Color, Size, FontWeight, Align
      - RadiusTopLeft, RadiusTopRight, RadiusBottomLeft, RadiusBottomRight
      - AccessibleLabel, OnChange, OnSelect, DisplayMode, BasePaletteColor
      - AlignInContainer, FillPortions, Height, Width, X, Y, Visible, TabIndex
    enums:
      Type: TextInputType
      TriggerOutput: TriggerOutput
      Appearance: Appearance
      FontWeight: FontWeight
      Align: TextCanvas.Align
      DisplayMode: DisplayMode
    renamed_from:
      HintText: Placeholder

  ModernCombobox:
    generation: modern
    note: >-
      SelectMultiple DEFAULTS TO TRUE — set it false explicitly for single-select.
      InputTextPlaceholder's factory default is the literal "Find items".
      Outputs: SelectedItems, Selected, SearchText. There is NO Value property.
    properties:
      - Items, ItemDisplayText, DefaultSelectedItems, InputTextPlaceholder
      - SelectMultiple, IsSearchable, MultiValueDelimiter, DelayOutput
      - Required, ValidationState, Appearance, Color, Size
      - AccessibleLabel, TabIndex, OnChange, DisplayMode, Visible
      - AlignInContainer, FillPortions, Height, Width, X, Y
    enums:
      Appearance: Appearance
      DisplayMode: DisplayMode
    renamed_from:
      Fields: ItemDisplayText
      TriggerOutput: DelayOutput

  ModernDatePicker:
    generation: modern
    properties:
      - DefaultDate, SelectedDate, Format, DateTimeZone, StartDate, EndDate
      - StartOfWeek, IsEditable, Placeholder, Appearance
      - RadiusTopLeft, RadiusTopRight, RadiusBottomLeft, RadiusBottomRight
      - ValidationState, AccessibleLabel, OnChange, DisplayMode, Visible
      - AlignInContainer, FillPortions, Height, Width, X, Y, TabIndex
    enums:
      Appearance: Appearance
      DisplayMode: DisplayMode

  Button:
    generation: previous
    note: >-
      Previous-generation modern button — what this skill's eight bundled components
      use. Takes the PLAIN Align enum, unlike the text controls. No Color, no Fill.
    properties:
      - FontColor, FontSize, BorderRadius, BorderThickness, BorderColor
      - BasePaletteColor, Icon, Appearance, Layout, IconStyle, Align
      - Text, AccessibleLabel, TabIndex, DisplayMode, OnSelect, Visible
      - AlignInContainer, FillPortions, Height, Width, X, Y
    enums:
      Appearance: ButtonCanvas.Appearance
      Layout: ButtonCanvas.Layout
      IconStyle: ButtonCanvas.IconStyle
      Align: Align
      DisplayMode: DisplayMode
    absent: [Color, Fill]

  ModernButton@1.0.0:
    generation: updated
    note: A different control again, per Learn. Not used by this skill's components.
    properties:
      - Color, Size, Text, Icon, IconStyle, Appearance, Layout, Tooltip
      - RadiusTopLeft, RadiusTopRight, RadiusBottomLeft, RadiusBottomRight
      - AccessibleLabel, TabIndex, DisplayMode, OnSelect, Visible
      - AlignInContainer, FillPortions, Height, Width, X, Y
    enums:
      DisplayMode: DisplayMode

  Gallery:
    generation: modern
    note: >-
      LEAF CONTROL. Inside an auto-layout container it defaults to FillPortions 0 and
      collapses to the ~200px control default — always set FillPortions or an explicit
      Height. No ShowScrollbar (classic only).
    properties:
      - Items, TemplateSize, TemplatePadding, Transition, WrapCount
      - DelayItemLoading, LoadingSpinner, LoadingSpinnerColor
      - BorderColor, BorderThickness, BorderStyle
      - AccessibleLabel, TabIndex, Visible, FillPortions
      - LayoutDirection, LayoutGap, LayoutJustifyContent, LayoutAlignItems
      - LayoutMinHeight, LayoutMinWidth, LayoutOverflowX, LayoutOverflowY
      - Height, Width, X, Y, AlignInContainer, Default, Selectable, ShowNavigation
    enums:
      BorderStyle: BorderStyle
      LayoutDirection: LayoutDirection
    absent: [ShowScrollbar]
    requires_one_of: [FillPortions, Height]
```

Note the `properties` lists use comma-joined strings on each line for readability. The loader in Task 5 flattens and splits on commas.

- [ ] **Step 4: Run the test to verify it passes**

```bash
python3 -m unittest tests.test_contracts_wellformed -v
```

Expected: FAIL initially — `test_expected_controls_present` and others will pass, but the comma-joined `properties` lists mean membership tests like `assertNotIn("HintText", ...)` behave oddly. Fix by normalizing in the test loader: add to `setUpClass`, after loading,

```python
        for spec in cls.data["controls"].values():
            flat = []
            for entry in spec.get("properties") or []:
                flat.extend(p.strip() for p in entry.split(",") if p.strip())
            spec["properties"] = flat
```

Re-run. Expected: OK, 8 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/references/control-contracts.yaml \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_contracts_wellformed.py
git commit -m "feat: machine-readable control contracts for 8 controls

Single source of truth read by the contract guard now and the Phase 2
generator later. Seeded from Learn, reconciled against a compiled app.
Well-formedness tests assert every enum reference resolves and that the
known-absent properties (HintText, Format, Value, ShowScrollbar) stay absent."
```

---

### Task 5: `check_control_props.py` — Layer 1, direct property checking

**Files:**
- Create: `scripts/check_control_props.py`
- Create: `tests/test_control_props_direct.py`
- Create: `tests/fixtures/` (fixture `.pa.yaml` files written by the tests)

**Interfaces:**
- Consumes: `references/control-contracts.yaml` from Task 4.
- Produces:
  - `load_contracts(path=None) -> dict` — normalized: `properties` flattened to a `set`, enum namespaces resolved.
  - `iter_properties(text, filename) -> Iterator[PropSite]` where `PropSite` is a `namedtuple("PropSite", "file line control control_type prop value")`.
  - `check_text(text, filename, contracts) -> List[Finding]` where `Finding` is `namedtuple("Finding", "severity file line control prop message")`; `severity` is `"error"` or `"warn"`.
  - CLI: `python3 check_control_props.py --src <dir> [--contracts <path>] [--quiet]`, exit 1 on any error-severity finding.

- [ ] **Step 1: Write the failing test**

Create `tests/test_control_props_direct.py`:

```python
"""Layer 1: direct property checking with indentation-tracked control context."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402


def errors(findings):
    return [f for f in findings if f.severity == "error"]


def warns(findings):
    return [f for f in findings if f.severity == "warn"]


class TestParsing(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()

    def test_tracks_enclosing_control(self):
        text = (
            "Screens:\n"
            "  ListScreen:\n"
            "    Children:\n"
            "      - lbl_A:\n"
            "          Control: ModernText\n"
            "          Properties:\n"
            "            Color: =RGBA(0,0,0,1)\n"
            "      - btn_B:\n"
            "          Control: Button\n"
            "          Properties:\n"
            "            FontColor: =RGBA(0,0,0,1)\n"
        )
        sites = list(ccp.iter_properties(text, "t.pa.yaml"))
        by_prop = {s.prop: s.control_type for s in sites}
        self.assertEqual(by_prop["Color"], "ModernText")
        self.assertEqual(by_prop["FontColor"], "Button")

    def test_multiline_block_body_is_not_parsed_as_properties(self):
        """A `|-` block's body must not be mistaken for property lines."""
        text = (
            "      - gal_X:\n"
            "          Control: Gallery\n"
            "          Properties:\n"
            "            FillPortions: =1\n"
            "            Items: |-\n"
            "              =Filter(\n"
            "                  colItems,\n"
            "                  Status: \"Open\"\n"
            "              )\n"
            "            TabIndex: =0\n"
        )
        props = [s.prop for s in ccp.iter_properties(text, "t.pa.yaml")]
        self.assertEqual(props, ["FillPortions", "Items", "TabIndex"])
        self.assertNotIn("Status", props)


class TestRenamedProperties(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()

    def _check(self, control, prop, value="=1"):
        text = (
            "      - c1:\n"
            "          Control: %s\n"
            "          Properties:\n"
            "            %s: %s\n" % (control, prop, value)
        )
        return ccp.check_text(text, "t.pa.yaml", self.contracts)

    def test_defect_1_fontcolor_on_moderntext(self):
        f = errors(self._check("ModernText", "FontColor", "=RGBA(0,0,0,1)"))
        self.assertEqual(len(f), 1)
        self.assertIn("Color", f[0].message)

    def test_defect_2_weight_on_moderntext(self):
        f = errors(self._check("ModernText", "Weight", "=FontWeight.Bold"))
        self.assertEqual(len(f), 1)
        self.assertIn("FontWeight", f[0].message)

    def test_defect_3_hinttext_on_moderntextinput(self):
        f = errors(self._check("ModernTextInput", "HintText", '="Search"'))
        self.assertEqual(len(f), 1)
        self.assertIn("Placeholder", f[0].message)

    def test_defect_4_format_on_moderntextinput(self):
        f = errors(self._check("ModernTextInput", "Format", "=TextFormat.Number"))
        self.assertEqual(len(f), 1)

    def test_defect_5_value_on_moderncombobox(self):
        f = errors(self._check("ModernCombobox", "Value", '="Value"'))
        self.assertEqual(len(f), 1)

    def test_valid_properties_produce_no_findings(self):
        self.assertEqual(errors(self._check("ModernText", "Color", "=RGBA(0,0,0,1)")), [])
        self.assertEqual(errors(self._check("Text", "FontColor", "=RGBA(0,0,0,1)")), [])
        self.assertEqual(errors(self._check("Text", "Weight", "='TextCanvas.Weight'.Bold")), [])


class TestEnumNamespaces(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()

    def _check(self, control, prop, value):
        text = (
            "      - c1:\n"
            "          Control: %s\n"
            "          Properties:\n"
            "            %s: %s\n" % (control, prop, value)
        )
        return ccp.check_text(text, "t.pa.yaml", self.contracts)

    def test_align_right_on_moderntext_is_an_error(self):
        """Right does not exist in 'TextCanvas.Align' — the member is End."""
        f = errors(self._check("ModernText", "Align", "=Align.Right"))
        self.assertEqual(len(f), 1)
        self.assertIn("End", f[0].message)

    def test_align_center_on_moderntext_is_only_a_warning(self):
        """Center is shared by both namespaces, so it compiles. Vendors.pa.yaml:133
        in the reference app does exactly this and shipped."""
        findings = self._check("ModernText", "Align", "=Align.Center")
        self.assertEqual(errors(findings), [])
        self.assertEqual(len(warns(findings)), 1)

    def test_correct_namespaces_are_clean(self):
        self.assertEqual(errors(self._check("ModernText", "Align", "='TextCanvas.Align'.End")), [])
        self.assertEqual(errors(self._check("Text", "Align", "='TextCanvas.Align'.Start")), [])
        self.assertEqual(errors(self._check("Button", "Align", "=Align.Right")), [])

    def test_nonexistent_member_in_correct_namespace_is_an_error(self):
        f = errors(self._check("ModernText", "Align", "='TextCanvas.Align'.Right"))
        self.assertEqual(len(f), 1)


class TestLeafControls(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()

    def test_defect_6_gallery_without_fillportions_or_height(self):
        text = (
            "      - gal_X:\n"
            "          Control: Gallery\n"
            "          Properties:\n"
            "            Items: =colItems\n"
        )
        f = errors(ccp.check_text(text, "t.pa.yaml", self.contracts))
        self.assertEqual(len(f), 1)
        self.assertIn("FillPortions", f[0].message)

    def test_gallery_with_fillportions_is_clean(self):
        text = (
            "      - gal_X:\n"
            "          Control: Gallery\n"
            "          Properties:\n"
            "            FillPortions: =1\n"
            "            Items: =colItems\n"
        )
        self.assertEqual(errors(ccp.check_text(text, "t.pa.yaml", self.contracts)), [])


class TestUnknownControlsAreUnchecked(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()

    def test_unlisted_control_is_reported_unchecked_not_failed(self):
        text = (
            "      - x1:\n"
            "          Control: SomeFutureControl\n"
            "          Properties:\n"
            "            Whatever: =1\n"
        )
        findings = ccp.check_text(text, "t.pa.yaml", self.contracts)
        self.assertEqual(errors(findings), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
python3 -m unittest tests.test_control_props_direct -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'check_control_props'`.

- [ ] **Step 3: Write `scripts/check_control_props.py` (Layer 1)**

```python
#!/usr/bin/env python3
"""Guard: control properties match their control's contract.

The four architectural guards check where logic lives. None of them checks whether
a property name exists on the control it is written under, which is how a tree can
pass every guard and still fail to compile.

There is no offline compile for Canvas Apps (`pac canvas pack` is deprecated and
crashes; `pac canvas validate` rejects every file of a working published app), so
this static check is the only pre-push signal.

    python3 check_control_props.py --src path/to/Src
    python3 check_control_props.py --src path/to/Src --contracts other-contracts.yaml

Exits non-zero on any error-severity finding. Warnings do not fail the run.

COVERAGE LIMITS — this guard does NOT check:
  * property VALUES beyond enum-namespace membership (no type or formula checking)
  * controls absent from references/control-contracts.yaml (reported as unchecked)
  * values it cannot resolve statically (If()/Switch()/ThisItem — counted, reported)
  * layout correctness beyond the leaf-control size rule (see check_layout.py)
  * anything only a live compile_canvas run can catch
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONTRACTS = SKILL / "references" / "control-contracts.yaml"

PropSite = collections.namedtuple(
    "PropSite", "file line control control_type component_name prop value")
Finding = collections.namedtuple(
    "Finding", "severity file line control prop message")

RE_ITEM = re.compile(r"^(\s*)- ([A-Za-z_][\w@.]*):\s*$")
RE_KEY = re.compile(r"^(\s*)([A-Za-z_][\w@.]*):\s*(.*)$")
RE_ENUM = re.compile(r"^=\s*'?([A-Za-z][\w.]*?)'?\.([A-Za-z]\w*)\s*$")
BLOCK_SCALAR = ("|", "|-", "|+", ">", ">-", ">+")


def load_contracts(path=None):
    """Load and normalize the contract file.

    `properties` entries may be comma-joined strings for readability; flatten them
    into a set. Returns the dict with `properties` as sets.
    """
    path = pathlib.Path(path) if path else DEFAULT_CONTRACTS
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    for spec in data["controls"].values():
        flat = set()
        for entry in spec.get("properties") or []:
            flat.update(p.strip() for p in str(entry).split(",") if p.strip())
        spec["properties"] = flat
        spec["absent"] = set(spec.get("absent") or [])
        spec["removed"] = set(spec.get("removed") or [])
        spec["renamed_from"] = spec.get("renamed_from") or {}
        spec["enums"] = spec.get("enums") or {}
    data["enums"] = {k: set(v) for k, v in data["enums"].items()}
    return data


def iter_properties(text, filename):
    """Yield a PropSite per property line, tracking the enclosing control.

    Control blocks look like:

        - lbl_Row_Title:
            Control: ModernText
            Properties:
              Color: =...

    Multi-line block scalars (`Items: |-`) are consumed whole so their bodies are
    never mistaken for property lines.
    """
    lines = text.splitlines()
    control_name = control_type = component_name = None
    control_indent = -1
    props_indent = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())

        m = RE_ITEM.match(raw)
        if m:
            control_name = m.group(2)
            control_type = component_name = None
            control_indent = len(m.group(1))
            props_indent = None
            continue

        m = RE_KEY.match(raw)
        if not m:
            continue
        key, value = m.group(2), m.group(3).strip()

        if key == "Control":
            control_type = value
            control_indent = indent
            props_indent = None
            continue
        if key == "ComponentName":
            component_name = value
            continue
        if key == "Properties":
            props_indent = indent
            continue
        if key == "Children":
            props_indent = None
            continue

        # Leaving the control's block entirely.
        if indent <= control_indent and props_indent is None:
            control_name = control_type = None
            continue

        if props_indent is None or indent != props_indent + 2:
            continue

        if value in BLOCK_SCALAR:
            body = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                    break
                body.append(nxt.strip())
                i += 1
            value = " ".join(body)

        yield PropSite(filename, i, control_name, control_type,
                       component_name, key, value)


def check_text(text, filename, contracts, resolver=None):
    """Return a list of Findings for one file's text.

    `resolver`, when given, maps a token reference like
    `constStyle.Label.NumberInput.AlignModern` to its literal value (Task 6).
    """
    findings = []
    seen_props = collections.defaultdict(set)
    controls_seen = {}

    for site in iter_properties(text, filename):
        if not site.control_type:
            continue
        if site.control_type == "CanvasComponent":
            continue  # Layer 3 (Task 7) handles these.
        spec = contracts["controls"].get(site.control_type)
        if spec is None:
            continue  # Unknown control: unchecked, not failed.

        controls_seen[(filename, site.control)] = site
        seen_props[(filename, site.control)].add(site.prop)

        prop = site.prop
        if prop in spec["renamed_from"]:
            new = spec["renamed_from"][prop]
            new = ", ".join(new) if isinstance(new, list) else new
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s has no %s — it was renamed to %s" % (site.control_type, prop, new)))
            continue
        if prop in spec["removed"]:
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s was removed from %s" % (prop, site.control_type)))
            continue
        if prop in spec["absent"]:
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s has no %s property" % (site.control_type, prop)))
            continue
        if prop not in spec["properties"]:
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s has no %s property" % (site.control_type, prop)))
            continue

        findings.extend(_check_enum(site, spec, contracts, resolver))

    # Leaf controls that must carry an explicit size.
    for key, site in controls_seen.items():
        spec = contracts["controls"].get(site.control_type)
        need = spec.get("requires_one_of") if spec else None
        if need and not (set(need) & seen_props[key]):
            findings.append(Finding(
                "error", site.file, site.line, site.control, need[0],
                "%s is a leaf control and needs one of %s — without it, it "
                "collapses to the control default"
                % (site.control_type, " or ".join(need))))
    return findings


def _check_enum(site, spec, contracts, resolver):
    expected_ns = spec["enums"].get(site.prop)
    if not expected_ns:
        return []
    value = site.value
    if resolver is not None and value.startswith("=const"):
        resolved = resolver(value[1:].strip())
        if resolved is None:
            return []  # Unresolved: reported separately as unchecked.
        value = "=" + resolved
    m = RE_ENUM.match(value)
    if not m:
        return []  # Not a literal enum reference — unchecked.
    actual_ns, member = m.group(1), m.group(2)
    if actual_ns == expected_ns:
        if member not in contracts["enums"].get(expected_ns, set()):
            return [Finding(
                "error", site.file, site.line, site.control, site.prop,
                "%s.%s is not a member of %s (valid: %s)"
                % (actual_ns, member, expected_ns,
                   ", ".join(sorted(contracts["enums"].get(expected_ns, ())))))]
        return []

    expected_members = contracts["enums"].get(expected_ns, set())
    if member in expected_members:
        return [Finding(
            "warn", site.file, site.line, site.control, site.prop,
            "%s takes %s, not %s — %s.%s compiles because %r is in both, but the "
            "tree is dialect-inconsistent"
            % (site.control_type, expected_ns, actual_ns, actual_ns, member, member))]
    return [Finding(
        "error", site.file, site.line, site.control, site.prop,
        "%s takes %s.{%s} — %s.%s does not exist there"
        % (site.control_type, expected_ns, "|".join(sorted(expected_members)),
           actual_ns, member))]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--contracts", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    contracts = load_contracts(args.contracts)
    src = pathlib.Path(args.src)
    files = sorted(p for p in src.rglob("*.pa.yaml") if p.name != "_EditorState.pa.yaml")

    findings = []
    for path in files:
        findings.extend(check_text(path.read_text(encoding="utf-8"),
                                   str(path), contracts))

    errs = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]

    if errs:
        print("FAIL: %d control-property violation(s).\n" % len(errs))
        for f in errs:
            print("  %s:%s  %s.%s\n      %s" % (f.file, f.line, f.control, f.prop, f.message))
        if warns:
            print("\n  plus %d dialect warning(s) — run without --quiet to see them"
                  % len(warns))
        print("\n  Contracts: %s\n  Prose: references/control-dialects.md"
              % (args.contracts or DEFAULT_CONTRACTS))
        sys.exit(1)

    for f in warns:
        print("  warn: %s:%s  %s.%s — %s" % (f.file, f.line, f.control, f.prop, f.message))

    print("PASS: control properties match their contracts (%d file(s) checked, "
          "%d warning(s))" % (len(files), len(warns)))
    print("  Not covered: property values beyond enum membership; controls absent "
          "from the contract file; unresolved expressions; layout; anything only a "
          "live compile_canvas catches.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_control_props_direct -v
```

Expected: OK. If `test_multiline_block_body_is_not_parsed_as_properties` fails, the block-scalar consumption in `iter_properties` is mis-indexed — the `while` loop must not consume the line that dedents.

- [ ] **Step 5: Run the guard against the real templates**

```bash
python3 scripts/check_control_props.py --src templates
python3 scripts/check_control_props.py --src components
```

Expected: PASS for both, because Tasks 2 and 3 fixed every error-severity defect. Any error here is a real defect those tasks missed — fix it and note it in the drift report.

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/check_control_props.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_control_props_direct.py
git commit -m "feat: control-contract guard, layer 1 (direct property checking)

Tracks the enclosing Control: by indentation, consumes block scalars whole,
and checks property names against references/control-contracts.yaml.

Severity is graded: a cross-namespace enum member that does not exist in the
target namespace is an error (Align.Right on ModernText); one that exists in
both is a warning (Align.Center), because the reference app ships that and
compiles. A flat rule would fail provably-working code."
```

---

### Task 6: Layer 2 — resolve design-token indirection

Without this the guard misses defect 8 entirely: `templates/design-tokens.pa.yaml` defined `Align: Align.Right` and a `ModernText` consumed it via `constStyle.Label.NumberInput.Align`. The wrong-namespace enum never appears on the screen line.

**Files:**
- Modify: `scripts/check_control_props.py` (add `parse_tokens`, wire `--tokens-file`, count unresolved)
- Create: `tests/test_control_props_tokens.py`

**Interfaces:**
- Consumes: Task 5's `check_text(..., resolver=)` parameter, already present.
- Produces: `parse_tokens(text) -> Dict[str, str]` mapping a dotted path (`constStyle.Label.NumberInput.AlignModern`) to its literal value (`'TextCanvas.Align'.End`). Also `make_resolver(mapping) -> Callable[[str], Optional[str]]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_control_props_tokens.py`:

```python
"""Layer 2: resolve constStyle.* token references before checking enum namespaces."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

TOKENS = """\
constStyle = {
    Label: {
        TextLabel: {
            AlignModern: 'TextCanvas.Align'.Start,
            AlignLegacy: Align.Left,
            PaddingLeft: 8
        },
        NumberInput: {
            AlignModern: 'TextCanvas.Align'.End,
            AlignLegacy: Align.Right,
            PaddingLeft: 8
        }
    },
    Button: {
        Height: {Large: 40, Medium: 32}
    }
};
"""


def errors(findings):
    return [f for f in findings if f.severity == "error"]


class TestTokenParsing(unittest.TestCase):
    def test_builds_dotted_paths(self):
        m = ccp.parse_tokens(TOKENS)
        self.assertEqual(m["constStyle.Label.NumberInput.AlignModern"],
                         "'TextCanvas.Align'.End")
        self.assertEqual(m["constStyle.Label.NumberInput.AlignLegacy"], "Align.Right")
        self.assertEqual(m["constStyle.Label.TextLabel.AlignModern"],
                         "'TextCanvas.Align'.Start")

    def test_inline_records_do_not_break_the_parser(self):
        m = ccp.parse_tokens(TOKENS)
        self.assertNotIn("constStyle.Button.Height.Large", m)
        self.assertIn("constStyle.Label.TextLabel.PaddingLeft", m)


class TestResolvedEnumChecking(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()
        self.resolver = ccp.make_resolver(ccp.parse_tokens(TOKENS))

    def _check(self, control, prop, value):
        text = (
            "      - c1:\n"
            "          Control: %s\n"
            "          Properties:\n"
            "            %s: %s\n" % (control, prop, value)
        )
        return ccp.check_text(text, "t.pa.yaml", self.contracts, resolver=self.resolver)

    def test_defect_8_wrong_namespace_laundered_through_a_token(self):
        """This is the case a line-oriented guard cannot see."""
        f = errors(self._check("ModernText", "Align",
                               "=constStyle.Label.NumberInput.AlignLegacy"))
        self.assertEqual(len(f), 1)
        self.assertIn("End", f[0].message)

    def test_correct_token_field_is_clean(self):
        self.assertEqual(
            errors(self._check("ModernText", "Align",
                               "=constStyle.Label.NumberInput.AlignModern")), [])

    def test_legacy_token_on_a_button_is_clean(self):
        self.assertEqual(
            errors(self._check("Button", "Align",
                               "=constStyle.Label.NumberInput.AlignLegacy")), [])

    def test_unknown_token_path_is_unresolved_not_an_error(self):
        self.assertEqual(
            errors(self._check("ModernText", "Align", "=constStyle.Nope.Missing")), [])


class TestRealTemplatesResolve(unittest.TestCase):
    def test_shipped_tokens_parse_and_the_templates_are_clean(self):
        tokens = (SKILL / "templates" / "design-tokens.pa.yaml").read_text(encoding="utf-8")
        mapping = ccp.parse_tokens(tokens)
        self.assertIn("constStyle.Label.NumberInput.AlignModern", mapping)
        resolver = ccp.make_resolver(mapping)
        contracts = ccp.load_contracts()
        for name in ("ListScreen.pa.yaml", "FormScreen.pa.yaml"):
            path = SKILL / "templates" / name
            f = errors(ccp.check_text(path.read_text(encoding="utf-8"),
                                      str(path), contracts, resolver=resolver))
            self.assertEqual(f, [], "%s: %s" % (name, f))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
python3 -m unittest tests.test_control_props_tokens -v
```

Expected: FAIL — `AttributeError: module 'check_control_props' has no attribute 'parse_tokens'`.

- [ ] **Step 3: Add the token parser and resolver**

Insert into `scripts/check_control_props.py`, after `load_contracts`:

```python
RE_TOKEN_OPEN = re.compile(r"^([A-Za-z_]\w*)\s*[:=]\s*\{\s*$")
RE_TOKEN_LEAF = re.compile(r"^([A-Za-z_]\w*)\s*:\s*(.+?),?\s*$")


def parse_tokens(text):
    """Parse a Power Fx token record into {dotted.path: literal}.

    Handles the one-key-per-line record style the skill's design-tokens file uses:

        constStyle = {
            Label: {
                NumberInput: {
                    AlignModern: 'TextCanvas.Align'.End,

    COVERAGE LIMIT: inline records (`Height: {Large: 40, Medium: 32}`) are recorded
    as opaque leaves, not descended into. Callers resolving a path below one get
    None and treat the site as unchecked rather than clean.
    """
    mapping = {}
    stack = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.endswith("};") or line == "}" or line == "},":
            if stack:
                stack.pop()
            continue
        m = RE_TOKEN_OPEN.match(line)
        if m:
            stack.append(m.group(1))
            continue
        m = RE_TOKEN_LEAF.match(line)
        if m and not m.group(2).startswith("{"):
            mapping[".".join(stack + [m.group(1)])] = m.group(2).rstrip(",").strip()
    return mapping


def make_resolver(mapping):
    """Return a resolver closing over a token map; unknown paths give None."""
    def resolve(path):
        return mapping.get(path)
    return resolve
```

- [ ] **Step 4: Wire `--tokens-file` into `main()`**

In `main()`, after `contracts = load_contracts(args.contracts)`:

```python
    resolver = None
    token_text = ""
    if args.tokens_file:
        token_text = pathlib.Path(args.tokens_file).read_text(encoding="utf-8")
    else:
        app = src / "App.pa.yaml"
        if app.exists():
            token_text = app.read_text(encoding="utf-8")
    if token_text:
        resolver = make_resolver(parse_tokens(token_text))
```

Add the argument alongside the others:

```python
    ap.add_argument("--tokens-file", default=None,
                    help="Power Fx fragment defining constStyle etc. "
                         "Defaults to <src>/App.pa.yaml, where new_app.py inlines them.")
```

and pass it through: `check_text(..., contracts, resolver=resolver)`.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_control_props_tokens -v
```

Expected: OK, 8 tests. `TestRealTemplatesResolve` passing is the proof that Task 3's token split is complete and both consumers point at `AlignModern`.

- [ ] **Step 6: Prove the guard now catches defect 8 end to end**

```bash
cp templates/ListScreen.pa.yaml /tmp/ls.bak
sed -i '' 's/NumberInput.AlignModern/NumberInput.AlignLegacy/' templates/ListScreen.pa.yaml
python3 scripts/check_control_props.py --src templates \
        --tokens-file templates/design-tokens.pa.yaml; echo "exit=$?"
cp /tmp/ls.bak templates/ListScreen.pa.yaml
```

Expected: `FAIL`, exit=1, message naming `'TextCanvas.Align'` and `End`. Then the restore returns the tree to clean.

- [ ] **Step 7: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/check_control_props.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_control_props_tokens.py
git commit -m "feat: control-contract guard, layer 2 (design-token resolution)

The token layer that makes this skill work is also a blind spot: a
wrong-namespace enum defined in design-tokens.pa.yaml and consumed through
constStyle.* never appears on the screen line. Resolve the path before
checking the namespace. Unresolvable paths count as unchecked, never clean."
```

---

### Task 7: Layer 3 — validate `CanvasComponent` instance properties

A `CanvasComponent` child's properties are custom component inputs, not control properties. Treating them as control properties false-positives on shipping code (the reference app's `cmp_Filter_*` instances). Validating them against the component's declared `CustomProperties` catches defect 9.

**Files:**
- Modify: `scripts/check_control_props.py`
- Create: `tests/test_control_props_components.py`

**Interfaces:**
- Consumes: Task 5's `check_text`.
- Produces: `parse_component_defs(paths) -> Dict[str, Dict[str, str]]` mapping component name → `{property_name: DataType}`. `check_text` gains a `components=` parameter.

- [ ] **Step 1: Write the failing test**

Create `tests/test_control_props_components.py`:

```python
"""Layer 3: CanvasComponent instance properties are custom inputs, not control props."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

COMPONENT_DEF = """\
ComponentDefinitions:
  cmp_FilterButton:
    DefinitionType: CanvasComponent
    AccessAppScope: true
    CustomProperties:
      Align:
        PropertyKind: Input
        DataType: Text
        Default: ="Center"
      Width:
        PropertyKind: Input
        DataType: Number
        Default: =140
      OnSort:
        PropertyKind: Event
"""


def errors(findings):
    return [f for f in findings if f.severity == "error"]


def instance(prop, value):
    return (
        "      - cmp_List_Head:\n"
        "          Control: CanvasComponent\n"
        "          ComponentName: cmp_FilterButton\n"
        "          Properties:\n"
        "            %s: %s\n" % (prop, value)
    )


class TestComponentDefParsing(unittest.TestCase):
    def test_extracts_declared_inputs_and_types(self):
        defs = ccp.parse_component_defs_text(COMPONENT_DEF)
        self.assertEqual(defs["cmp_FilterButton"]["Align"], "Text")
        self.assertEqual(defs["cmp_FilterButton"]["Width"], "Number")

    def test_parses_every_shipped_component(self):
        paths = sorted((SKILL / "components").glob("cmp_*.pa.yaml"))
        self.assertEqual(len(paths), 8)
        defs = ccp.parse_component_defs(paths)
        self.assertEqual(len(defs), 8)
        self.assertIn("Align", defs["cmp_FilterButton"])


class TestInstanceChecking(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()
        self.components = ccp.parse_component_defs_text(COMPONENT_DEF)

    def _check(self, text):
        return ccp.check_text(text, "t.pa.yaml", self.contracts,
                              components=self.components)

    def test_defect_9_enum_into_a_text_typed_input(self):
        f = errors(self._check(instance("Align", "=Align.Center")))
        self.assertEqual(len(f), 1)
        self.assertIn("Text", f[0].message)

    def test_string_into_a_text_typed_input_is_clean(self):
        self.assertEqual(errors(self._check(instance("Align", '="Center"'))), [])

    def test_number_into_a_number_typed_input_is_clean(self):
        self.assertEqual(errors(self._check(instance("Width", "=140"))), [])

    def test_undeclared_property_is_an_error(self):
        f = errors(self._check(instance("Nonexistent", "=1")))
        self.assertEqual(len(f), 1)

    def test_unknown_component_is_unchecked_not_failed(self):
        text = (
            "      - x:\n"
            "          Control: CanvasComponent\n"
            "          ComponentName: cmp_NotLoaded\n"
            "          Properties:\n"
            "            Whatever: =1\n"
        )
        self.assertEqual(errors(self._check(text)), [])

    def test_expression_into_a_text_input_is_unchecked(self):
        """Only bare enum literals are judged; formulas are left alone."""
        self.assertEqual(
            errors(self._check(instance("Align", '=If(x, "Left", "Right")'))), [])


class TestRealTreeIsClean(unittest.TestCase):
    def test_templates_against_shipped_components(self):
        contracts = ccp.load_contracts()
        components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        resolver = ccp.make_resolver(ccp.parse_tokens(
            (SKILL / "templates" / "design-tokens.pa.yaml").read_text(encoding="utf-8")))
        for path in sorted((SKILL / "templates").glob("*.pa.yaml")):
            f = errors(ccp.check_text(path.read_text(encoding="utf-8"), str(path),
                                      contracts, resolver=resolver,
                                      components=components))
            self.assertEqual(f, [], "%s: %s" % (path.name, f))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
python3 -m unittest tests.test_control_props_components -v
```

Expected: FAIL — no attribute `parse_component_defs_text`.

- [ ] **Step 3: Add the component-definition parser**

Insert into `scripts/check_control_props.py`:

```python
RE_CMP_NAME = re.compile(r"^(\s*)(cmp_[\w]+):\s*$")
RE_PROP_NAME = re.compile(r"^(\s*)([A-Za-z_]\w*):\s*$")
RE_DATATYPE = re.compile(r"^\s*DataType:\s*(\w+)\s*$")

# Bare enum literals that are NOT valid in a Text-typed component input.
RE_BARE_ENUM = re.compile(r"^=\s*'?([A-Za-z][\w.]*?)'?\.([A-Za-z]\w*)\s*$")


def parse_component_defs_text(text):
    """Map component name -> {input property name: DataType}.

    Only PropertyKind Input/Output properties carry a DataType; Events do not and
    are recorded with DataType None so an instance may still set them.
    """
    defs = {}
    current = None
    cmp_indent = None
    prop = None
    prop_indent = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        m = RE_CMP_NAME.match(raw)
        if m:
            current = m.group(2)
            cmp_indent = indent
            defs.setdefault(current, {})
            prop = None
            continue
        if current is None:
            continue
        if indent <= cmp_indent:
            current = None
            continue
        m = RE_DATATYPE.match(raw)
        if m and prop:
            defs[current][prop] = m.group(1)
            continue
        m = RE_PROP_NAME.match(raw)
        if m and m.group(2) not in ("CustomProperties", "Properties", "Children"):
            if prop_indent is None or indent == prop_indent:
                prop_indent = indent
                prop = m.group(2)
                defs[current].setdefault(prop, None)
    return defs


def parse_component_defs(paths):
    defs = {}
    for path in paths:
        defs.update(parse_component_defs_text(
            pathlib.Path(path).read_text(encoding="utf-8")))
    return defs
```

- [ ] **Step 4: Add instance checking to `check_text`**

Change the signature to `def check_text(text, filename, contracts, resolver=None, components=None):` and replace the early `continue` for `CanvasComponent`:

```python
        if site.control_type == "CanvasComponent":
            if components and site.component_name in components:
                findings.extend(_check_instance(site, components[site.component_name]))
            continue
```

Add the helper:

```python
TEXTY = {"Text": ("a quoted string",), "Number": ("a number",),
         "Boolean": ("true/false",)}


def _check_instance(site, declared):
    """Check one CanvasComponent instance property against its declaration."""
    if site.prop not in declared:
        return [Finding(
            "error", site.file, site.line, site.control, site.prop,
            "component %s declares no %s input (declared: %s)"
            % (site.component_name, site.prop,
               ", ".join(sorted(declared)) or "none"))]
    datatype = declared[site.prop]
    if datatype != "Text":
        return []
    m = RE_BARE_ENUM.match(site.value)
    if m:
        return [Finding(
            "error", site.file, site.line, site.control, site.prop,
            "%s.%s is DataType Text — pass the string \"%s\", not the enum %s.%s"
            % (site.component_name, site.prop, m.group(2), m.group(1), m.group(2)))]
    return []
```

- [ ] **Step 5: Wire components into `main()`**

After the resolver block:

```python
    comp_dirs = [src, src / "Components", SKILL / "components"]
    comp_paths = []
    for d in comp_dirs:
        if d.exists():
            comp_paths.extend(sorted(d.glob("cmp_*.pa.yaml")))
    components = parse_component_defs(comp_paths)
```

and pass `components=components` to `check_text`.

- [ ] **Step 6: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_control_props_components -v
```

Expected: OK, 9 tests.

- [ ] **Step 7: Run the full suite and the guard on the real tree**

```bash
python3 -m unittest discover -s tests -v 2>&1 | tail -5
python3 scripts/check_control_props.py --src templates \
        --tokens-file templates/design-tokens.pa.yaml
```

Expected: all tests OK; guard PASS.

- [ ] **Step 8: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/check_control_props.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_control_props_components.py
git commit -m "feat: control-contract guard, layer 3 (component instance properties)

A CanvasComponent child's properties are custom inputs, not control
properties — checking them as control properties false-positives on
shipping code. Validate against the component's declared CustomProperties
instead, which catches an enum passed into a DataType: Text input."
```

---

### Task 8: Nine-defect regression suite

Definition of Done item 4 requires proof the guard fails on each defect, not an assumption.

**Files:**
- Create: `tests/test_defect_regression.py`

**Interfaces:**
- Consumes: everything from Tasks 4–7.
- Produces: nothing consumed downstream; a gate.

- [ ] **Step 1: Write the test**

Create `tests/test_defect_regression.py`:

```python
"""Every defect that reached a live environment gets a test that reproduces it.

Six were live in the tree when this guard was written; three were already fixed
and are reintroduced synthetically. All nine must fail the guard.
"""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

TOKENS = (SKILL / "templates" / "design-tokens.pa.yaml").read_text(encoding="utf-8")


def control(ctype, props, name="c1", component=None):
    head = "      - %s:\n          Control: %s\n" % (name, ctype)
    if component:
        head += "          ComponentName: %s\n" % component
    head += "          Properties:\n"
    return head + "".join("            %s: %s\n" % (k, v) for k, v in props)


class TestNineDefectClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = ccp.load_contracts()
        cls.resolver = ccp.make_resolver(ccp.parse_tokens(TOKENS))
        cls.components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))

    def assertRejected(self, text, expect_in_message=None):
        findings = ccp.check_text(text, "t.pa.yaml", self.contracts,
                                  resolver=self.resolver, components=self.components)
        errs = [f for f in findings if f.severity == "error"]
        self.assertTrue(errs, "guard did not reject:\n%s" % text)
        if expect_in_message:
            joined = " ".join(f.message for f in errs)
            self.assertIn(expect_in_message, joined)

    def test_1_fontcolor_on_moderntext(self):
        self.assertRejected(
            control("ModernText", [("FontColor", "=RGBA(0,0,0,1)")]), "Color")

    def test_2_weight_on_moderntext(self):
        self.assertRejected(
            control("ModernText", [("Weight", "=FontWeight.Bold")]), "FontWeight")

    def test_3_hinttext_on_moderntextinput(self):
        self.assertRejected(
            control("ModernTextInput", [("HintText", '="Search"')]), "Placeholder")

    def test_4_format_on_moderntextinput(self):
        self.assertRejected(
            control("ModernTextInput", [("Format", "=TextFormat.Number")]))

    def test_5_value_on_moderncombobox(self):
        self.assertRejected(
            control("ModernCombobox", [("Value", '="Value"')]))

    def test_6_gallery_without_fillportions(self):
        self.assertRejected(
            control("Gallery", [("Items", "=colItems")]), "FillPortions")

    def test_8_wrong_namespace_via_token(self):
        self.assertRejected(
            control("ModernText",
                    [("Align", "=constStyle.Label.NumberInput.AlignLegacy")]), "End")

    def test_9_enum_into_text_typed_component_input(self):
        self.assertRejected(
            control("CanvasComponent", [("Align", "=Align.Center")],
                    component="cmp_FilterButton"), "Text")

    def test_direct_wrong_namespace_enum(self):
        self.assertRejected(
            control("ModernText", [("Align", "=Align.Right")]), "End")


class TestDefect7DataLayer(unittest.TestCase):
    """Defect 7 is a data-layer rule, not a control-property one."""

    def test_bare_clear_on_entity_collection_is_rejected(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        import check_data_layer as cdl
        text = (
            "      funcLoadItems(): Void =\n"
            "      {\n"
            "          ClearCollect(colItems, Table({Key: \"A|1\"}));\n"
            "          Clear(colItems);\n"
            "      };\n"
        )
        findings = cdl.check_bare_clear(text, "App.pa.yaml")
        self.assertTrue(findings, "bare Clear(colItems) after seeding not caught")

    def test_clear_on_framework_collections_is_allowed(self):
        import check_data_layer as cdl
        for col in ("colFilters", "colSorts", "colBack", "colNotifications"):
            text = "          Clear(%s);\n" % col
            self.assertEqual(cdl.check_bare_clear(text, "App.pa.yaml"), [], col)


class TestCleanTreeStaysClean(unittest.TestCase):
    """The guard must not cry wolf on the shipped tree."""

    def test_no_errors_in_templates_or_components(self):
        contracts = ccp.load_contracts()
        resolver = ccp.make_resolver(ccp.parse_tokens(TOKENS))
        components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        for d in ("templates", "components"):
            for path in sorted((SKILL / d).glob("*.pa.yaml")):
                errs = [f for f in ccp.check_text(
                    path.read_text(encoding="utf-8"), str(path), contracts,
                    resolver=resolver, components=components)
                    if f.severity == "error"]
                self.assertEqual(errs, [], "%s: %s" % (path.name, errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it — the data-layer tests must fail**

```bash
python3 -m unittest tests.test_defect_regression -v
```

Expected: the nine control-property tests PASS; `TestDefect7DataLayer` FAILS with `AttributeError: module 'check_data_layer' has no attribute 'check_bare_clear'`. That function is added in Task 9.

- [ ] **Step 3: Commit the suite**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_defect_regression.py
git commit -m "test: regression suite for all nine defect classes

Six were live in the tree; three were already fixed and are reintroduced
synthetically. Includes a cry-wolf test asserting the shipped tree stays
clean. Defect 7's data-layer test fails until check_bare_clear lands."
```

---

### Task 9: Bare-`Clear` rule, coverage limits on every guard, wire into `new_app.py`

**Files:**
- Modify: `scripts/check_data_layer.py` (add `check_bare_clear`, call it, extend PASS message)
- Modify: `scripts/check_tokens.py`, `scripts/check_references.py`, `scripts/check_collection_columns.py` (PASS messages)
- Modify: `scripts/new_app.py` (add the new guard to `checks`, replace "All checks pass")

**Interfaces:**
- Consumes: Task 8's expectations for `check_bare_clear(text, filename) -> List[tuple]`.
- Produces: `check_bare_clear`, used by `check_data_layer.main()` and the regression suite.

- [ ] **Step 1: Verify the regression test still fails**

```bash
python3 -m unittest tests.test_defect_regression.TestDefect7DataLayer -v
```

Expected: FAIL, no attribute `check_bare_clear`.

- [ ] **Step 2: Add `check_bare_clear` to `scripts/check_data_layer.py`**

```python
FRAMEWORK_COLLECTIONS = {"colFilters", "colSorts", "colBack", "colNotifications"}
RE_CLEAR = re.compile(r"\bClear\(\s*(col\w+)\s*\)")


def check_bare_clear(text, filename):
    """Flag Clear() on an entity collection.

    Seed-then-clear is correct ONLY for the framework collections, where a typed
    schema with no rows is genuinely wanted. On an entity collection it is what
    made every scaffolded app render an empty grid: the mock rows were seeded to
    establish the schema and then deleted.

    Use ClearCollect() to replace contents; a bare Clear() on an entity collection
    is almost always a leftover.
    """
    findings = []
    for n, raw in enumerate(text.splitlines(), 1):
        code = raw.split("//")[0]
        for m in RE_CLEAR.finditer(code):
            col = m.group(1)
            if col in FRAMEWORK_COLLECTIONS:
                continue
            findings.append((filename, n, col, raw.strip()[:80]))
    return findings
```

- [ ] **Step 3: Call it from `check_data_layer.main()`**

Where violations are collected, add:

```python
    bare_clears = []
    for path in files:
        bare_clears.extend(check_bare_clear(path.read_text(encoding="utf-8"), str(path)))
    if bare_clears:
        print("FAIL: %d bare Clear() on an entity collection.\n" % len(bare_clears))
        for fname, n, col, ctx in bare_clears:
            print("  %s:%s  Clear(%s)\n      %s" % (fname, n, col, ctx))
        print("\n  Seed-then-clear is correct only for %s.\n"
              "  On an entity collection this empties the app. Use ClearCollect() to\n"
              "  replace contents, or delete the Clear()."
              % ", ".join(sorted(FRAMEWORK_COLLECTIONS)))
        sys.exit(1)
```

- [ ] **Step 4: Run the regression suite to verify it passes**

```bash
python3 -m unittest tests.test_defect_regression -v
```

Expected: OK, 12 tests.

- [ ] **Step 5: Add coverage-limit lines to all five guards**

Append a `Not covered:` line after each PASS message. `check_control_props.py` already has one from Task 5. For the other four:

`check_tokens.py`, after its PASS block:

```python
    print("  Not covered: spacing literals (reported by inventory.py, not enforced); "
          "literals inside token-exempt lines; values built at runtime.")
```

`check_references.py`:

```python
    print("  Not covered: whether a resolved name has the right TYPE or arity; "
          "control property names (see check_control_props.py); runtime nulls.")
```

`check_collection_columns.py`:

```python
    print("  Not covered: column TYPES; columns added at runtime by Patch/Collect "
          "with a new shape; SortByColumns strings against the sorted collection.")
```

`check_data_layer.py`:

```python
    print("  Not covered: whether the data-access banner is accurate; delegation "
          "warnings; UDF parameter/column case collisions.")
```

- [ ] **Step 6: Wire the new guard into `new_app.py` and drop the misleading claim**

In the `checks` list add:

```python
        ("check_control_props.py", ["--src", str(out)]),
```

Replace the bare `All checks pass.` line with:

```python
    print(f"""
All 5 local guards pass. That means: architecture, tokens, data layer, collection
columns and control contracts are clean.

It does NOT mean the app compiles. There is no offline compile for Canvas Apps —
`pac canvas pack` is deprecated and crashes, and `pac canvas validate` rejects every
file of a working published app. The only real validator is compile_canvas against a
live coauthoring session.
""")
```

- [ ] **Step 7: Verify the scaffolder runs all five guards and stays clean**

```bash
rm -rf /tmp/guard5 && python3 scripts/new_app.py --name "Guard Five" --brand "#300091" --out /tmp/guard5
echo "exit=$?"
```

Expected: exit 0, five PASS lines including `check_control_props.py`, and the honest closing message.

- [ ] **Step 8: Prove the scaffolder now fails on a reintroduced defect**

```bash
cp templates/ListScreen.pa.yaml /tmp/ls.bak
sed -i '' 's/Placeholder: ="Search"/HintText: ="Search"/' templates/ListScreen.pa.yaml
rm -rf /tmp/guardfail && python3 scripts/new_app.py --name "Should Fail" --brand "#300091" --out /tmp/guardfail
echo "exit=$? (expect 1)"
cp /tmp/ls.bak templates/ListScreen.pa.yaml
```

Expected: exit 1, `FAIL check_control_props.py`, and no push instructions printed. This is the behaviour whose absence let a broken app reach a live environment.

- [ ] **Step 9: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/
git commit -m "feat: bare-Clear rule, coverage limits on every guard, wire 5th guard in

check_data_layer gains check_bare_clear: Clear() on an entity collection is
what rendered every scaffolded app empty. Framework collections are exempt.

Every guard now states what it does NOT cover, and new_app.py no longer
prints a bare 'All checks pass' — it says which five things are clean and
that none of them means the app compiles."
```

---

### Task 10: Version bump, docs, sync the installed copy

**Files:**
- Modify: `SKILL.md`, `README.md`
- Sync: `~/.claude/skills/formulas-first-canvas-app/`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: the shipped skill.

- [ ] **Step 1: Document the new guard in `SKILL.md`**

In the guards table/section, add a row and update the count from four to five:

```markdown
| `check_control_props.py` | Control properties match `references/control-contracts.yaml` — property names, renamed-away names, and enum namespaces, resolved through design tokens and component declarations. |
```

Update the sentence `Copy scripts/ into the target repo and run all five alongside every compile.` to say six (five `check_*` plus `inventory.py`), and verify the count matches reality:

```bash
ls plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/check_*.py | wc -l
```

Expected: 5.

- [ ] **Step 2: Add the loop to `SKILL.md`**

```markdown
## The verification loop

There is no offline compile. Local guards are the only pre-push signal, so run them
all, then close the loop against a live session:

    draft model → generate → local guards → push (compile_canvas)
                                   ↑                    ↓
                                   └──── fix ──── parse errors

The five `check_*.py` guards catch architecture, tokens, data layer, collection
columns and control contracts. Each prints what it does NOT cover. Everything else
needs `compile_canvas`.
```

- [ ] **Step 3: Update `README.md`**

Add `check_control_props.py`, `references/control-contracts.yaml`, `references/control-dialects.md` and `tests/` to the layout section, and note that tests run with `python3 -m unittest discover -s tests`.

- [ ] **Step 4: Bump the version**

```bash
grep -rn "version" plugins/acoe-skills/.claude-plugin/plugin.json 2>/dev/null || \
  find plugins/acoe-skills -name '*.json' -maxdepth 2
```

Bump the minor version (0.7.1 → 0.8.0 — this adds a guard and changes `new_app.py` output).

- [ ] **Step 5: Run everything one final time**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
python3 -m unittest discover -s tests -v 2>&1 | tail -5
for g in check_references check_tokens check_collection_columns check_control_props; do
  python3 scripts/$g.py --src templates --tokens-file templates/design-tokens.pa.yaml \
    >/dev/null 2>&1 && echo "PASS $g" || echo "FAIL $g"
done
rm -rf /tmp/final && python3 scripts/new_app.py --name "Final" --brand "#300091" --out /tmp/final && echo "scaffold OK"
```

Expected: all tests OK, all guards PASS, scaffold exits 0.

- [ ] **Step 6: Sync the installed copy so drift cannot recur silently**

```bash
rsync -a --delete \
  --exclude '.DS_Store' --exclude '__pycache__' \
  plugins/acoe-skills/skills/formulas-first-canvas-app/ \
  ~/.claude/skills/formulas-first-canvas-app/
diff -rq plugins/acoe-skills/skills/formulas-first-canvas-app \
         ~/.claude/skills/formulas-first-canvas-app | grep -v DS_Store || echo "IN SYNC"
```

Expected: `IN SYNC`.

- [ ] **Step 7: Commit**

```bash
git add -A plugins/acoe-skills/
git commit -m "docs: document the contract guard, bump to 0.8.0, sync installed copy

Fifth guard documented in SKILL.md and README, verification loop written
down, installed copy re-synced from repo so the 18-file bidirectional drift
cannot recur unnoticed."
```

---

## Self-review

**Spec coverage.** Phase 1 items 1–8 of the spec map to tasks: drift reconciliation → Task 2; SKILL.md correction → Task 1; six live defects → Tasks 2 (cmp_Header) and 3 (the other five); control-contracts.yaml → Task 4; check_control_props.py three layers → Tasks 5, 6, 7; control-dialects.md → Task 1; defect-reintroduction test → Task 8; coverage-limit messages → Task 9. Version bump and installed sync → Task 10.

**Gap found and closed.** Defects 6 and 7 are not control-property defects. Defect 6 is handled by the `requires_one_of` rule in the contract file (Task 4) and enforced in Task 5; defect 7 needed a home, so Task 9 adds `check_bare_clear` to `check_data_layer.py`. Without this the spec's "nine defect classes" claim would have been unmet by two.

**Type consistency.** `check_text(text, filename, contracts, resolver=None, components=None)` is introduced with `resolver` in Task 5, used in Task 6, extended with `components` in Task 7 — all call sites in Tasks 8 and 9 use the final signature. `Finding` and `PropSite` field names are consistent across all four test files. `parse_component_defs_text` (string) and `parse_component_defs` (paths) are distinct and both used.

**Known risk.** The `iter_properties` indentation parser assumes the `Properties:` children sit exactly two spaces deeper than `Properties:`. This holds throughout the skill's tree and the reference app. If a target app uses a different indent width the guard silently checks nothing — Task 5 Step 5 running it against the real templates and getting a non-zero file count is the check against that. A future hardening would assert a minimum property count per file.
