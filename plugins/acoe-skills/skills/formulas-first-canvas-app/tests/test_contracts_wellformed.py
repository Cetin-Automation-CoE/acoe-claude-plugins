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

        # The brief writes `properties` as comma-joined strings per line for
        # readability. Task 5's loader flattens and splits on commas before
        # using the data — normalize here too so this test exercises the same
        # shape the guard will see.
        for spec in cls.data["controls"].values():
            flat = []
            for entry in spec.get("properties") or []:
                flat.extend(p.strip() for p in entry.split(",") if p.strip())
            spec["properties"] = flat

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
