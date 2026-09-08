"""The dashboard is the baseline's landing page: title/caption, KPI band,
status-chip pipeline, navigation tiles, trademark.

Ruling 14 (Phase 3 Task 7 controller rulings): `check_layout.Finding` is
`namedtuple("Finding", "rule file line control message")` — it has no
`severity` field at all, unlike `check_control_props.Finding` (which does).
Every `check_layout` finding IS an error by construction, so the layout-guard
assertion below is a bare `== []`, with the `.severity == "error"` filter kept
ONLY for the `check_control_props` (ccp) findings, per the brief's own
verbatim test would otherwise raise AttributeError on the layout guard's
findings.
"""
import pathlib, sys, unittest, yaml
SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import model as m, emit_dashboard as ed, check_control_props as ccp, check_layout as cl  # noqa


def dash_model():
    return m.Model({"app_name": "Ops", "dashboard": True, "description": "Two registers.", "entities": [
        {"entity": "Asset", "plural": "Assets", "fields": [
            {"name": "Tag", "type": "text", "grid": 100, "role": "title"},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True, "role": "status", "vocab": ["Open", "Shut"]},
            {"name": "Amount", "type": "number", "grid": 118, "money": True}]},
        {"entity": "Site", "plural": "Sites", "fields": [
            {"name": "Name", "type": "text", "grid": "flex"},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True, "vocab": ["Live", "Closed"]}]}]})


class TestDashboardScreen(unittest.TestCase):
    def setUp(self):
        self.text = ed.emit_dashboard_screen(dash_model())

    def test_screen_is_named_dashboardscreen(self):
        self.assertTrue(self.text.startswith("Screens:\n  DashboardScreen:"))

    def test_has_header_nav_and_body_like_the_list_screen(self):
        for n in ("cmp_Dashboard_Header", "cmp_Dashboard_Navigation", "con_Dashboard_Body"):
            self.assertIn("- %s:" % n, self.text, n)

    def test_five_regions(self):
        for n in ("lbl_Dash_BandTitle", "gal_Dash_Band", "lbl_Dash_PipelineTitle",
                  "gal_Dash_Pipeline", "gal_NavigationTiles", "lbl_Dashboard_Trademark"):
            self.assertIn("- %s:" % n, self.text, n)

    def test_galleries_read_the_named_formulas(self):
        self.assertIn("Items: =constDashboardBand", self.text)
        self.assertIn("Items: =constDashboardNavigation", self.text)
        self.assertIn("Items: =constDashboardPipelineAsset", self.text)

    def test_chip_text_matches_the_baseline_shape(self):
        self.assertIn('CountRows(Filter(constAssetsInScope, Status = ThisItem.S))', self.text)

    def test_tile_navigates(self):
        self.assertIn("OnSelect: =Navigate(ThisItem.Screen, ScreenTransition.Fade)", self.text)

    def test_band_omitted_when_model_has_none(self):
        mo = dash_model()
        for e in mo.entities:
            e.fields = [f for f in e.fields if not f.money]
        t = ed.emit_dashboard_screen(mo)
        self.assertNotIn("gal_Dash_Band", t)
        # Important 3 (Phase 3 Task 7 fix round): the title/caption above the
        # band must be omitted too, not just the gallery — this held by
        # construction (both live inside _band_section's early `return []`)
        # but nothing pinned it before this assertion existed.
        self.assertNotIn("lbl_Dash_BandTitle", t)
        self.assertNotIn("lbl_Dash_BandCaption", t)

    def test_pipeline_omitted_for_an_entity_with_no_status_field(self):
        """An entity with no `role: status` field AND no choice field that
        is also `filter: true` has `status_field is None` (model.py's own
        fallback chain) — _pipeline_entities must skip it, so its own
        suffixed gal_Dash_Pipeline<Entity>/con_Dash_Pipeline<Entity>/etc.
        never appear, even though Asset (unaffected) still gets the bare,
        unsuffixed set."""
        mo = dash_model()
        site = [e for e in mo.entities if e.entity == "Site"][0]
        for f in site.fields:
            f.filter = False
        self.assertIsNone(site.status_field, "fixture no longer exercises the intended shape")
        t = ed.emit_dashboard_screen(mo)
        self.assertNotIn("gal_Dash_PipelineSite", t)
        self.assertNotIn("con_Dash_PipelineSite", t)
        self.assertNotIn("con_Dash_StatusChipSite", t)
        self.assertNotIn("lbl_Dash_ChipSite", t)
        # Asset (still status-bearing, and now the ONLY such entity) keeps
        # its own bare-named pipeline.
        self.assertIn("- gal_Dash_Pipeline:", t)

    def test_caption_falls_back_to_generated_text_when_description_is_empty(self):
        mo = dash_model()
        mo.description = ""
        t = ed.emit_dashboard_screen(mo)
        self.assertIn('Text: ="%d registers · live counts"' % len(mo.entities), t)

    def test_no_dimension_or_colour_literals_outside_tokens(self):
        for lit in ("=15", "=140", "=200", "=170", "RGBA("):
            self.assertNotIn(lit, self.text, lit)

    def test_yaml_and_both_guards_clean(self):
        yaml.safe_load(self.text)
        contracts = ccp.load_contracts()
        comps = ccp.parse_component_defs(sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        errs = [f for f in ccp.check_text(self.text, "Dashboard.pa.yaml", contracts, components=comps)
                if f.severity == "error"]
        self.assertEqual(errs, [])
        # Ruling 14: check_layout.Finding has no `severity` field — every
        # finding it returns already IS an error, so no filter here.
        self.assertEqual(cl.check_text(self.text, "Dashboard.pa.yaml"), [])


if __name__ == "__main__":
    unittest.main()
