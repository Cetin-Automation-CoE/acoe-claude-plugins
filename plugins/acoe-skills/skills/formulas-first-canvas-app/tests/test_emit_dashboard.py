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

    def test_nav_instance_binds_the_registry(self):
        """C1 (final review, CRITICAL): the dashboard's own nav rail comes
        from the same _screen_chrome() helper the list screen uses — this
        pins that the fix there (Screens: =constScreens on the instance)
        actually reaches the dashboard too, not just the list screen."""
        self.assertIn("Screens: =constScreens", self.text)

    def test_all_dashboard_regions_present(self):
        # M3 (final review): renamed from test_five_regions, which actually
        # checked six names — the name is now what it asserts.
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

    def test_tile_navigate_and_count_buttons_are_siblings_of_the_container(self):
        """I3 (final review, IMPORTANT): the baseline's gallery template
        (Dashboard.pa.yaml:303/333/349) has con_ScreenTiles,
        btn_ScreenTiles_Navigate and btn_ScreenTiles_Count as three SIBLING
        template children, in that order — not the two buttons nested
        INSIDE the container. Nesting kept the baseline's absolute-position
        coordinates (X/Y off con_ScreenTiles.X/.Y/.Width/.Height) but no
        longer matched what they are positioned relative TO, which is how
        the count badge ended up overhanging the tile from outside instead
        of pinned to its corner."""
        data = yaml.safe_load(self.text)
        top_children = data["Screens"]["DashboardScreen"]["Children"]
        body_children = next(c["con_Dashboard_Body"] for c in top_children
                             if "con_Dashboard_Body" in c)["Children"]
        tiles_body = next(c["con_Dash_Tiles"] for c in body_children
                          if "con_Dash_Tiles" in c)
        gallery_body = next(c["gal_NavigationTiles"] for c in tiles_body["Children"]
                            if "gal_NavigationTiles" in c)
        names = [list(c.keys())[0] for c in gallery_body["Children"]]
        self.assertEqual(names, ["con_ScreenTiles", "btn_ScreenTiles_Navigate",
                                 "btn_ScreenTiles_Count"])
        # lbl_ScreenTiles_Screen stays INSIDE the container.
        container_children = [list(c.keys())[0] for c in gallery_body["Children"][0]
                              ["con_ScreenTiles"]["Children"]]
        self.assertEqual(container_children, ["lbl_ScreenTiles_Screen"])

    def test_dashboard_seeds_locnavigation_on_visible(self):
        """I4 (final review): seeded exactly like every list screen's own
        OnVisible tail (see emit_list_screen) — a dashboard-as-StartScreen
        app must reset the nav rail to collapsed on entry same as every
        other screen. Rendered as a block scalar (`OnVisible: |-`), not
        inline: the value's embedded `:` (inside `{locNavigation: false}`)
        is exactly the shape `_needs_block_scalar` exists to catch, the
        same reason the nav instance's own OnClose (identical value)
        already renders this way."""
        self.assertIn("OnVisible: |-", self.text)
        block = self.text.split("OnVisible: |-", 1)[1].split("\n", 2)[1]
        self.assertIn("=UpdateContext({locNavigation: false})", block)

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

    def test_band_template_size_divides_by_status_vocab_count(self):
        """Bundled fidelity item (deferred from Task 7): gal_Dash_Band's
        TemplateSize must divide the gallery's own rendered width by its
        status field's vocab count — the same shape the pipeline gallery
        already uses (RoundDown(Self.Width / len(vocab), 0)) — not the
        fixed constStyle.Dashboard.BandTileSize token, which never adapted
        to a model whose band entity has a different status vocab size."""
        mo = dash_model()
        asset = [e for e in mo.entities if e.entity == "Asset"][0]
        n = len(asset.status_field.vocab)
        t = ed.emit_dashboard_screen(mo)
        self.assertIn("TemplateSize: =RoundDown(Self.Width / %d, 0)" % n, t)
        self.assertNotIn("BandTileSize", t)

    def test_band_gallery_has_explicit_width(self):
        """M4: gal_Dash_Band previously had no Width at all, unlike the
        pipeline gallery's own Width: =Parent.Width sibling property."""
        text = ed.emit_dashboard_screen(dash_model())
        block = text.split("- gal_Dash_Band:", 1)[1].split("Children:", 1)[0]
        self.assertIn("Width: =Parent.Width", block)

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
