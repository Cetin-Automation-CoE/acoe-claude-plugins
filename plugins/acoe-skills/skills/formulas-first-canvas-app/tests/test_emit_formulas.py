"""App.Formulas must be strictly dependency-ordered.

The studio binder cannot forward-reference between named formulas, and ONE
unresolved name drops the entire Formulas blob — the app goes blank with no
error naming the cause. These tests are the only thing standing between a
model and that failure.
"""
import datetime
import pathlib
import re
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_formulas as ef  # noqa: E402
import emit_mock  # noqa: E402

TODAY = datetime.date(2026, 9, 7)


def two_entity_model():
    return m.Model({
        "app_name": "Ops",
        "entities": [
            {"entity": "Asset", "plural": "Assets", "fields": [
                {"name": "Tag", "type": "text", "grid": 100, "search": True},
                {"name": "Status", "type": "choice", "grid": 120, "filter": True,
                 "vocab": ["Open", "Shut"]},
                {"name": "Amount", "type": "number", "grid": 118, "money": True},
            ]},
            {"entity": "Site", "plural": "Sites", "fields": [
                {"name": "Name", "type": "text", "grid": "flex", "search": True},
                {"name": "Status", "type": "choice", "grid": 120, "filter": True,
                 "vocab": ["Live", "Closed"]},
            ]},
        ],
    })


class TestTopoSort(unittest.TestCase):
    def test_a_block_comes_after_everything_it_uses(self):
        B = ef.Block
        blocks = [
            B("c", {"c"}, {"b"}, "c = b + 1;"),
            B("a", {"a"}, set(), "a = 1;"),
            B("b", {"b"}, {"a"}, "b = a + 1;"),
        ]
        order = [b.name for b in ef.topo_sort(blocks)]
        self.assertLess(order.index("a"), order.index("b"))
        self.assertLess(order.index("b"), order.index("c"))

    def test_a_cycle_raises_rather_than_emitting_a_blob_that_silently_dies(self):
        B = ef.Block
        blocks = [B("a", {"a"}, {"b"}, ""), B("b", {"b"}, {"a"}, "")]
        with self.assertRaises(ef.OrderError) as cm:
            ef.topo_sort(blocks)
        self.assertIn("a", str(cm.exception))

    def test_ordering_is_deterministic_across_runs(self):
        mo = two_entity_model()
        a = ef.emit_all(mo, rows=8, today=TODAY)
        b = ef.emit_all(mo, rows=8, today=TODAY)
        self.assertEqual(a, b)


class TestEmittedNamesResolve(unittest.TestCase):
    """Every name used must be defined earlier in the emitted text."""

    def test_no_forward_references_in_the_assembled_body(self):
        text = ef.emit_all(two_entity_model(), rows=8, today=TODAY)
        defined_at = {}
        for match in re.finditer(r"^      (\w+)(?:\([^)]*\))?\s*(?::\s*\w+\s*)?=",
                                 text, re.M):
            defined_at.setdefault(match.group(1), match.start())
        for name, pos in defined_at.items():
            for use in re.finditer(r"\b%s\b" % re.escape(name), text):
                if use.start() < pos:
                    self.fail("%s used at %d before its definition at %d"
                              % (name, use.start(), pos))


class TestGenuineDependencyEdges(unittest.TestCase):
    """`topo_sort` must honor a REAL dependency edge regardless of the order
    blocks happen to be constructed in — not merely reproduce whatever order
    `_all_specs` built them in. Without deliberately scrambling the input,
    a test proves nothing here: `_all_specs` already appends blocks in the
    right order, so a bug that silently degrades `uses` to "whatever the
    input order already gives you" would still pass an unscrambled check.
    """

    def test_registry_stays_after_the_enums_it_references_even_when_specs_are_scrambled(self):
        mo = two_entity_model()
        specs = ef._all_specs(mo, rows=4, today=TODAY)
        # Reverse, not shuffle: this deterministically puts constScreens (the
        # last block `_all_specs` appends) FIRST and the enum blocks (the
        # first two it appends) LAST — the worst-case ordering for a
        # position-only tie-break. If `uses` were empty or hand-declared
        # incompletely, constScreens would end up before enumEntity here.
        scrambled = list(reversed(specs))
        blocks, _ = ef._finalize(scrambled, ef._known_names(mo))
        ordered = ef.topo_sort(blocks)
        names = [b.name for b in ordered]
        self.assertLess(names.index("enumEntity"), names.index("constScreens"),
                         "constScreens must be ordered after enumEntity, which its "
                         "own text references, even from a reversed input list")
        self.assertLess(names.index("enumScreenType"), names.index("constScreens"),
                         "constScreens must be ordered after enumScreenType, which "
                         "its own text references, even from a reversed input list")


