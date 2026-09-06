# ACOE Idea — field reference

Everything needed to fill the template and to build a valid `createJiraIssue` call.

**Snapshot taken from live Jira metadata on 2026-09-06** (re-verified same day after the
Affected People field was rebuilt) (`getJiraIssueTypeMetaWithFields`,
project `ACOE`, issue type `Idea` = `10016`, cloudId `c0888f66-71ea-425a-b9e3-2b8f4c553d31`).
The short closed lists below (Affected People, Effort Estimation, PR Potential, Priority
Override, Components, Used Applications) are complete as of that date, so **do not call Jira
just to read them**. **Requestor and Department are never cached** and are always fetched
live, in one shared call (§5).

## Contents

1. Field map
2. The scoring model: which fields feed which calculation
3. The four benefit fields, per technology
4. Allowed values (complete lists)
5. Resolving Requestor and Department (always live)
6. Content format and the Business Case ADF gotcha
7. Workflow status
8. Worked `createJiraIssue` payload
9. Failure modes

---

## 1. Field map

Fixed for every ACOE Idea: `projectKey: "ACOE"`, `issueTypeName: "Idea"`.

### Input fields — the skill fills these

| Template field | Jira name | API key | Type / format |
|---|---|---|---|
| Summary | Summary | `summary` (top-level) | string, 3–8 words |
| Description | Description | `description` (top-level) | markdown string |
| Business Case Description | Business Case Description | `customfield_10089` | **textarea → ADF** (§6) |
| Requestor | Requestor | `customfield_10071` | select → `{"value": "Příjmení Jméno"}` |
| Department | Department | `customfield_10079` | select → `{"value": "..."}` |
| Components | Components | `components` | `[{"name": "RPA"}]` — `name`, not `value` |
| Used Applications | Used Applications | `customfield_10106` | multiselect → `[{"value": "..."}, ...]` |
| Affected People | Affected People | `customfield_11363` | number (headcount) |
| Monthly Runs per Person | Monthly Runs per Person | `customfield_10081` | number |
| Minutes per Run | Minutes per Run | `customfield_10082` | number |
| Monthly Run Cost | Monthly Run Cost | `customfield_11261` | number (CZK/month) |
| Other Cash Saved / Month | Other Cash Saved / Month | `customfield_10090` | number (CZK/month) |
| Effort Estimation | Effort Estimation | `customfield_10080` | select → `{"value": "M (5-10 MD)"}` |
| PR Potential | PR Potential | `customfield_11262` | select → `{"value": "Low"}` |
| Team | Team | `customfield_10001` | bare UUID string, always Automation CoE |
| External ID | External ID | `customfield_10062` | plain text string, e.g. `WP3560` |
| Due date | Due date | `duedate` | date `YYYY-MM-DD` |
| Target start | Target start | `customfield_10022` | date `YYYY-MM-DD` |
| Target end | Target end | `customfield_10023` | date `YYYY-MM-DD` |

### Calculated fields — never write to these

Jira computes them from the inputs above. Writing to them corrupts the backlog ranking.

| Jira name | API key |
|---|---|
| Saved FTEs | `customfield_10103` |
| Net Benefit 3Y | `customfield_11296` |
| ROI 3Y | `customfield_10083` |
| Payback Months | `customfield_11297` |
| Idea Priority | `customfield_10105` |

### On the create screen but out of scope

`attachment` (cannot be set through `createJiraIssue` at all), `labels`, `parent`,
`customfield_11330` People Working On It (delivery assigns it later), and **Priority Override
`customfield_11263`** — see below.

### Priority Override — never send it

`customfield_11263` has a Jira-side default of **`Standard`** (confirmed in the live metadata,
`hasDefaultValue: true`). Omitting it is therefore correct and produces the right value.

**Never ask the user about it and never put it in the payload.** It is the backlog owner's
ranking control, applied in the Jira UI after intake, not something an intake conversation
decides. This is the opposite of Effort Estimation, whose default is actively wrong.

### Team — always set it

`customfield_10001` is always **Automation CoE** = `99e75e3e-d31e-4aae-941a-f60e8e548378`,
passed as a **bare UUID string**. Passing the team's name fails with
`Team with id '<n>' not found.` Set it on every Idea and do not ask the user.

