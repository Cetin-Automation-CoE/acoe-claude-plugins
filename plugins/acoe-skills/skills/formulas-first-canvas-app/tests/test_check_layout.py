"""Tests for check_layout.py: one positive and one negative case per rule.

Fragments mirror the real `Variant: AutoLayout` block shape used throughout
templates/ListScreen.pa.yaml (a `- name:` item, `Control:`/`Variant:` siblings
before `Properties:`, then `Children:`), since check_layout.py's own parser
inherits check_control_props.iter_properties's coverage limits and this is the
shape that parser expects.
"""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_layout as cl  # noqa: E402


def screen(children_yaml):
    return "Screens:\n  TestScreen:\n    Children:\n" + children_yaml


def findings_for(text):
    return cl.check_text(text, "test.pa.yaml")


class TestRule1FixedChildNeedsMainAxisSize(unittest.TestCase):
    """FillPortions: =0 child of an auto-layout container needs the explicit
    size matching the parent's main axis (Width for horizontal, Height for
    vertical) — LayoutMinHeight does not substitute."""

    def _row(self, fixed_props):
        return screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - con_Fixed:\n"
            "                Control: GroupContainer\n"
            "                Variant: AutoLayout\n"
            "                Properties:\n"
            + fixed_props +
            "            - con_Flex:\n"
            "                Control: GroupContainer\n"
            "                Variant: AutoLayout\n"
            "                Properties:\n"
            "                  FillPortions: =1\n"
            "                  Height: =40\n"
        )

    def test_missing_width_is_flagged(self):
        text = self._row(
            "                  FillPortions: =0\n"
            "                  Height: =40\n"
        )
        findings = findings_for(text)
        self.assertTrue(any(f.rule == "R1" and f.control == "con_Fixed" for f in findings),
                         findings)

    def test_layoutminwidth_does_not_substitute_for_width(self):
        text = self._row(
            "                  FillPortions: =0\n"
            "                  Height: =40\n"
            "                  LayoutMinWidth: =100\n"
        )
        findings = findings_for(text)
        self.assertTrue(any(f.rule == "R1" and f.control == "con_Fixed" for f in findings),
                         findings)

    def test_explicit_width_passes(self):
        text = self._row(
            "                  FillPortions: =0\n"
            "                  Height: =40\n"
            "                  Width: =120\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R1" for f in findings), findings)


class TestRule2ContainerNeedsSizeOrFlexibleChild(unittest.TestCase):
    def test_no_size_and_no_flexible_child_is_flagged(self):
        text = screen(
            "      - con_Empty:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Vertical\n"
            "          Children:\n"
            "            - con_Fixed:\n"
            "                Control: GroupContainer\n"
            "                Variant: AutoLayout\n"
            "                Properties:\n"
            "                  FillPortions: =0\n"
            "                  Height: =40\n"
        )
        findings = findings_for(text)
        self.assertTrue(any(f.rule == "R2" and f.control == "con_Empty" for f in findings),
                         findings)

    def test_explicit_own_height_passes_with_no_flexible_child(self):
        text = screen(
            "      - con_Sized:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Vertical\n"
            "            Height: =200\n"
            "          Children:\n"
            "            - con_Fixed:\n"
            "                Control: GroupContainer\n"
            "                Variant: AutoLayout\n"
            "                Properties:\n"
            "                  FillPortions: =0\n"
            "                  Height: =40\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R2" and f.control == "con_Sized" for f in findings),
                          findings)

    def test_flexible_child_passes_with_no_own_size(self):
        text = screen(
            "      - con_Fills:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Vertical\n"
            "          Children:\n"
            "            - gal_Items:\n"
            "                Control: Gallery\n"
            "                Variant: Vertical\n"
            "                Properties:\n"
            "                  FillPortions: =1\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R2" and f.control == "con_Fills" for f in findings),
                          findings)


class TestRule3LeafNeedsFillPortionsOrSize(unittest.TestCase):
    def test_leaf_with_nothing_is_flagged(self):
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - gal_Naked:\n"
            "                Control: Gallery\n"
            "                Variant: Vertical\n"
            "                Properties:\n"
            "                  TemplateSize: =40\n"
        )
        findings = findings_for(text)
        self.assertTrue(any(f.rule == "R3" and f.control == "gal_Naked" for f in findings),
                         findings)

    def test_leaf_with_fillportions_passes(self):
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - gal_Sized:\n"
            "                Control: Gallery\n"
            "                Variant: Vertical\n"
            "                Properties:\n"
            "                  FillPortions: =1\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R3" for f in findings), findings)

    def test_container_child_is_not_a_rule3_leaf(self):
        """A GroupContainer with neither FillPortions nor size is Rule 2's
        concern (its OWN sizing), not Rule 3's — no double-report."""
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - con_Naked:\n"
            "                Control: GroupContainer\n"
            "                Variant: AutoLayout\n"
            "                Properties:\n"
            "                  LayoutDirection: =LayoutDirection.Vertical\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R3" and f.control == "con_Naked" for f in findings),
                          findings)
        self.assertTrue(any(f.rule == "R2" and f.control == "con_Naked" for f in findings),
                         findings)


