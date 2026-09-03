# Power Fx limits, engine differences, and the errors they produce

Confirmed against the strict Power Fx engine in the Canvas Authoring coauthoring
service. Each entry pairs the limit with the error text it produces, because several of
these report at a location far from the cause.

## User-defined functions

| Limit | Error you actually see | Do this instead |
|---|---|---|
| Cannot declare `Table` as a return type | Declaration: `Unknown type Table`. Then **every call site**: `'funcX' is an unknown or unsupported function` | Use a named formula. They return tables fine. |
| Record parameters are unreliable | Varies; often a resolution failure at the call | Stage the record in a global the UDF reads (`glFormDraft`). |
| Cannot read `Set()` globals reliably | — | Named formulas *can* read globals; move the derivation there. |
| Side effects need `: Void` | `Behavior function in a non-behavior property` | Declare `funcX(): Void =` and wrap the body in `{ … }`. |
| Scalar params are fine | — | Ten-plus scalar parameters work. Verbose but reliable. |

**Why the `Table` return type misleads.** The declaration error and the call-site errors
look unrelated: you get N reports of "unknown function" across screens and none of them
points at the declaration. Whenever a `func*` reports as unknown at every call site,
read its **declaration**, not its calls.

## Named formulas

- **Can** return tables.
- **Can** read `Set()` globals — this is the supported way to make a derived view react
  to app state.
- Are pure: no `Set`, `Collect`, `Patch`, `Notify`. Side effects belong in a `Void` UDF.
- Cannot forward-reference another named formula *in the studio binder* (see
  `app-formulas-layout.md`). The compile service tolerates it; the binder does not, and
  the binder is what your user's studio tab runs.

## Collections vs named formulas

A table that is never mutated belongs in a named formula. The app checker flags the
alternative as `CollectingReadOnlyTable` and it is correct — collections cost startup
time and lose type fidelity at the boundary.

Collections that *are* mutated need a **typed seed**: Power Fx cannot infer a schema
from an empty collection, and named formulas built over an unseeded one fail with
"no type found". Seed with one fully typed row, then clear:

```
ClearCollect(colSorts, Table({Table: "", ID: "", SortOrder: ""}));
Clear(colSorts);
```

The same applies to any global a UDF reads: `Set()` it to a fully typed record at
`OnStart`. `Set(glFormDraft, Blank())` gives it no type at all.

## Components

- **`AccessAppScope: true` or the component is an island.** Without it, `Set(glX, …)`
  inside the component creates a *component-scoped* `glX` disjoint from the app global
  of the same name. Both exist, neither sees the other, and every app-side write is a
  dead store that raises no error. Symptom: a value that "won't update" in one
  direction only.
- Without app scope the component also cannot read `constStyle`. Pass tokens in as input
  properties, or flip the flag.
- **Whole-record output resolution.** The strict engine resolves a component's Record
  output as a unit. Reading one field bare (`flt.List`) forces resolution of every
  sibling; if a sibling reaches back into the collection currently being defined, that
  is a type cycle — the collection collapses to `Error` and hundreds of unrelated errors
  cascade app-wide.

  Anchor every field with a fixed-return projection so the record never needs resolving:

  ```
  // scalars
  Text(flt.Title), Value(flt.Count), If(flt.Mode = "asc", SortOrder.Ascending, …)

  // tables — JSON() accepts the unresolved lambda value; Text(l.Value) does NOT
  ForAll(flt.List As l, {Value: Substitute(JSON(l.Value), Char(34), "")})
  ```

  The reverse direction (`{List: LookUp(colFilters, ID = …).List}`) is safe once the
  collection itself is anchored — resolution is then acyclic.

## Function signature oddities

| Function | Gotcha |
|---|---|
| `Ungroup(t, Rows)` | Column is an **identifier**. `Ungroup(t, "Rows")` fails: `Expected identifier name` plus `Ungroup has some invalid arguments`. |
| `SortByColumns(t, "Col", …)` | Still takes **quoted strings**, and they are never validated. A typo compiles green and sorts by nothing. |
| `Text(n, "[$-cs-CZ]#,##0")` | Locale formats render decimals unexpectedly. Use `[$-en-US]` for deterministic output. |
| `Text(n, "0.0%")` | Power Fx treats `%` as a **literal** — no ×100. Multiply explicitly. |

## Engine differences — three engines, three verdicts

| Engine | Strictness | Notes |
|---|---|---|
| `compile_canvas` | Strictest | Pushes local YAML into the session **before** validating. Needs the studio tab open. |
| `get_appchecker_errors` | Laxer | Different rule set; catches accessibility and performance findings compile ignores. Compare both. |
| Studio document-server binder | Different again | The forward-reference limitation. Only visible in the user's studio, not in your tooling. |

**What compile catches:** unknown control properties, unknown functions, bad UDF return
types. The commonest property trap is the two text generations: `Control: Text`
(previous-generation modern) takes `FontColor`, `Weight` and `'TextCanvas.Align'.Start`;
`Control: ModernText` takes `Color`, `FontWeight` and `Align.Left`. `Button` in this
skill is the previous-generation modern button (`'ButtonCanvas.*'` enums, `FontColor`,
`BorderRadius`, no `Fill`).

**What compile misses:** every column referenced off a collection, every
`SortByColumns` string, every arithmetic sign. Hence the guard scripts.

## Two `pac` commands that will waste your afternoon

Both look like exactly what you want. Neither works (checked against pac 2.4.1
and a live, published, working app):

- **`pac canvas validate -d <dir>`** reports **every** file of a working app as
  `Invalid` — screens, components, `App.pa.yaml`, even `_EditorState.pa.yaml`.
  Its bundled schema wants `Control:` on a `ComponentDefinitions` entry, while
  real unpacked apps carry `DefinitionType: CanvasComponent`. The schema is
  skewed against the current MSApp structure version, so a failure here tells
  you nothing about your source.
- **`pac canvas pack --sources <dir> --msapp <file>`** is deprecated *and* dies
  with an unhandled `System.Text.Json.JsonException` on a real unpacked app.

**Consequence:** there is no offline compile and no local path to an importable
`.msapp`. The only validator that reflects reality is `compile_canvas` against a
live coauthoring session, which is why the guard scripts in this skill exist —
they cover statically what you would otherwise only learn at runtime.

## Session mechanics that look like tool failures

- **Closed studio tab** → `compile_canvas` does not error. It hangs until the MCP idle
  timeout (1800s) and aborts. A long silent stall is a closed tab, not broken auth.
- **Reloaded studio tab** → a *new* coauthoring session is created. The MCP connection
  keeps talking to the orphaned one: compile still passes, sync still round-trips your
  own pushes, and none of it reaches the user's app. Symptom: their screenshots stop
  reflecting your changes while every tool says green. Fix: `connect` again, then
  compile. **Do not `sync_canvas` first** — the new session holds the stale document and
  would clobber local files.
- **Stale tab clobber** → a tab holding an older in-memory document can write its state
  back over your push. Symptom: `sync_canvas` pulls a diff that is exactly your last
  commit reversed. Recovery: `git checkout`, re-push, then have the user reload the tab
  before touching anything.
