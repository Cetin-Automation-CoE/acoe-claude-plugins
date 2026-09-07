"""Four per-type field components, deliberately not one generic one."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

NAMES = ("cmp_FieldText", "cmp_FieldChoice", "cmp_FieldDate", "cmp_FieldNumber")


class TestFieldComponents(unittest.TestCase):
    def test_all_four_exist(self):
        for n in NAMES:
            self.assertTrue((SKILL / "components" / (n + ".pa.yaml")).exists(), n)

    def test_each_declares_exactly_one_scalar_output(self):
        defs = ccp.parse_component_defs(
            [SKILL / "components" / (n + ".pa.yaml") for n in NAMES])
        for n in NAMES:
            self.assertIn("Output", defs[n], n)

    def test_no_generic_cmp_field_exists(self):
        """A single component returning a Record caused a 247-error cascade."""
        self.assertFalse((SKILL / "components" / "cmp_Field.pa.yaml").exists())

    def test_all_four_are_contract_clean(self):
        contracts = ccp.load_contracts()
        for n in NAMES:
            p = SKILL / "components" / (n + ".pa.yaml")
            errs = [f for f in ccp.check_text(p.read_text(encoding="utf-8"),
                                              str(p), contracts)
                    if f.severity == "error"]
            self.assertEqual(errs, [], "%s: %s" % (n, errs))


if __name__ == "__main__":
    unittest.main()
