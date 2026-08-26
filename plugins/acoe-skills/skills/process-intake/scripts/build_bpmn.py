#!/usr/bin/env python3
"""
Build a valid, laid-out BPMN 2.0 file from a compact JSON process spec.

Hand-writing BPMN XML is slow and the diagram-interchange (DI) section is where it
always goes wrong: a model without DI opens as a blank canvas in Camunda Modeler, so
the reviewer sees nothing and assumes the work wasn't done. This script takes the
part that needs judgement (what the steps are, who does them, where the process
branches) and does the mechanical part (ids, incoming/outgoing refs, waypoints,
lane bounds) for you.

Usage:
    python build_bpmn.py process.json -o process.bpmn
    python build_bpmn.py process.json -o process.bpmn --check   # validate only

The spec schema is documented in references/bpmn-spec.md. Minimal shape:

{
  "id": "cars_report",
  "name": "CETIN - monthly fleet cost report",
  "pools": [
    {"id": "cetin", "name": "CETIN", "lanes": [
        {"id": "ops", "name": "Transport / Fleet"},
        {"id": "ctrl", "name": "Controlling / BI"}]},
    {"id": "ext", "name": "Leasing companies"}
  ],
  "nodes": [
    {"id": "start", "type": "startEvent", "name": "Month-end close", "lane": "ops", "col": 0},
    {"id": "t1",    "type": "task",       "name": "Extract KOB1",    "lane": "ops", "col": 1, "ts": "8:36"},
    {"id": "g1",    "type": "exclusiveGateway", "name": "Damages?",  "lane": "ops", "col": 2},
    {"id": "t2",    "type": "task", "name": "Run Z1FI", "lane": "ops", "col": 3, "row": 1}
  ],
  "flows": [
    {"from": "start", "to": "t1"},
    {"from": "t1", "to": "g1"},
    {"from": "g1", "to": "t2", "name": "yes"}
  ],
  "messageFlows": [{"from": "extTask", "to": "t1", "name": "invoice files"}]
}

Notes on the two fields that do the layout work:
  col - horizontal position, 0-based. Nodes sharing a col line up vertically.
  row - vertical position *within the lane*, 0-based. row 0 is the main line;
        put exception and rework branches on row 1+ so the happy path stays readable.

"ts" is optional and appends "[8:36]" to the task label, which is how the reviewer
jumps from a box in the diagram back to the moment in the recording that describes it.
"""

import argparse
import json
import sys
from xml.sax.saxutils import escape as _esc


def esc(s):
    return _esc(s or "", {'"': "&quot;", "'": "&apos;"})


# ---------------------------------------------------------------- geometry

TASK_W, TASK_H = 170, 90
GW = 50
EV = 36
COL_W = 200          # horizontal spacing between columns
ROW_H = 210          # vertical spacing between rows inside a lane
LANE_PAD = 30        # padding above the first row in a lane
POOL_LABEL_W = 30    # width of the vertical pool name strip
X0 = 360             # x of column 0 (leaves room for the start event's label)
POOL_GAP = 40

EVENTS = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent"}
GATEWAYS = {"exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway"}
VALID_TYPES = EVENTS | GATEWAYS | {"task", "userTask", "serviceTask", "manualTask",
                                   "scriptTask", "sendTask", "receiveTask", "subProcess"}


def node_size(kind):
    if kind in EVENTS:
        return EV, EV
    if kind in GATEWAYS:
        return GW, GW
    return TASK_W, TASK_H


# ---------------------------------------------------------------- validation

