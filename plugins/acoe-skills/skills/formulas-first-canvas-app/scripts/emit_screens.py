#!/usr/bin/env python3
"""Per-entity list and form screens.

Parameterises `templates/ListScreen.pa.yaml` and `templates/FormScreen.pa.yaml`
over `model.Entity` — same chrome (header, navigation, command bar, empty
state, notification, spinner; delete dialog on the form), but every identifier
that touches DATA is entity-derived via `model.py` (the single source of
truth: `entity.collection`, `entity.gallery`, `entity.loc_var`,
`entity.scope_formula`, `entity.head_control`/`cell_control`/`form_control`,
`entity.choices_table`) — never the templates' generic `colItems`/`locItem`/
`gal_List_Items`, which stay in the templates as a pattern to read.

CONTRACT-AWARE BY CONSTRUCTION (Phase 1's whole point): every CONTROL property
this module writes — via `_block`, for a plain control (ModernText,
ModernTextInput, ModernCombobox, ModernDatePicker, Button, Gallery) via
`_check_control_prop`, or for a CanvasComponent instance (cmp_Header,
cmp_FilterButton, ...) against that component's own declared CustomProperties
via `_check_component_prop` — is checked against
`references/control-contracts.yaml` BEFORE the property line is ever written.
An unknown property raises `ContractError` at generation time, never at push
time. `check_control_props.py` reads the exact same contract file, so
`tests/test_emit_screens.py`'s `TestGeneratedOutputPassesTheContractGuard`
passes because the emitter is correct, not because output was tuned until the
guard went quiet.

M4: this does NOT cover the handful of top-level SCREEN properties (`Fill`,
`LoadingSpinnerColor`, `OnVisible`) that `emit_list_screen`/`emit_form_screen`
write directly via `_render_prop_line`, bypassing `_block` entirely — a
Screen is not a control and has no entry in control-contracts.yaml for
`_check_control_prop` to check it against. An earlier version of this
docstring claimed blanket coverage; that was an overclaim, not a description
of what the code does.

ARCHETYPE -> CONTROL (grid cell always ModernText; only Color/Text/Align
formulas vary):

    text, longtext  ModernTextInput (Type: Multiline for longtext)
    choice          ModernCombobox, SelectMultiple: =false
    number          ModernTextInput, no Format — parsed with Value() on save
    date            ModernDatePicker
    boolean         ModernToggle if present in the contract file, else
                    ModernCombobox over an inline two-row Yes/No table.
                    As of writing, ModernToggle is NOT in
                    references/control-contracts.yaml (confirmed by reading
                    it) — Ruling 2 forbids inventing a contract entry to get
                    it, so the fallback is what ships. `_boolean_form_input`
                    raises loudly if ModernToggle ever appears in the
                    contract file without this module being updated to use
                    it, rather than silently guessing its property shape.

Component inputs take STRINGS, never enums: `cmp_FilterButton.Align` is
`DataType: Text`, so a money column's header gets `Align: ="Right"`, not
`Align: =Align.Right`.

Galleries always get `FillPortions: =1` — a Gallery is a leaf control; inside
an auto-layout container it otherwise defaults to FillPortions 0 and collapses
to the ~200px control default.

`model` (the second argument to both `emit_*` functions) is accepted per the
Task 4 interface for forward compatibility with cross-entity concerns a later
task may add (e.g. foreign-key pickers); nothing in this module reads it yet
because nothing in today's `model.Entity` needs another entity's shape.
"""
from __future__ import annotations

import pathlib

import check_control_props as ccp

SKILL = pathlib.Path(__file__).resolve().parents[1]

CONTRACTS = ccp.load_contracts()
COMPONENTS = ccp.parse_component_defs(
    sorted((SKILL / "components").glob("cmp_*.pa.yaml")))


class ContractError(Exception):
    """Raised when the emitter is about to write a property that
    references/control-contracts.yaml (for a plain control) or a component's
    own declared CustomProperties (for a CanvasComponent instance) does not
    recognise. This is the mistake-fails-at-generation-time guard Phase 1
    exists to provide — never silence this by adding the property to the
    contract file from here; that is a corpus-evidence ruling, not an
    implementation detail (see the module docstring's boolean note)."""


def _check_control_prop(control_type, prop):
    spec = CONTRACTS["controls"].get(control_type)
    if spec is None:
        # Not covered by the contract file at all (e.g. GroupContainer) —
        # check_control_props.py itself treats this as "unchecked", not
        # "failed", so there is nothing for the emitter to validate against.
        return
    if prop not in spec["properties"]:
        raise ContractError(
            "%s.%s is not a known property in references/control-contracts.yaml"
            % (control_type, prop))


def _check_component_prop(component_name, prop):
    declared = COMPONENTS.get(component_name)
    if declared is None:
        raise ContractError(
            "component %r was not found under components/*.pa.yaml" % component_name)
    if prop in declared or prop in ccp.UNIVERSAL_INSTANCE_PROPS:
        return
    raise ContractError(
        "component %s declares no %s input (declared: %s)"
        % (component_name, prop, ", ".join(sorted(declared)) or "none"))


# ---- generic block renderer ----------------------------------------------
# One control's YAML, as the value of a `- name:` list item. `item_indent` is
# the column the leading "- " sits at; Control/Variant/ComponentName/
# Properties/Children all sit at item_indent+4, property VALUES at
# item_indent+6 (matching templates/ListScreen.pa.yaml's own nesting: a
# top-level item at column 6 has its `Control:` at column 10 and its
# property lines at column 12). `children` is a list of already-rendered
# line-lists, each produced by a recursive `_block(..., item_indent=I+6)`
# call — callers own the recursion, this function only stitches them in.

def _needs_block_scalar(value):
    """A value must be written as a YAML `|-` block scalar, not inline,
    whenever it contains anything a plain YAML scalar cannot hold safely:

    * an embedded newline (an explicit multi-statement formula), or
    * a colon (a Power Fx record literal like `{locDirty: true}` — YAML's
      block-mapping grammar reads an unquoted `: ` inside a plain scalar as
      the start of a NESTED mapping, which corrupts the document silently
      for a line-oriented reader and raises `yaml.safe_load` outright for a
      real one), or
    * a `#` (Ruling 16/C2: YAML treats a space followed by `#` as the start
      of a COMMENT in a plain scalar — `Label: ="ORDER # REF"` is emitted,
      parsed, and quietly truncated to `Label: ="ORDER`, with everything
      after the `#` gone. The file stays perfectly valid YAML, which is
      exactly why no well-formedness check can see this — only a value-aware
      reader like this function can), or
    * leading/trailing whitespace (defensive: a plain scalar's surrounding
      whitespace is not part of its value once the wrapping quotes are
      stripped by a downstream tool, so anything already touching the edges
      of the line is not safe to trust to inline rendering either).

    This is not cosmetic: `OnChange: =UpdateContext({locDirty: true})`
    rendered inline breaks the file, and `Label: ="ORDER # REF"` breaks it
    silently. `templates/*.pa.yaml` always wraps the colon/newline shape in
    `|-` for exactly this reason, even for a single logical line.
    """
    return ("\n" in value or ":" in value or "#" in value
            or value != value.strip())


