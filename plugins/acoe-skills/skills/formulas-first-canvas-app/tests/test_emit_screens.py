"""Generated screens must be contract-clean by construction, not by luck."""
import pathlib
import sys
import unittest

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_screens as es  # noqa: E402
import check_control_props as ccp  # noqa: E402


def entity():
    return m.Entity({
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Tag", "type": "text", "grid": 100, "search": True},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True,
             "vocab": ["Open", "Shut"]},
            {"name": "Amount", "type": "number", "grid": 118, "money": True},
            {"name": "Due", "type": "date", "grid": 112, "semantics": "due"},
            {"name": "Notes", "type": "longtext", "grid": "hidden"},
        ],
    })


def entity_without_money():
    """Same shape as `entity()` but with no `money: true` field anywhere —
    the footer must still show a count and must not emit a stray `Sum()`."""
    return m.Entity({
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Tag", "type": "text", "grid": 100, "search": True},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True,
             "vocab": ["Open", "Shut"]},
            {"name": "Due", "type": "date", "grid": 112, "semantics": "due"},
        ],
    })


def small_model():
    return m.Model({"app_name": "Ops", "entities": [{
        "entity": "Asset", "plural": "Assets",
        "fields": [{"name": "Tag", "type": "text", "grid": 100}]}]})


class TestListScreen(unittest.TestCase):
    def setUp(self):
        self.e = entity()
        self.text = es.emit_list_screen(self.e, small_model())

    def test_one_header_per_grid_field_and_none_for_hidden(self):
        for f in self.e.grid_fields:
            self.assertIn(self.e.head_control(f), self.text, f.name)
        self.assertNotIn("Notes", self.text.split("Children:")[0])

    def test_one_row_cell_per_grid_field(self):
        for f in self.e.grid_fields:
            self.assertIn(self.e.cell_control(f), self.text, f.name)

    def test_gallery_has_explicit_fillportions(self):
        """A Gallery is a leaf control; without this it collapses to ~200px."""
        gal = self.text.split(self.e.gallery)[1]
        self.assertIn("FillPortions: =1", gal.split("Children:")[0])

    def test_search_box_searches_every_search_field(self):
        self.assertIn("Tag", self.text)

    def test_money_cells_use_the_money_colour_function_not_a_literal(self):
        self.assertIn("funcMoneyTextColor(ThisItem.Amount)", self.text)

    def test_component_inputs_receive_strings_not_enums(self):
        """cmp_FilterButton.Align is DataType: Text."""
        self.assertNotIn("Align: =Align.", self.text)


class TestFormScreen(unittest.TestCase):
    def setUp(self):
        self.e = entity()
        self.text = es.emit_form_screen(self.e, small_model())

    def test_one_input_per_field_including_grid_hidden_ones(self):
        for f in self.e.form_fields:
            self.assertIn(self.e.form_control(f), self.text, f.name)

    def test_archetype_picks_the_control(self):
        self.assertIn("Control: ModernCombobox", self.text)
        self.assertIn("Control: ModernDatePicker", self.text)
        self.assertIn("Control: ModernTextInput", self.text)

    def test_no_format_property_on_a_number_input(self):
        """ModernTextInput has no Format; numeric entry is a text input."""
        self.assertNotIn("Format: =TextFormat", self.text)

    def test_placeholder_not_hinttext(self):
        self.assertNotIn("HintText:", self.text)


class TestGeneratedOutputPassesTheContractGuard(unittest.TestCase):
    """The emitter reads the same contract file the guard checks against, so
    this must hold by construction, not by coincidence."""

    def test_list_and_form_are_contract_clean(self):
        contracts = ccp.load_contracts()
        components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        e, mo = entity(), small_model()
        for name, text in (("list", es.emit_list_screen(e, mo)),
                           ("form", es.emit_form_screen(e, mo))):
            errs = [f for f in ccp.check_text(text, name + ".pa.yaml", contracts,
                                              components=components)
                    if f.severity == "error"]
            self.assertEqual(errs, [], "%s: %s" % (name, errs))


class TestNoGenericLeakage(unittest.TestCase):
    def test_template_identifiers_do_not_appear_in_generated_screens(self):
        e, mo = entity(), small_model()
        for text in (es.emit_list_screen(e, mo), es.emit_form_screen(e, mo)):
            for leaked in ("colItems", "locItem", "gal_List_Items"):
                self.assertNotIn(leaked, text, leaked)


class TestFooterAggregates(unittest.TestCase):
    """Ruling 12: the list screen's footer must show a filtered/total count
    against the SAME scope formula the gallery reads (so it cannot silently
    disagree with the grid), plus one Sum() per money field."""

    def test_count_references_the_scope_formula_not_the_raw_collection(self):
        e = entity()
        text = es.emit_list_screen(e, small_model())
        self.assertIn("CountRows(%s)" % e.scope_formula, text)

    def test_money_field_produces_a_sum_over_the_scope_formula(self):
        e = entity()
        text = es.emit_list_screen(e, small_model())
        self.assertIn("Sum(%s, Amount)" % e.scope_formula, text)
        self.assertIn("funcAsCurrency(Sum(%s, Amount))" % e.scope_formula, text)

    def test_entity_without_a_money_field_still_gets_a_count_and_no_stray_sum(self):
        e = entity_without_money()
        text = es.emit_list_screen(e, small_model())
        self.assertIn("CountRows(%s)" % e.scope_formula, text)
        self.assertNotIn("Sum(", text)


class TestEmittedYamlIsValid(unittest.TestCase):
    """check_control_props.py is a line-oriented regex parser, not a real
    YAML parser — it can (and, during development of this module, did) pass
    output that yaml.safe_load rejects outright. Round-tripping through a
    real parser is a cheap, mechanical way to catch that class of bug."""

    def test_both_screens_parse_as_yaml(self):
        e, mo = entity(), small_model()
        for name, text in (("list", es.emit_list_screen(e, mo)),
                           ("form", es.emit_form_screen(e, mo))):
            try:
                data = yaml.safe_load(text)
            except yaml.YAMLError as exc:
                self.fail("%s screen is not valid YAML: %s" % (name, exc))
            self.assertIn("Screens", data, name)


if __name__ == "__main__":
    unittest.main()
