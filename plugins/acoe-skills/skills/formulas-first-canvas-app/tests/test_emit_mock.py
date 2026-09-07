"""Mock data must exercise every control, or the app looks broken on first run."""
import datetime
import pathlib
import sys
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import model as m  # noqa: E402
import emit_mock  # noqa: E402

TODAY = datetime.date(2026, 9, 7)


def entity(**over):
    spec = {
        "entity": "Asset", "plural": "Assets",
        "fields": [
            {"name": "Tag", "type": "text", "grid": 100,
             "samples": ["EQ-10041", "EQ-10042", "EQ-10043"]},
            {"name": "Status", "type": "choice", "grid": 120,
             "vocab": ["In Service", "Faulty", "Retired"]},
            {"name": "Health", "type": "choice", "grid": 118,
             "vocab": ["green", "amber", "red"], "semantics": "semafor"},
            {"name": "Amount", "type": "number", "grid": 118, "money": True, "min": 0},
            {"name": "Due", "type": "date", "grid": 112, "semantics": "due"},
            {"name": "Active", "type": "boolean", "grid": 80},
        ],
    }
    spec.update(over)
    return m.Entity(spec)


class TestVocabCoverage(unittest.TestCase):
    def test_every_vocab_value_appears_at_least_once(self):
        """A filter option that yields an empty grid looks like a broken app."""
        e = entity()
        rows = emit_mock.mock_rows(e, n=16, today=TODAY)
        for f in e.choice_fields:
            got = {r[f.name].strip('"') for r in rows}
            self.assertEqual(set(f.vocab) - got, set(),
                             "%s: unused vocab values" % f.name)

    def test_holds_even_when_rows_barely_exceed_vocab_size(self):
        e = entity()
        rows = emit_mock.mock_rows(e, n=3, today=TODAY)
        got = {r["Status"].strip('"') for r in rows}
        self.assertEqual(got, {"In Service", "Faulty", "Retired"})


class TestDates(unittest.TestCase):
    def test_due_dates_emit_date_literals_never_strings(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        for r in rows:
            self.assertRegex(r["Due"], r"^Date\(\d{4}, \d{1,2}, \d{1,2}\)$")

    def test_roughly_thirty_percent_of_due_dates_are_overdue(self):
        """Overdue styling and counters must be visible on first run."""
        rows = emit_mock.mock_rows(entity(), n=20, today=TODAY)
        past = sum(1 for r in rows if emit_mock._parse_date_literal(r["Due"]) < TODAY)
        self.assertGreaterEqual(past, 3)
        self.assertLessEqual(past, 10)


class TestNumbers(unittest.TestCase):
    def test_spread_across_two_orders_of_magnitude(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        vals = [float(r["Amount"]) for r in rows]
        self.assertGreater(max(vals) / max(min(vals), 1), 50)

    def test_min_is_respected(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        self.assertTrue(all(float(r["Amount"]) >= 0 for r in rows))


class TestText(unittest.TestCase):
    def test_samples_are_cycled_not_numbered(self):
        rows = emit_mock.mock_rows(entity(), n=6, today=TODAY)
        tags = [r["Tag"].strip('"') for r in rows]
        self.assertTrue(all(t.startswith("EQ-") for t in tags), tags)
        self.assertNotIn('"Item 1"', tags)

    def test_a_text_field_with_no_samples_still_reads_as_a_record(self):
        e = m.Entity({"entity": "A", "plural": "As",
                      "fields": [{"name": "Title", "type": "text"}]})
        rows = emit_mock.mock_rows(e, n=4, today=TODAY)
        titles = [r["Title"] for r in rows]
        self.assertEqual(len(set(titles)), 4)


class TestKeys(unittest.TestCase):
    def test_composite_keys_are_prefixed_and_unique(self):
        rows = emit_mock.mock_rows(entity(), n=16, today=TODAY)
        keys = [r["Key"] for r in rows]
        self.assertEqual(len(set(keys)), 16)
        self.assertTrue(all("|" in k for k in keys))


class TestTableLiteral(unittest.TestCase):
    def test_emits_a_parseable_table_with_no_bare_clear(self):
        text = emit_mock.mock_table_literal(entity(), 16, TODAY, indent=10)
        self.assertTrue(text.lstrip().startswith("Table("))
        self.assertNotIn("Clear(", text)
        self.assertEqual(text.count("{Key:"), 16)

    def test_every_row_has_every_column(self):
        e = entity()
        text = emit_mock.mock_table_literal(e, 5, TODAY, indent=10)
        for f in e.fields:
            self.assertEqual(text.count(f.name + ":"), 5, f.name)


if __name__ == "__main__":
    unittest.main()
