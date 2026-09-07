"""Assembled-file forward-reference check (Ruling 5).

emit_formulas.py's own forward-reference test (tests/test_emit_formulas.py)
only scans the text IT emits. Task 5 splices that text into
templates/App.pa.yaml AROUND static template content emit_formulas.py never
sees — the pure helper UDFs, the loading-indicator pair, the colBack /
navigation-stack helpers, and the UI utility UDFs. A forward reference
introduced at the SEAM between emitted and static content would not be
caught by emit_formulas.py's own tests, and it is the worst failure mode
this project has: the studio binder drops the ENTIRE Formulas blob and every
screen reports "unknown name" with nothing pointing at the cause.

This test scans the ASSEMBLED App.pa.yaml a real `new_app.py --model` run
produces, reusing check_references.py's own (already-tested, already
guard-approved) definition/use patterns rather than re-implementing them —
so a false pass here would mean the guard itself is broken, not just this
test. It also runs check_references.py directly against the assembled tree
as a second, independent confirmation of the same property.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_references as cr  # noqa: E402

# Three entities, deliberately in a different shape than the brief's fixture
# (mixed choice/non-choice fields, one entity with no choice field at all) so
# this exercises a different topo_sort tie-break path than the two-entity
# case Task 5's main contract test already covers.
THREE_ENTITY = textwrap.dedent("""\
    app_name: Forward Ref Probe
    entities:
      - entity: Alpha
        plural: Alphas
        fields:
          - {name: Code, type: text, required: true, grid: 100}
          - {name: Kind, type: choice, required: true, grid: 120, vocab: [One, Two]}
      - entity: Beta
        plural: Betas
        fields:
          - {name: Label, type: text, required: true, grid: flex}
          - {name: Mood, type: choice, required: true, grid: 120, vocab: [Good, Bad, Ugly]}
      - entity: Gamma
        plural: Gammas
        fields:
          - {name: Note, type: text, grid: flex}
    """)


class TestAssembledAppHasNoForwardReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        model = pathlib.Path(cls.tmp) / "model.yaml"
        model.write_text(THREE_ENTITY, encoding="utf-8")
        cls.out = pathlib.Path(cls.tmp) / "Src"
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "new_app.py"),
             "--model", str(model), "--out", str(cls.out), "--rows", "3"],
            capture_output=True, text=True)
        cls.proc = proc
        cls.app_text = (cls.out / "App.pa.yaml").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_generation_wrote_an_app_pa_yaml(self):
        # A sanity gate for the two tests below: if this fails, they would
        # otherwise fail on a missing/empty file with a confusing message.
        self.assertTrue((self.out / "App.pa.yaml").exists(),
                        self.proc.stdout + self.proc.stderr)

    def test_no_name_is_used_before_its_definition(self):
        """Independently re-run check_references.py's own order-check logic
        (its DEF_PATTERNS / USE_PATTERN / strip_comments / formulas_block —
        not a reimplementation) directly against the assembled Formulas
        block, in-process, so a failure here points straight at a line."""
        block = cr.strip_comments(cr.formulas_block(self.app_text))
        order = []
        for pat in cr.DEF_PATTERNS:
            for m in pat.finditer(block):
                order.append((m.group(1), m.start()))
        pos = {}
        for name, start in order:
            pos.setdefault(name, start)

        forward = []
        for name, start in order:
            # A UDF may reference a named formula declared later — only a
            # named-formula -> named-formula reference is a real forward
            # reference to the studio binder. See check_references.py.
            if name.startswith("func"):
                continue
            later = [p for _, p in order if p > start]
            end = min(later) if later else len(block)
            body = block[start:end]
            for used in set(cr.USE_PATTERN.findall(body)):
                if (used in pos and pos[used] > start and used != name
                        and not used.startswith("func")):
                    forward.append((name, used))
        self.assertEqual(forward, [],
                         "forward reference(s) in the assembled App.pa.yaml: %r"
                         % (forward,))

    def test_check_references_guard_passes_on_the_assembled_tree(self):
        """Second, independent confirmation: the actual guard script, run
        the same way new_app.py itself runs it."""
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "check_references.py"),
             "--src", str(self.out)],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
