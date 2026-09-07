"""--frame / model.yaml frame: wiring (Task 7).

new_app.py copies one of the two reference frame layouts
(templates/frame-headermainfooter.pa.yaml, templates/frame-headerrailmain.pa.yaml)
into the output tree as Frame.pa.yaml — for a --name build from the new
--frame CLI flag, for a --model build from model.yaml's own `frame:` field
(scripts/model.py already validates that field; this is the first thing that
consumes it). "headermain" (the default either way) writes no extra file: the
stock screens already are that shape.

Ruling 14 fixed the two real layout defects check_layout.py found in
emit_screens.py's generated output (a ModernDatePicker with no sizing; footer
summary labels with FillPortions: =0 and no Width), so a --model build's exit
code is asserted directly here too, alongside an isolated check on
Frame.pa.yaml by itself.
"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
NEW_APP = SKILL / "scripts" / "new_app.py"
MODEL_EXAMPLE = SKILL / "templates" / "model.example.yaml"


def run(*args):
    return subprocess.run([sys.executable, str(NEW_APP), *args],
                          capture_output=True, text=True)


class TestFrameModelMutualExclusivity(unittest.TestCase):
    def test_frame_and_model_together_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--model", str(MODEL_EXAMPLE), "--frame", "headerrailmain",
                    "--out", str(pathlib.Path(tmp) / "Src"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--frame and --model are mutually exclusive", r.stdout + r.stderr)


class TestFrameOnNamePath(unittest.TestCase):
    def test_default_frame_writes_no_extra_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--name", "No Frame", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((out / "Frame.pa.yaml").exists())

    def test_headermainfooter_writes_frame_and_all_six_guards_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--name", "Framed", "--frame", "headermainfooter", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = (out / "Frame.pa.yaml").read_text(encoding="utf-8")
            self.assertIn("FrameHeaderMainFooter:", text)
            self.assertIn("- FrameHeaderMainFooter",
                          (out / "_EditorState.pa.yaml").read_text(encoding="utf-8"))
            self.assertIn("PASS  check_layout.py", r.stdout)

    def test_headerrailmain_writes_frame_and_all_six_guards_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--name", "Framed", "--frame", "headerrailmain", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = (out / "Frame.pa.yaml").read_text(encoding="utf-8")
            self.assertIn("FrameHeaderRailMain:", text)
            self.assertIn("PASS  check_layout.py", r.stdout)

    def test_unknown_frame_choice_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--name", "Bad", "--frame", "sidebar",
                    "--out", str(pathlib.Path(tmp) / "Src"))
        self.assertNotEqual(r.returncode, 0)


class TestFrameOnModelPath(unittest.TestCase):
    """model.example.yaml sets `frame: headermainfooter` — model.py already
    validates this field (scripts/model.py, unmodifiable); new_app.py is the
    first thing that consumes it."""

    def test_model_frame_field_writes_matching_frame_file_and_all_six_guards_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            r = run("--model", str(MODEL_EXAMPLE), "--out", str(out), "--rows", "3")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS  check_layout.py", r.stdout)
            frame_file = out / "Frame.pa.yaml"
            self.assertTrue(frame_file.exists())
            self.assertIn("FrameHeaderMainFooter:", frame_file.read_text(encoding="utf-8"))
            self.assertIn("- FrameHeaderMainFooter",
                          (out / "_EditorState.pa.yaml").read_text(encoding="utf-8"))

    def test_frame_file_itself_is_layout_clean_in_isolation(self):
        """Confirms Frame.pa.yaml is clean on its own, independent of the
        unrelated emit_screens.py defects check_layout.py also (correctly)
        finds elsewhere in this same --model build."""
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "Src"
            run("--model", str(MODEL_EXAMPLE), "--out", str(out), "--rows", "3")
            isolated = pathlib.Path(tmp) / "FrameOnly"
            isolated.mkdir()
            (isolated / "Frame.pa.yaml").write_text(
                (out / "Frame.pa.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(SKILL / "scripts" / "check_layout.py"),
                 "--src", str(isolated)],
                capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("PASS:"), r.stdout)


if __name__ == "__main__":
    unittest.main()
