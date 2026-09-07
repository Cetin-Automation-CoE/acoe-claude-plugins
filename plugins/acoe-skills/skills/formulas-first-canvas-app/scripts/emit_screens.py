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

CONTRACT-AWARE BY CONSTRUCTION (Phase 1's whole point): every property this
module writes is checked against `references/control-contracts.yaml` — for a
plain control (ModernText, ModernTextInput, ModernCombobox, ModernDatePicker,
Button, Gallery) via `_check_control_prop`, for a CanvasComponent instance
(cmp_Header, cmp_FilterButton, ...) against that component's own declared
CustomProperties via `_check_component_prop` — BEFORE the property line is
ever written. An unknown property raises `ContractError` at generation time,
never at push time. `check_control_props.py` reads the exact same contract
file, so `tests/test_emit_screens.py`'s
`TestGeneratedOutputPassesTheContractGuard` passes because the emitter is
correct, not because output was tuned until the guard went quiet.

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
      real one).

    This is not cosmetic: `OnChange: =UpdateContext({locDirty: true})`
    rendered inline breaks the file. `templates/*.pa.yaml` always wraps this
    shape in `|-` for exactly this reason, even for a single logical line.
    """
    return "\n" in value or ":" in value


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


def _width_pair(field):
    """FillPortions for a flex column, an explicit pixel Width otherwise.

    Carried finding from Task 1: `field.grid_width` can also be the string
    "hidden" — but this is only ever called with a field drawn from
    `entity.grid_fields`, which already excludes hidden fields, so "hidden"
    can never reach here. The assert makes that invariant loud instead of
    producing `Width: =hidden`.
    """
    assert field.grid_width != "hidden", (
        "_width_pair called on a grid-hidden field %r — read widths off "
        "entity.grid_fields, never entity.form_fields" % field.name)
    if field.grid_width == "flex":
        return [("FillPortions", "=1")]
    return [("Width", "=%d" % field.grid_width)]


_HEADER_DATATYPE = {
    "text": "string", "longtext": "string", "choice": "string",
    "number": "number", "date": "date", "boolean": "boolean",
}


# ---- list screen: per-field pieces ---------------------------------------

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
        ("Title", "=%s" % _quote(field.name)),
    ]
    if field.type == "choice":
        props.append(("Choices", "=%s" % entity.choices_table(field)))
    if field.type == "number":
        # Component inputs take STRINGS: cmp_FilterButton.Align is
        # DataType: Text, never the Align enum.
        props.append(("Align", "=%s" % _quote("Right")))
    props.extend(_width_pair(field))
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
    props.extend(_width_pair(field))
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
    """
    if not filter_ctrls:
        return "true"
    parts = []
    for field_name, ctrl in filter_ctrls.items():
        parts.append("IsEmpty(%s.SelectedItems) Or %s in %s.SelectedItems.Value"
                      % (ctrl, field_name, ctrl))
    return " Or\n    ".join(parts)