def _render_prop_line(pad, name, value):
    if _needs_block_scalar(value):
        lines = ["%s%s: |-" % (pad, name)]
        lines.extend("%s    %s" % (pad, vline) for vline in value.split("\n"))
        return lines
    return ["%s%s: %s" % (pad, name, value)]


def _block(name, item_indent, control_type, props, variant=None,
           component_name=None, children=None):
    pad_item = " " * item_indent
    pad_ctrl = " " * (item_indent + 4)
    pad_prop = " " * (item_indent + 6)
    lines = ["%s- %s:" % (pad_item, name)]
    lines.append("%sControl: %s" % (pad_ctrl, control_type))
    if variant:
        lines.append("%sVariant: %s" % (pad_ctrl, variant))
    if component_name:
        lines.append("%sComponentName: %s" % (pad_ctrl, component_name))
    if props:
        lines.append("%sProperties:" % pad_ctrl)
        for prop_name, value in sorted(props):
            if control_type == "CanvasComponent":
                _check_component_prop(component_name, prop_name)
            else:
                _check_control_prop(control_type, prop_name)
            lines.extend(_render_prop_line(pad_prop, prop_name, value))
    if children:
        lines.append("%sChildren:" % pad_ctrl)
        for child_lines in children:
            lines.extend(child_lines)
    return lines


def _quote(text):
    return '"' + str(text).replace('"', '""') + '"'


FLEX_COLUMN_PX = 240   # the baseline has no flex column; a "flex" field becomes a wide fixed one


def _column_px(field):
    """Pixel width for a grid column. `grid: flex` is a wide fixed column — the
    baseline has no flex column at all; one FillPortions=1 header crushes its
    fixed siblings to zero width on a narrow canvas (seen live 2026-09-07)."""
    return FLEX_COLUMN_PX if field.grid_width == "flex" else int(field.grid_width)


ROW_OPEN_WIDTH = "constStyle.List.RowOpenWidth"


def _row_min_width_formula(grid_fields):
    """LayoutMinWidth shared by the header row (`con_%sList_Headers`) and
    the gallery (`entity.gallery`) — I2 (final review): the raw column-width
    sum alone under-states the row's real rendered width. Both rows lay out
    their children Horizontal with `LayoutGap: =constStyle.Spacing.S`
    between every pair, and the gallery's row template has an (N+1)th child
    (`btn_<Plural>Row_Open`, no width previously) the header has no
    counterpart for at all — below ~1050px this clipped the trailing column
    and the Open button, and `LayoutOverflowX: Scroll` only ever scrolled to
    the (too-small) column sum.

    The fix gives the header row its own trailing spacer cell of the SAME
    width as the Open button (see `emit_list_screen`), so both rows have
    identical child counts (`len(grid_fields) + 1`) and therefore identical
    gap counts (`len(grid_fields)`) — the formula below is exactly that
    shape: the column-width sum stays a plain literal (same discipline
    `_column_dims` already uses for one column), but the gap multiplier and
    the Open width are TOKEN REFERENCES, never their resolved literals, so a
    future change to `constStyle.Spacing.S` or `constStyle.List.RowOpenWidth`
    is reflected here without touching this generator.
    """
    total = sum(_column_px(f) for f in grid_fields)
    return "=%d + %d * constStyle.Spacing.S + %s" % (
        total, len(grid_fields), ROW_OPEN_WIDTH)


def _column_dims(field):
    """`Width` + `LayoutMinWidth`, both pinned to the SAME pixel value
    (Task 1/baseline conformance): every grid column is fixed now, none
    flex — see `_column_px`. `LayoutMinWidth` is what lets the header row
    and the gallery declare a combined min-width (the sum over all columns)
    so the table can scroll horizontally instead of squeezing columns to
    fit a narrow canvas.

    Carried finding from the previous `_width_pair`: `field.grid_width` can
    also be the string "hidden" — but this is only ever called with a field
    drawn from `entity.grid_fields`, which already excludes hidden fields,
    so "hidden" can never reach here. The assert makes that invariant loud
    instead of producing `Width: =hidden`.
    """
    assert field.grid_width != "hidden", (
        "_column_dims called on a grid-hidden field %r — read widths off "
        "entity.grid_fields, never entity.form_fields" % field.name)
    px = _column_px(field)
    return [("LayoutMinWidth", "=%d" % px), ("Width", "=%d" % px)]


_HEADER_DATATYPE = {
    "text": "string", "longtext": "string", "choice": "string",
    "number": "number", "date": "date", "boolean": "boolean",
}


# ---- screen chrome: header + nav rail, shared by every screen ------------

def _screen_chrome(prefix, display_name, on_refresh=None):
    """The `cmp_<prefix>_Header` / `cmp_<prefix>_Navigation` pair every
    screen composes as direct SCREEN children — the baseline's own header +
    nav-rail skeleton (Task 1/baseline conformance), factored out here
    (Ruling 12, Phase 3 Task 7) so a SECOND screen family (the dashboard,
    `emit_dashboard.py`) can produce the identical pair without copying
    these absolute-position formulas into a second module. `emit_list_screen`
    below is this function's only OTHER caller; `TestListScreenMatchesBaselineSkeleton`
    (tests/test_emit_screens.py) is the byte-identical gate that proves this
    refactor changed nothing about its output.

    `prefix` is the screen's own naming stem — `"<Plural>List"` for a list
    screen, `"Dashboard"` for the dashboard — and nothing else about it is
    entity-derived: `cmp_AssetsList_Header`/`cmp_AssetsList_Navigation` and
    `cmp_Dashboard_Header`/`cmp_Dashboard_Navigation` are both just
    `"cmp_%s_Header" % prefix` / `"cmp_%s_Navigation" % prefix`.

    `display_name` is the header's title text (a list screen shows its own
    `entity.plural`; the dashboard shows `model.app_name`). `on_refresh`,
    when given, is the OnSelectRefresh formula body — a list screen always
    has exactly one entity's own reload action to run and so always passes
    one; the dashboard has no single entity to reload and passes `None`,
    which omits `CanRefresh`/`NotificationCount`/`OnSelectRefresh` entirely
    rather than wiring a refresh button to nothing.

    Returns `(header_block, nav_block, header_name, nav_name)` — the last
    two so a caller's OWN direct children (the list screen's
    `con_%sList_List`, the dashboard's `con_Dashboard_Body`) can position
    themselves off `<header_name>.Height` / `<nav_name>.Width` exactly like
    the baseline does.
    """
    header_name = "cmp_%s_Header" % prefix
    nav_name = "cmp_%s_Navigation" % prefix

    header_props = [
        ("AllowNavigation", "=true"),
        ("DisplayName", "=%s" % _quote(display_name)),
        ("Height", "=constStyle.Header.Height"),
        ("IsLoading", "=glBoolIsLoading"),
        ("OnNavigate", "=UpdateContext({locNavigation: !locNavigation})"),
        ("Width", "=Parent.Width"),
    ]
    if on_refresh is not None:
        header_props.extend([
            ("CanRefresh", "=true"),
            ("NotificationCount", "=CountRows(colNotifications)"),
            ("OnSelectRefresh", on_refresh),
        ])
    header_block = _block(header_name, 6, "CanvasComponent", header_props,
                          component_name="cmp_Header")

    # cmp_<prefix>_Navigation: a direct SCREEN child, self-sizing off its OWN
    # Navigation input via Self-referential-by-name formulas (copied from the
    # baseline verbatim, substituting only the control name), never a
    # FillPortions share of a wrapper.
    nav_block = _block(
        nav_name, 6, "CanvasComponent",
        [
            ("Height", "=Parent.Height - %s.Height" % header_name),
            ("Navigation", "=locNavigation"),
            ("OnClose", "=UpdateContext({locNavigation: false})"),
            # C1 (final review, CRITICAL): the component's own Screens
            # Default (components/cmp_Navigation.pa.yaml) is only a one-row
            # TYPED SEED — proven live, kept exactly as shipped — never the
            # real registry. Its menu gallery reads
            # `Filter(cmp_Navigation.Screens, Type = enumScreenType.List)`,
            # so without this instance override every generated nav rail
            # renders EMPTY and constScreens (defined in App.pa.yaml) is
            # never read anywhere. Baseline: Activities.pa.yaml:97
            # (cmp_Activities_Navigation carries the identical
            # `Screens: =constScreens`).
            ("Screens", "=constScreens"),
            ("Width", "=If(%s.Navigation, 250, 60)" % nav_name),
            ("Y", "=%s.Y + %s.Height" % (header_name, header_name)),
        ], component_name="cmp_Navigation")

    return header_block, nav_block, header_name, nav_name


