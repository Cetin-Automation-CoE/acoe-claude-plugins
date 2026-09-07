"""Generated screens must be contract-clean by construction, not by luck."""
import pathlib
import re
import sys
import unittest

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_screens as es  # noqa: E402
import check_control_props as ccp  # noqa: E402
import check_layout as cl  # noqa: E402


def entity():
    return m.Entity({
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Tag", "type": "text", "grid": 100, "search": True},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True,
             "vocab": ["Open", "Shut"]},
            {"name": "Amount", "type": "number", "grid": 118, "money": True},
            {"name": "Due", "type": "date", "grid": 112, "semantics": "due"},
            {"name": "Notes", "type": "longtext", "grid": "hidden"},
            # Task 1 (baseline conformance): the baseline has no flex grid
            # column at all, so entity() needs one to exercise the
            # flex-becomes-wide-fixed conversion (_column_px / FLEX_COLUMN_PX).
            {"name": "Region", "type": "text", "grid": "flex"},
        ],
    })


def entity_without_money():
    """Same shape as `entity()` but with no `money: true` field anywhere —
    the footer must still show a count and must not emit a stray `Sum()`."""
    return m.Entity({
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Tag", "type": "text", "grid": 100, "search": True},
            {"name": "Status", "type": "choice", "grid": 120, "filter": True,
             "vocab": ["Open", "Shut"]},
            {"name": "Due", "type": "date", "grid": 112, "semantics": "due"},
        ],
    })


def small_model():
    return m.Model({"app_name": "Ops", "entities": [{
        "entity": "Asset", "plural": "Assets",
        "fields": [{"name": "Tag", "type": "text", "grid": 100}]}]})


def entity_two_filters():
    """Two independent choice filter fields — the minimum shape that can
    actually distinguish `And` from `Or` between per-field filter clauses
    (Ruling 15/C1)."""
    return m.Entity({
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Status", "type": "choice", "grid": 120, "filter": True,
             "vocab": ["Open", "Shut"]},
            {"name": "Category", "type": "choice", "grid": 120, "filter": True,
             "vocab": ["A", "B"]},
        ],
    })


def entity_number_first():
    """No text/longtext field ANYWHERE — the shape that used to make the
    form header's DisplayName a type error (Ruling 20/I3): DisplayName is
    DataType: Text, and the previous emitter unconditionally used the first
    GRID field regardless of its archetype."""
    return m.Entity({
        "entity": "Reading", "plural": "Readings",
        "fields": [
            {"name": "Amount", "type": "number", "grid": 100},
            {"name": "Status", "type": "choice", "grid": 120,
             "vocab": ["Open", "Shut"]},
        ],
    })


class TestListScreen(unittest.TestCase):
    def setUp(self):
        self.e = entity()
        self.text = es.emit_list_screen(self.e, small_model())

    def test_one_header_per_grid_field_and_none_for_hidden(self):
        for f in self.e.grid_fields:
            self.assertIn(self.e.head_control(f), self.text, f.name)
        self.assertNotIn("Notes", self.text.split("Children:")[0])

    def test_one_row_cell_per_grid_field(self):
        for f in self.e.grid_fields:
            self.assertIn(self.e.cell_control(f), self.text, f.name)

    def test_gallery_has_explicit_fillportions(self):
        """A Gallery is a leaf control; without this it collapses to ~200px."""
        gal = self.text.split(self.e.gallery)[1]
        self.assertIn("FillPortions: =1", gal.split("Children:")[0])

    def test_search_box_searches_every_search_field(self):
        self.assertIn("Tag", self.text)

    def test_money_cells_use_the_money_colour_function_not_a_literal(self):
        self.assertIn("funcMoneyTextColor(ThisItem.Amount)", self.text)

    def test_component_inputs_receive_strings_not_enums(self):
        """cmp_FilterButton.Align is DataType: Text."""
        self.assertNotIn("Align: =Align.", self.text)


