"""Every defect that reached a live environment gets a test that reproduces it.

Six were live in the tree when this guard was written; three were already fixed
and are reintroduced synthetically. All nine must fail the guard.
"""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

TOKENS = (SKILL / "templates" / "design-tokens.pa.yaml").read_text(encoding="utf-8")


def control(ctype, props, name="c1", component=None):
    head = "      - %s:\n          Control: %s\n" % (name, ctype)
    if component:
        head += "          ComponentName: %s\n" % component
    head += "          Properties:\n"
    return head + "".join("            %s: %s\n" % (k, v) for k, v in props)


class TestNineDefectClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = ccp.load_contracts()
        # staticmethod() wrapping is required here: make_resolver returns a plain
        # function, and assigning a plain function to a CLASS attribute (cls.x = ...)
        # makes attribute access on an instance (self.resolver) go through the
        # function descriptor protocol, silently binding `self` as resolve()'s first
        # positional arg ("resolve() takes 1 positional argument but 2 were given").
        # The other test files in this suite avoid the trap by assigning
        # self.resolver = ... inside setUp() (an instance attribute, never bound);
        # staticmethod() gives the same immunity while keeping this setUpClass shape.
        cls.resolver = staticmethod(ccp.make_resolver(ccp.parse_tokens(TOKENS)))
        cls.components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))

    def assertRejected(self, text, expect_in_message=None):
        findings = ccp.check_text(text, "t.pa.yaml", self.contracts,
                                  resolver=self.resolver, components=self.components)
        errs = [f for f in findings if f.severity == "error"]
        self.assertTrue(errs, "guard did not reject:\n%s" % text)
        if expect_in_message:
            joined = " ".join(f.message for f in errs)
            self.assertIn(expect_in_message, joined)

    def test_1_fontcolor_on_moderntext(self):
        self.assertRejected(
            control("ModernText", [("FontColor", "=RGBA(0,0,0,1)")]), "Color")

    def test_2_weight_on_moderntext(self):
        self.assertRejected(
            control("ModernText", [("Weight", "=FontWeight.Bold")]), "FontWeight")

    def test_3_hinttext_on_moderntextinput(self):
        self.assertRejected(
            control("ModernTextInput", [("HintText", '="Search"')]), "Placeholder")

    def test_4_format_on_moderntextinput(self):
        self.assertRejected(
            control("ModernTextInput", [("Format", "=TextFormat.Number")]))

    def test_5_value_on_moderncombobox(self):
        self.assertRejected(
            control("ModernCombobox", [("Value", '="Value"')]))

    def test_6_gallery_without_fillportions(self):
        self.assertRejected(
            control("Gallery", [("Items", "=colItems")]), "FillPortions")

    def test_8_wrong_namespace_via_token(self):
        self.assertRejected(
            control("ModernText",
                    [("Align", "=constStyle.Label.NumberInput.AlignLegacy")]), "End")

    def test_9_enum_into_text_typed_component_input(self):
        self.assertRejected(
            control("CanvasComponent", [("Align", "=Align.Center")],
                    component="cmp_FilterButton"), "Text")

    def test_direct_wrong_namespace_enum(self):
        self.assertRejected(
            control("ModernText", [("Align", "=Align.Right")]), "End")


class TestDefect7DataLayer(unittest.TestCase):
    """Defect 7 is a data-layer rule, not a control-property one."""

    def test_bare_clear_on_entity_collection_is_rejected(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        import check_data_layer as cdl
        text = (
            "      funcLoadItems(): Void =\n"
            "      {\n"
            "          ClearCollect(colItems, Table({Key: \"A|1\"}));\n"
            "          Clear(colItems);\n"
            "      };\n"
        )
        findings = cdl.check_bare_clear(text, "App.pa.yaml")
        self.assertTrue(findings, "bare Clear(colItems) after seeding not caught")

    def test_clear_on_framework_collections_is_allowed(self):
        import check_data_layer as cdl
        for col in ("colFilters", "colSorts", "colBack", "colNotifications"):
            text = "          Clear(%s);\n" % col
            self.assertEqual(cdl.check_bare_clear(text, "App.pa.yaml"), [], col)


class TestCleanTreeStaysClean(unittest.TestCase):
    """The guard must not cry wolf on the shipped tree."""

    def test_no_errors_in_templates_or_components(self):
        contracts = ccp.load_contracts()
        resolver = ccp.make_resolver(ccp.parse_tokens(TOKENS))
        components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        for d in ("templates", "components"):
            for path in sorted((SKILL / d).glob("*.pa.yaml")):
                errs = [f for f in ccp.check_text(
                    path.read_text(encoding="utf-8"), str(path), contracts,
                    resolver=resolver, components=components)
                    if f.severity == "error"]
                self.assertEqual(errs, [], "%s: %s" % (path.name, errs))


if __name__ == "__main__":
    unittest.main()
