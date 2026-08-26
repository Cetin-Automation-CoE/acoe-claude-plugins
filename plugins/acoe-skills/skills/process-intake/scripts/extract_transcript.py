#!/usr/bin/env python3
"""
Extract a meeting transcript into a line-numbered, timestamped text file plus JSON.

Handles the formats intake recordings actually arrive in:
  .docx  - Teams "Meeting Recording" transcript exports (the common case at CETIN)
  .vtt   - WebVTT, from Teams/Stream/Zoom "download transcript"
  .srt   - SubRip
  .txt   - already-plain transcripts with "Speaker  mm:ss" turn headers

Why this exists: you will need to cite timestamps constantly, and you will need to
grep the transcript dozens of times while reconstructing the process. Both are much
easier against a stable, line-numbered file where every line belongs to a known turn
at a known time. Reading a .docx directly gives you neither.

Usage:
    python extract_transcript.py INPUT [-o OUTDIR]

Writes into OUTDIR (default: alongside the input):
    transcript.txt   - line-numbered, one turn per block: "[7] Speaker Name   12:34"
    transcript.json  - [{idx, speaker, time, seconds, text, line}] for programmatic use
    summary.txt      - duration, speaker turn counts, and the turn index for quick orientation

Then work against transcript.txt with Grep/Read. Every line number in transcript.json
maps to transcript.txt, so a grep hit tells you the timestamp immediately.
"""

import argparse
import json
import os
import re
import sys
import zipfile


# ---------------------------------------------------------------- helpers

TIME_RE = re.compile(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?")


def to_seconds(t):
    """'1:12:58' or '12:58' -> int seconds. Returns None if unparseable."""
    if not t:
        return None
    m = TIME_RE.fullmatch(t.strip())
    if not m:
        return None
    h, mm, ss, _ = m.groups()
    return int(h or 0) * 3600 + int(mm) * 60 + int(ss)


def fmt_time(sec):
    if sec is None:
        return ""
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ---------------------------------------------------------------- readers

def read_docx_paragraphs(path):
    """Pull paragraph text out of a .docx without needing python-docx installed."""
    try:
        import docx  # noqa
        d = docx.Document(path)
        return [p.text for p in d.paragraphs]
    except Exception:
        pass
    # Fallback: parse the XML directly. Teams exports are simple enough for this.
    import xml.etree.ElementTree as ET
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    out = []
    for p in root.iter(f"{W}p"):
        out.append("".join(t.text or "" for t in p.iter(f"{W}t")))
    return out


# Teams turn header: "Mach Milan   12:34" or "Speaker 2 (Room name (Teams))   1:12:58"
TURN_HEADER = re.compile(r"^\s*(?P<speaker>.*?)\s{2,}(?P<time>(?:\d{1,2}:)?\d{1,2}:\d{2})\s*$")
# Looser variant for transcripts that use a single space or a dash
TURN_HEADER_LOOSE = re.compile(
    r"^\s*(?P<speaker>[^\d].{0,80}?)\s*[-–—]?\s*[\[(]?(?P<time>(?:\d{1,2}:)?\d{1,2}:\d{2})[\])]?\s*:?\s*$"
)


def parse_turn_lines(lines):
    """Split a flat list of text lines into turns using 'Speaker   mm:ss' headers."""
    turns = []
    cur = None
    preamble = []
    for raw in lines:
        line = (raw or "").rstrip()
        if not line.strip():
            continue
        m = TURN_HEADER.match(line) or TURN_HEADER_LOOSE.match(line)
        if m and m.group("speaker").strip():
            if cur:
                turns.append(cur)
            cur = {
                "speaker": m.group("speaker").strip(),
                "time": m.group("time"),
                "seconds": to_seconds(m.group("time")),
                "lines": [],
            }
        elif cur is not None:
            cur["lines"].append(line.strip())
        else:
            preamble.append(line.strip())
    if cur:
        turns.append(cur)
    return turns, preamble


def parse_vtt_srt(text):
    """WebVTT / SRT cues -> turns. Consecutive cues by the same speaker are merged."""
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    cues = []
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        # find the timing line
        ti = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if ti is None:
            continue
        start = lines[ti].split("-->")[0].strip()
        start = re.sub(r"[.,]\d+$", "", start)
        rest = lines[ti + 1:]
        speaker = None
        # Some Teams exports put the speaker on its own line as "@1" / "@2" between the
        # timing line and the text. Without this the whole meeting collapses to one speaker.
        if rest and re.fullmatch(r"@\d+", rest[0].strip()):
            speaker = "Mluvčí " + rest[0].strip()[1:]
            rest = rest[1:]
        body = " ".join(rest).strip()
        if not body:
            continue
        # "<v Milan Mach>text" or "Milan Mach: text"
        vm = re.match(r"<v\s+([^>]+)>\s*(.*)", body)
        if vm:
            speaker, body = vm.group(1).strip(), vm.group(2).strip()
        elif speaker is None:
            cm = re.match(r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^:]{1,60}):\s+(.*)", body)
            if cm:
                speaker, body = cm.group(1).strip(), cm.group(2).strip()
        body = re.sub(r"</?[vc][^>]*>", "", body).strip()
        cues.append({"speaker": speaker or "(neoznačený mluvčí)", "time": start,
                     "text": body})

    turns = []
    for c in cues:
        secs = to_seconds(c["time"])
        if turns and turns[-1]["speaker"] == c["speaker"]:
            turns[-1]["lines"].append(c["text"])
            turns[-1]["line_times"].append(secs)
        else:
            turns.append({
                "speaker": c["speaker"],
                "time": fmt_time(secs),
                "seconds": secs,
                "lines": [c["text"]],
                "line_times": [secs],
            })
    return turns, []