class TestFormScreen(unittest.TestCase):
    def setUp(self):
        self.e = entity()
        self.text = es.emit_form_screen(self.e, small_model())

    def test_one_input_per_field_including_grid_hidden_ones(self):
        for f in self.e.form_fields:
            self.assertIn(self.e.form_control(f), self.text, f.name)

    def test_archetype_picks_the_control(self):
        self.assertIn("Control: ModernCombobox", self.text)
        self.assertIn("Control: ModernDatePicker", self.text)
        self.assertIn("Control: ModernTextInput", self.text)

    def test_no_format_property_on_a_number_input(self):
        """ModernTextInput has no Format; numeric entry is a text input."""
        self.assertNotIn("Format: =TextFormat", self.text)

    def test_placeholder_not_hinttext(self):
        self.assertNotIn("HintText:", self.text)


class TestGeneratedOutputPassesTheContractGuard(unittest.TestCase):
    """The emitter reads the same contract file the guard checks against, so
    this must hold by construction, not by coincidence."""

    def test_list_and_form_are_contract_clean(self):
        contracts = ccp.load_contracts()
        components = ccp.parse_component_defs(
            sorted((SKILL / "components").glob("cmp_*.pa.yaml")))
        e, mo = entity(), small_model()
        for name, text in (("list", es.emit_list_screen(e, mo)),
                           ("form", es.emit_form_screen(e, mo))):
            errs = [f for f in ccp.check_text(text, name + ".pa.yaml", contracts,
                                              components=components)
                    if f.severity == "error"]
            self.assertEqual(errs, [], "%s: %s" % (name, errs))


class TestGeneratedOutputPassesTheLayoutGuard(unittest.TestCase):
    """Ruling 14: check_layout.py found two real defects here (a
    ModernDatePicker with no sizing at all, and footer summary labels
    declaring FillPortions: =0 in a Horizontal container with no explicit
    Width) — this must hold by construction, not by coincidence, exactly
    like TestGeneratedOutputPassesTheContractGuard above for control
    contracts. Covers both the with-money and without-money footer code
    paths, since they emit a different number of footer labels."""

    def _findings(self, e):
        findings = []
        for name, text in (("list", es.emit_list_screen(e, small_model())),
                           ("form", es.emit_form_screen(e, small_model()))):
            findings.extend(cl.check_text(text, name + ".pa.yaml"))
        return findings

    def test_list_and_form_are_layout_clean_with_a_money_and_date_field(self):
        self.assertEqual(self._findings(entity()), [])

    def test_list_and_form_are_layout_clean_without_a_money_field(self):
        self.assertEqual(self._findings(entity_without_money()), [])

    def test_date_input_carries_an_explicit_height(self):
        text = es.emit_form_screen(entity(), small_model())
        # The Due field's own control block, not just anywhere in the file.
        due_ctrl = entity().form_control(
            [f for f in entity().fields if f.name == "Due"][0])
        block = text.split("- %s:" % due_ctrl, 1)[1].split("- ", 1)[0]
        self.assertIn("Height: =constStyle.Label.TextInput.Height.SingleLine", block)

    def test_footer_count_label_is_the_flexible_child(self):
        text = es.emit_list_screen(entity(), small_model())
        block = text.split("- lbl_AssetsList_Count:", 1)[1].split("- ", 1)[0]
        self.assertIn("FillPortions: =1", block)
        self.assertNotIn("FillPortions: =0", block)

    def test_footer_money_total_label_keeps_fixed_width(self):
        text = es.emit_list_screen(entity(), small_model())
        block = text.split("- lbl_AssetsList_AmountTotal:", 1)[1].split("- ", 1)[0]
        self.assertIn("FillPortions: =0", block)
        self.assertIn("Width: =200", block)


class TestNoGenericLeakage(unittest.TestCase):
    def test_template_identifiers_do_not_appear_in_generated_screens(self):
        e, mo = entity(), small_model()
        for text in (es.emit_list_screen(e, mo), es.emit_form_screen(e, mo)):
            for leaked in ("colItems", "locItem", "gal_List_Items"):
                self.assertNotIn(leaked, text, leaked)