# ---- list screen: per-field pieces ---------------------------------------

def _header_sort_toggle(entity, field):
    """Ruling 19/I2: clicking a column header must toggle that column's sort
    state in `colSorts` — before this fix, `_header_block` never emitted
    `OnSelect` at all, so nothing ever wrote `colSorts`, `IsSorted` was
    permanently false, and the gallery's `SortByColumns` (which reads
    `LookUp(colSorts, Table = <entity>).ID`/`.SortOrder`) was frozen on
    whatever `OnVisible` seeded once at screen load.

    `UpdateIf`, not `With()`: `OnVisible` (see `top_props` below) guarantees
    there is always exactly one `colSorts` row for this entity's
    `enum_member`, so a click only ever needs to UPDATE it, never insert one.
    `UpdateIf`'s change record is evaluated against the ORIGINAL row being
    replaced — `ID`/`SortOrder` inside it read the row's value BEFORE this
    update — which is what lets the direction flip (asc -> desc -> asc) read
    its own prior state without a scratch variable: clicking the currently-
    sorted column's header flips `SortOrder`; clicking any other column
    resets to ascending.
    """
    return (
        "=UpdateIf(\n"
        "    colSorts,\n"
        "    Table = %s,\n"
        "    {\n"
        "        ID: %s,\n"
        "        SortOrder: If(\n"
        "            ID = %s And SortOrder = \"asc\",\n"
        "            \"desc\",\n"
        "            \"asc\"\n"
        "        )\n"
        "    }\n"
        ")"
    ) % (entity.enum_member, _quote(field.name), _quote(field.name))


def _header_block(entity, field, item_indent):
    """One `cmp_FilterButton` instance — a column header that doubles as the
    filter/sort affordance. Its own custom-property contract is
    components/cmp_FilterButton.pa.yaml, checked via `_check_component_prop`.
    """
    props = [
        ("DataType", "=%s" % _quote(_HEADER_DATATYPE[field.type])),
        ("Field", "=%s" % _quote(field.name)),
        ("Height", "=constStyle.List.HeaderHeight"),
        ("IsFiltered", "=%s in colFilters.ID" % _quote(field.name)),
        ("IsSorted", "=%s in colSorts.ID" % _quote(field.name)),
        ("Label", "=%s" % _quote(field.label)),
        ("OnSelect", _header_sort_toggle(entity, field)),
        ("Title", "=%s" % _quote(field.name)),
    ]
    if field.type == "choice":
        props.append(("Choices", "=%s" % entity.choices_table(field)))
    if field.type == "number":
        # Component inputs take STRINGS: cmp_FilterButton.Align is
        # DataType: Text, never the Align enum.
        props.append(("Align", "=%s" % _quote("Right")))
    props.extend(_column_dims(field))
    return _block(entity.head_control(field), item_indent, "CanvasComponent",
                  props, component_name="cmp_FilterButton")


def _cell_block(entity, field, item_indent):
    """One grid cell. Every archetype renders as ModernText — only the
    Color/Text/Align formulas vary. Money and semafor-choice colour route
    through the ONE function that owns that decision (funcMoneyTextColor,
    funcStatusTextColor) rather than a Switch re-authored per screen.
    """
    color = "=constStyle.BasicStyle.FontColor"
    size = "=constStyle.BasicStyle.FontSize.Medium"
    align = None
    ref = "ThisItem.%s" % field.name

    if field.type in ("text", "longtext"):
        text = "=funcEllipsis(%s, 48)" % ref
    elif field.type == "choice":
        text = "=%s" % ref
        size = "=constStyle.BasicStyle.FontSize.Small"
        if field.semantics == "semafor":
            color = "=funcStatusTextColor(%s)" % ref
    elif field.type == "number":
        align = "=constStyle.Label.NumberInput.AlignModern"
        if field.money:
            text = "=funcAsCurrency(%s)" % ref
            color = "=funcMoneyTextColor(%s)" % ref
        else:
            text = "=Text(%s)" % ref
    elif field.type == "date":
        text = "=Text(%s, DateTimeFormat.ShortDate)" % ref
        if field.semantics == "due":
            color = ("=If(%s < Today(), constLossTextColor.RGBA, "
                      "constStyle.BasicStyle.FontColor)" % ref)
    elif field.type == "boolean":
        text = '=If(%s, "Yes", "No")' % ref
    else:
        raise ContractError("unhandled field archetype: %r" % field.type)

    props = [("Color", color), ("Size", size), ("Text", text)]
    if align:
        props.append(("Align", align))
    props.extend(_column_dims(field))
    return _block(entity.cell_control(field), item_indent, "ModernText", props)


def _search_clause(entity, search_ctrl):
    fields = entity.search_fields
    if not fields:
        return "true"
    ors = " Or\n    ".join("%s.Text in %s" % (search_ctrl, f.name) for f in fields)
    return "IsBlank(%s.Text) Or\n    %s" % (search_ctrl, ors)


