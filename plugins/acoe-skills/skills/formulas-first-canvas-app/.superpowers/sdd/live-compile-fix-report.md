# Live-compile fix report — 2026-09-07

First real `compile_canvas` push of this generator's output returned 59 errors
against a live environment, all attributable to exactly two root causes. Both
fixed, both guarded against regression.

## Root cause 1 — `TabIndex` is not a valid property (52/59 errors)

`TabIndex` was seeded into `references/control-contracts.yaml` from a
documentation source and never corpus-verified against the compiled reference
app — it appears zero times there. The live compiler confirmed it is unknown
on `ModernTextInput`, `ModernCombobox`, `ModernDatePicker`, and `Button`.

**Checked for a legitimate custom-property escape hatch first** — inspected
every `components/cmp_*.pa.yaml`'s `CustomProperties:` block. None declares
`TabIndex` as its own input; every hit was a plain control-property
assignment (`TabIndex: =0`). No exception found — all removed.

Fixed:
- `references/control-contracts.yaml`: removed `TabIndex` from the
  `properties` list of all 8 controls that carried it (ModernText, Text,
  ModernTextInput, ModernCombobox, ModernDatePicker, Button,
  ModernButton@1.0.0, Gallery) and curated it as a hard-error `absent` entry
  on each, so a reintroduction fails the guard instead of only warning. Added
  a dated provenance comment recording the live-compile evidence.
- `scripts/emit_screens.py`: removed all 11 `("TabIndex", "=0")` emissions.
- 12 hand-authored files (`components/cmp_Notification.pa.yaml`,
  `cmp_Dialog.pa.yaml`, `cmp_FilterButton.pa.yaml`, `cmp_Navigation.pa.yaml`,
  `cmp_FieldText.pa.yaml`, `cmp_FieldDate.pa.yaml`, `cmp_FieldNumber.pa.yaml`,
  `cmp_FieldChoice.pa.yaml`, `cmp_CommandBar.pa.yaml`, `cmp_Header.pa.yaml`,
  `templates/FormScreen.pa.yaml`, `templates/ListScreen.pa.yaml`): removed
  every `TabIndex: =0` line (28 lines total). No substitute property added —
  tab order reverts to document order.
- `scripts/check_control_props.py`'s `UNIVERSAL_INSTANCE_PROPS` (the
  fallback allowlist for properties every `CanvasComponent` instance carries
  regardless of its own declared inputs) also carried `TabIndex` on the same
  unverified basis. Removed it there too, with a comment explaining why —
  leaving it would have silently waved the same invalid property through on
  a component instance instead of catching it.
- `references/design-system.md` and `references/component-library.md`:
  corrected prose that had recommended `TabIndex` as deliberate practice.

Remaining `TabIndex` hits after the fix (verified via
`grep -rn "TabIndex" templates/ components/ scripts/ references/`): only
provenance comments, the curated `absent: [...]` entries in
`control-contracts.yaml`, and corrected prose explaining the removal. None is
a control-property assignment. `tests/test_control_props_direct.py` still
uses the literal string `TabIndex` once as an arbitrary property name in a
low-level parser test (`iter_properties`, not contract validity) — untouched,
since it doesn't assert `TabIndex` is a valid property.

## Root cause 2 — control names must be globally unique (7/59 errors)

Power Apps control names are unique across the **whole app**, not scoped to
their own screen or component — a real constraint no guard in this repo knew
about. All four field components (`cmp_FieldText`, `cmp_FieldChoice`,
`cmp_FieldDate`, `cmp_FieldNumber`) declared the same inner names (`con_Field`,
`lbl_Field_Label`, and `txt_Field_Input` shared by Text and Number).

Fixed: renamed each component's inner controls to be unique, consistent with
the task's suggested pattern:

| Component | Container | Label | Input |
|---|---|---|---|
| cmp_FieldText | `con_FieldText` | `lbl_FieldText_Label` | `txt_FieldText_Input` |
| cmp_FieldChoice | `con_FieldChoice` | `lbl_FieldChoice_Label` | `com_FieldChoice_Input` |
| cmp_FieldDate | `con_FieldDate` | `lbl_FieldDate_Label` | `dp_FieldDate_Input` |
| cmp_FieldNumber | `con_FieldNumber` | `lbl_FieldNumber_Label` | `txt_FieldNumber_Input` |

