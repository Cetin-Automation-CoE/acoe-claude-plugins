"""Layer 3: CanvasComponent instance properties are custom inputs, not control props."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

COMPONENT_DEF = """\
ComponentDefinitions:
  cmp_FilterButton:
    DefinitionType: CanvasComponent
    AccessAppScope: true
    CustomProperties:
      Align:
        PropertyKind: Input
        DataType: Text
        Default: ="Center"
      Width:
        PropertyKind: Input
        DataType: Number
        Default: =140
      OnSort:
        PropertyKind: Event
"""


def errors(findings):
    return [f for f in findings if f.severity == "error"]


def instance(prop, value):
    return (
        "      - cmp_List_Head:\n"
        "          Control: CanvasComponent\n"
        "          ComponentName: cmp_FilterButton\n"
        "          Properties:\n"
        "            %s: %s\n" % (prop, value)
    )


class TestComponentDefParsing(unittest.TestCase):
    def test_extracts_declared_inputs_and_types(self):
        defs = ccp.parse_component_defs_text(COMPONENT_DEF)
        self.assertEqual(defs["cmp_FilterButton"]["Align"], "Text")
        self.assertEqual(defs["cmp_FilterButton"]["Width"], "Number")

    def test_parses_every_shipped_component(self):
        paths = sorted((SKILL / "components").glob("cmp_*.pa.yaml"))
        self.assertEqual(len(paths), 8)
        defs = ccp.parse_component_defs(paths)
        self.assertEqual(len(defs), 8)
        self.assertIn("Align", defs["cmp_FilterButton"])


class TestInstanceChecking(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()
        self.components = ccp.parse_component_defs_text(COMPONENT_DEF)

    def _check(self, text):
        return ccp.check_text(text, "t.pa.yaml", self.contracts,
                              components=self.components)

    def test_defect_9_enum_into_a_text_typed_input(self):
        f = errors(self._check(instance("Align", "=Align.Center")))
        self.assertEqual(len(f), 1)
        self.assertIn("Text", f[0].message)

    def test_string_into_a_text_typed_input_is_clean(self):
        self.assertEqual(errors(self._check(instance("Align", '="Center"'))), [])

    def test_number_into_a_number_typed_input_is_clean(self):
        self.assertEqual(errors(self._check(instance("Width", "=140"))), [])

    def test_undeclared_property_is_an_error(self):
        f = errors(self._check(instance("Nonexistent", "=1")))
        self.assertEqual(len(f), 1)

    def test_unknown_component_is_unchecked_not_failed(self):
        text = (
            "      - x:\n"
            "          Control: CanvasComponent\n"
            "          ComponentName: cmp_NotLoaded\n"
            "          Properties:\n"
            "            Whatever: =1\n"
        )
        self.assertEqual(errors(self._check(text)), [])

    def test_expression_into_a_text_input_is_unchecked(self):
        """Only bare enum literals are judged; formulas are left alone."""
        self.assertEqual(
            errors(self._check(instance("Align", '=If(x, "Left", "Right")'))), [])

    def test_undeclared_universal_property_is_unchecked(self):
        """Ruling 10: Height is a universal control property, not a custom input —
        cmp_FilterButton never declares it, and that must not be an error."""
        self.assertEqual(errors(self._check(instance("Height", "=40"))), [])

    def test_undeclared_non_universal_property_still_errors(self):
        """The allowlist is a narrow fallback, not a blanket exemption — an
        undeclared property outside it must still be reported."""
        f = errors(self._check(instance("Nonexistent", "=1")))
        self.assertEqual(len(f), 1)


class TestRealTreeIsClean(unittest.TestCase):
    def test_templates_against_shipped_components(self):
        contracts = ccp.load_contracts()
        components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        resolver = ccp.make_resolver(ccp.parse_tokens(
            (SKILL / "templates" / "design-tokens.pa.yaml").read_text(encoding="utf-8")))
        for path in sorted((SKILL / "templates").glob("*.pa.yaml")):
            f = errors(ccp.check_text(path.read_text(encoding="utf-8"), str(path),
                                      contracts, resolver=resolver,
                                      components=components))
            self.assertEqual(f, [], "%s: %s" % (path.name, f))


if __name__ == "__main__":
    unittest.main()