class TestFooterAggregates(unittest.TestCase):
    """Ruling 12, corrected by Ruling 18/I1: the list screen's footer must
    show a filtered count and per-money-field Sum() over the SAME `Filter`
    expression the gallery's own `Items` reads — not the bare, unfiltered
    scope formula (which is what the pre-fix footer read, permanently
    showing "N of N" and a Sum() that ignored search). `_visible_rows_expr`
    is the ONE function both the gallery and the footer call, so this test
    reconstructs its exact output and confirms both consumers embed it
    verbatim — the thing that makes them incapable of silently disagreeing.
    """

    def _filter_ctrls(self, e):
        return {f.name: "com_%sList_%sFilter" % (e.plural, f.name)
                for f in e.filter_fields if f.type == "choice"}

    def _visible(self, e):
        search_ctrl = "txt_%sList_Search" % e.plural
        return es._visible_rows_expr(e, self._filter_ctrls(e), search_ctrl)

    def test_count_reads_the_same_filter_expression_the_gallery_uses(self):
        e = entity()
        text = es.emit_list_screen(e, small_model())
        visible = self._visible(e)
        # The gallery's Items and the footer's count both embed this exact
        # text (reindented, so compare with whitespace collapsed).
        # >= 2, not == 2: `entity()` also has a money field, so the footer's
        # Sum() embeds a third copy — the point here is that the gallery's
        # Items and the footer's count are never allowed to drift apart, not
        # an exact occurrence count that depends on how many money fields
        # the entity happens to have.
        squashed = re.sub(r"\s+", " ", text)
        self.assertGreaterEqual(squashed.count(re.sub(r"\s+", " ", visible).strip()), 2,
                         "gallery Items and footer count must both embed the "
                         "identical Filter(...) expression")
        self.assertIn("CountRows(", text)
        self.assertNotIn("CountRows(%s)" % e.scope_formula, text,
                         "the footer must not read the bare, unfiltered scope "
                         "(Ruling 18) — that is what froze the count at N of N")

    def test_money_field_produces_a_sum_over_the_filtered_expression(self):
        e = entity()
        text = es.emit_list_screen(e, small_model())
        visible = self._visible(e)
        squashed = re.sub(r"\s+", " ", text)
        sum_needle = re.sub(r"\s+", " ", "Sum(\n    %s,\n    Amount\n)" % visible).strip()
        self.assertIn(sum_needle, squashed)
        # Task 1 (baseline conformance): the footer total is now coalesced
        # (funcAsCurrency(Coalesce(Sum(...), 0))) so a fully-filtered-out
        # money column reads "0", not a blank Sum() result — this literal
        # adjacency check is updated to match, not loosened; the inner Sum()
        # text asserted above is unchanged and still embeds verbatim.
        self.assertIn("funcAsCurrency(Coalesce(Sum(", text)
        self.assertNotIn("Sum(%s, Amount)" % e.scope_formula, text,
                         "the footer Sum() must not read the bare, unfiltered "
                         "scope (Ruling 18) — that ignored search entirely")

    def test_entity_without_a_money_field_still_gets_a_count_and_no_stray_sum(self):
        e = entity_without_money()
        text = es.emit_list_screen(e, small_model())
        self.assertIn("CountRows(", text)
        self.assertNotIn("Sum(", text)


