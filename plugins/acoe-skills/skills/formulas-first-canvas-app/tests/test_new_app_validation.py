"""Final whole-branch review fix wave: CLI-level guards new_app.py must
enforce on its own, before writing anything.

C3/Ruling 17: --rows 0 emits an empty, untyped Table() — the founding
empty-app defect, with six guard PASS lines printed over it.

Ruling 23: --components was silently ignored with --model (a --model build
always writes all twelve regardless of the flag) — accepting a flag and
discarding it is the same trust failure as a guard printing PASS over broken
output.

C2/Ruling 16: a '#' in any model string (or a legacy --name) used to
truncate the emitted Power Fx, because YAML treats a space followed by '#'
as the start of a COMMENT in a plain scalar — the file stays perfectly valid
YAML, which is exactly why no well-formedness check could ever see it.
"""
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[1]
NEW_APP = SKILL / "scripts" / "new_app.py"
MODEL_EXAMPLE = SKILL / "templates" / "model.example.yaml"

HASH_MODEL = textwrap.dedent("""\
    app_name: Ops
    entities:
      - entity: Order
        plural: Orders
        fields:
          - {name: Reference, type: text, grid: 140, label: "ORDER # REF", samples: ["A#1"]}
          - {name: Status, type: choice, grid: 120, vocab: [Open, Shut]}
    """)


def run(*args):
    return subprocess.run([sys.executable, str(NEW_APP), *args],
                          capture_output=True, text=True)


class TestRowsRejection(unittest.TestCase):
    def test_rows_zero_is_rejected_before_writing_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--model", str(MODEL_EXAMPLE), "--rows", "0", "--out", str(out))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--rows must be at least 1", r.stdout + r.stderr)
            self.assertFalse(out.exists(), "a rejected --rows must write nothing")

    def test_negative_rows_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--model", str(MODEL_EXAMPLE), "--rows", "-3",
                    "--out", str(pathlib.Path(tmp) / "Src"))
        self.assertNotEqual(r.returncode, 0)

    def test_rows_one_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--model", str(MODEL_EXAMPLE), "--rows", "1", "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestComponentsModelRejection(unittest.TestCase):
    def test_components_and_model_together_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--model", str(MODEL_EXAMPLE), "--components", "none",
                    "--out", str(pathlib.Path(tmp) / "Src"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--components and --model are mutually exclusive",
                      r.stdout + r.stderr)

    def test_components_all_explicitly_with_model_is_still_rejected(self):
        """Even passing the flag's own default value explicitly is rejected
        — it is the PRESENCE of the flag with --model that is the problem,
        not which value it happens to carry."""
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--model", str(MODEL_EXAMPLE), "--components", "all",
                    "--out", str(pathlib.Path(tmp) / "Src"))
        self.assertNotEqual(r.returncode, 0)

    def test_model_without_a_components_flag_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--model", str(MODEL_EXAMPLE), "--rows", "3", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(len(list((out / "Components").glob("cmp_*.pa.yaml"))), 12)


class TestHashCharacterInModelStrings(unittest.TestCase):
    def test_hash_in_a_model_label_survives_intact_and_all_guards_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = pathlib.Path(tmp) / "model.yaml"
            model_path.write_text(HASH_MODEL, encoding="utf-8")
            out = pathlib.Path(tmp) / "Src"
            r = run("--model", str(model_path), "--rows", "3", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotIn("FAIL", r.stdout)
            text = (out / "OrdersListScreen.pa.yaml").read_text(encoding="utf-8")
            self.assertIn("ORDER # REF", text)
            data = yaml.safe_load(text)
            self.assertIsNotNone(data)
            self.assertIn("ORDER # REF", yaml.dump(data))

    def test_hash_in_a_legacy_name_survives_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--name", "Orders # 2024", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = (out / "ListScreen.pa.yaml").read_text(encoding="utf-8")
            self.assertIn("Orders # 2024", text)
            data = yaml.safe_load(text)
            self.assertIsNotNone(data)
            self.assertIn("Orders # 2024", yaml.dump(data))


if __name__ == "__main__":
    unittest.main()
