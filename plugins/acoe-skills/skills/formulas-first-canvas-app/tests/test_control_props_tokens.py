"""Layer 2: resolve constStyle.* token references before checking enum namespaces."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

TOKENS = """\
constStyle = {
    Label: {
        TextLabel: {
            AlignModern: 'TextCanvas.Align'.Start,
            AlignLegacy: Align.Left,
            PaddingLeft: 8
        },
        NumberInput: {
            AlignModern: 'TextCanvas.Align'.End,
            AlignLegacy: Align.Right,
            PaddingLeft: 8
        }
    },
    Button: {
        Height: {Large: 40, Medium: 32}
    }
};
"""


def errors(findings):
    return [f for f in findings if f.severity == "error"]


class TestTokenParsing(unittest.TestCase):
    def test_builds_dotted_paths(self):
        m = ccp.parse_tokens(TOKENS)
        self.assertEqual(m["constStyle.Label.NumberInput.AlignModern"],
                         "'TextCanvas.Align'.End")
        self.assertEqual(m["constStyle.Label.NumberInput.AlignLegacy"], "Align.Right")
        self.assertEqual(m["constStyle.Label.TextLabel.AlignModern"],
                         "'TextCanvas.Align'.Start")

    def test_inline_records_do_not_break_the_parser(self):
        m = ccp.parse_tokens(TOKENS)
        self.assertNotIn("constStyle.Button.Height.Large", m)
        self.assertIn("constStyle.Label.TextLabel.PaddingLeft", m)


class TestResolvedEnumChecking(unittest.TestCase):
    def setUp(self):
        self.contracts = ccp.load_contracts()
        self.resolver = ccp.make_resolver(ccp.parse_tokens(TOKENS))

    def _check(self, control, prop, value):
        text = (
            "      - c1:\n"
            "          Control: %s\n"
            "          Properties:\n"
            "            %s: %s\n" % (control, prop, value)
        )
        return ccp.check_text(text, "t.pa.yaml", self.contracts, resolver=self.resolver)

    def test_defect_8_wrong_namespace_laundered_through_a_token(self):
        """This is the case a line-oriented guard cannot see."""
        f = errors(self._check("ModernText", "Align",
                               "=constStyle.Label.NumberInput.AlignLegacy"))
        self.assertEqual(len(f), 1)
        self.assertIn("End", f[0].message)

    def test_correct_token_field_is_clean(self):
        self.assertEqual(
            errors(self._check("ModernText", "Align",
                               "=constStyle.Label.NumberInput.AlignModern")), [])

    def test_legacy_token_on_a_button_is_clean(self):
        self.assertEqual(
            errors(self._check("Button", "Align",
                               "=constStyle.Label.NumberInput.AlignLegacy")), [])

    def test_unknown_token_path_is_unresolved_not_an_error(self):
        self.assertEqual(
            errors(self._check("ModernText", "Align", "=constStyle.Nope.Missing")), [])


class TestRealTemplatesResolve(unittest.TestCase):
    def test_shipped_tokens_parse_and_the_templates_are_clean(self):
        tokens = (SKILL / "templates" / "design-tokens.pa.yaml").read_text(encoding="utf-8")
        mapping = ccp.parse_tokens(tokens)
        self.assertIn("constStyle.Label.NumberInput.AlignModern", mapping)
        resolver = ccp.make_resolver(mapping)
        contracts = ccp.load_contracts()
        for name in ("ListScreen.pa.yaml", "FormScreen.pa.yaml"):
            path = SKILL / "templates" / name
            f = errors(ccp.check_text(path.read_text(encoding="utf-8"),
                                      str(path), contracts, resolver=resolver))
            self.assertEqual(f, [], "%s: %s" % (name, f))


if __name__ == "__main__":
    unittest.main()