class TestNeedsBlockScalar(unittest.TestCase):
    """Ruling 16/C2: a `#` in a value used to render inline, and YAML treats
    a space followed by `#` as the start of a COMMENT in a plain scalar —
    `Label: ="ORDER # REF"` silently truncates to `Label: ="ORDER`, with the
    file staying perfectly valid YAML the whole time. `_needs_block_scalar`
    is the only thing that can catch this, since it inspects the VALUE, not
    just whether the resulting file parses."""

    def test_hash_forces_a_block_scalar(self):
        self.assertTrue(es._needs_block_scalar('="ORDER # REF"'))

    def test_leading_or_trailing_whitespace_forces_a_block_scalar(self):
        self.assertTrue(es._needs_block_scalar('="trailing space" '))
        self.assertTrue(es._needs_block_scalar(' ="leading space"'))

    def test_ordinary_value_stays_inline(self):
        self.assertFalse(es._needs_block_scalar('=constStyle.List.HeaderHeight'))
        self.assertFalse(es._needs_block_scalar('="TAG"'))

    def test_a_hash_containing_label_round_trips_through_real_yaml(self):
        e = m.Entity({"entity": "Order", "plural": "Orders", "fields": [
            {"name": "Reference", "type": "text", "grid": 140,
             "label": "ORDER # REF", "samples": ["A#1"]},
        ]})
        text = es.emit_list_screen(e, small_model())
        self.assertIn("ORDER # REF", text)
        data = yaml.safe_load(text)
        self.assertIsNotNone(data)
        # The label must reach the parsed structure WHOLE, not truncated at
        # the '#' — this is the actual defect, not merely "the file parses".
        rendered = yaml.dump(data)
        self.assertIn("ORDER # REF", rendered)


class TestFilterSemantics(unittest.TestCase):
    """Ruling 15/C1: the previous joiner between per-field filter clauses was
    `Or`, so any ONE unset combobox's own `IsEmpty(...)` (always true when
    that combobox is unset) made the WHOLE predicate `true` regardless of
    what any OTHER filter combobox held — picking a value in one filter did
    nothing. There was no test anywhere asserting filter semantics, which is
    why this shipped through nine reviews."""

    def test_multiple_filter_fields_are_joined_with_and(self):
        e = entity_two_filters()
        ctrls = {f.name: "com_%s" % f.name for f in e.filter_fields}
        clause = es._filter_clause(e, ctrls)
        self.assertIn(") And\n    (", clause,
                     "per-field filter clauses must be joined with And — an "
                     "Or joiner lets any one unset combobox make the whole "
                     "predicate true, and filtering does nothing")
        self.assertNotIn(") Or\n    (", clause)

    def test_each_field_clause_is_still_the_isempty_or_match_pair(self):
        """WITHIN one field's own clause, Or is correct: IsEmpty(...) being
        true is exactly what makes an UNSET combobox mean "no constraint
        from this field". Only the joiner BETWEEN fields must change to And."""
        e = entity_two_filters()
        ctrls = {f.name: "com_%s" % f.name for f in e.filter_fields}
        clause = es._filter_clause(e, ctrls)
        for name, ctrl in ctrls.items():
            pair = ("(IsEmpty(%s.SelectedItems) Or %s in %s.SelectedItems.Value)"
                    % (ctrl, name, ctrl))
            self.assertIn(pair, clause)

    def test_no_filter_fields_is_no_constraint(self):
        self.assertEqual(es._filter_clause(entity(), {}), "true")

    def test_search_clause_unset_search_box_is_no_constraint(self):
        clause = es._search_clause(entity(), "txtSearch")
        self.assertTrue(clause.startswith("IsBlank(txtSearch.Text) Or"))

    def test_search_clause_matches_any_one_of_several_search_fields(self):
        """Search fields are Or'd together — deliberately unlike filter
        fields, which must ALL be satisfied at once: a term matching ANY one
        search field should match."""
        e = m.Entity({"entity": "Asset", "plural": "Assets", "fields": [
            {"name": "Tag", "type": "text", "search": True},
            {"name": "Notes", "type": "longtext", "search": True},
        ]})
        clause = es._search_clause(e, "txtSearch")
        self.assertIn("txtSearch.Text in Tag Or\n    txtSearch.Text in Notes", clause)


