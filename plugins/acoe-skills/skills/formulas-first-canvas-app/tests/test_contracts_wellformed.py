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

    def test_align_members_are_scoped_to_button(self):
        """The plain Align namespace validates only Button.Align. Members are
        added only when verified against a compiled app — an unverified member
        is a silent false negative in the guard."""
        self.assertEqual(set(self.data["enums"]["Align"]), {"Left", "Center", "Right"})

    def test_known_absent_properties_are_absent(self):
        c = self.data["controls"]
        self.assertNotIn("HintText", c["ModernTextInput"]["properties"])
        self.assertNotIn("Format", c["ModernTextInput"]["properties"])
        self.assertNotIn("Value", c["ModernCombobox"]["properties"])
        # ShowScrollbar moved OUT of Gallery's `absent` list 2026-09-08:
        # `Control: Gallery` is the Classic family per describe_control,
        # the reference app uses it, and a live compile_canvas accepted
        # `ShowScrollbar: =false` on four galleries with 0 errors. The old
        # entry was inferred from a "modern gallery" reading rather than
        # from a live rejection, and it made the guard refuse valid YAML.
        # TabIndex stays asserted absent below — there a live rejection
        # IS on record.
        self.assertNotIn("Color", c["Button"]["properties"])
        self.assertNotIn("Fill", c["Button"]["properties"])

    def test_tabindex_is_absent_everywhere_live_compile_2026_09_07(self):
        """A live `compile_canvas` run rejected `TabIndex` with "Unknown
        property 'TabIndex'" on ModernTextInput, ModernCombobox,
        ModernDatePicker and Button — 52 of 59 errors in that run. It had
        been carried in this file's `properties` lists since the original
        Microsoft-Learn seeding and was never corpus-verified (zero
        occurrences in the provably-compiled reference app). Must be absent
        from every control's `properties` and curated as a hard-error
        `absent` entry everywhere it used to appear."""
        c = self.data["controls"]
        for name in ("ModernText", "Text", "ModernTextInput", "ModernCombobox",
                     "ModernDatePicker", "Button", "ModernButton@1.0.0", "Gallery"):
            self.assertNotIn("TabIndex", c[name]["properties"], name)
            self.assertIn("TabIndex", c[name].get("absent") or [], name)


if __name__ == "__main__":
    unittest.main()
