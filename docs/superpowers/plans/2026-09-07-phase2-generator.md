# Phase 2 — Multi-Entity Model-Driven Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `new_app.py` from a template copier into a generator that produces a complete, working, multi-entity Canvas App — N list screens with data tables, N edit forms, and visible mock data — from a `model.yaml` the agent either normalises from the user's input or infers from a domain sentence.

**Architecture:** Hybrid emitter. Static chrome (App.Formulas scaffold, frames, the eight components) stays as template files carrying splice markers; the repeating per-field and per-entity shapes are emitted by Python functions driven by the model. The emitter reads `references/control-contracts.yaml` — the same file `check_control_props.py` validates against — so generated output cannot contain a property the guard would reject.

**Tech Stack:** Python 3.9.6 (no `match`, no runtime PEP 604 unions, no `functools.cache`), PyYAML 6.0.3, stdlib `unittest` (pytest is NOT installed and must not be introduced).

**Spec:** `docs/superpowers/specs/2026-09-07-phase2-model-driven-generator-design.md`

## Global Constraints

- Skill root for all relative paths: `plugins/acoe-skills/skills/formulas-first-canvas-app/`
- Python 3.9.6 only. Tests via `python3 -m unittest discover -s tests -v` from the skill root.
- **Templates and documentation keep generic identifiers** (`colItems`, `funcLoadItems`, `funcSaveItem`, `locItem`). **Generated output uses entity-derived identifiers** (`colAssets`, `funcLoadAssets`, `funcSaveAsset`, `locAsset`). This split is a standing user preference — do not collapse it in either direction.
- Do not weaken the five existing guards or the six architectural rules.
- Generated output must be guard-clean by construction: no colour/font-size/radius literals outside the token region; no data-source name outside the data-access banners.
- Preserve the two deliberate warts: `cmp_Notification`'s repeated `First(SortByColumns(…))`, and any `// token-exempt:` literal.
- `new_app.py` runs **all** guards on its own output and exits non-zero rather than leaving a broken tree behind.
- `references/control-contracts.yaml` is evidence-backed against the compiled app at `/Users/krystofpe/powerapps-work/canvas-src`. Do NOT add entries. If the emitter needs a property that is missing, report it — that is a ruling, not an implementation detail.

## Two parked questions (do not try to settle them here)

1. Defect class 9 — a bare enum into a `DataType: Text` component input — may not be a real error; the compiled reference app does it and ships. **The emitter must pass strings, not enums, to component inputs**, which keeps generated output clean under the current rule either way.
2. `requires_one_of` on `Gallery` may need to accept `AlignInContainer: SetByContainer`. **The emitter always emits `FillPortions: =1` on galleries**, so generated output is unaffected.

## Naming derivation (used by every task — single source of truth)

For an entity with `entity: Asset`, `plural: Assets`:

| Thing | Derived name |
|---|---|
| collection | `colAssets` |
| scope formula | `constAssetsInScope` |
| load / save / delete UDF | `funcLoadAssets` / `funcSaveAsset` / `funcDeleteAsset` |
| form context variable | `locAsset` |
| list / form screen | `AssetsListScreen` / `AssetFormScreen` |
| gallery | `gal_Assets_Items` |
| choices table for field `Status` | `constAssetStatusChoices` |
| enumEntity member | `enumEntity.Assets` |
| header control for field `Tag` | `cmp_AssetsList_HeadTag` |
| row cell for field `Tag` | `lbl_AssetsRow_Tag` |
| form input for field `Tag` | `txt_AssetForm_Tag` |

All of this lives in `model.py` as properties on the `Entity` object. No other module recomputes a name.

---

### Task 1: `scripts/model.py` — schema, validation, derived names

**Files:**
- Create: `scripts/model.py`
- Create: `tests/test_model.py`
- Create: `templates/model.example.yaml`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Field` with attributes `name, type, required, search, filter, grid, label, money, currency, min, max, semantics, vocab, samples`, plus `in_grid` (bool), `grid_width` (int or `"flex"`).
  - `Entity` with `entity, plural, icon, group, key, fields`, plus derived-name properties from the table above, plus `grid_fields`, `form_fields`, `search_fields`, `filter_fields`, `choice_fields`.
  - `Model` with `app_name, brand, frame, entities`.
  - `load_model(path) -> Model` — raises `ModelError` with an actionable message.
  - `ModelError(Exception)`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_model.py`:

