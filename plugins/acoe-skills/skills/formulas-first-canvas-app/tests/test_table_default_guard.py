"""Guard: a `DataType: Table` Input custom property must have a typed Default.

LIVE 2026-09-07 (third run, the first against a genuine coauthoring session):
`cmp_FilterButton.Choices` shipped a BLANK Default (`Default: =`), which
cannot establish a concrete table schema — the Studio silently falls back to
a placeholder schema (`SampleBooleanField`/`SampleNumberField`/
`SampleStringField`), and a caller's real table then fails to type-match it.
Same defect already fixed once on `cmp_FieldChoice.Choices` in the prior
round. This test file exists so a repeat of the BLANK shape fails locally
instead of live.

`cmp_Navigation.Screens`'s `Default: =constScreens` was flagged bad through
this same run on the theory that a bare app-scope named-formula reference
also cannot establish a schema. LIVE 2026-09-07 (fourth run) disproved that:
bisecting a validator crash showed the third run's 2
`cmp_*_Navigation.Screens` errors were a CASCADE from `cmp_FilterButton`'s
blank default in the same push, and a bare `=constScreens` on its own
compiles with zero errors. A bare name/dotted reference is therefore NOT
flagged — only a genuinely blank Default is. See
`references/compile-error-playbook.md` for the full trail.
"""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402


def errors(findings):
    return [f for f in findings if f.severity == "error"]


def component_def(default_line, prop_kind="Input", datatype="Table", prop_name="Choices"):
    return (
        "ComponentDefinitions:\n"
        "  cmp_X:\n"
        "    DefinitionType: CanvasComponent\n"
        "    CustomProperties:\n"
        "      %s:\n"
        "        PropertyKind: %s\n"
        "        DisplayName: %s\n"
        "        DataType: %s\n"
        "        %s\n" % (prop_name, prop_kind, prop_name, datatype, default_line)
    )


class TestBadTableDefaultsAreCaught(unittest.TestCase):
    """The one shape confirmed live: blank."""

    def test_blank_default_is_an_error(self):
        text = component_def("Default: =")
        findings = errors(ccp.find_bad_table_defaults(text, "f.pa.yaml"))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].control, "cmp_X")
        self.assertEqual(findings[0].prop, "Choices")


class TestBareReferencesAreNotFlagged(unittest.TestCase):
    """LIVE 2026-09-07 (fourth run): a bare app-scope named-formula
    reference is proven correct (`cmp_Navigation.Screens`'s
    `Default: =constScreens`), not bad — the third run's errors on this
    shape were a cascade from an unrelated component's blank default. The
    guard must not flag the exact shape the live compiler accepts.
    """

    def test_bare_app_scope_name_reference_is_not_flagged(self):
        # The exact live shape: cmp_Navigation.Screens's `Default: =constScreens`.
        text = component_def("Default: =constScreens", prop_name="Screens")
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])

    def test_dotted_bare_reference_is_also_not_flagged(self):
        text = component_def("Default: =App.SomeGlobal")
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])


class TestTypedTableDefaultsPass(unittest.TestCase):
    def test_single_line_table_literal_passes(self):
        text = component_def('Default: =Table({Value: ""})')
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])

    def test_block_scalar_table_literal_passes(self):
        text = (
            "ComponentDefinitions:\n"
            "  cmp_X:\n"
            "    DefinitionType: CanvasComponent\n"
            "    CustomProperties:\n"
            "      Choices:\n"
            "        PropertyKind: Input\n"
            "        DataType: Table\n"
            "        Default: |-\n"
            '          =Table({Value: ""})\n'
        )
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])

    def test_bracket_table_literal_passes(self):
        # cmp_Notification.Notifications's real shape: `=[ {...} ]`.
        text = (
            "ComponentDefinitions:\n"
            "  cmp_X:\n"
            "    DefinitionType: CanvasComponent\n"
            "    CustomProperties:\n"
            "      Notifications:\n"
            "        PropertyKind: Input\n"
            "        DataType: Table\n"
            "        Default: |-\n"
            "          =[\n"
            "              {\n"
            '                  Title: "Title"\n'
            "              }\n"
            "          ]\n"
        )
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])

    def test_multi_row_inline_table_literal_passes(self):
        text = component_def(
            'Default: =Table({Value: "A"}, {Value: "B"})')
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])


class TestOnlyInputTableIsChecked(unittest.TestCase):
    def test_output_property_is_not_checked(self):
        text = component_def("DataType: Table", prop_kind="Output")
        # Output properties normally carry no Default line at all — still
        # must not explode, and must not be flagged even if one is present.
        text_no_default = (
            "ComponentDefinitions:\n"
            "  cmp_X:\n"
            "    DefinitionType: CanvasComponent\n"
            "    CustomProperties:\n"
            "      Value:\n"
            "        PropertyKind: Output\n"
            "        DataType: Table\n"
        )
        self.assertEqual(errors(ccp.find_bad_table_defaults(text_no_default, "f.pa.yaml")), [])

    def test_text_typed_blank_default_is_not_checked(self):
        text = component_def("Default: =", datatype="Text")
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])

    def test_event_kind_is_not_checked(self):
        text = component_def("Default: =false", prop_kind="Event", datatype="Table")
        self.assertEqual(errors(ccp.find_bad_table_defaults(text, "f.pa.yaml")), [])


class TestShippedComponentsAreAllClean(unittest.TestCase):
    """Every `cmp_*.pa.yaml` this skill ships must pass the guard — this is
    the regression proof that the live fixes to cmp_FilterButton.{Choices,
    Items} and cmp_Navigation.Screens actually stuck."""

    def test_no_shipped_component_has_a_bad_table_default(self):
        comp_dir = SKILL / "components"
        all_findings = []
        for path in sorted(comp_dir.glob("cmp_*.pa.yaml")):
            text = path.read_text(encoding="utf-8")
            all_findings.extend(
                errors(ccp.find_bad_table_defaults(text, str(path))))
        self.assertEqual(
            all_findings, [],
            "shipped component(s) have a Table-typed Default that "
            "establishes no schema: %s" % all_findings)


if __name__ == "__main__":
    unittest.main()
