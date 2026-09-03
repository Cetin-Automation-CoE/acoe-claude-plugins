#!/usr/bin/env python3
"""Guard: no colour, font-size or radius literal outside the token region.

App.pa.yaml's Formulas block IS the token region. Every other file must reference
constStyle / const*Color and never carry a raw value.

Exemptions exist and are legitimate — a component without `AccessAppScope: true`
cannot see app tokens. Mark those lines explicitly:

    Fill: =RGBA(255, 255, 255, 1)   // token-exempt: cmp has no AccessAppScope

An unrecorded exemption is indistinguishable from rot, which is why the marker is
required rather than a silent allow-list.

    python3 check_tokens.py --src path/to/Src
    python3 check_tokens.py --src path/to/Src --allow-sizes 28,20,14,12,11

Exits non-zero on violation.
"""
import argparse
import collections
import pathlib
import re
import sys

EXEMPT = re.compile(r"(?://|#)\s*token-exempt\b", re.I)

# Structural values that are not design decisions: fully transparent, and the
# pure black/white that Power Fx idiom uses for shadows and masks.
STRUCTURAL = {"RGBA(0,0,0,0)"}

COLOUR = re.compile(r"RGBA\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*\)")
HEXCOL = re.compile(r"ColorValue\(\s*\"(#[0-9A-Fa-f]{3,8})\"\s*\)")
SIZE = re.compile(r"\b(?:Size|FontSize)\s*:\s*=\s*([\d.]+)\b")
RADIUS = re.compile(r"\b\w*Radius\w*\s*:\s*=\s*([\d.]+)\b")


def code_only(line: str) -> str:
    # Strip Power Fx // comments AND YAML # comments. Without the second,
    # a comment that merely QUOTES a literal ("was Size: =16") is reported
    # as a violation — documentation flagged as code.
    line = re.sub(r"//.*$", "", line)
    return re.sub(r"(^|\s)#.*$", "", line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--allow-sizes", default="28,20,14,12,11",
                    help="font sizes permitted as literals (the type scale)")
    # 0 is structural, not a design decision: it means "square corner", and every
    # container that opts out of rounding sets it four times.
    ap.add_argument("--allow-radius", default="0,10", help="radius values permitted as literals")
    ap.add_argument("--token-files", default="App.pa.yaml",
                    help="comma-separated file names that ARE the token region "
                         "(default App.pa.yaml; add design-tokens.pa.yaml if you keep them separately)")
    ap.add_argument("--strict-sizes", action="store_true",
                    help="flag EVERY font-size literal, even ones on the scale")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit(f"error: --src is not a directory: {src}")
    files = sorted(src.rglob("*.pa.yaml"))
    if not files:
        sys.exit(f"error: no .pa.yaml files under {src}")

    ok_sizes = {float(s) for s in args.allow_sizes.split(",") if s.strip()}
    ok_radius = {float(s) for s in args.allow_radius.split(",") if s.strip()}

    violations = []
    exempted = collections.Counter()

    token_files = {s.strip() for s in args.token_files.split(",") if s.strip()}
    for f in files:
        # The token region itself is where literals belong.
        if f.name in token_files:
            continue
        for ln, raw in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if EXEMPT.search(raw):
                exempted[f.name] += 1
                continue
            code = code_only(raw)
            loc = f"{f.relative_to(src)}:{ln}"

            for m in COLOUR.finditer(code):
                val = re.sub(r"\s+", "", m.group(0))
                if val not in STRUCTURAL:
                    violations.append((loc, "colour", val, raw.strip()[:80]))
            for m in HEXCOL.finditer(raw):
                violations.append((loc, "colour", m.group(1), raw.strip()[:80]))
            for m in SIZE.finditer(code):
                v = float(m.group(1))
                if args.strict_sizes or v not in ok_sizes:
                    violations.append((loc, "font size", m.group(1), raw.strip()[:80]))
            for m in RADIUS.finditer(code):
                v = float(m.group(1))
                if v not in ok_radius:
                    violations.append((loc, "radius", m.group(1), raw.strip()[:80]))

    if violations:
        print(f"FAIL: {len(violations)} literal(s) outside the token region.\n")
        by_kind = collections.Counter(v[1] for v in violations)
        for loc, kind, val, ctx in violations:
            print(f"  {loc}  [{kind}] {val}\n      {ctx}")
        print("\n  " + " · ".join(f"{k}: {n}" for k, n in by_kind.most_common()))
        print("\n  Fix: reference constStyle / const*Color, or mark a genuine exemption\n"
              "       with `// token-exempt: <reason>` on the same line.")
        sys.exit(1)

    msg = f"PASS: no literals outside the token region "\
          f"({len(files) - len([f for f in files if f.name in token_files])} files checked"
    if exempted:
        msg += f", {sum(exempted.values())} recorded exemption(s) in {len(exempted)} file(s)"
    print(msg + ")")
    for name, n in exempted.most_common():
        print(f"  exempt: {name} ({n})")


if __name__ == "__main__":
    main()