class TestHeaderSortToggle(unittest.TestCase):
    """Ruling 19/I2: a header's OnSelect must write colSorts, or nothing
    ever changes IsSorted/IsFiltered and SortByColumns stays frozen forever
    on whatever OnVisible seeded once at screen load."""

    def _tag_header_block(self, e, mo):
        text = es.emit_list_screen(e, mo)
        tag_header = e.head_control([f for f in e.fields if f.name == "Tag"][0])
        return text.split("- %s:" % tag_header, 1)[1].split("- ", 1)[0]

    def test_header_emits_onselect_that_updates_colsorts_for_its_own_entity(self):
        e, mo = entity(), small_model()
        block = self._tag_header_block(e, mo)
        self.assertIn("OnSelect: |-", block)
        self.assertIn("UpdateIf(", block)
        self.assertIn("colSorts,", block)
        self.assertIn("Table = %s," % e.enum_member, block)
        self.assertIn('ID: "Tag"', block)

    def test_onselect_flip_reads_the_original_row_not_a_scratch_variable(self):
        """UpdateIf's change record is evaluated against the row being
        replaced, so ID/SortOrder inside it read the PRIOR state — that is
        what lets a second click on the same column flip direction without
        a With() or a context variable."""
        e, mo = entity(), small_model()
        block = self._tag_header_block(e, mo)
        self.assertIn('ID = "Tag" And SortOrder = "asc"', block)
        self.assertIn('"desc"', block)
        self.assertIn('"asc"', block)
        self.assertNotIn("With(", block)


class TestFormDisplayNameTypeMatchesTextInput(unittest.TestCase):
    """Ruling 20/I3: cmp_Header.DisplayName is DataType: Text. The previous
    emitter unconditionally used the first GRID field's raw value — a type
    error the instant that field is a number or a date."""

    def test_number_first_entity_wraps_the_value_in_text(self):
        e = entity_number_first()
        text = es.emit_form_screen(e, small_model())
        self.assertIn("Text(locReading.Amount)", text)

    def test_text_field_is_preferred_over_wrapping_when_one_exists(self):
        e = entity()
        text = es.emit_form_screen(e, small_model())
        self.assertIn("locAsset.Tag)", text)
        self.assertNotIn("Text(locAsset.Tag)", text)


class TestEmittedYamlIsValid(unittest.TestCase):
    """check_control_props.py is a line-oriented regex parser, not a real
    YAML parser — it can (and, during development of this module, did) pass
    output that yaml.safe_load rejects outright. Round-tripping through a
    real parser is a cheap, mechanical way to catch that class of bug."""

    def test_both_screens_parse_as_yaml(self):
        e, mo = entity(), small_model()
        for name, text in (("list", es.emit_list_screen(e, mo)),
                           ("form", es.emit_form_screen(e, mo))):
            try:
                data = yaml.safe_load(text)
            except yaml.YAMLError as exc:
                self.fail("%s screen is not valid YAML: %s" % (name, exc))
            self.assertIn("Screens", data, name)


