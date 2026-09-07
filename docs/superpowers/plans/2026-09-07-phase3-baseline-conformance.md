# Phase 3 — Baseline Conformance, Dashboard, Discovery — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the generator's output render like the baseline app — nav rail, header, populated grid, correctly sized form — then add the baseline-style Dashboard and a one-round richer discovery step.

**Architecture:** The emitters copy the baseline's screen skeleton verbatim (absolute-positioned header/nav/body as direct screen children; fixed-width scrollable column headers; typed empty `DefaultSelectedItems` on every filter combobox; sort through `funcTableSortColumn`/`funcTableSortOrder` UDFs). The dashboard is a new emitter module producing one screen from named formulas the topological sort already orders. Discovery answers land in two new model modifiers, `role: title` and `role: status`.

**Tech Stack:** Python 3.9.6 (no `match`, no runtime PEP 604 unions, no `functools.cache`), PyYAML 6.0.3, stdlib `unittest` (pytest is NOT installed and must not be introduced).

**Spec:** `docs/superpowers/specs/2026-09-07-phase3-baseline-conformance-design.md`

## Global Constraints

- Skill root for all relative paths: `plugins/acoe-skills/skills/formulas-first-canvas-app/`
- Tests via `python3 -m unittest discover -s tests -v` from the skill root. Currently 252 green.
- **The baseline wins.** `/Users/krystofpe/Documents/DEVOPS/CETIN-IT-Platforms/ACOE/acoe-3688-regional-procurement-plan/canvasapps/acoe_regionalprocurementplan_76cad/acoe_regionalprocurementplan_76cad_DocumentUri/Src/` — `Activities.pa.yaml` is the canonical list screen, `Activity Form.pa.yaml` the form, `Dashboard.pa.yaml` the dashboard. `/Users/krystofpe/powerapps-work/canvas-src` is a STALE copy; do not consult it.
- Templates and docs keep generic identifiers (`colItems`, `funcSaveItem`); generated output uses entity-derived ones (`colAssets`, `funcSaveAsset`).
- Do not weaken the six guards or the six architectural rules. `references/control-contracts.yaml` changes only on live-compiler or baseline evidence, stated in the commit.
- No colour/font-size/radius literals outside the token region. Dimension literals (`250`, `60`, `200`) are permitted where the baseline uses them, but prefer tokens where a `constStyle` value already exists.
- Preserve the two deliberate warts: `cmp_Notification`'s repeated `First(SortByColumns(…))`, and any `// token-exempt:` literal.
- Every emitted control property must route through `emit_screens._block()` so `_check_control_prop` sees it.
- Live pushes are done by the controller, against an active coauthoring session. A task ends at "guards pass, ready to push"; it never claims the app renders.

## Baseline formulas to copy (verbatim source of truth)

From `Activities.pa.yaml`:

```yaml
# nav — direct screen child
cmp_Activities_Navigation:
  Height: =Parent.Height - cmp_Activities_Header.Height
  Width: =If(cmp_Activities_Navigation.Navigation, 250, 60)
  Y: =cmp_Activities_Header.Y + cmp_Activities_Header.Height

# list container — direct screen child
con_Activities_List:
  Height: =Parent.Height - cmp_Activities_Header.Height - 20
  Width: =Parent.Width - cmp_Activities_Navigation.Width - 20
  X: =cmp_Activities_Navigation.Width + 10
  Y: =cmp_Activities_Header.Height + 10
  LayoutDirection: =LayoutDirection.Vertical
  LayoutAlignItems: =LayoutAlignItems.Stretch

# table container
con_Activities_Table:
  LayoutOverflowX: =LayoutOverflow.Scroll

# header row
con_Activities_ColumnHeader:
  FillPortions: =0
  Height: =35
  LayoutMinWidth: =11 * 200 + 280      # sum of column widths

# one header
cmp_Filter_REG_ID:
  Height: =35
  LayoutMinWidth: =110
  Width: =200

# filter combobox
com_Activities_StatusFilter:
  DefaultSelectedItems: =FirstN(constStatusChoices, 0)
  InputTextPlaceholder: ="Status"
  IsSearchable: =false
  ItemDisplayText: =ThisItem.Value
```

From `App.pa.yaml`:

```
funcTableSortColumn(TableName: Text): Text =
    LookUp(colSorts, Table = TableName).ID;

funcTableSortOrder(TableName: Text): Text =
    Coalesce(LookUp(colSorts, Table = TableName).SortOrder, "id");
```

From `Activity Form.pa.yaml`:

```yaml
con_Form_Body:
  Height: =Parent.Height - cmp_Form_Header.Height
  Width: =Parent.Width
  Y: =cmp_Form_Header.Height
  LayoutDirection: =LayoutDirection.Vertical
  LayoutAlignItems: =LayoutAlignItems.Stretch
  PaddingLeft: =20
  PaddingTop: =15
```

From `Dashboard.pa.yaml`:

```yaml
gal_NavigationTiles:
  Items: =constDashboardNavigation      # rows {Screen, DisplayName, Icon, Count}
  TemplateSize: =200
  Height: =170
  Width: =Parent.Width
lbl_Dash_Chip:
  Text: =$"{ThisItem.S} · {CountRows(Filter(constActivitiesInScope, Status = ThisItem.S))}"
lbl_Dash_TileCode / lbl_Dash_TileValue / lbl_Dash_TileUnit:
  Text: =ThisItem.Code  /  =Text(ThisItem.Amount, "[$-en-US]#,##0")  /  ="EUR"
lbl_Dashboard_Trademark:
  Text: ="Created by Automation CoE ♥"
```

---

### Task 1: List screen — adopt the baseline skeleton

**Files:**
- Modify: `scripts/emit_screens.py` — `emit_list_screen` (line ~442), `_header_block` (~249), `_cell_block` (~275), `_footer_block` (~379); the `con_%sList_Main` wrapper at ~604 is removed
- Test: `tests/test_emit_screens.py` (extend)