class TestRule3Carveouts(unittest.TestCase):
    """Two principled exceptions discovered while running check_layout.py
    against this skill's own templates/components AND emit_screens.py's own
    generated output (see the module docstring's COVERAGE LIMITS):
    ModernText/Text are exempt from Rule 3 entirely (their own control
    default is natural content height, not a Gallery-style collapse), and a
    CanvasComponent instance's sizing is governed by its own definition file,
    which this guard cannot see."""

    def test_moderntext_with_autoheight_is_exempt(self):
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Vertical\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - lbl_Auto:\n"
            "                Control: ModernText\n"
            "                Properties:\n"
            "                  AutoHeight: =true\n"
            "                  Text: =\"hello\"\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R3" for f in findings), findings)

    def test_moderntext_with_no_sizing_at_all_is_exempt(self):
        """The exemption is by CONTROL TYPE, not by the presence of
        AutoHeight — emit_screens.py's own generated form labels carry
        neither Width, Height, FillPortions, nor AutoHeight, identically to
        every hand-authored template label, and are not a real defect."""
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Vertical\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - lbl_Bare:\n"
            "                Control: ModernText\n"
            "                Properties:\n"
            "                  Text: =\"hello\"\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R3" for f in findings), findings)

    def test_moderntext_is_still_subject_to_rule1(self):
        """The R3 carve-out is narrow: a ModernText leaf that explicitly
        declares FillPortions: =0 in a Horizontal parent still needs Width —
        no control has an "auto-width" mechanism the way Text has AutoHeight,
        so Rule 1 is unaffected by this carve-out."""
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - lbl_Fixed:\n"
            "                Control: ModernText\n"
            "                Properties:\n"
            "                  FillPortions: =0\n"
            "                  Text: =\"hello\"\n"
            "            - con_Flex:\n"
            "                Control: GroupContainer\n"
            "                Variant: AutoLayout\n"
            "                Properties:\n"
            "                  FillPortions: =1\n"
        )
        findings = findings_for(text)
        self.assertTrue(any(f.rule == "R1" and f.control == "lbl_Fixed" for f in findings),
                         findings)

    def test_canvascomponent_instance_is_exempt_from_rule1_and_rule3(self):
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - cmp_Rail:\n"
            "                Control: CanvasComponent\n"
            "                ComponentName: cmp_Navigation\n"
            "                Properties:\n"
            "                  FillPortions: =0\n"
            "                  Height: =Parent.Height\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule in ("R1", "R3") for f in findings), findings)


class TestRule4VisibleOnFlexibleSpacer(unittest.TestCase):
    def test_visible_on_flexible_child_is_flagged(self):
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - spc_Gap:\n"
            "                Control: ModernText\n"
            "                Properties:\n"
            "                  FillPortions: =1\n"
            "                  Text: =\"\"\n"
            "                  Visible: =locShowGap\n"
        )
        findings = findings_for(text)
        self.assertTrue(any(f.rule == "R4" and f.control == "spc_Gap" for f in findings),
                         findings)

    def test_visible_on_fixed_child_passes(self):
        """A fixed (FillPortions: =0) child toggling Visible is the normal,
        safe pattern (e.g. cmp_Header's back/menu buttons) — only a FLEXIBLE
        child dropping out collapses a gap."""
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - btn_Back:\n"
            "                Control: Button\n"
            "                Properties:\n"
            "                  FillPortions: =0\n"
            "                  Width: =32\n"
            "                  Visible: =locAllowBack\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R4" for f in findings), findings)

    def test_visible_on_flexible_child_with_no_fillportions_at_all_passes(self):
        """FillPortions absent entirely is Rule 3's concern, not Rule 4's —
        Rule 4 only fires once a child has actually declared itself flexible."""
        text = screen(
            "      - con_Row:\n"
            "          Control: GroupContainer\n"
            "          Variant: AutoLayout\n"
            "          Properties:\n"
            "            LayoutDirection: =LayoutDirection.Horizontal\n"
            "            Height: =40\n"
            "          Children:\n"
            "            - lbl_Plain:\n"
            "                Control: ModernText\n"
            "                Properties:\n"
            "                  Width: =80\n"
            "                  Visible: =locShow\n"
        )
        findings = findings_for(text)
        self.assertFalse(any(f.rule == "R4" for f in findings), findings)


class TestCLIConvention(unittest.TestCase):
    """Exercised via subprocess since this is main()'s own exit/print
    behavior, not check_text()'s — matching test_control_props_direct.py's
    TestTypoedSrcFailsLoud convention."""

    def _run(self, src):
        import subprocess

        return subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "check_layout.py"),
             "--src", src],
            capture_output=True, text=True)

    def test_pass_line_and_not_covered_line(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "Clean.pa.yaml"
            p.write_text(screen(
                "      - lbl_Ok:\n"
                "          Control: ModernText\n"
                "          Properties:\n"
                "            Text: =\"ok\"\n"
            ), encoding="utf-8")
            r = self._run(tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("PASS:"), r.stdout)
        self.assertIn("Not covered:", r.stdout)

    def test_fail_exits_nonzero(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "Broken.pa.yaml"
            p.write_text(screen(
                "      - con_Row:\n"
                "          Control: GroupContainer\n"
                "          Variant: AutoLayout\n"
                "          Properties:\n"
                "            LayoutDirection: =LayoutDirection.Horizontal\n"
                "            Height: =40\n"
                "          Children:\n"
                "            - con_Fixed:\n"
                "                Control: GroupContainer\n"
                "                Variant: AutoLayout\n"
                "                Properties:\n"
                "                  FillPortions: =0\n"
                "                  Height: =40\n"
            ), encoding="utf-8")
            r = self._run(tmp)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("FAIL:"), r.stdout)


if __name__ == "__main__":
    unittest.main()
