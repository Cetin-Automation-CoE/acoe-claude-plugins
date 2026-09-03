#!/usr/bin/env python3
"""Scaffold a complete, guard-clean Canvas App source tree.

Assembles App.pa.yaml (with the design tokens INLINED at the top, so they can
never land below their first use), the list and form screens already wired to
the components, the components themselves, and _EditorState.pa.yaml.

    python3 new_app.py --name "Vendor Register" --brand "#0F6CBD" --out ./Src

Names stay generic on purpose (colItems, funcLoadItems, funcSaveItem, locItem):
the scaffold is a pattern to copy per entity, not a one-entity app.

Then verifies its own output with the guard scripts and refuses to leave a
broken tree behind.

There is no local path to an importable .msapp: `pac canvas pack` is deprecated
and crashes on real apps, and `pac canvas validate` rejects every file of a
working published app. Get the generated source into Power Apps through a
coauthoring session — the command prints the steps.
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import sys

SKILL = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
COMPONENTS = SKILL / "components"
MARKER = "// >>> PASTE templates/design-tokens.pa.yaml HERE <<<"

ALL_COMPONENTS = [
    "cmp_Header", "cmp_Navigation", "cmp_CommandBar", "cmp_FilterButton",
    "cmp_Notification", "cmp_Dialog", "cmp_Empty", "cmp_Spinner",
]

def strip_header(text: str) -> str:
    """Drop the tokens file's usage header (the first // ==== ... ==== banner)."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("// ="):
        return text
    for i in range(1, len(lines)):
        if re.match(r"^//\s*=+\s*$", lines[i]):
            return "\n".join(lines[i + 1:]).lstrip("\n")
    return text


def hex_to_rgba(h: str):
    """Return (RGBA(...) literal, normalised "#RRGGBB") for a hex colour."""
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise SystemExit(f"error: --brand is not a 6-digit hex colour: {h}")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"RGBA({r}, {g}, {b}, 1)", "#" + h.upper()


