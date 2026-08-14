#!/usr/bin/env python3
"""Return public holidays for a country in a date range.

Supported countries: CZ, SK, DE, AT, PL, UK, US (2026 + selected 2027).
Extend COUNTRY_HOLIDAYS for more years or countries.

Usage:
    python holidays.py --country CZ --start 2026-05-18 --end 2026-05-24

Exit codes:
    0 — success, JSON list of {"date","name","country"} on stdout
    2 — invalid dates (end before start, bad format)
    3 — country not supported (supported list printed to stderr)

EMAIL_SUFFIX_HINTS exposes the TLD→country map for callers that want to
infer the country from the user's email before invoking this script.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta

EMAIL_SUFFIX_HINTS = {
    ".cz": "CZ",
    ".sk": "SK",
    ".de": "DE",
    ".at": "AT",
    ".pl": "PL",
    ".uk": "UK",
    ".co.uk": "UK",
    ".us": "US",
}

COUNTRY_HOLIDAYS = {
    "CZ": {
        "2026-01-01": "Den obnovy samostatného českého státu",
        "2026-04-03": "Velký pátek",
        "2026-04-06": "Velikonoční pondělí",
        "2026-05-01": "Svátek práce",
        "2026-05-08": "Den vítězství",
        "2026-07-05": "Den slovanských věrozvěstů Cyrila a Metoděje",
        "2026-07-06": "Den upálení mistra Jana Husa",
        "2026-09-28": "Den české státnosti",
        "2026-10-28": "Den vzniku samostatného československého státu",
        "2026-11-17": "Den boje za svobodu a demokracii",
        "2026-12-24": "Štědrý den",
        "2026-12-25": "1. svátek vánoční",
        "2026-12-26": "2. svátek vánoční",
        "2027-01-01": "Den obnovy samostatného českého státu",
        "2027-03-26": "Velký pátek",
        "2027-03-29": "Velikonoční pondělí",
        "2027-05-01": "Svátek práce",
        "2027-05-08": "Den vítězství",
        "2027-07-05": "Den slovanských věrozvěstů Cyrila a Metoděje",
        "2027-07-06": "Den upálení mistra Jana Husa",
        "2027-09-28": "Den české státnosti",
        "2027-10-28": "Den vzniku samostatného československého státu",
        "2027-11-17": "Den boje za svobodu a demokracii",
        "2027-12-24": "Štědrý den",
        "2027-12-25": "1. svátek vánoční",
        "2027-12-26": "2. svátek vánoční",
    },
    "SK": {
        "2026-01-01": "Deň vzniku Slovenskej republiky",
        "2026-01-06": "Zjavenie Pána",
        "2026-04-03": "Veľký piatok",
        "2026-04-06": "Veľkonočný pondelok",
        "2026-05-01": "Sviatok práce",
        "2026-05-08": "Deň víťazstva nad fašizmom",
        "2026-07-05": "Sv. Cyrila a Metoda",
        "2026-08-29": "Výročie SNP",
        "2026-09-01": "Deň Ústavy SR",
        "2026-09-15": "Sedembolestná Panna Mária",
        "2026-11-01": "Sviatok všetkých svätých",
        "2026-11-17": "Deň boja za slobodu a demokraciu",
        "2026-12-24": "Štedrý deň",
        "2026-12-25": "Prvý sviatok vianočný",
        "2026-12-26": "Druhý sviatok vianočný",
    },
    "DE": {
        "2026-01-01": "Neujahrstag",
        "2026-04-03": "Karfreitag",
        "2026-04-06": "Ostermontag",
        "2026-05-01": "Tag der Arbeit",
        "2026-05-14": "Christi Himmelfahrt",
        "2026-05-25": "Pfingstmontag",
        "2026-10-03": "Tag der Deutschen Einheit",
        "2026-12-25": "1. Weihnachtstag",
        "2026-12-26": "2. Weihnachtstag",
    },
    "AT": {
        "2026-01-01": "Neujahr",
        "2026-01-06": "Heilige Drei Könige",
        "2026-04-06": "Ostermontag",
        "2026-05-01": "Staatsfeiertag",
        "2026-05-14": "Christi Himmelfahrt",
        "2026-05-25": "Pfingstmontag",
        "2026-06-04": "Fronleichnam",
        "2026-08-15": "Mariä Himmelfahrt",
        "2026-10-26": "Nationalfeiertag",
        "2026-11-01": "Allerheiligen",
        "2026-12-08": "Mariä Empfängnis",
        "2026-12-25": "Christtag",
        "2026-12-26": "Stefanitag",
    },
    "PL": {
        "2026-01-01": "Nowy Rok",
        "2026-01-06": "Trzech Króli",
        "2026-04-05": "Wielkanoc",
        "2026-04-06": "Poniedziałek Wielkanocny",
        "2026-05-01": "Święto Pracy",
        "2026-05-03": "Święto Konstytucji 3 Maja",
        "2026-05-24": "Zielone Świątki",
        "2026-06-04": "Boże Ciało",
        "2026-08-15": "Wniebowzięcie NMP",
        "2026-11-01": "Wszystkich Świętych",
        "2026-11-11": "Święto Niepodległości",
        "2026-12-25": "Boże Narodzenie",
        "2026-12-26": "Drugi dzień Bożego Narodzenia",
    },
    "UK": {
        "2026-01-01": "New Year's Day",
        "2026-04-03": "Good Friday",
        "2026-04-06": "Easter Monday",
        "2026-05-04": "Early May bank holiday",
        "2026-05-25": "Spring bank holiday",
        "2026-08-31": "Summer bank holiday",
        "2026-12-25": "Christmas Day",
        "2026-12-28": "Boxing Day (substitute)",
    },
    "US": {
        "2026-01-01": "New Year's Day",
        "2026-01-19": "Martin Luther King Jr. Day",
        "2026-02-16": "Presidents' Day",
        "2026-05-25": "Memorial Day",
        "2026-06-19": "Juneteenth",
        "2026-07-03": "Independence Day (observed)",
        "2026-09-07": "Labor Day",
        "2026-10-12": "Columbus Day",
        "2026-11-11": "Veterans Day",
        "2026-11-26": "Thanksgiving",
        "2026-12-25": "Christmas Day",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", required=True, help="ISO country code (CZ/SK/DE/AT/PL/UK/US)")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD inclusive")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD inclusive")
    args = parser.parse_args()

    country = args.country.upper()
    if country not in COUNTRY_HOLIDAYS:
        print(
            json.dumps(
                {
                    "error": f"country '{country}' not supported",
                    "supported": sorted(COUNTRY_HOLIDAYS.keys()),
                }
            ),
            file=sys.stderr,
        )
        return 3

    try:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
    except ValueError as exc:
        print(json.dumps({"error": f"bad date: {exc}"}), file=sys.stderr)
        return 2
    if end < start:
        print(json.dumps({"error": "end before start"}), file=sys.stderr)
        return 2

    table = COUNTRY_HOLIDAYS[country]
    out = []
    d = start
    while d <= end:
        key = d.isoformat()
        if key in table:
            out.append({"date": key, "name": table[key], "country": country})
        d += timedelta(days=1)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
