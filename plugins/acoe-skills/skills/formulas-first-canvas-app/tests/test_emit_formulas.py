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
        reg = ef.emit_screens_registry(self.model)
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


if __name__ == "__main__":
    unittest.main()
