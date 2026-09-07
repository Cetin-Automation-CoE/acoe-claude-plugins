#!/usr/bin/env python3
"""The multi-entity data layer for App.Formulas, dependency-ordered.

WHY THIS EXISTS: the studio's document-server binder cannot forward-reference
one named formula from another. When it fails on a single unresolved name it
drops the ENTIRE `Formulas` blob — every named formula, UDF and constant in
the app stops existing, and every screen reports "unknown name" with nothing
pointing at the cause. There is no offline compile for Canvas Apps, so
nothing catches this before a push.

With one entity a hand-written order is easy to get right by inspection. With
N entities it stops being trivial, so this module never emits blocks in a
hand-maintained sequence: every block records what it `defines` and what
names it textually `uses`, and `topo_sort` (Kahn's algorithm) computes a
declaration order from those edges. A cycle raises `OrderError` naming the
participants rather than silently emitting a body that would die in studio.

Identifiers in generated output are entity-derived (colAssets, funcSaveAsset,
constAssetStatusChoices, …) via `model.py` — never the templates' generic
placeholders (colItems, funcSaveItem, locItem), which stay in the templates
as a pattern to read, not finished domain code.

Scope: this module owns the layers that are driven by the entity model —
enums (`enumScreenType`, `enumEntity`), one choices table per choice field,
the per-entity data-access layer (scope formula, load/save/delete UDFs), and
the `constScreens` registry. Scalar constants, pure helper UDFs and globals
(layers 3-5 in `templates/App.pa.yaml`) are entity-agnostic and are not part
of this module's contract — see `templates/design-tokens.pa.yaml`, which
`scripts/new_app.py` already inlines into `App.pa.yaml` separately.
"""
from __future__ import annotations

import collections
import re

import emit_mock

Block = collections.namedtuple("Block", "name defines uses text")


class OrderError(Exception):
    """Raised when named formulas form a cycle no linear order can satisfy.

    Never caught internally: emitting a body anyway would mean shipping a
    Formulas blob the studio binder is guaranteed to drop, with no error
    naming the cause. Raising here, at generation time, is the whole point.
    """


_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_PF_TYPE = {
    "text": "Text",
    "longtext": "Text",
    "choice": "Text",
    "number": "Number",
    "boolean": "Boolean",
    "date": "DateTime",
}

_DATA_BEGIN_BANNER = (
    "      // ============================================================\n"
    "      // ===== DATA ACCESS LAYER — BEGIN ============================\n"
    "      // ============================================================"
)
_DATA_END_BANNER = (
    "      // ============================================================\n"
    "      // ===== DATA ACCESS LAYER — END ==============================\n"
    "      // ============================================================"
)

_LAYER_HEADER = {
    "enums": "      // ############ 1. ENUMS AND VOCABULARIES ############",
    "choices": "      // ############ 2. CHOICES TABLES ############\n"
               "      // Every dropdown, filter and validation reads these. A value\n"
               "      // that exists in the UI but not here is a value nothing can\n"
               "      // validate.",
    "data": "      // ############ 6. DATA ACCESS LAYER ############\n" + _DATA_BEGIN_BANNER,
    "registry": "      // ############ 7. REGISTRIES AND NAVIGATION ############\n"
                "      // MUST come last: these read layer-6 formulas and the enum\n"
                "      // vocab above. Adding a screen is a ROW here, not a new\n"
                "      // Switch arm elsewhere.",
}


def _quote(text):
    """Render a Python string as a Power Fx text literal, doubling inner quotes."""
    return '"' + text.replace('"', '""') + '"'


def _param_name(field):
    """The UDF parameter name for `field`.

    Always `p`-prefixed. `UpdateIf`/`Patch` open the target collection's row
    scope over both the condition and the change record, so a parameter
    named `tag` sits one case-fold from the column `Tag` — `{Tag: tag}` can
    then resolve to `Tag: Tag`, a save that writes nothing and reports
    success. The `p` prefix makes that collision impossible.
    """
    return "p" + field.name


def _param_sig(field):
    return "%s: %s" % (_param_name(field), _PF_TYPE[field.type])


# ---- block builders: each returns (layer, name, text) -----------------------

