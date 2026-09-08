"""The plan's Definition of Done, executable: a one-entity model and a
three-entity model each produce a guard-clean, RENDERING app.

This is deliberately not the same fixture shape as tests/test_new_app_model.py
(two entities, both with a single choice field and no money/date/longtext/
boolean mix) or tests/test_new_app_model_assembly.py's THREE_ENTITY (a
forward-reference probe with no money, no date, no longtext, no boolean).
Task 9's brief for this file asks for genuinely different per-entity shapes —
one entity mixing money and dates, one with only text and choice, one with a
longtext and a boolean — so this file exercises code paths (money formatting,
due-date mock generation, longtext controls, boolean toggles, multi-choice
vocab coverage) the other end-to-end tests do not combine in one run.

WHY THIS FILE EXISTS, specifically: the defect that started this whole effort
was a scaffolder that printed "All checks pass" over an app whose mock rows
had been Clear()ed right after being seeded — every generated app rendered as
an empty grid the moment it was opened in a live environment. "The guards
pass" and "the app renders something real" are different claims; every
assertion below is chosen to pin down the second, not just the first. File
existence alone is never treated as sufficient evidence.

Every check here is a require-to-hold assertion, not a threshold tuned to
whatever the generator happened to emit — if the generator's output does not
satisfy one of these, that is a defect in the generator, to be reported
against the emitter/guard in question, not "fixed" by loosening this test.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from model import Model  # noqa: E402  (used to compute expected names/vocab)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# One entity, but not a trivial one: two choice fields (so multi-choice-field
# vocab coverage is exercised even in the single-entity case), a due date, a
# boolean and a search field.
ONE_ENTITY_YAML = textwrap.dedent("""\
    app_name: Task Tracker
    brand: "#300091"
    entities:
      - entity: Task
        plural: Tasks
        group: Work
        fields:
          - {name: Title,    type: text,    required: true, grid: flex, search: true, samples: [Draft proposal, Review budget]}
          - {name: Status,   type: choice,  required: true, grid: 120,  filter: true, vocab: [Todo, Doing, Done]}
          - {name: Priority, type: choice,  grid: 110, filter: chips, vocab: [Low, Medium, High]}
          - {name: DueDate,  type: date,    grid: 112, semantics: due}
          - {name: Done,     type: boolean, grid: 90}
    """)

# Three entities, genuinely different shapes:
#   Invoice - money + a due date
#   Contact - only text and choice, nothing else
#   Ticket  - a longtext field and a boolean, no money/date at all
THREE_ENTITY_YAML = textwrap.dedent("""\
    app_name: Ops Suite
    brand: "#300091"
    entities:
      - entity: Invoice
        plural: Invoices
        group: Finance
        fields:
          - {name: Number,   type: text,    required: true, grid: 110, search: true, samples: [INV-1001, INV-1002]}
          - {name: Status,   type: choice,  required: true, grid: 120, filter: true, vocab: [Open, Paid, Overdue]}
          - {name: Amount,   type: number,  grid: 118, money: true, currency: EUR, min: 0}
          - {name: DueDate,  type: date,    grid: 112, semantics: due}
      - entity: Contact
        plural: Contacts
        group: Sales
        fields:
          - {name: Name,     type: text,   required: true, grid: flex, search: true, samples: [Jana Novakova, Petr Svoboda]}
          - {name: Category, type: choice, required: true, grid: 130, filter: true, vocab: [Lead, Customer, Partner]}
      - entity: Ticket
        plural: Tickets
        group: Support
        fields:
          - {name: Summary,  type: longtext, grid: hidden}
          - {name: Priority, type: choice,   required: true, grid: 110, filter: chips, vocab: [Low, Medium, High]}
          - {name: Resolved, type: boolean,  grid: 90}
    """)

# Rows per entity for these runs. Deliberately not the CLI default (16) so
# this test also proves --rows is honoured end to end; large enough that
# every vocab list here (max 3 values) cycles at least once with headroom.
ROWS = 10

GENERIC_IDENTIFIERS = ("colItems", "funcSaveItem", "locItem")


def _run(model_yaml, rows=ROWS):
    """Write `model_yaml` to a temp file and invoke new_app.py exactly as a
    user would (subprocess, real CLI args). Returns (proc, out_dir, tmp_dir);
    caller is responsible for cleaning up tmp_dir."""
    tmp = tempfile.mkdtemp()
    model_path = pathlib.Path(tmp) / "model.yaml"
    model_path.write_text(model_yaml, encoding="utf-8")
    out = pathlib.Path(tmp) / "Src"
    proc = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "new_app.py"),
         "--model", str(model_path), "--out", str(out), "--rows", str(rows)],
        capture_output=True, text=True)
    return proc, out, tmp


class _AcceptanceBase(object):
    """Shared assertions for one generated app. Subclasses set up
    cls.proc / cls.out / cls.model / cls.rows in setUpClass and provide
    tearDownClass to remove the temp tree.

    Inheriting from `object` (not TestCase) keeps this base's methods from
    being collected and run on their own — only the two concrete subclasses
    below (which set up real fixtures) run them.
    """

    # ---- 1. the process itself -----------------------------------------
    def test_exits_zero(self):
        # A non-zero exit with a broken tree left behind is exactly the
        # "All checks pass" defect's sibling failure mode: this must be the
        # very first thing checked, since nothing below means anything if
        # the run didn't succeed.
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout + self.proc.stderr)

    # ---- 2. every guard reports PASS ------------------------------------
    def test_at_least_six_guards_pass(self):
        # >=6, not ==6 or ==7: a future guard addition must not break this
        # test. (Six check_*.py guards plus the YAML-well-formedness
        # pre-check both print "PASS" today; asserting a floor rather than
        # an exact count is the point.)
        out = self.proc.stdout
        self.assertGreaterEqual(out.count("PASS"), 6, out)
        # And there must be no FAIL anywhere in the run's own report — a
        # generator that prints both PASS and FAIL lines (partial failure)
        # must not slip past a bare ">=6 PASS" count.
        self.assertNotIn("FAIL", out, out)

    # ---- 3. expected screen count: one list + one form per entity -------
    def test_one_list_and_one_form_screen_per_entity(self):
        for entity in self.model.entities:
            list_file = self.out / (entity.list_screen + ".pa.yaml")
            form_file = self.out / (entity.form_screen + ".pa.yaml")
            self.assertTrue(list_file.exists(), list_file)
            self.assertTrue(form_file.exists(), form_file)
            # Not just present — non-trivially sized. An empty or near-empty
            # file existing on disk is not a screen; this is the file-
            # existence-is-not-the-bar check made concrete.
            self.assertGreater(list_file.stat().st_size, 200, list_file)
            self.assertGreater(form_file.stat().st_size, 200, form_file)
        expected_screens = 2 * len(self.model.entities)
        actual_screens = len(list(self.out.glob("*ListScreen.pa.yaml"))) + \
            len(list(self.out.glob("*FormScreen.pa.yaml")))
        self.assertEqual(actual_screens, expected_screens)

    # ---- 4. mock rows present AND not cleared ----------------------------
    def test_mock_rows_present_and_not_cleared(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        for entity in self.model.entities:
            # ClearCollect must exist for every entity's collection — the
            # seeding call itself. (The real emitted shape wraps the
            # collection name onto its own indented line inside
            # `ClearCollect(\n    colX,\n    Table(...)\n);`, so match with
            # whitespace tolerance rather than assuming it is on the same
            # line as the call.)
            seed_re = re.compile(r"ClearCollect\(\s*%s\s*,"
                                 % re.escape(entity.collection))
            self.assertRegex(app, seed_re,
                             "%s never seeded" % entity.collection)
            # The specific defect that reached production: a bare Clear()
            # right after ClearCollect wipes every row back out, and no
            # guard below ever notices because the file still parses, still
            # references real names, and still has well-formed control
            # props. This is the one assertion in this whole file that maps
            # directly onto that incident.
            self.assertNotIn("Clear(%s)" % entity.collection, app,
                             "%s was Clear()ed after being seeded — this is "
                             "the empty-grid defect" % entity.collection)
        # Total quoted Key literals across the whole file == rows * entities
        # — the row count actually generated matches what was asked for,
        # ('{Key: "' matches only mock-row literals, not the save UDFs'
        # `{Key: pKey, ...}` Collect() record, which has no quote after
        # 'Key: '.)
        self.assertEqual(app.count('{Key: "'), ROWS * len(self.model.entities))

    # ---- 5. every choice field's vocab is fully represented --------------
    def test_every_vocab_value_appears_in_mock_data(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        for entity in self.model.entities:
            for field in entity.choice_fields:
                for value in field.vocab:
                    literal = '"%s"' % value
                    self.assertIn(literal, app,
                                 "%s.%s: vocab value %r never appears in mock "
                                 "data — a filter on this value would render "
                                 "an empty grid" % (entity.entity, field.name, value))

    # ---- 6. nav registry: two constScreens rows per entity, plus the ------
    #        dashboard row when the model has one
    def test_nav_registry_has_two_rows_per_entity_plus_dashboard(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("constScreens = [", app)
        # Scope every count to the registry block itself, not the whole
        # file: a list screen's name also appears once more outside the
        # registry (the OnStart colBack seed names the first entity's list
        # screen), so counting "Screen: <name>," across the whole file
        # over-counts that one row by one — this must not be mistaken for a
        # duplicate registry entry.
        start = app.index("constScreens = [")
        end = app.index("];", start)
        registry = app[start:end]
        for entity in self.model.entities:
            self.assertEqual(registry.count("Screen: %s," % entity.list_screen), 1,
                             "%s missing (or duplicated) in constScreens"
                             % entity.list_screen)
            self.assertEqual(registry.count("Screen: %s," % entity.form_screen), 1,
                             "%s missing (or duplicated) in constScreens"
                             % entity.form_screen)
        # Total row count: exactly 2 per entity, not accidentally shared
        # across entities and not double-counted — PLUS one more List-typed
        # row when `dashboard` is on (Task 5 defaults it on for >1 entity):
        # Ruling 10 types that row List too, so cmp_Navigation renders it.
        expected_list = len(self.model.entities) + (1 if self.model.dashboard else 0)
        self.assertEqual(registry.count("Type: enumScreenType.List,"), expected_list)
        self.assertEqual(registry.count("Type: enumScreenType.Form,"), len(self.model.entities))
        if self.model.dashboard:
            self.assertIn("Screen: DashboardScreen", registry)

    # ---- 7. no generic template identifier leaked -------------------------
    def test_no_generic_template_identifier_leaked(self):
        for p in self.out.rglob("*.pa.yaml"):
            text = p.read_text(encoding="utf-8")
            for leaked in GENERIC_IDENTIFIERS:
                self.assertNotIn(leaked, text, "%s leaked into %s" % (leaked, p.name))
        # And the positive side of the same claim: entity-derived names are
        # actually present, so this isn't passing because nothing was
        # generated at all.
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        for entity in self.model.entities:
            self.assertIn(entity.collection, app)
            self.assertIn(entity.func_save, app)

    # ---- 9. C1: constScreens is referenced, not just defined --------------
    def test_constscreens_is_referenced_not_just_defined(self):
        """The nav rail's menu gallery reads `Filter(cmp_Navigation.Screens,
        ...)`, and the component's own Default is only a one-row typed seed
        (proven live) — nothing shows in the rail unless some INSTANCE
        overrides Screens with the app-scope constScreens. A build where
        constScreens is defined in App.pa.yaml but never read anywhere else
        is the exact empty-nav-rail defect (C1, final review).

        Checks for the literal `Screens: =constScreens` REFERENCE shape, not
        just the bare identifier: the shipped cmp_Navigation.pa.yaml's own
        prose comments ("Reads the constScreens REGISTRY", "Defaults to the
        app-wide constScreens") already mention the bare word in every
        generated app, fixed or not — a substring check on the bare name
        alone would pass even with the defect still present."""
        for p in self.out.rglob("*.pa.yaml"):
            if p.name == "App.pa.yaml":
                continue
            if "Screens: =constScreens" in p.read_text(encoding="utf-8"):
                return
        self.fail("constScreens is defined in App.pa.yaml but no "
                 "'Screens: =constScreens' instance override was found "
                 "anywhere else in the generated tree — the nav rail would "
                 "render empty")

    # ---- 8. all eight base components are written -------------------------
    def test_all_base_components_written(self):
        base = ("cmp_Header", "cmp_Navigation", "cmp_CommandBar",
                "cmp_FilterButton", "cmp_Notification", "cmp_Dialog",
                "cmp_Empty", "cmp_Spinner")
        for name in base:
            f = self.out / "Components" / (name + ".pa.yaml")
            self.assertTrue(f.exists(), f)
            self.assertGreater(f.stat().st_size, 0, f)


class TestOneEntityModel(_AcceptanceBase, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Model(_yaml_load(ONE_ENTITY_YAML))
        cls.proc, cls.out, cls.tmp = _run(ONE_ENTITY_YAML)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- Task 8: dashboard wired — StartScreen, registry, editor order ----
    #      ONE_ENTITY_YAML has a single entity, so Model.dashboard defaults
    #      OFF (Task 5) — Ruling 16: this fixture is not changed to force
    #      it on; these assertions cover the dashboard-off path.
    def test_no_dashboard_screen_written(self):
        self.assertFalse(self.model.dashboard,
                         "fixture must default dashboard off with 1 entity")
        self.assertFalse((self.out / "DashboardScreen.pa.yaml").exists())

    def test_start_screen_is_its_list_screen(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("StartScreen: =%s" % self.model.entities[0].list_screen, app)

    def test_cmp_navigation_default_points_at_its_list_screen(self):
        # Ruling 18: the copied component's Screens default is rewritten to
        # name this build's real first screen — never left pointing at the
        # generic shipped template's ListScreen, a name this app never
        # defines.
        nav = (self.out / "Components" / "cmp_Navigation.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("Screen: %s" % self.model.entities[0].list_screen, nav)
        self.assertNotIn("Screen: ListScreen", nav)


class TestThreeEntityModel(_AcceptanceBase, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Model(_yaml_load(THREE_ENTITY_YAML))
        cls.proc, cls.out, cls.tmp = _run(THREE_ENTITY_YAML)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- Task 8: dashboard wired — StartScreen, registry, editor order ----
    #      THREE_ENTITY_YAML has three entities, so Model.dashboard defaults
    #      ON (Task 5) — Ruling 16: this existing fixture already has an
    #      entity (Invoice) pairing a money field with a filter: true choice
    #      field, so the KPI band is eligible too; no new fixture, no
    #      `dashboard: true` added anywhere.
    def test_dashboard_screen_written(self):
        self.assertTrue(self.model.dashboard,
                        "fixture must default dashboard on with 3 entities")
        dash_file = self.out / "DashboardScreen.pa.yaml"
        self.assertTrue(dash_file.exists(), dash_file)
        # Not just present — the file-existence-is-not-the-bar check this
        # whole module is built around (see the module docstring).
        self.assertGreater(dash_file.stat().st_size, 200, dash_file)

    def test_start_screen_is_the_dashboard(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("StartScreen: =DashboardScreen", app)

    def test_dashboard_band_is_spliced_into_app(self):
        # Invoice has both a money field (Amount) and a filterable Status
        # field, so the KPI band is eligible and its named formula must be
        # spliced into App.pa.yaml.
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("constDashboardBand", app)

    def test_editor_state_lists_dashboard_first(self):
        lines = (self.out / "_EditorState.pa.yaml").read_text(encoding="utf-8").splitlines()
        order_at = lines.index("  ScreensOrder:")
        self.assertEqual(lines[order_at + 1].strip(), "- DashboardScreen",
                         "DashboardScreen must be the first entry under "
                         "ScreensOrder:\n%s" % "\n".join(lines))

    def test_dashboard_registry_row_is_first_and_typed_list(self):
        # Ruling 10 (Phase 3 Task 8 dispatch): there is no
        # enumScreenType.Dashboard. cmp_Navigation renders
        # Filter(Screens, Type = enumScreenType.List), so the dashboard's
        # own constScreens row must be typed List (not something else that
        # would make the start screen unreachable from the nav rail) and
        # must be the FIRST row in the registry.
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        start = app.index("constScreens = [")
        end = app.index("];", start)
        registry = app[start:end]
        first_row = registry[registry.index("{"):registry.index("}") + 1]
        self.assertIn("Screen: DashboardScreen,", first_row)
        self.assertIn("Type: enumScreenType.List,", first_row)

    def test_cmp_navigation_default_points_at_the_dashboard(self):
        # Ruling 18: same rewrite as the one-entity case, but the build's
        # real first screen here is the dashboard, not any entity's list
        # screen.
        nav = (self.out / "Components" / "cmp_Navigation.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("Screen: DashboardScreen", nav)
        self.assertNotIn("Screen: ListScreen", nav)


class TestLegacyNamePath(unittest.TestCase):
    """The --name (legacy) path is untouched by Task 8's dashboard wiring —
    Ruling 18(b) says it "copies the file unchanged". No existing test class
    runs this path once in setUpClass the way the --model classes above do,
    so this one generates a single legacy build to guard that one invariant:
    the copied Components/cmp_Navigation.pa.yaml must be byte-identical to
    the shipped components/cmp_Navigation.pa.yaml — only a --model build may
    rewrite its Screens default's Screen column (Ruling 18(b))."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.out = pathlib.Path(cls.tmp) / "Src"
        cls.proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "new_app.py"),
             "--name", "Legacy", "--out", str(cls.out)],
            capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_exits_zero(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout + self.proc.stderr)

    def test_cmp_navigation_is_copied_byte_identical(self):
        shipped = (SKILL / "components" / "cmp_Navigation.pa.yaml").read_text(encoding="utf-8")
        copied = (self.out / "Components" / "cmp_Navigation.pa.yaml").read_text(encoding="utf-8")
        self.assertEqual(copied, shipped,
                         "the --name (legacy) path must copy "
                         "cmp_Navigation.pa.yaml unchanged — only a --model "
                         "build rewrites its Screens default's Screen column")

    def test_list_screen_nav_instance_binds_the_registry(self):
        """C1 (final review, CRITICAL): the legacy --name path's own
        ListScreen.pa.yaml template must set Screens: =constScreens on its
        cmp_List_Navigation instance too — the component's own Default is
        only a one-row typed seed, never the real registry."""
        listing = (self.out / "ListScreen.pa.yaml").read_text(encoding="utf-8")
        self.assertIn("Screens: =constScreens", listing)


def _yaml_load(text):
    import yaml
    return yaml.safe_load(text)


if __name__ == "__main__":
    unittest.main()
