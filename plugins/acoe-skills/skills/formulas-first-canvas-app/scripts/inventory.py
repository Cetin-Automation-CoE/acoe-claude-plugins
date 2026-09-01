#!/usr/bin/env python3
"""Rung 1 of the refactor ladder: a read-only census of a Canvas App's source.

Counts are a proxy for how load-bearing a value is. A colour used 129 times gets a
token named for its role; a colour used once beside a high-count near-twin is a typo.
The census is what tells you which is which BEFORE you start editing.

This script never writes to the source tree.

    python3 inventory.py --src path/to/Src
    python3 inventory.py --src path/to/Src --datasource-pattern 'PP_[A-Za-z]' --out docs/inventory.md
"""
import argparse
import collections
import hashlib
import pathlib
import re
import sys

BEGIN = "DATA ACCESS LAYER — BEGIN"
END = "DATA ACCESS LAYER — END"
# Accept the Czech banners too — this convention started bilingual.
BEGIN_ALT = "DATA ACCESS LAYER — ZAČÁTEK"
END_ALT = "DATA ACCESS LAYER — KONEC"

TYPE_SCALE = {28, 20, 14, 12, 11}


def code_only(line: str) -> str:
    """Drop quoted strings and // comments so only live code remains.

    Prose is not coupling: a list name in a comment or a UI label is documentation.
    """
    line = re.sub(r'"[^"]*"', '""', line)
    return re.sub(r"//.*$", "", line)


BLOCK_KEY = re.compile(r"^(\s*)(?:-\s+)?[\w'\"][\w'\" .]*:\s*\|-?\s*$")
INLINE_KEY = re.compile(r"^(\s*)(?:-\s+)?[\w'\"][\w'\" .]*:\s*(=.+)$")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _property_values(lines):
    """Yield each property's value text, block scalars bounded by indentation."""
    i = 0
    while i < len(lines):
        line = lines[i]
        m = BLOCK_KEY.match(line)
        if m:
            key_indent = _indent(line)
            body, i = [], i + 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and _indent(nxt) <= key_indent:
                    break
                body.append(nxt)
                i += 1
            yield "\n".join(body)
            continue
        m = INLINE_KEY.match(line)
        if m:
            yield m.group(2)
        i += 1


