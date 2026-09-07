#!/usr/bin/env python3
"""Guard: auto-layout sizing that actually renders, not just parses.

None of the other guards look at layout. A tree can pass every architectural,
token, data-layer and control-contract check and still render visually broken,
because Power Apps' modern auto-layout containers silently fall back to a
control default the moment sizing is ambiguous — the documented case is
Gallery, which "defaults to FillPortions 0 and collapses to the ~200px control
default" (see references/control-contracts.yaml) instead of filling the space
it was meant to. This guard generalizes that one counted case into four
static rules that catch the same failure family before it reaches a live app:

  R1 every `FillPortions: =0` (fixed) child of an auto-layout container
     carries an explicit size on the parent's MAIN axis — Width for a
     Horizontal parent, Height for a Vertical one. `LayoutMinHeight` (or
     `LayoutMinWidth`) does NOT substitute — it bounds auto-sizing, it does
     not provide it, and a fixed child ignores it entirely.
  R2 every auto-layout container has either an explicit size on itself
     (Width or Height) or at least one flexible child (`FillPortions` present
     and not `=0`) — otherwise its own size is undetermined.
  R3 a leaf control (anything but a GroupContainer, CanvasComponent,
     ModernText or Text — see COVERAGE LIMITS) that is a direct child of an
     auto-layout container needs SOME sizing info — `FillPortions` or an
     explicit Width/Height — or it collapses to its control default.
  R4 `Visible:` on a flexible (`FillPortions` present and not `=0`) child is
     flagged. An invisible child is dropped from auto-layout ENTIRELY, not
     hidden in place — the gap it held collapses and the layout shifts with
     whatever made it invisible. A fixed (`FillPortions: =0`) child toggling
     Visible is the normal, safe pattern (cmp_Header's back/menu buttons do
     exactly this) and is not flagged; only a flexible child's Visible is a
     collapsing-gap bug. The fix is to keep it Visible and blank whatever it
     displays (a spacer keeps `Text: =""` and stays visible).

    python3 check_layout.py --src path/to/Src

Exits non-zero on any violation, PASS/FAIL as the first line, so it drops into
CI or new_app.py's own guard list the same way every other check_*.py does.

PARSER: property values (FillPortions, Width, Height, Visible, LayoutDirection,
LayoutMin*) are read via check_control_props.iter_properties — this guard does
NOT re-implement that state machine, so it inherits its coverage limits
verbatim: block scalars are consumed whole, an off-indent property line inside
a Properties block is skipped (and counted), and a `Variant:`/`ComponentName:`
sibling of `Control:` does not end the control's block. See that module's own
docstring for the full list.

COVERAGE LIMITS beyond what iter_properties already carries:
  * Parent/child NESTING and each control's `Variant:` are NOT something
    iter_properties exposes (it deliberately does not yield `Variant:` as a
    property — see its docstring), so this guard adds one small, separate,
    indentation-based scan of `- name:` control-item lines (the same RE_ITEM
    shape iter_properties itself parses control boundaries from) to recover
    them. This is NOT a second property-value parser: every property VALUE
    used by the four rules above still comes from iter_properties. A control
    name is assumed unique within one file — the same invariant
    check_control_props.py's own per-file `seen_props`/`controls_seen` dicts
    already rely on.
  * Only `Variant: AutoLayout` GroupContainers are treated as auto-layout
    containers. `ManualLayout` containers (absolute X/Y positioning) and
    Gallery's own `Variant: Vertical`/`Horizontal` template layout are out of
    scope for R1/R2/R4 (a Gallery's OWN sizing, as a leaf, is still covered by
    R3) — Power Apps' auto-layout distribution rules do not apply there.
  * R1 and R3 do not apply to `CanvasComponent` instances. A component
    definition's own root `Properties:` supply a real, working Height/Width
    formula for every instance that does not override them — that is a
    cross-file fact (the definition lives in a different `.pa.yaml` than the
    instance) this guard cannot see, and check_control_props.py's own
    UNIVERSAL_INSTANCE_PROPS precedent already treats Height/Width as
    optional-to-restate at the instance site for exactly this reason (its own
    comment cites a compiled reference app with 19 Width-setting instances
    against a higher total instance count). Requiring every instance to
    restate its own component's default would be checking something that is
    already correct by construction. R2 and R4 still apply to a
    `CanvasComponent` instance used AS an auto-layout container's child
    (R4: a flexible, conditionally-invisible component instance still drops
    the same way a primitive control would).
  * R3 does not apply to `ModernText`/`Text`. R1 (main-axis sizing on an
    explicit `FillPortions: =0`) and R2 (a container's own sizing) still do —
    this carve-out is narrow, R3 only. A text leaf's "control default" along
    the CROSS axis of a Vertical container (the common case: a label above an
    input) is its own natural content height, not a Gallery-style forced
    ~200px that steals space from something meant to fill it — the failure
    class R3 exists to catch does not apply the same way here. This was
    discovered by running this guard against emit_screens.py's OWN generated
    form screens (an unmodifiable module per this skill's task brief): every
    generated form label uses exactly this pattern — no Width, no Height, no
    FillPortions — identically to every hand-authored template and component
    in this repo. That is not an oversight to fix in twelve places; it is
    evidence the rule's initial scope was wrong about which leaf controls
    have a genuinely bad default. `AutoHeight: =true` (Text/ModernText's own
    genuine self-measuring property) remains a fine, MORE explicit way to
    write the same thing and several components use it, but R3 no longer
    requires it.
  * R1/R2's "main axis" test reads the PARENT's own `LayoutDirection` value
    textually (looking for the substring `Horizontal` or `Vertical`); a
    parent whose `LayoutDirection` is absent, unresolved, or set through an
    indirection this guard cannot read the value of is left unchecked for R1
    and counted, rather than guessed at.
  * A top-level Screen or ComponentDefinition's OWN direct children are never
    "children of an auto-layout container" (a Screen/component root is not
    itself a GroupContainer), so R1/R3/R4 never fire on them — only R2 can,
    and only for a GroupContainer among them.
  * Anything only a live compile_canvas run can catch (this guard is static).
"""
import argparse
import collections
import pathlib
import sys

