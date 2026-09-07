#!/usr/bin/env python3
"""Scaffold a complete, guard-clean Canvas App source tree.

Two modes:

    python3 new_app.py --name "Vendor Register" --brand "#0F6CBD" --out ./Src
    python3 new_app.py --model model.yaml --out ./Src [--rows 16] [--force]

`--name` (the legacy path) writes the generic one-entity pattern: names stay
generic on purpose (colItems, funcLoadItems, funcSaveItem, locItem) — it is a
pattern to copy per entity, not a one-entity app.

`--model` reads a model.yaml (see templates/model.example.yaml) and produces a
COMPLETE multi-entity app: one list screen and one form screen per entity,
entity-derived identifiers throughout (colAssets, funcSaveAsset, ...), mock
rows that survive to render, and a navigation registry covering every entity.
App.pa.yaml is assembled from the template's static chrome (helper UDFs, the
loading-indicator pair, colBack/navigation helpers, UI utility UDFs) plus the
design tokens (inlined) plus emit_formulas.emit_all()'s output, spliced in at
TWO points — one for the vocabulary layer, one for the data-access layer plus
the constScreens registry — because emit_all() deliberately does not emit the
template's entity-agnostic middle layers. See templates/App.pa.yaml's
`SPLICE:` comments.

`--model` and `--name` are mutually exclusive: the app name and brand for a
model-driven build come from model.yaml (`app_name`, `brand`), not the CLI.

Either way, the command then verifies its own output — first that every
written file parses as YAML, then the five check_*.py guard scripts — and
refuses to leave a broken tree behind.

There is no local path to an importable .msapp: `pac canvas pack` is deprecated
and crashes on real apps, and `pac canvas validate` rejects every file of a
working published app. Get the generated source into Power Apps through a
coauthoring session — the command prints the steps.
"""
import argparse
import datetime
import pathlib
import re
import shutil
import subprocess
import sys

import yaml

import emit_formulas
import emit_screens
from model import ModelError, load_model

SKILL = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
COMPONENTS = SKILL / "components"
TOKENS_MARKER = "// >>> PASTE templates/design-tokens.pa.yaml HERE <<<"

# The two splice points a --model build fills in. See templates/App.pa.yaml.
VOCAB_BEGIN = "// >>> SPLICE: emit_formulas vocabulary BEGIN <<<"
VOCAB_END = "// >>> SPLICE: emit_formulas vocabulary END <<<"
DATA_BEGIN = "// >>> SPLICE: emit_formulas data-layer+registry BEGIN <<<"
DATA_END = "// >>> SPLICE: emit_formulas data-layer+registry END <<<"

# emit_formulas.emit_all()'s own promised banner text (see that module's
# docstring: "its data-access layer is '7'") — the boundary this module
# splits emit_all()'s single returned string on, to feed the two markers
# above separately.
DATA_LAYER_HEADER = "      // ############ 7. DATA ACCESS LAYER ############"