def _filter_clause(entity, filter_ctrls):
    """`filter_ctrls`: {field.name: combobox control name} for every
    choice-type filter field. Only choice fields get a combobox filter
    widget — a `filter: true` on a non-choice field is accepted by the model
    but this generator does not (yet) build a widget for it, so it is simply
    left out of the clause rather than guessed at.

    Ruling 15/C1: the clause for EACH field is its own `IsEmpty(...) Or
    <field> in ...` pair — that `Or` is what makes an UNSET combobox mean "no
    constraint from this field" (IsEmpty is true, so the pair is
    true regardless of the field's value). But the fields themselves must be
    joined with `And`: filtering is supposed to narrow the result to rows
    that satisfy EVERY active filter at once. Joining fields with `Or`
    instead (the original bug) means picking a value in any ONE combobox
    makes every other combobox's own `IsEmpty(...) Or ...` pair irrelevant —
    the whole predicate short-circuits to `true` and nothing is ever
    filtered out. Each field's pair is parenthesised so `And`/`Or` precedence
    is never ambiguous when there is more than one filter field.
    """
    if not filter_ctrls:
        return "true"
    parts = []
    for field_name, ctrl in filter_ctrls.items():
        parts.append("(IsEmpty(%s.SelectedItems) Or %s in %s.SelectedItems.Value)"
                      % (ctrl, field_name, ctrl))
    return " And\n    ".join(parts)


def _visible_rows_expr(entity, filter_ctrls, search_ctrl):
    """The `Filter(...)` expression that decides which rows are visible in
    the grid right now — factored into ONE function so the gallery's `Items`
    and the footer's aggregates read the textually IDENTICAL expression and
    cannot silently drift apart (Ruling 18/I1: the footer used to read the
    bare, unfiltered `entity.scope_formula` while the gallery read
    `Filter(scope, filters, search)`, so the count was permanently "N of N"
    and the money `Sum()` ignored search entirely — the exact opposite of
    what Ruling 12 asked for). Every caller below embeds this SAME rendered
    text rather than rebuilding an equivalent expression by hand, so the two
    genuinely cannot disagree.

    Returned with the first line unindented and continuation lines at a
    relative 4-space indent; callers splice it in and reindent as needed
    (see the `.replace("\\n", "\\n    ")` calls below).
    """
    return (
        "Filter(\n"
        "    %s,\n"
        "    %s,\n"
        "    %s\n"
        ")"
    ) % (entity.scope_formula, _filter_clause(entity, filter_ctrls),
         _search_clause(entity, search_ctrl))


