#!/usr/bin/env python3
"""Validate an ACOE Team Hub post folder against the team-hub-post contract.

Team Hub derives its /automation-solutions listing from each post's
frontmatter and there is no central index. A broken post therefore does not
fail loudly -- it silently disappears from the listing. Nothing between the
upload and the portal checks a post, so this script is what turns that silent
failure into an error.

Exit codes
    0  valid (warnings may still be printed)
    1  at least one ERROR -- do not publish

Usage
    python scripts/validate_post.py <post-folder>
    python scripts/validate_post.py <post-folder> --allow-english-only
    python scripts/validate_post.py <library-root> --all --format azdo
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# The contract. Keep in step with SKILL.md.
# --------------------------------------------------------------------------- #

REQUIRED_KEYS = ("title", "desc", "category", "business", "author", "added")
# `role` renders after the author on the detail page ("Author -- Role").
# titleCz/descCz are read ONLY from the English file, as the Czech listing
# texts when there is no .cz.md (content.js: pick(cz.title, en.titleCz)).
OPTIONAL_KEYS = ("tags", "role")

# Spelled as the listing already spells them: the filter pills group by the
# exact string, so "RPA (UiPath)" would be a second pill beside "RPA".
CATEGORIES = {
    "Power Apps", "Power BI", "RPA", "Reporting", "Power Automate", "SharePoint",
    "AI", "Code", "Excel", "Copilot Studio", "n8n",
}

BUSINESS_AREAS = {
    "Finance", "Sales", "HR", "PMO", "Network Deployment", "Network Operations",
    "Legal", "Procurement", "IT", "Wholesale", "Regulatory", "Automation CoE",
}

# The three-column storyline block renders only when all three sections are
# found. Mirrors kindOf() in portal/automation-solutions/index.html: any H2-H4,
# compared case-insensitively with `*` and `:` stripped, against ONE bilingual
# synonym set -- an English heading in a Czech post matches just as well.
# Keep in step with that function; it is the thing that actually decides.
STORYLINE_KINDS = {
    "initial": ("initial state", "original state", "as is",
                "původní stav", "originální status"),
    "current": ("current state", "actual state",
                "aktuální stav", "současný stav"),
    "benefits": ("benefits", "benefits & statistics",
                 "benefity", "benefity & statistiky", "výhody", "přínosy"),
}
# What a new post should use -- the spellings most of the library already has.
HOUSE_STYLE = {
    "EN": ("### ORIGINAL STATE", "### CURRENT STATE", "### BENEFITS"),
    "CZ": ("### PŮVODNÍ STAV", "### AKTUÁLNÍ STAV", "### BENEFITY"),
}
HEADING_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$", re.M)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AUTHOR_RE = re.compile(r"^[^\W\d_][\w'-]+(?:\s+[^\W\d_][\w'-]+)+$", re.UNICODE)
FM_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*):\s*(.*)$")
MEDIA_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")

MEDIA_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".webm"}
VIDEO_EXT = {".mp4", ".webm"}
ALLOWED_EXT = MEDIA_EXT | {".md", ".pdf"}

MAX_VIDEO_BYTES = 110 * 1024 * 1024
# Czech carries the same content in fewer words than English -- no articles,
# and cases do the work prepositions do -- so an equivalent post scores lower.
# A single floor would systematically reject correct Czech.
MIN_BODY_WORDS = {"EN": 90, "CZ": 70}

# Finder / Office droppings. upload-batch takes everything in the folder, so
# they would land in the container next to the post -- warn, the author deletes.
IGNORED_RE = re.compile(r"^(\.DS_Store|Thumbs\.db|desktop\.ini|~\$.*)$", re.I)

# OneDrive conflict copies. These DO end in .md and DO start with the slug, so
# upload-batch would put a second markdown file next to the post: not listed
# (the listing takes <slug>.md only) but served, and the wrong version waiting
# to be pasted over the right one. This is the dangerous case and must be an
# error.
CONFLICT_RE = re.compile(r"-[A-Z][\w' .-]*(MacBook|iMac|Mac ?mini|PC|Laptop|Notebook)", re.I)


@dataclass
class Report:
    slug: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def split_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    problems: list[str] = []
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        return {}, text, ["frontmatter must start on line 1 with `---`"]
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text, ["frontmatter is never closed with `---`"]

    fm: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        m = FM_LINE_RE.match(raw)
        if not m:
            problems.append(f"not a single-line `key: value` pair: {raw!r}")
            continue
        key, value = m.group(1), m.group(2).strip()
        if key in fm:
            problems.append(f"duplicate frontmatter key `{key}`")
        fm[key] = value

    return fm, "\n".join(lines[end + 1:]), problems


def check_frontmatter(fm: dict[str, str], rep: Report, label: str) -> None:
    for key in REQUIRED_KEYS:
        if not fm.get(key):
            rep.error(f"{label}: required frontmatter `{key}` is missing or empty")

    cat = fm.get("category")
    if cat and cat not in CATEGORIES:
        rep.error(
            f"{label}: category {cat!r} is not a known technology "
            f"(expected one of: {', '.join(sorted(CATEGORIES))})"
        )
    if cat and ("," in cat or "/" in cat):
        rep.error(f"{label}: category must be exactly one technology, got {cat!r}")
    if cat == "Power Platform":
        rep.error(
            f"{label}: `Power Platform` is not a portal category -- resolve it to "
            "Power Apps, Power Automate or Power BI from Used Applications"
        )

    biz = fm.get("business")
    if biz and biz not in BUSINESS_AREAS:
        rep.warn(f"{label}: business {biz!r} is not in the known list -- it will render as a new filter pill")

    added = fm.get("added")
    if added:
        try:
            when = dt.date.fromisoformat(added)
        except ValueError:
            rep.error(f"{label}: `added` must be YYYY-MM-DD, got {added!r}")
        else:
            if when > dt.date.today() + dt.timedelta(days=1):
                rep.warn(f"{label}: `added` is in the future ({added}) -- it will pin to the top of the listing")

    author = fm.get("author")
    if author and not AUTHOR_RE.match(author):
        rep.error(f"{label}: `author` must be `Surname Firstname` (e.g. `Horák Dominik`), got {author!r}")

    desc = fm.get("desc", "")
    if desc and len(desc) > 120:
        rep.warn(
            f"{label}: `desc` is {len(desc)} chars -- the band shows three lines and the card "
            "four, the rest runs on in the body; keep it to one whole sentence of at most 120"
        )

    known = REQUIRED_KEYS + OPTIONAL_KEYS + (("titleCz", "descCz") if label == "EN" else ())
    for key in fm:
        if key not in known:
            rep.warn(f"{label}: unknown frontmatter key `{key}` will be ignored")

    if label == "CZ" and ("titleCz" in fm or "descCz" in fm):
        rep.warn(
            "CZ: titleCz/descCz in the Czech file do nothing -- the portal reads "
            "this file's own `title`/`desc` for the Czech listing"
        )


def first_paragraph(body: str) -> str:
    """The first blank-line-delimited block, joined into a single line.

    A bold lead is normally hard-wrapped across several lines, so testing only
    the first LINE for a closing ** rejects every correctly wrapped post --
    both templates in references/ included.
    """
    block: list[str] = []
    for line in body.splitlines():
        if line.strip():
            block.append(line.strip())
        elif block:
            break
    return " ".join(block)


def storyline_kinds(body: str) -> set[str]:
    """Which storyline sections the portal would find -- see STORYLINE_KINDS."""
    found = set()
    for _, text in HEADING_RE.findall(body):
        norm = " ".join(text.lower().replace("*", "").replace(":", "").split())
        for kind, names in STORYLINE_KINDS.items():
            if norm in names:
                found.add(kind)
    return found


def check_body(body: str, rep: Report, label: str, slug: str, folder: Path) -> None:
    lead = first_paragraph(body)
    if not lead:
        rep.error(f"{label}: body is empty")
        return

    # House style, not a contract: the card deck comes from `desc`, never from
    # the body, so a plain opening paragraph still renders correctly.
    if lead.startswith("#"):
        rep.warn(f"{label}: opens with a heading -- a **bold lead paragraph** reads better as the elevator pitch")
    elif not (lead.startswith("**") and lead.endswith("**")):
        rep.warn(f"{label}: the lead paragraph is not bold -- wrap the elevator pitch in ** **")

    found = storyline_kinds(body)
    missing = [k for k in ("initial", "current", "benefits") if k not in found]
    if missing:
        house = HOUSE_STYLE.get(label, HOUSE_STYLE["EN"])
        rep.warn(
            f"{label}: nothing matches the storyline section(s) {', '.join(missing)} -- "
            f"the three-column block renders only when all three are found. "
            f"House style is {', '.join(house)}"
        )
    elif label == "CZ" and any(
        " ".join(h.lower().replace("*", "").replace(":", "").split())
        in ("original state", "current state", "actual state", "benefits", "initial state", "as is")
        for _, h in HEADING_RE.findall(body)
    ):
        rep.warn("CZ: storyline headings are in English -- the block renders, but write them in Czech")

    floor = MIN_BODY_WORDS.get(label, MIN_BODY_WORDS["EN"])
    words = len(re.findall(r"\w+", body))
    if words < floor:
        rep.error(f"{label}: body is only {words} words -- too thin to publish (minimum {floor})")

    for ref in MEDIA_REF_RE.findall(body):
        if ref.startswith(("http://", "https://")):
            if "my.sharepoint.com/personal/" in ref or "-my.sharepoint.com" in ref:
                rep.error(f"{label}: media on personal OneDrive ({ref}) will 403 for every other user")
            continue
        prefix = f"/solutions/{slug}/"
        if not ref.startswith(prefix):
            rep.error(f"{label}: media path {ref!r} must be absolute as `{prefix}<file>`")
            continue
        name = ref[len(prefix):]
        if not (folder / name).is_file():
            rep.error(f"{label}: references `{name}` but that file is not in the folder")

    for link in re.findall(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)", body):
        if link.startswith(f"/solutions/{slug}/") and Path(link).suffix.lower() in VIDEO_EXT:
            rep.error(
                f"{label}: local video {link!r} is linked, not embedded -- "
                f"use image syntax `![]({link})` for the inline player"
            )


def validate_folder(folder: Path, *, allow_english_only: bool) -> Report:
    slug = folder.name
    rep = Report(slug=slug)

    if not SLUG_RE.match(slug):
        rep.error(
            f"slug {slug!r} must be kebab-case ASCII (a-z, 0-9, single hyphens) -- "
            "the slug is the public URL and can never be renamed"
        )

    for child in folder.iterdir():
        if child.is_dir():
            rep.error(f"`{child.name}/` -- post folders are flat, no subfolders allowed")
        elif child.name == "index.json":
            rep.error("index.json is obsolete: the listing is derived from frontmatter. Delete it.")
        elif IGNORED_RE.match(child.name):
            rep.warn(f"`{child.name}` would be uploaded with the post -- delete it first")
        elif CONFLICT_RE.search(child.stem):
            rep.error(
                f"`{child.name}` is a OneDrive conflict copy -- it would be uploaded next to "
                "the real post. Delete it and re-check the original."
            )
        elif child.suffix.lower() not in ALLOWED_EXT and not child.name.startswith("."):
            rep.warn(f"`{child.name}` has an unexpected extension for a Team Hub post")

    en = folder / f"{slug}.md"
    cz = folder / f"{slug}.cz.md"

    if not en.is_file():
        rep.error(f"missing required English post `{slug}.md`")
    if not cz.is_file():
        if allow_english_only:
            rep.warn(f"missing Czech post `{slug}.cz.md` -- English-only was explicitly allowed")
        else:
            rep.error(
                f"missing Czech post `{slug}.cz.md` -- Czech is required when a person is "
                "writing (pass --allow-english-only for the unattended path)"
            )

    for path, label in ((en, "EN"), (cz, "CZ")):
        if not path.is_file():
            continue
        fm, body, problems = split_frontmatter(path.read_text(encoding="utf-8"))
        for p in problems:
            rep.error(f"{label}: {p}")
        if fm:
            check_frontmatter(fm, rep, label)
            check_body(body, rep, label, slug, folder)

    if not any(p.suffix.lower() in MEDIA_EXT for p in folder.iterdir() if p.is_file()):
        rep.warn("no media in the folder -- the post will publish without a gallery")

    for video in folder.glob("*"):
        if video.suffix.lower() in VIDEO_EXT:
            size = video.stat().st_size
            if size > MAX_VIDEO_BYTES:
                rep.error(
                    f"`{video.name}` is {size / 1048576:.0f} MB -- keep demo videos under "
                    f"{MAX_VIDEO_BYTES // 1048576} MB (H.264)"
                )
            if not (folder / f"{video.stem}-poster.jpg").is_file():
                rep.warn(f"`{video.name}` has no `{video.stem}-poster.jpg` -- the player shows a black first frame")

    return rep


def emit(reports: list[Report], fmt: str, strict: bool) -> int:
    n_err = sum(len(r.errors) for r in reports)
    n_warn = sum(len(r.warnings) for r in reports)

    for rep in reports:
        if not rep.errors and not rep.warnings:
            print(f"  OK    {rep.slug}")
            continue
        print(f"\n  {rep.slug}")
        for msg in rep.errors:
            print(f"    ERROR   {msg}")
            if fmt == "azdo":
                print(f"##vso[task.logissue type=error]{rep.slug}: {msg}")
        for msg in rep.warnings:
            print(f"    WARN    {msg}")
            if fmt == "azdo":
                print(f"##vso[task.logissue type=warning]{rep.slug}: {msg}")

    print(f"\n{len(reports)} post(s) checked -- {n_err} error(s), {n_warn} warning(s)")
    if n_err or (strict and n_warn):
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="the post folder, or a root with --all")
    ap.add_argument("--all", action="store_true", help="treat PATH as a root and check every subfolder")
    ap.add_argument("--allow-english-only", action="store_true",
                    help="downgrade the missing-Czech error to a warning (unattended path)")
    ap.add_argument("--format", choices=("plain", "azdo"), default="plain")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    if not args.path.is_dir():
        print(f"not a directory: {args.path}", file=sys.stderr)
        return 1

    folders = sorted(p for p in args.path.iterdir() if p.is_dir()) if args.all else [args.path]
    if not folders:
        print("nothing to validate")
        return 0

    print(f"Validating {len(folders)} post folder(s)\n")
    return emit(
        [validate_folder(f, allow_english_only=args.allow_english_only) for f in folders],
        args.format,
        args.strict,
    )


if __name__ == "__main__":
    raise SystemExit(main())
