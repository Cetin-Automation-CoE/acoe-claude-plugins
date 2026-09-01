#!/usr/bin/env python3
"""Guard: every column referenced off a collection actually exists on it.

compile_canvas does NOT type-check collection column references. A gallery bound to
Filter(colItems, ...) reading ThisItem.Year compiles clean and fails at runtime;
SortByColumns(..., "Year", ...) string column names are never validated at all.
This script closes that gap — it is the reason a green compile is necessary but not
sufficient.

Schemas are inferred from the seed record literals in App.pa.yaml (ClearCollect /
Collect for collections, `name = Table(...)` for read-only named formulas), which is
exactly where the formulas-first layout puts them.

    python3 check_collection_columns.py --src path/to/Src
    python3 check_collection_columns.py --src path/to/Src --names colItems,colNotes

Exits non-zero on violation.
"""
import argparse
import pathlib
import re
import sys

# Row-scope names that are never collection columns.
SCOPE_WORDS = {"ThisItem", "ThisRecord", "Parent", "Self", "App", "Value", "As"}


def balanced(text: str, open_idx: int) -> str:
    """Return the substring from an opening paren to its matching close."""
    depth = 0
    for k in range(open_idx, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx:k + 1]
    return text[open_idx:]


def record_keys(body: str) -> set:
    """Union of keys across every record literal `{...}` in body, depth 1 only."""
    cols, depth, cur = set(), 0, ""
    for ch in body:
        if ch == "{":
            depth += 1
            if depth == 1:
                cur = ""
                continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                cols |= set(re.findall(r"(\w+)\s*:", cur))
                continue
        if depth >= 1:
            cur += ch
    return cols


def discover(app_text: str):
    """Find every collection / table-valued named formula and its columns."""
    schemas = {}
    patterns = [
        r"(?:ClearCollect|Collect)\(\s*\n?\s*(col\w+)\s*,",   # collections
        r"^\s*(const\w+)\s*=\s*\n?\s*Table\(",                 # read-only tables
    ]
    for pat in patterns:
        for m in re.finditer(pat, app_text, re.M):
            name = m.group(1)
            body = balanced(app_text, app_text.index("(", m.start()))
            cols = record_keys(body)
            if cols:
                schemas.setdefault(name, set()).update(cols)
    return schemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--names", default=None,
                    help="comma-separated collections to check (default: all discovered)")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-collection column summary")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit(f"error: --src is not a directory: {src}")
    app = src / "App.pa.yaml"
    if not app.exists():
        sys.exit("error: no App.pa.yaml found — is --src the unpacked Src/ directory?")

    schemas = discover(app.read_text(encoding="utf-8", errors="replace"))
    if args.names:
        wanted = {n.strip() for n in args.names.split(",") if n.strip()}
        missing = wanted - set(schemas)
        for n in sorted(missing):
            print(f"WARN: no seed literal found for {n} — cannot check it", file=sys.stderr)
        schemas = {k: v for k, v in schemas.items() if k in wanted}

    if not schemas:
        print("WARN: no collection schemas discovered; nothing checked.", file=sys.stderr)
        print("      Seed collections with one fully typed row so a schema exists.", file=sys.stderr)
        return

    bad = []
    for f in sorted(src.rglob("*.pa.yaml")):
        for ln, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            # Filter/LookUp/RemoveIf/UpdateIf(colX, <Column> ...)
            # The (?!\s*\() guard matters: Filter(constX, funcCanWrite(Value)) has a
            # FUNCTION CALL as its predicate, not a column reference.
            for m in re.finditer(r"\b(?:Filter|LookUp|RemoveIf|UpdateIf)\(\s*((?:col|const)\w+)\s*,\s*([A-Za-z_]\w*)(?!\w)(?!\s*\()", line):
                col, ref = m.group(1), m.group(2)
                if col in schemas and ref not in schemas[col] and ref not in SCOPE_WORDS:
                    bad.append((f.relative_to(src), ln, col, ref, line.strip()[:80]))
            # SortByColumns(<expr over colX>, "Column", ...) — never validated by compile
            for m in re.finditer(r'SortByColumns\(\s*(?:\w+\()*\s*((?:col|const)\w+)[^)]*?\)?\s*,\s*"(\w+)"', line):
                col, ref = m.group(1), m.group(2)
                if col in schemas and ref not in schemas[col]:
                    bad.append((f.relative_to(src), ln, col, ref, line.strip()[:80]))

    if bad:
        print(f"FAIL: {len(bad)} reference(s) to columns that do not exist on the collection\n")
        for fn, ln, col, ref, ctx in bad:
            print(f"  {fn}:{ln}  {col}.{ref}\n      {ctx}")
        print("\n  These compile GREEN and fail at runtime. Check for a rename that "
              "missed a call site.")
        sys.exit(1)

    print(f"PASS: every checked collection column reference resolves "
          f"({len(schemas)} collections)")
    if not args.quiet:
        for c in sorted(schemas):
            print(f"  {c}: {len(schemas[c])} columns")


if __name__ == "__main__":
    main()