def _footer_block(entity, item_indent):
    """The footer aggregate strip (Ruling 12): a filtered/total count that
    reads the SAME scope formula the gallery and filter chips read — the
    whole point of `entity.scope_formula` existing is that this count cannot
    silently disagree with what the grid shows — plus one `Sum()` total per
    `money: true` field, formatted through `funcAsCurrency` so currency
    formatting stays owned by one function.

    A fixed-height, `FillPortions: =0` sibling of the gallery (which keeps
    `FillPortions: =1`): the same leaf-control-collapse rule that requires
    the gallery's own `FillPortions` applies here too.
    """
    count_text = ('="Showing " & CountRows(%s) & " of " & CountRows(%s)'
                  % (entity.scope_formula, entity.collection))
    cells = [_block(
        "lbl_%sList_Count" % entity.plural, item_indent + 6, "ModernText",
        [
            ("Color", "=constStyle.BasicStyle.FontColor"),
            ("FillPortions", "=0"),
            ("Size", "=constStyle.BasicStyle.FontSize.Small"),
            ("Text", count_text),
        ])]
    for f in entity.fields:
        if f.type != "number" or not f.money:
            continue
        total_text = ('="%s: " & funcAsCurrency(Sum(%s, %s))'
                      % (f.label, entity.scope_formula, f.name))
        cells.append(_block(
            "lbl_%sList_%sTotal" % (entity.plural, f.name), item_indent + 6, "ModernText",
            [
                ("Color", "=constStyle.BasicStyle.FontColor"),
                ("FillPortions", "=0"),
                ("Size", "=constStyle.BasicStyle.FontSize.Small"),
                ("Text", total_text),
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
    navigation, command bar, notifications, spinner)."""
    search_ctrl = "txt_%sList_Search" % entity.plural
    grid_fields = entity.grid_fields
    default_sort_field = grid_fields[0].name if grid_fields else entity.fields[0].name

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
            ("TabIndex", "=0"),
            ("Text", "=%s" % _quote("Open")),
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
        "    Filter(\n"
        "        %s,\n"
        "        %s,\n"
        "        %s\n"
        "    ),\n"
        "    // WARNING: this string column name is NEVER validated by the\n"
        "    // compiler. check_collection_columns.py is what catches a typo.\n"
        "    LookUp(colSorts, Table = %s).ID,\n"
        "    If(\n"
        "        LookUp(colSorts, Table = %s).SortOrder = \"asc\",\n"
        "        SortOrder.Ascending,\n"
        "        SortOrder.Descending\n"
        "    )\n"
        ")"
    ) % (entity.scope_formula, _filter_clause(entity, filter_ctrls),
         _search_clause(entity, search_ctrl), entity.enum_member, entity.enum_member)

    gallery_block = _block(
        entity.gallery, 18, "Gallery",
        [
            ("AccessibleLabel", "=%s" % _quote("%s table" % entity.plural)),
            ("BorderColor", "=constTransparent.RGBA"),
            ("FillPortions", "=1"),
            ("Items", items_formula),
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

    footer_block = _footer_block(entity, 18)

    # ---- toolbar: search box, one filter combobox per choice filter field,
    # command bar ------------------------------------------------------------
    toolbar_children = [_block(
        search_ctrl, 24, "ModernTextInput",
        [
            ("AccessibleLabel", "=%s" % _quote("Search %s" % entity.plural.lower())),
            ("Appearance", "=constStyle.Label.TextInput.Appearance"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.TextInput.Height.SingleLine"),
            ("Placeholder", "=%s" % _quote("Search")),
            ("TabIndex", "=0"),
            ("Width", "=280"),
        ])]
    for f in entity.filter_fields:
        if f.type != "choice":
            continue
        ctrl = filter_ctrls[f.name]
        toolbar_children.append(_block(
            ctrl, 24, "ModernCombobox",
            [
                ("AccessibleLabel", "=%s" % _quote("Filter by %s" % f.name)),
                ("FillPortions", "=0"),
                ("Height", "=constStyle.Combobox.Height.Medium"),
                ("Items", "=%s" % entity.choices_table(f)),
                ("SelectMultiple", "=true"),
                ("TabIndex", "=0"),
                ("Width", "=200"),
            ]))
    toolbar_children.append(_block(
        "cmp_%sList_Commands" % entity.plural, 24, "CanvasComponent",
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
        "con_%sList_Toolbar" % entity.plural, 18, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.Label.Height.Medium"),
            ("LayoutAlignItems", "=LayoutAlignItems.Center"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.S"),
        ], variant="AutoLayout", children=toolbar_children)

    headers_block = _block(
        "con_%sList_Headers" % entity.plural, 18, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=0"),
            ("Height", "=constStyle.List.HeaderHeight"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("LayoutGap", "=constStyle.Spacing.S"),
        ], variant="AutoLayout",
        children=[[l for f in grid_fields for l in _header_block(entity, f, 24)]])

    body_block = _block(
        "con_%sList_Body" % entity.plural, 12, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("FillPortions", "=1"),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Vertical"),
            ("LayoutGap", "=constStyle.Spacing.M"),
            ("PaddingBottom", "=constStyle.Spacing.L"),
            ("PaddingLeft", "=constStyle.Spacing.XL"),
            ("PaddingRight", "=constStyle.Spacing.XL"),
            ("PaddingTop", "=constStyle.Spacing.L"),
        ], variant="AutoLayout",
        children=[toolbar_block, headers_block, gallery_block, empty_block, footer_block])

    nav_block = _block(
        "cmp_%sList_Navigation" % entity.plural, 12, "CanvasComponent",
        [
            ("FillPortions", "=0"),
            ("Height", "=Parent.Height"),
            ("Navigation", "=locNavigation"),
            ("OnClose", "=UpdateContext({locNavigation: false})"),
        ], component_name="cmp_Navigation")

    header_name = "cmp_%sList_Header" % entity.plural
    main_block = _block(
        "con_%sList_Main" % entity.plural, 6, "GroupContainer",
        [
            ("BorderStyle", "=BorderStyle.None"),
            ("Height", "=Parent.Height - %s.Height" % header_name),
            ("LayoutAlignItems", "=LayoutAlignItems.Stretch"),
            ("LayoutDirection", "=LayoutDirection.Horizontal"),
            ("Width", "=Parent.Width"),
            ("Y", "=%s.Height" % header_name),
        ], variant="AutoLayout", children=[nav_block, body_block])

    header_block = _block(
        header_name, 6, "CanvasComponent",
        [
            ("AllowNavigation", "=true"),
            ("CanRefresh", "=true"),
            ("DisplayName", "=%s" % _quote(entity.plural)),
            ("Height", "=constStyle.Header.Height"),
            ("IsLoading", "=glBoolIsLoading"),
            ("NotificationCount", "=CountRows(colNotifications)"),
            ("OnNavigate", "=UpdateContext({locNavigation: !locNavigation})"),
            ("OnSelectRefresh", "=funcStartLoading();\n"
                                "%s();\n"
                                "funcStopLoading();\n"
                                "funcNotifySuccess(\"Data reloaded.\")" % entity.func_load),
            ("Width", "=Parent.Width"),
        ], component_name="cmp_Header")

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
    for block in (header_block, main_block, notification_block, spinner_block):
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
        ("Items", "=%s" % yes_no),
        ("OnChange", dirty_setter),
        ("SelectMultiple", "=false"),
        ("TabIndex", "=0"),
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
            ("TabIndex", "=0"),
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
            ("TabIndex", "=0"),
        ]
    elif field.type == "choice":
        control_type = "ModernCombobox"
        props = [
            ("AccessibleLabel", label_text),
            ("DefaultSelectedItems",
             "=Filter(%s, Value = %s)" % (entity.choices_table(field), loc_ref)),
            ("Height", "=constStyle.Combobox.Height.Medium"),
            ("Items", "=%s" % entity.choices_table(field)),
            ("OnChange", dirty_setter),
            ("SelectMultiple", "=false"),
            ("TabIndex", "=0"),
        ]
    elif field.type == "date":
        control_type = "ModernDatePicker"
        props = [
            ("AccessibleLabel", label_text),
            ("DefaultDate", "=%s" % loc_ref),
            ("OnChange", dirty_setter),
            ("TabIndex", "=0"),
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


def emit_form_screen(entity, model):
    """The form screen for `entity`: one label+input pair per field —
    INCLUDING grid-hidden ones, since `entity.form_fields` (unlike
    `entity.grid_fields`) is every field — a validation summary, Save/
    Cancel/Delete, a delete-confirmation dialog, and the standard chrome."""
    fields = entity.form_fields
    display_field = entity.grid_fields[0].name if entity.grid_fields else fields[0].name

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
            ("TabIndex", "=0"),
            ("Text", "=%s" % _quote("Delete")),
            ("Visible", "=!IsBlank(glSelectedKey)"),
        ])
    cancel_btn = _block(
        "btn_%sForm_Cancel" % entity.entity, 18, "Button",
        [
            ("AccessibleLabel", "=%s" % _quote("Discard changes and go back")),
            ("Height", "=constStyle.Button.Height.Medium"),
            ("OnSelect", "=funcGoBack()"),
            ("TabIndex", "=0"),
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
            ("TabIndex", "=0"),
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
            ("PaddingBottom", "=constStyle.Spacing.L"),
            ("PaddingLeft", "=constStyle.Spacing.XL"),
            ("PaddingRight", "=constStyle.Spacing.XL"),
            ("PaddingTop", "=constStyle.Spacing.L"),
        ], variant="AutoLayout", children=[card_block, errors_block, actions_block])

    header_name = "cmp_%sForm_Header" % entity.entity
    header_block = _block(
        header_name, 6, "CanvasComponent",
        [
            ("AllowBack", "=true"),
            ("AllowNavigation", "=false"),
            ("BackLabel", "=%s" % _quote("Back to the %s list" % entity.plural.lower())),
            ("DisplayName",
             '=If(IsBlank(glSelectedKey), "New %s", %s.%s)'
             % (entity.entity, entity.loc_var, display_field)),
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
