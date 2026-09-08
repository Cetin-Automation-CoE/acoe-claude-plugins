"""The model is the app's spec. A bad model must fail loudly here, never downstream."""
import pathlib
import sys
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402

MINIMAL = textwrap.dedent("""\
    app_name: Test App
    entities:
      - entity: Asset
        plural: Assets
        fields:
          - {name: Tag, type: text, required: true, grid: 100}
          - {name: Status, type: choice, grid: 120, filter: true, vocab: [Open, Shut]}
          - {name: Amount, type: number, grid: 118, money: true}
          - {name: Due, type: date, grid: 112, semantics: due}
          - {name: Notes, type: text, grid: hidden}
    """)


def write(tmpdir, text):
    p = pathlib.Path(tmpdir) / "model.yaml"
    p.write_text(text, encoding="utf-8")
    return p


class TestDerivedNames(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.model = m.load_model(write(self.tmp, MINIMAL))
        self.e = self.model.entities[0]

    def test_entity_derived_identifiers(self):
        e = self.e
        self.assertEqual(e.collection, "colAssets")
        self.assertEqual(e.scope_formula, "constAssetsInScope")
        self.assertEqual(e.func_load, "funcLoadAssets")
        self.assertEqual(e.func_save, "funcSaveAsset")
        self.assertEqual(e.func_delete, "funcDeleteAsset")
        self.assertEqual(e.loc_var, "locAsset")
        self.assertEqual(e.list_screen, "AssetsListScreen")
        self.assertEqual(e.form_screen, "AssetFormScreen")
        self.assertEqual(e.gallery, "gal_Assets_Items")
        self.assertEqual(e.enum_member, "enumEntity.Assets")

    def test_choices_table_name_is_per_entity_and_field(self):
        """Two entities may both have a Status field; the names must not collide."""
        status = [f for f in self.e.fields if f.name == "Status"][0]
        self.assertEqual(self.e.choices_table(status), "constAssetStatusChoices")

    def test_field_partitions(self):
        e = self.e
        self.assertEqual([f.name for f in e.grid_fields],
                         ["Tag", "Status", "Amount", "Due"])
        self.assertEqual([f.name for f in e.form_fields],
                         ["Tag", "Status", "Amount", "Due", "Notes"])
        self.assertEqual([f.name for f in e.choice_fields], ["Status"])
        self.assertEqual([f.name for f in e.filter_fields], ["Status"])

    def test_label_defaults_to_uppercased_name(self):
        self.assertEqual(self.e.grid_fields[0].label, "TAG")


class TestValidation(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def _err(self, text):
        with self.assertRaises(m.ModelError) as cm:
            m.load_model(write(self.tmp, text))
        return str(cm.exception)

    def test_unknown_archetype_is_rejected_and_lists_valid_ones(self):
        msg = self._err(MINIMAL.replace("type: text, required: true", "type: wibble"))
        self.assertIn("wibble", msg)
        self.assertIn("text", msg)

    def test_choice_without_vocab_is_rejected(self):
        bad = MINIMAL.replace(", vocab: [Open, Shut]", "")
        self.assertIn("vocab", self._err(bad))

    def test_no_entities_is_rejected(self):
        self.assertIn("entities", self._err("app_name: X\nentities: []\n"))

    def test_duplicate_entity_names_are_rejected(self):
        # NOTE: appended with explicit indentation (not textwrap.dedent) because
        # dedent always zeroes out the least-indented line — here that's the
        # "- entity:" list item itself, which would pull it out of the
        # `entities:` block and produce a YAML syntax error instead of
        # exercising duplicate-entity validation.
        dup = MINIMAL + "  - entity: Asset\n    plural: Assets\n    fields:\n      - {name: Tag, type: text}\n"
        self.assertIn("Asset", self._err(dup))

    def test_duplicate_field_names_within_an_entity_are_rejected(self):
        dup = MINIMAL.replace("- {name: Notes, type: text, grid: hidden}",
                              "- {name: Tag, type: text, grid: hidden}")
        self.assertIn("Tag", self._err(dup))

    def test_field_name_colliding_with_the_key_column_is_rejected(self):
        bad = MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                              "{name: Key, type: text, required: true, grid: 100}")
        self.assertIn("Key", self._err(bad))

    def test_field_name_must_be_a_valid_powerfx_identifier(self):
        bad = MINIMAL.replace("{name: Tag,", "{name: 'Tag Number',")
        self.assertIn("Tag Number", self._err(bad))

    def test_field_name_value_is_rejected_as_a_powerfx_reserved_word(self):
        """M1: a SharePoint column literally named 'Value' is common, and it
        would shadow the Power Fx built-in inside every control formula that
        reads the row (ThisItem.Value, locX.Value, ...)."""
        bad = MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                              "{name: Value, type: text, required: true, grid: 100}")
        msg = self._err(bad)
        self.assertIn("Value", msg)
        self.assertIn("reserved", msg)

    def test_field_names_self_parent_thisitem_text_are_also_rejected(self):
        for reserved in ("Self", "Parent", "ThisItem", "Text"):
            bad = MINIMAL.replace(
                "{name: Tag, type: text, required: true, grid: 100}",
                "{name: %s, type: text, required: true, grid: 100}" % reserved)
            self.assertIn(reserved, self._err(bad), reserved)

    def test_grid_garbage_value_is_a_model_error_not_a_bare_valueerror(self):
        """M6: `grid: <garbage>` used to escape as a bare ValueError from
        int(), bypassing the friendly error handler entirely."""
        bad = MINIMAL.replace("grid: 100", "grid: wibble")
        msg = self._err(bad)
        self.assertIn("grid", msg)
        self.assertIn("wibble", msg)

    def test_colliding_derived_choices_table_names_are_rejected(self):
        """M2: entity 'Asset' field 'StatusChoices' and entity 'AssetStatus'
        field 'Choices' both derive the SAME choices-table name
        (constAssetStatusChoicesChoices) — undetected, this used to reach
        emit_formulas.topo_sort as two blocks sharing one name and raise
        OrderError with an EMPTY cycle list, a confusing internal error for
        what is really a model problem."""
        text = ("app_name: X\nentities:\n"
                "  - entity: Asset\n    plural: Assets\n    fields:\n"
                "      - {name: StatusChoices, type: choice, vocab: [Open, Shut]}\n"
                "  - entity: AssetStatus\n    plural: AssetStatuses\n    fields:\n"
                "      - {name: Choices, type: choice, vocab: [A, B]}\n")
        msg = self._err(text)
        self.assertIn("constAssetStatusChoicesChoices", msg)