The field is on the Idea create screen and verified populated with that UUID on 2026-09-06.
Send it on create. Note that Atlassian Team fields often do not appear in
`getJiraIssueTypeMetaWithFields` even when settable, so its absence there means nothing. In the
unlikely event a create is rejected naming `customfield_10001`, re-create without it and set it
afterwards with `editJiraIssue`; a rejected create makes no issue, so retrying cannot
duplicate anything.

If the UUID ever stops working, recover it with:

```
Atlassian Rovo:searchJiraIssuesUsingJql
  jql: project = ACOE AND Team IS NOT EMPTY ORDER BY created DESC
  fields: ["summary", "customfield_10001"]
```

and read `customfield_10001.id` from any hit.

### External ID — ask for it

`customfield_10062` is a **plain text field**, back on the Idea create screen as of 2026-09-06.
It holds the reference to the same work in another system, in practice a Clooney work-package
number such as `WP3560`.

Pull it from the source when a `WP`-style reference appears, and otherwise **ask once**: is
there a Clooney or other external ID for this? An Idea without one is normal, so accept "ne"
immediately and leave the field empty. Never invent or guess a number, and never reuse one
from a different Idea in the conversation.

Send the reference exactly as the user gives it, as a bare string:
`"customfield_10062": "WP3560"`.

Its Jira display name carries a **trailing space** (`"External ID "`). That affects nothing
when writing by field ID, but it is worth knowing when matching field names from a response.

### Effort Estimation has a default, and it is dangerous

`customfield_10080` defaults to **`XS (0-1 MD)`** when omitted. Omitting it does not leave the
field blank, it silently claims the cheapest possible build and inflates ROI, Payback and Idea
Priority.

The default is a shared field configuration used by other teams and **cannot be changed**, so
the guard is entirely on our side: **always send an explicit value.** There is no case where
omitting this field is acceptable.

### PR Potential has no default and no `None`

`customfield_11262` is deliberately empty until someone chooses. **Do not propose a value, do
not infer one from the source, and do not fall back to `Low` to fill the field.** Present the
four options and let the user pick. If they skip it, leave it unset and list it under the
empty fields.

---

## 2. The scoring model

Three fields multiply into the labour saving:

```
Affected People  ×  Monthly Runs per Person  ×  Minutes per Run
```

An error in any one is an error in all three. The rest of the chain:

| Scoring field | Needs |
|---|---|
| Saved FTEs | Affected People + Monthly Runs per Person + Minutes per Run |
| Net Benefit 3Y | the above + Effort Estimation + Monthly Run Cost |
| ROI 3Y | the above + Effort Estimation |
| Payback Months | the above, and monthly benefit must exceed Monthly Run Cost |
| Idea Priority | all of the above + PR Potential + Priority Override (Jira default `Standard`) |

Partial ideas score partially, so every missing benefit field costs backlog position.

Idea Priority bands: **Deferred 0-100 · Standard 100-200 · Raised 200-300 · Expedited 1000+**.
Each band is a block of the backlog, and ideas rank on their business case inside the band.
An Expedited idea outranks every Raised one regardless of score.

**Monthly Run Cost counts 36 times** in the three-year calculation. Zero is a claim, not a
default. It is correct for a simple n8n flow and almost never correct for Copilot Studio,
premium Power Platform or Power BI premium capacity.

### Sanity checks before submitting

Run **all** of these before presenting anything. Each one that fires becomes a question to the
user, never a silent correction. The user's number stays until they change it themselves.

Two derived quantities do most of the work:

```
saturation = (Monthly Runs per Person × Minutes per Run) ÷ 10 080     one person-month = 168 h
saving     = Affected People × Monthly Runs per Person × Minutes per Run ÷ 60   hours/month
```

**Hard stops.** Do not present an Idea carrying one of these without resolving it first.

