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


def control(ctype, props, name="c1", component=None, variant=None):
    """Build a fixture control block in the REAL `.pa.yaml` shape.

    Ruling 13 (C1): every regression fixture in this file used to omit the
    `Variant:` line that real GroupContainer and Gallery blocks always carry
    between `Control:` and `Properties:` — the exact sibling key that wiped
    control context and made the guard blind to `gal_List_Items`. A fixture
    without `Variant:` cannot exercise that bug, which is how it survived 10
    tasks and 9 reviews. `variant` defaults to a real value for Gallery so
    every gallery fixture below exercises the actual shape, not an idealized
    one; pass `variant=None` explicitly only for controls that genuinely have
    no Variant in this repo's shipped tree (ModernText, Button, etc.).
    """
    if variant is None and ctype == "Gallery":
        variant = "Vertical"
    head = "      - %s:\n          Control: %s\n" % (name, ctype)
    if variant:
        head += "          Variant: %s\n" % variant
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


class TestParserSeesRealControlShapes(unittest.TestCase):
    """Ruling 13 (C1): `Control:` followed by a sibling `Variant:` (the shape
    every real GroupContainer and Gallery block uses) must not wipe control
    context before `Properties:` is reached. A test suite that only asserts
    "the guard rejected this" passes vacuously if the parser silently skipped
    the block entirely with zero findings — this is a POSITIVE assertion that
    the parser actually attributed properties to the control, which is the
    class of test that was missing when this bug shipped."""

    def test_gallery_with_variant_line_keeps_control_context(self):
        text = control("Gallery", [("Items", "=colItems"), ("FillPortions", "=1")])
        sites = list(ccp.iter_properties(text, "t.pa.yaml"))
        self.assertTrue(sites, "no property sites found at all")
        for site in sites:
            self.assertEqual(site.control_type, "Gallery",
                              "control context lost: %r" % (site,))
        self.assertIn("FillPortions", [s.prop for s in sites])

    def test_real_listscreen_sees_the_gallery(self):
        """The exact regression: templates/ListScreen.pa.yaml's gal_List_Items
        sits behind a `Variant: Vertical` line. Before the fix this yielded
        ZERO property sites for it."""
        path = SKILL / "templates" / "ListScreen.pa.yaml"
        text = path.read_text(encoding="utf-8")
        sites = [s for s in ccp.iter_properties(text, str(path))
                 if s.control == "gal_List_Items"]
        self.assertTrue(sites, "gal_List_Items produced no property sites")
        self.assertTrue(all(s.control_type == "Gallery" for s in sites))
        self.assertIn("FillPortions", [s.prop for s in sites])

    def test_real_listscreen_site_count_floor(self):
        """Before the fix, templates/ListScreen.pa.yaml yielded 129 sites with
        40 lacking control context (31%) — the fix does not change the total
        line count parsed, but it must sharply cut how many go unattributed.
        A floor on total sites plus a ceiling on unattributed ones catches a
        regression that silently drops sites again, in either direction."""
        path = SKILL / "templates" / "ListScreen.pa.yaml"
        text = path.read_text(encoding="utf-8")
        sites = list(ccp.iter_properties(text, str(path)))
        self.assertGreaterEqual(len(sites), 120)
        no_ctx = sum(1 for s in sites if not s.control_type)
        self.assertLess(no_ctx, 15, "too many property sites lost control context")


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