def _footer_block(entity, item_indent, filter_ctrls, search_ctrl):
    """The footer aggregate strip (Ruling 12, corrected by Ruling 18/I1): a
    filtered/total count and a `Sum()` per `money: true` field that read the
    SAME `Filter(...)` expression the gallery's `Items` reads
    (`_visible_rows_expr`) — that is what makes it genuinely impossible for
    this count to disagree with what the grid shows, rather than merely
    claiming so. The "of M" denominator stays the full, unfiltered
    `entity.collection` — "Showing 4 of 16" — so the total is legible even
    while filtered. `Sum()` totals are formatted through `funcAsCurrency` so
    currency formatting stays owned by one function.

    A fixed-height, `FillPortions: =0` sibling of the gallery (which keeps
    `FillPortions: =1`): the same leaf-control-collapse rule that requires
    the gallery's own `FillPortions` applies here too.

    Ruling 14: the container's OWN sizing (above) said nothing about its
    CHILDREN inside this Horizontal layout — every one of them still needs
    a main-axis size (check_layout.py's Rule 1). The count label is the
    ONE flexible child (`FillPortions: =1`), which both satisfies Rule 1
    (no width needed once it isn't `=0`) and gives the strip its natural
    layout: the count sits at the left edge of the space it absorbs, and
    any money totals land pinned to the right of it. Money-total labels
    stay fixed (`FillPortions: =0`) with an explicit Width, since their
    text is short and bounded ("Label: $amount") and letting them flex
    would just leave them adrift in the middle of the strip.
    """
    visible = _visible_rows_expr(entity, filter_ctrls, search_ctrl)
    count_text = ('="Showing " & CountRows(\n    %s\n) & " of " & CountRows(%s)'
                  % (visible.replace("\n", "\n    "), entity.collection))
    cells = [_block(
        "lbl_%sList_Count" % entity.plural, item_indent + 6, "ModernText",
        [
            ("Color", "=constStyle.BasicStyle.FontColor"),
            ("FillPortions", "=1"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", count_text),
        ])]
    for f in entity.fields:
        if f.type != "number" or not f.money:
            continue
        # Coalesce(..., 0): Sum() over a filtered-to-nothing set returns
        # blank, not 0 — funcAsCurrency(blank) is not "0", it is whatever
        # that function does with a non-number. Coalesce pins the floor.
        total_text = ('="%s: " & funcAsCurrency(Coalesce(Sum(\n    %s,\n    %s\n), 0))'
                      % (f.label, visible.replace("\n", "\n    "), f.name))
        cells.append(_block(
            "lbl_%sList_%sTotal" % (entity.plural, f.name), item_indent + 6, "ModernText",
            [
                ("Color", "=constStyle.BasicStyle.FontColor"),
                ("FillPortions", "=0"),
                ("Size", "=constStyle.BasicStyle.FontSize.Small"),
                ("Text", total_text),
                ("Width", "=200"),
            ]))
    return _block(
        "con_%sList_Footer" % entity.plural, item_indent, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.Height.Medium"),
            ("LayoutAlignItems", "=LayoutAlignItems.Center"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.L"),
        ], variant="AutoLayout", children=cells)


def emit_list_screen(entity, model):
    """The list screen for `entity`: search, per-field filter/sort headers,
    a gallery of row cells, an empty state, and the standard chrome (header,
    navigation, command bar, notifications, spinner).

    Task 1 (baseline conformance): the header/nav/list skeleton mirrors the
    baseline's Activities.pa.yaml, not the earlier `con_%sList_Main`
    horizontal-wrapper shape. `cmp_%sList_Header`, `cmp_%sList_Navigation`
    and `con_%sList_List` are direct SCREEN children — each absolutely
    positioned off `Parent.Height`/`Parent.Width` and each other's own
    Height/Width/Y — never a FillPortions share of a wrapper GroupContainer.
    That wrapper (`con_%sList_Main`, Horizontal, nav + body as its two
    FillPortions children) is what flexed the nav rail to half the screen
    live on 2026-09-07: a Horizontal auto-layout container divides ITS OWN
    width between flexible children, so the nav's `FillPortions: =0` fixed
    width was never actually fixed against the container's real width the
    way an absolute `Width` formula is.
    """
    search_ctrl = "txt_%sList_Search" % entity.plural
    grid_fields = entity.grid_fields
    default_sort_field = grid_fields[0].name if grid_fields else entity.fields[0].name
    # I2 (final review): the header row and the gallery share this ONE
    # LayoutMinWidth formula so the table scrolls horizontally as one unit
    # instead of squeezing columns — see _row_min_width_formula's own
    # docstring for why the raw column-width sum alone is not enough.
    row_min_width = _row_min_width_formula(grid_fields)

    # cmp_%sList_Header / cmp_%sList_Navigation: the baseline's own header +
    # nav-rail pair, via the shared _screen_chrome helper (Ruling 12, Phase 3
    # Task 7) — see that function's docstring for why this is not entity-
    # specific beyond the prefix/display name/refresh formula passed in here.
    refresh_formula = (
        "=funcStartLoading();\n"
        "%s();\n"
        "funcStopLoading();\n"
        "funcNotifySuccess(\"Data reloaded.\")" % entity.func_load)
    header_block, nav_block, header_name, nav_name = _screen_chrome(
        "%sList" % entity.plural, entity.plural, on_refresh=refresh_formula)

    filter_ctrls = {}
    for f in entity.filter_fields:
        if f.type == "choice":
            filter_ctrls[f.name] = "com_%sList_%sFilter" % (entity.plural, f.name)

    # ---- gallery row: cell per grid field + an "Open" button -------------
    row_children = [_cell_block(entity, f, item_indent=30) for f in grid_fields]
    open_btn = _block(
        "btn_%sRow_Open" % entity.plural, 30, "Button",
        [
            ("AccessibleLabel", "=\"Open \" & ThisItem.%s" % default_sort_field),
            ("Height", "=constStyle.Button.Height.Small"),
            ("OnSelect", "=Set(glSelectedKey, ThisItem.Key);\n"
                         "funcAddBack();\n"
                         "Navigate(%s)" % entity.form_screen),
            ("Text", "=%s" % _quote("Open")),
            # I2 (final review): an explicit Width, via the same token the
            # header's trailing spacer and the row's own LayoutMinWidth
            # reserve space for — previously unset, so nothing accounted
            # for this 8th child's own footprint in the row's rendered
            # width. Baseline: Activities.pa.yaml btn_Row_Open, Width: =32.
            ("Width", "=%s" % ROW_OPEN_WIDTH),
        ])
    row_children.append(open_btn)
    row_block = _block(
        "con_%sRow" % entity.plural, 24, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("Fill", "=If(ThisItem.IsSelected, constBrandTint.T100.RGBA, "
                     "constPaperColor.RGBA)"),
            ("Height", "=constStyle.List.TemplateHeight"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.S"),
            ("Width", "=Parent.Width"),
        ], variant="AutoLayout", children=row_children)

    items_formula = (
        "=SortByColumns(\n"
        "    %s,\n"
        "    // WARNING: this string column name is NEVER validated by the\n"
        "    // compiler. check_collection_columns.py is what catches a typo.\n"
        "    funcTableSortColumn(%s),\n"
        "    If(\n"
        "        funcTableSortOrder(%s) = \"desc\",\n"
        "        SortOrder.Descending,\n"
        "        SortOrder.Ascending\n"
        "    )\n"
        ")"
    ) % (_visible_rows_expr(entity, filter_ctrls, search_ctrl).replace("\n", "\n    "),
         entity.enum_member, entity.enum_member)

    gallery_block = _block(
        entity.gallery, 18, "Gallery",
        [
            ("AccessibleLabel", "=%s" % _quote("%s table" % entity.plural)),
            ("BorderColor", "=constTransparent.RGBA"),
            ("FillPortions", "=1"),
            ("Items", items_formula),
            ("LayoutMinWidth", row_min_width),
            ("TemplateSize", "=constStyle.List.TemplateHeight"),
        ], variant="Vertical", children=[row_block])

    empty_block = _block(
        "cmp_%sList_Empty" % entity.plural, 18, "CanvasComponent",
        [
            ("FillPortions", "=0"),
            ("Height", "=200"),
            ("Icon", "=%s" % _quote("Search")),
            ("Message", "=%s" % _quote("No %s match these filters" % entity.plural.lower())),
            ("Visible", "=IsEmpty(%s.AllItems)" % entity.gallery),
        ], component_name="cmp_Empty")

    footer_block = _footer_block(entity, 12, filter_ctrls, search_ctrl)

    # ---- toolbar: search box, one filter combobox per choice filter field,
    # command bar ------------------------------------------------------------
    toolbar_children = [_block(
        search_ctrl, 18, "ModernTextInput",
        [
            ("AccessibleLabel", "=%s" % _quote("Search %s" % entity.plural.lower())),
            ("Appearance", "=constStyle.Label.TextInput.Appearance"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.TextInput.Height.SingleLine"),
            ("Placeholder", "=%s" % _quote("Search")),
            ("Width", "=280"),
        ])]
    for f in entity.filter_fields:
        if f.type != "choice":
            continue
        ctrl = filter_ctrls[f.name]
        toolbar_children.append(_block(
            ctrl, 18, "ModernCombobox",
            [
                ("AccessibleLabel", "=%s" % _quote("Filter by %s" % f.name)),
                # Empty but TYPED default selection. Without it an untouched
                # ModernCombobox has no defined selection state,
                # IsEmpty(SelectedItems) never returns true, and the gallery
                # stays empty until the first reset. (Baseline comment,
                # translated; confirmed live 2026-09-07 — the grid read "0 of 16".)
                #
                # Ruling 6: this rationale must reach the GENERATED APP, not
                # just this generator — a maker who opens the property in
                # Studio and sees a bare `=FirstN(...)` with no explanation
                # will delete it as redundant. So the SAME rationale is also
                # embedded as a `//` Power Fx comment INSIDE the formula
                # value itself, baseline-style (Activities.pa.yaml lines
                # 156-161) — the Python comment above documents the
                # generator; the formula comment below is what a maker
                # actually sees.
                ("DefaultSelectedItems",
                 "=// Empty but TYPED default selection. Without it an untouched\n"
                 "// ModernCombobox has no defined selection state, IsEmpty(SelectedItems)\n"
                 "// never returns true, and the gallery stays empty until the first reset.\n"
                 "FirstN(%s, 0)" % entity.choices_table(f)),
                ("FillPortions", "=0"),
                ("Height", "=constStyle.Combobox.Height.Medium"),
                ("InputTextPlaceholder", "=%s" % _quote(f.label)),
                ("IsSearchable", "=false"),
                ("ItemDisplayText", "=ThisItem.Value"),
                ("Items", "=%s" % entity.choices_table(f)),
                ("SelectMultiple", "=true"),
                ("Width", "=200"),
            ]))
    toolbar_children.append(_block(
        "cmp_%sList_Commands" % entity.plural, 18, "CanvasComponent",
        [
            ("CanAdd", "=true"),
            ("CanRemoveFilters", "=!IsEmpty(colFilters)"),
            ("FillPortions", "=1"),
            ("Height", "=constStyle.Label.Height.Medium"),
            ("OnAdd", "=Set(glSelectedKey, \"\");\n"
                      "funcAddBack();\n"
                      "Navigate(%s)" % entity.form_screen),
            ("OnRemoveFilter", "=Clear(colFilters)"),
        ], component_name="cmp_CommandBar"))
    toolbar_block = _block(
        "con_%sList_Toolbar" % entity.plural, 12, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.Height.Medium"),
            ("LayoutAlignItems", "=LayoutAlignItems.Center"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.S"),
        ], variant="AutoLayout", children=toolbar_children)

    # I2 (final review): a trailing, blank spacer cell the same width as the
    # gallery row's own Open button — the header has no per-column
    # counterpart for that trailing column at all, so without this the
    # header row has one fewer child (and one fewer gap) than the gallery
    # row, and the two drift out of column alignment the moment the canvas
    # narrows to the shared LayoutMinWidth floor. Baseline idea (not shape):
    # Activities.pa.yaml's own header row ends in a trailing cell
    # (lbl_Activities_HeaderProgress, LayoutMinWidth: =60) that plays the
    # same "close out the row" role for whatever trails the last real
    # column there.
    header_spacer_block = _block(
        "lbl_%sList_HeaderSpacer" % entity.plural, 24, "ModernText",
        [
            ("Text", "=%s" % _quote("")),
            ("Width", "=%s" % ROW_OPEN_WIDTH),
        ])
    headers_block = _block(
        "con_%sList_Headers" % entity.plural, 18, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.List.HeaderHeight"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.S"),
            ("LayoutMinWidth", row_min_width),
        ], variant="AutoLayout",
        children=[[l for f in grid_fields for l in _header_block(entity, f, 24)],
                  header_spacer_block])

    # con_%sList_Table: header row + gallery + empty state, one scrolling
    # unit (Task 1/baseline conformance, modelled on the baseline's
    # con_Activities_Table) — this is what lets fixed-width columns overflow
    # a narrow canvas horizontally instead of being crushed to fit it.
    table_block = _block(
        "con_%sList_Table" % entity.plural, 12, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=1"),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.S"),
            ("LayoutOverflowX", "=LayoutOverflow.Scroll"),
        ], variant="AutoLayout", children=[headers_block, gallery_block, empty_block])

    # con_%sList_List: the baseline's con_Activities_List — a direct SCREEN
    # child, absolutely positioned off the nav rail's OWN Width (never a
    # fixed 250/60 literal) and the header's Height. See the module
    # docstring above for why this replaces the old FillPortions wrapper.
    list_block = _block(
        "con_%sList_List" % entity.plural, 6, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("Height", "=Parent.Height - %s.Height - 20" % header_name),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.M"),
            # Carried from the pre-Task-1 con_%sList_Body: this container's
            # own inset from its (new) absolutely-positioned edges. Nothing
            # about the skeleton restructure changes this padding.
            ("PaddingBottom", "=constStyle.Spacing.L"),
            ("PaddingLeft", "=constStyle.Spacing.XL"),
            ("PaddingRight", "=constStyle.Spacing.XL"),
            ("PaddingTop", "=constStyle.Spacing.L"),
            ("Width", "=Parent.Width - %s.Width - 20" % nav_name),
            ("X", "=%s.Width + 10" % nav_name),
            ("Y", "=%s.Height + 10" % header_name),
        ], variant="AutoLayout", children=[toolbar_block, table_block, footer_block])

    notification_block = _block(
        "cmp_%sList_Notification" % entity.plural, 6, "CanvasComponent",
        [
            ("Notifications", "=colNotifications"),
            ("OnCancel", "=RemoveIf(colNotifications, Created = ThisRecord.Created)"),
            ("Visible", "=!IsEmpty(colNotifications)"),
            ("Width", "=400"),
            ("X", "=Parent.Width - Self.Width - constStyle.Spacing.XL"),
            ("Y", "=%s.Height + constStyle.Spacing.M" % header_name),
        ], component_name="cmp_Notification")

    spinner_block = _block(
        "cmp_%sList_Spinner" % entity.plural, 6, "CanvasComponent",
        [("Visible", "=glBoolIsLoading")], component_name="cmp_Spinner")

    top_props = [
        ("Fill", "=constReactGray.RGBA"),
        ("LoadingSpinnerColor", "=constPrimaryColor.RGBA"),
        ("OnVisible",
         "=RemoveIf(colSorts, Table = %s);\n"
         "Collect(\n"
         "    colSorts,\n"
         "    {\n"
         "        Table: %s,\n"
         "        ID: %s,\n"
         "        SortOrder: \"asc\"\n"
         "    }\n"
         ");\n"
         "UpdateContext({locNavigation: false})"
         % (entity.enum_member, entity.enum_member, _quote(default_sort_field))),
    ]

    lines = ["Screens:", "  %s:" % entity.list_screen, "    Properties:"]
    for name, value in sorted(top_props):
        lines.extend(_render_prop_line("      ", name, value))
    lines.append("    Children:")
    for block in (header_block, nav_block, list_block, notification_block, spinner_block):
        lines.extend(block)
    return "\n".join(lines) + "\n"