```python
"""The model is the app's spec. A bad model must fail loudly here, never downstream."""
import pathlib
import sys
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402

MINIMAL = textwrap.dedent("""\
    app_name: Test App
    entities:
      - entity: Asset
        plural: Assets
        fields:
          - {name: Tag, type: text, required: true, grid: 100}
          - {name: Status, type: choice, grid: 120, filter: true, vocab: [Open, Shut]}
          - {name: Amount, type: number, grid: 118, money: true}
          - {name: Due, type: date, grid: 112, semantics: due}
          - {name: Notes, type: text, grid: hidden}
    """)


def write(tmpdir, text):
    p = pathlib.Path(tmpdir) / "model.yaml"
    p.write_text(text, encoding="utf-8")
    return p


class TestDerivedNames(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.model = m.load_model(write(self.tmp, MINIMAL))
        self.e = self.model.entities[0]

    def test_entity_derived_identifiers(self):
        e = self.e
        self.assertEqual(e.collection, "colAssets")
        self.assertEqual(e.scope_formula, "constAssetsInScope")
        self.assertEqual(e.func_load, "funcLoadAssets")
        self.assertEqual(e.func_save, "funcSaveAsset")
        self.assertEqual(e.func_delete, "funcDeleteAsset")
        self.assertEqual(e.loc_var, "locAsset")
        self.assertEqual(e.list_screen, "AssetsListScreen")
        self.assertEqual(e.form_screen, "AssetFormScreen")
        self.assertEqual(e.gallery, "gal_Assets_Items")
        self.assertEqual(e.enum_member, "enumEntity.Assets")

    def test_choices_table_name_is_per_entity_and_field(self):
        """Two entities may both have a Status field; the names must not collide."""
        status = [f for f in self.e.fields if f.name == "Status"][0]
        self.assertEqual(self.e.choices_table(status), "constAssetStatusChoices")

    def test_field_partitions(self):
        e = self.e
        self.assertEqual([f.name for f in e.grid_fields],
                         ["Tag", "Status", "Amount", "Due"])
        self.assertEqual([f.name for f in e.form_fields],
                         ["Tag", "Status", "Amount", "Due", "Notes"])
        self.assertEqual([f.name for f in e.choice_fields], ["Status"])
        self.assertEqual([f.name for f in e.filter_fields], ["Status"])

    def test_label_defaults_to_uppercased_name(self):
        self.assertEqual(self.e.grid_fields[0].label, "TAG")


class TestValidation(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def _err(self, text):
        with self.assertRaises(m.ModelError) as cm:
            m.load_model(write(self.tmp, text))
        return str(cm.exception)

    def test_unknown_archetype_is_rejected_and_lists_valid_ones(self):
        msg = self._err(MINIMAL.replace("type: text, required: true", "type: wibble"))
        self.assertIn("wibble", msg)
        self.assertIn("text", msg)

    def test_choice_without_vocab_is_rejected(self):
        bad = MINIMAL.replace(", vocab: [Open, Shut]", "")
        self.assertIn("vocab", self._err(bad))

    def test_no_entities_is_rejected(self):
        self.assertIn("entities", self._err("app_name: X\nentities: []\n"))

    def test_duplicate_entity_names_are_rejected(self):
        dup = MINIMAL + textwrap.dedent("""\
              - entity: Asset
                plural: Assets
                fields:
                  - {name: Tag, type: text}
            """)
        self.assertIn("Asset", self._err(dup))

    def test_duplicate_field_names_within_an_entity_are_rejected(self):
        dup = MINIMAL.replace("- {name: Notes, type: text, grid: hidden}",
                              "- {name: Tag, type: text, grid: hidden}")
        self.assertIn("Tag", self._err(dup))

    def test_field_name_colliding_with_the_key_column_is_rejected(self):
        bad = MINIMAL.replace("{name: Tag, type: text, required: true, grid: 100}",
                              "{name: Key, type: text, required: true, grid: 100}")
        self.assertIn("Key", self._err(bad))

    def test_field_name_must_be_a_valid_powerfx_identifier(self):
        bad = MINIMAL.replace("{name: Tag,", "{name: 'Tag Number',")
        self.assertIn("Tag Number", self._err(bad))


class TestGridCap(unittest.TestCase):
    def test_fields_beyond_the_cap_fall_off_the_grid_but_stay_on_the_form(self):
        import tempfile
        fields = "\n".join(
            "          - {name: F%d, type: text, grid: 100}" % i for i in range(12))
        text = ("app_name: T\nentities:\n  - entity: A\n    plural: As\n"
                "    fields:\n" + fields + "\n")
        mo = m.load_model(write(tempfile.mkdtemp(), text))
        e = mo.entities[0]
        self.assertEqual(len(e.grid_fields), m.MAX_GRID_COLUMNS)
        self.assertEqual(len(e.form_fields), 12)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd plugins/acoe-skills/skills/formulas-first-canvas-app
python3 -m unittest tests.test_model -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'model'`.

- [ ] **Step 3: Write `scripts/model.py`**

```python
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
        self.type = str(spec.get("type", "text")).strip()
        if self.type not in ARCHETYPES:
            raise ModelError("entity %r, field %r: unknown type %r — valid types are: %s"
                             % (entity_name, self.name, self.type, ", ".join(ARCHETYPES)))
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
        self.grid_width = raw_grid if raw_grid in ("flex", "hidden") else int(raw_grid)

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
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_model -v
```

Expected: OK.

- [ ] **Step 5: Write `templates/model.example.yaml`**

The full worked example from the spec's "Model schema" section, with two entities (`Asset` and `Site`) so the multi-entity shape is documented by example. Include a header comment saying this file is the app's spec and should be committed beside the source tree.

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/model.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_model.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/templates/model.example.yaml
git commit -m "feat: model schema, validation and derived naming

model.py owns every generated identifier so no two emitters can disagree
about what a collection is called. Validation fails with an actionable
message rather than letting a bad model reach the emitters."
```

---

### Task 2: `scripts/emit_mock.py` — mock data that looks alive

The defect that started this whole effort was a scaffold that rendered empty. Mock data is not decoration; it is the proof the app works.

**Files:**
- Create: `scripts/emit_mock.py`
- Create: `tests/test_emit_mock.py`

**Interfaces:**
- Consumes: `model.Entity`, `model.Field` from Task 1.
- Produces: `mock_rows(entity, n=16, today=None) -> List[Dict[str, str]]` — each dict maps a column name to a **Power Fx literal string** (already quoted/formatted, ready to splice). Plus `mock_table_literal(entity, n, today, indent) -> str` returning the full `Table({...}, {...})` text.

- [ ] **Step 1: Write the failing test**

Create `tests/test_emit_mock.py`:

```python
"""Mock data must exercise every control, or the app looks broken on first run."""
import datetime
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_mock  # noqa: E402

TODAY = datetime.date(2026, 9, 7)


def entity(**over):
    spec = {
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Tag", "type": "text", "grid": 100,
             "samples": ["EQ-10041", "EQ-10042", "EQ-10043"]},
            {"name": "Status", "type": "choice", "grid": 120,
             "vocab": ["In Service", "Faulty", "Retired"]},
            {"name": "Health", "type": "choice", "grid": 118,
             "vocab": ["green", "amber", "red"], "semantics": "semafor"},
            {"name": "Amount", "type": "number", "grid": 118, "money": True, "min": 0},
            {"name": "Due", "type": "date", "grid": 112, "semantics": "due"},
            {"name": "Active", "type": "boolean", "grid": 80},
        ],
    }
    spec.update(over)
    return m.Entity(spec)