def run_guard(script, *args):
    r = subprocess.run([sys.executable, str(SKILL / "scripts" / script), *args],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="destination Src/ directory")
    ap.add_argument("--name", default="New App", help="app display name, used in the header title")
    ap.add_argument("--brand", default=None, help="primary brand colour as hex, e.g. '#0F6CBD'")
    ap.add_argument("--components", default="all",
                    help="'all' (default), 'none' for the formula layer only (no screens), "
                         "or a comma-separated subset of: " + ", ".join(ALL_COMPONENTS))
    ap.add_argument("--force", action="store_true", help="overwrite a non-empty --out")
    args = ap.parse_args()

    if args.components == "all":
        chosen = list(ALL_COMPONENTS)
    elif args.components == "none":
        chosen = []
    else:
        chosen = [c.strip() for c in args.components.split(",") if c.strip()]
        unknown = [c for c in chosen if c not in ALL_COMPONENTS]
        if unknown:
            sys.exit(f"error: unknown component(s): {', '.join(unknown)}\n"
                     f"       available: {', '.join(ALL_COMPONENTS)}")

    # Pre-flight: the stock screens instantiate components by name. A subset that
    # does not cover them produces an app that references definitions which are
    # not there — so fail BEFORE writing anything, not after.
    screens = ["ListScreen.pa.yaml", "FormScreen.pa.yaml"] if chosen else []
    if screens:
        needed = set()
        for f in screens:
            needed |= set(re.findall(r"^\s*ComponentName:\s*(cmp_\w+)\s*$",
                                     (TEMPLATES / f).read_text(encoding="utf-8"), re.M))
        gap = sorted(needed - set(chosen))
        if gap:
            sys.exit(f"error: the stock screens instantiate {', '.join(gap)}, which "
                     f"--components leaves out.\n"
                     f"       Add them, use --components all, or use --components none "
                     f"to scaffold the\n       formula layer alone and write your own screens.")

    out = pathlib.Path(args.out).resolve()
    if out.exists() and any(out.iterdir()) and not args.force:
        sys.exit(f"error: {out} exists and is not empty (use --force to overwrite)")
    (out / "Components").mkdir(parents=True, exist_ok=True)

    # ---- App.pa.yaml: inline the tokens at the marker ------------------------
    tokens = strip_header((TEMPLATES / "design-tokens.pa.yaml").read_text(encoding="utf-8"))
    if args.brand:
        rgba, hexcol = hex_to_rgba(args.brand)
        tokens = re.sub(r"(constPrimaryColor\s*=\s*\{RGBA:\s*)RGBA\([^)]*\)(,\s*HEX:\s*\")[^\"]*(\")",
                        rf"\g<1>{rgba}\g<2>{hexcol}\g<3>", tokens)

    app = (TEMPLATES / "App.pa.yaml").read_text(encoding="utf-8")
    if MARKER not in app:
        sys.exit(f"error: token marker missing from templates/App.pa.yaml — cannot assemble")
    indent = " " * (len(app[:app.index(MARKER)].split("\n")[-1]))
    app = app.replace(MARKER, "\n".join(
        (indent + ln) if ln.strip() else "" for ln in tokens.splitlines()).lstrip())
    (out / "App.pa.yaml").write_text(app, encoding="utf-8")

    # ---- screens ------------------------------------------------------------
    for f in screens:
        t = (TEMPLATES / f).read_text(encoding="utf-8")
        # Only the header title is app-specific; every identifier stays generic.
        t = t.replace('DisplayName: ="Items"', f'DisplayName: ="{args.name}"', 1)
        (out / f).write_text(t, encoding="utf-8")

    # ---- components ---------------------------------------------------------
    for c in chosen:
        shutil.copyfile(COMPONENTS / f"{c}.pa.yaml", out / "Components" / f"{c}.pa.yaml")

    # ---- _EditorState -------------------------------------------------------
    editor = ["EditorState:"]
    if screens:
        editor += ["  ScreensOrder:", "    - ListScreen", "    - FormScreen"]
    if chosen:
        editor.append("  ComponentDefinitionsOrder:")
        editor += [f"    - {c}" for c in chosen]
    (out / "_EditorState.pa.yaml").write_text("\n".join(editor) + "\n", encoding="utf-8")

    cdir = out / "Components"
    if not chosen and cdir.exists() and not any(cdir.iterdir()):
        cdir.rmdir()

    written = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.pa.yaml"))
    if not screens:
        print("--components none: scaffolding the formula layer only, no screens.\n"
              "      App.pa.yaml still names ListScreen and FormScreen (constScreens,\n"
              "      the colBack seed and StartScreen). Create screens with those names\n"
              "      or edit those three places before the first compile.\n")
    print(f"Scaffolded {args.name!r} into {out}")
    for w in written:
        print(f"  {w}")

    # ---- verify what we just wrote ------------------------------------------
    print("\nVerifying:")
    checks = [
        ("check_references.py", ["--src", str(out)]),
        ("check_tokens.py", ["--src", str(out)]),
        ("check_collection_columns.py", ["--src", str(out), "--quiet"]),
        # No data sources exist yet; the sentinel pattern matches nothing, so
        # this still checks the banners and that no screen writes a data
        # collection directly.
        ("check_data_layer.py", ["--src", str(out), "--datasource-pattern", "__NO_DATASOURCE__"]),
    ]
    failed = 0
    for script, argv in checks:
        code, output = run_guard(script, *argv)
        first = output.splitlines()[0] if output else "(no output)"
        print(f"  {'PASS' if code == 0 else 'FAIL'}  {script}: {first}")
        if code != 0:
            failed += 1
            print("\n".join("        " + l for l in output.splitlines()[1:12]))
    if failed:
        print(f"\n{failed} check(s) failed — the scaffold is NOT clean. This is a bug in the\n"
              f"skill's templates, not in your arguments. Do not push this to a live app.")
        sys.exit(1)

    print(f"""
All checks pass.

Next — there is no local .msapp path (pac canvas pack is deprecated and
crashes; pac canvas validate rejects even working apps), so push the source
into a live app:

  1. In Power Apps Studio create a BLANK TABLET app named "{args.name}".
  2. Point the Canvas Authoring MCP at it:
       connect(environment_id=..., app_id=..., environment_category=...)
  3. Push this tree:
       compile_canvas(directory="{out}")
     compile_canvas pushes BEFORE it validates, so the first run doubles as
     the first compile. Keep the studio tab open — a closed tab makes it hang
     for the full 1800s idle timeout rather than erroring.
  4. Fix what the strict engine reports. These components have never been
     compiled; treat the first run as a debugging session.
  5. Commit the moment it goes green.

Then wire your real backend: everything to change is between the
DATA ACCESS LAYER banners in App.pa.yaml. See references/data-access-layer.md.""")


if __name__ == "__main__":
    main()
