#!/usr/bin/env python3
"""
Draft a data model in DBML and render it as an ER diagram.

DBML (dbdiagram.io's language) is the right format for a target data model in an
automation intake: it is readable in a pull request, it pastes straight into
dbdiagram.io for a shared visual, and it converts to real DDL for whichever database
the CoE picks. The one thing it does not give you offline is a picture -- which is
exactly what a stakeholder wants to see. This script closes that gap.

What it does:
  1. Parses the .dbml (a pure-Python parser -- no install needed for the common subset)
  2. Emits Graphviz DOT, styled in CETIN brand colours
  3. Renders SVG/PNG if Graphviz `dot` is on the PATH
  4. Optionally emits DDL via @dbml/cli if that is installed

Usage:
    python build_dbml_diagram.py model.dbml                     # -> model.dot, model.svg
    python build_dbml_diagram.py model.dbml --format png
    python build_dbml_diagram.py model.dbml --sql postgres      # -> model.sql (needs @dbml/cli)
    python build_dbml_diagram.py model.dbml --check             # parse and report only

Neither Graphviz nor @dbml/cli is required to parse and validate; the script degrades
to writing the .dot file and telling you what is missing. The .dbml itself always
remains the primary deliverable -- paste it into https://dbdiagram.io to get the
interactive version.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

# CETIN brand (see references/cetin-brand.md)
BLUE = "#300091"
RED = "#f12e49"
LIGHTBLUE = "#41b6e6"
GREY = "#c7c9c7"
BG = "#f5f6fa"
INK = "#1a1346"


# ---------------------------------------------------------------- parsing

def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", l) for l in text.split("\n"))


def split_blocks(text):
    """Yield (header, body) for every top-level `header { ... }` block, plus bare lines."""
    blocks, bare, i, n = [], [], 0, len(text)
    while i < n:
        b = text.find("{", i)
        if b == -1:
            bare.extend(text[i:].split("\n"))
            break
        nl = text.rfind("\n", i, b)
        header_start = i if nl == -1 else nl + 1
        bare.extend(text[i:header_start].split("\n"))
        header = text[header_start:b].strip()
        depth, j = 1, b + 1
        while j < n and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        blocks.append((header, text[b + 1:j - 1]))
        i = j
    return blocks, [l.strip() for l in bare if l.strip()]


REL = {">": "many-to-one", "<": "one-to-many", "-": "one-to-one", "<>": "many-to-many"}


def parse_ref(expr, default_from=None):
    """'posts.user_id > users.id' -> dict. Also handles inline '> users.id'."""
    m = re.match(r"^\s*(?P<a>[\w\".]+)?\s*(?P<op><>|[<>-])\s*(?P<b>[\w\".]+)\s*$", expr)
    if not m:
        return None
    a = m.group("a") or default_from
    if not a:
        return None
    def split(ref):
        parts = [p.strip('"') for p in ref.split(".")]
        return (parts[-2], parts[-1]) if len(parts) >= 2 else (None, parts[-1])
    ft, fc = split(a)
    tt, tc = split(m.group("b"))
    return {"from_table": ft, "from_col": fc, "to_table": tt, "to_col": tc,
            "op": m.group("op"), "kind": REL.get(m.group("op"), "?")}


def parse_dbml(text):
    text = strip_comments(text)
    blocks, bare = split_blocks(text)
    model = {"project": None, "tables": [], "refs": [], "enums": [], "groups": []}

    for line in bare:
        if line.lower().startswith("ref"):
            m = re.match(r"^[Rr]ef\s*[\w\"]*\s*:\s*(.+)$", line)
            if m:
                r = parse_ref(m.group(1))
                if r:
                    model["refs"].append(r)

    for header, body in blocks:
        h = header.strip()
        hl = h.lower()

        if hl.startswith("project"):
            model["project"] = h.split(None, 1)[1].strip() if " " in h else "project"
            continue

        if hl.startswith("enum"):
            name = h.split(None, 1)[1].strip().strip('"') if " " in h else "enum"
            vals = [re.split(r"[\s\[]", l.strip())[0]
                    for l in body.split("\n") if l.strip() and "{" not in l]
            model["enums"].append({"name": name, "values": [v for v in vals if v]})
            continue

        if hl.startswith("tablegroup"):
            name = h.split(None, 1)[1].strip() if " " in h else "group"
            model["groups"].append({"name": name,
                                    "tables": [l.strip() for l in body.split("\n") if l.strip()]})
            continue

        if hl.startswith("ref"):
            for l in body.split("\n"):
                if l.strip():
                    r = parse_ref(l.strip())
                    if r:
                        model["refs"].append(r)
            continue

        if hl.startswith("table"):
            rest = h[5:].strip()
            m = re.match(r'^"?([\w.]+)"?(?:\s+as\s+(\w+))?', rest)
            if not m:
                continue
            tname = m.group(1).split(".")[-1]
            table = {"name": tname, "alias": m.group(2), "columns": [], "note": None,
                     "indexes": []}

            inner_blocks, inner_lines = split_blocks(body)
            for ih, ib in inner_blocks:
                if ih.strip().lower().startswith("indexes"):
                    table["indexes"] = [l.strip() for l in ib.split("\n") if l.strip()]

            for line in inner_lines:
                if not line or line.startswith("}"):
                    continue
                if line.lower().startswith("note"):
                    nm = re.search(r"['\"](.+?)['\"]", line, re.S)
                    if nm:
                        table["note"] = nm.group(1)
                    continue
                cm = re.match(r'^"?(?P<name>[\w]+)"?\s+(?P<type>[\w]+(?:\([^)]*\))?)'
                              r'(?:\s*\[(?P<settings>.*)\])?\s*$', line)
                if not cm:
                    continue
                settings = cm.group("settings") or ""
                col = {
                    "name": cm.group("name"),
                    "type": cm.group("type"),
                    "pk": bool(re.search(r"\b(pk|primary key)\b", settings, re.I)),
                    "unique": bool(re.search(r"\bunique\b", settings, re.I)),
                    "not_null": bool(re.search(r"\bnot null\b", settings, re.I)),
                    "increment": bool(re.search(r"\bincrement\b", settings, re.I)),
                }
                rm = re.search(r"\bref\s*:\s*([<>-]{1,2}\s*[\w\".]+)", settings, re.I)
                if rm:
                    r = parse_ref(rm.group(1), default_from=f"{tname}.{col['name']}")
                    if r:
                        model["refs"].append(r)
                        col["fk"] = True
                nm = re.search(r"note\s*:\s*['\"](.+?)['\"]", settings, re.I)
                if nm:
                    col["note"] = nm.group(1)
                table["columns"].append(col)
            model["tables"].append(table)

    # Resolve aliases used in refs back to real table names.
    alias = {t["alias"]: t["name"] for t in model["tables"] if t.get("alias")}
    for r in model["refs"]:
        r["from_table"] = alias.get(r["from_table"], r["from_table"])
        r["to_table"] = alias.get(r["to_table"], r["to_table"])
    return model


def validate(model):
    warns = []
    names = {t["name"] for t in model["tables"]}
    if not names:
        warns.append("no tables parsed — check the file is DBML")
    for t in model["tables"]:
        if not any(c["pk"] for c in t["columns"]):
            warns.append(f"table '{t['name']}' has no primary key")
        if not t["columns"]:
            warns.append(f"table '{t['name']}' has no columns")
    for r in model["refs"]:
        for side in ("from_table", "to_table"):
            if r[side] and r[side] not in names:
                warns.append(f"ref {r['from_table']}.{r['from_col']} -> "
                             f"{r['to_table']}.{r['to_col']} references unknown table "
                             f"'{r[side]}'")
    linked = {r["from_table"] for r in model["refs"]} | {r["to_table"] for r in model["refs"]}
    for t in model["tables"]:
        if len(names) > 1 and t["name"] not in linked:
            warns.append(f"table '{t['name']}' has no relationships — intentional?")
    return warns


# ---------------------------------------------------------------- rendering

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


HEADS = {">": ("none", "crow"), "<": ("crow", "none"),
         "-": ("none", "none"), "<>": ("crow", "crow")}


def to_dot(model, title=None):
    o = ["digraph ERD {",
         '  graph [rankdir=LR, splines=spline, nodesep=0.55, ranksep=1.1, '
         f'bgcolor="white", fontname="Arial", labelloc="t", fontsize=16, '
         f'fontcolor="{INK}"' + (f', label="{esc(title)}\\n "' if title else "") + "];",
         '  node  [shape=plaintext, fontname="Arial"];',
         f'  edge  [color="{GREY}", penwidth=1.2, arrowsize=0.9, fontname="Arial", '
         'fontsize=9, fontcolor="#66678a"];']

    for t in model["tables"]:
        rows = [
            f'<TR><TD BGCOLOR="{BLUE}" ALIGN="LEFT" COLSPAN="3">'
            f'<FONT COLOR="white" POINT-SIZE="12"><B>  {esc(t["name"].upper())}  </B></FONT>'
            f'</TD></TR>'
        ]
        for c in t["columns"]:
            marks = []
            if c["pk"]:
                marks.append(f'<FONT COLOR="{RED}"><B>PK</B></FONT>')
            if c.get("fk"):
                marks.append(f'<FONT COLOR="{LIGHTBLUE}"><B>FK</B></FONT>')
            if c["unique"] and not c["pk"]:
                marks.append('<FONT COLOR="#66678a">U</FONT>')
            mark = " ".join(marks) or " "
            name = esc(c["name"])
            if c["pk"]:
                name = f"<B>{name}</B>"
            nn = "" if c["not_null"] or c["pk"] else '<FONT COLOR="#9aa0b0"> ?</FONT>'
            rows.append(
                f'<TR><TD ALIGN="LEFT" PORT="{esc(c["name"])}">  {name}{nn}  </TD>'
                f'<TD ALIGN="LEFT"><FONT COLOR="#66678a" POINT-SIZE="10">'
                f'{esc(c["type"])}  </FONT></TD>'
                f'<TD ALIGN="RIGHT"><FONT POINT-SIZE="9">{mark}  </FONT></TD></TR>')
        if t.get("note"):
            rows.append(f'<TR><TD COLSPAN="3" ALIGN="LEFT" BGCOLOR="{BG}">'
                        f'<FONT POINT-SIZE="9" COLOR="#66678a">  {esc(t["note"])[:70]}  </FONT>'
                        f'</TD></TR>')
        label = ('<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" '
                 f'COLOR="{GREY}" BGCOLOR="white">' + "".join(rows) + "</TABLE>>")
        o.append(f'  "{t["name"]}" [label={label}];')

    for r in model["refs"]:
        if not (r["from_table"] and r["to_table"]):
            continue
        tail, head = HEADS.get(r["op"], ("none", "crow"))
        o.append(f'  "{r["from_table"]}":"{r["from_col"]}" -> '
                 f'"{r["to_table"]}":"{r["to_col"]}" '
                 f'[arrowtail={tail}, arrowhead={head}, dir=both];')
    o.append("}")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dbml")
    ap.add_argument("-o", "--out", default=None, help="output basename (default: input name)")
    ap.add_argument("--format", default="svg", choices=["svg", "png", "pdf"])
    ap.add_argument("--sql", default=None,
                    choices=["postgres", "mysql", "mssql", "oracle"],
                    help="also emit DDL (requires @dbml/cli)")
    ap.add_argument("--check", action="store_true", help="parse and validate only")
    args = ap.parse_args()

    text = open(args.dbml, encoding="utf-8").read()
    model = parse_dbml(text)
    warns = validate(model)

    print(f"parsed: {len(model['tables'])} tables, {len(model['refs'])} relationships, "
          f"{len(model['enums'])} enums")
    for t in model["tables"]:
        print(f"  {t['name']:<28} {len(t['columns'])} cols")
    if warns:
        print("\nwarnings:")
        for w in warns:
            print(f"  ! {w}")
    if args.check:
        return

    base = args.out or os.path.splitext(args.dbml)[0]
    dot_path = base + ".dot"
    open(dot_path, "w", encoding="utf-8").write(to_dot(model, model.get("project")))
    print(f"\nwrote {dot_path}")

    if shutil.which("dot"):
        out = f"{base}.{args.format}"
        subprocess.run(["dot", f"-T{args.format}", dot_path, "-o", out], check=True)
        print(f"wrote {out}")
    else:
        print("! Graphviz 'dot' not found — install graphviz to render, or paste the "
              ".dbml into https://dbdiagram.io")

    if args.sql:
        if shutil.which("dbml2sql"):
            out = base + ".sql"
            with open(out, "w", encoding="utf-8") as fh:
                subprocess.run(["dbml2sql", args.dbml, "--" + args.sql],
                               stdout=fh, check=True)
            print(f"wrote {out}")
        else:
            print("! dbml2sql not found — `npm install -g @dbml/cli` to emit DDL")

    print("\nThe .dbml file is the deliverable to share: paste it into "
          "https://dbdiagram.io for the interactive diagram.")


if __name__ == "__main__":
    main()