ALL_COMPONENTS = [
    "cmp_Header", "cmp_Navigation", "cmp_CommandBar", "cmp_FilterButton",
    "cmp_Notification", "cmp_Dialog", "cmp_Empty", "cmp_Spinner",
    # Hand-authoring library (Controller Ruling 3): four per-type field
    # components, not wired into emit_screens.py. Nothing in the stock
    # templates instantiates these, so adding them here is safe for the
    # --components pre-flight check below — they are available to copy into
    # a target app, not required by it.
    "cmp_FieldText", "cmp_FieldChoice", "cmp_FieldDate", "cmp_FieldNumber",
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


def inline_tokens(brand):
    """The design-tokens fragment, header stripped, brand colour applied."""
    tokens = strip_header((TEMPLATES / "design-tokens.pa.yaml").read_text(encoding="utf-8"))
    if brand:
        rgba, hexcol = hex_to_rgba(brand)
        tokens = re.sub(r"(constPrimaryColor\s*=\s*\{RGBA:\s*)RGBA\([^)]*\)(,\s*HEX:\s*\")[^\"]*(\")",
                        rf"\g<1>{rgba}\g<2>{hexcol}\g<3>", tokens)
    return tokens


def splice_tokens(app_text, tokens):
    """Replace the single-line design-tokens marker with the (reindented)
    tokens fragment. Shared by both the --name and --model paths."""
    if TOKENS_MARKER not in app_text:
        sys.exit("error: token marker missing from templates/App.pa.yaml — cannot assemble")
    indent = " " * (len(app_text[:app_text.index(TOKENS_MARKER)].split("\n")[-1]))
    return app_text.replace(TOKENS_MARKER, "\n".join(
        (indent + ln) if ln.strip() else "" for ln in tokens.splitlines()).lstrip())


def _splice_span(text, begin_marker, end_marker, replacement):
    """Replace every line from `begin_marker`'s line through `end_marker`'s
    line (inclusive) with `replacement`. Used to drop emit_formulas' output
    in where templates/App.pa.yaml's generic vocabulary / data-layer content
    otherwise sits."""
    if begin_marker not in text or end_marker not in text:
        sys.exit("error: splice marker missing from templates/App.pa.yaml — cannot "
                  "assemble a --model build (expected to find %r and %r)"
                  % (begin_marker, end_marker))
    start = text.index(begin_marker)
    line_start = text.rfind("\n", 0, start) + 1
    end = text.index(end_marker, start)
    line_end = text.find("\n", end)
    line_end = len(text) if line_end == -1 else line_end + 1
    return text[:line_start] + replacement.rstrip("\n") + "\n" + text[line_end:]


def _replace_once(text, old, new, what):
    """Like str.replace(old, new, 1), but refuses to guess when `old` isn't
    present exactly once — a template shape change should fail loudly here,
    not silently emit a broken app."""
    n = text.count(old)
    if n != 1:
        sys.exit("error: expected exactly one occurrence of %s in "
                  "templates/App.pa.yaml, found %d — the template shape "
                  "changed; update new_app.py's assembly logic to match."
                  % (what, n))
    return text.replace(old, new, 1)


def build_app_pa_yaml_for_model(model, rows, today, brand):
    """Assemble App.pa.yaml for a --model build.

    `brand` is already resolved by the caller (model.brand when present,
    else --brand, else None) — Requirement 8.

    Ruling 5: emit_formulas.emit_all() deliberately excludes the template's
    entity-agnostic layers 5-6 (pure helper UDFs, derived values, the
    loading-indicator pair) and layer 9 (UI utility UDFs, colBack/navigation
    helpers) — those stay put, unedited, from templates/App.pa.yaml. Only the
    vocabulary layer and the data-access-layer + constScreens registry are
    spliced in, at the two markers that file declares.
    """
    app = (TEMPLATES / "App.pa.yaml").read_text(encoding="utf-8")
    app = splice_tokens(app, inline_tokens(brand))

    body = emit_formulas.emit_all(model, rows, today)
    if DATA_LAYER_HEADER not in body:
        sys.exit("error: emit_formulas.emit_all() output changed shape — cannot find "
                  "the data-access-layer boundary (expected %r). This module may not "
                  "be modified per the task brief; report this instead of patching "
                  "around it." % DATA_LAYER_HEADER)
    split_at = body.index(DATA_LAYER_HEADER)
    vocab_part = body[:split_at]
    data_registry_part = body[split_at:]

    app = _splice_span(app, VOCAB_BEGIN, VOCAB_END, vocab_part)
    app = _splice_span(app, DATA_BEGIN, DATA_END, data_registry_part)

    # OnStart / StartScreen still name the template's generic ListScreen —
    # repoint them at the first entity's list screen (a real, defined
    # screen), and load every entity's collection on start, not just one.
    first_screen = model.entities[0].list_screen
    app = _replace_once(
        app,
        'ClearCollect(colBack, Table({Screen: ListScreen, Label: ""}));',
        'ClearCollect(colBack, Table({Screen: %s, Label: ""}));' % first_screen,
        "the colBack seed in OnStart")

    load_calls = ("%s();" % model.entities[0].func_load) + "".join(
        "\n      %s();" % e.func_load for e in model.entities[1:])
    app = _replace_once(app, "funcLoadItems();", load_calls,
                        "the funcLoadItems(); call in OnStart")

    app = _replace_once(app, "StartScreen: =ListScreen",
                        "StartScreen: =%s" % first_screen, "StartScreen")
    return app


class _PaYamlLoader(yaml.SafeLoader):
    """SafeLoader plus one tolerance: a bare `=` value (e.g. `Default: =`,
    this skill's convention for "the formula is empty/blank"), which YAML's
    core schema resolves to the reserved `tag:yaml.org,2002:value` tag that
    SafeLoader has no constructor for. Without this, every genuine,
    already-shipped component that declares a property with no default
    formula (components/cmp_FilterButton.pa.yaml has two) would report as
    "not valid YAML" — a false positive this check must not raise, since it
    is meant to catch REAL malformed YAML (the two Task 4 found), not this
    skill's own `=`-prefixed-formula convention colliding with a YAML 1.1
    reserved scalar. Nothing else about SafeLoader's behaviour changes."""


_PaYamlLoader.add_constructor(
    "tag:yaml.org,2002:value",
    lambda loader, node: loader.construct_scalar(node))


def check_yaml_wellformed(out):
    """Every .pa.yaml file just written must at least parse as YAML.

    No check_*.py guard verifies this — they all assume well-formed YAML and
    look for text patterns inside it. Two real bugs (Task 4) reached this
    point undetected before a human noticed. Runs before the guards: a file
    that doesn't parse makes every guard's finding about it meaningless.
    """
    files = sorted(out.rglob("*.pa.yaml"))
    bad = []
    for f in files:
        try:
            yaml.load(f.read_text(encoding="utf-8"), Loader=_PaYamlLoader)
        except yaml.YAMLError as exc:
            bad.append((f, exc))
    return files, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="destination Src/ directory")
    ap.add_argument("--model", default=None,
                    help="model.yaml driving a complete multi-entity app — see "
                         "templates/model.example.yaml. Mutually exclusive with --name.")
    ap.add_argument("--rows", type=int, default=16,
                    help="mock rows per entity (only used with --model; default 16)")
    ap.add_argument("--name", default=None,
                    help="app display name, used in the header title (default 'New "
                         "App'). With --model the name comes from model.yaml's "
                         "app_name instead — do not pass both.")
    ap.add_argument("--brand", default=None, help="primary brand colour as hex, e.g. '#0F6CBD'")
    ap.add_argument("--components", default="all",
                    help="'all' (default), 'none' for the formula layer only (no screens), "
                         "or a comma-separated subset of: " + ", ".join(ALL_COMPONENTS)
                         + " (--name only — a --model build always writes all eight)")
    ap.add_argument("--force", action="store_true", help="overwrite a non-empty --out")
    args = ap.parse_args()

    if args.model and args.name is not None:
        sys.exit("error: --model and --name are mutually exclusive — a model-driven "
                  "build takes its app name from model.yaml's app_name field. Drop "
                  "--name (or drop --model).")

    # Ruling 1: load the model FIRST, before touching the filesystem at all,
    # so a bad model.yaml writes nothing.
    model = None
    if args.model:
        try:
            model = load_model(args.model)
        except ModelError as exc:
            sys.exit("error: %s" % exc)

    if model is None:
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
    else:
        chosen = list(ALL_COMPONENTS)
        screens = None  # written per-entity below, not from the stock templates

    out = pathlib.Path(args.out).resolve()
    if out.exists() and any(out.iterdir()) and not args.force:
        sys.exit(f"error: {out} exists and is not empty (use --force to overwrite)")
    (out / "Components").mkdir(parents=True, exist_ok=True)

    if model is not None:
        # ---- App.pa.yaml: template chrome + inlined tokens + emitted vocab
        # and data-layer/registry, spliced in at the two markers. ----------
        today = datetime.date.today()
        brand = model.brand if model.brand else args.brand
        app = build_app_pa_yaml_for_model(model, args.rows, today, brand)
        (out / "App.pa.yaml").write_text(app, encoding="utf-8")

        # ---- one list screen and one form screen per entity --------------
        for entity in model.entities:
            (out / (entity.list_screen + ".pa.yaml")).write_text(
                emit_screens.emit_list_screen(entity, model), encoding="utf-8")
            (out / (entity.form_screen + ".pa.yaml")).write_text(
                emit_screens.emit_form_screen(entity, model), encoding="utf-8")

        # ---- components: all eight, as today ------------------------------
        for c in chosen:
            shutil.copyfile(COMPONENTS / f"{c}.pa.yaml", out / "Components" / f"{c}.pa.yaml")

        # ---- _EditorState: every generated screen, entity by entity -------
        editor = ["EditorState:", "  ScreensOrder:"]
        for entity in model.entities:
            editor += ["    - %s" % entity.list_screen, "    - %s" % entity.form_screen]
        editor.append("  ComponentDefinitionsOrder:")
        editor += ["    - %s" % c for c in chosen]
        (out / "_EditorState.pa.yaml").write_text("\n".join(editor) + "\n", encoding="utf-8")

        display_name = model.app_name
    else:
        # ---- App.pa.yaml: inline the tokens at the marker ------------------------
        app = (TEMPLATES / "App.pa.yaml").read_text(encoding="utf-8")
        app = splice_tokens(app, inline_tokens(args.brand))
        (out / "App.pa.yaml").write_text(app, encoding="utf-8")

        # ---- screens ------------------------------------------------------------
        name = args.name if args.name is not None else "New App"
        for f in screens:
            t = (TEMPLATES / f).read_text(encoding="utf-8")
            # Only the header title is app-specific; every identifier stays generic.
            t = t.replace('DisplayName: ="Items"', f'DisplayName: ="{name}"', 1)
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

        display_name = name

    written = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.pa.yaml"))
    if model is None and not screens:
        print("--components none: scaffolding the formula layer only, no screens.\n"
              "      App.pa.yaml still names ListScreen and FormScreen (constScreens,\n"
              "      the colBack seed and StartScreen). Create screens with those names\n"
              "      or edit those three places before the first compile.\n")
    if model is not None:
        print(f"Scaffolded {display_name!r} ({len(model.entities)} entities, "
              f"{args.rows} mock rows each) into {out}")
    else:
        print(f"Scaffolded {display_name!r} into {out}")
    for w in written:
        print(f"  {w}")

    # ---- YAML well-formedness: before any guard, which all assume it -----------
    print("\nChecking YAML well-formedness:")
    yaml_files, bad_yaml = check_yaml_wellformed(out)
    if bad_yaml:
        print(f"FAIL: {len(bad_yaml)} of {len(yaml_files)} file(s) are not valid YAML —\n"
              f"no guard below can be trusted until this is fixed:\n")
        for f, exc in bad_yaml:
            print(f"  {f.relative_to(out)}: {exc}")
        sys.exit(1)
    print(f"  PASS: {len(yaml_files)} file(s) parse as YAML: "
          + ", ".join(p.relative_to(out).as_posix() for p in yaml_files))

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
        ("check_control_props.py", ["--src", str(out)]),
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
All 5 local guards pass. That means: architecture, tokens, data layer, collection
columns and control contracts are clean.

It does NOT mean the app compiles. There is no offline compile for Canvas Apps —
`pac canvas pack` is deprecated and crashes, and `pac canvas validate` rejects every
file of a working published app. The only real validator is compile_canvas against a
live coauthoring session.
""")

    print(f"""
Next — there is no local .msapp path (pac canvas pack is deprecated and
crashes; pac canvas validate rejects even working apps), so push the source
into a live app:

  1. In Power Apps Studio create a BLANK TABLET app named "{display_name}".
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