| # | Check | Rule | Why |
|---|---|---|---|
| H1 | Saturation impossible | `saturation > 1.0` | claims a person spends more than a full month on this. One of the two numbers is a team total or an elapsed duration |
| H2 | Non-positive input | any of Affected People, Monthly Runs per Person, Minutes per Run is 0 or negative | the saving computes to zero or nonsense, the field was misunderstood |
| H3 | Fractional people | Affected People is not a whole number | the field is a float, so 2,5 is accepted and always wrong |
| H4 | Text disagrees with fields | the arithmetic written in the Business Case does not reproduce the values sent to Jira | a reviewer who checks the maths loses trust in the whole Idea |

**Warnings.** Present the Idea, but raise each one explicitly and get an answer.

| # | Check | Rule | Why |
|---|---|---|---|
| W1 | Saturation implausible | `saturation > 0.5` | it is very unusual for one automation to take over more than half of somebody's working month. Above this, the person would have little else to do. Ask what else they do |
| W2 | ROI implausible | ROI 3Y above 15 | cheap build plus a saving spread thin. Reporting Ideas trip this constantly |
| W3 | Whole FTE claimed | Saved FTEs above 1.0 | a whole person back is a headcount conversation, so the inputs must be defensible |
| W4 | Run cost zero | Monthly Run Cost is 0 | correct for a simple n8n flow, almost never for Copilot Studio, premium Power Platform or Power BI premium capacity (§3) |
| W5 | Cost exceeds benefit | Monthly Run Cost ≥ the monthly saving valued in CZK | Payback never happens and Jira leaves it empty. The Idea may still be right, but say so out loud |
| W6 | Cadence implausible | Monthly Runs per Person above ~500, i.e. more than ~25 per working day | usually an annual or team figure |
| W7 | Run too long | Minutes per Run above ~120 | a two-hour "run" is normally a batch of several tasks. Split it, or say what one run really is |
| W8 | Effort on a band edge | the estimate is exactly 5, 10, 20 or 50 MD | it sits between two sizes and the choice changes ROI. Make the user pick |
| W9 | Effort against scale | XS or S effort with a saving above ~1 FTE, or XL/XXL effort with a saving below ~0,1 FTE | one of the two is out by an order of magnitude |
| W10 | Round-number tell | Affected People, Monthly Runs per Person and Minutes per Run are all round (10, 100, 20, 1000) | nothing was measured, these are placeholders. Ask which one is real |
| W11 | Period mismatch | Other Cash Saved / Month derived from a quarterly or annual figure | the field is monthly. Show the division you did |
| W12 | Double counting | the same benefit appears both as time saved and in Other Cash Saved / Month | inflates the case twice over |
| W13 | Coverage ignored | the Cílový stav says partial coverage (e.g. 80 %) but the saving is stated at 100 % | state both the gross and the discounted figure |
| W14 | Recipients counted | Affected People matches the number who *receive* the output rather than *do* the work | the single most common way this field is inflated |
| W15 | Large headcount unsourced | Affected People above ~50 with no source named in the Business Case | a round division-wide number needs its origin |
| W16 | Due date before Target end | `duedate < customfield_10023` | the requestor needs it before the work is scheduled to finish |
| W17 | Peak versus average | work arrives in waves and the rate used is not identified as one or the other | the average keeps ROI honest, the peak describes the pain. Record both |

**How to raise them.** One line per check that fired, phrased as a question with the number
attached, for example *"2 100 minut na osobu měsíčně je 52 % pracovního měsíce jedné osoby.
Sedí to, nebo je 15 minut spíš průběžný čas včetně čekání?"* Do not stack a wall of warnings,
and do not re-raise a check the user has already answered.

---

## 3. The four benefit fields, per technology

**Affected People** is the number of people who *do the work today*, not the number who
receive the output. **Monthly Runs per Person** is how many times **one** person does it per
month: daily is 20, weekly is 4, twice a day is 40. Never the team total. **Minutes per Run**
is how long one execution takes that person **today**, end to end, including waiting and
rework, not the estimate of what it will take after delivery.

### RPA (UiPath, n8n) — Components: `RPA`

| Field | How to read it |
|---|---|
| Affected People | Usually 1 to 5. How many people currently run this process. If one clerk does it, the answer is 1, even when 200 people receive the output. |
| Monthly Runs per Person | Executions per month by that person. A daily job is 20. |
| Minutes per Run | Clock time for one execution today, including logging into systems and waiting for exports. |
| Monthly Run Cost | Unattended robot licence share, Orchestrator capacity, n8n hosting, expected maintenance. Rarely 0. Budget 1,000–3,000 CZK for a typical unattended bot. |

