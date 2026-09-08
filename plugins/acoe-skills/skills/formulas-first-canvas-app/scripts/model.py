#!/usr/bin/env python3
"""The data model that drives generation.

A model.yaml is the app's SPEC — commit it beside the source tree. The agent
writes it (from what the user pasted, or inferred from a domain sentence); this
module validates it and derives every name the emitters use, so no two emitters
can disagree about what a collection is called.

Identifiers in GENERATED output are entity-derived (colAssets, funcSaveAsset).
The skill's own templates stay generic (colItems, funcSaveItem) — they are a
pattern to read, not finished domain code.
"""
from __future__ import annotations

import pathlib
import re

import yaml

ARCHETYPES = ("text", "longtext", "choice", "number", "date", "boolean")
SEMANTICS = ("semafor", "due", "none")
FILTER_KINDS = (True, False, "chips")
MAX_GRID_COLUMNS = 7
KEY_COLUMN = "Key"
RESERVED = {KEY_COLUMN, "IsSelected"}
# Power Fx names a field would shadow inside every control formula that
# references the row it came from (ThisItem.Self, locX.Value, ...). A
# SharePoint column literally named "Value" is common — catch it here, at
# generation time, rather than as a baffling compile error later.
RESERVED_POWERFX = {"Self", "Parent", "ThisItem", "Value", "Text"}
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


class ModelError(Exception):
    """A model problem the user can act on. Never raised for internal bugs."""


class Field(object):
    def __init__(self, spec, entity_name):
        if not isinstance(spec, dict):
            raise ModelError("entity %r: each field must be a mapping, got %r"
                             % (entity_name, spec))
        self.name = str(spec.get("name", "")).strip()
        if not IDENT.match(self.name):
            raise ModelError(
                "entity %r: field name %r is not a valid Power Fx identifier — "
                "use letters and digits only, starting with a letter (e.g. TagNumber)"
                % (entity_name, self.name))
        if self.name in RESERVED:
            raise ModelError(
                "entity %r: field name %r is reserved — the generator adds it as the "
                "key column. Rename the field." % (entity_name, self.name))
        if self.name in RESERVED_POWERFX:
            raise ModelError(
                "entity %r: field name %r is a Power Fx reserved word — it would "
                "shadow the built-in %r inside every control formula that reads this "
                "row (e.g. ThisItem.%s, Self.%s). Rename the field."
                % (entity_name, self.name, self.name, self.name, self.name))
        self.type = str(spec.get("type", "text")).strip()
        if self.type not in ARCHETYPES:
            raise ModelError("entity %r, field %r: unknown type %r — valid types are: %s"
                             % (entity_name, self.name, self.type, ", ".join(ARCHETYPES)))
        self.role = spec.get("role")
        if self.role not in (None, "title", "status"):
            raise ModelError(
                "entity %r, field %r: role %r is not valid — set it to 'title', "
                "'status', or remove the key" % (entity_name, self.name, self.role))
        if self.role == "status" and self.type != "choice":
            raise ModelError(
                "entity %r, field %r: role: status requires type: choice, got "
                "type: %r — change the field's type to choice or remove role: status"
                % (entity_name, self.name, self.type))
        if self.role == "title" and self.type not in ("text", "longtext"):
            raise ModelError(
                "entity %r, field %r: role: title requires type: text or longtext, "
                "got type: %r — change the field's type or remove role: title"
                % (entity_name, self.name, self.type))
        self.required = bool(spec.get("required", False))
        self.search = bool(spec.get("search", False))
        self.filter = spec.get("filter", False)
        if self.filter not in FILTER_KINDS:
            raise ModelError("entity %r, field %r: filter must be true, false or 'chips'"
                             % (entity_name, self.name))
        self.money = bool(spec.get("money", False))
        self.currency = spec.get("currency", "EUR")
        self.min = spec.get("min")
        self.max = spec.get("max")
        self.semantics = str(spec.get("semantics", "none"))
        if self.semantics not in SEMANTICS:
            raise ModelError("entity %r, field %r: semantics must be one of: %s"
                             % (entity_name, self.name, ", ".join(SEMANTICS)))
        self.vocab = list(spec.get("vocab") or [])
        if self.type == "choice" and not self.vocab:
            raise ModelError(
                "entity %r, field %r: a choice field needs a vocab list — without one "
                "the generator cannot build its dropdown or its mock rows"
                % (entity_name, self.name))
        self.samples = list(spec.get("samples") or [])
        self.label = str(spec.get("label") or self.name.upper())
        raw_grid = spec.get("grid", "flex")
        self.grid_hidden = (raw_grid == "hidden")
        if raw_grid in ("flex", "hidden"):
            self.grid_width = raw_grid
        else:
            try:
                self.grid_width = int(raw_grid)
            except (TypeError, ValueError):
                raise ModelError(
                    "entity %r, field %r: grid must be 'flex', 'hidden' or an integer "
                    "pixel width, got %r" % (entity_name, self.name, raw_grid))

    @property
    def in_grid(self):
        return not self.grid_hidden

    def __repr__(self):
        return "<Field %s:%s>" % (self.name, self.type)