**Interfaces:**
- Consumes: `model.Entity` (`grid_fields`, `filter_fields`, `choices_table()`, `head_control()`, `gallery`, `list_screen`), `_block()`, `_check_control_prop()`.
- Produces: `emit_list_screen(entity, model) -> str` with the new skeleton. Task 2 changes the sort argument inside it; nothing else depends on internals.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_emit_screens.py`:

```python
class TestListScreenMatchesBaselineSkeleton(unittest.TestCase):
    """The first live render showed a nav rail at 50% width, an empty grid and
    factory placeholders. Every assertion here is a symptom from that screenshot,
    traced to a divergence from the baseline's Activities.pa.yaml."""

    def setUp(self):
        self.e = entity()
        self.text = es.emit_list_screen(self.e, small_model())

    def _props_of(self, control_name):
        lines = self.text.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "- %s:" % control_name)
        indent = len(lines[start]) - len(lines[start].lstrip())
        props = {}
        for l in lines[start + 1:]:
            if l.strip().startswith("- ") and (len(l) - len(l.lstrip())) <= indent:
                break
            if l.strip() == "Children:":
                break
            if ":" in l and (len(l) - len(l.lstrip())) == indent + 6:
                k, _, v = l.strip().partition(":")
                props[k] = v.strip()
        return props

    def test_no_horizontal_main_wrapper(self):
        """The wrapper is what made the nav flex to half the screen."""
        self.assertNotIn("con_%sList_Main" % self.e.plural, self.text)

    def test_nav_is_a_direct_screen_child_with_self_sizing_width(self):
        p = self._props_of("cmp_%sList_Navigation" % self.e.plural)
        self.assertEqual(p["Width"], "=If(cmp_%sList_Navigation.Navigation, 250, 60)" % self.e.plural)
        self.assertIn("cmp_%sList_Header.Height" % self.e.plural, p["Y"])
        self.assertIn("Parent.Height", p["Height"])

    def test_list_container_derives_position_from_nav_and_header(self):
        p = self._props_of("con_%sList_List" % self.e.plural)
        self.assertEqual(p["X"], "=cmp_%sList_Navigation.Width + 10" % self.e.plural)
        self.assertIn("cmp_%sList_Navigation.Width" % self.e.plural, p["Width"])
        self.assertIn("cmp_%sList_Header.Height" % self.e.plural, p["Y"])
        self.assertEqual(p["LayoutAlignItems"], "=LayoutAlignItems.Stretch")

    def test_every_filter_combobox_has_typed_empty_default_and_placeholder(self):
        """An untouched ModernCombobox has no defined selection state, so
        IsEmpty(SelectedItems) never returns true and the grid reads 0 of N."""
        for f in self.e.filter_fields:
            p = self._props_of("com_%sList_%sFilter" % (self.e.plural, f.name))
            self.assertEqual(p["DefaultSelectedItems"],
                             "=FirstN(%s, 0)" % self.e.choices_table(f), f.name)
            self.assertEqual(p["InputTextPlaceholder"], '="%s"' % f.label, f.name)
            self.assertEqual(p["ItemDisplayText"], "=ThisItem.Value", f.name)

    def test_no_flex_column_and_min_widths_everywhere(self):
        """A FillPortions=1 header crushes fixed siblings on a narrow canvas."""
        for f in self.e.grid_fields:
            p = self._props_of(self.e.head_control(f))
            self.assertNotIn("FillPortions", p, f.name)
            self.assertIn("Width", p, f.name)
            self.assertIn("LayoutMinWidth", p, f.name)

    def test_header_row_min_width_is_the_sum_of_column_widths(self):
        widths = [es._column_px(f) for f in self.e.grid_fields]
        p = self._props_of("con_%sList_Headers" % self.e.plural)
        self.assertEqual(p["LayoutMinWidth"], "=%d" % sum(widths))

    def test_table_container_scrolls_horizontally(self):
        p = self._props_of("con_%sList_Table" % self.e.plural)
        self.assertEqual(p["LayoutOverflowX"], "=LayoutOverflow.Scroll")

    def test_footer_total_is_coalesced(self):
        self.assertIn("Coalesce(Sum(", self.text)


class TestFlexColumnBecomesWideFixed(unittest.TestCase):
    def test_flex_maps_to_240_px(self):
        f = [x for x in entity().fields if x.grid_width == "flex"]
        if f:
            self.assertEqual(es._column_px(f[0]), 240)
```

Ensure the file's existing `entity()` fixture has at least one `filter: True` choice field and one `grid: "flex"` field; add them if not.

- [ ] **Step 2: Run to verify RED**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
python3 -m unittest tests.test_emit_screens -v 2>&1 | tail -15
```

Expected: the new tests FAIL (`con_AssetsList_Main` present, `_column_px` missing, no `DefaultSelectedItems`).

- [ ] **Step 3: Implement in `scripts/emit_screens.py`**

Add a module-level helper:

```python
FLEX_COLUMN_PX = 240   # the baseline has no flex column; a "flex" field becomes a wide fixed one


def _column_px(field):
    """Pixel width for a grid column. `grid: flex` is a wide fixed column — the
    baseline has no flex column at all; one FillPortions=1 header crushes its
    fixed siblings to zero width on a narrow canvas (seen live 2026-09-07)."""
    return FLEX_COLUMN_PX if field.grid_width == "flex" else int(field.grid_width)
```

In `_header_block` and `_cell_block`: replace any `FillPortions: =1` / `_width_pair` flex logic with `Width: =<px>` and `LayoutMinWidth: =<px>` from `_column_px(field)`. Keep `Height`.

In `emit_list_screen`:

1. Delete the `con_%sList_Main` GroupContainer. Emit, as **direct screen children in this order**: `cmp_%sList_Header`, `cmp_%sList_Navigation`, `con_%sList_List`, then the existing Notification and Spinner instances.
2. Navigation instance properties (copy the baseline, substituting names):
   ```
   Height: =Parent.Height - cmp_<P>List_Header.Height
   Width: =If(cmp_<P>List_Navigation.Navigation, 250, 60)
   Y: =cmp_<P>List_Header.Y + cmp_<P>List_Header.Height
   ```
   plus whatever inputs it already received (`Screens`, `Navigation`, events).
