#!/usr/bin/env python3
"""Mock data generation for scaffolded Canvas Apps.

WHY THIS EXISTS: the defect that started this whole effort was a scaffolder
whose generated app called Clear(colItems) right after seeding its mock rows,
so every app it produced rendered as an empty grid on first run — one was
pushed to a live environment that way. Mock data in this codebase is not
decoration; it is the proof a generated app renders correctly and exercises
every control (every filter option has at least one matching row, overdue
styling is visible, money fields span a realistic range, dates are real
Date() values a gallery can sort and filter on) the moment it is opened.

Determinism: nothing here calls `random` and nothing reads the real current
date — `today` is always supplied by the caller. Two calls with identical
(entity, n, today) inputs must produce byte-identical output, because a
later assembly step diffs generated trees for exact reproducibility.
"""
from __future__ import annotations

import datetime
import re

_DATE_RE = re.compile(r"^Date\((\d{4}), (\d{1,2}), (\d{1,2})\)$")

# Multipliers chosen to spread numeric mock values across roughly two orders
# of magnitude (10x base .. 1400x base) so a bar chart or a sort-by-amount
# view looks like it has real variance, not five copies of the same number.
_NUMBER_MULTIPLIERS = (1, 3, 12, 47, 140)
_NUMBER_BASE = 10.0

# Used only when a text field has no `samples` in the model. Words are
# combined with the field name and cycled so rows read like distinct records
# ("Central Title Record", "North Title Record", ...) rather than the
# "Item 1", "Item 2" placeholder pattern this generator exists to avoid.
_RECORD_WORDS = (
    "Central", "North", "Harbor", "Summit", "Cedar", "Union", "Lakeside",
    "Meridian", "Riverside", "Highland",
)
_RECORD_SUFFIXES = ("Record", "Entry", "Case", "File", "Log", "Ticket")


def _quote(text):
    """Render a Python string as a Power Fx text literal, doubling inner quotes."""
    return '"' + text.replace('"', '""') + '"'


def _choice_value(field, i):
    """Row i gets vocab[i % len(vocab)].

    Because i is 0-based, this maps rows 0..len(vocab)-1 to distinct vocab
    values one-for-one *before* anything repeats — so the "every vocab value
    appears" guarantee holds even when n barely exceeds len(vocab). Applied
    independently per choice field (each field cycles its own vocab off the
    same row index).
    """
    vocab = field.vocab
    return vocab[i % len(vocab)]


