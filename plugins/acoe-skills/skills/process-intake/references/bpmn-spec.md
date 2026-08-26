# process.json — spec format for `scripts/build_bpmn.py`

You write this file; the script turns it into valid BPMN 2.0 with diagram interchange,
so the model opens as a drawn diagram in Camunda Modeler / bpmn.io rather than a blank
canvas. Run `python scripts/build_bpmn.py process.json --check` first — it catches
orphan nodes, unknown ids and cross-pool sequence flows before you waste time on layout.

A complete worked example is in `references/example-process.json` (the CETIN fleet
report). Read it if you want to see the conventions in practice rather than in prose.

## Top level

```json
{
  "id": "short_slug",
  "name": "Human-readable process name",
  "pools": [...],
  "nodes": [...],
  "flows": [...],
  "messageFlows": [...]
}
```

## pools

A pool is an organisation or system boundary. Lanes divide a pool by role.

```json
"pools": [
  {"id": "cetin", "name": "CETIN — monthly fleet cost report",
   "lanes": [{"id": "ops",  "name": "Transport / Fleet — process owner"},
             {"id": "ctrl", "name": "Controlling / BI"}]},
  {"id": "ext", "name": "Leasing companies (Arval, Business Lease, Ayvens)"}
]
```

A pool without `lanes` becomes a single implicit lane addressed by the pool's own id.
Use that for external parties — you rarely know or care how they organise internally.

**Put external parties in their own pool, not a lane.** A lane means "someone inside our
boundary whose work we can change". A supplier who e-mails you a spreadsheet is not that,
and drawing them as a lane quietly implies the automation project can redesign their
process. It usually can't, and that distinction is exactly what the reader needs to see.

## nodes

```json
{"id": "kob1", "type": "task", "name": "Extract line items (KOB1)",
 "lane": "ops", "col": 1, "row": 0, "ts": "8:36"}
```

| Field  | Required | Meaning |
|---|---|---|
| `id`   | yes | unique, referenced by flows |
| `type` | yes | `startEvent`, `endEvent`, `task`, `userTask`, `serviceTask`, `manualTask`, `exclusiveGateway`, `parallelGateway`, `subProcess`, … |
| `name` | usually | the label. Gateways read best as a question ("Vehicle found?") |
| `lane` | yes | lane id, or pool id for a pool with no lanes |
| `col`  | yes | horizontal position, 0-based. Same col = vertically aligned |
| `row`  | no (default 0) | vertical position **within the lane**, 0-based |
| `ts`   | no | recording timestamp; appended to the label as `[8:36]` |

### The layout convention that makes the diagram readable

**Row 0 is the happy path. Exceptions and rework drop to row 1.** A reader should be able
to trace the main line straight across without their eye leaving the top row, then look
down to see what goes wrong and how it gets fixed. If you scatter exception handling
along the main line, the diagram technically documents the process but nobody can see
its shape — which defeats the point of drawing it.

Columns are cheap; leave gaps where a branch needs room. A diagram 30 columns wide is
completely normal for a real process and modellers scroll horizontally without complaint.

### Always set `ts`

The timestamp is what makes the model auditable. A reviewer who doubts a box can jump to
that moment in the recording and check, instead of taking your reconstruction on faith.
Use `~` for a position inferred from content inside a long monologue (`"~11:38"`), which
signals honestly that the marker is approximate.

## flows

```json
{"from": "g_dmg", "to": "z1fi", "name": "yes"}
```

Name every branch out of an exclusive gateway (`yes` / `no` / `no — future period`).
An unnamed branch is a decision the reader can't reconstruct.

**Every gateway that splits must be joined.** Model the join as a second gateway of the
same type. It costs one node and keeps the model structurally valid.

Sequence flows may never cross pool boundaries — the validator rejects this. Use a
message flow instead.

## messageFlows

```json
{"from": "lsend", "to": "recv", "name": "invoice Excel + data records"}
```

For anything crossing a pool boundary: an e-mail, a file drop, a portal upload. Name it
with *what actually moves*, since in an automation intake the artefact is the thing the
robot will have to receive.

## Sizing

25–45 nodes is the useful range for a walkthrough of a single process. Below ~15 you have
probably collapsed real steps that carry exceptions; above ~50 the diagram stops being
readable and the extra detail belongs in the written analysis instead.

Model what the person actually does, not what the tidy version would be. If they export
to Excel, re-import, and export again because a row limit forces it, that round trip is a
step — and it is very often exactly the step automation removes.