3. `con_%sList_List` (GroupContainer, AutoLayout, Vertical, Stretch):
   ```
   Height: =Parent.Height - cmp_<P>List_Header.Height - 20
   Width: =Parent.Width - cmp_<P>List_Navigation.Width - 20
   X: =cmp_<P>List_Navigation.Width + 10
   Y: =cmp_<P>List_Header.Height + 10
   ```
   Its children are the existing toolbar, then `con_%sList_Table`, then the footer.
4. `con_%sList_Table` gains `LayoutOverflowX: =LayoutOverflow.Scroll`. The header row `con_%sList_Headers` and the gallery both gain `LayoutMinWidth: =<sum of _column_px over grid_fields>`.
5. Every filter combobox gains, in this order among its properties:
   ```
   DefaultSelectedItems: =FirstN(<choices_table>, 0)
   InputTextPlaceholder: ="<label>"
   IsSearchable: =false
   ItemDisplayText: =ThisItem.Value
   ```
   Put a comment above `DefaultSelectedItems` carrying the translated baseline rationale:
   ```
   # Empty but TYPED default selection. Without it an untouched ModernCombobox
   # has no defined selection state, IsEmpty(SelectedItems) never returns true,
   # and the gallery stays empty until the first reset. (Baseline comment,
   # translated; confirmed live 2026-09-07 — the grid read "0 of 16".)
   ```
6. In `_footer_block`, wrap the money total: `funcAsCurrency(Coalesce(Sum(<expr>, <Field>), 0))`.

Confirm `LayoutOverflowX`, `LayoutMinWidth`, `DefaultSelectedItems`, `InputTextPlaceholder`, `IsSearchable` are all in `references/control-contracts.yaml` for their controls. `LayoutOverflowX` and `LayoutMinWidth` are on `Gallery`; check `GroupContainer` — it is unchecked (not in the contract file), so `_block` passes it through. If a `ModernCombobox` property is missing from the contract, STOP and report: it must be added only with the live-compiler evidence from 2026-09-07 stated in the commit.

- [ ] **Step 4: Run to verify GREEN**

```bash
python3 -m unittest tests.test_emit_screens -v 2>&1 | tail -5
python3 -m unittest discover -s tests 2>&1 | tail -3
```

Expected: all green. If `TestGeneratedOutputPassesTheLayoutGuard` fails, read the finding — do not loosen the guard.

- [ ] **Step 5: Generate and run every guard**

```bash
rm -rf /tmp/p3t1 && python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/p3t1; echo "exit=$?"
grep -c "FirstN(" /tmp/p3t1/AssetsListScreen.pa.yaml
grep -c "con_AssetsList_Main" /tmp/p3t1/AssetsListScreen.pa.yaml   # expect 0
```

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/emit_screens.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_emit_screens.py
git commit -m "fix(list): adopt the baseline screen skeleton