def _text_value(field, i):
    """Cycle `samples` when present; otherwise compose a distinct, readable
    value from the field name and row index so it reads like a real record."""
    if field.samples:
        return field.samples[i % len(field.samples)]
    word = _RECORD_WORDS[i % len(_RECORD_WORDS)]
    suffix = _RECORD_SUFFIXES[(i // len(_RECORD_WORDS)) % len(_RECORD_SUFFIXES)]
    return "%s %s %s" % (word, field.name, suffix)


def _number_value(field, i):
    """Spread across two orders of magnitude by cycling a multiplier list,
    then clamp to min/max when given. Money is rounded to 2dp here (and
    again at format time, which is harmless and keeps the two paths honest
    independently)."""
    mult = _NUMBER_MULTIPLIERS[i % len(_NUMBER_MULTIPLIERS)]
    val = _NUMBER_BASE * mult + i
    if field.min is not None:
        val = max(val, field.min)
    if field.max is not None:
        val = min(val, field.max)
    if field.money:
        val = round(val, 2)
    return val


def _boolean_value(field, i):
    return i % 2 == 0


def _due_date_value(i, today):
    """~30% of rows land before `today` (overdue), the rest after, spread
    over +/-90 days so overdue styling and "N overdue" counters are visible
    on first run. The split is deterministic, not random: every block of 10
    rows puts its first 3 in the past."""
    if i % 10 < 3:
        days = -(1 + (i * 7) % 90)
    else:
        days = 1 + (i * 13) % 90
    return today + datetime.timedelta(days=days)


def _forward_date_value(i, today):
    """Date fields without `semantics: due` just spread forward from today."""
    return today + datetime.timedelta(days=i * 5)


def _date_value(field, i, today):
    if field.semantics == "due":
        return _due_date_value(i, today)
    return _forward_date_value(i, today)


def _raw_value(field, i, today):
    """The row's value for this field, as a plain Python value (not yet a
    Power Fx literal string)."""
    if field.type == "choice":
        return _choice_value(field, i)
    if field.type in ("text", "longtext"):
        return _text_value(field, i)
    if field.type == "number":
        return _number_value(field, i)
    if field.type == "boolean":
        return _boolean_value(field, i)
    if field.type == "date":
        return _date_value(field, i, today)
    raise ValueError("emit_mock: unhandled field type %r for field %r"
                     % (field.type, field.name))


def _format_value(field, raw):
    """Render one field's raw Python value as a Power Fx literal string."""
    if field.type == "boolean":
        return "true" if raw else "false"
    if field.type == "date":
        return "Date(%d, %d, %d)" % (raw.year, raw.month, raw.day)
    if field.type == "number":
        if field.money:
            return "%.2f" % raw
        if float(raw).is_integer():
            return str(int(raw))
        return str(raw)
    # text, longtext, choice all render as quoted text literals.
    return _quote(raw)


def _key_prefix(entity, row_raw_values):
    """PREFIX for the Key column: the first choice field's value for this
    row (uppercased, alnum only, first 3 chars) when the entity has a choice
    field, else the entity name. Uniqueness itself comes from appending the
    row index in `mock_rows`, not from this prefix."""
    choice_fields = entity.choice_fields
    source = str(row_raw_values[choice_fields[0].name]) if choice_fields else entity.entity
    letters = "".join(ch for ch in source.upper() if ch.isalnum())
    return letters[:3] or entity.entity.upper()[:3] or "REC"


def mock_rows(entity, n=16, today=None):
    """Build `n` mock rows for `entity`.

    `n` is the ROW COUNT (an int) — how many mock rows to generate — not a
    collection of rows to format. `today` must be an explicit `datetime.date`;
    generation never reads the real current date, so the same (entity, n,
    today) always produces the same rows.

    Returns a list of `n` dicts. Each dict has a "Key" entry plus one entry
    per field in `entity.fields`, and every value is already rendered as a
    ready-to-splice Power Fx literal string: quoted text for text/longtext/
    choice fields, `Date(y, m, d)` for dates, `true`/`false` for booleans,
    and a bare numeral for numbers.
    """
    if today is None:
        raise ValueError(
            "mock_rows: `today` must be an explicit datetime.date — mock data must "
            "never depend on the real current date, or two runs would not agree")
    rows = []
    for i in range(n):
        raw = {f.name: _raw_value(f, i, today) for f in entity.fields}
        prefix = _key_prefix(entity, raw)
        row = {"Key": _quote("%s|%d" % (prefix, i))}
        for f in entity.fields:
            row[f.name] = _format_value(f, raw[f.name])
        rows.append(row)
    return rows


def _parse_date_literal(s):
    """Test/debug helper: parse a `Date(y, m, d)` literal string back into a
    `datetime.date`. Module-level so tests can reach it as
    `emit_mock._parse_date_literal`; not used by the emitters themselves."""
    match = _DATE_RE.match(s)
    if not match:
        raise ValueError("emit_mock: not a Date(...) literal: %r" % s)
    year, month, day = (int(part) for part in match.groups())
    return datetime.date(year, month, day)


def _render_row(entity, row):
    parts = ["Key: %s" % row["Key"]]
    for f in entity.fields:
        parts.append("%s: %s" % (f.name, row[f.name]))
    return "{" + ", ".join(parts) + "}"


def mock_table_literal(entity, n, today, indent=0):
    """Render the full `Table({...}, {...})` mock literal for `entity`, ready
    to splice into a `ClearCollect(colX, <this>)` call.

    `n` is the ROW COUNT (an int), not a collection of rows — it is passed
    straight through to `mock_rows`. `indent` is the number of leading
    spaces at which the `Table(` call itself sits; each row is indented four
    spaces deeper than that, one row per line, `Key` first.
    """
    rows = mock_rows(entity, n, today)
    pad = " " * indent
    row_pad = " " * (indent + 4)
    lines = [row_pad + _render_row(entity, r) for r in rows]
    body = ",\n".join(lines)
    return "%sTable(\n%s\n%s)" % (pad, body, pad)