def _enum_screen_type_spec():
    text = (
        "      // ---- enums: screen kinds -------------------------------\n"
        "      // Keys, not display text: a typo in an enum reference fails\n"
        "      // to compile, while a typo in a bare string silently matches\n"
        "      // nothing. Screens compare against this by member, below.\n"
        "      enumScreenType = {\n"
        "          List: \"list\",\n"
        "          Form: \"form\"\n"
        "      };"
    )
    return ("enums", "enumScreenType", text)


def _enum_entity_spec(model):
    members = []
    for i, entity in enumerate(model.entities):
        comma = "," if i < len(model.entities) - 1 else ""
        members.append("          %s: %s%s" % (entity.plural, _quote(entity.plural.lower()), comma))
    text = (
        "      // ---- enums: keys, not display text ---------------------\n"
        "      // One member per entity below. Screens compare against it by\n"
        "      // member, never a bare string.\n"
        "      enumEntity = {\n"
        + "\n".join(members) + "\n"
        "      };"
    )
    return ("enums", "enumEntity", text)


def _choices_spec(entity, field):
    name = entity.choices_table(field)
    rows = []
    for i, value in enumerate(field.vocab):
        comma = "," if i < len(field.vocab) - 1 else ""
        rows.append("          {Value: %s}%s" % (_quote(value), comma))
    text = (
        "      // ---- vocabulary: %s.%s -----------------------------\n"
        "      %s = Table(\n"
        + "\n".join(rows) + "\n"
        "      );"
    ) % (entity.entity, field.name, name)
    return ("choices", name, text)


def _scope_spec(entity):
    name = entity.scope_formula
    text = (
        "      // ---- scope: one base for grid, filters and counters ----\n"
        "      // Defining this once is what keeps a gallery, its filter\n"
        "      // chips and its \"N of M\" counter from silently disagreeing.\n"
        "      // Generic base below — extend the condition as scope filters\n"
        "      // (owner, region, …) are added.\n"
        "      %s =\n"
        "          Filter(\n"
        "              %s,\n"
        "              true\n"
        "          );"
    ) % (name, entity.collection)
    return ("data", name, text)


def _load_spec(entity, rows, today):
    name = entity.func_load
    mock = emit_mock.mock_table_literal(entity, rows, today, indent=14)

    switch_lines = [
        "          // SWITCH DAY: delete the mock above, uncomment below.",
        "          // Choice/lookup unwrapping happens HERE and nowhere else.",
        "          // ClearCollect(",
        "          //     %s," % entity.collection,
        "          //     ForAll(",
        "          //         My%sList As r," % entity.plural,
        "          //         {",
        "          //             Key: r.Suffix & \"|\" & r.ID,",
    ]
    field_lines = []
    for f in entity.fields:
        if f.type == "choice":
            field_lines.append("          //             %s: r.%s.Value," % (f.name, f.name))
        else:
            field_lines.append("          //             %s: r.%s," % (f.name, f.name))
    if field_lines:
        field_lines[-1] = field_lines[-1].rstrip(",")
    switch_lines.extend(field_lines)
    switch_lines += [
        "          //         }",
        "          //     )",
        "          // );",
    ]

    text = (
        "      // ---- read: %s -------------------------------------\n"
        "      %s(): Void =\n"
        "      {\n"
        "          // MOCK — one fully typed row per shape. Power Fx infers\n"
        "          // the collection schema from this literal; an untyped or\n"
        "          // empty seed makes every named formula over it fail with\n"
        "          // \"no type found\".\n"
        "          ClearCollect(\n"
        "              %s,\n"
        "%s\n"
        "          );\n"
        "          // NOTE: no Clear() here. The seeded rows above are the\n"
        "          // mock data and must survive: clearing them is what made\n"
        "          // every scaffolded app render an empty grid. Seed-then-\n"
        "          // clear is correct ONLY for the framework collections\n"
        "          // (colFilters, colSorts, colBack, colNotifications),\n"
        "          // where a typed schema with no rows is genuinely wanted.\n"
        "%s\n"
        "      };"
    ) % (entity.plural, name, entity.collection, mock, "\n".join(switch_lines))
    return ("data", name, text)