class Entity(object):
    def __init__(self, spec):
        if not isinstance(spec, dict):
            raise ModelError("each entry under 'entities' must be a mapping, got %r" % spec)
        self.entity = str(spec.get("entity", "")).strip()
        if not IDENT.match(self.entity):
            raise ModelError("entity name %r is not a valid Power Fx identifier"
                             % self.entity)
        self.plural = str(spec.get("plural") or (self.entity + "s")).strip()
        if not IDENT.match(self.plural):
            raise ModelError("entity %r: plural %r is not a valid Power Fx identifier"
                             % (self.entity, self.plural))
        self.icon = str(spec.get("icon") or "AppsListDetail")
        self.group = str(spec.get("group") or "Data")
        self.key = str(spec.get("key") or "composite")
        if self.key not in ("composite", "single"):
            raise ModelError("entity %r: key must be 'composite' or 'single'" % self.entity)
        raw = spec.get("fields") or []
        if not raw:
            raise ModelError("entity %r: needs at least one field" % self.entity)
        self.fields = [Field(f, self.entity) for f in raw]
        seen = set()
        for f in self.fields:
            if f.name in seen:
                raise ModelError("entity %r: duplicate field name %r"
                                 % (self.entity, f.name))
            seen.add(f.name)
        titles = [f.name for f in self.fields if f.role == "title"]
        if len(titles) > 1:
            raise ModelError(
                "entity %r: more than one field has role: title (%s) — an entity "
                "may have only one; remove role: title from the extra fields"
                % (self.entity, ", ".join(titles)))
        statuses = [f.name for f in self.fields if f.role == "status"]
        if len(statuses) > 1:
            raise ModelError(
                "entity %r: more than one field has role: status (%s) — an entity "
                "may have only one; remove role: status from the extra fields"
                % (self.entity, ", ".join(statuses)))

    # ---- derived names: the single source of truth -------------------------
    @property
    def collection(self):
        return "col" + self.plural

    @property
    def scope_formula(self):
        return "const" + self.plural + "InScope"

    @property
    def func_load(self):
        return "funcLoad" + self.plural

    @property
    def func_save(self):
        return "funcSave" + self.entity

    @property
    def func_delete(self):
        return "funcDelete" + self.entity

    @property
    def loc_var(self):
        return "loc" + self.entity

    @property
    def list_screen(self):
        return self.plural + "ListScreen"

    @property
    def form_screen(self):
        return self.entity + "FormScreen"

    @property
    def gallery(self):
        return "gal_" + self.plural + "_Items"

    @property
    def enum_member(self):
        return "enumEntity." + self.plural

    def choices_table(self, field):
        return "const" + self.entity + field.name + "Choices"

    def head_control(self, field):
        return "cmp_" + self.plural + "List_Head" + field.name

    def cell_control(self, field):
        return "lbl_" + self.plural + "Row_" + field.name

    def form_control(self, field):
        prefix = {"choice": "com", "date": "dtp", "boolean": "tgl"}.get(field.type, "txt")
        return prefix + "_" + self.entity + "Form_" + field.name

    # ---- field partitions --------------------------------------------------
    @property
    def grid_fields(self):
        return [f for f in self.fields if f.in_grid][:MAX_GRID_COLUMNS]

    @property
    def form_fields(self):
        return list(self.fields)

    @property
    def search_fields(self):
        return [f for f in self.fields if f.search]

    @property
    def filter_fields(self):
        return [f for f in self.fields if f.filter]

    @property
    def choice_fields(self):
        return [f for f in self.fields if f.type == "choice"]

    @property
    def title_field(self):
        for f in self.fields:
            if f.role == "title":
                return f
        for f in self.fields:
            if f.type in ("text", "longtext"):
                return f
        return self.fields[0]

    @property
    def status_field(self):
        for f in self.fields:
            if f.role == "status":
                return f
        for f in self.fields:
            if f.type == "choice" and f.filter:
                return f
        return None

    @property
    def due_fields(self):
        return [f for f in self.fields if f.type == "date" and f.semantics == "due"]

    @property
    def money_fields(self):
        return [f for f in self.fields if f.type == "number" and f.money]

    def __repr__(self):
        return "<Entity %s (%d fields)>" % (self.entity, len(self.fields))