import check_control_props as ccp

SKILL = pathlib.Path(__file__).resolve().parents[1]

Finding = collections.namedtuple("Finding", "rule file line control message")

SIZE_PROPS = ("Width", "Height")


def _peek_meta(lines, start_idx, item_indent):
    """Look ahead from a `- name:` item line for its `Control:`/`Variant:`
    siblings — the same fields `Control:`/`Variant:` occupy in
    iter_properties, which stops at the first of `Properties:`/`Children:`
    or a shallower indent. Cheap: these siblings sit within 1-3 lines of the
    item line in every shape this skill uses."""
    control_type = variant = None
    j = start_idx
    while j < len(lines):
        nxt = lines[j]
        if not nxt.strip():
            j += 1
            continue
        nindent = len(nxt) - len(nxt.lstrip())
        if nindent <= item_indent:
            break
        m = ccp.RE_KEY.match(nxt)
        if m:
            key, val = m.group(2), m.group(3).strip()
            if key == "Control":
                control_type = val
            elif key == "Variant":
                variant = val
            elif key in ("Properties", "Children"):
                break
        j += 1
    return control_type, variant


def build_structure(text):
    """Return {control_name: {"parent": name_or_None, "type": ..., "variant":
    ..., "line": lineno}}, built from a lightweight scan of `- name:` item
    lines (ccp.RE_ITEM) plus their immediate Control:/Variant: siblings.

    See the module docstring's COVERAGE LIMITS: this recovers exactly the two
    things iter_properties does not expose (nesting depth, `Variant:`) and
    nothing else — property values are not read here.
    """
    meta = {}
    stack = []  # list of (indent, name)
    lines = text.splitlines()
    for i, raw in enumerate(lines):
        m = ccp.RE_ITEM.match(raw)
        if not m:
            continue
        indent = len(m.group(1))
        name = m.group(2)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else None
        stack.append((indent, name))
        control_type, variant = _peek_meta(lines, i + 1, indent)
        meta[name] = {"parent": parent, "type": control_type,
                      "variant": variant, "line": i + 1}
    return meta


def collect_props(text, filename, counts=None):
    """Map control name -> {prop: value}, via check_control_props's own
    property-block parser (not re-implemented here)."""
    props = collections.defaultdict(dict)
    for site in ccp.iter_properties(text, filename, counts=counts):
        if site.control:
            props[site.control][site.prop] = site.value
    return props