**Watch for:** counting the recipients of the output instead of the people doing the work.

### Digitalization (Power Platform) — Components: `Power Platform`

| Field | How to read it |
|---|---|
| Affected People | Expected app users, the people whose work actually changes. Not everyone holding a licence. Usually the largest count of the four technologies. |
| Monthly Runs per Person | How often one user opens the app to do the thing: submissions, inspections, approvals, requests. |
| Minutes per Run | What the old way took: filling a paper form, chasing an approval by e-mail, re-typing into a system. |
| Monthly Run Cost | **Do not leave at 0.** Premium connector licences, Dataverse capacity, per-app plans. A 60-user app on premium licences is a five-figure monthly cost. |

**Watch for:** an approval step that stays manual after delivery. Enter the time actually
saved, not the whole end-to-end duration.

### Reporting (Power BI) — Components: `Power BI`

The hardest to estimate honestly, and the most likely to produce a wrong number. Time saved
on a report is a claim nobody can verify afterwards.

| Field | How to read it |
|---|---|
| Affected People | People who consume the report **and whose work changes because of it**. Not everyone with view access. If 200 can open it but 8 use it to decide something, the answer is 8, not 200. |
| Monthly Runs per Person | How often one consumer needs the numbers. A weekly review is 4, a daily operational check is 20. |
| Minutes per Run | Time to get the same answer today: pulling an export, building a pivot, mailing someone for a figure. If the answer today is "they simply do not have it", the saving is 0 and the value belongs in Other Cash Saved or in the Business Case text. |
| Monthly Run Cost | Premium capacity share, gateway, dataset refresh. Often small, rarely truly 0. |

**Watch for:** reporting ideas routinely produce ROI above 15 because the build is cheap and
the claimed saving is spread across many people. Anything over 15 gets reviewed. Ask whether
you would defend the Minutes per Run figure to the requestor's manager.

### AI (Copilot Studio, custom agents) — Components: `AI`

| Field | How to read it |
|---|---|
| Affected People | People the agent serves. For a helpdesk agent, everyone who would otherwise raise a ticket. |
| Monthly Runs per Person | Queries or conversations per person per month. Be conservative, adoption is never 100 %. |
| Minutes per Run | What the person does today instead: searching a wiki, waiting for a ticket response, asking a colleague. |
| Monthly Run Cost | **The field that matters most here.** Message packs, model consumption, Copilot Studio capacity, prompt maintenance. Five figures monthly is normal, and it is the main reason an agent can score worse than a bot. |

### Cross-technology ideas

One Idea can carry several Components. Fill the four benefit fields **once**, for the process
as a whole, from the point of view of the people doing the work today. Do not add up separate
savings per technology, and do not create one Idea per technology for the same process.

Example: a bot extracts from a legacy system, a Power BI report presents it, a Power App
captures corrections. Components = `RPA`, `Power BI`, `Power Platform`. Affected People = the
people who do this end to end today. Minutes per Run = the whole current process, not one leg.

---

## 4. Allowed values

### Affected People — `customfield_11363`

**A plain number: how many people do this work today.** No bands, no default, no wrapper object.
Send `12`, not `{"value": "M (6-20)"}`.

Ask the user directly, "how many people do this today?", and put the same figure in the
Business Case text so a reviewer can judge it. Count the people who *do the work*, never the
people who receive the output.

Note the ID. The field was rebuilt as a number on 2026-09-06 and the old select
`customfield_11260` no longer exists on the Idea screen. If any older note or payload still
references `11260`, it is stale.

### Effort Estimation — `customfield_10080`

`XS (0-1 MD)` · `S (1-5 MD)` · `M (5-10 MD)` · `L (10-20 MD)` · `XL (20-50 MD)` · `XXL (50+ MD)`

Our implementation estimate after a quick analysis. S is roughly half a sprint, M one sprint,
L two sprints. Defaults to XS if omitted, so always send it.

### PR Potential — `customfield_11262`

`Low` · `Medium` · `High` · `Flagship`

