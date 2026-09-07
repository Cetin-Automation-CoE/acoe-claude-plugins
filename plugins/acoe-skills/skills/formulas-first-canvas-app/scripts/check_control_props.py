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
  * layout correctness beyond the leaf-control size rule (layout is Phase 2)
  * anything only a live compile_canvas run can catch

SEVERITY: a property in a control's curated `renamed_from`, `removed`, or `absent`
list is a hard ERROR — the contract file KNOWS it is wrong. A property simply
missing from a control's `properties` list is a WARNING — the contract file is
not exhaustive, so absence there means "not verified," not "invalid." Errors
fail the run; warnings do not.

UNCHECKED sites (unresolved token paths, properties on a control type absent
from the contract file entirely, and property lines the parser could not
attribute to any control) are counted and reported, never silently dropped.
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
# Used both for a control property's enum literal (_check_enum) and a component
# instance property's bare enum literal (_check_instance) — one pattern, two
# call sites; kept as a single name so there is nothing to accidentally let
# drift apart.
RE_ENUM = re.compile(r"^=\s*'?([A-Za-z][\w.]*?)'?\.([A-Za-z]\w*)\s*$")
BLOCK_SCALAR = ("|", "|-", "|+", ">", ">-", ">+")


def strip_trailing_comment(value):
    """Drop a trailing `  # comment` from a property value, honoring quotes.

    `Control: ModernText  # a label` and `Align: =Align.Right  # right` are
    legal YAML/Power Fx but defeat exact-match parsing (RE_ENUM anchors on
    `$`, and an unknown-with-comment control type silently drops its whole
    block) unless the comment is stripped first. Only a `#` preceded by
    whitespace (or at position 0) outside a double-quoted string counts as a
    comment marker, so `"#FFAA00"` and similar in-string hashes survive.
    """
    in_quotes = False
    for i, ch in enumerate(value):
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == "#" and not in_quotes and (i == 0 or value[i - 1].isspace()):
            return value[:i].rstrip()
    return value


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


RE_TOKEN_OPEN = re.compile(r"^([A-Za-z_]\w*)\s*[:=]\s*\{\s*$")
RE_TOKEN_LEAF = re.compile(r"^([A-Za-z_]\w*)\s*:\s*(.+?),?\s*$")


def parse_tokens(text):
    """Parse a Power Fx token record into {dotted.path: literal}.

    Handles the one-key-per-line record style the skill's design-tokens file uses:

        constStyle = {
            Label: {
                NumberInput: {
                    AlignModern: 'TextCanvas.Align'.End,

    COVERAGE LIMIT: inline records (`Height: {Large: 40, Medium: 32}`) are recorded
    as opaque leaves, not descended into. Callers resolving a path below one get
    None and treat the site as unchecked rather than clean.
    """
    mapping = {}
    stack = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.endswith("};") or line == "}" or line == "},":
            if stack:
                stack.pop()
            continue
        m = RE_TOKEN_OPEN.match(line)
        if m:
            stack.append(m.group(1))
            continue
        m = RE_TOKEN_LEAF.match(line)
        if m and not m.group(2).startswith("{"):
            mapping[".".join(stack + [m.group(1)])] = m.group(2).rstrip(",").strip()
    return mapping


def make_resolver(mapping):
    """Return a resolver closing over a token map; unknown paths give None."""
    def resolve(path):
        return mapping.get(path)
    return resolve


RE_CMP_NAME = re.compile(r"^(\s*)(cmp_[\w]+):\s*$")
RE_PROP_NAME = re.compile(r"^(\s*)([A-Za-z_]\w*):\s*$")
RE_DATATYPE = re.compile(r"^\s*DataType:\s*(\w+)\s*$")