def table(rows, headers):
    if not rows:
        return "| " + " | ".join(headers) + " |\n|" + "|".join(["---"] * len(headers)) + "|\n| _none_ |" + " |" * (len(headers) - 1) + "\n"
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="path to the unpacked Src/ directory")
    ap.add_argument("--datasource-pattern", default=None,
                    help="regex matching your data source names, e.g. 'PP_[A-Za-z]' or 'MyList|OtherList'")
    ap.add_argument("--out", default=None, help="write markdown here instead of stdout")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit(f"error: --src is not a directory: {src}")
    files = sorted(src.rglob("*.pa.yaml"))
    if not files:
        sys.exit(f"error: no .pa.yaml files under {src}")

    app_file = next((f for f in files if f.name == "App.pa.yaml"), None)

    colours = collections.Counter()
    sizes = collections.Counter()
    spacing = collections.Counter()
    ds_refs = []
    switches = collections.Counter()
    switch_sites = collections.defaultdict(set)
    per_screen = []
    bodies = collections.defaultdict(list)

    ds_re = re.compile(args.datasource_pattern) if args.datasource_pattern else None

    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        in_layer = False
        controls = 0

        for ln, raw in enumerate(lines, 1):
            if f == app_file:
                if BEGIN in raw or BEGIN_ALT in raw:
                    in_layer = True
                if END in raw or END_ALT in raw:
                    in_layer = False

            if "Control: " in raw:
                controls += 1

            code = code_only(raw)

            # Colours are counted everywhere except inside App.pa.yaml, whose
            # Formulas block IS the token region by definition.
            if f != app_file:
                for m in re.finditer(r"RGBA\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*\)", code):
                    colours[re.sub(r"\s+", "", m.group(0))] += 1
                for m in re.finditer(r"ColorValue\(\s*\"(#[0-9A-Fa-f]{3,8})\"\s*\)", raw):
                    colours[m.group(1).upper()] += 1

            for m in re.finditer(r"\b(?:Size|FontSize)\s*:\s*=\s*([\d.]+)\b", code):
                sizes[float(m.group(1))] += 1
            for m in re.finditer(r"\b(?:Padding\w*|LayoutGap|Gap)\s*:\s*=\s*([\d.]+)\b", code):
                spacing[float(m.group(1))] += 1

            if ds_re and not in_layer and ds_re.search(code):
                ds_refs.append((f.name, ln, raw.strip()[:90]))

            for m in re.finditer(r"Switch\(\s*([A-Za-z_][\w.]*)", code):
                switches[m.group(1)] += 1
                switch_sites[m.group(1)].add(f.name)

        per_screen.append((f.name, controls, len(lines)))

        # Duplicated formula bodies. Bounded by INDENTATION, not by regex: a
        # block scalar ends at the first line indented no deeper than its key.
        # (A regex like (?:\s+.*\n)+ runs away and swallows the rest of the file.)
        for body in _property_values(lines):
            body = re.sub(r"//.*$", "", body, flags=re.M)
            body = re.sub(r"\s+", " ", body).strip().lstrip("=").strip()
            if len(body) >= 60:
                bodies[hashlib.sha1(body.encode()).hexdigest()].append((f.name, body))

    dupes = [(v[0][1][:70].replace("|", "\\|"), len(v), ", ".join(sorted({n for n, _ in v})))
             for v in bodies.values() if len(v) >= 2]
    dupes.sort(key=lambda r: -r[1])

    def fmt_num(x):
        return int(x) if float(x).is_integer() else x

    md = []
    md.append(f"# Design & structure inventory\n")
    md.append(f"**Source:** `{src}` ({len(files)} `.pa.yaml` files)  ")
    md.append("**Rung 1 — read-only. No file was modified.**\n")
    md.append("Counts are occurrences in source, a proxy for how load-bearing each value is.\n")

    md.append("\n## Colour literals outside App.pa.yaml\n")
    md.append(table([(c, n, "") for c, n in colours.most_common()],
                    ["Value", "Uses", "Verdict"]))
    md.append("\nVerdict: `→ constXxx` (fold) · `keep + exempt` (component without "
              "`AccessAppScope` — record the reason) · `delete` (drift).\n")

    md.append("\n## Font sizes\n")
    md.append(table([(fmt_num(s), n, "yes" if s in TYPE_SCALE else "**no**")
                     for s, n in sorted(sizes.items(), key=lambda kv: -kv[1])],
                    ["Size", "Uses", "In scale (28/20/14/12/11)?"]))

    md.append("\n## Spacing values\n")
    md.append(table([(fmt_num(s), n, "yes" if float(s) % 4 == 0 else "**no**")
                     for s, n in sorted(spacing.items(), key=lambda kv: -kv[1])],
                    ["Value", "Uses", "On 4px grid?"]))

    if ds_re:
        md.append("\n## Data-source references outside the data-access region\n")
        md.append(table(ds_refs, ["File", "Line", "Code"]))
        md.append("\nEvery row is rung-4 work: this number is how expensive a backend "
                  "change currently is.\n")

    md.append("\n## Duplicated formula bodies (2+ occurrences)\n")
    md.append(table(dupes, ["Body (truncated)", "Occurrences", "Files"]))
    md.append("\nTwo occurrences is the trigger to extract, not three: retrofitting costs "
              "roughly ten times what extracting on the spot does.\n")

    md.append("\n## Switch discriminators\n")
    md.append(table([(d, n, ", ".join(sorted(switch_sites[d])))
                     for d, n in switches.most_common() if n >= 2],
                    ["Discriminator", "Uses", "Files"]))
    md.append("\nA discriminator branched on in several places is a registry that has "
              "not been written yet.\n")

    md.append("\n## Size per file\n")
    md.append(table(sorted(per_screen, key=lambda r: -r[2]), ["File", "Controls", "Lines"]))

    out = "\n".join(md)
    if args.out:
        pathlib.Path(args.out).write_text(out, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(out)

    print(f"\n--- summary ---\n"
          f"colour literals outside App.pa.yaml: {sum(colours.values())} "
          f"({len(colours)} distinct)\n"
          f"font sizes off the scale: {sum(n for s, n in sizes.items() if s not in TYPE_SCALE)}\n"
          f"spacing values off the 4px grid: {sum(n for s, n in spacing.items() if float(s) % 4)}\n"
          f"data-source refs outside the layer: {len(ds_refs)}\n"
          f"duplicated formula bodies (2+): {len(dupes)}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
