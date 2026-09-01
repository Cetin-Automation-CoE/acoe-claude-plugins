#!/usr/bin/env python3
"""Guard: every const*/enum*/func*/gl* name a screen or component uses is defined.

Power Fx resolves these at compile time, but an unresolved name in App.Formulas can
take the WHOLE Formulas blob down in the studio binder — producing dozens of
"unknown name" errors on screens you never touched. This finds the one real cause
before you go hunting.

It also flags forward references INSIDE App.Formulas: the studio document-server
binder cannot resolve a named formula that refers to one declared below it, even
though the compile service can.

    python3 check_references.py --src path/to/Src
    python3 check_references.py --src path/to/Src --extra-dirs components,templates

Exits non-zero on violation.
"""
import argparse
import pathlib
import re
import sys

# Power Fx built-ins and enums that look like our prefixes but are not ours.
BUILTINS = {
    "constrain",  # defensive: no built-in actually collides, but keep the hook
}

# Names must be prefix + UpperCamelCase, which is the convention this skill
# mandates. Without the [A-Z] anchor, English words in prose match:
# "global" -> gl, "function" -> func, "construct" -> const.
NAME = r"(?:const|enum|func|gl)[A-Z][A-Za-z0-9_]*"

DEF_PATTERNS = [
    re.compile(r"^\s*((?:const|enum)[A-Z][A-Za-z0-9_]*)\s*=", re.M),
    re.compile(r"^\s*(func[A-Z][A-Za-z0-9_]*)\s*\(", re.M),
]
SET_PATTERN = re.compile(r"\bSet\(\s*(gl[A-Z][A-Za-z0-9_]*)\s*,")
# Component definitions and the screens that instantiate them.
CMPDEF_PATTERN = re.compile(r"^\s{2}(cmp_[A-Za-z0-9_]+)\s*:\s*$", re.M)
CMPUSE_PATTERN = re.compile(r"^\s*ComponentName:\s*(cmp_[A-Za-z0-9_]+)\s*$", re.M)
USE_PATTERN = re.compile(r"\b(" + NAME + r")\b")