class TestVocabCoverage(unittest.TestCase):
    def test_every_vocab_value_appears_at_least_once(self):
        """A filter option that yields an empty grid looks like a broken app."""
        e = entity()
        rows = emit_mock.mock_rows(e, n=16, today=TODAY)
        for f in e.choice_fields:
            got = {r[f.name].strip('"') for r in rows}
            self.assertEqual(set(f.vocab) - got, set(),
                             "%s: unused vocab values" % f.name)

    def test_holds_even_when_rows_barely_exceed_vocab_size(self):
        e = entity()
        rows = emit_mock.mock_rows(e, n=3, today=TODAY)
        got = {r["Status"].strip('"') for r in rows}
        self.assertEqual(got, {"In Service", "Faulty", "Retired"})


class TestDates(unittest.TestCase):
    def test_due_dates_emit_date_literals_never_strings(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        for r in rows:
            self.assertRegex(r["Due"], r"^Date\(\d{4}, \d{1,2}, \d{1,2}\)$")

    def test_roughly_thirty_percent_of_due_dates_are_overdue(self):
        """Overdue styling and counters must be visible on first run."""
        rows = emit_mock.mock_rows(entity(), n=20, today=TODAY)
        past = sum(1 for r in rows if emit_mock._parse_date_literal(r["Due"]) < TODAY)
        self.assertGreaterEqual(past, 3)
        self.assertLessEqual(past, 10)


class TestNumbers(unittest.TestCase):
    def test_spread_across_two_orders_of_magnitude(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        vals = [float(r["Amount"]) for r in rows]
        self.assertGreater(max(vals) / max(min(vals), 1), 50)

    def test_min_is_respected(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        self.assertTrue(all(float(r["Amount"]) >= 0 for r in rows))


class TestText(unittest.TestCase):
    def test_samples_are_cycled_not_numbered(self):
        rows = emit_mock.mock_rows(entity(), n=6, today=TODAY)
        tags = [r["Tag"].strip('"') for r in rows]
        self.assertTrue(all(t.startswith("EQ-") for t in tags), tags)
        self.assertNotIn('"Item 1"', tags)

    def test_a_text_field_with_no_samples_still_reads_as_a_record(self):
        e = m.Entity({"entity": "A", "plural": "As",
                      "fields": [{"name": "Title", "type": "text"}]})
        rows = emit_mock.mock_rows(e, n=4, today=TODAY)
        titles = [r["Title"] for r in rows]
        self.assertEqual(len(set(titles)), 4)


class TestKeys(unittest.TestCase):
    def test_composite_keys_are_prefixed_and_unique(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        keys = [r["Key"] for r in rows]
        self.assertEqual(len(set(keys)), 16)
        self.assertTrue(all("|" in k for k in keys))


class TestTableLiteral(unittest.TestCase):
    def test_emits_a_parseable_table_with_no_bare_clear(self):
        text = emit_mock.mock_table_literal(entity(), 16, TODAY, indent=10)
        self.assertTrue(text.lstrip().startswith("Table("))
        self.assertNotIn("Clear(", text)
        self.assertEqual(text.count("{Key:"), 16)

    def test_every_row_has_every_column(self):
        e = entity()
        text = emit_mock.mock_table_literal(e, 5, TODAY, indent=10)
        for f in e.fields:
            self.assertEqual(text.count(f.name + ":"), 5, f.name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
python3 -m unittest tests.test_emit_mock -v
```

Expected: FAIL — no module named `emit_mock`.

- [ ] **Step 3: Write `scripts/emit_mock.py`**

Requirements the implementation must satisfy (the tests above are the contract):

- `mock_rows(entity, n, today)` returns `n` dicts, each with a `Key` plus one entry per field, values already formatted as Power Fx literals: text as `"..."` (quotes included, inner quotes escaped), number as a bare numeral, date as `Date(y, m, d)`, boolean as `true`/`false`, choice as a quoted vocab value.
- **Vocab coverage first, cycling second.** Assign the first `len(vocab)` rows one distinct vocab value each, then cycle. This is what makes the guarantee hold when `n` barely exceeds the vocab size.
- **Dates:** for `semantics: due`, place roughly 30% before `today` and the rest after, spread over ±90 days. For other date fields, spread forward.
- **Numbers:** spread across two orders of magnitude, e.g. cycle a multiplier over `[1, 3, 12, 47, 140]` times a base, clamped to `min`/`max` when given. Round money to 2dp.
- **Text:** cycle `samples` when present. With no samples, compose distinct readable values from the field name and row index in a way that does not read as `Item 1` — e.g. join a small internal word list so rows look like records.
- **Keys:** `"<PREFIX>|<n>"` where `PREFIX` is derived from the first choice field's value for that row (uppercased, first 3 chars) when one exists, else from the entity name. Guarantee uniqueness by appending the row index.
- `_parse_date_literal(s)` is a small test helper — keep it module-level and documented as such.
- `mock_table_literal(entity, n, today, indent)` renders `Table(\n  {…},\n  {…}\n)` with the given indent, one row per line group, keys in field order with `Key` first.

Add a module docstring recording **why** this exists: every scaffolded app rendered empty because the seed rows were cleared; mock data is the proof the app works, not decoration.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_emit_mock -v
```

Expected: OK, 11 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/emit_mock.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_emit_mock.py
git commit -m "feat: mock data generator that exercises every control

Guarantees at least one row per vocab value so no filter option yields an
empty grid, ~30% overdue dates so overdue styling is visible on first run,
numbers across two orders of magnitude, and Date() literals never strings."
```

---

### Task 3: `scripts/emit_formulas.py` — the multi-entity data layer, dependency-ordered

**This is the riskiest task in the plan.** The studio binder cannot forward-reference between named formulas, and one unresolved name drops the entire `Formulas` blob — the whole app goes blank with no error pointing at the cause. With N entities the ordering stops being trivial.

**Files:**
- Create: `scripts/emit_formulas.py`
- Create: `tests/test_emit_formulas.py`

**Interfaces:**
- Consumes: `model.Model`, `emit_mock.mock_table_literal`.
- Produces:
  - `emit_enum_entity(model) -> str`
  - `emit_choices_tables(model) -> str`
  - `emit_data_layer(model, rows, today) -> str` — per entity: scope formula, load/save/delete UDFs, with the real-datasource binding commented beneath each mock.
  - `emit_screens_registry(model) -> str` — `constScreens` rows, two per entity.
  - `topo_sort(blocks) -> List[Block]` where `Block` is `namedtuple("Block", "name defines uses text")`.
  - `emit_all(model, rows, today) -> str` — the assembled, ordered Formulas body.

- [ ] **Step 1: Write the failing test**

Create `tests/test_emit_formulas.py`:

```python
"""App.Formulas must be strictly dependency-ordered.

The studio binder cannot forward-reference between named formulas, and ONE
unresolved name drops the entire Formulas blob — the app goes blank with no
error naming the cause. These tests are the only thing standing between a
model and that failure.
"""
import datetime
import pathlib
import re
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_formulas as ef  # noqa: E402

TODAY = datetime.date(2026, 9, 7)


def two_entity_model():
    return m.Model({
        "app_name": "Ops",
        "entities": [
            {"entity": "Asset", "plural": "Assets", "fields": [
                {"name": "Tag", "type": "text", "grid": 100, "search": True},
                {"name": "Status", "type": "choice", "grid": 120, "filter": True,
                 "vocab": ["Open", "Shut"]},
                {"name": "Amount", "type": "number", "grid": 118, "money": True},
            ]},
            {"entity": "Site", "plural": "Sites", "fields": [
                {"name": "Name", "type": "text", "grid": "flex", "search": True},
                {"name": "Status", "type": "choice", "grid": 120, "filter": True,
                 "vocab": ["Live", "Closed"]},
            ]},
        ],
    })


class TestTopoSort(unittest.TestCase):
    def test_a_block_comes_after_everything_it_uses(self):
        B = ef.Block
        blocks = [
            B("c", {"c"}, {"b"}, "c = b + 1;"),
            B("a", {"a"}, set(), "a = 1;"),
            B("b", {"b"}, {"a"}, "b = a + 1;"),
        ]
        order = [b.name for b in ef.topo_sort(blocks)]
        self.assertLess(order.index("a"), order.index("b"))
        self.assertLess(order.index("b"), order.index("c"))

    def test_a_cycle_raises_rather_than_emitting_a_blob_that_silently_dies(self):
        B = ef.Block
        blocks = [B("a", {"a"}, {"b"}, ""), B("b", {"b"}, {"a"}, "")]
        with self.assertRaises(ef.OrderError) as cm:
            ef.topo_sort(blocks)
        self.assertIn("a", str(cm.exception))

    def test_ordering_is_deterministic_across_runs(self):
        mo = two_entity_model()
        a = ef.emit_all(mo, rows=8, today=TODAY)
        b = ef.emit_all(mo, rows=8, today=TODAY)
        self.assertEqual(a, b)


class TestEmittedNamesResolve(unittest.TestCase):
    """Every name used must be defined earlier in the emitted text."""

    def test_no_forward_references_in_the_assembled_body(self):
        text = ef.emit_all(two_entity_model(), rows=8, today=TODAY)
        defined_at = {}
        for match in re.finditer(r"^      (\w+)(?:\([^)]*\))?\s*(?::\s*\w+\s*)?=",
                                 text, re.M):
            defined_at.setdefault(match.group(1), match.start())
        for name, pos in defined_at.items():
            for use in re.finditer(r"\b%s\b" % re.escape(name), text):
                if use.start() < pos:
                    self.fail("%s used at %d before its definition at %d"
                              % (name, use.start(), pos))


class TestPerEntityLayer(unittest.TestCase):
    def setUp(self):
        self.model = two_entity_model()
        self.text = ef.emit_all(self.model, rows=8, today=TODAY)

    def test_each_entity_gets_its_own_collection_and_udfs(self):
        for name in ("colAssets", "funcLoadAssets", "funcSaveAsset", "funcDeleteAsset",
                     "colSites", "funcLoadSites", "funcSaveSite", "funcDeleteSite"):
            self.assertIn(name, self.text, name)

    def test_generic_template_identifiers_do_not_leak_into_generated_output(self):
        for leaked in ("colItems", "funcLoadItems", "funcSaveItem", "locItem"):
            self.assertNotIn(leaked, self.text, leaked)

    def test_same_named_fields_on_two_entities_get_distinct_choices_tables(self):
        self.assertIn("constAssetStatusChoices", self.text)
        self.assertIn("constSiteStatusChoices", self.text)

    def test_no_bare_clear_on_an_entity_collection(self):
        self.assertNotIn("Clear(colAssets)", self.text)
        self.assertNotIn("Clear(colSites)", self.text)

    def test_udf_parameters_use_the_p_prefix_to_avoid_row_scope_collision(self):
        """A parameter one case-fold from a column makes {Tag: tag} resolve to
        Tag: Tag — a save that writes nothing and reports success."""
        for sig in re.findall(r"funcSave\w+\(([^)]*)\)", self.text):
            for param in [p.split(":")[0].strip() for p in sig.split(",") if p.strip()]:
                self.assertTrue(param.startswith("p"),
                                "parameter %r must use the p prefix" % param)

    def test_registry_has_two_rows_per_entity(self):
        reg = ef.emit_screens_registry(self.model)
        self.assertEqual(reg.count("Screen:"), 4)
        for s in ("AssetsListScreen", "AssetFormScreen",
                  "SitesListScreen", "SiteFormScreen"):
            self.assertIn(s, reg)

    def test_enum_entity_has_one_member_per_entity(self):
        e = ef.emit_enum_entity(self.model)
        self.assertIn("Assets:", e)
        self.assertIn("Sites:", e)

    def test_switch_day_binding_is_present_but_commented(self):
        self.assertIn("// SWITCH DAY", self.text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
python3 -m unittest tests.test_emit_formulas -v
```

Expected: FAIL — no module named `emit_formulas`.

- [ ] **Step 3: Write `scripts/emit_formulas.py`**

Structure the emitter as `Block` objects — `namedtuple("Block", "name defines uses text")` — one per named formula or UDF, then `topo_sort` them before joining. Do NOT emit in a hand-maintained order; the whole point is that the order is computed.

`topo_sort` requirements:
- Kahn's algorithm over `defines` → `uses` edges.
- Ties broken by a stable key (the layer index, then the name) so output is byte-identical across runs.
- On a cycle, raise `OrderError` naming the participating blocks. Never emit a body that would silently die.

Layers, in the order the existing `templates/App.pa.yaml` documents them (read it — the comments name each layer):
1. enums (`enumScreenType`, `enumEntity`)
2. choices tables, one per choice field per entity
3. scalar constants
4. pure helper UDFs (unchanged from the template)
5. globals
6. data-access layer, per entity: scope formula → load → save → delete
7. registries (`constScreens`), which read layer 6 and must come last

For each entity's load UDF, emit the mock `ClearCollect` from `emit_mock.mock_table_literal`, then the commented `// SWITCH DAY` real-datasource binding beneath it, matching the shape already in `templates/App.pa.yaml`. **No bare `Clear()` on the entity collection** — Phase 1's `check_bare_clear` enforces this and the tests above assert it.

UDF parameters take a `p` prefix (`pKey`, `pTag`, `pStatus`) because `UpdateIf`/`Patch` open the collection's row scope over both the condition and the change record, so a parameter one case-fold from a column silently writes nothing.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_emit_formulas -v
```

Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/emit_formulas.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_emit_formulas.py
git commit -m "feat: multi-entity data layer with computed dependency order

Blocks are topologically sorted rather than hand-ordered: the studio binder
cannot forward-reference between named formulas, and one unresolved name
drops the entire Formulas blob with no error naming the cause. A cycle
raises instead of emitting a body that dies silently."
```

---

### Task 4: `scripts/emit_screens.py` — list and form screens per entity

**Files:**
- Create: `scripts/emit_screens.py`
- Create: `tests/test_emit_screens.py`

**Interfaces:**
- Consumes: `model.Entity`, and `check_control_props.load_contracts` for property validation.
- Produces: `emit_list_screen(entity, model) -> str`, `emit_form_screen(entity, model) -> str`.

**Read these before writing anything** — they are the shapes being parameterised:
- `templates/ListScreen.pa.yaml` lines 146-161 (one `cmp_FilterButton` header instance)
- `templates/ListScreen.pa.yaml` lines 232-262 (row cells inside the gallery)
- `templates/ListScreen.pa.yaml` lines 196-215 (the gallery `Items` formula)
- `templates/FormScreen.pa.yaml` lines 70-102 (a text field block and a choice field block)

- [ ] **Step 1: Write the failing test**

Create `tests/test_emit_screens.py`:

```python
"""Generated screens must be contract-clean by construction, not by luck."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_screens as es  # noqa: E402
import check_control_props as ccp  # noqa: E402


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
        ],
    })


def small_model():
    return m.Model({"app_name": "Ops", "entities": [{
        "entity": "Asset", "plural": "Assets",
        "fields": [{"name": "Tag", "type": "text", "grid": 100}]}]})


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


class TestNoGenericLeakage(unittest.TestCase):
    def test_template_identifiers_do_not_appear_in_generated_screens(self):
        e, mo = entity(), small_model()
        for text in (es.emit_list_screen(e, mo), es.emit_form_screen(e, mo)):
            for leaked in ("colItems", "locItem", "gal_List_Items"):
                self.assertNotIn(leaked, text, leaked)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
python3 -m unittest tests.test_emit_screens -v
```

Expected: FAIL — no module named `emit_screens`.

- [ ] **Step 3: Write `scripts/emit_screens.py`**

Archetype → control mapping for grid cells and form inputs:

| Archetype | Grid cell | Form input |
|---|---|---|
| `text`, `longtext` | `ModernText` | `ModernTextInput` (`Type: =TextInputType.Multiline` for longtext) |
| `choice` | `ModernText`, colour via `funcStatusTextColor` when `semantics: semafor` | `ModernCombobox`, `SelectMultiple: =false` |
| `number` | `ModernText`, `Align: =constStyle.Label.NumberInput.AlignModern`, text via `funcAsCurrency` when `money` | `ModernTextInput` (no `Format` — parse with `Value()` on save) |
| `date` | `ModernText`, overdue colour when `semantics: due` | `ModernDatePicker` |
| `boolean` | `ModernText` showing Yes/No | `ModernToggle` if present in the contract file, else `ModernCombobox` over a two-row table — **check the contract file first and report if neither is available** |

Every emitted property must be checked against `references/control-contracts.yaml` before it is written. Add a small helper that raises on an unknown property so a mistake fails at generation time, not at push time.

Component inputs take **strings**, never enums (`Align: ="Right"`), because `cmp_FilterButton` declares them `DataType: Text`.

Galleries always get `FillPortions: =1`.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_emit_screens -v
```

Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/emit_screens.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_emit_screens.py
git commit -m "feat: per-entity list and form screen emitters

The emitter reads references/control-contracts.yaml — the same file the
guard validates against — so generated screens cannot carry a property the
guard would reject. Verified by running the guard over emitter output."
```

---

### Task 5: Wire `--model` into `new_app.py`

**Files:**
- Modify: `scripts/new_app.py`
- Create: `tests/test_new_app_model.py`

**Interfaces:**
- Consumes: everything from Tasks 1-4.
- Produces: `new_app.py --model model.yaml --out DIR [--rows N] [--force]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_new_app_model.py`:

```python
"""End-to-end: a model in, a guard-clean multi-entity app out."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]

TWO_ENTITY = textwrap.dedent("""\
    app_name: Ops Register
    brand: "#300091"
    entities:
      - entity: Asset
        plural: Assets
        group: Operations
        fields:
          - {name: Tag, type: text, required: true, grid: 100, search: true, samples: [EQ-1, EQ-2]}
          - {name: Status, type: choice, required: true, grid: 120, filter: true, vocab: [Open, Shut]}
          - {name: Amount, type: number, grid: 118, money: true, min: 0}
          - {name: Due, type: date, grid: 112, semantics: due}
      - entity: Site
        plural: Sites
        group: Operations
        fields:
          - {name: Name, type: text, required: true, grid: flex, search: true}
          - {name: Status, type: choice, required: true, grid: 120, filter: true, vocab: [Live, Closed]}
    """)


class TestGenerateTwoEntityApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        model = pathlib.Path(cls.tmp) / "model.yaml"
        model.write_text(TWO_ENTITY, encoding="utf-8")
        cls.out = pathlib.Path(cls.tmp) / "Src"
        cls.proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "new_app.py"),
             "--model", str(model), "--out", str(cls.out), "--rows", "12"],
            capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_exits_zero(self):
        self.assertEqual(self.proc.returncode, 0,
                         self.proc.stdout + self.proc.stderr)

    def test_all_guards_report_pass(self):
        self.assertEqual(self.proc.stdout.count("PASS"), 5, self.proc.stdout)

    def test_one_list_and_one_form_screen_per_entity(self):
        for f in ("AssetsListScreen.pa.yaml", "AssetFormScreen.pa.yaml",
                  "SitesListScreen.pa.yaml", "SiteFormScreen.pa.yaml"):
            self.assertTrue((self.out / f).exists(), f)

    def test_mock_rows_are_present_and_not_cleared(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        self.assertEqual(app.count("{Key:"), 24)   # 12 rows x 2 entities
        self.assertNotIn("Clear(colAssets)", app)
        self.assertNotIn("Clear(colSites)", app)

    def test_navigation_registry_lists_all_four_screens(self):
        app = (self.out / "App.pa.yaml").read_text(encoding="utf-8")
        self.assertEqual(app.count("Type: enumScreenType.List"), 2)
        self.assertEqual(app.count("Type: enumScreenType.Form"), 2)

    def test_no_generic_template_identifier_leaked(self):
        for p in self.out.rglob("*.pa.yaml"):
            text = p.read_text(encoding="utf-8")
            for leaked in ("colItems", "funcSaveItem", "locItem"):
                self.assertNotIn(leaked, text, "%s in %s" % (leaked, p.name))

    def test_all_eight_components_are_written(self):
        self.assertEqual(len(list((self.out / "Components").glob("cmp_*.pa.yaml"))), 8)


class TestBadModelFailsBeforeWriting(unittest.TestCase):
    def test_invalid_model_exits_nonzero_and_writes_nothing(self):
        tmp = tempfile.mkdtemp()
        model = pathlib.Path(tmp) / "model.yaml"
        model.write_text("app_name: X\nentities:\n  - entity: A\n    plural: As\n"
                         "    fields:\n      - {name: S, type: choice}\n",
                         encoding="utf-8")
        out = pathlib.Path(tmp) / "Src"
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "new_app.py"),
             "--model", str(model), "--out", str(out)],
            capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("vocab", proc.stdout + proc.stderr)
        self.assertFalse(out.exists() and any(out.iterdir()))
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
python3 -m unittest tests.test_new_app_model -v
```

Expected: FAIL — `--model` is not a recognised argument.

- [ ] **Step 3: Wire `--model` into `new_app.py`**

Add `--model` and `--rows` (default 16). When `--model` is given:
1. `load_model()` first, before creating any directory, so a bad model writes nothing.
2. Assemble `App.pa.yaml` from the template plus `emit_formulas.emit_all()` spliced at a new marker.
3. Write one list screen and one form screen per entity from `emit_screens`.
4. Write the components as today.
5. Write `_EditorState.pa.yaml` listing every generated screen.
6. Run all five guards; exit non-zero on any failure.

Keep the existing `--name`/`--brand` path working for a model-less scaffold — it is what the tests from Phase 1 exercise. `--model` and `--name` are mutually exclusive; say so if both are given.

The brand colour comes from `model.brand` when present, else `--brand`.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m unittest tests.test_new_app_model -v
```

Expected: OK.

- [ ] **Step 5: Verify the full suite and a real generation**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
rm -rf /tmp/twoent && python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/twoent
echo "exit=$?"
ls /tmp/twoent
```

Expected: suite green; generation exits 0 with five PASS lines; one list and one form screen per entity in the example model.

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/new_app.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_new_app_model.py
git commit -m "feat: new_app.py --model generates a complete multi-entity app

A model with N tables produces N list screens and N forms, mock rows that
survive to render, and a navigation registry the nav rail reads. All five
guards run on the output; a bad model fails before anything is written."
```

---

### Task 6: The four field components

**Files:**
- Create: `components/cmp_FieldText.pa.yaml`, `cmp_FieldChoice.pa.yaml`, `cmp_FieldDate.pa.yaml`, `cmp_FieldNumber.pa.yaml`
- Modify: `scripts/new_app.py` (`ALL_COMPONENTS`)
- Create: `tests/test_field_components.py`

**Separate per type on purpose.** Each has ONE scalar output of a known type. A single generic `cmp_Field` switching over four control types and returning a Record is exactly the construct that caused the 247-error type-cycle cascade documented in `references/powerfx-limits.md`. Do not build it, and do not "simplify" these four into one.

**Interfaces produced:** each component exposes inputs `Label` (Text), `Value` (the scalar, typed per component), `Required` (Boolean), `Placeholder` (Text), `DisplayMode`; and one output `Output` of the matching scalar type, plus `OnChange`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_field_components.py`:

```python
"""Four per-type field components, deliberately not one generic one."""
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import check_control_props as ccp  # noqa: E402

NAMES = ("cmp_FieldText", "cmp_FieldChoice", "cmp_FieldDate", "cmp_FieldNumber")


class TestFieldComponents(unittest.TestCase):
    def test_all_four_exist(self):
        for n in NAMES:
            self.assertTrue((SKILL / "components" / (n + ".pa.yaml")).exists(), n)

    def test_each_declares_exactly_one_scalar_output(self):
        defs = ccp.parse_component_defs(
            [SKILL / "components" / (n + ".pa.yaml") for n in NAMES])
        for n in NAMES:
            self.assertIn("Output", defs[n], n)

    def test_no_generic_cmp_field_exists(self):
        """A single component returning a Record caused a 247-error cascade."""
        self.assertFalse((SKILL / "components" / "cmp_Field.pa.yaml").exists())

    def test_all_four_are_contract_clean(self):
        contracts = ccp.load_contracts()
        for n in NAMES:
            p = SKILL / "components" / (n + ".pa.yaml")
            errs = [f for f in ccp.check_text(p.read_text(encoding="utf-8"),
                                              str(p), contracts)
                    if f.severity == "error"]
            self.assertEqual(errs, [], "%s: %s" % (n, errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails, then write the four components**

Model them on the existing `components/cmp_Spinner.pa.yaml` for the file shape and on `templates/FormScreen.pa.yaml` lines 70-102 for the label-plus-input layout. Each is a vertical container with a `ModernText` label and one input control.

- [ ] **Step 3: Add them to `ALL_COMPONENTS` in `new_app.py` and re-run the full suite**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
rm -rf /tmp/fc && python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/fc && echo ok
```

- [ ] **Step 4: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/components/ \
        plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/new_app.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_field_components.py
git commit -m "feat: four per-type field components

Separate per type on purpose: each has one scalar output of a known type,
which structurally avoids the whole-record type-cycle cascade that produced
247 errors. A generic cmp_Field returning a Record must never be built."
```

---

### Task 7: `scripts/check_layout.py` and `--frame`

**Files:**
- Create: `scripts/check_layout.py`
- Create: `tests/test_check_layout.py`
- Modify: `scripts/new_app.py` (add to the guard list, add `--frame`)
- Create: `templates/frame-headermainfooter.pa.yaml`, `templates/frame-headerrailmain.pa.yaml`

**Interfaces:** `check_layout.py --src DIR`, same CLI convention as the other guards, PASS/FAIL first line, coverage-limit line, `sys.exit(1)` on violation.

Rules to enforce:
- every `FillPortions: =0` child of an auto-layout container carries an explicit `Width` (horizontal parent) or `Height` (vertical parent) — `LayoutMinHeight` is ignored for fixed children
- every auto-layout container has at least one flexible child or an explicit size
- a leaf control with neither `FillPortions` nor an explicit size is flagged
- `Visible:` on a flexible spacer is flagged — **an invisible child is dropped from auto-layout entirely**, so the gap collapses and the layout shifts with the data. The correct pattern keeps it visible and blanks its `Text`.

- [ ] **Step 1: Write the failing test** covering one positive and one negative case per rule, using the real `Variant: AutoLayout` block shape (see `templates/ListScreen.pa.yaml`). Reuse `check_control_props.iter_properties` for parsing rather than writing a second parser — and note in the docstring that it inherits that parser's coverage limits.

- [ ] **Step 2: Run it, confirm RED, implement, confirm GREEN.**

- [ ] **Step 3: Add the two frame templates and the `--frame` flag.** Header and footer pinned with explicit heights; main sized `Parent.Height - header - footer`. Comment each frame so a reader can see why the sizing works.

- [ ] **Step 4: Run `check_layout.py` against `templates/` and `components/`.** If it flags something, that is a real layout defect — fix it and say so, do not loosen the rule.

- [ ] **Step 5: Add to `new_app.py`'s guard list and confirm generation still exits 0 with six PASS lines.**

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/check_layout.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/tests/test_check_layout.py \
        plugins/acoe-skills/skills/formulas-first-canvas-app/templates/ \
        plugins/acoe-skills/skills/formulas-first-canvas-app/scripts/new_app.py
git commit -m "feat: layout guard and frame options

Catches the auto-layout failures that produce a visually broken app which
every other guard passes — notably a Visible: toggle on a flexible spacer,
which drops the child from layout entirely and collapses the gap."
```

---

### Task 8: The ask-for-model workflow in `SKILL.md`, and the compile-error playbook

This is the task that makes the feature real for a user. Everything before it is machinery.

**Files:**
- Modify: `SKILL.md`
- Create: `references/compile-error-playbook.md`
- Modify: `README.md`

- [ ] **Step 1: Write the workflow section in `SKILL.md`**

It must be written as a required sequence the agent performs, not as background. Cover:

```
1. ASK  — "Do you have a data model? Paste it in any form — a table, a
           SharePoint list, a Dataverse table, CSV headers, or just field
           names. If not, say so and I'll draft one."
2a. PROVIDED → normalise whatever arrived into model.yaml. Infer archetypes
               from the source's types; infer vocab from any choice column.
2b. ABSENT   → infer 8-12 fields per table from the domain sentence, with
               plausible vocab lists and 3-5 realistic samples per text field.
3. CONFIRM — show a compact field table. ONE round trip maximum. Accept
             "just go". Do not conduct a long interview.
4. WRITE   — model.yaml beside the source tree. It is the app's spec; commit it.
5. GENERATE— python3 scripts/new_app.py --model model.yaml --out ./Src
6. VERIFY  — the script runs every guard and exits non-zero on failure.
```

State the division of labour explicitly: **the agent supplies domain judgement** (which fields, which vocabulary values, realistic sample strings); **the script supplies correctness** (guard-clean YAML, vocabulary coverage, dates relative to today, dependency-ordered formulas). Neither does the other's job.

Also document that a model with N tables produces N list screens and N forms, and that generated identifiers are entity-derived while the skill's own templates stay generic.

- [ ] **Step 2: Write `references/compile-error-playbook.md`**

A table keyed by the **exact** error text `compile_canvas` returns → cause → remedy. Seed it from `references/powerfx-limits.md`, which already has the prose, plus the nine defect classes in `tests/test_defect_regression.py`. Include at minimum: unknown property errors for each renamed property; the named-formula forward-reference failure and its whole-blob symptom; the UDF row-scope collision; the type-cycle cascade.

- [ ] **Step 3: Document the loop in `SKILL.md`**

```
ask → draft model → generate → local guards → push (compile_canvas)
                                     ↑                    ↓
                                     └──── fix ──── parse errors
```

State plainly that the guards do not prove the app compiles — only `compile_canvas` does.

- [ ] **Step 4: Update `README.md`** with the new scripts, the model schema pointer, and the two new reference files.

- [ ] **Step 5: Verify every count and filename in the added prose** against the actual directory listing.

```bash
ls scripts/check_*.py | wc -l
ls scripts/emit_*.py
ls references/
```

- [ ] **Step 6: Commit**

```bash
git add plugins/acoe-skills/skills/formulas-first-canvas-app/SKILL.md \
        plugins/acoe-skills/skills/formulas-first-canvas-app/README.md \
        plugins/acoe-skills/skills/formulas-first-canvas-app/references/compile-error-playbook.md
git commit -m "docs: the ask-for-model workflow and the compile-error playbook

Encodes the division of labour: the agent supplies domain judgement, the
script supplies correctness. The playbook is what lets an agent iterate
push -> read errors -> fix -> repush unattended."
```

---

### Task 9: Version bump, sync, and a two-model acceptance check

**Files:**
- Modify: `plugins/acoe-skills/.claude-plugin/plugin.json`
- Create: `tests/test_acceptance.py`

- [ ] **Step 1: Write an acceptance test** that generates from a ONE-entity model and a THREE-entity model, and asserts for each: exit 0, every guard PASS, the expected screen count, mock rows present, no generic identifier leaked, and the nav registry populated. This is the plan's Definition of Done items 3 and 4, executable.

- [ ] **Step 2: Run it.**

```bash
python3 -m unittest tests.test_acceptance -v
```

- [ ] **Step 3: Bump the version** in `plugins/acoe-skills/.claude-plugin/plugin.json` from 0.8.0 to 0.9.0 (a feature addition).

- [ ] **Step 4: Full verification.**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
rm -rf /tmp/acc1 && python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/acc1 && echo "multi-entity OK"
rm -rf /tmp/acc2 && python3 scripts/new_app.py --name "Legacy Path" --brand "#300091" --out /tmp/acc2 && echo "legacy path OK"
```

Both must exit 0. The legacy `--name` path must keep working.

- [ ] **Step 5: Sync the installed copy, after a precheck you actually read.**

```bash
diff -rq plugins/acoe-skills/skills/formulas-first-canvas-app ~/.claude/skills/formulas-first-canvas-app | head -30
```

Read the output. Confirm the target contains only this skill's files. Then:

```bash
rsync -a --delete --exclude '.DS_Store' --exclude '__pycache__' \
  plugins/acoe-skills/skills/formulas-first-canvas-app/ \
  ~/.claude/skills/formulas-first-canvas-app/
diff -rq plugins/acoe-skills/skills/formulas-first-canvas-app \
         ~/.claude/skills/formulas-first-canvas-app | grep -v DS_Store || echo "IN SYNC"
```

- [ ] **Step 6: Commit**

```bash
git add -A plugins/acoe-skills/
git commit -m "feat: v0.9.0 — model-driven multi-entity generation

Acceptance-tested on one-entity and three-entity models: guards pass,
screens generated per entity, mock rows visible, nav registry populated."
```

---

## Self-review

**Spec coverage.** Every Phase 2 spec section maps to a task: model schema → Task 1; mock data rules → Task 2; multi-entity data layer and topological sort → Task 3; the five repeated shapes → Tasks 3 and 4; the ask-for-model workflow → Task 8; field components → Task 6; frames and layout guard → Task 7; compile-error playbook → Task 8; Definition of Done items 3 and 4 → Task 9's acceptance test.

**Gap found and closed.** The spec lists three silent-failure guards (UDF row-scope collision, `With()` wrapping behaviour functions, `SortByColumns` per-collection). Only the first is covered, and only by *generating* correct code (Task 3's `p`-prefix test) rather than by a guard. That is deliberate for this phase — the generator controls its own output, so a guard against hand-written mistakes is lower value than shipping generation. **Recorded as an explicit deferral, not an oversight:** if these are wanted as guards for hand-edited apps, they are a follow-up plan.

**Type consistency.** `model.Entity`'s derived-name properties are defined once in Task 1 and used by name in Tasks 3, 4 and 5 — `collection`, `func_load`, `func_save`, `func_delete`, `loc_var`, `list_screen`, `form_screen`, `gallery`, `enum_member`, `choices_table()`, `head_control()`, `cell_control()`, `form_control()`. `emit_mock.mock_rows`/`mock_table_literal` signatures match their use in Task 3. `ccp.check_text(text, filename, contracts, components=)` matches the Phase 1 signature.

**Known risk.** Task 3's topological sort is the one place a subtle bug produces a silently blank app rather than an error. Its test asserts no forward references in the assembled text by scanning definition positions — a real check, not a proxy — and a cycle raises rather than emitting. Task 5's end-to-end test then runs the real guards over the real output, which is the backstop.