# ---- Teams web-export format (common for Czech "Přepis" downloads) -------------
# Speaker name on its own line, then a duration line, then the utterances:
#
#   Mluvcí 2 (Room (Teams))
#   0 min 18 s.0:18
#   @2 0 min 18 s.
#   Jaky formě vy chcete ...
#
# Single stray capital letters (avatar initials) and the "@N" marker lines are noise.

TEAMS_TIME = re.compile(
    r"^\s*(?:(?P<h>\d+)\s*(?:h|hod[^\W\d]*)\.?\s*)?(?P<m>\d+)\s*(?:min[^\W\d]*)\.?\s*"
    r"(?P<s>\d+)\s*(?:s|sek[^\W\d]*)\.?"
    r"\s*(?P<clock>(?:\d{1,2}:)?\d{1,2}:\d{2})?\s*$")
# Some exports repeat the attribution inside the turn as "Name 47 min 39 s." - that is
# metadata, not speech, and counting it inflates the word count the coverage check relies on.
TEAMS_ATTRIB = re.compile(
    r"^\s*(?P<who>.*?)\s*\d+\s*(?:min[^\W\d]*)\.?\s*\d+\s*(?:s|sek[^\W\d]*)\.?\s*$")
TEAMS_MARKER = re.compile(r"^\s*@\d+\b")
PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")


def looks_like_teams_export(lines):
    hits = sum(1 for l in lines[:400] if TEAMS_TIME.match(l or ""))
    return hits >= 5