class TestPerEntityLayer(unittest.TestCase):
    def setUp(self):
        self.model = two_entity_model()
        self.text = ef.emit_all(self.model, rows=8, today=TODAY)

    def test_each_entity_gets_its_own_collection_and_udfs(self):
        for name in ("colAssets", "funcLoadAssets", "funcSaveAsset", "funcDeleteAsset",
                     "colSites", "funcLoadSites", "funcSaveSite", "funcDeleteSite"):
            self.assertIn(name, self.text, name)

    def test_generic_template_identifiers_do_not_leak_into_generated_output(self):
        for leaked in ("colItems", "funcLoadItems", "funcSaveItem", "locItem"):
            self.assertNotIn(leaked, self.text, leaked)

    def test_same_named_fields_on_two_entities_get_distinct_choices_tables(self):
        self.assertIn("constAssetStatusChoices", self.text)
        self.assertIn("constSiteStatusChoices", self.text)

    def test_no_bare_clear_on_an_entity_collection(self):
        self.assertNotIn("Clear(colAssets)", self.text)
        self.assertNotIn("Clear(colSites)", self.text)

    def test_udf_parameters_use_the_p_prefix_to_avoid_row_scope_collision(self):
        """A parameter one case-fold from a column makes {Tag: tag} resolve to
        Tag: Tag — a save that writes nothing and reports success."""
        for sig in re.findall(r"funcSave\w+\(([^)]*)\)", self.text):
            for param in [p.split(":")[0].strip() for p in sig.split(",") if p.strip()]:
                self.assertTrue(param.startswith("p"),
                                "parameter %r must use the p prefix" % param)

    def test_registry_has_two_rows_per_entity(self):
        # two_entity_model() defaults `dashboard` on (Task 5: on by default
        # for >1 entity) — scoped off here so this test's own claim (two
        # rows PER ENTITY) stays exact regardless of the dashboard feature,
        # which prepends its own row and is covered by TestDashboardFormulas.
        mo = two_entity_model()
        mo.dashboard = False
        reg = ef.emit_screens_registry(mo)
        self.assertEqual(reg.count("Screen:"), 4)
        for s in ("AssetsListScreen", "AssetFormScreen",
                  "SitesListScreen", "SiteFormScreen"):
            self.assertIn(s, reg)

    def test_enum_entity_has_one_member_per_entity(self):
        e = ef.emit_enum_entity(self.model)
        self.assertIn("Assets:", e)
        self.assertIn("Sites:", e)

    def test_switch_day_binding_is_present_but_commented(self):
        self.assertIn("// SWITCH DAY", self.text)