How visible the delivery is outside the team. Low = one team or department. Medium = division
level, appears in division reporting. High = top management asks about it, C-level reporting.
Flagship = board level, CEO showcase, external reference case.

**No default and no `None` option.** The CoE decides this, never the requestor, and the user
selects it themselves. Ask, show all four, and never pre-fill or recommend one.

### Priority Override — `customfield_11263`

`Deferred` · `Standard` · `Raised` · `Expedited`, defaulting to `Standard`.

Listed for reference only. **The skill never sets it and never asks about it** (§1). The bands
still matter for reading a backlog: `Deferred` means risky, unproven or deprioritised, `Raised`
pulls an Idea forward, and `Expedited` forces it above every `Raised` one regardless of
business case.

### Components — `components`

`AI` · `Excel` · `Power BI` · `Power Platform` · `RPA`

Five options only. The older granular values (`RPA - Ui Path`, `Power Platform - Canvas Power
App`, `M365 - SharePoint`, `Microsoft Excel - VBA`, `DWH SandBox` and the rest) no longer
exist. If the source names a specific product, map it up: UiPath and n8n → `RPA`; Canvas /
Model-Driven / Power Automate / Dataverse / Forms / Power Pages → `Power Platform`; VBA and
Power Query → `Excel`; Copilot Studio and custom agents → `AI`.

Format is `[{"name": "RPA"}]`, using `name` rather than `value`.

### Department — `customfield_10079`

**Not cached. Fetch it live every time** (§5) — the org structure moves, sub-departments get
renamed, and a stale value here silently misattributes where demand comes from.

The list has roughly twenty top-level units, most with sub-departments. Ask for the top level
first, then narrow. The stored value for a sub-department is the **full concatenated string**,
for example `"IT - IT Platforms"` or `"Network Deployment & Maintenance - FLM"`. A bare
top-level value is also valid where the list has one. Note there is no bare `CEO` option, only
the three `CEO - …` entries.

### Used Applications — `customfield_10106`

Systems the solution will need to reach. Drives feasibility and access requests.

ARES · CLOONEY · CRM · Datario · DAVYS · DBM · DMSP8 · DocuSign · DWH · EnterpriseScan · GIMS ·
IPMS · JIRA · LMS · MDS · METRO · Microsoft Access · Microsoft Email · Microsoft Excel ·
Microsoft Forms · Microsoft Power App · Microsoft Power Point · Microsoft Project Planner ·
Microsoft SharePoint · Microsoft Teams · Microsoft Word · MoneyS5 · MSSQL · NIMS · ODOS ·
Portál Výstavby · PPPS · ROP3G · RTS · SAP ERP-S4HANA · SAP Fiori-S4HANA · SAP Success Factor ·
Shared Drives · SVS PORTAL · TSM-Core · Web Browser · WGIS · ZIS

Common mappings from how people actually talk: "Outlook / mail" → `Microsoft Email`;
"P8 / DMS" → `DMSP8`; "TSM" → `TSM-Core`; "SAP" → `SAP ERP-S4HANA` unless Fiori is named;
"sdílený disk / L:\" → `Shared Drives`; "web / portál" → `Web Browser`.

If a system in the source has no matching option, for instance an in-house tool, **do not
force a wrong option**. Leave it out of the field and name it in the Description instead.

---

## 5. Resolving Requestor and Department

`customfield_10071` (Requestor) holds several hundred names and grows every month.
`customfield_10079` (Department) tracks a live org structure. **Neither is cached here.
Fetch both every time you need to fill them.**

One call returns both lists, so this is a single call per Idea, not two:

```
Atlassian Rovo:getJiraIssueTypeMetaWithFields
  cloudId: cetin.atlassian.net
  projectIdOrKey: ACOE
  issueTypeId: 10016
  requiredFieldsOnly: false
```

Then match the user's answers against `allowedValues` for `customfield_10071` and
`customfield_10079`. Make this call once, in Round 1, and reuse the response for the rest of
the conversation. Do not call it again per field.

### Matching a Requestor

- The format is **`Příjmení Jméno`**, surname first: `Minarovič Martin`, not `Martin Minarovič`.
  A handful of legacy entries are reversed (`David Sýkora`, `Jiří Bádr`, `Markéta Surovcová`),
  so match on both orders.
