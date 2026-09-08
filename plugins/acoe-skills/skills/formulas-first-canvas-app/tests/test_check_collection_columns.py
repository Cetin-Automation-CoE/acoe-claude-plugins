"""Regression test for the false positive check_collection_columns.py
raised on emit_formulas.py's own "SWITCH DAY" comment (Ruling 13).

The guard used to scan raw lines with no comment-stripping at all — the one
sibling of check_tokens.py/check_data_layer.py that didn't — so a `//`
comment merely SHOWING a column name it doesn't validate (e.g.
`// SWITCH DAY: Patch(colAssets, LookUp(colAssets, ID = pKey), {...});`,
which documents the real data-source binding on purpose) was flagged as a
live, broken reference. A comment can never be a real column reference, so
this file tests BOTH directions: a bogus reference inside a `//` comment
must NOT be flagged (the fix), and the identical reference in live code
still MUST be flagged (so the fix isn't just "stop checking anything").
"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_collection_columns as ccc  # noqa: E402

APP_TEMPLATE = """\
App:
  Properties:
    Formulas: |
      =constItemsInScope = colItems;

      funcLoadItems(): Void =
      {{
          ClearCollect(
              colItems,
              Table(
                  {{Key: "A|1", Title: "Example item"}}
              )
          );
      }};

      funcSaveItem(pKey: Text): Void =
      {{
          If(
              IsBlank(LookUp(colItems, Key = pKey)),
              Collect(colItems, {{Key: pKey}}),
              UpdateIf(colItems, Key = pKey, {{}})
          );
{line}
      }};
"""


def run_guard(src):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "check_collection_columns.py"),
         "--src", str(src), "--quiet"],
        capture_output=True, text=True)


class TestCodeOnly(unittest.TestCase):
    """Unit-level: code_only() itself, both directions."""

    def test_strips_a_trailing_comment(self):
        self.assertEqual(
            ccc.code_only('LookUp(colItems, Key = 1) // trailing note'),
            'LookUp(colItems, Key = 1) ')

    def test_strips_a_comment_only_line(self):
        self.assertEqual(
            ccc.code_only('          // SWITCH DAY: Patch(colAssets, LookUp(colAssets, ID = pKey), {...});'),
            '          ')

    def test_leaves_live_code_with_no_comment_untouched(self):
        line = 'LookUp(colItems, Key = pKey)'
        self.assertEqual(ccc.code_only(line), line)

    def test_a_slash_slash_inside_a_quoted_string_is_not_a_comment(self):
        # The exact trap Ruling 13 calls out: a URL (or any "//"-bearing
        # string literal) must survive intact when there is no REAL trailing
        # comment, and must not stop a genuine trailing comment from being
        # found either.
        line = 'Set(glUrl, "https://example.com")'
        self.assertEqual(ccc.code_only(line), line)
        line_with_comment = 'Set(glUrl, "https://example.com") // set the url'
        self.assertEqual(ccc.code_only(line_with_comment),
                         'Set(glUrl, "https://example.com") ')

    def test_quoted_content_survives_for_sortbycolumns_to_read(self):
        # code_only() must NOT blank quoted strings the way
        # check_data_layer.py's does — SortByColumns(colX, "Year", ...)
        # needs the quoted column name intact to match at all.
        line = 'SortByColumns(colItems, "Year", SortOrder.Ascending)'
        self.assertEqual(ccc.code_only(line), line)


class TestCommentedColumnReferenceIsNotFlagged(unittest.TestCase):
    """The fix: a bogus column reference that only ever appears inside a
    `//` comment must not fail the guard."""

    def test_switch_day_style_comment_produces_no_finding(self):
        tmp = tempfile.mkdtemp()
        src = pathlib.Path(tmp) / "Src"
        src.mkdir()
        line = ('          // SWITCH DAY: Patch(colItems, LookUp(colItems, '
                'ID = pKey), {...});')
        (src / "App.pa.yaml").write_text(
            APP_TEMPLATE.format(line=line), encoding="utf-8")
        proc = run_guard(src)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS", proc.stdout)
        self.assertNotIn("colItems.ID", proc.stdout)


class TestLiveColumnReferenceIsStillFlagged(unittest.TestCase):
    """The other direction: the SAME bogus reference, in real (uncommented)
    code, must still fail the guard — this fix must not have gutted the
    check itself."""

    def test_the_same_reference_in_live_code_still_fails(self):
        tmp = tempfile.mkdtemp()
        src = pathlib.Path(tmp) / "Src"
        src.mkdir()
        line = '          Trace(LookUp(colItems, ID = pKey).Title);'
        (src / "App.pa.yaml").write_text(
            APP_TEMPLATE.format(line=line), encoding="utf-8")
        proc = run_guard(src)
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("FAIL", proc.stdout)
        self.assertIn("colItems.ID", proc.stdout)

    def test_a_live_reference_with_a_trailing_comment_on_the_same_line_still_fails(self):
        tmp = tempfile.mkdtemp()
        src = pathlib.Path(tmp) / "Src"
        src.mkdir()
        line = '          Trace(LookUp(colItems, ID = pKey).Title); // note'
        (src / "App.pa.yaml").write_text(
            APP_TEMPLATE.format(line=line), encoding="utf-8")
        proc = run_guard(src)
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("colItems.ID", proc.stdout)


if __name__ == "__main__":
    unittest.main()
