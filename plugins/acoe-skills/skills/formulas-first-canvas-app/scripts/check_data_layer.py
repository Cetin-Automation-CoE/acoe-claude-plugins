#!/usr/bin/env python3
"""Guard: no data-source name and no data write escapes the data-access region.

This is the invariant the whole backend-switch procedure rests on. If it fails,
changing backends is no longer "edit ~20 function bodies" — it is a hunt through
every screen in the app.

Prose is not coupling: a list name in a comment or a UI label is documentation, so
// comments and "quoted strings" are stripped before matching.

    python3 check_data_layer.py --src path/to/Src --datasource-pattern 'PP_[A-Za-z]'

Exits non-zero on violation, so it drops into CI or a pre-commit hook.
"""
import argparse
import pathlib
import re
import sys

BANNERS = [("DATA ACCESS LAYER — BEGIN", "DATA ACCESS LAYER — END"),
           ("DATA ACCESS LAYER — ZAČÁTEK", "DATA ACCESS LAYER — KONEC")]

# Collections screens legitimately own: UI state, not data.
DEFAULT_APP_STATE = {"colFilters", "colSorts", "colBack", "colNotifications"}

WRITE_FNS = r"Collect|ClearCollect|Patch|Remove|RemoveIf|UpdateIf|Update"


def code_only(line: str) -> str:
    line = re.sub(r'"[^"]*"', '""', line)
    return re.sub(r"//.*$", "", line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--datasource-pattern", required=True,
                    help=r"regex matching your data source names, e.g. 'PP_[A-Za-z]'")
    ap.add_argument("--app-state", default=",".join(sorted(DEFAULT_APP_STATE)),
                    help="comma-separated collections screens may write (UI state)")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit(f"error: --src is not a directory: {src}")
    files = sorted(src.rglob("*.pa.yaml"))
    app = next((f for f in files if f.name == "App.pa.yaml"), None)
    if app is None:
        sys.exit("error: no App.pa.yaml found — is --src the unpacked Src/ directory?")

    ds_re = re.compile(args.datasource_pattern)
    app_state = {s.strip() for s in args.app_state.split(",") if s.strip()}
    fail = []

    # 1. Both banners must exist, or every region test below passes vacuously.
    #    A guard that silently checks nothing is worse than no guard.
    app_text = app.read_text(encoding="utf-8", errors="replace")
    begin, end = None, None
    for b, e in BANNERS:
        if b in app_text and e in app_text:
            begin, end = b, e
            break
    if begin is None:
        fail.append("FAIL: data-access banners missing from App.pa.yaml — "
                    "the region is undefined, so this check would pass vacuously.\n"
                    "       Expected a pair such as:\n"
                    "         // ===== DATA ACCESS LAYER — BEGIN =====\n"
                    "         // ===== DATA ACCESS LAYER — END =====")

    # 2. Data-source names referenced as code outside the region.
    ds_hits = []
    for f in files:
        inside = False
        for ln, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if f == app and begin:
                if begin in line:
                    inside = True
                if end in line:
                    inside = False
            if inside:
                continue
            if ds_re.search(code_only(line)):
                ds_hits.append(f"  {f.relative_to(src)}:{ln}: {line.strip()[:100]}")
    if ds_hits:
        fail.append("FAIL: data source referenced as code outside the data-access region:\n"
                    + "\n".join(ds_hits))

    # 3. Direct writes to data collections from screens or components.
    writes = []
    for f in files:
        if f == app:
            continue
        for ln, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in re.finditer(rf"\b(?:{WRITE_FNS})\(\s*(col\w+)", code_only(line)):
                if m.group(1) not in app_state:
                    writes.append(f"  {f.relative_to(src)}:{ln}: {line.strip()[:100]}")
    if writes:
        fail.append("FAIL: direct writes to data collections outside the layer "
                    "(screens must call funcSaveX / funcDeleteX):\n" + "\n".join(writes))

    if fail:
        print("\n\n".join(fail))
        sys.exit(1)

    print(f"PASS: data sources and data writes confined to the layer "
          f"({len(files)} files, app-state exempt: {', '.join(sorted(app_state))})")


if __name__ == "__main__":
    main()
