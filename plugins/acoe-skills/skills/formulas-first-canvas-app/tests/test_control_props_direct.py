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
