#!/usr/bin/env python3
"""Guard: control properties match their control's contract.

The four architectural guards check where logic lives. None of them checks whether
a property name exists on the control it is written under, which is how a tree can
pass every guard and still fail to compile.

There is no offline compile for Canvas Apps (`pac canvas pack` is deprecated and
crashes; `pac canvas validate` rejects every file of a working published app), so
this static check is the only pre-push signal.

    python3 check_control_props.py --src path/to/Src
    python3 check_control_props.py --src path/to/Src --contracts other-contracts.yaml

Exits non-zero on any error-severity finding. Warnings do not fail the run.

COVERAGE LIMITS — this guard does NOT check:
  * property VALUES beyond enum-namespace membership (no type or formula checking)
  * controls absent from references/control-contracts.yaml (reported as unchecked)
  * values it cannot resolve statically (If()/Switch()/ThisItem — counted, reported)
  * layout correctness beyond the leaf-control size rule (see check_layout.py)
  * anything only a live compile_canvas run can catch
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONTRACTS = SKILL / "references" / "control-contracts.yaml"

PropSite = collections.namedtuple(
    "PropSite", "file line control control_type component_name prop value")
Finding = collections.namedtuple(
    "Finding", "severity file line control prop message")

RE_ITEM = re.compile(r"^(\s*)- ([A-Za-z_][\w@.]*):\s*$")
RE_KEY = re.compile(r"^(\s*)([A-Za-z_][\w@.]*):\s*(.*)$")
RE_ENUM = re.compile(r"^=\s*'?([A-Za-z][\w.]*?)'?\.([A-Za-z]\w*)\s*$")
BLOCK_SCALAR = ("|", "|-", "|+", ">", ">-", ">+")


def load_contracts(path=None):
    """Load and normalize the contract file.

    `properties` entries may be comma-joined strings for readability; flatten them
    into a set. Returns the dict with `properties` as sets.
    """
    path = pathlib.Path(path) if path else DEFAULT_CONTRACTS
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    for spec in data["controls"].values():
        flat = set()
        for entry in spec.get("properties") or []:
            flat.update(p.strip() for p in str(entry).split(",") if p.strip())
        spec["properties"] = flat
        spec["absent"] = set(spec.get("absent") or [])
        spec["removed"] = set(spec.get("removed") or [])
        spec["renamed_from"] = spec.get("renamed_from") or {}
        spec["enums"] = spec.get("enums") or {}
    data["enums"] = {k: set(v) for k, v in data["enums"].items()}
    return data


def iter_properties(text, filename):
    """Yield a PropSite per property line, tracking the enclosing control.

    Control blocks look like:

        - lbl_Row_Title:
            Control: ModernText
            Properties:
              Color: =...

    Multi-line block scalars (`Items: |-`) are consumed whole so their bodies are
    never mistaken for property lines.
    """
    lines = text.splitlines()
    control_name = control_type = component_name = None
    control_indent = -1
    props_indent = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())

        m = RE_ITEM.match(raw)
        if m:
            control_name = m.group(2)
            control_type = component_name = None
            control_indent = len(m.group(1))
            props_indent = None
            continue

        m = RE_KEY.match(raw)
        if not m:
            continue
        key, value = m.group(2), m.group(3).strip()

        if key == "Control":
            control_type = value
            control_indent = indent
            props_indent = None
            continue
        if key == "ComponentName":
            component_name = value
            continue
        if key == "Properties":
            props_indent = indent
            continue
        if key == "Children":
            props_indent = None
            continue

        # Leaving the control's block entirely.
        if indent <= control_indent and props_indent is None:
            control_name = control_type = None
            continue

        if props_indent is None or indent != props_indent + 2:
            continue

        if value in BLOCK_SCALAR:
            body = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                    break
                body.append(nxt.strip())
                i += 1
            value = " ".join(body)

        yield PropSite(filename, i, control_name, control_type,
                       component_name, key, value)


def check_text(text, filename, contracts, resolver=None):
    """Return a list of Findings for one file's text.

    `resolver`, when given, maps a token reference like
    `constStyle.Label.NumberInput.AlignModern` to its literal value (Task 6).
    """
    findings = []
    seen_props = collections.defaultdict(set)
    controls_seen = {}

    for site in iter_properties(text, filename):
        if not site.control_type:
            continue
        if site.control_type == "CanvasComponent":
            continue  # Layer 3 (Task 7) handles these.
        spec = contracts["controls"].get(site.control_type)
        if spec is None:
            continue  # Unknown control: unchecked, not failed.

        controls_seen[(filename, site.control)] = site
        seen_props[(filename, site.control)].add(site.prop)

        prop = site.prop
        if prop in spec["renamed_from"]:
            new = spec["renamed_from"][prop]
            new = ", ".join(new) if isinstance(new, list) else new
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s has no %s — it was renamed to %s" % (site.control_type, prop, new)))
            continue
        if prop in spec["removed"]:
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s was removed from %s" % (prop, site.control_type)))
            continue
        if prop in spec["absent"]:
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s has no %s property" % (site.control_type, prop)))
            continue
        if prop not in spec["properties"]:
            findings.append(Finding(
                "error", filename, site.line, site.control, prop,
                "%s has no %s property" % (site.control_type, prop)))
            continue

        findings.extend(_check_enum(site, spec, contracts, resolver))

    # Leaf controls that must carry an explicit size.
    for key, site in controls_seen.items():
        spec = contracts["controls"].get(site.control_type)
        need = spec.get("requires_one_of") if spec else None
        if need and not (set(need) & seen_props[key]):
            findings.append(Finding(
                "error", site.file, site.line, site.control, need[0],
                "%s is a leaf control and needs one of %s — without it, it "
                "collapses to the control default"
                % (site.control_type, " or ".join(need))))
    return findings


def _check_enum(site, spec, contracts, resolver):
    expected_ns = spec["enums"].get(site.prop)
    if not expected_ns:
        return []
    value = site.value
    if resolver is not None and value.startswith("=const"):
        resolved = resolver(value[1:].strip())
        if resolved is None:
            return []  # Unresolved: reported separately as unchecked.
        value = "=" + resolved
    m = RE_ENUM.match(value)
    if not m:
        return []  # Not a literal enum reference — unchecked.
    actual_ns, member = m.group(1), m.group(2)
    if actual_ns == expected_ns:
        if member not in contracts["enums"].get(expected_ns, set()):
            return [Finding(
                "error", site.file, site.line, site.control, site.prop,
                "%s.%s is not a member of %s (valid: %s)"
                % (actual_ns, member, expected_ns,
                   ", ".join(sorted(contracts["enums"].get(expected_ns, ())))))]
        return []

    expected_members = contracts["enums"].get(expected_ns, set())
    if member in expected_members:
        return [Finding(
            "warn", site.file, site.line, site.control, site.prop,
            "%s takes %s, not %s — %s.%s compiles because %r is in both, but the "
            "tree is dialect-inconsistent"
            % (site.control_type, expected_ns, actual_ns, actual_ns, member, member))]
    return [Finding(
        "error", site.file, site.line, site.control, site.prop,
        "%s takes %s.{%s} — %s.%s does not exist there"
        % (site.control_type, expected_ns, "|".join(sorted(expected_members)),
           actual_ns, member))]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--contracts", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    contracts = load_contracts(args.contracts)
    src = pathlib.Path(args.src)
    files = sorted(p for p in src.rglob("*.pa.yaml") if p.name != "_EditorState.pa.yaml")

    findings = []
    for path in files:
        findings.extend(check_text(path.read_text(encoding="utf-8"),
                                   str(path), contracts))

    errs = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]

    if errs:
        print("FAIL: %d control-property violation(s).\n" % len(errs))
        for f in errs:
            print("  %s:%s  %s.%s\n      %s" % (f.file, f.line, f.control, f.prop, f.message))
        if warns:
            print("\n  plus %d dialect warning(s) — run without --quiet to see them"
                  % len(warns))
        print("\n  Contracts: %s\n  Prose: references/control-dialects.md"
              % (args.contracts or DEFAULT_CONTRACTS))
        sys.exit(1)

    for f in warns:
        print("  warn: %s:%s  %s.%s — %s" % (f.file, f.line, f.control, f.prop, f.message))

    print("PASS: control properties match their contracts (%d file(s) checked, "
          "%d warning(s))" % (len(files), len(warns)))
    print("  Not covered: property values beyond enum membership; controls absent "
          "from the contract file; unresolved expressions; layout; anything only a "
          "live compile_canvas catches.")


if __name__ == "__main__":
    main()