def parse_component_defs_text(text):
    """Map component name -> {input property name: DataType}.

    Only PropertyKind Input/Output properties carry a DataType; Events do not and
    are recorded with DataType None so an instance may still set them.

    COVERAGE LIMIT: relies on an implicit invariant of this skill's own
    ComponentDefinitions shape — a bare `Name:` line (nothing after the colon)
    is a property/field name, while every value-bearing line (an instance
    assignment, or a `PropertyKind:`/`DisplayName:`/`Description:`/`Default:`
    field) carries something after the colon. That invariant has been verified
    against all 8 shipped `components/cmp_*.pa.yaml` files, including
    cmp_FilterButton's custom property literally named `DataType` (its own
    nested `DataType: Text` field resolves correctly because indentation, not
    the key's name, decides what it belongs to). It has NOT been exercised
    against component shapes outside this repo — a `ComponentDefinitions` block
    with a different formatting convention could defeat it silently.
    """
    defs = {}
    current = None
    cmp_indent = None
    prop = None
    prop_indent = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        m = RE_CMP_NAME.match(raw)
        if m:
            current = m.group(2)
            cmp_indent = indent
            defs.setdefault(current, {})
            prop = None
            continue
        if current is None:
            continue
        if indent <= cmp_indent:
            current = None
            continue
        m = RE_DATATYPE.match(raw)
        if m and prop:
            defs[current][prop] = m.group(1)
            continue
        m = RE_PROP_NAME.match(raw)
        if m and m.group(2) not in ("CustomProperties", "Properties", "Children"):
            if prop_indent is None or indent == prop_indent:
                prop_indent = indent
                prop = m.group(2)
                defs[current].setdefault(prop, None)
    return defs


def parse_component_defs(paths):
    defs = {}
    for path in paths:
        defs.update(parse_component_defs_text(
            pathlib.Path(path).read_text(encoding="utf-8")))
    return defs