- Diacritics matter. Compare case- and diacritics-insensitively, but submit the **exact**
  stored string including diacritics.
- Several surnames repeat with different first names (Bartoš, Novák, Poláček, Šedivý, Štekr,
  Nováček, Opluštil, Svoboda). If more than one candidate matches, show the candidates and let
  the user pick. Never guess.
- If the name is genuinely absent, say so. A Jira admin has to add it to the field
  configuration. The Idea can be created with Requestor empty and fixed afterwards, or a
  different requestor named. Do not substitute a similar name.

### Matching a Department

- Present the top-level units, take the user's pick, then present that unit's sub-departments.
- Submit the full concatenated string exactly as stored, sub-department included.
- If the user names a unit that is not in the list, the org may have been restructured. Show
  the closest entries rather than choosing one for them.

Use the same call if a Components or Used Applications value is rejected, since those lists in
§4 are a dated snapshot.

---

## 6. Content format and the Business Case field

`createJiraIssue` accepts `contentFormat: "markdown"` (the default) and converts the top-level
`description` for you. That conversion does **not** extend to custom fields passed inside
`additional_fields`.

`customfield_10089` (Business Case Description) is **asymmetric**, and this is verified
behaviour rather than a guess:

- **On write it demands ADF.** A plain string is rejected with
  `The field value is not valid Atlassian Document Format (ADF) content.`
- **On read it renders as plain text.** Whatever ADF you send is flattened to wiki markup for
  storage, and the field then displays that markup *literally*.

So if you send `heading` and `bulletList` nodes, the user sees `h3. Proč to řešit` and
`* bullet` printed on screen as text. It looks broken, because it is.

**The rule: one `paragraph` per section, lines joined with `hardBreak`.** No headings, no
lists, no marks, since bold and italic also survive as literal `*text*`. Bullets are drawn by
hand with a `•` character. Do **not** use one paragraph per line, because each paragraph
renders with a blank line after it and the field ends up double-spaced.

Layout inside each section paragraph:

1. the section title, prefixed with `▚ ` (U+259A plus a space) and **ending with a colon**,
   in normal sentence case
2. **one** `hardBreak`, so the first bullet sits directly under the title
3. the bullets, one `hardBreak` between each
4. **no trailing** `hardBreak` — the paragraph break already supplies the single blank line
   between blocks

The **first paragraph opens with a single `hardBreak`**, so the whole field starts on a blank
line rather than flush against the field label.

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    { "type": "paragraph", "content": [
      { "type": "hardBreak" },
      { "type": "text", "text": "▚ Proč to řešit:" },
      { "type": "hardBreak" },
      { "type": "text", "text": "• První důvod." },
      { "type": "hardBreak" },
      { "type": "text", "text": "• Druhý důvod." }
    ] },
    { "type": "paragraph", "content": [
      { "type": "text", "text": "▚ Přínosy:" },
      { "type": "hardBreak" },
      { "type": "text", "text": "• Časová úspora …" }
    ] }
  ] }
```

Which renders as:

```

▚ Proč to řešit:
• První důvod.
• Druhý důvod.

▚ Přínosy:
• Časová úspora …
```

The `▚` glyph is plain text, so it survives the wiki-markup flattening that destroys real
formatting. That is the whole reason it works as a heading marker here.

Do not waste a call trying a plain string first, it always fails on this field.

The top-level `description` is a different field and renders rich text correctly, so `##`
headings and `-` bullets via `contentFormat: "markdown"` are fine there. Only the Business
Case needs the paragraphs-only treatment.

---

## 7. Workflow status

**The initial status for an ACOE Idea is `Backlog`.** `New` was removed as an initial status
by the project owner on 2026-09-06, so a freshly created Idea lands in `Backlog` on its own.

**Do not send a `transition` on create.** It is unnecessary now and a transition that is no
longer valid from the initial status will fail the whole call.

Still check the `status` in the create response. If an Idea somehow lands anywhere other than
`Backlog`, fix it with one follow-up call rather than leaving it:

```
Atlassian Rovo:transitionJiraIssue
  cloudId: cetin.atlassian.net
  issueIdOrKey: <new key>
  transition: { "id": "2" }
```