class TestListScreenMatchesBaselineSkeleton(unittest.TestCase):
    """The first live render showed a nav rail at 50% width, an empty grid and
    factory placeholders. Every assertion here is a symptom from that screenshot,
    traced to a divergence from the baseline's Activities.pa.yaml."""

    def setUp(self):
        self.e = entity()
        self.text = es.emit_list_screen(self.e, small_model())

    def _props_of(self, control_name):
        """Properties of one control, as {name: value}. A block-scalar
        property (`k: |-` followed by indented lines — e.g.
        DefaultSelectedItems once it carries an embedded `//` rationale,
        Ruling 6) is returned with its FULL multi-line body joined by "\\n",
        not just the `|-` marker: a helper that cannot see block scalars is
        a blind spot for every future test that needs to inspect an
        embedded-comment formula, not just this one."""
        lines = self.text.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "- %s:" % control_name)
        indent = len(lines[start]) - len(lines[start].lstrip())
        prop_indent = indent + 6
        props = {}
        i = start + 1
        while i < len(lines):
            l = lines[i]
            if l.strip().startswith("- ") and (len(l) - len(l.lstrip())) <= indent:
                break
            if l.strip() == "Children:":
                break
            if ":" in l and (len(l) - len(l.lstrip())) == prop_indent:
                k, _, v = l.strip().partition(":")
                v = v.strip()
                if v in ("|-", "|"):
                    body = []
                    j = i + 1
                    while j < len(lines) and (
                            lines[j].strip() == ""
                            or (len(lines[j]) - len(lines[j].lstrip())) > prop_indent):
                        body.append(lines[j].strip())
                        j += 1
                    props[k] = "\n".join(body)
                    i = j
                    continue
                props[k] = v
            i += 1
        return props

    def test_no_horizontal_main_wrapper(self):
        """Structural, not textual (Ruling 7): a future regression that
        renests nav+list under a DIFFERENTLY NAMED horizontal wrapper — not
        literally `con_<Plural>List_Main` — must still fail here. Parse the
        real YAML and require both controls to be DIRECT entries of the
        screen's own Children list, not nested one level inside some other
        container, named or not. (A `grep`-style textual check of the old
        wrapper's literal name would pass even if a regression renamed it.)
        """
        data = yaml.safe_load(self.text)
        children = data["Screens"][self.e.list_screen]["Children"]
        direct_names = set()
        for child in children:
            direct_names.update(child.keys())
        self.assertIn("cmp_%sList_Navigation" % self.e.plural, direct_names)
        self.assertIn("con_%sList_List" % self.e.plural, direct_names)

    def test_nav_is_a_direct_screen_child_with_self_sizing_width(self):
        p = self._props_of("cmp_%sList_Navigation" % self.e.plural)
        self.assertEqual(p["Width"], "=If(cmp_%sList_Navigation.Navigation, 250, 60)" % self.e.plural)
        self.assertIn("cmp_%sList_Header.Height" % self.e.plural, p["Y"])
        self.assertIn("Parent.Height", p["Height"])

    def test_list_container_derives_position_from_nav_and_header(self):
        p = self._props_of("con_%sList_List" % self.e.plural)
        self.assertEqual(p["X"], "=cmp_%sList_Navigation.Width + 10" % self.e.plural)
        self.assertIn("cmp_%sList_Navigation.Width" % self.e.plural, p["Width"])
        self.assertIn("cmp_%sList_Header.Height" % self.e.plural, p["Y"])
        self.assertEqual(p["LayoutAlignItems"], "=LayoutAlignItems.Stretch")

    def test_every_filter_combobox_has_typed_empty_default_and_placeholder(self):
        """An untouched ModernCombobox has no defined selection state, so
        IsEmpty(SelectedItems) never returns true and the grid reads 0 of N.

        Ruling 6: DefaultSelectedItems is now a block scalar carrying the
        rationale as an embedded `//` Power Fx comment (baseline-style) —
        the deliverable is the GENERATED APP, and a maker opening this
        property in Studio must see WHY it exists, not just a bare
        `=FirstN(...)` that looks deletable. Assert the formula CONTAINS
        the call and the rationale text, not exact equality, since the
        comment lines are part of the value now."""
        for f in self.e.filter_fields:
            p = self._props_of("com_%sList_%sFilter" % (self.e.plural, f.name))
            default_selected = p["DefaultSelectedItems"]
            self.assertIn("FirstN(%s, 0)" % self.e.choices_table(f),
                          default_selected, f.name)
            self.assertIn("IsEmpty(SelectedItems)", default_selected, f.name)
            self.assertEqual(p["InputTextPlaceholder"], '="%s"' % f.label, f.name)
            # Minor: emitted but previously untested.
            self.assertEqual(p["IsSearchable"], "=false", f.name)
            self.assertEqual(p["ItemDisplayText"], "=ThisItem.Value", f.name)

    def test_header_width_matches_cell_width_per_grid_field(self):
        """Minor: guaranteed by construction today, since both the header
        and the cell call the SAME `_column_dims(field)` — locked here so a
        future change to either call site cannot let them silently drift
        apart (a header wider or narrower than its own column's cells is a
        visibly broken grid, not just a cosmetic mismatch)."""
        for f in self.e.grid_fields:
            head = self._props_of(self.e.head_control(f))
            cell = self._props_of(self.e.cell_control(f))
            self.assertEqual(head["Width"], cell["Width"], f.name)

    def test_no_flex_column_and_min_widths_everywhere(self):
        """A FillPortions=1 header crushes fixed siblings on a narrow canvas."""
        for f in self.e.grid_fields:
            p = self._props_of(self.e.head_control(f))
            self.assertNotIn("FillPortions", p, f.name)
            self.assertIn("Width", p, f.name)
            self.assertIn("LayoutMinWidth", p, f.name)

    def test_header_row_min_width_is_the_sum_of_column_widths(self):
        widths = [es._column_px(f) for f in self.e.grid_fields]
        p = self._props_of("con_%sList_Headers" % self.e.plural)
        self.assertEqual(p["LayoutMinWidth"], "=%d" % sum(widths))

    def test_table_container_scrolls_horizontally(self):
        p = self._props_of("con_%sList_Table" % self.e.plural)
        self.assertEqual(p["LayoutOverflowX"], "=LayoutOverflow.Scroll")

    def test_footer_total_is_coalesced(self):
        self.assertIn("Coalesce(Sum(", self.text)