All internal references (formulas, `Output:` bindings, doc comments) were
updated to match.

**Checked the rest of the tree** by walking every `*.pa.yaml` file's control
declarations (the same `RE_ITEM` pattern `iter_properties` already uses) and
diffing names across files:

- `scripts/emit_screens.py`'s generated screens are safe by construction —
  every screen-level control name is entity-derived (`"con_%sList_Main" %
  entity.plural`, etc.), confirmed by generating two apps and scanning their
  full output for duplicates (zero found in both).
- One other cross-file name match exists in the tree:
  `templates/frame-headermainfooter.pa.yaml` and
  `templates/frame-headerrailmain.pa.yaml` both declare `con_Frame_Header`
  and `con_Frame_Main`. **Not a real collision** — these are mutually
  exclusive reference layouts; `scripts/new_app.py`'s `write_frame` copies
  exactly one of them into any given generated app as `Frame.pa.yaml`, so
  they never coexist in one app's tree.
- No same-file duplicate declarations exist anywhere in `components/` or
  `templates/`.

## New guard: duplicate control names

Added `find_duplicate_controls()` to `scripts/check_control_props.py`,
wired into `main()`. It walks every file under `--src` (reusing `RE_ITEM`,
the same declaration-line pattern `iter_properties` already relies on),
tracks the first declaration site of every control name, and emits a hard
error naming both definition sites — matching the compiler's own wording —
on any second declaration anywhere in the app (same file or a different one).

Deliberately scoped to `--src` only (one generated app's tree), not the
skill's own `templates/` library as a whole, because the two frame templates
are legitimate alternatives that are never both part of one app.

Tests added to `tests/test_defect_regression.py`
(`TestDuplicateControlNamesAcrossFiles`, 6 tests): a genuine cross-file
duplicate fails; a genuine same-file duplicate fails; a synthetic
reproduction of the exact pre-fix four-field-component collision fails with
one error per redeclaration; a control name appearing only as a **formula
reference** (`=con_Header.Height`) in another file is correctly NOT flagged
(RE_ITEM only matches declaration lines, never a formula value); the two
alternative frame templates each pass on their own (real usage); and the
shipped, renamed field components have zero cross-file collisions.

Also added `test_tabindex_is_absent_everywhere_live_compile_2026_09_07` to
`tests/test_contracts_wellformed.py` guarding the TabIndex fix.

## Playbook

`references/compile-error-playbook.md`: added a **LIVE (2026-09-07)** row to
the renamed-property table for the exact `TabIndex` error text, and a new
"Duplicate control names" section with the exact `An entity with name ...
already exists` error text — both marked with the real transcript wording
and dated, upgrading the file's sourcing legend to include a `LIVE` tier
above `EXACT`/`PATTERN`.

## Verification

1. `grep -rn "TabIndex" templates/ components/ scripts/ references/` — every
   hit is a comment, curated `absent:` entry, or corrected prose; zero
   control-property assignments remain.
2. `python3 -m unittest discover -s tests` — **233 tests, all green** (226
   baseline + 7 new: 6 duplicate-control-name tests, 1 TabIndex-contract
   test).
3. `python3 scripts/new_app.py --model templates/model.example.yaml --out /tmp/live2`
   — exit 0, all 6 local guards PASS.
4. `python3 scripts/new_app.py --name "Legacy" --brand "#300091" --out /tmp/live3`
   — exit 0, all 6 local guards PASS.
5. Confirmed zero `TabIndex` and zero duplicate control names in both
   generated trees (`find_duplicate_controls()` run directly against each
   output, and `check_control_props.py --src` run directly against each —
   both PASS).

No guard was weakened. Two were strengthened: `TabIndex` moved from
"unverified" (warning-only) to a curated `absent` hard error on 8 controls,
and a brand-new cross-file duplicate-control-name check was added where none
existed before.