# ---- form screen: per-field pieces ---------------------------------------

def _label_block(entity, field, item_indent):
    return _block(
        "lbl_%sForm_%sLabel" % (entity.entity, field.name), item_indent, "ModernText",
        [
            ("FontWeight", "=FontWeight.Semibold"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", "=%s" % _quote(field.label)),
        ])


def _boolean_form_input(entity, field, dirty_setter):
    if "ModernToggle" in CONTRACTS["controls"]:
        raise ContractError(
            "ModernToggle is now in references/control-contracts.yaml, but "
            "emit_screens.py's boolean-archetype branch was never updated to "
            "use it. This is a generator gap to fix deliberately, not a "
            "value to guess at — do not fall through to the ModernCombobox "
            "path silently.")
    loc_ref = "%s.%s" % (entity.loc_var, field.name)
    yes_no = 'Table({Value: "Yes"}, {Value: "No"})'
    return "ModernCombobox", [
        ("AccessibleLabel", "=%s" % _quote(field.label)),
        ("DefaultSelectedItems",
         '=Filter(%s, Value = If(%s, "Yes", "No"))' % (yes_no, loc_ref)),
        ("Height", "=constStyle.Combobox.Height.Medium"),
        ("ItemDisplayText", "=ThisItem.Value"),
        ("Items", "=%s" % yes_no),
        ("OnChange", dirty_setter),
        ("SelectMultiple", "=false"),
    ]


def _form_input_block(entity, field, item_indent):
    loc_ref = "%s.%s" % (entity.loc_var, field.name)
    dirty_setter = "=UpdateContext({locDirty: true})"
    label_text = "=%s" % _quote(field.label)

    if field.type in ("text", "longtext"):
        control_type = "ModernTextInput"
        props = [
            ("AccessibleLabel", label_text),
            ("Appearance", "=constStyle.Label.TextInput.Appearance"),
            ("Default", "=%s" % loc_ref),
            ("Height", "=constStyle.Label.TextInput.Height.%s"
             % ("MultiLine" if field.type == "longtext" else "SingleLine")),
            ("OnChange", dirty_setter),
        ]
        if field.type == "longtext":
            props.append(("Type", "=TextInputType.Multiline"))
    elif field.type == "number":
        control_type = "ModernTextInput"
        props = [
            ("AccessibleLabel", label_text),
            # ModernTextInput has no Format (that is the classic TextInput).
            # Numeric entry stays a text input: right-align via the token,
            # parse with Value() in funcSaveEntity.
            ("Align", "=constStyle.Label.NumberInput.AlignModern"),
            ("Appearance", "=constStyle.Label.TextInput.Appearance"),
            ("Default", "=Text(%s)" % loc_ref),
            ("Height", "=constStyle.Label.TextInput.Height.SingleLine"),
            ("OnChange", dirty_setter),
        ]
    elif field.type == "choice":
        control_type = "ModernCombobox"
        # DefaultSelectedItems: =Filter(<choices>, Value = loc<Entity>.<Field>)
        # is correct as-is for edit mode — it seeds the combobox from the
        # record being edited, unlike the list screen's filter comboboxes
        # (which seed empty via FirstN(..., 0)). ItemDisplayText was already
        # added by the live-compile fix (Phase 2); InputTextPlaceholder and
        # IsSearchable were not — a bare combobox otherwise shows the factory
        # "Find items" placeholder.
        props = [
            ("AccessibleLabel", label_text),
            ("DefaultSelectedItems",
             "=Filter(%s, Value = %s)" % (entity.choices_table(field), loc_ref)),
            ("Height", "=constStyle.Combobox.Height.Medium"),
            ("InputTextPlaceholder", label_text),
            ("IsSearchable", "=false"),
            ("ItemDisplayText", "=ThisItem.Value"),
            ("Items", "=%s" % entity.choices_table(field)),
            ("OnChange", dirty_setter),
            ("SelectMultiple", "=false"),
        ]
    elif field.type == "date":
        control_type = "ModernDatePicker"
        props = [
            ("AccessibleLabel", label_text),
            ("DefaultDate", "=%s" % loc_ref),
            # Leaf control in an auto-layout container (con_*Form_Card, a
            # Vertical layout): an explicit Height is mandatory or it
            # collapses to its control default (check_layout.py's Rule 3).
            # Same token its ModernTextInput/ModernCombobox siblings in this
            # same card use for a single-line field.
            ("Height", "=constStyle.Label.TextInput.Height.SingleLine"),
            ("OnChange", dirty_setter),
        ]
    elif field.type == "boolean":
        control_type, props = _boolean_form_input(entity, field, dirty_setter)
    else:
        raise ContractError("unhandled field archetype: %r" % field.type)

    return _block(entity.form_control(field), item_indent, control_type, props)


def _required_check(entity, field):
    ctrl = entity.form_control(field)
    if field.type == "choice" or field.type == "boolean":
        return "IsEmpty(%s.SelectedItems)" % ctrl
    if field.type == "date":
        return "IsBlank(%s.SelectedDate)" % ctrl
    return "IsBlank(%s.Text)" % ctrl


def _save_arg(entity, field):
    ctrl = entity.form_control(field)
    if field.type == "choice":
        return "First(%s.SelectedItems).Value" % ctrl
    if field.type == "boolean":
        return 'First(%s.SelectedItems).Value = "Yes"' % ctrl
    if field.type == "number":
        return "Value(%s.Text)" % ctrl
    if field.type == "date":
        return "%s.SelectedDate" % ctrl
    return "%s.Text" % ctrl


def _display_name_ref(entity):
    """The value shown in the form header's title (Ruling 20/I3).

    `cmp_Header.DisplayName` is `DataType: Text`. The previous emitter always
    used the FIRST GRID field, unconditionally — a type error the moment
    that field is a number or date, since neither unifies with `Text`
    without an explicit cast. Prefer the first text/longtext field (grid
    fields first, since that is what a reader expects the title to track;
    then any text/longtext field on the entity at all); only when the entity
    has NO text field anywhere does this fall back to the first grid field,
    wrapped in `Text(...)` so it still type-checks.
    """
    for f in entity.grid_fields:
        if f.type in ("text", "longtext"):
            return "%s.%s" % (entity.loc_var, f.name)
    for f in entity.fields:
        if f.type in ("text", "longtext"):
            return "%s.%s" % (entity.loc_var, f.name)
    fallback = entity.grid_fields[0] if entity.grid_fields else entity.fields[0]
    return "Text(%s.%s)" % (entity.loc_var, fallback.name)


def emit_form_screen(entity, model):
    """The form screen for `entity`: one label+input pair per field —
    INCLUDING grid-hidden ones, since `entity.form_fields` (unlike
    `entity.grid_fields`) is every field — a validation summary, Save/
    Cancel/Delete, a delete-confirmation dialog, and the standard chrome."""
    fields = entity.form_fields
    display_ref = _display_name_ref(entity)

    card_children = []
    for f in fields:
        card_children.append(_label_block(entity, f, 18))
        card_children.append(_form_input_block(entity, f, 18))
    # A fixed-height card scaled to field count — plain pixel literals are
    # fine here (check_tokens.py only restricts colour/font-size/radius
    # literals), a fixed Height is mandatory for a fixed child of an
    # auto-layout container.
    card_height = 100 + 70 * len(fields)
    card_block = _block(
        "con_%sForm_Card" % entity.entity, 12, "GroupContainer",
        [
            ("DropShadow", "=constStyle.Card.Shadow"),
            ("Fill", "=constStyle.Card.Fill"),
            ("FillPortions", "=0"),
            ("Height", "=%d" % card_height),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.M"),
            ("PaddingBottom", "=constStyle.Card.Padding"),
            ("PaddingLeft", "=constStyle.Card.Padding"),
            ("PaddingRight", "=constStyle.Card.Padding"),
            ("PaddingTop", "=constStyle.Card.Padding"),
            ("RadiusBottomLeft", "=constStyle.Card.Radius"),
            ("RadiusBottomRight", "=constStyle.Card.Radius"),
            ("RadiusTopLeft", "=constStyle.Card.Radius"),
            ("RadiusTopRight", "=constStyle.Card.Radius"),
        ], variant="AutoLayout", children=card_children)

    required = [f for f in fields if f.required]
    if required:
        rows = ["{Msg: If(%s, %s, \"\")}" % (_required_check(entity, f),
                                              _quote("%s is required" % f.label))
                for f in required]
    else:
        rows = ['{Msg: ""}']
    errors_text = (
        "=Concat(\n"
        "    Filter(\n"
        "        Table(\n"
        "            %s\n"
        "        ),\n"
        "        !IsBlank(Msg)\n"
        "    ),\n"
        "    Msg,\n"
        "    \" · \"\n"
        ")"
    ) % ",\n            ".join(rows)
    errors_block = _block(
        "lbl_%sForm_Errors" % entity.entity, 12, "ModernText",
        [
            ("Color", "=constLossTextColor.RGBA"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.Height.Medium"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", errors_text),
            ("Visible", "=!IsBlank(Self.Text)"),
        ])
    errors_ctrl = "lbl_%sForm_Errors" % entity.entity

    save_args = ["glSelectedKey"] + [_save_arg(entity, f) for f in fields]
    delete_btn = _block(
        "btn_%sForm_Delete" % entity.entity, 18, "Button",
        [
            ("AccessibleLabel", "=%s" % _quote("Delete this %s" % entity.entity.lower())),
            ("BasePaletteColor", "=constSecondaryColor.RGBA"),
            ("Height", "=constStyle.Button.Height.Medium"),
            ("OnSelect", "=UpdateContext({locConfirmDelete: true})"),
            ("Text", "=%s" % _quote("Delete")),
            ("Visible", "=!IsBlank(glSelectedKey)"),
        ])
    cancel_btn = _block(
        "btn_%sForm_Cancel" % entity.entity, 18, "Button",
        [
            ("AccessibleLabel", "=%s" % _quote("Discard changes and go back")),
            ("Height", "=constStyle.Button.Height.Medium"),
            ("OnSelect", "=funcGoBack()"),
            ("Text", "=%s" % _quote("Cancel")),
        ])
    save_btn = _block(
        "btn_%sForm_Save" % entity.entity, 18, "Button",
        [
            ("AccessibleLabel", "=%s" % _quote("Save %s" % entity.entity.lower())),
            ("Appearance", "='ButtonCanvas.Appearance'.Primary"),
            ("BasePaletteColor", "=constPrimaryColor.RGBA"),
            ("DisplayMode",
             "=If(\n"
             "    locDirty And IsBlank(%s.Text),\n"
             "    DisplayMode.Edit,\n"
             "    DisplayMode.Disabled\n"
             ")" % errors_ctrl),
            ("Height", "=constStyle.Button.Height.Medium"),
            ("OnSelect",
             "=funcStartLoading();\n"
             "%s(\n"
             "    %s\n"
             ");\n"
             "funcStopLoading();\n"
             "UpdateContext({locDirty: false});\n"
             "funcNotifySuccess(\"%s saved.\");\n"
             "funcGoBack()" % (entity.func_save, ",\n    ".join(save_args), entity.entity)),
            ("Text", "=%s" % _quote("Save")),
        ])
    actions_block = _block(
        "con_%sForm_Actions" % entity.entity, 12, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Button.Height.Medium"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.S"),
            ("LayoutJustifyContent", "=LayoutJustifyContent.End"),
        ], variant="AutoLayout", children=[delete_btn, cancel_btn, save_btn])

    body_block = _block(
        "con_%sForm_Body" % entity.entity, 6, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("Height", "=Parent.Height - cmp_%sForm_Header.Height" % entity.entity),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.M"),
            ("LayoutOverflowY", "=LayoutOverflow.Scroll"),
            # Baseline con_Form_Body: PaddingLeft/Right=20, PaddingTop/Bottom=15
            # literals. House style is tokens, not literals (check_tokens.py
            # would only flag colour/size/radius literals, not these — but
            # tokens are the rule anyway) — Spacing.L is the closest token to
            # the baseline's horizontal 20, Spacing.M to its vertical 15.
            ("PaddingBottom", "=constStyle.Spacing.M"),
            ("PaddingLeft", "=constStyle.Spacing.L"),
            ("PaddingRight", "=constStyle.Spacing.L"),
            ("PaddingTop", "=constStyle.Spacing.M"),
            # Baseline: Width=Parent.Width, Y=cmp_Form_Header.Height. Without
            # these the body has no Width (so it sits at its content's
            # natural width) and no Y (so it sits at 0 and covers the
            # header) — the live-render defect this task fixes.
            ("Width", "=Parent.Width"),
            ("Y", "=cmp_%sForm_Header.Height" % entity.entity),
        ], variant="AutoLayout", children=[card_block, errors_block, actions_block])

    header_name = "cmp_%sForm_Header" % entity.entity
    header_block = _block(
        header_name, 6, "CanvasComponent",
        [
            ("AllowBack", "=true"),
            ("AllowNavigation", "=false"),
            ("BackLabel", "=%s" % _quote("Back to the %s list" % entity.plural.lower())),
            ("DisplayName",
             '=If(IsBlank(glSelectedKey), "New %s", %s)'
             % (entity.entity, display_ref)),
            ("Height", "=constStyle.Header.Height"),
            ("IsLoading", "=glBoolIsLoading"),
            ("OnBack", "=funcGoBack()"),
            ("Width", "=Parent.Width"),
        ], component_name="cmp_Header")

    dialog_block = _block(
        "cmp_%sForm_Dialog" % entity.entity, 6, "CanvasComponent",
        [
            ("CancelLabel", "=%s" % _quote("Keep it")),
            ("Description", "=%s" % _quote(
                "This removes the %s permanently. There is no undo." % entity.entity.lower())),
            ("Height", "=Parent.Height"),
            ("OnCancel", "=UpdateContext({locConfirmDelete: false})"),
            ("OnSubmit",
             "=funcStartLoading();\n"
             "%s(glSelectedKey);\n"
             "funcStopLoading();\n"
             "UpdateContext({locConfirmDelete: false});\n"
             "funcNotifySuccess(\"%s deleted.\");\n"
             "funcGoBack()" % (entity.func_delete, entity.entity)),
            ("SubmitLabel", "=%s" % _quote("Delete")),
            ("Title", "=%s" % _quote("Delete this %s?" % entity.entity.lower())),
            ("Visible", "=locConfirmDelete"),
            ("Width", "=Parent.Width"),
            ("X", "=0"),
            ("Y", "=0"),
        ], component_name="cmp_Dialog")

    notification_block = _block(
        "cmp_%sForm_Notification" % entity.entity, 6, "CanvasComponent",
        [
            ("Notifications", "=colNotifications"),
            ("OnCancel", "=RemoveIf(colNotifications, Created = ThisRecord.Created)"),
            ("Visible", "=!IsEmpty(colNotifications)"),
            ("Width", "=400"),
            ("X", "=Parent.Width - Self.Width - constStyle.Spacing.XL"),
            ("Y", "=%s.Height + constStyle.Spacing.M" % header_name),
        ], component_name="cmp_Notification")

    spinner_block = _block(
        "cmp_%sForm_Spinner" % entity.entity, 6, "CanvasComponent",
        [("Visible", "=glBoolIsLoading")], component_name="cmp_Spinner")

    top_props = [
        ("Fill", "=constReactGray.RGBA"),
        ("LoadingSpinnerColor", "=constPrimaryColor.RGBA"),
        ("OnVisible",
         "=UpdateContext(\n"
         "    {\n"
         "        %s: LookUp(%s, Key = glSelectedKey),\n"
         "        locDirty: false,\n"
         "        locConfirmDelete: false\n"
         "    }\n"
         ")" % (entity.loc_var, entity.scope_formula)),
    ]

    lines = ["Screens:", "  %s:" % entity.form_screen, "    Properties:"]
    for name, value in sorted(top_props):
        lines.extend(_render_prop_line("      ", name, value))
    lines.append("    Children:")
    for block in (header_block, body_block, dialog_block, notification_block, spinner_block):
        lines.extend(block)
    return "\n".join(lines) + "\n"