def _save_spec(entity):
    name = entity.func_save
    key_param = "pKey: Text"
    field_params = [key_param] + [_param_sig(f) for f in entity.fields]
    sig = ", ".join(field_params)

    create_fields = ["Key: pKey"] + ["%s: %s" % (f.name, _param_name(f)) for f in entity.fields]
    update_fields = ["%s: %s" % (f.name, _param_name(f)) for f in entity.fields]

    text = (
        "      // ---- write: %s ------------------------------------\n"
        "      // Takes scalars, not a record: record params on UDFs are\n"
        "      // unreliable. Every param is p-prefixed so it cannot shadow\n"
        "      // a column of the same name inside UpdateIf's row scope.\n"
        "      %s(%s): Void =\n"
        "      {\n"
        "          If(\n"
        "              IsBlank(LookUp(%s, Key = pKey)),\n"
        "              Collect(\n"
        "                  %s,\n"
        "                  {%s}\n"
        "              ),\n"
        "              UpdateIf(\n"
        "                  %s,\n"
        "                  Key = pKey,\n"
        "                  {%s}\n"
        "              )\n"
        "          );\n"
        "          // SWITCH DAY: Patch(%s, LookUp(%s, ID = pKey), {…});\n"
        "      };"
    ) % (
        entity.entity, name, sig,
        entity.collection,
        entity.collection, ", ".join(create_fields),
        entity.collection, ", ".join(update_fields),
        entity.collection, entity.collection,
    )
    return ("data", name, text)


def _delete_spec(entity):
    name = entity.func_delete
    text = (
        "      // ---- delete: %s -----------------------------------\n"
        "      %s(pKey: Text): Void =\n"
        "      {\n"
        "          RemoveIf(%s, Key = pKey);\n"
        "      };"
    ) % (entity.entity, name, entity.collection)
    return ("data", name, text)


def _entity_data_layer_specs(entity, rows, today):
    return [
        _scope_spec(entity),
        _load_spec(entity, rows, today),
        _save_spec(entity),
        _delete_spec(entity),
    ]


def _registry_spec(model):
    rows = []
    for entity in model.entities:
        rows.append(
            "          {\n"
            "              Screen: %s,\n"
            "              DisplayName: %s,\n"
            "              Icon: %s,\n"
            "              Entity: enumEntity.%s,\n"
            "              Type: enumScreenType.List,\n"
            "              Group: %s,\n"
            "              BackLabel: %s\n"
            "          }" % (
                entity.list_screen, _quote(entity.plural), _quote(entity.icon),
                entity.plural, _quote(entity.group), _quote(entity.plural + " list"),
            )
        )
        rows.append(
            "          {\n"
            "              Screen: %s,\n"
            "              DisplayName: %s,\n"
            "              Icon: %s,\n"
            "              Entity: enumEntity.%s,\n"
            "              Type: enumScreenType.Form,\n"
            "              Group: \"\",\n"
            "              BackLabel: %s\n"
            "          }" % (
                entity.form_screen, _quote(entity.entity), _quote(entity.icon),
                entity.plural, _quote(entity.entity),
            )
        )
    text = (
        "      // ---- registries: one row per screen, not a new Switch --\n"
        "      constScreens = [\n"
        + ",\n".join(rows) + "\n"
        "      ];"
    )
    return ("registry", "constScreens", text)


# ---- assembly ----------------------------------------------------------

def _all_specs(model, rows, today):
    """The ordered [(layer, name, text), ...] for every block `emit_all`
    assembles. This insertion order is the tie-break `topo_sort` falls back
    to when two blocks have no dependency relationship — it is NOT itself
    the emitted order; that is computed by `topo_sort` from real `uses`
    edges detected in each block's text.
    """
    specs = [_enum_screen_type_spec(), _enum_entity_spec(model)]
    for entity in model.entities:
        for field in entity.choice_fields:
            specs.append(_choices_spec(entity, field))
    for entity in model.entities:
        specs.extend(_entity_data_layer_specs(entity, rows, today))
    specs.append(_registry_spec(model))
    return specs


def _finalize(specs):
    """Turn [(layer, name, text), ...] into (blocks, layer_of).

    `uses` is computed by scanning each block's text for whole-word tokens
    that match another block's defined name — never hand-listed. That is
    what makes the dependency graph, and therefore the order `topo_sort`
    derives from it, genuinely computed rather than asserted.
    """
    names = frozenset(name for _, name, _ in specs)
    blocks = []
    layer_of = {}
    for layer, name, text in specs:
        tokens = frozenset(_TOKEN_RE.findall(text))
        uses = (tokens & names) - {name}
        blocks.append(Block(name, frozenset([name]), uses, text))
        layer_of[name] = layer
    return blocks, layer_of