def parse_teams_export(lines):
    """Speaker line, then a duration line, then utterances until the next speaker."""
    clean = []
    for raw in lines:
        # Teams emits private-use glyphs (U+E000-U+F8FF) as layout artefacts. They are
        # not speech, and left in place they inflate the word count the coverage check
        # depends on -- so strip them before anything else looks at the line.
        l = PRIVATE_USE.sub("", raw or "").strip()
        if not l:
            continue
        if len(l) <= 2 and l.isalpha() and l.isupper():   # avatar initial
            continue
        clean.append(l)

    turns, preamble, i, n = [], [], 0, len(clean)
    while i < n:
        line = clean[i]
        tm = TEAMS_TIME.match(line)
        if tm and turns:
            # a bare timestamp inside the current turn - just skip it
            i += 1
            continue
        if tm and not turns:
            i += 1
            continue
        # A speaker header is a non-time line followed by a duration line that also
        # carries the clock suffix ("0 min 28 s.0:28"). Bare duration lines are
        # intra-turn utterance markers -- without this test, a one-word utterance
        # followed by its own marker gets mistaken for a speaker name.
        nxt_t = TEAMS_TIME.match(clean[i + 1]) if i + 1 < n else None
        if nxt_t and nxt_t.group("clock") and not TEAMS_MARKER.match(line):
            speaker = line
            t = nxt_t
            if t.group("clock"):
                secs = to_seconds(t.group("clock"))
            else:
                secs = (int(t.group("h") or 0) * 3600 + int(t.group("m")) * 60
                        + int(t.group("s")))
            i += 2
            body = []
            while i < n:
                nxt = clean[i]
                nt = TEAMS_TIME.match(clean[i + 1]) if i + 1 < n else None
                if (nt and nt.group("clock") and not TEAMS_TIME.match(nxt)
                        and not TEAMS_MARKER.match(nxt)):
                    break                      # next speaker header
                if TEAMS_TIME.match(nxt) or TEAMS_MARKER.match(nxt):
                    i += 1
                    continue
                am = TEAMS_ATTRIB.match(nxt)
                if am and (not am.group("who") or am.group("who") == speaker):
                    i += 1                      # repeated attribution line
                    continue
                body.append(nxt)
                i += 1
            if turns and turns[-1]["speaker"] == speaker:
                turns[-1]["lines"].extend(body)      # merge consecutive same-speaker turns
            else:
                turns.append({"speaker": speaker, "time": fmt_time(secs),
                              "seconds": secs, "lines": body})
            continue
        if not turns:
            preamble.append(line)
        elif not TEAMS_MARKER.match(line):
            turns[-1]["lines"].append(line)
        i += 1
    return turns, preamble


# ---------------------------------------------------------------- main