class TestGridCap(unittest.TestCase):
    def test_fields_beyond_the_cap_fall_off_the_grid_but_stay_on_the_form(self):
        import tempfile
        fields = "\n".join(
            "          - {name: F%d, type: text, grid: 100}" % i for i in range(12))
        text = ("app_name: T\nentities:\n  - entity: A\n    plural: As\n"
                "    fields:\n" + fields + "\n")
        mo = m.load_model(write(tempfile.mkdtemp(), text))
        e = mo.entities[0]
        self.assertEqual(len(e.grid_fields), m.MAX_GRID_COLUMNS)
        self.assertEqual(len(e.form_fields), 12)


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

    def test_invalid_role_value_is_an_error(self):
        bad = MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                              "{name: Tag, type: text, required: true, grid: 100, role: owner}")
        with self.assertRaises(m.ModelError) as cm:
            self._model(bad)
        msg = str(cm.exception)
        self.assertIn("title", msg)
        self.assertIn("status", msg)

    def test_role_title_on_a_non_text_field_is_an_error(self):
        bad = MINIMAL.replace("{name: Amount, type: number, grid: 118, money: true}",
                              "{name: Amount, type: number, grid: 118, money: true, role: title}")
        with self.assertRaises(m.ModelError) as cm:
            self._model(bad)
        self.assertIn("title", str(cm.exception))

    def test_two_status_roles_is_an_error(self):
        bad = MINIMAL.replace(
                "{name: Status, type: choice, grid: 120, filter: true, vocab: [Open, Shut]}",
                "{name: Status, type: choice, grid: 120, filter: true, role: status, vocab: [Open, Shut]}") \
            .replace(
                "{name: Notes, type: text, grid: hidden}",
                "{name: Notes, type: choice, grid: hidden, role: status, vocab: [A, B]}")
        with self.assertRaises(m.ModelError) as cm:
            self._model(bad)
        msg = str(cm.exception)
        self.assertIn("status", msg)
        self.assertIn("Asset", msg)

    def test_status_field_is_none_without_role_or_filterable_choice(self):
        text = ("app_name: T\nentities:\n  - entity: A\n    plural: As\n"
                "    fields:\n      - {name: Name, type: text}\n      - {name: Notes, type: text}\n")
        e = self._model(text).entities[0]
        self.assertIsNone(e.status_field)

    def test_description_round_trips_and_defaults_to_empty(self):
        self.assertEqual(self._model(MINIMAL).description, "")
        self.assertEqual(
            self._model("description: Track site equipment.\n" + MINIMAL).description,
            "Track site equipment.")

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


if __name__ == "__main__":
    unittest.main()
