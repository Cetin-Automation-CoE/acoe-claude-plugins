"""Guard: a `func*(): Void = ...` UDF without a brace body is rejected.

LIVE 2026-09-07 (second run): `templates/App.pa.yaml`'s `funcStartLoading`
and `funcStopLoading` were declared as `funcX(): Void = Set(...);` — a bare
expression body, not a behavior UDF's `{ ... }` form. A Void return type is
only valid on a behavior UDF, so the strict engine rejected both with
"Void return type is only supported with behavior user-defined functions."
and then reported every CALL SITE of each function as unknown — 16 of that
run's 34 errors. `check_references.py` already parses every `App.Formulas`
declaration for the forward-reference check; this adds the brace check to
the same pass rather than writing a second parser.
"""
import pathlib
import subprocess
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_references as cr  # noqa: E402


class TestBracelessVoidUdfIsRejected(unittest.TestCase):
    def test_single_line_bare_expression_body_is_caught(self):
        block = (
            "      funcStartLoading(): Void = Set(glBoolIsLoading, true);\n"
            "      funcStopLoading(): Void = Set(glBoolIsLoading, false);\n"
        )
        found = cr.find_braceless_void_udfs(block)
        self.assertEqual(sorted(found), ["funcStartLoading", "funcStopLoading"])

    def test_multiline_bare_expression_body_is_also_caught(self):
        # The `=` and the body's first token can be on different lines; the
        # check must not be fooled by the newline into thinking there is no
        # body at all.
        block = (
            "      funcDoThing(pKey: Text): Void =\n"
            "          RemoveIf(colItems, Key = pKey);\n"
        )
        self.assertEqual(cr.find_braceless_void_udfs(block), ["funcDoThing"])

    def test_a_non_void_udf_is_never_flagged(self):
        block = "      funcDaysBetween(fromDate: DateTime): Number =\n          fromDate;\n"
        self.assertEqual(cr.find_braceless_void_udfs(block), [])


class TestBracedVoidUdfIsAccepted(unittest.TestCase):
    def test_single_line_brace_body_passes(self):
        block = "      funcStartLoading(): Void = { Set(glBoolIsLoading, true); };\n"
        self.assertEqual(cr.find_braceless_void_udfs(block), [])

    def test_multiline_brace_body_passes(self):
        block = (
            "      funcLoadItems(): Void =\n"
            "      {\n"
            "          ClearCollect(colItems, Table({Key: \"A|1\"}));\n"
            "      };\n"
        )
        self.assertEqual(cr.find_braceless_void_udfs(block), [])

    def test_multiple_params_with_brace_body_passes(self):
        block = (
            "      funcNotify(title: Text, description: Text, color: Color, icon: Text): Void =\n"
            "      {\n"
            "          Collect(colNotifications, {Title: title});\n"
            "      };\n"
        )
        self.assertEqual(cr.find_braceless_void_udfs(block), [])


class TestFixedTemplateNoLongerTriggersTheGuard(unittest.TestCase):
    """Regression proof against the real fixed file, not just a fixture
    string: templates/App.pa.yaml's funcStartLoading/funcStopLoading pair
    (the actual defect) must now pass, and check_references.py run as a
    subprocess against the generic scaffold must exit 0."""

    def test_templates_app_pa_yaml_has_no_braceless_void_udf(self):
        app_text = cr.strip_comments(
            (SKILL / "templates" / "App.pa.yaml").read_text(encoding="utf-8"))
        block = cr.formulas_block(app_text)
        self.assertEqual(cr.find_braceless_void_udfs(block), [])

    def test_check_references_cli_passes_on_a_fresh_scaffold(self):
        import shutil
        import tempfile
        tmp = tempfile.mkdtemp()
        try:
            out = pathlib.Path(tmp) / "Src"
            gen = subprocess.run(
                [sys.executable, str(SKILL / "scripts" / "new_app.py"),
                 "--name", "Void UDF Probe", "--out", str(out)],
                capture_output=True, text=True)
            self.assertEqual(gen.returncode, 0, gen.stdout + gen.stderr)
            proc = subprocess.run(
                [sys.executable, str(SKILL / "scripts" / "check_references.py"),
                 "--src", str(out)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