def strip_comments(text: str) -> str:
    """Remove // line comments and /* */ blocks. Quoted strings are kept:
    a token name inside a string is not a reference, but stripping strings
    wholesale would also hide nothing useful here."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//.*$", "", text, flags=re.M)
    # YAML comments too: a '#' opening a line. Not mid-line, which would eat
    # hex colour literals like "#300091".
    return re.sub(r"^\s*#.*$", "", text, flags=re.M)


def formulas_block(app_text: str) -> str:
    """The App.Formulas block scalar, bounded by indentation."""
    lines = app_text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^\s*Formulas:\s*\|", line):
            indent = len(line) - len(line.lstrip())
            body = []
            for nxt in lines[i + 1:]:
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--extra-dirs", default="",
                    help="comma-separated sibling dirs to include (e.g. components,templates)")
    ap.add_argument("--tokens-file", default=None,
                    help="extra Power Fx fragment holding definitions (e.g. templates/design-tokens.pa.yaml)")
    ap.add_argument("--no-order-check", action="store_true",
                    help="skip the App.Formulas forward-reference check")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit(f"error: --src is not a directory: {src}")

    roots = [src] + [src.parent / d.strip() for d in args.extra_dirs.split(",") if d.strip()]
    files = sorted({f for r in roots if r.is_dir() for f in r.rglob("*.pa.yaml")})
    if not files:
        sys.exit(f"error: no .pa.yaml files under {', '.join(str(r) for r in roots)}")

    app = next((f for f in files if f.name == "App.pa.yaml"), None)
    if app is None:
        sys.exit("error: no App.pa.yaml found")

    app_text = strip_comments(app.read_text(encoding="utf-8", errors="replace"))
    block = formulas_block(app_text)
    if args.tokens_file:
        tf = pathlib.Path(args.tokens_file)
        if not tf.exists():
            sys.exit(f"error: --tokens-file not found: {tf}")
        # Tokens are declared FIRST, so prepend: order checks stay meaningful.
        block = strip_comments(tf.read_text(encoding="utf-8", errors="replace")) + "\n" + block

    # --- collect definitions -------------------------------------------------
    defined, order = set(), []
    for pat in DEF_PATTERNS:
        for m in pat.finditer(block):
            defined.add(m.group(1))
    for m in re.finditer(r"^\s*((?:const|enum|func)[A-Z][A-Za-z0-9_]*)\s*[=(]", block, re.M):
        if m.group(1) not in [n for n, _ in order]:
            order.append((m.group(1), m.start()))
    # gl* globals are defined by Set() anywhere in the app
    for f in files:
        defined |= set(SET_PATTERN.findall(strip_comments(f.read_text(encoding="utf-8", errors="replace"))))

    # --- collect uses --------------------------------------------------------
    unknown = []
    for f in files:
        for ln, line in enumerate(strip_comments(
                f.read_text(encoding="utf-8", errors="replace")).splitlines(), 1):
            for name in USE_PATTERN.findall(line):
                if name in defined or name in BUILTINS:
                    continue
                # A definition line is not a use of itself.
                if re.match(rf"^\s*{re.escape(name)}\s*[=(]", line):
                    continue
                unknown.append((f.name, ln, name, line.strip()[:80]))

    fail = False
    if unknown:
        fail = True
        seen = set()
        print(f"FAIL: {len(unknown)} reference(s) to names that are never defined\n")
        for fn, ln, name, ctx in unknown:
            if (fn, name) in seen:
                continue
            seen.add((fn, name))
            print(f"  {fn}:{ln}  {name}\n      {ctx}")
        print("\n  In the studio binder an unresolved name drops the WHOLE Formulas\n"
              "  blob, so this shows up as many unrelated errors on screens.")

    # --- component instantiations resolve to a definition --------------------
    # A screen naming a component that was never copied in is a broken app that
    # no other guard sees: the name is not a Power Fx identifier.
    defined_cmps, used_cmps = set(), []
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        if "ComponentDefinitions:" in raw:
            defined_cmps |= set(CMPDEF_PATTERN.findall(raw))
        for ln, line in enumerate(raw.splitlines(), 1):
            m = CMPUSE_PATTERN.match(line)
            if m:
                used_cmps.append((f.name, ln, m.group(1)))
    missing = [(fn, ln, c) for fn, ln, c in used_cmps if c not in defined_cmps]
    if missing:
        fail = True
        print(f"\nFAIL: {len(missing)} screen(s) instantiate a component with no definition\n")
        for fn, ln, c in missing:
            print(f"  {fn}:{ln}  ComponentName: {c}")
        print(f"\n  Defined here: {', '.join(sorted(defined_cmps)) or '(none)'}\n"
              f"  Copy the missing component .pa.yaml into Src/Components/.")

    # --- forward references inside App.Formulas ------------------------------
    if not args.no_order_check:
        pos = {n: p for n, p in order}
        forward = []
        for name, start in order:
            # ONLY named-formula -> named-formula matters. A UDF may reference a
            # named formula declared later: verified against a production app
            # where funcToEur reads constFxRates from 600 lines below and the
            # binder resolves it fine.
            if name.startswith("func"):
                continue
            # body of this declaration = until the next declaration
            later = [p for _, p in order if p > start]
            end = min(later) if later else len(block)
            body = block[start:end]
            for used in set(USE_PATTERN.findall(body)):
                if (used in pos and pos[used] > start and used != name
                        and not used.startswith("func")):
                    forward.append((name, used))
        if forward:
            fail = True
            print(f"\nFAIL: {len(forward)} forward reference(s) inside App.Formulas\n")
            for a, b in forward:
                print(f"  {a} references {b}, which is declared LATER")
            print("\n  The studio document-server binder cannot resolve these (the compile\n"
                  "  service can), and one failure drops the entire Formulas blob.\n"
                  "  Fix: move the declaration above its first use.")

    if fail:
        sys.exit(1)

    print(f"PASS: every const/enum/func/gl reference resolves, and App.Formulas "
          f"declares in dependency order ({len(files)} files, {len(defined)} names)")


if __name__ == "__main__":
    main()