Nav and list container become absolutely positioned direct screen children
(the horizontal wrapper flexed the nav to half the screen). No flex column:
fixed Width + LayoutMinWidth per header, row min-width = sum, table scrolls.
Every filter combobox gets DefaultSelectedItems: =FirstN(choices, 0) — an
untouched ModernCombobox has no defined selection state, so IsEmpty never
returns true and the grid read 0 of 16 live. Placeholders set; footer Sum
coalesced."
```

---

### Task 2: Sort through UDFs that cannot blank the grid

**Files:**
- Modify: `scripts/emit_formulas.py` — add two specs to `_all_specs` (line ~416) in the helper-UDF layer
- Modify: `scripts/emit_screens.py` — the `SortByColumns(` argument inside `emit_list_screen`
- Test: `tests/test_emit_formulas.py`, `tests/test_emit_screens.py`

**Interfaces:**
- Produces: named formulas `funcTableSortColumn(pTable: Text): Text` and `funcTableSortOrder(pTable: Text): Text`, emitted once per app (not per entity). `_known_names` must list both.

- [ ] **Step 1: Failing tests**

`tests/test_emit_formulas.py`:

```python
class TestSortUdfs(unittest.TestCase):
    def setUp(self):
        self.text = ef.emit_all(two_entity_model(), rows=4, today=TODAY)

    def test_both_udfs_emitted_once(self):
        self.assertEqual(self.text.count("funcTableSortColumn(pTable: Text): Text ="), 1)
        self.assertEqual(self.text.count("funcTableSortOrder(pTable: Text): Text ="), 1)

    def test_sort_column_defaults_when_colsorts_has_no_row(self):
        """A blank column name makes SortByColumns error and the grid go empty."""
        body = self.text.split("funcTableSortColumn(pTable: Text): Text =")[1].split(";")[0]
        self.assertIn("Coalesce(", body)
        self.assertIn('"Key"', body)

    def test_sort_order_defaults_to_asc(self):
        body = self.text.split("funcTableSortOrder(pTable: Text): Text =")[1].split(";")[0]
        self.assertIn('Coalesce(', body)
        self.assertIn('"asc"', body)

    def test_udf_parameter_uses_p_prefix(self):
        self.assertNotIn("(TableName: Text)", self.text)
```

`tests/test_emit_screens.py`:

```python
class TestGallerySortUsesUdfs(unittest.TestCase):
    def test_no_raw_lookup_on_colsorts_in_items(self):
        text = es.emit_list_screen(entity(), small_model())
        items = text.split("Items: |-")[1].split("TemplateSize")[0]
        self.assertNotIn("LookUp(colSorts", items)
        self.assertIn("funcTableSortColumn(enumEntity.", items)
        self.assertIn('funcTableSortOrder(enumEntity.', items)
```

- [ ] **Step 2: RED**

```bash
python3 -m unittest tests.test_emit_formulas.TestSortUdfs tests.test_emit_screens.TestGallerySortUsesUdfs -v
```

- [ ] **Step 3: Implement**

In `emit_formulas.py`, add to the helper-UDF layer (after the existing helpers, before the data layer):

```python
def _sort_udf_specs():
    """Baseline pattern. A raw LookUp(colSorts, ...).ID is blank whenever the
    entity has no row in colSorts, and SortByColumns on a blank column errors —
    the gallery renders nothing with no message. Coalesce to a column every
    entity has (Key) and to ascending."""
    col = (
        "      funcTableSortColumn(pTable: Text): Text =\n"
        "          Coalesce(LookUp(colSorts, Table = pTable).ID, \"Key\");\n"
    )
    order = (
        "      funcTableSortOrder(pTable: Text): Text =\n"
        "          Coalesce(LookUp(colSorts, Table = pTable).SortOrder, \"asc\");\n"
    )
    return [("helpers", "funcTableSortColumn", col),
            ("helpers", "funcTableSortOrder", order)]
```

Wire into `_all_specs` and add both names to `_known_names`. Match the file's existing spec tuple shape exactly — read `_scope_spec` for the convention.

In `emit_screens.py`, the gallery `Items` sort arguments become:

```
    funcTableSortColumn(<entity.enum_member>),
    If(funcTableSortOrder(<entity.enum_member>) = "desc", SortOrder.Descending, SortOrder.Ascending)
```

- [ ] **Step 4: GREEN + full suite + generate**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
rm -rf /tmp/p3t2 && python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/p3t2; echo "exit=$?"
```

`check_references.py` must still PASS (the UDFs must be declared before the gallery-independent data layer references them — they are helpers, layer 5, so they sort early).

- [ ] **Step 5: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/emit_formulas.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/emit_screens.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_emit_formulas.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_emit_screens.py
git commit -m "fix: sort through funcTableSortColumn/Order UDFs with defaults

Baseline pattern. A raw LookUp on colSorts is blank when the entity has no
row, and SortByColumns on a blank column errors — the grid renders nothing
with no message."
```

---

### Task 3: Form screen — body sized and positioned like the baseline

**Files:**
- Modify: `scripts/emit_screens.py` — `emit_form_screen` (~813), `_form_input_block` (~706)
- Test: `tests/test_emit_screens.py`

**Interfaces:** none new.

- [ ] **Step 1: Failing tests**

```python
class TestFormScreenMatchesBaselineSkeleton(unittest.TestCase):
    """Live render: a ~420px card pinned top-left, covering the header."""

    def setUp(self):
        self.e = entity()
        self.text = es.emit_form_screen(self.e, small_model())
        self.props = TestListScreenMatchesBaselineSkeleton._props_of

    def test_body_fills_width_and_sits_below_header(self):
        p = self.props(self, "con_%sForm_Body" % self.e.entity)
        self.assertEqual(p["Width"], "=Parent.Width")
        self.assertEqual(p["Y"], "=cmp_%sForm_Header.Height" % self.e.entity)
        self.assertEqual(p["LayoutAlignItems"], "=LayoutAlignItems.Stretch")
        self.assertIn("PaddingLeft", p)
        self.assertIn("PaddingTop", p)

    def test_form_comboboxes_have_placeholder_and_typed_default(self):
        for f in self.e.choice_fields:
            p = self.props(self, self.e.form_control(f))
            self.assertEqual(p["InputTextPlaceholder"], '="%s"' % f.label, f.name)
            self.assertIn("DefaultSelectedItems", p, f.name)
            self.assertEqual(p["ItemDisplayText"], "=ThisItem.Value", f.name)
```

- [ ] **Step 2: RED, Step 3: Implement**

`con_%sForm_Body` gets, copying the baseline:

```
Height: =Parent.Height - cmp_<E>Form_Header.Height
Width: =Parent.Width
Y: =cmp_<E>Form_Header.Height
LayoutDirection: =LayoutDirection.Vertical
LayoutAlignItems: =LayoutAlignItems.Stretch
PaddingLeft: =constStyle.Spacing.L
PaddingTop: =constStyle.Spacing.M
```

(Use the existing `constStyle.Spacing` tokens; the baseline's `20`/`15` literals would trip `check_tokens.py` only if they were colours/sizes/radii — they would not — but tokens are the house style.)

Form comboboxes: the existing `DefaultSelectedItems: =Filter(<choices>, Value = loc.<Field>)` is correct for edit mode. Keep it. Add `InputTextPlaceholder: ="<label>"`, `IsSearchable: =false`, and confirm `ItemDisplayText: =ThisItem.Value` is present (Phase 2's live fix added it — verify, do not duplicate).

- [ ] **Step 4: GREEN + generate + guards**, **Step 5: Commit**

```bash
git commit -m "fix(form): body fills the screen below the header, like the baseline

The body had no Width, Y or Stretch, so it rendered as a ~420px card at
(0,0) that covered the header. Form comboboxes get placeholders."
```

---

### Task 4: `cmp_Header` root Width; layout guard covers component instances

**Files:**
- Modify: `components/cmp_Header.pa.yaml:108` — remove `Width: =App.Width`
- Modify: `scripts/check_layout.py:219-222` — remove the CanvasComponent exemption; add rule text
- Test: `tests/test_check_layout.py`

**Interfaces:** none new.

- [ ] **Step 1: Failing test**

```python
class TestComponentInstancesAreNotExempt(unittest.TestCase):
    """The nav rail flexed to half the screen because its instance had no Width
    and the guard exempted CanvasComponent children. The baseline sizes every
    component instance explicitly."""

    def test_unsized_component_in_horizontal_container_is_flagged(self):
        text = (
            "Screens:\n  S:\n    Children:\n"
            "      - con_Row:\n          Control: GroupContainer\n          Variant: AutoLayout\n"
            "          Properties:\n            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n            Width: =Parent.Width\n"
            "          Children:\n"
            "            - cmp_X:\n                Control: CanvasComponent\n"
            "                ComponentName: cmp_Navigation\n"
            "                Properties:\n                  Height: =Parent.Height\n"
        )
        findings = cl.check_text(text, "t.pa.yaml")
        self.assertTrue(any("cmp_X" in f.message for f in findings), findings)

    def test_sized_component_passes(self):
        text = (
            "Screens:\n  S:\n    Children:\n"
            "      - con_Row:\n          Control: GroupContainer\n          Variant: AutoLayout\n"
            "          Properties:\n            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n            Width: =Parent.Width\n"
            "          Children:\n"
            "            - cmp_X:\n                Control: CanvasComponent\n"
            "                ComponentName: cmp_Navigation\n"
            "                Properties:\n                  Height: =Parent.Height\n"
            "                  Width: =60\n                  FillPortions: =0\n"
        )
        self.assertEqual([f for f in cl.check_text(text, "t.pa.yaml") if "cmp_X" in f.message], [])
```

Adapt the entry-point name to whatever `check_layout.py` exposes (read it; it reuses `check_control_props.iter_properties`).

- [ ] **Step 2: RED, Step 3: Implement** — delete the exemption branch at ~219-222, update the docstring's R1/R3 text, remove line 108 from `cmp_Header.pa.yaml`.

- [ ] **Step 4: GREEN + run the layout guard on `templates/` and `components/`.** If it now flags instances in the hand-authored files, **fix them** (add `Width`/`FillPortions: =0` as the baseline does) — do not restore the exemption.

- [ ] **Step 5: Commit**

```bash
git commit -m "fix: cmp_Header drops root Width: =App.Width; layout guard covers component instances

The baseline's header root sets no Width. The CanvasComponent exemption in
check_layout.py hid the unsized nav instance that flexed to half the screen."
```

**Controller gate after Task 4:** regenerate, push to the live app, user screenshots Play mode. The spec's DoD item 1 is judged here, not by tests.

---

### Task 5: Model — `role:` and `dashboard:`

**Files:**
- Modify: `scripts/model.py` — `Field.__init__` (~line 60-90), `Entity` properties, `Model.__init__` (~218)
- Test: `tests/test_model.py`

**Interfaces:**
- Produces: `Field.role` in `{None, "title", "status"}`; `Entity.title_field -> Field`; `Entity.status_field -> Field or None`; `Entity.due_fields -> List[Field]`; `Entity.money_fields -> List[Field]`; `Model.dashboard -> bool`; `Model.description -> str`.

- [ ] **Step 1: Failing tests**

```python
class TestRolesAndDashboard(unittest.TestCase):
    def _model(self, text):
        import tempfile
        return m.load_model(write(tempfile.mkdtemp(), text))

    def test_role_title_and_status_are_read(self):
        mo = self._model(MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                                         "{name: Tag, type: text, required: true, grid: 100, role: title}")
                                .replace("filter: true, vocab: [Open, Shut]",
                                         "filter: true, role: status, vocab: [Open, Shut]"))
        e = mo.entities[0]
        self.assertEqual(e.title_field.name, "Tag")
        self.assertEqual(e.status_field.name, "Status")

    def test_title_defaults_to_first_text_field(self):
        e = self._model(MINIMAL).entities[0]
        self.assertEqual(e.title_field.name, "Tag")

    def test_status_defaults_to_first_filterable_choice(self):
        e = self._model(MINIMAL).entities[0]
        self.assertEqual(e.status_field.name, "Status")

    def test_two_title_roles_is_an_error(self):
        bad = MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                              "{name: Tag, type: text, grid: 100, role: title}") \
                     .replace("{name: Notes, type: text, grid: hidden}",
                              "{name: Notes, type: text, grid: hidden, role: title}")
        with self.assertRaises(m.ModelError) as cm:
            self._model(bad)
        self.assertIn("title", str(cm.exception))

    def test_role_status_on_a_non_choice_is_an_error(self):
        bad = MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                              "{name: Tag, type: text, grid: 100, role: status}")
        with self.assertRaises(m.ModelError):
            self._model(bad)

    def test_dashboard_defaults_on_for_multiple_entities_off_for_one(self):
        self.assertFalse(self._model(MINIMAL).dashboard)
        two = MINIMAL + "  - entity: Site\n    plural: Sites\n    fields:\n      - {name: Name, type: text}\n"
        self.assertTrue(self._model(two).dashboard)

    def test_dashboard_can_be_forced(self):
        self.assertTrue(self._model("dashboard: true\n" + MINIMAL).dashboard)

    def test_due_and_money_partitions(self):
        e = self._model(MINIMAL).entities[0]
        self.assertEqual([f.name for f in e.due_fields], ["Due"])
        self.assertEqual([f.name for f in e.money_fields], ["Amount"])