def check_text(text, filename, counts=None):
    """Return a list of Findings for one file's text. See the module
    docstring for the four rules and their coverage limits."""
    if counts is None:
        counts = collections.Counter()

    meta = build_structure(text)
    props = collect_props(text, filename, counts=counts)

    children_of = collections.defaultdict(list)
    for name, m in meta.items():
        if m["parent"] is not None:
            children_of[m["parent"]].append(name)

    def is_autolayout(name):
        return meta.get(name, {}).get("variant") == "AutoLayout"

    def is_flexible(control_props):
        fp = control_props.get("FillPortions")
        return fp is not None and fp != "=0"

    findings = []

    for name, m in meta.items():
        cprops = props.get(name, {})
        parent = m["parent"]
        line = m["line"]

        if parent is not None and is_autolayout(parent):
            parent_props = props.get(parent, {})
            direction = parent_props.get("LayoutDirection", "") or ""

            # ---- R1: fixed child needs the parent's main-axis size --------
            # CanvasComponent instances are exempt: the component's own
            # definition file supplies a working Height/Width default for
            # any instance that doesn't override it (see COVERAGE LIMITS).
            if m["type"] != "CanvasComponent" and cprops.get("FillPortions") == "=0":
                if "Horizontal" in direction:
                    needed = "Width"
                elif "Vertical" in direction:
                    needed = "Height"
                else:
                    needed = None
                    counts["layout_direction_unknown"] += 1
                if needed and needed not in cprops:
                    minprop = "LayoutMin" + needed
                    hint = ""
                    if minprop in cprops:
                        hint = (" (%s is set, but LayoutMin%s is ignored for "
                                "a fixed child — it bounds auto-sizing, it "
                                "does not provide it)" % (minprop, needed))
                    findings.append(Finding(
                        "R1", filename, line, name,
                        "FillPortions: =0 child of %r (a %s auto-layout "
                        "container) has no explicit %s%s"
                        % (parent, direction.split(".")[-1] or "?",
                           needed, hint)))

            # ---- R3: leaf control needs FillPortions or an explicit size --
            # GroupContainer is R2's concern instead (its own sizing, not a
            # leaf-default collapse); CanvasComponent is exempt for the same
            # cross-file reason as R1 (see COVERAGE LIMITS). ModernText/Text
            # are exempt too — their own "control default" is their natural
            # content height, not a Gallery-style forced collapse (see
            # COVERAGE LIMITS for how this was discovered and why it is
            # narrow to R3 only).
            if m["type"] not in ("GroupContainer", "CanvasComponent",
                                  "ModernText", "Text"):
                if not (("FillPortions" in cprops) or
                        any(p in cprops for p in SIZE_PROPS)):
                    findings.append(Finding(
                        "R3", filename, line, name,
                        "%s %r is a leaf child of auto-layout container %r "
                        "with neither FillPortions nor an explicit Width or "
                        "Height — it collapses to its control default"
                        % (m["type"] or "control", name, parent)))

            # ---- R4: Visible: on a flexible child --------------------------
            if is_flexible(cprops) and "Visible" in cprops:
                findings.append(Finding(
                    "R4", filename, line, name,
                    "%r is a flexible child (FillPortions: %s) that also "
                    "sets Visible — an invisible child is dropped from "
                    "auto-layout entirely, so the gap it held collapses and "
                    "the layout shifts with the data; keep it Visible and "
                    "blank whatever it displays instead"
                    % (name, cprops.get("FillPortions"))))

        # ---- R2: every auto-layout container needs sizing or a flexible
        # child -------------------------------------------------------------
        if is_autolayout(name):
            has_explicit_size = any(p in cprops for p in SIZE_PROPS)
            has_flexible_child = any(
                is_flexible(props.get(k, {})) for k in children_of.get(name, []))
            if not has_explicit_size and not has_flexible_child:
                findings.append(Finding(
                    "R2", filename, line, name,
                    "auto-layout container %r has no explicit Width/Height "
                    "and no flexible (FillPortions != 0) child — its own "
                    "size is undetermined" % name))

    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    args = ap.parse_args(argv)

    src = pathlib.Path(args.src)
    if not src.is_dir():
        sys.exit("error: --src is not a directory: %s" % src)
    files = sorted(p for p in src.rglob("*.pa.yaml") if p.name != "_EditorState.pa.yaml")
    if not files:
        sys.exit("error: no *.pa.yaml files found under %s — is --src correct? "
                  "A guard that silently checks nothing is worse than no guard." % src)

    counts = collections.Counter()
    findings = []
    for path in files:
        findings.extend(check_text(path.read_text(encoding="utf-8"),
                                   str(path), counts=counts))

    if findings:
        print("FAIL: %d layout violation(s).\n" % len(findings))
        for f in findings:
            print("  %s:%s  [%s] %s\n      %s" % (f.file, f.line, f.rule, f.control, f.message))
        print("\n  Prose: this file's own module docstring (`check_layout.py --help`).")
        sys.exit(1)

    print("PASS: auto-layout sizing is consistent (%d file(s) checked, %d unchecked)"
          % (len(files), sum(counts.values())))
    print("  Unchecked: %d fixed child/children whose parent's LayoutDirection "
          "could not be resolved (R1 skipped for them), %d off-indent "
          "property line(s) inside a Properties block (iter_properties's own "
          "limit)."
          % (counts["layout_direction_unknown"], counts["off_indent"]))
    print("  Not covered: property values beyond FillPortions/Width/Height/"
          "Visible/LayoutDirection; ManualLayout containers and Gallery's own "
          "template layout; cross-axis (stretch/hug) sizing; anything only a "
          "live compile_canvas catches. Inherits check_control_props.py's "
          "own parser coverage limits (see this module's docstring).")


if __name__ == "__main__":
    main()
