# Presentation layout for Step 4

Show the assembled Idea in chat in exactly this shape. No provenance annotations on fields,
the conversation already shows where things came from.

---

**ACOE Idea — návrh k odsouhlasení**

| Pole | Hodnota |
|---|---|
| Summary | … |
| Requestor | Příjmení Jméno |
| Department | … |
| Components | RPA / Power Platform / Power BI / AI / Excel |
| Used Applications | …, …, … |
| External ID | WP… / *(žádné)* |
| Due date | … |
| Target start | … |
| Target end | … |

**Business case — vstupy do scoringu**

| Pole | Hodnota |
|---|---|
| Affected People | 12 |
| Monthly Runs per Person | … |
| Minutes per Run | … |
| Monthly Run Cost | … CZK/měsíc |
| Other Cash Saved / Month | … CZK/měsíc |
| Effort Estimation | M (5-10 MD) |
| PR Potential | Low / Medium / High / Flagship — *nechat prázdné, dokud si uživatel nevybere* |

Under the second table, show the derived saving on one line so the user can check it before
Jira computes it:

**Úspora:** `<lidí> × <běhů/os./měsíc> × <minut> = <hodin> h/měsíc ≈ <MD> MD/měsíc`
(kontrola: `<běhů> × <minut>` = `<minut/měsíc na osobu>`, strop je 10 080)

Team is always Automation CoE and is set automatically, and Priority Override is left to
Jira's own `Standard` default, so neither appears as a row to be decided. PR Potential has no default: show the row empty until the user chooses, never
pre-filled with a suggestion.

Do not show Saved FTEs, Net Benefit 3Y, ROI 3Y, Payback Months or Idea Priority as rows.
Jira calculates them and showing a guess invites the user to correct a number we do not set.

**Description**

> full text as it will be submitted, in the source language, starting with the `## Shrnutí` block

**Business Case Description**

> full text as it will be submitted

**Nevyplněno:** list the empty fields in one line, so the gaps are explicit rather than
invisible.

**Předpoklady k ověření:** any number you derived or converted (team total → per person,
daily → monthly, quarterly → monthly, weighted averages), one line each.

---

Then close with the three options: **založit v Jira** / **upravit** (which field) /
**nechat jako draft**.

Do not create the issue until the user picks the first one.