def extract(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        # Teams packs an entire turn -- header line plus every utterance -- into a
        # single Word paragraph separated by soft line breaks, so flatten first.
        paras = read_docx_paragraphs(path)
        joined = "\n\n".join(paras)
        if "-->" in joined[:8000]:
            # Teams also exports VTT cues wrapped one-per-paragraph inside a .docx.
            return parse_vtt_srt(joined)
        lines = []
        for p in paras:
            lines.extend((p or "").split("\n"))
        return parse_turn_lines(lines)
    text = open(path, encoding="utf-8", errors="replace").read()
    if ext in (".vtt", ".srt") or "-->" in text[:4000]:
        return parse_vtt_srt(text)
    lines = text.split("\n")
    if looks_like_teams_export(lines):
        return parse_teams_export(lines)
    turns, pre = parse_turn_lines(lines)
    if not turns and looks_like_teams_export(lines):
        return parse_teams_export(lines)
    return turns, pre


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()

    outdir = args.outdir or os.path.dirname(os.path.abspath(args.input)) or "."
    os.makedirs(outdir, exist_ok=True)

    turns, preamble = extract(args.input)
    if not turns:
        print("ERROR: no turns found. Inspect the file manually — the turn-header "
              "pattern may differ from 'Speaker   mm:ss'.", file=sys.stderr)
        sys.exit(2)

    # Render the line-numbered text file, recording each turn's line number.
    out_lines = []
    if preamble:
        for p in preamble:
            out_lines.append(f"# {p}")
        out_lines.append("")
    records = []
    for i, t in enumerate(turns):
        header_line = len(out_lines) + 1
        out_lines.append(f"[{i}] {t['speaker']}   {t['time']}")
        lt = t.get("line_times") or []
        for j, l in enumerate(t["lines"]):
            # Continuation lines carry their own cue time when it differs from the turn
            # start, so a grep hit anywhere inside a long turn is still citable.
            stamp = ""
            if j < len(lt) and lt[j] is not None and lt[j] != t.get("seconds"):
                stamp = f"[{fmt_time(lt[j])}] "
            out_lines.append(f"    {stamp}{l}")
        out_lines.append("")
        records.append({
            "idx": i,
            "speaker": t["speaker"],
            "time": t["time"],
            "seconds": t["seconds"],
            "text": " ".join(t["lines"]),
            "line": header_line,
            "cues": [{"time": fmt_time(x), "text": y}
                     for x, y in zip(t.get("line_times") or [], t["lines"])
                     if x is not None],
        })

    txt_path = os.path.join(outdir, "transcript.txt")
    json_path = os.path.join(outdir, "transcript.json")
    sum_path = os.path.join(outdir, "summary.txt")

    open(txt_path, "w", encoding="utf-8").write("\n".join(out_lines))
    open(json_path, "w", encoding="utf-8").write(
        json.dumps(records, ensure_ascii=False, indent=1))

    # Summary: duration, who spoke how much, and a coarse turn index for orientation.
    secs = [r["seconds"] for r in records if r["seconds"] is not None]
    duration = max(secs) if secs else None
    counts, words = {}, {}
    for r in records:
        counts[r["speaker"]] = counts.get(r["speaker"], 0) + 1
        words[r["speaker"]] = words.get(r["speaker"], 0) + len(r["text"].split())

    s = [f"source        : {os.path.basename(args.input)}",
         f"turns         : {len(records)}",
         f"duration      : {fmt_time(duration)}" if duration else "duration      : unknown",
         "",
         "speakers (turns / words) — the one with the most words is usually the process owner:"]
    for sp in sorted(words, key=lambda k: -words[k]):
        s.append(f"  {words[sp]:7d} words  {counts[sp]:4d} turns   {sp}")
    # Coverage check. A transcript can look fine and still be missing the middle:
    # transcription drops out during screen-share, or the export is truncated. A large
    # silent gap is the difference between "a quiet stretch" and "the walkthrough is
    # not in this file" -- and that must be caught BEFORE anyone writes an analysis.
    gaps = []
    for a, b in zip(records, records[1:]):
        if a["seconds"] is not None and b["seconds"] is not None:
            d = b["seconds"] - a["seconds"]
            if d >= 120:
                gaps.append((a, b, d))
    spoken = sum(len(r["text"].split()) for r in records)
    s += ["", f"words transcribed: {spoken}"]
    if duration and duration > 60:
        density = spoken / (duration / 60.0)
        s.append(f"words per minute of recording: {density:.0f}"
                 + ("   <-- LOW: expect ~100-150 wpm for a walkthrough" if density < 40 else ""))
    if gaps:
        s += ["", f"!! {len(gaps)} silent gap(s) of 2 minutes or more -- content may be missing:"]
        for a, b, d in gaps:
            s.append(f"   {a['time']:>8} -> {b['time']:<8} ({d // 60} min {d % 60} s with no speech)"
                     f"   after turn [{a['idx']}]")
        s.append("   Check the source before analysing: a gap covering the demonstration means")
        s.append("   the walkthrough is not in this file and no analysis can be built from it.")
    s += ["", "turn index every ~5 minutes (for orientation before you read in detail):"]
    nxt = 0
    for r in records:
        if r["seconds"] is not None and r["seconds"] >= nxt:
            snippet = r["text"][:90].replace("\n", " ")
            s.append(f"  [{r['idx']:4d}] line {r['line']:5d}  {r['time']:>8}  {r['speaker'][:28]:28} {snippet}")
            nxt = r["seconds"] + 300
    open(sum_path, "w", encoding="utf-8").write("\n".join(s))

    print(f"wrote {txt_path}")
    print(f"wrote {json_path}")
    print(f"wrote {sum_path}")
    print()
    print("\n".join(s[:14]))


if __name__ == "__main__":
    main()