def _balanced(text, open_idx):
    """The substring from an opening paren at `open_idx` to its true
    matching close, counting nesting depth — a naive non-greedy regex
    (`\\(.*?\\)`) stops at the FIRST `)` that happens to precede a comma,
    which is wrong the moment the expression nests parens of its own (as
    Ruling 25's Max(...)/Split(...) expression does). Mirrors
    check_collection_columns.py's own `balanced()` helper."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx:i + 1]
    raise ValueError("unbalanced parens from index %d" % open_idx)


class TestGeneratedKeyOnCreate(unittest.TestCase):
    """Ruling 21/I4: every created record used to get Key: "" (the screen's
    "Add" action always passes glSelectedKey, which is ""), so the SECOND
    create's LookUp(col, Key = "") found the first blank-keyed row and
    silently overwrote it — and that row could never be opened again.

    Ruling 25: the FIRST fix derived the suffix from CountRows(collection),
    which is how many rows are LEFT, not how many have ever existed —
    create -> delete ANY row -> create reissued the same suffix the first
    create just used, colliding with that still-live row. The current
    formula derives the suffix from the MAXIMUM suffix among rows PRESENT
    right now (Max(collection, Value(Last(Split(Key, "|")).Value)) + 1),
    which cannot be reset by an unrelated delete.

    There is no local Power Fx evaluator (there is no offline compile for
    Canvas Apps), so `_next_key` below is a Python MODEL of the formula's
    specified semantics, not an execution of it — it is used to reason
    about the algorithm's behavior across a sequence of creates/deletes.
    The tests that guard against silently regressing back to the old,
    delete-unsafe formula instead inspect the ACTUAL emitted text (see
    `test_create_branch_key_expression_is_max_based_not_count_based`).
    """

    def setUp(self):
        self.model = two_entity_model()
        self.entity = self.model.entities[0]  # Asset
        self.mock_rows = emit_mock.mock_rows(self.entity, n=16, today=TODAY)
        self.text = ef.emit_all(self.model, rows=16, today=TODAY)

    def _create_key_expr(self):
        """The full, correctly paren-balanced Key expression from
        funcSaveAsset's create-branch Collect() call, read out of the
        ACTUAL emitted text (self.text) — not re-derived from Python."""
        marker = "Collect(\n                  colAssets,\n                  {Key: ("
        start = self.text.index(marker)
        open_idx = start + len(marker) - 1  # index of the "(" itself
        full = _balanced(self.text, open_idx)
        return full[1:-1]  # strip the outer, test-added-for-disambiguation parens

    def _max_suffix(self, keys):
        """Parse the numeric suffix off each "PREFIX|n" key — mock keys and
        generated keys both use this shape — mirroring what the emitted
        Value(Last(Split(Key, "|")).Value) formula computes per row."""
        suffixes = [int(k.rsplit("|", 1)[1]) for k in keys]
        return max(suffixes) if suffixes else 0

    def _next_key(self, existing_keys):
        """Python model of the CURRENT formula: suffix is one past the
        MAXIMUM suffix among rows present right now, never the row count."""
        prefix = ef._key_prefix_literal(self.entity)
        return "%s|%d" % (prefix, self._max_suffix(existing_keys) + 1)

    def test_two_successive_creates_get_distinct_keys(self):
        existing = [row["Key"].strip('"') for row in self.mock_rows]
        first = self._next_key(existing)
        second = self._next_key(existing + [first])  # after the first Collect
        self.assertNotEqual(first, second)
        self.assertNotIn(first, existing)
        self.assertNotIn(second, existing)

    def test_ruling_25_create_delete_a_different_row_then_create_stays_distinct(self):
        """The exact repro from the re-review: 16 mock rows, create (suffix
        16), delete some OTHER row (not the one just created), create again
        — the second create must not reissue the first create's key. A
        CountRows(collection)-based suffix fails this (16 rows -> create ->
        17 rows, suffix 16 [0-based+1]; delete one -> 16 rows again; create
        -> CountRows is 16 again -> suffix 16 AGAIN, colliding with the
        still-live first create)."""
        existing = [row["Key"].strip('"') for row in self.mock_rows]
        first = self._next_key(existing)
        after_first_create = existing + [first]
        after_delete = after_first_create[1:]  # drop one pre-existing row; keep `first`
        second = self._next_key(after_delete)
        self.assertNotEqual(first, second,
                            "a delete between two creates must not let the second "
                            "create reissue the first create's key (Ruling 25)")

    def test_create_branch_key_expression_is_max_based_not_count_based(self):
        """The regression guard that does not depend on this file's own
        Python model being right: inspects the ACTUAL emitted Power Fx
        text. A future regression back to a CountRows(collection)-based
        suffix — the exact defect Ruling 25 reported — fails this even if
        `_next_key` above were (wrongly) left unchanged to match it."""
        key_expr = self._create_key_expr()
        self.assertIn("Max(colAssets,", key_expr)
        self.assertIn('Split(Key, "|")', key_expr)
        self.assertNotIn("CountRows(colAssets)", key_expr,
                         "the create-branch key must not be derived from the "
                         "CURRENT row count — that reissues a suffix the moment "
                         "any row is deleted between two creates (Ruling 25)")

    def test_save_udf_create_branch_never_emits_a_blank_or_bare_pkey_as_key(self):
        key_expr = self._create_key_expr()
        self.assertNotIn('""', key_expr,
                         "the create branch must never emit a blank Key literal")
        self.assertNotEqual(key_expr.strip(), "pKey",
                            "the create branch must never emit the bare (blank) "
                            "pKey parameter as the new row's Key")

    def test_save_udf_branches_on_isblank_pkey_not_a_lookup(self):
        """The original bug routed create-vs-update through
        IsBlank(LookUp(collection, Key = pKey)) — with pKey = "", that LookUp
        could find a PRIOR blank-keyed row and take the UPDATE branch
        instead, silently overwriting it. Branching on IsBlank(pKey) directly
        removes the possibility entirely: blank always creates, non-blank
        always updates."""
        self.assertIn("If(\n              IsBlank(pKey),", self.text)
        self.assertNotIn("IsBlank(LookUp(", self.text)


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


def dashboard_model():
    mo = two_entity_model()
    mo.dashboard = True
    return mo


class TestDashboardFormulas(unittest.TestCase):
    def setUp(self):
        self.text = ef.emit_all(dashboard_model(), rows=4, today=TODAY)

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

    def test_dashboard_registry_row_is_typed_list_and_grouped_overview(self):
        # RULING 10: cmp_Navigation renders Filter(cmp_Navigation.Screens,
        # Type = enumScreenType.List) — a row typed anything else (the
        # brief's original enumScreenType.Dashboard) is invisible in the
        # nav rail, making the dashboard the start screen yet unreachable
        # the moment the user navigates away from it. Group "Overview"
        # gives it a section in the expanded menu, same as any entity.
        reg = ef.emit_screens_registry(dashboard_model())
        row = reg.split("Screen: DashboardScreen")[1].split("}")[0]
        self.assertIn("Type: enumScreenType.List", row)
        self.assertIn('Group: "Overview"', row)

    def test_registry_lists_dashboard_first(self):
        reg = ef.emit_screens_registry(dashboard_model())
        self.assertLess(reg.index("Screen: DashboardScreen"), reg.index("Screen: AssetsListScreen"))
        # RULING 10: typed List (see test_dashboard_registry_row_is_typed_
        # list_and_grouped_overview), not the brief's original Dashboard —
        # scoped to the dashboard row itself, not just anywhere in `reg`
        # (every entity's list row also carries Type: enumScreenType.List).
        row = reg.split("Screen: DashboardScreen")[1].split("}")[0]
        self.assertIn("Type: enumScreenType.List", row)

    def test_nothing_emitted_when_dashboard_off(self):
        mo = two_entity_model(); mo.dashboard = False
        t = ef.emit_all(mo, rows=4, today=TODAY)
        self.assertNotIn("constDashboard", t)
        self.assertNotIn("DashboardScreen", t)

    def test_assembled_body_still_has_no_forward_references(self):
        # the existing forward-reference test in this file runs over two_entity_model();
        # run its logic over the dashboard model too:
        text = self.text
        defined_at = {}
        for match in re.finditer(r"^      (\w+)(?:\([^)]*\))?\s*(?::\s*\w+\s*)?=", text, re.M):
            defined_at.setdefault(match.group(1), match.start())
        for name, pos in defined_at.items():
            for use in re.finditer(r"\b%s\b" % re.escape(name), text):
                self.assertGreaterEqual(use.start(), pos, "%s used before definition" % name)


if __name__ == "__main__":
    unittest.main()