class Model(object):
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ModelError("model.yaml must be a mapping at the top level")
        self.app_name = str(data.get("app_name") or "New App")
        self.brand = data.get("brand")
        self.frame = str(data.get("frame") or "headermain")
        if self.frame not in ("headermain", "headermainfooter", "headerrailmain"):
            raise ModelError("frame must be headermain, headermainfooter or headerrailmain")
        raw = data.get("entities") or []
        if not raw:
            raise ModelError(
                "model.yaml needs at least one entry under 'entities'. See "
                "templates/model.example.yaml for the shape.")
        self.entities = [Entity(e) for e in raw]
        seen = set()
        for e in self.entities:
            if e.entity in seen:
                raise ModelError("duplicate entity name %r" % e.entity)
            seen.add(e.entity)
            if e.plural in {x.plural for x in self.entities if x is not e}:
                raise ModelError("duplicate plural %r — collections would collide" % e.plural)

        # ---- M2: derived choices-table names must not collide -------------
        # choices_table() concatenates entity.entity + field.name with no
        # separator, so entity "Asset" field "StatusChoices" and entity
        # "AssetStatus" field "Choices" both derive
        # "constAssetStatusChoicesChoices". Undetected, this reaches
        # emit_formulas.topo_sort as two blocks that define the SAME name,
        # which raises OrderError with an EMPTY cycle list — a confusing
        # internal error for what is really a model problem. Catch it here
        # with a message the user can act on.
        choices_owner = {}
        for e in self.entities:
            for f in e.choice_fields:
                cname = e.choices_table(f)
                if cname in choices_owner:
                    other_entity, other_field = choices_owner[cname]
                    raise ModelError(
                        "entity %r field %r and entity %r field %r both derive the "
                        "same choices table name %r — rename one of the fields (or "
                        "entities) so their names do not concatenate to the same "
                        "identifier" % (other_entity, other_field, e.entity, f.name, cname))
                choices_owner[cname] = (e.entity, f.name)

        raw = data.get("dashboard")
        self.dashboard = bool(raw) if raw is not None else len(self.entities) > 1
        self.description = str(data.get("description") or "")


def load_model(path):
    path = pathlib.Path(path)
    if not path.exists():
        raise ModelError("model file not found: %s" % path)
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ModelError("model.yaml is not valid YAML: %s" % exc)
    return Model(data)