def topo_sort(blocks):
    """Kahn's algorithm over `defines` -> `uses` edges.

    Deterministic: ties among simultaneously-ready blocks are broken by a
    stable key — the block's position in the input `blocks` list (its
    "layer index"), then its name — so two runs over the same input produce
    byte-identical output.

    Raises `OrderError`, naming the participants, if the blocks contain a
    cycle. Never emits a partial or best-effort order: a body that would
    forward-reference is worse than no body at all, because the studio
    binder drops the entire Formulas blob with no error naming the cause.
    """
    blocks = list(blocks)
    order_index = {b.name: i for i, b in enumerate(blocks)}
    by_name = {b.name: b for b in blocks}

    producer_of = {}
    for b in blocks:
        for defined in b.defines:
            producer_of[defined] = b.name

    dependents = collections.defaultdict(set)
    indegree = {}
    for b in blocks:
        deps = set()
        for used in b.uses:
            producer = producer_of.get(used)
            if producer is not None and producer != b.name:
                deps.add(producer)
        indegree[b.name] = len(deps)
        for dep in deps:
            dependents[dep].add(b.name)

    ready = [name for name, deg in indegree.items() if deg == 0]
    result = []
    while ready:
        ready.sort(key=lambda n: (order_index[n], n))
        name = ready.pop(0)
        result.append(by_name[name])
        for dependent in sorted(dependents.get(name, ())):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)

    if len(result) != len(blocks):
        remaining = sorted(name for name, deg in indegree.items() if deg > 0)
        raise OrderError(
            "cycle detected — no forward-reference-free order exists among: %s"
            % ", ".join(remaining))
    return result


def _render(ordered, layer_of):
    out = []
    prev_layer = None
    for b in ordered:
        layer = layer_of[b.name]
        if layer != prev_layer:
            if prev_layer == "data":
                out.append(_DATA_END_BANNER)
            out.append(_LAYER_HEADER[layer])
        out.append(b.text)
        prev_layer = layer
    if prev_layer == "data":
        out.append(_DATA_END_BANNER)
    return "\n\n".join(out)


def emit_enum_entity(model):
    """The `enumEntity` block: one member per entity, keyed by `entity.plural`."""
    return _enum_entity_spec(model)[2]


def emit_choices_tables(model):
    """One `constXChoices` table per choice field per entity, entity- and
    field-derived (never a generic name), topologically sorted (they carry
    no dependencies on each other, so this also fixes a stable order)."""
    specs = [_choices_spec(e, f) for e in model.entities for f in e.choice_fields]
    blocks, _ = _finalize(specs)
    ordered = topo_sort(blocks)
    return "\n\n".join(b.text for b in ordered)


def emit_data_layer(model, rows, today):
    """The per-entity data-access layer: scope formula, then load, save and
    delete UDFs, for every entity in `model`, wrapped in the DATA ACCESS
    LAYER banners `check_data_layer.py` looks for.

    `rows` is the per-entity ROW COUNT (an int) — how many mock rows
    `emit_mock` generates for each entity — not a collection of row objects.
    `today` anchors the mock data's dates; it is never read from the real
    clock, so the same (model, rows, today) always produces the same text.
    """
    specs = []
    for entity in model.entities:
        specs.extend(_entity_data_layer_specs(entity, rows, today))
    blocks, _ = _finalize(specs)
    ordered = topo_sort(blocks)
    body = "\n\n".join(b.text for b in ordered)
    return "\n\n".join([_DATA_BEGIN_BANNER, body, _DATA_END_BANNER])


def emit_screens_registry(model):
    """The `constScreens` registry: two rows per entity (list screen, form
    screen), entity-derived screen names — never the generic ListScreen/
    FormScreen pair the templates use as a pattern."""
    return _registry_spec(model)[2]


def emit_all(model, rows, today):
    """The assembled, dependency-ordered Formulas body for every entity in
    `model`: enums, choices tables, the per-entity data-access layer, and
    the `constScreens` registry — in the order `topo_sort` computes from
    each block's real `defines`/`uses` edges, never a hand-maintained
    sequence.

    `rows` is the per-entity ROW COUNT (an int), passed straight through to
    `emit_mock.mock_table_literal` for every entity — not a collection of
    row objects. `today` anchors the mock data's dates and must be an
    explicit `datetime.date` so two calls with the same arguments always
    produce byte-identical output.
    """
    specs = _all_specs(model, rows, today)
    blocks, layer_of = _finalize(specs)
    ordered = topo_sort(blocks)
    return _render(ordered, layer_of)