```

- [ ] **Step 2: RED, Step 3: Implement**

`Field.__init__`: `self.role = spec.get("role")`; validate `role in (None, "title", "status")`; `role: status` requires `type == "choice"`; `role: title` requires `type in ("text", "longtext")`.

`Entity.__init__`: after fields are built, raise `ModelError` if more than one field has `role == "title"` or more than one has `role == "status"`.

```python
    @property
    def title_field(self):
        for f in self.fields:
            if f.role == "title":
                return f
        for f in self.fields:
            if f.type in ("text", "longtext"):
                return f
        return self.fields[0]

    @property
    def status_field(self):
        for f in self.fields:
            if f.role == "status":
                return f
        for f in self.fields:
            if f.type == "choice" and f.filter:
                return f
        return None

    @property
    def due_fields(self):
        return [f for f in self.fields if f.type == "date" and f.semantics == "due"]

    @property
    def money_fields(self):
        return [f for f in self.fields if f.type == "number" and f.money]
```

`Model.__init__`: `raw = data.get("dashboard")`; `self.dashboard = bool(raw) if raw is not None else len(self.entities) > 1`; `self.description = str(data.get("description") or "")`.

Update `templates/model.example.yaml` with `role: title` on Title, `role: status` on Status, and `dashboard: true`.

- [ ] **Step 4: GREEN + full suite**, **Step 5: Commit** — `feat(model): role: title/status, dashboard:, entity partitions`.

---

### Task 6: Dashboard named formulas

**Files:**
- Modify: `scripts/emit_formulas.py` — `_enum_screen_type_spec` (~138), new `_dashboard_specs(model)`, `_registry_spec` (~369), `_all_specs`, `_known_names`
- Test: `tests/test_emit_formulas.py`

**Interfaces:**
- Consumes: `Model.dashboard`, `Entity.status_field`, `due_fields`, `money_fields`, `choices_table()`, `enum_member`, `list_screen`, `scope_formula`, `collection`.
- Produces, only when `model.dashboard`:
  - `enumScreenType.Dashboard: "dashboard"`
  - `constDashboardNavigation` — rows `{Screen, DisplayName, Icon, Count}`
  - `constDashboardPipeline<Entity>` per entity with a status field — rows `{S: Text}` from the vocab
  - `constDashboardBand` — rows `{Code, Amount}`, only when some entity has a money field AND a status field (Amount = `Sum(Filter(scope, Status = Code), Money)`)
  - a `constScreens` row for `DashboardScreen`, first, `Type: enumScreenType.Dashboard`
  - `DashboardScreen` as the name the registry, `_EditorState` and `StartScreen` use (a fixed name; there is one dashboard)

- [ ] **Step 1: Failing tests**

```python
def dashboard_model():
    mo = two_entity_model()
    mo.dashboard = True
    return mo


