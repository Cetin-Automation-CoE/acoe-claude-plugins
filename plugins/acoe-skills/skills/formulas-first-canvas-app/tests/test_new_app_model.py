"""End-to-end: a model in, a guard-clean multi-entity app out."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]

TWO_ENTITY = textwrap.dedent("""\
    app_name: Ops Register
    brand: "#300091"
    entities:
      - entity: Asset
        plural: Assets
        group: Operations
        fields:
          - {name: Tag, type: text, required: true, grid: 100, search: true, samples: [EQ-1, EQ-2]}
          - {name: Status, type: choice, required: true, grid: 120, filter: true, vocab: [Open, Shut]}
          - {name: Amount, type: number, grid: 118, money: true, min: 0}
          - {name: Due, type: date, grid: 112, semantics: due}
      - entity: Site
        plural: Sites
        group: Operations
        fields:
          - {name: Name, type: text, required: true, grid: flex, search: true}
          - {name: Status, type: choice, required: true, grid: 120, filter: true, vocab: [Live, Closed]}
    """)


class TestGenerateTwoEntityApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        model = pathlib.Path(cls.tmp) / "model.yaml"
        model.write_text(TWO_ENTITY, encoding="utf-8")
        cls.out = pathlib.Path(cls.tmp) / "Src"
        cls.proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "new_app.py"),
             "--model", str(model), "--out", str(cls.out), "--rows", "12"],
            capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_exits_zero(self):
        self.assertEqual(self.proc.returncode, 0,
                         self.proc.stdout + self.proc.stderr)

    def test_all_guards_report_pass(self):
        self.assertGreaterEqual(self.proc.stdout.count("PASS"), 6, self.proc.stdout)

    def test_one_list_and_one_form_screen_per_entity(self):
        for f in ("AssetsListScreen.pa.yaml", "AssetFormScreen.pa.yaml",
                  "SitesListScreen.pa.yaml", "SiteFormScreen.pa.yaml"):
            self.assertTrue((self.out / f).exists(), f)

    def test_mock_rows_are_present_and_not_cleared(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        # '{Key: "' (quoted) matches only mock-row literals: 12 rows x 2
        # entities. The brief's original substring, '{Key:' (unquoted),
        # ALSO matches funcSaveAsset/funcSaveSite's `{Key: pKey, ...}`
        # Collect() record (emit_formulas.py's _save_spec, unmodifiable —
        # see the task brief), which would make this count 26, not 24, with
        # no mock-row deficiency at all. Quoting keeps the test's original
        # intent (mock rows present, in the right quantity) accurate.
        self.assertEqual(app.count('{Key: "'), 24)   # 12 rows x 2 entities
        self.assertNotIn("Clear(colAssets)", app)
        self.assertNotIn("Clear(colSites)", app)

    def test_navigation_registry_lists_all_four_screens_plus_dashboard(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        # Ruling 13: TWO_ENTITY has two entities, so `dashboard` defaults on
        # (Task 5) — two entity list rows plus the dashboard row, which is
        # typed List (Ruling 10) so cmp_Navigation renders it in the nav rail.
        self.assertEqual(app.count("Type: enumScreenType.List"), 3)
        self.assertEqual(app.count("Type: enumScreenType.Form"), 2)
        self.assertIn("Screen: DashboardScreen", app)

    def test_no_generic_template_identifier_leaked(self):
        for p in self.out.rglob("*.pa.yaml"):
            text = p.read_text(encoding="utf-8")
            for leaked in ("colItems", "funcSaveItem", "locItem"):
                self.assertNotIn(leaked, text, "%s in %s" % (leaked, p.name))

    def test_all_eight_components_are_written(self):
        # 8 original + 4 per-type field components (Task 6, hand-authoring
        # library — a --model build always writes every ALL_COMPONENTS entry).
        self.assertEqual(len(list((self.out / "Components").glob("cmp_*.pa.yaml"))), 12)


class TestBadModelFailsBeforeWriting(unittest.TestCase):
    def test_invalid_model_exits_nonzero_and_writes_nothing(self):
        tmp = tempfile.mkdtemp()
        model = pathlib.Path(tmp) / "model.yaml"
        model.write_text("app_name: X\nentities:\n  - entity: A\n    plural: As\n"
                         "    fields:\n      - {name: S, type: choice}\n",
                         encoding="utf-8")
        out = pathlib.Path(tmp) / "Src"
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "new_app.py"),
             "--model", str(model), "--out", str(out)],
            capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("vocab", proc.stdout + proc.stderr)
        self.assertFalse(out.exists() and any(out.iterdir()))
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