def iter_properties(text, filename, counts=None):
    """Yield a PropSite per property line, tracking the enclosing control.

    Control blocks look like:

        - lbl_Row_Title:
            Control: ModernText
            Variant: SomeVariant   # optional, sits BEFORE Properties
            Properties:
              Color: =...

    `Variant:` (and `ComponentName:`) are real siblings of `Control:` at the
    SAME indent, appearing before `Properties:` — every GroupContainer and
    Gallery in this repo's own templates carries one. The control-leaving
    check below must not treat that sibling as "we left the block," or every
    property under it is silently orphaned (control_type None) — this is
    exactly what made the guard blind to `gal_List_Items`'s missing
    `FillPortions` before the fix (Ruling 13).

    Multi-line block scalars (`Items: |-`) are consumed whole so their bodies are
    never mistaken for property lines.

    `counts`, when given, is a `collections.Counter`-like mapping incremented
    for off-indent property lines seen inside an active `Properties:` block
    (indent deeper than the block's own +2 step, e.g. a multi-line inline
    record that is not a `|`/`>` block scalar) — these are silently skipped
    rather than misparsed, but the skip is now visible instead of mute (I3/I4).
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
        key, value = m.group(2), strip_trailing_comment(m.group(3).strip())

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

        # Leaving the control's block entirely — but a sibling key of Control:
        # (Variant, or anything else at the identical indent) is NOT that; only
        # a shallower indent means we have actually stepped back out.
        if indent < control_indent and props_indent is None:
            control_name = control_type = None
            continue

        if props_indent is None or indent != props_indent + 2:
            if counts is not None and props_indent is not None and indent > props_indent:
                counts["off_indent"] += 1
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


def check_text(text, filename, contracts, resolver=None, components=None, counts=None):
    """Return a list of Findings for one file's text.

    `resolver`, when given, maps a token reference like
    `constStyle.Label.NumberInput.AlignModern` to its literal value (Task 6).

    `components`, when given, maps a component name to its declared
    `{property: DataType}` inputs, so CanvasComponent instances are checked
    against their own contract instead of the control-property one (Task 7).

    `counts`, when given, is a `collections.Counter`-like mapping this
    function increments for every UNCHECKED site: a property line with no
    control context, a property on a control type absent from the contract
    file entirely, an unresolved token reference, and (via `iter_properties`)
    an off-indent property line. These are reported, never silently dropped
    (I3/I4) — a guard that never says what it skipped invites the same
    "All checks pass" blindness this whole task exists to close.

    SEVERITY (Ruling 14): a property in `renamed_from`, `removed`, or `absent`
    is a curated negative — the contract file KNOWS it is wrong, so it is a
    hard ERROR. A property simply missing from `properties` is a WARNING: the
    contract file's own header says absence there means "not verified," not
    "invalid," and the compiled reference app proves the lists are not
    exhaustive enough to carry hard-error semantics.
    """
    findings = []
    seen_props = collections.defaultdict(set)
    controls_seen = {}

    for site in iter_properties(text, filename, counts=counts):
        if not site.control_type:
            if counts is not None:
                counts["no_control_context"] += 1
            continue
        if site.control_type == "CanvasComponent":
            if components and site.component_name in components:
                findings.extend(_check_instance(
                    site, components[site.component_name], contracts))
            continue
        spec = contracts["controls"].get(site.control_type)
        if spec is None:
            if counts is not None:
                counts["unknown_control"] += 1
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
                "warn", filename, site.line, site.control, prop,
                "%s not in the contract file for %s — unverified, not "
                "necessarily invalid" % (prop, site.control_type)))
            continue

        findings.extend(_check_enum(site, spec, contracts, resolver, counts))

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


def _check_enum(site, spec, contracts, resolver, counts=None):
    expected_ns = spec["enums"].get(site.prop)
    if not expected_ns:
        return []
    value = site.value
    if resolver is not None and value.startswith("=const"):
        resolved = resolver(value[1:].strip())
        if resolved is None:
            if counts is not None:
                counts["unresolved_token"] += 1
            return []  # Unresolved: reported separately as unchecked.
        value = "=" + resolved
    m = RE_ENUM.match(value)
    if not m:
        return []  # Not a literal enum reference — unchecked.
    actual_ns, member = m.group(1), m.group(2)
    if actual_ns not in contracts["enums"]:
        return []  # token path or variable, not an enum literal — unchecked
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


# Ruling 10: universal placement/layout properties every CanvasComponent instance
# carries regardless of its own CustomProperties — these are control properties, not
# custom inputs, so a component that never declares them is not "missing" them. Do
# not delete this as redundant: measured directly against the compiled reference app
# (occurrence counts across component instances there: Height 20, Width 19,
# LayoutMinWidth 10, LayoutMinHeight 10, LayoutMaxHeight 10, Visible 6, Y 5).
# This is a FALLBACK for properties the component does NOT declare — a component
# that explicitly declares one of these (e.g. a custom `Width: DataType: Number`
# input) is checked against that declaration instead; see `_check_instance` below.
# Deliberately excluded: OnSelect, Color — on this skill's components those are
# real declared Event/Input properties and must keep resolving through the
# declaration, not this allowlist.
UNIVERSAL_INSTANCE_PROPS = {
    "X", "Y", "Width", "Height", "Visible", "FillPortions", "AlignInContainer",
    "LayoutMinWidth", "LayoutMinHeight", "LayoutMaxWidth", "LayoutMaxHeight",
    "TabIndex", "DisplayMode",
}


def _check_instance(site, declared, contracts):
    """Check one CanvasComponent instance property against its declaration.

    Ruling 15 (C3): Ruling 6 taught `_check_enum` that ANY dotted value is not
    necessarily an enum literal — `ThisItem.Title`, `Parent.Width`, `Self.Text`
    and `constStyle.Header.Title` all match the same regex shape as a real
    `Namespace.Member` enum reference but are property/record/token paths, not
    enums. That fix never reached `_check_instance` (added later, Task 7),
    which received no `contracts` at all — so every one of those hard-errored
    as DataType-Text-gets-an-enum on any Text-typed component input. Same
    fix, same reasoning: a namespace this contract file has never heard of is
    not a literal enum reference, so it is unchecked, not wrong.
    """
    if site.prop not in declared:
        if site.prop in UNIVERSAL_INSTANCE_PROPS:
            return []  # Universal control property, not a custom input — unchecked.
        return [Finding(
            "error", site.file, site.line, site.control, site.prop,
            "component %s declares no %s input (declared: %s)"
            % (site.component_name, site.prop,
               ", ".join(sorted(declared)) or "none"))]
    datatype = declared[site.prop]
    if datatype != "Text":
        return []
    m = RE_ENUM.match(site.value)
    if not m:
        return []
    actual_ns = m.group(1)
    if actual_ns not in contracts["enums"]:
        return []  # ThisItem/Parent/Self/token path, not an enum literal — unchecked.
    return [Finding(
        "error", site.file, site.line, site.control, site.prop,
        "%s.%s is DataType Text — pass the string \"%s\", not the enum %s.%s"
        % (site.component_name, site.prop, m.group(2), m.group(1), m.group(2)))]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--contracts", default=None)
    ap.add_argument("--tokens-file", default=None,
                    help="Power Fx fragment defining constStyle etc. "
                         "Defaults to <src>/App.pa.yaml, where new_app.py inlines them.")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress dialect-warning lines (PASS/FAIL summary still prints)")
    args = ap.parse_args()

    contracts = load_contracts(args.contracts)
    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit("error: --src is not a directory: %s" % src)
    files = sorted(p for p in src.rglob("*.pa.yaml") if p.name != "_EditorState.pa.yaml")
    if not files:
        sys.exit("error: no *.pa.yaml files found under %s — is --src correct? "
                  "A guard that silently checks nothing is worse than no guard." % src)

    resolver = None
    token_text = ""
    if args.tokens_file:
        token_text = pathlib.Path(args.tokens_file).read_text(encoding="utf-8")
    else:
        app = src / "App.pa.yaml"
        if app.exists():
            token_text = app.read_text(encoding="utf-8")
    if token_text:
        resolver = make_resolver(parse_tokens(token_text))

    # C4 (Ruling 16): the skill's own bundled components/ are a FALLBACK — a
    # target app's own copy of, say, cmp_Header must win. Precedence is
    # decided by dict.update() overwrite order: list the skill's fallback
    # copies FIRST so anything the target repo defines under Components/ or
    # directly under --src is applied afterwards and wins.
    comp_dirs = [SKILL / "components", src / "Components", src]
    comp_paths = []
    for d in comp_dirs:
        if d.exists():
            comp_paths.extend(sorted(d.glob("cmp_*.pa.yaml")))
    components = parse_component_defs(comp_paths)

    counts = collections.Counter()
    findings = []
    for path in files:
        findings.extend(check_text(path.read_text(encoding="utf-8"),
                                   str(path), contracts, resolver=resolver,
                                   components=components, counts=counts))

    errs = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    unchecked = sum(counts.values())

    if errs:
        print("FAIL: %d control-property violation(s).\n" % len(errs))
        for f in errs:
            print("  %s:%s  %s.%s\n      %s" % (f.file, f.line, f.control, f.prop, f.message))
        if warns:
            if args.quiet:
                print("\n  plus %d dialect warning(s) (suppressed by --quiet)" % len(warns))
            else:
                print()
                for f in warns:
                    print("  warn: %s:%s  %s.%s — %s"
                          % (f.file, f.line, f.control, f.prop, f.message))
        print("\n  Contracts: %s\n  Prose: references/control-dialects.md"
              % (args.contracts or DEFAULT_CONTRACTS))
        sys.exit(1)

    if not args.quiet:
        for f in warns:
            print("  warn: %s:%s  %s.%s — %s" % (f.file, f.line, f.control, f.prop, f.message))

    print("PASS: control properties match their contracts (%d file(s) checked, "
          "%d warning(s), %d unchecked)" % (len(files), len(warns), unchecked))
    print("  Unchecked: %d unresolved token reference(s), %d property site(s) on a "
          "control type absent from the contract file, %d property site(s) with no "
          "control context, %d off-indent property line(s) inside a Properties block."
          % (counts["unresolved_token"], counts["unknown_control"],
             counts["no_control_context"], counts["off_indent"]))
    print("  Not covered: property values beyond enum membership; layout; anything "
          "only a live compile_canvas catches.")


if __name__ == "__main__":
    main()