class TestDashboardFormulas(unittest.TestCase):
    def setUp(self):
        self.text = ef.emit_all(dashboard_model(), rows=4, today=TODAY)

    def test_enum_screen_type_gains_dashboard(self):
        self.assertIn('Dashboard: "dashboard"', self.text)

    def test_navigation_has_entity_totals_first(self):
        nav = self.text.split("constDashboardNavigation =")[1].split("];")[0]
        self.assertLess(nav.index("CountRows(colAssets)"), nav.index("Status ="))
        self.assertIn("Screen: AssetsListScreen", nav)
        self.assertIn("Screen: SitesListScreen", nav)

    def test_navigation_has_status_slices(self):
        nav = self.text.split("constDashboardNavigation =")[1].split("];")[0]
        self.assertIn('CountRows(Filter(constAssetsInScope, Status = "Open"))', nav)

    def test_navigation_capped_at_eight_rows(self):
        nav = self.text.split("constDashboardNavigation =")[1].split("];")[0]
        self.assertLessEqual(nav.count("Screen:"), 8)

    def test_pipeline_per_entity_with_status(self):
        self.assertIn("constDashboardPipelineAsset =", self.text)
        self.assertIn("constDashboardPipelineSite =", self.text)
        pipe = self.text.split("constDashboardPipelineAsset =")[1].split(";")[0]
        self.assertIn('{S: "Open"}', pipe)
        self.assertIn('{S: "Shut"}', pipe)

    def test_band_only_when_money_and_status_coexist(self):
        self.assertIn("constDashboardBand =", self.text)            # Asset has Amount + Status
        band = self.text.split("constDashboardBand =")[1].split(";")[0]
        self.assertIn('Code: "Open"', band)
        self.assertIn("Sum(Filter(constAssetsInScope, Status = \"Open\"), Amount)", band)

    def test_no_band_without_money(self):
        mo = dashboard_model()
        for e in mo.entities:
            e.fields = [f for f in e.fields if not f.money]
        self.assertNotIn("constDashboardBand", ef.emit_all(mo, rows=4, today=TODAY))

    def test_registry_lists_dashboard_first(self):
        reg = ef.emit_screens_registry(dashboard_model())
        self.assertLess(reg.index("Screen: DashboardScreen"), reg.index("Screen: AssetsListScreen"))
        self.assertIn("Type: enumScreenType.Dashboard", reg)

    def test_nothing_emitted_when_dashboard_off(self):
        mo = two_entity_model(); mo.dashboard = False
        t = ef.emit_all(mo, rows=4, today=TODAY)
        self.assertNotIn("constDashboard", t)
        self.assertNotIn("DashboardScreen", t)

    def test_assembled_body_still_has_no_forward_references(self):
        TestEmittedNamesResolve().test_no_forward_references_in_the_assembled_body.__func__(
            type("T", (unittest.TestCase,), {})()) if False else None
        # the existing forward-reference test in this file runs over two_entity_model();
        # run its logic over the dashboard model too:
        text = self.text
        defined_at = {}
        for match in re.finditer(r"^      (\w+)(?:\([^)]*\))?\s*(?::\s*\w+\s*)?=", text, re.M):
            defined_at.setdefault(match.group(1), match.start())
        for name, pos in defined_at.items():
            for use in re.finditer(r"\b%s\b" % re.escape(name), text):
                self.assertGreaterEqual(use.start(), pos, "%s used before definition" % name)
```

(Delete the first two lines of the last test's body — they are a no-op left from drafting; keep only the scan.)

- [ ] **Step 2: RED, Step 3: Implement**

`_dashboard_specs(model)` returns an empty list when `not model.dashboard`. Otherwise it builds, in the data-access layer (so they sort after the collections):

`constDashboardNavigation` — rows in priority order until 8:
1. per entity: `{Screen: <list_screen>, DisplayName: "<plural>", Icon: "<icon>", Count: CountRows(<collection>)}`
2. per entity, per `due_fields`: `{Screen: <list_screen>, DisplayName: "<plural> overdue", Icon: "Clock", Count: CountRows(Filter(<scope>, <Due> < Today()))}`
3. per entity with a status field, per vocab value: `{Screen: <list_screen>, DisplayName: "<value>", Icon: "<icon>", Count: CountRows(Filter(<scope>, <Status> = "<value>"))}`

`constDashboardPipeline<Entity>` = `Table({S: "<v>"}, …)` for each entity with a status field.

`constDashboardBand` — for the FIRST entity having both `money_fields` and a `status_field`: `Table({Code: "<v>", Amount: Sum(Filter(<scope>, <Status> = "<v>"), <Money>)}, …)`. Omit entirely otherwise.

All strings through the module's `_quote`. Register every emitted name in `_known_names`. In `_registry_spec`, when `model.dashboard`, prepend `{Screen: DashboardScreen, DisplayName: "Dashboard", Icon: "Home", Entity: "", Type: enumScreenType.Dashboard, Group: "", BackLabel: "Dashboard"}`. Add `Dashboard: "dashboard"` to `_enum_screen_type_spec` unconditionally (harmless when off — but the test `test_nothing_emitted_when_dashboard_off` checks `constDashboard`/`DashboardScreen`, not the enum member).

- [ ] **Step 4: GREEN + full suite**, **Step 5: Commit** — `feat(formulas): dashboard sources — navigation tiles, pipeline, band, registry row`.

---

### Task 7: `scripts/emit_dashboard.py` — the screen

**Files:**
- Create: `scripts/emit_dashboard.py`
- Modify: `templates/design-tokens.pa.yaml` — add a `Dashboard` group to `constStyle`
- Test: `tests/test_emit_dashboard.py`

**Interfaces:**
- Consumes: Task 6's formula names; `emit_screens._block`, `_check_control_prop`, `_quote`, `_needs_block_scalar` (import them — do not duplicate).
- Produces: `emit_dashboard_screen(model) -> str` for a screen named `DashboardScreen`.

- [ ] **Step 1: Failing tests**

```python
"""The dashboard is the baseline's landing page: title/caption, KPI band,
status-chip pipeline, navigation tiles, trademark."""
import pathlib, sys, unittest, yaml
SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import model as m, emit_dashboard as ed, check_control_props as ccp, check_layout as cl  # noqa