Known transitions, read from the live workflow on 2026-09-06. Neither has a transition screen,
so neither needs extra fields:

| Transition | ID | Target status |
|---|---|---|
| Backlog | `2` | `Backlog` (`10024`) |
| Canceled | `161` | `Canceled` (`10051`), global |

If an ID stops working, re-read it with `getTransitionsForJiraIssue` on any ACOE Idea.

**Never change status during an update.** Where an Idea sits in the workflow is the backlog
owner's call, not a side effect of adding a description. Only transition when the user asks
for it in so many words.

---

## 8. Worked payload

```
Atlassian Rovo:createJiraIssue
  cloudId: "cetin.atlassian.net"
  projectKey: "ACOE"
  issueTypeName: "Idea"
  contentFormat: "markdown"
  summary: "Směrování datových zpráv z podatelny"
  description: "## Shrnutí\n...\n\n## Aktuální proces\n- ...\n\n## Cílový stav\n- ..."
  additional_fields: {
    "duedate": "2026-12-31",
    "customfield_10022": "2026-10-05",
    "customfield_10023": "2026-12-31",
    "customfield_10071": { "value": "Minarovič Martin" },
    "customfield_10079": { "value": "IT - IT Platforms" },
    "customfield_10080": { "value": "L (10-20 MD)" },
    "customfield_11363": 3,
    "customfield_10081": 420,
    "customfield_10082": 10,
    "customfield_11261": 1500,
    "customfield_10090": 0,
    "customfield_11262": { "value": "Medium" },
    "customfield_10001": "99e75e3e-d31e-4aae-941a-f60e8e548378",
    "customfield_10062": "WP3560",
    "customfield_10106": [ { "value": "DMSP8" }, { "value": "ODOS" },
                           { "value": "Microsoft Excel" } ],
    "components": [ { "name": "RPA" } ],
    "customfield_10089": <paragraphs-only ADF doc — see §6>
  }
```

Omit any key whose value is empty. Do not send `null` or `""` on create, it can trip
validation on select fields. The one exception is Effort Estimation, which must always carry
an explicit value because of its XS default.

---

## 9. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `The field value is not valid Atlassian Document Format (ADF) content.` | Business Case got a plain string | send `customfield_10089` as paragraphs-only ADF (§6) |
| Business Case shows `h3.` / `*` literally on screen | ADF headings or lists flattened to wiki markup, which this field does not render | rebuild as paragraphs-only ADF with `•` bullets (§6) |
| Business Case double-spaced, blank line after every bullet | one `paragraph` per line | one paragraph per *section*, lines joined with `hardBreak` (§6) |
| `Option id 'X' is not valid` / value not found | option string does not match exactly | re-fetch allowed values (§5), match exactly including diacritics |
| `Field cannot be set, it is not on the appropriate screen`, naming `customfield_10001` | Team blocked on the create screen | re-create without it, then set Team via `editJiraIssue` (§1) |
| `Field cannot be set, it is not on the appropriate screen`, naming `customfield_10062` | External ID removed from the screen again | drop it, put the reference in the Description |
| `Team with id '<n>' not found.` | Team passed as a name instead of a UUID | pass the bare UUID string |
| Effort Estimation came out XS when nobody chose XS | field omitted, Jira applied its default | always send `customfield_10080` explicitly |
| Idea Priority looks absurdly high or low | a calculated field was written directly, or a team total went into Monthly Runs per Person | never write calculated fields; re-check §2 and §3 |
| Idea created outside `Backlog` | workflow initial status changed | call `transitionJiraIssue` with `{"id": "2"}` on the new key (§7) |
| `transition` rejected on create | `New` is no longer an initial status, so the New→Backlog transition is not valid there | drop `transition` from the create call entirely (§7) |
| `issuetype` invalid | wrong name | it is `Idea`, id `10016`, hierarchy level 2 |
| whole call fails, cause unclear | several fields at once | create with Summary + Description only, then `editJiraIssue` field by field to isolate |

If creation partially succeeds, report the issue key immediately along with which fields did
not land. A created issue with three missing fields is recoverable, a lost issue key is not.