def validate(spec):
    errs = []
    if not spec.get("pools"):
        errs.append("spec has no 'pools'")
    lane_ids, pool_of_lane = set(), {}
    for p in spec.get("pools", []):
        if not p.get("id"):
            errs.append("a pool has no id")
        lanes = p.get("lanes") or [{"id": p.get("id"), "name": p.get("name", "")}]
        for l in lanes:
            if l["id"] in lane_ids:
                errs.append(f"duplicate lane id {l['id']!r}")
            lane_ids.add(l["id"])
            pool_of_lane[l["id"]] = p["id"]

    ids = set()
    for n in spec.get("nodes", []):
        for f in ("id", "type", "lane"):
            if f not in n:
                errs.append(f"node {n.get('id', '?')!r} is missing {f!r}")
        if n.get("id") in ids:
            errs.append(f"duplicate node id {n['id']!r}")
        ids.add(n.get("id"))
        if n.get("type") not in VALID_TYPES:
            errs.append(f"node {n.get('id')!r} has unknown type {n.get('type')!r}")
        if n.get("lane") not in lane_ids:
            errs.append(f"node {n.get('id')!r} references unknown lane {n.get('lane')!r}")
        if "col" not in n:
            errs.append(f"node {n.get('id')!r} has no 'col'")

    lane_of = {n["id"]: n.get("lane") for n in spec.get("nodes", [])}
    for f in spec.get("flows", []):
        for side in ("from", "to"):
            if f.get(side) not in ids:
                errs.append(f"flow {f.get('from')}->{f.get('to')} references unknown node {f.get(side)!r}")
        if f.get("from") in ids and f.get("to") in ids:
            pf, pt = pool_of_lane.get(lane_of[f["from"]]), pool_of_lane.get(lane_of[f["to"]])
            if pf != pt:
                errs.append(
                    f"flow {f['from']}->{f['to']} crosses pools ({pf} -> {pt}). "
                    "BPMN forbids a sequence flow between pools — use messageFlows instead.")
    for m in spec.get("messageFlows", []):
        for side in ("from", "to"):
            if m.get(side) not in ids:
                errs.append(f"messageFlow references unknown node {m.get(side)!r}")

    # Reachability: an orphan node is nearly always a spec typo, not a deliberate choice.
    touched = set()
    for f in spec.get("flows", []):
        touched.add(f.get("from"))
        touched.add(f.get("to"))
    for n in spec.get("nodes", []):
        if n.get("id") not in touched:
            errs.append(f"node {n.get('id')!r} has no sequence flows — orphan")
    return errs


# ---------------------------------------------------------------- build