class TestFlexColumnBecomesWideFixed(unittest.TestCase):
    def test_flex_maps_to_240_px(self):
        f = [x for x in entity().fields if x.grid_width == "flex"]
        if f:
            self.assertEqual(es._column_px(f[0]), 240)


class TestGallerySortUsesUdfs(unittest.TestCase):
    def test_no_raw_lookup_on_colsorts_in_items(self):
        text = es.emit_list_screen(entity(), small_model())
        # [-1], not [1]: entity() has a Status filter field, so the toolbar's
        # combobox emits its own "DefaultSelectedItems: |-" property FIRST —
        # a substring match on "Items: |-" fires there too (it ends in
        # exactly that text), so [1] captures the span between that filter
        # property and the gallery's OWN Items line, not the gallery's Items
        # body. The gallery's Items is always the LAST such match: every
        # filter combobox is toolbar chrome that renders before the table.
        items = text.split("Items: |-")[-1].split("TemplateSize")[0]
        self.assertNotIn("LookUp(colSorts", items)
        self.assertIn("funcTableSortColumn(enumEntity.", items)
        self.assertIn('funcTableSortOrder(enumEntity.', items)


class TestFormScreenMatchesBaselineSkeleton(unittest.TestCase):
    """Live render: a ~420px card pinned top-left, covering the header."""

    def setUp(self):
        self.e = entity()
        self.text = es.emit_form_screen(self.e, small_model())
        self.props = TestListScreenMatchesBaselineSkeleton._props_of

    def test_body_fills_width_and_sits_below_header(self):
        p = self.props(self, "con_%sForm_Body" % self.e.entity)
        self.assertEqual(p["Width"], "=Parent.Width")
        self.assertEqual(p["Y"], "=cmp_%sForm_Header.Height" % self.e.entity)
        self.assertEqual(p["LayoutAlignItems"], "=LayoutAlignItems.Stretch")
        self.assertIn("PaddingLeft", p)
        self.assertIn("PaddingTop", p)

    def test_form_comboboxes_have_placeholder_and_typed_default(self):
        for f in self.e.choice_fields:
            p = self.props(self, self.e.form_control(f))
            self.assertEqual(p["InputTextPlaceholder"], '="%s"' % f.label, f.name)
            self.assertIn("DefaultSelectedItems", p, f.name)
            self.assertEqual(p["ItemDisplayText"], "=ThisItem.Value", f.name)


if __name__ == "__main__":
    unittest.main()
