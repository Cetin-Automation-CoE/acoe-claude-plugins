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


if __name__ == "__main__":
    unittest.main()