def build(spec):
    pools = spec["pools"]
    nodes = spec["nodes"]
    flows = spec.get("flows", [])
    mflows = spec.get("messageFlows", [])

    for i, f in enumerate(flows):
        f.setdefault("id", f"flow_{i}_{f['from']}__{f['to']}")
    for i, m in enumerate(mflows):
        m.setdefault("id", f"msg_{i}_{m['from']}__{m['to']}")

    # Label decoration: append the recording timestamp so the diagram is self-documenting.
    for n in nodes:
        if n.get("ts") and n.get("name"):
            n["name"] = f"{n['name']} [{n['ts']}]"

    # ---- lane geometry
    lane_rows = {}
    for n in nodes:
        r = int(n.get("row", 0))
        lane_rows[n["lane"]] = max(lane_rows.get(n["lane"], 0), r)

    lane_geo, pool_geo = {}, {}
    y = 100
    for p in pools:
        lanes = p.get("lanes") or [{"id": p["id"], "name": p.get("name", "")}]
        pool_top = y
        for l in lanes:
            rows = lane_rows.get(l["id"], 0) + 1
            h = LANE_PAD * 2 + rows * ROW_H - (ROW_H - TASK_H) // 2
            lane_geo[l["id"]] = {"y": y, "h": h, "name": l.get("name", "")}
            y += h
        pool_geo[p["id"]] = {"y": pool_top, "h": y - pool_top,
                             "name": p.get("name", ""), "lanes": [l["id"] for l in lanes]}
        y += POOL_GAP

    maxcol = max(n["col"] for n in nodes)
    pool_x = POOL_LABEL_W + 150
    pool_w = X0 + maxcol * COL_W + TASK_W // 2 + 80 - pool_x

    by_id = {n["id"]: n for n in nodes}

    def geom(n):
        w, h = node_size(n["type"])
        cx = X0 + n["col"] * COL_W
        lg = lane_geo[n["lane"]]
        cy = lg["y"] + LANE_PAD + int(n.get("row", 0)) * ROW_H + TASK_H // 2
        return cx - w // 2, cy - h // 2, w, h

    def centre(n):
        x, y_, w, h = geom(n)
        return x + w / 2, y_ + h / 2

    # ---- XML
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
         'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
         'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
         f'id="Definitions_{spec.get("id", "process")}" '
         f'targetNamespace="http://example.org/bpmn/{spec.get("id", "process")}">']

    o.append('  <bpmn:collaboration id="Collab_1">')
    for p in pools:
        o.append(f'    <bpmn:participant id="Pool_{p["id"]}" name="{esc(p.get("name", ""))}" '
                 f'processRef="Proc_{p["id"]}" />')
    for m in mflows:
        nm = f' name="{esc(m.get("name", ""))}"' if m.get("name") else ""
        o.append(f'    <bpmn:messageFlow id="{m["id"]}"{nm} '
                 f'sourceRef="{m["from"]}" targetRef="{m["to"]}" />')
    o.append('  </bpmn:collaboration>')

    for p in pools:
        lanes = p.get("lanes") or [{"id": p["id"], "name": p.get("name", "")}]
        lane_ids = [l["id"] for l in lanes]
        members = [n for n in nodes if n["lane"] in lane_ids]
        mids = {n["id"] for n in members}
        o.append(f'  <bpmn:process id="Proc_{p["id"]}" isExecutable="false">')
        if p.get("lanes"):
            o.append(f'    <bpmn:laneSet id="LaneSet_{p["id"]}">')
            for l in lanes:
                o.append(f'      <bpmn:lane id="Lane_{l["id"]}" name="{esc(l.get("name", ""))}">')
                for n in members:
                    if n["lane"] == l["id"]:
                        o.append(f'        <bpmn:flowNodeRef>{n["id"]}</bpmn:flowNodeRef>')
                o.append('      </bpmn:lane>')
            o.append('    </bpmn:laneSet>')
        for n in members:
            nm = f' name="{esc(n["name"].replace(chr(10), " "))}"' if n.get("name") else ""
            o.append(f'    <bpmn:{n["type"]} id="{n["id"]}"{nm}>')
            for f in flows:
                if f["to"] == n["id"]:
                    o.append(f'      <bpmn:incoming>{f["id"]}</bpmn:incoming>')
            for f in flows:
                if f["from"] == n["id"]:
                    o.append(f'      <bpmn:outgoing>{f["id"]}</bpmn:outgoing>')
            o.append(f'    </bpmn:{n["type"]}>')
        for f in flows:
            if f["from"] in mids and f["to"] in mids:
                nm = f' name="{esc(f.get("name", ""))}"' if f.get("name") else ""
                o.append(f'    <bpmn:sequenceFlow id="{f["id"]}"{nm} '
                         f'sourceRef="{f["from"]}" targetRef="{f["to"]}" />')
        o.append('  </bpmn:process>')

    # ---- DI
    o.append('  <bpmndi:BPMNDiagram id="Diag_1">')
    o.append('    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Collab_1">')

    def shape(el, x, y_, w, h, horiz=False, label=None):
        a = ' isHorizontal="true"' if horiz else ""
        r = [f'      <bpmndi:BPMNShape id="Shape_{el}" bpmnElement="{el}"{a}>',
             f'        <dc:Bounds x="{int(x)}" y="{int(y_)}" width="{int(w)}" height="{int(h)}" />']
        if label:
            r.append('        <bpmndi:BPMNLabel><dc:Bounds '
                     f'x="{int(label[0])}" y="{int(label[1])}" '
                     f'width="{int(label[2])}" height="{int(label[3])}" /></bpmndi:BPMNLabel>')
        r.append('      </bpmndi:BPMNShape>')
        return r

    for p in pools:
        pg = pool_geo[p["id"]]
        o += shape(f'Pool_{p["id"]}', pool_x, pg["y"], pool_w, pg["h"], horiz=True)
        if p.get("lanes"):
            for lid in pg["lanes"]:
                lg = lane_geo[lid]
                o += shape(f"Lane_{lid}", pool_x + POOL_LABEL_W, lg["y"],
                           pool_w - POOL_LABEL_W, lg["h"], horiz=True)

    for n in nodes:
        x, y_, w, h = geom(n)
        lbl = None
        if n["type"] not in {"task", "userTask", "serviceTask", "manualTask",
                             "scriptTask", "sendTask", "receiveTask", "subProcess"} and n.get("name"):
            lbl = (x - 60, y_ + h + 6, 170, 40)
        o += shape(n["id"], x, y_, w, h, label=lbl)

    for f in flows:
        s, t = by_id[f["from"]], by_id[f["to"]]
        sx, sy, sw, sh = geom(s)
        tx, ty, tw, th = geom(t)
        scx, scy = centre(s)
        tcx, tcy = centre(t)
        if abs(scy - tcy) < 1:
            pts = [(sx + sw, scy), (tx, tcy)]
        elif s["type"] in GATEWAYS and tcy > scy:
            pts = [(scx, sy + sh), (scx, tcy), (tx, tcy)]
        elif t["type"] in GATEWAYS and scy > tcy:
            pts = [(sx + sw, scy), (tcx, scy), (tcx, ty + th)]
        elif tcx > scx:
            pts = [(sx + sw, scy), (sx + sw + 40, scy), (sx + sw + 40, tcy), (tx, tcy)]
        else:
            pts = [(scx, sy + sh), (scx, tcy), (tx, tcy)]
        o.append(f'      <bpmndi:BPMNEdge id="Edge_{f["id"]}" bpmnElement="{f["id"]}">')
        for px, py in pts:
            o.append(f'        <di:waypoint x="{int(round(px))}" y="{int(round(py))}" />')
        if f.get("name"):
            mx = (pts[0][0] + pts[-1][0]) / 2
            my = min(p_[1] for p_ in pts) - 18
            o.append('        <bpmndi:BPMNLabel><dc:Bounds '
                     f'x="{int(mx - 60)}" y="{int(my)}" width="120" height="28" /></bpmndi:BPMNLabel>')
        o.append('      </bpmndi:BPMNEdge>')

    for m in mflows:
        s, t = by_id[m["from"]], by_id[m["to"]]
        sx, sy, sw, sh = geom(s)
        tx, ty, tw, th = geom(t)
        scx, tcx = sx + sw / 2, tx + tw / 2
        up = sy > ty
        y_edge = sy if up else sy + sh
        y_mid = y_edge - 40 if up else y_edge + 40
        y_end = ty + th if up else ty
        o.append(f'      <bpmndi:BPMNEdge id="Edge_{m["id"]}" bpmnElement="{m["id"]}">')
        for px, py in [(scx, y_edge), (scx, y_mid), (tcx, y_mid), (tcx, y_end)]:
            o.append(f'        <di:waypoint x="{int(round(px))}" y="{int(round(py))}" />')
        if m.get("name"):
            o.append('        <bpmndi:BPMNLabel><dc:Bounds '
                     f'x="{int(tcx - 75)}" y="{int(y_mid - 30)}" width="150" height="28" /></bpmndi:BPMNLabel>')
        o.append('      </bpmndi:BPMNEdge>')

    o.append('    </bpmndi:BPMNPlane>')
    o.append('  </bpmndi:BPMNDiagram>')
    o.append('</bpmn:definitions>')
    return "\n".join(o), {"nodes": len(nodes), "flows": len(flows),
                          "messageFlows": len(mflows), "width": int(pool_w), "height": int(y)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--check", action="store_true", help="validate the spec and exit")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    errs = validate(spec)
    if errs:
        print("Spec problems:\n  - " + "\n  - ".join(errs), file=sys.stderr)
        sys.exit(1)
    if args.check:
        print(f"spec OK: {len(spec['nodes'])} nodes, {len(spec.get('flows', []))} flows")
        return

    xml, stats = build(spec)
    out = args.out or (args.spec.rsplit(".", 1)[0] + ".bpmn")
    open(out, "w", encoding="utf-8").write(xml)

    # Parse it back — a file that does not parse is worse than no file at all.
    import xml.etree.ElementTree as ET
    ET.parse(out)
    print(f"wrote {out}")
    print(f"  {stats['nodes']} nodes, {stats['flows']} sequence flows, "
          f"{stats['messageFlows']} message flows, canvas {stats['width']}x{stats['height']}")


if __name__ == "__main__":
    main()
