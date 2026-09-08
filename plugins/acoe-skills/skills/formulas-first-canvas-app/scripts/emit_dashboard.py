#!/usr/bin/env python3
"""The dashboard screen: the baseline's landing page.

A port, not a copy, of the baseline app's `Dashboard.pa.yaml` (376 lines):
section title/caption, a KPI band, a status-chip pipeline, navigation tiles,
a trademark line — every identifier that touches DATA is model/entity-
derived via `model.py` and Task 6's own named formulas
(`constDashboardNavigation`, `constDashboardPipeline<Entity>`,
`constDashboardBand`, `scripts/emit_formulas.py`'s `_dashboard_specs`) —
never a raw baseline literal.

RULING 12 (Phase 3 Task 7 controller rulings): the header + navigation-rail
chrome is NOT reimplemented here. `_screen_chrome`, factored out of
`emit_screens.emit_list_screen`, produces the identical `cmp_Dashboard_Header`
/ `cmp_Dashboard_Navigation` pair a list screen gets (`cmp_<Plural>List_Header`
/ `cmp_<Plural>List_Navigation` there), parametrized only by the screen's own
naming prefix, its header's display text, and (list screens only) a refresh
formula. See that function's docstring in `emit_screens.py` for the full
rationale and the byte-identical proof this refactor did not touch the list
screen's own output.

RULING 1: Task 6 emits one `constDashboardPipeline<Entity>` table per entity
with a status field. The FIRST such entity (in `model.entities` order) gets
the bare control names (`gal_Dash_Pipeline`, `con_Dash_Pipeline`,
`con_Dash_StatusChip`, `lbl_Dash_Chip`); every subsequent one suffixes all
four with its own `entity.entity` — Power Apps control names are unique
across the whole app, so a model with more than one status-bearing entity
would otherwise emit duplicate names for entity #2 onward.

Band/pipeline eligibility is computed here by mirroring
`emit_formulas._dashboard_specs`'s OWN conditions exactly (first entity with
BOTH `money_fields` and a `status_field`, for the band; every entity with a
`status_field`, for the pipeline) — never re-derived a different way, so
this module and Task 6's formulas cannot silently disagree about whether a
`constDashboardBand`/`constDashboardPipeline<Entity>` a gallery's `Items`
references here actually exists.

TOKENS: `templates/design-tokens.pa.yaml`'s `constStyle.Dashboard` group
(`TileSize`, `TileHeight`, `BandTileSize`, `BandHeight`, `ChipHeight`,
`Radius`, `Gap`, `TileIconSize`) plus `constStyle.BasicStyle.FontColorMuted`
are this screen's ONLY new token surface — every dimension/colour this
module writes that isn't already covered by an existing `constStyle.*` token
(Spacing, BasicStyle.FontSize, Label.Height, ...) comes from one of those two
additions. `FontColorMuted` (Ruling 17, Phase 3 Task 7 fix round) is the
baseline's own muted secondary-text colour
(`constStyle.Button.ColorGrey`/`RGBA(89, 91, 95, 1)` there) — this skill had
no equivalent, so `lbl_Dash_BandCaption`/`lbl_Dash_TileCode`/
`lbl_Dash_TileUnit`/`lbl_Dashboard_Trademark` used to fall back to full body
ink (`FontColor`) and the text hierarchy flattened. The one deliberate
literal exception is `Size: =28` on `lbl_Dash_TileValue` —
`constStyle.BasicStyle.FontSize`'s own comment reserves 28 for "the one
control that shows a headline figure," which is exactly this KPI value, and
`check_tokens.py --allow-sizes` (default `28,20,14,12,11`) already permits it
as a literal. The pipeline gallery's `TemplateSize` divides `Self.Width` by a
plain COUNT literal (`len(status.vocab)`) rather than a token — a count is
not a colour/size/radius value `check_tokens.py` restricts, and it can never
collide with the forbidden dimension literals (it always appears after `/ `,
never immediately after `=`).

CONTRACT-AWARE BY CONSTRUCTION, same discipline as `emit_screens.py`: every
property is written through `_block`, imported from there rather than
duplicated, so an unknown property raises `ContractError` at generation
time. `GroupContainer` is not in `references/control-contracts.yaml` at all
— unchecked by the contract guard, same as every `GroupContainer`
`emit_screens.py` itself writes.
"""
from __future__ import annotations