def dash_model():
    return m.Model({"app_name": "Ops", "dashboard": True, "description": "Two registers.", "entities": [
        {"entity": "Asset", "plural": "Assets", "fields": [
            {"name": "Tag", "type": "text", "grid": 100, "role": "title"},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True, "role": "status", "vocab": ["Open", "Shut"]},
            {"name": "Amount", "type": "number", "grid": 118, "money": True}]},
        {"entity": "Site", "plural": "Sites", "fields": [
            {"name": "Name", "type": "text", "grid": "flex"},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True, "vocab": ["Live", "Closed"]}]}]})

class TestDashboardScreen(unittest.TestCase):
    def setUp(self):
        self.text = ed.emit_dashboard_screen(dash_model())

    def test_screen_is_named_dashboardscreen(self):
        self.assertTrue(self.text.startswith("Screens:\n  DashboardScreen:"))

    def test_has_header_nav_and_body_like_the_list_screen(self):
        for n in ("cmp_Dashboard_Header", "cmp_Dashboard_Navigation", "con_Dashboard_Body"):
            self.assertIn("- %s:" % n, self.text, n)

    def test_five_regions(self):
        for n in ("lbl_Dash_BandTitle", "gal_Dash_Band", "lbl_Dash_PipelineTitle",
                  "gal_Dash_Pipeline", "gal_NavigationTiles", "lbl_Dashboard_Trademark"):
            self.assertIn("- %s:" % n, self.text, n)

    def test_galleries_read_the_named_formulas(self):
        self.assertIn("Items: =constDashboardBand", self.text)
        self.assertIn("Items: =constDashboardNavigation", self.text)
        self.assertIn("Items: =constDashboardPipelineAsset", self.text)

    def test_chip_text_matches_the_baseline_shape(self):
        self.assertIn('CountRows(Filter(constAssetsInScope, Status = ThisItem.S))', self.text)

    def test_tile_navigates(self):
        self.assertIn("OnSelect: =Navigate(ThisItem.Screen, ScreenTransition.Fade)", self.text)

    def test_band_omitted_when_model_has_none(self):
        mo = dash_model()
        for e in mo.entities:
            e.fields = [f for f in e.fields if not f.money]
        t = ed.emit_dashboard_screen(mo)
        self.assertNotIn("gal_Dash_Band", t)

    def test_no_dimension_or_colour_literals_outside_tokens(self):
        for lit in ("=15", "=140", "=200", "=170", "RGBA("):
            self.assertNotIn(lit, self.text, lit)

    def test_yaml_and_both_guards_clean(self):
        yaml.safe_load(self.text)
        contracts = ccp.load_contracts()
        comps = ccp.parse_component_defs(sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        errs = [f for f in ccp.check_text(self.text, "Dashboard.pa.yaml", contracts, components=comps)
                if f.severity == "error"]
        self.assertEqual(errs, [])
        self.assertEqual([f for f in cl.check_text(self.text, "Dashboard.pa.yaml") if f.severity == "error"], [])
```

- [ ] **Step 2: RED, Step 3: Implement**

Add to `templates/design-tokens.pa.yaml` inside `constStyle`:

```
        Dashboard: {
            TileSize: 200,
            TileHeight: 170,
            BandTileSize: 140,
            BandHeight: 120,
            ChipHeight: 32,
            Radius: 15,
            Gap: 20
        },
```

`emit_dashboard_screen(model)` composes, as direct screen children, the same header/nav pattern as Task 1's list screen (reuse the formulas — factor a `_screen_chrome(prefix)` helper into `emit_screens.py` if that avoids copying, and import it), then `con_Dashboard_Body` (Vertical, Stretch, `Width: =Parent.Width - Nav.Width - 20`, `X: =Nav.Width + 10`, `Y: =Header.Height + 10`) containing, in order:

1. `lbl_Dash_BandTitle` (`ModernText`, `Text: ="<band entity plural> by <status label>"`) and `lbl_Dash_BandCaption` (`Text: ="<model.description or generated one-liner>"`) — only when a band exists.
2. `con_Dash_Band` → `gal_Dash_Band` (`Gallery`, `Variant: Horizontal`, `Items: =constDashboardBand`, `TemplateSize: =constStyle.Dashboard.BandTileSize`, `Height: =constStyle.Dashboard.BandHeight`, `FillPortions: =0`) → tile container with `lbl_Dash_TileCode` (`=ThisItem.Code`), `lbl_Dash_TileValue` (`=funcAsCurrency(ThisItem.Amount)`), `lbl_Dash_TileUnit` (`="<currency>"`). Only when a band exists.
3. `lbl_Dash_PipelineTitle` (`="Pipeline"`) then, per entity with a status field, `gal_Dash_Pipeline<Entity>` (`Horizontal`, `Items: =constDashboardPipeline<Entity>`, `Height: =constStyle.Dashboard.ChipHeight + constStyle.Spacing.M`, `FillPortions: =0`) → `con_Dash_StatusChip` → `lbl_Dash_Chip` with `Text: =$"{ThisItem.S} · {CountRows(Filter(<scope>, <Status> = ThisItem.S))}"`. The test expects the first one named `gal_Dash_Pipeline`; name the first exactly that and subsequent ones with the entity suffix, OR name all with suffix and adjust the test to `gal_Dash_PipelineAsset`. Pick one and keep test and code consistent.
4. `con_Dash_Tiles` → `gal_NavigationTiles` (`Items: =constDashboardNavigation`, `WrapCount` from width, `TemplateSize: =constStyle.Dashboard.TileSize`, `Height: =constStyle.Dashboard.TileHeight`, `FillPortions: =0`) → `con_ScreenTiles` (radius from token, `Fill: =constPaperColor.RGBA`) with `lbl_ScreenTiles_Screen` (`=ThisItem.DisplayName`), `btn_ScreenTiles_Navigate` (`Button`, `Icon: =ThisItem.Icon`, `Layout: ='ButtonCanvas.Layout'.IconOnly`, `OnSelect: =Navigate(ThisItem.Screen, ScreenTransition.Fade)`), `btn_ScreenTiles_Count` (`Text: =ThisItem.Count`).
5. `lbl_Dashboard_Trademark` (`="Created by Automation CoE ♥"`), `FillPortions: =0`.

Every property through `_block`. Every fixed-height child `FillPortions: =0` with explicit `Height`; one flexible spacer `ModernText` with blank `Text` (never `Visible:` on it). Galleries always carry `FillPortions` or `Height`.

- [ ] **Step 4: GREEN**, **Step 5: Commit** — `feat: dashboard screen emitter — band, pipeline, tiles, trademark`.

---

### Task 8: Wire the dashboard into `new_app.py`; acceptance

**Files:**
- Modify: `scripts/new_app.py` — screen writing (~416), `StartScreen` (~256), `_EditorState` (~428-466)
- Modify: `tests/test_acceptance.py`

**Interfaces:** consumes `emit_dashboard.emit_dashboard_screen`, `Model.dashboard`.

- [ ] **Step 1: Failing acceptance tests** — in `tests/test_acceptance.py` add a three-entity model fixture where one entity has a money+status pair and `dashboard: true`, generate via subprocess, and assert: `DashboardScreen.pa.yaml` exists; `App.pa.yaml` has `StartScreen: =DashboardScreen`; `_EditorState.pa.yaml` lists `DashboardScreen` first; `constScreens` has `Type: enumScreenType.Dashboard`; `>= 6` PASS lines; exit 0. Also assert that the one-entity fixture (dashboard off by default) produces NO `DashboardScreen.pa.yaml` and `StartScreen` is its list screen.

- [ ] **Step 2: RED, Step 3: Implement** — when `model.dashboard`: write `DashboardScreen.pa.yaml`, set `StartScreen: =DashboardScreen`, put `DashboardScreen` first in `ScreensOrder`. Otherwise unchanged.

- [ ] **Step 4: GREEN + full suite + both generation paths exit 0 with all guards PASS**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
rm -rf /tmp/p3t8 && python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/p3t8; echo "exit=$?"
rm -rf /tmp/p3t8b && python3 scripts/new_app.py --name "Legacy" --brand "#300091" --out /tmp/p3t8b; echo "exit=$?"
```

- [ ] **Step 5: Commit** — `feat: dashboard wired — StartScreen, registry, editor order`.

**Controller gate after Task 8:** push, user screenshots the Dashboard and the list in Play mode.

---

### Task 9: Discovery in `SKILL.md`, docs, version, sync

**Files:**
- Modify: `SKILL.md` (the workflow section, step 3), `README.md`
- Modify: `plugins/acoe-skills/.claude-plugin/plugin.json` — 0.9.0 → 0.10.0

- [ ] **Step 1: Rewrite step 3 of the workflow** as one message that shows the field table AND asks only what the sentence left ambiguous, each mapped to a model field:

```
3. CONFIRM — one message, one round trip. Show the field table, then ask only
   the questions the sentence did not already answer:
     • Which field identifies a record?        → role: title on that field
     • Which status matters most?              → role: status (drives dashboard
                                                  pipeline, semafor colour, default sort)
     • Is there a deadline date?               → semantics: due on that field
     • Do you want a dashboard? (default: yes when there is more than one table)
                                               → dashboard:
   Accept "just go". Do not ask a question whose answer is already in the model.
```

Document `role:`, `dashboard:`, `description:` in the model-schema section, and that the dashboard is emitted only when on and mirrors the baseline's five regions (Gates skipped). State the baseline path and that the older corpus is stale.

- [ ] **Step 2: README** — add `emit_dashboard.py`, the `Dashboard` token group, the new model keys. Verify every count against `ls scripts/`.

- [ ] **Step 3: Bump version to 0.10.0.**

- [ ] **Step 4: Full verification, then sync the installed copy after a `diff -rq` precheck you read.**

- [ ] **Step 5: Commit** — `docs: one-round discovery with role: landing, dashboard docs, v0.10.0`.

---

## Self-review

**Spec coverage.** Part 1: Task 1 (skeleton, FirstN, placeholders, min-widths, scroll, Coalesce), Task 2 (sort UDFs), Task 3 (form body), Task 4 (header Width, layout guard) — every row of the spec's symptom table has a task, and the two Studio-only symptoms are correctly given no task. Part 2: Task 5 (model keys), 6 (formulas), 7 (screen), 8 (wiring). Part 3: Task 9. Order of work: controller gates after Tasks 4 and 8 match the spec's "push → screenshot" points.

**Placeholder scan.** One drafting artifact caught and flagged inline in Task 6's last test (two dead lines to delete). Task 7 leaves one naming choice (`gal_Dash_Pipeline` vs per-entity suffix) explicitly to the implementer with the instruction to keep test and code consistent — that is a decision, not a placeholder.

**Type consistency.** `_column_px(field)` introduced in Task 1, used by its tests. `funcTableSortColumn(pTable: Text)` in Task 2 matches its test strings. `Entity.title_field/status_field/due_fields/money_fields` and `Model.dashboard/description` from Task 5 are the exact names Tasks 6–7 use. `emit_dashboard_screen(model)` is the name Task 8 imports. `check_layout.check_text` is assumed in Task 4's tests — the implementer is told to read the module for the real entry point.

**Known risk.** Task 4's header fix is a hypothesis verified only by the push after Task 4; if the header is still empty, the controller opens a fix round rather than the next task.
