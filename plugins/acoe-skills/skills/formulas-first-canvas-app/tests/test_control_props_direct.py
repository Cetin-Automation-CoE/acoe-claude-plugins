"""Layer 1: direct property checking with indentation-tracked control context."""
import collections
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

    def test_trailing_comment_on_control_line_does_not_hide_the_block(self):
        """`Control: ModernText  # a label` used to yield an unknown control
        type ("ModernText  # a label") and silently skip the whole block."""
        text = (
            "      - lbl_A:\n"
            "          Control: ModernText  # a label\n"
            "          Properties:\n"
            "            Color: =RGBA(0,0,0,1)\n"
        )
        sites = list(ccp.iter_properties(text, "t.pa.yaml"))
        self.assertEqual(sites[0].control_type, "ModernText")

    def test_trailing_comment_on_enum_value_does_not_defeat_the_regex(self):
        """`Align: =Align.Right  # right` used to stop RE_ENUM's `$`-anchored
        match from firing at all, silently skipping the enum check."""
        text = (
            "      - c1:\n"
            "          Control: Button\n"
            "          Properties:\n"
            "            Align: =Align.Right  # right\n"
        )
        sites = list(ccp.iter_properties(text, "t.pa.yaml"))
        self.assertEqual(sites[0].value, "=Align.Right")

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

    def test_token_path_on_enum_property_is_unchecked_not_an_error(self):
        """`constStyle.Something.FontWeight` is a named-formula token reference,
        not a literal `Namespace.Member` enum value. RE_ENUM's dotted-path match
        can mistake its last two segments for one — e.g. namespace
        `constStyle.Header`, member `FontWeight` — which isn't a known enum
        namespace at all, so it must be reported as unchecked, not wrong."""
        findings = self._check("ModernText", "FontWeight", "=constStyle.Something.FontWeight")
        self.assertEqual(errors(findings), [])
        self.assertEqual(warns(findings), [])


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

    def test_unlisted_control_is_counted_as_unchecked(self):
        """I3: an unknown control's properties must be COUNTED, not just
        silently let through — a guard that never says what it skipped can
        hide the exact kind of gap that let a Gallery go unseen."""
        text = (
            "      - x1:\n"
            "          Control: SomeFutureControl\n"
            "          Properties:\n"
            "            Whatever: =1\n"
        )
        counts = collections.Counter()
        ccp.check_text(text, "t.pa.yaml", self.contracts, counts=counts)
        self.assertEqual(counts["unknown_control"], 1)


class TestSeverityIsSplit(unittest.TestCase):
    """Ruling 14 (C2): a curated negative (renamed_from/removed/absent) is a
    hard ERROR; a property simply missing from `properties` is a WARNING —
    the contract file's own header says absence there means "not verified,"
    not "invalid," and the compiled reference app proved the lists are not
    exhaustive enough to carry hard-error semantics."""

    def setUp(self):
        self.contracts = ccp.load_contracts()

    def test_curated_absent_property_is_still_an_error(self):
        text = (
            "      - c1:\n"
            "          Control: ModernTextInput\n"
            "          Properties:\n"
            "            Format: =TextFormat.Number\n"
        )
        findings = ccp.check_text(text, "t.pa.yaml", self.contracts)
        self.assertEqual(len(errors(findings)), 1)

    def test_property_merely_missing_from_the_list_is_only_a_warning(self):
        text = (
            "      - c1:\n"
            "          Control: ModernText\n"
            "          Properties:\n"
            "            SomeBrandNewProperty: =1\n"
        )
        findings = ccp.check_text(text, "t.pa.yaml", self.contracts)
        self.assertEqual(errors(findings), [])
        self.assertEqual(len(warns(findings)), 1)
        self.assertIn("unverified", warns(findings)[0].message)


class TestUnresolvedTokenIsCounted(unittest.TestCase):
    def test_unresolved_token_path_is_counted_not_just_silently_unchecked(self):
        contracts = ccp.load_contracts()
        resolver = ccp.make_resolver({})  # empty map: every path is unresolved
        text = (
            "      - c1:\n"
            "          Control: ModernText\n"
            "          Properties:\n"
            "            Align: =constStyle.Nope.Missing\n"
        )
        counts = collections.Counter()
        ccp.check_text(text, "t.pa.yaml", contracts, resolver=resolver, counts=counts)
        self.assertEqual(counts["unresolved_token"], 1)


class TestNoControlContextIsCounted(unittest.TestCase):
    def test_property_with_no_control_context_is_counted(self):
        """A screen- or App-level `Properties:` block (Fill, OnVisible, ...)
        sits above any `- control:` item and never sets control_type — real
        shape taken from templates/ListScreen.pa.yaml's own screen header."""
        contracts = ccp.load_contracts()
        text = (
            "Screens:\n"
            "  ListScreen:\n"
            "    Properties:\n"
            "      Fill: =constReactGray.RGBA\n"
        )
        counts = collections.Counter()
        ccp.check_text(text, "t.pa.yaml", contracts, counts=counts)
        self.assertEqual(counts["no_control_context"], 1)


class TestTypoedSrcFailsLoud(unittest.TestCase):
    """I2: check_data_layer.py already refuses to run against a --src that
    isn't a directory ("A guard that silently checks nothing is worse than no
    guard."); check_control_props.py did not, so a typo'd path printed PASS
    and exited 0. Exercised via subprocess since this is main()'s own exit
    behavior, not check_text()'s."""

    def _run(self, src):
        import subprocess
        return subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "check_control_props.py"),
             "--src", src],
            capture_output=True, text=True)

    def test_nonexistent_src_exits_nonzero(self):
        r = self._run(str(SKILL / "no-such-directory-xyz"))
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("PASS", r.stdout)

    def test_empty_src_exits_nonzero(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            r = self._run(d)
            self.assertNotEqual(r.returncode, 0)
            self.assertNotIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