from emit_screens import _block, _quote, _render_prop_line, _screen_chrome


# ---- eligibility: mirrors emit_formulas._dashboard_specs's own conditions -

def _band_entity(model):
    """The first entity (model order) with both a money field and a status
    field — the SAME condition `emit_formulas._dashboard_specs`'s band loop
    uses to decide whether `constDashboardBand` exists at all, and which
    entity/fields it is built from. Returns `None` when no entity qualifies
    — the band section is entirely omitted in that case."""
    for entity in model.entities:
        if entity.money_fields and entity.status_field is not None:
            return entity
    return None


def _pipeline_entities(model):
    """Every entity with a status field, in model order — the same
    condition `emit_formulas._dashboard_specs`'s pipeline loop uses to decide
    which `constDashboardPipeline<Entity>` tables exist."""
    return [e for e in model.entities if e.status_field is not None]


# ---- region 1+2: KPI band (title/caption + gallery), only when one exists -

def _band_section(model, item_indent):
    band = _band_entity(model)
    if band is None:
        return []
    status = band.status_field
    money = band.money_fields[0]
    currency = money.currency

    title_block = _block(
        "lbl_Dash_BandTitle", item_indent, "ModernText",
        [
            ("AccessibleLabel", "=Self.Text"),
            ("AutoHeight", "=true"),
            ("Color", "=constPrimaryColor.RGBA"),
            ("FontWeight", "=FontWeight.Bold"),
            ("Size", "=constStyle.BasicStyle.FontSize.Large"),
            ("Text", "=%s" % _quote("%s by %s" % (band.plural, status.label))),
        ])

    caption_text = model.description or (
        "%d registers · live counts" % len(model.entities))
    caption_block = _block(
        "lbl_Dash_BandCaption", item_indent, "ModernText",
        [
            ("AccessibleLabel", "=Self.Text"),
            ("AutoHeight", "=true"),
            ("Color", "=constStyle.BasicStyle.FontColorMuted.RGBA"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", "=%s" % _quote(caption_text)),
        ])

    # con_Dash_BandTile: the gallery's own per-row template. No FillPortions
    # on its three labels (they stay "auto", exempt from R3 as ModernText
    # always is) — the CONTAINER carries the explicit size instead, off the
    # enclosing Gallery's own TemplateHeight/TemplateWidth so it fills its
    # cell; TemplatePadding on the gallery itself (below) is what puts a gap
    # BETWEEN cells, so no per-tile inset literal is needed here.
    tile_block = _block(
        "con_Dash_BandTile", item_indent + 12, "GroupContainer",
        [
            ("BorderColor", "=constBrandTint.T200.RGBA"),
            ("BorderThickness", "=1"),
            ("Fill", "=constPaperColor.RGBA"),
            ("Height", "=Parent.TemplateHeight"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.XS"),
            ("PaddingBottom", "=constStyle.Spacing.S"),
            ("PaddingLeft", "=constStyle.Spacing.S"),
            ("PaddingRight", "=constStyle.Spacing.S"),
            ("PaddingTop", "=constStyle.Spacing.S"),
            ("RadiusBottomLeft", "=constStyle.Dashboard.Radius"),
            ("RadiusBottomRight", "=constStyle.Dashboard.Radius"),
            ("RadiusTopLeft", "=constStyle.Dashboard.Radius"),
            ("RadiusTopRight", "=constStyle.Dashboard.Radius"),
            ("Width", "=Parent.TemplateWidth"),
        ], variant="AutoLayout",
        children=[
            _block(
                "lbl_Dash_TileCode", item_indent + 18, "ModernText",
                [
                    ("AccessibleLabel", "=Self.Text"),
                    ("AutoHeight", "=true"),
                    ("Color", "=constStyle.BasicStyle.FontColorMuted.RGBA"),
                    ("FontWeight", "=FontWeight.Semibold"),
                    ("Size", "=constStyle.BasicStyle.FontSize.Small"),
                    ("Text", "=ThisItem.Code"),
                ]),
            _block(
                "lbl_Dash_TileValue", item_indent + 18, "ModernText",
                [
                    ("AccessibleLabel", "=Self.Text"),
                    ("AutoHeight", "=true"),
                    ("Color", "=funcMoneyTextColor(ThisItem.Amount)"),
                    ("FontWeight", "=FontWeight.Bold"),
                    # KPI-only literal — see the module docstring's TOKENS note.
                    ("Size", "=28"),
                    ("Text", "=funcAsCurrency(ThisItem.Amount)"),
                ]),
            _block(
                "lbl_Dash_TileUnit", item_indent + 18, "ModernText",
                [
                    ("AccessibleLabel", "=Self.Text"),
                    ("AutoHeight", "=true"),
                    ("Color", "=constStyle.BasicStyle.FontColorMuted.RGBA"),
                    ("Size", "=constStyle.BasicStyle.FontSize.Small"),
                    ("Text", "=%s" % _quote(currency)),
                ]),
        ])

    gallery_block = _block(
        "gal_Dash_Band", item_indent + 6, "Gallery",
        [
            ("AccessibleLabel", "=%s" % _quote(
                "%s by %s" % (band.plural, status.label))),
            ("BorderColor", "=constTransparent.RGBA"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Dashboard.BandHeight"),
            ("Items", "=constDashboardBand"),
            ("TemplatePadding", "=constStyle.Spacing.S"),
            ("TemplateSize", "=constStyle.Dashboard.BandTileSize"),
        ], variant="Horizontal", children=[tile_block])

    band_block = _block(
        "con_Dash_Band", item_indent, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Dashboard.BandHeight"),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
        ], variant="AutoLayout", children=[gallery_block])

    return [title_block, caption_block, band_block]


# ---- region 3: pipeline title + one chip-gallery per status-bearing entity

def _pipeline_section(model, item_indent):
    title_block = _block(
        "lbl_Dash_PipelineTitle", item_indent, "ModernText",
        [
            ("AccessibleLabel", "=Self.Text"),
            ("AutoHeight", "=true"),
            ("Color", "=constPrimaryColor.RGBA"),
            ("FontWeight", "=FontWeight.Bold"),
            ("Size", "=constStyle.BasicStyle.FontSize.Medium"),
            ("Text", "=%s" % _quote("Pipeline")),
        ])
    blocks = [title_block]

    for i, entity in enumerate(_pipeline_entities(model)):
        # RULING 1: bare names for the first entity, entity-suffixed for
        # every subsequent one — see the module docstring.
        suffix = "" if i == 0 else entity.entity
        status = entity.status_field
        gal_name = "gal_Dash_Pipeline" + suffix
        con_name = "con_Dash_Pipeline" + suffix
        chip_name = "con_Dash_StatusChip" + suffix
        chip_lbl_name = "lbl_Dash_Chip" + suffix
        height_formula = "=constStyle.Dashboard.ChipHeight + constStyle.Spacing.M"

        # The baseline's exact chip shape: "<value> · <count in the current
        # scope>" — `entity.scope_formula`/`status.name`, never a hand-typed
        # collection or column name, so a rename anywhere else in model.py
        # cannot silently desync this string.
        chip_text = (
            '=$"{ThisItem.S} · {CountRows(Filter(%s, %s = ThisItem.S))}"'
            % (entity.scope_formula, status.name))
        chip_lbl = _block(
            chip_lbl_name, item_indent + 18, "ModernText",
            [
                ("AccessibleLabel", "=Self.Text"),
                ("Color", "=funcStatusTextColor(ThisItem.S)"),
                ("FillPortions", "=1"),
                ("FontWeight", "=FontWeight.Semibold"),
                ("Size", "=constStyle.BasicStyle.FontSize.Small"),
                ("Text", chip_text),
            ])
        # con_Dash_StatusChip: AutoLayout Horizontal with ONE flexible child
        # (the label above, FillPortions: =1) — that alone satisfies R2
        # (check_layout.py), so this container needs no explicit size of its
        # own; Height is still given for real rendering, off the enclosing
        # Gallery's own TemplateHeight, never a literal.
        chip_block = _block(
            chip_name, item_indent + 12, "GroupContainer",
            [
                ("BorderColor", "=constBrandTint.T200.RGBA"),
                ("BorderThickness", "=1"),
                ("Fill", "=constBrandTint.T100.RGBA"),
                ("Height", "=Parent.TemplateHeight"),
                ("LayoutAlignItems", "=LayoutAlignItems.Center"),
                ("LayoutDirection", "=LayoutDirection.Horizontal"),
                ("PaddingLeft", "=constStyle.Spacing.M"),
                ("PaddingRight", "=constStyle.Spacing.M"),
                ("RadiusBottomLeft", "=constStyle.Dashboard.Radius"),
                ("RadiusBottomRight", "=constStyle.Dashboard.Radius"),
                ("RadiusTopLeft", "=constStyle.Dashboard.Radius"),
                ("RadiusTopRight", "=constStyle.Dashboard.Radius"),
                ("Width", "=Parent.TemplateWidth"),
            ], variant="AutoLayout", children=[chip_lbl])
        # TemplateSize: the baseline's own pipeline gallery divides its
        # rendered width by its vocab count (`RoundDown(Self.Width / 6, 0)`
        # for its 6-value Status field) so its chips fill one row evenly —
        # generalised here to `len(status.vocab)` rather than a hand-typed
        # 6. A plain count, not a colour/size/radius value check_tokens.py
        # restricts, and it can never collide with a forbidden dimension
        # literal (it always follows `/ `, never `=`).
        gallery_block = _block(
            gal_name, item_indent + 6, "Gallery",
            [
                ("AccessibleLabel", "=%s" % _quote("%s pipeline" % entity.plural)),
                ("BorderColor", "=constTransparent.RGBA"),
                ("FillPortions", "=0"),
                ("Height", height_formula),
                ("Items", "=constDashboardPipeline%s" % entity.entity),
                ("TemplatePadding", "=constStyle.Spacing.S"),
                ("TemplateSize", "=RoundDown(Self.Width / %d, 0)" % len(status.vocab)),
                ("Width", "=Parent.Width"),
            ], variant="Horizontal", children=[chip_block])
        wrapper_block = _block(
            con_name, item_indent, "GroupContainer",
            [
                ("BorderStyle", "=BorderStyle.None"),
                ("FillPortions", "=0"),
                ("Height", height_formula),
                ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
                ("LayoutDirection", "=LayoutDirection.Vertical"),
            ], variant="AutoLayout", children=[gallery_block])
        blocks.append(wrapper_block)

    return blocks


# ---- region 4: navigation tiles --------------------------------------------

def _tiles_section(model, item_indent):
    """`con_Dash_Tiles` -> `gal_NavigationTiles` -> `con_ScreenTiles` plus
    its two SIBLING buttons, always emitted (Task 6's
    `constDashboardNavigation` always has at least one row — one per entity
    — so unlike the band/pipeline this is never conditional).

    I3 (final review, IMPORTANT): the baseline's own gallery template
    (Dashboard.pa.yaml:303/333/349) has `con_ScreenTiles`,
    `btn_ScreenTiles_Navigate` and `btn_ScreenTiles_Count` as three SIBLING
    entries of `gal_NavigationTiles`'s template — not the two buttons
    NESTED inside the container (an earlier version of this module did
    that while keeping the baseline's absolute-position coordinates, which
    is exactly the bug: `X: =con_ScreenTiles.X`/`Y: =con_ScreenTiles.Y - 10`
    etc. position each button relative to the container FROM OUTSIDE it,
    so nesting them inside doubles up the container's own offset and the
    count badge overhangs the tile's corner instead of sitting pinned to
    it). Only `lbl_ScreenTiles_Screen` stays a real child of the container.
    `con_ScreenTiles` is `Variant: ManualLayout`, matching the baseline
    exactly: check_layout.py's own coverage limits mean R1/R2/R4 never
    apply to a ManualLayout container or its children, so every control
    here reuses the baseline's own absolute-position formulas verbatim,
    off `con_ScreenTiles`'s own Height/Width/X/Y — unchanged by this fix,
    only WHERE each control sits in the tree changed.
    """
    lbl_screen = _block(
        "lbl_ScreenTiles_Screen", item_indent + 18, "ModernText",
        [
            ("AccessibleLabel", "=Self.Text"),
            ("Align", "='TextCanvas.Align'.Center"),
            ("Color", "=constPrimaryColor.RGBA"),
            ("FontWeight", "=FontWeight.Bold"),
            ("Height", "=20"),
            ("PaddingLeft", "=constStyle.Spacing.S"),
            ("PaddingRight", "=constStyle.Spacing.S"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", "=ThisItem.DisplayName"),
            ("VerticalAlign", "=VerticalAlign.Top"),
            ("Width", "=Parent.Width"),
            ("Wrap", "=false"),
            ("Y", "=Parent.Height - Self.Height - 8"),
        ])
    btn_navigate = _block(
        "btn_ScreenTiles_Navigate", item_indent + 12, "Button",
        [
            ("AccessibleLabel", '=$"Open {ThisItem.DisplayName}"'),
            ("Appearance", "='ButtonCanvas.Appearance'.Transparent"),
            ("BasePaletteColor", "=constSecondaryColor.RGBA"),
            ("FontSize", "=constStyle.Dashboard.TileIconSize"),
            ("Height", "=con_ScreenTiles.Height"),
            ("Icon", "=ThisItem.Icon"),
            ("IconStyle", "='ButtonCanvas.IconStyle'.Filled"),
            ("Layout", "='ButtonCanvas.Layout'.IconOnly"),
            ("OnSelect", "=Navigate(ThisItem.Screen, ScreenTransition.Fade)"),
            ("Text", "=%s" % _quote("")),
            ("Width", "=con_ScreenTiles.Width"),
            ("X", "=con_ScreenTiles.X"),
            ("Y", "=con_ScreenTiles.Y"),
        ])
    btn_count = _block(
        "btn_ScreenTiles_Count", item_indent + 12, "Button",
        [
            ("AccessibleLabel", "=Self.Text"),
            ("BasePaletteColor", "=constSecondaryColor.RGBA"),
            ("BorderRadius", "=Self.Height / 2"),
            ("Height", "=30"),
            ("Layout", "='ButtonCanvas.Layout'.TextOnly"),
            ("PaddingBottom", "=0"),
            ("PaddingLeft", "=0"),
            ("PaddingRight", "=0"),
            ("PaddingTop", "=0"),
            ("Text", "=ThisItem.Count"),
            ("Width", "=30"),
            ("X", "=con_ScreenTiles.X + con_ScreenTiles.Width - Self.Width / 2"),
            ("Y", "=con_ScreenTiles.Y - 10"),
        ])
    tile_block = _block(
        "con_ScreenTiles", item_indent + 12, "GroupContainer",
        [
            ("BorderColor", "=constBrandTint.T200.RGBA"),
            ("BorderThickness", "=1"),
            ("Fill", "=constPaperColor.RGBA"),
            ("Height", "=Parent.TemplateHeight"),
            ("RadiusBottomLeft", "=constStyle.Dashboard.Radius"),
            ("RadiusBottomRight", "=constStyle.Dashboard.Radius"),
            ("RadiusTopLeft", "=constStyle.Dashboard.Radius"),
            ("RadiusTopRight", "=constStyle.Dashboard.Radius"),
            ("Width", "=Parent.TemplateWidth"),
        # I3: lbl_ScreenTiles_Screen ONLY — btn_ScreenTiles_Navigate/_Count
        # are siblings of this container in the gallery template below, not
        # children of it (see this function's own docstring).
        ], variant="ManualLayout", children=[lbl_screen])

    gallery_block = _block(
        "gal_NavigationTiles", item_indent + 6, "Gallery",
        [
            ("AccessibleLabel", "=%s" % _quote("Navigation tiles")),
            ("BorderColor", "=constTransparent.RGBA"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Dashboard.TileHeight"),
            ("Items", "=constDashboardNavigation"),
            ("TemplatePadding", "=constStyle.Spacing.S"),
            ("TemplateSize", "=constStyle.Dashboard.TileSize"),
            ("Width", "=Parent.Width"),
            # WrapCount derived from width: how many TileSize-plus-Gap
            # columns fit the gallery's OWN rendered width, floor 1 so a
            # very narrow canvas still shows a single column rather than 0.
            ("WrapCount",
             "=Max(1, RoundDown(Self.Width / (constStyle.Dashboard.TileSize + "
             "constStyle.Dashboard.Gap), 0))"),
        # I3 (final review): baseline order — con_ScreenTiles,
        # btn_ScreenTiles_Navigate, btn_ScreenTiles_Count — as three SIBLING
        # template children, not two of them nested inside the first.
        ], variant="Horizontal", children=[tile_block, btn_navigate, btn_count])

    wrapper_block = _block(
        "con_Dash_Tiles", item_indent, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Dashboard.TileHeight"),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
        ], variant="AutoLayout", children=[gallery_block])

    return [wrapper_block]


# ---- region 5: flexible spacer + trademark ---------------------------------

def _trailer(item_indent):
    """The ONE flexible spacer (blank `ModernText`, `FillPortions: =1`, no
    `Visible:`) — it absorbs whatever vertical space the fixed band/
    pipeline/tiles blocks above do not use, so the trademark line sits near
    the screen's bottom edge instead of immediately after the tiles grid —
    followed by the trademark itself. Unlike the title/caption/pipeline-
    title labels above (which stay "auto": no FillPortions, no Height, exempt
    from check_layout.py's R3 as every ModernText is), the trademark is the
    one label this task calls out explicitly as `FillPortions: =0` with an
    explicit Height, so `AutoHeight` is deliberately NOT set here — the two
    are contradictory (self-measured vs. fixed) and the explicit Height is
    the one that must win.
    """
    spacer_block = _block(
        "lbl_Dash_Spacer", item_indent, "ModernText",
        [
            ("FillPortions", "=1"),
            ("Text", "=%s" % _quote("")),
        ])
    trademark_block = _block(
        "lbl_Dashboard_Trademark", item_indent, "ModernText",
        [
            ("AccessibleLabel", "=Self.Text"),
            ("Align", "='TextCanvas.Align'.Center"),
            ("Color", "=constStyle.BasicStyle.FontColorMuted.RGBA"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.Height.Small"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", "=%s" % _quote("Created by Automation CoE ♥")),
            ("VerticalAlign", "=VerticalAlign.Bottom"),
        ])
    return [spacer_block, trademark_block]


# ---- assembly ---------------------------------------------------------------

def emit_dashboard_screen(model):
    """The dashboard screen: `cmp_Dashboard_Header`, `cmp_Dashboard_Navigation`
    (both from `_screen_chrome`), then `con_Dashboard_Body` — sized exactly
    like the list screen's own list container (`_screen_chrome`'s
    `header_name`/`nav_name` feed the same X/Y/Width/Height shape
    `emit_screens.emit_list_screen`'s `con_%sList_List` uses) — containing,
    in order: the KPI band (title/caption/gallery, omitted when no entity
    has both a money field and a status field), the pipeline title and one
    chip-gallery per status-bearing entity, the navigation tiles, a flexible
    spacer, and the trademark line.
    """
    header_block, nav_block, header_name, nav_name = _screen_chrome(
        "Dashboard", model.app_name, on_refresh=None)

    body_children = []
    body_children.extend(_band_section(model, 12))
    body_children.extend(_pipeline_section(model, 12))
    body_children.extend(_tiles_section(model, 12))
    body_children.extend(_trailer(12))

    body_block = _block(
        "con_Dashboard_Body", 6, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("Height", "=Parent.Height - %s.Height - 20" % header_name),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.M"),
            ("PaddingBottom", "=constStyle.Spacing.L"),
            ("PaddingLeft", "=constStyle.Spacing.XL"),
            ("PaddingRight", "=constStyle.Spacing.XL"),
            ("PaddingTop", "=constStyle.Spacing.L"),
            ("Width", "=Parent.Width - %s.Width - 20" % nav_name),
            ("X", "=%s.Width + 10" % nav_name),
            ("Y", "=%s.Height + 10" % header_name),
        ], variant="AutoLayout", children=body_children)

    # Screen-level Properties (Fill/LoadingSpinnerColor/OnVisible): never a
    # control property, so never routed through _block/_check_control_prop
    # (see emit_screens.py's own module docstring, M4, for why that split
    # exists) — rendered via _render_prop_line instead, exactly like
    # emit_list_screen/emit_form_screen's own top_props, since OnVisible's
    # value carries a `:` (inside `{locNavigation: false}`) that a bare
    # string line would hand to a YAML reader as an ambiguous nested
    # mapping (see _needs_block_scalar's own docstring in emit_screens.py).
    top_props = [
        ("Fill", "=constReactGray.RGBA"),
        ("LoadingSpinnerColor", "=constPrimaryColor.RGBA"),
        # I4 (final review): seeds locNavigation collapsed on entry, exactly
        # like every list screen's own OnVisible tail (emit_list_screen) —
        # without this, a dashboard-as-StartScreen app never resets the nav
        # rail's expanded/collapsed state on entry the way every other
        # screen does.
        ("OnVisible", "=UpdateContext({locNavigation: false})"),
    ]
    lines = ["Screens:", "  DashboardScreen:", "    Properties:"]
    for name, value in sorted(top_props):
        lines.extend(_render_prop_line("      ", name, value))
    lines.append("    Children:")
    for block in (header_block, nav_block, body_block):
        lines.extend(block)
    return "\n".join(lines) + "\n"
