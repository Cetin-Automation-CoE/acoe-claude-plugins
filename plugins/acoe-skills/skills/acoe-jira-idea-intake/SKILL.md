---
name: acoe-jira-idea-intake
description: Turn any source material into a complete, ready-to-submit Idea in the CETIN ACOE Jira project (Automation CoE), then create or update that issue through the Atlassian connector. Sources can be a meeting transcript, e-mail thread, Word, PDF or PowerPoint document, screenshots, or a loose verbal description. Use this whenever someone raises an automation, digitalisation, RPA, UiPath, Power Platform, VBA, Power BI reporting or AI/Copilot Studio request, or says things like 'založ ideu', 'nová idea do ACOE', 'ACOE zadání', 'udělej z toho ideu', 'automation request', 'idea template' or 'zaeviduj požadavek na automatizaci'. Use it too when someone hands over notes or minutes describing a manual process they want automated, even if they never say the word idea or Jira. Use it as well for Ideas that already exist, whenever the user names an ACOE issue key or Jira link and wants to fill it in, correct a field, or attach transcripts and numbers to a near-empty placeholder Idea created earlier.
---

# ACOE Idea intake

The ACOE (Automation CoE) Jira project is where CETIN collects requests for automation,
digitalisation, AI and custom PowerBI reporting. Delivery happens through RPA (UiPath, n8n),
Power Platform, Excel, PowerBI and AI (custom, Copilot Studio, Microsoft Cowork).

An Idea is the intake artefact. It has to be good enough that someone who was **not** in the
meeting can read it, understand the current pain, and prioritise it against thirty other
requests. That is the bar to write for.

The benefit fields also feed an **automatic scoring model** that decides the Idea's backlog
position. Sloppy inputs there do not just look bad, they misrank the whole backlog. See
`references/fields.md` §2 and §3.

## Two modes — decide this first

**Create mode** builds a new Idea from source material. **Update mode** changes an Idea that
already exists in Jira.

Update mode applies whenever the user names an issue key (`ACOE-4618`), pastes a Jira link, or
refers to an Idea that already exists, including the common case where they created a
near-empty Idea earlier just to track their work and are now handing over the transcript and
the numbers. Words like *doplň, aktualizuj, oprav, dodělej, update, add to* are the signal.

If update mode applies, **read `references/update-mode.md` and follow it instead of Steps 1–5
below.** It reuses the same writing rules and the same field reference, but it reads the issue
first and it protects fields that already have values. Getting this wrong overwrites work
somebody else did.

If you are unsure which mode applies, ask. Creating a duplicate Idea is worse than one extra
question.

## Two phases — do not merge them

1. **Template preparation.** Read the source, extract what it supports, ask about the rest,
   assemble the filled template, show it to the user.
2. **Submission.** Only after the user explicitly approves the assembled template, create the
   Idea in Jira.

Never create the Jira issue in the same turn as first presenting the template. The user
approves first. This matters because an Idea in ACOE is visible to the whole CoE and a
half-baked one costs more to clean up than to get right.

## The one rule that governs everything

**Never invent a fact.** Every number, system name, person and claim in the final Idea either
comes from the source material or from the user. If neither supplies it, the field stays empty
and you say so. A confidently wrong FTE saving is worse than a blank field.

Two categories of fields, and they behave differently:

| Behaviour | Fields |
|---|---|
| **Always ask the user. Never distil from the source, even if the answer looks obvious.** | Requestor, Department, Effort Estimation, Affected People, Monthly Run Cost, PR Potential, Due date, Target start, Target end |
| **Never ask. Set it automatically.** | Team (always Automation CoE) |
| **Never ask. Never send. Jira's own default is correct.** | Priority Override (defaults to `Standard`) |
| **Distil from the source, then have the user confirm or correct.** | Summary, Description, Business Case Description, Monthly Runs per Person, Minutes per Run, Other Cash Saved / Month, Used Applications, External ID |

The reason for the split: the first group depends on organisational context, on cost data and
on CoE judgement that a transcript cannot carry (who owns the budget, how many people actually
do this, what a licence costs, when someone genuinely *needs* it). Guessing there produces
plausible-looking errors that nobody catches. The second group is genuinely described in the
material, so extracting a draft saves the user time, but they still confirm it.

## Step 1 — Read the source

Handle whatever arrives:

- **Text, e-mail, chat export, Markdown, transcript** — already readable in context or via `view`.
- **Word / PDF / PowerPoint / Excel** — read the matching public skill (`docx`, `pdf-reading`,
  `pptx`, `xlsx`) first, then extract.
- **Video / audio recording** — you cannot watch or listen. Say so plainly and ask for a
  transcript, minutes, or the key points. Do not pretend to have processed it.
- **Screenshots / photos of screens** — read them visually, they are often the best evidence of
  which applications are in play.
- **Nothing but a verbal description** — fine. Go straight to the questions, the whole template
  can be built by interview.
- **Several sources at once** — normal. Merge them, and when two sources disagree on a number,
  do not average or pick one silently, put both to the user as a question.

Sources are frequently Czech or Slovak. Write the Idea in the language the source and the user
use (Czech by default at CETIN), except for the Jira option values, which are stored strings
and must be reproduced **exactly** as Jira has them.

## Step 2 — Silent extraction pass

Before asking anything, work through the material once and note, for each distillable field,
what the source supports and how strongly. Keep this internal, do not dump the raw extraction
on the user.

While reading, actively hunt for the things that make a business case, because sources bury
them in passing remarks:

- **headcount** — "dělají to tři holky z podatelny", "tým osmi lidí", "každý technik v terénu".
  This is the single most commonly missing input, because sources describe the work and not
  the people doing it.
- volumes and cadence — "cca 750 zpráv denně", "80× měsíčně", "každé ráno"
- durations — "zabere cca 15 minut", "kumulativně 10 minut na zprávu"
- **whether a duration is hands-on time or elapsed time** — "trvá to dva dny" is usually
  elapsed, and elapsed time is not what Minutes per Run wants
- error/rework rates — "jednotky kusů se denně vracejí"
- money already being lost — fines, penalties, SLA credits, overtime
- running costs — licences, capacity, message packs already being paid for
- deadlines and regulatory pressure — "na odeslání nabídky máme 20 dní"
- system names — TSM, CRM, ZIS, P8, ODOS, SAP, Excel, Outlook…
- **external references** — a Clooney work package (`WP3560`) or any other system's ID for the
  same work. These have a field now, so do not bury them in prose.

**Then convert to per-person figures yourself.** Monthly Runs per Person and Minutes per Run
are both *per person*, and sources almost always give team totals. Divide the total by the
headcount, show the division in the Business Case, and flag it as an assumption to verify.

Compute the derived numbers too rather than asking the user to: monthly minutes = people ×
runs × minutes; hours/month = that ÷ 60; MD/month = hours ÷ 8.

## Step 3 — Ask, in rounds

Ask in **two or three short rounds**, not one giant questionnaire and not one question at a
time. Group by what unblocks the most, and carry the answers forward so nothing is asked twice.

Format each round as a compact numbered list in chat, with your proposed answer already filled
in where you have one, so the user can reply "1 ok, 2 change to X" instead of retyping
everything. For choices with four or fewer options, `ask_user_input_v0` is nicer on mobile, but
do not force a 60-item list like Department into tappable buttons, show the relevant subset as
text instead.

**Whenever a field has a fixed option list, show the options.** Never ask "what T-shirt size?"
or "which component?" and expect the user to recall the allowed values. Print them inline, in
full where the list is short and narrowed to the plausible subset where it is long (Department,
Used Applications). Asking someone to guess at a closed vocabulary is how you get a value that
has to be corrected afterwards. Ask in plain language too: "kolik lidí to dnes dělá?" beats
"specify Affected People".

The short option lists are cached in `references/fields.md` §4, so do not call Jira to read
them. **Requestor and Department are the exception**: they are never cached, because names and
org structure both drift. Fetch them live in Round 1, in the single shared metadata call that
returns both, and reuse that response for the rest of the conversation.

**Round 1 — blockers:**

- Requestor and Department — one `getJiraIssueTypeMetaWithFields` call returns both option
  lists (`references/fields.md` §5). Make it once, here. Ask for a name and match it in the
  `Příjmení Jméno` format, then offer the top-level org units and narrow to the
  sub-department. Never guess between two candidates, show them and let the user pick.
- Components — which delivery technology is expected. Five options only: `RPA`,
  `Power Platform`, `Power BI`, `AI`, `Excel`. Several are allowed on one Idea. This is the
  CoE's call, not something to read out of the source.
- Anything mandatory (Summary, Description) where the source is too thin to draft.

**Round 2 — the scoring inputs.** These decide backlog position, so they are worth pushing on
even though Jira marks them optional. Read the per-technology guidance in
`references/fields.md` §3 first, because the same field means different things for a bot and
for a report.

- Present your drafted Summary, Description and Business Case for correction.
- **Affected People** — a plain number: how many people *do this work today*, not how many
  receive the output. The Jira field takes the headcount directly, so no bands are involved.
  Put the same figure in the Business Case text.
- **Monthly Runs per Person** — how many times **one** person does this per month. Daily is 20,
  weekly is 4, twice a day is 40. State the division you did from any team total.
- **Minutes per Run** — how long one run takes that person **today**, end to end, including
  waiting and rework. Not our estimate of the after state, and not elapsed calendar time.
- **Monthly Run Cost** — what the solution costs us every month once live. Zero is a claim, not
  a default. Say what you expect for the chosen technology (a bot is usually 1 000–3 000 CZK,
  premium Power Platform and Copilot Studio are far higher) and let the user correct it.
- **Other Cash Saved / Month** — money saved *elsewhere*, not the labour saving. Fines avoided,
  SLA penalties, licences retired. Ask only if the source hints at any, otherwise enter 0.
- **Used Applications** — confirm your extracted list against the allowed values.

**Round 3 — CoE judgement and planning:**

- **Effort Estimation** — print all six sizes: `XS (0-1 MD)`, `S (1-5 MD)`, `M (5-10 MD)`,
  `L (10-20 MD)`, `XL (20-50 MD)`, `XXL (50+ MD)`. If the user answers with a bare number that
  lands on a band edge (5, 10, 20, 50), make them choose which band. **This field must always
  be set.** Jira defaults it to `XS (0-1 MD)` and silently inflates the whole score. That
  default comes from a shared field configuration used by other teams and cannot be changed,
  so never leave this field to the default, not even when the user skips the question.
- **PR Potential** — how visible the delivery is outside the team: `Low`, `Medium`, `High`,
  `Flagship`. The CoE decides this, never the requestor, and **the user picks it themselves**.
  Show the four options with their one-line meanings and stop there. Do not propose a value,
  do not infer one from the source, and do not fall back to `Low` just to fill the field.
  There is no `None` option and no default. If the user skips it, leave it empty and list it
  under the unfilled fields.
- **External ID** — is there a Clooney or other external reference for this? Propose one if the
  source contained a `WP`-style number, otherwise ask once and accept "ne" immediately. Most
  Ideas have none. Never invent a number.
- **Due date** — ask for when the requestor **needs** it, not when they want it. Probe: what
  happens if it lands a month later? If the answer is "nothing much", leave it empty.
- **Target start / Target end** — planning fields, usually left empty at intake.

When the user does not know an optional value, accept "nevím / skip" immediately and move on.
Do not re-litigate.

## Summary and Description — two rules that override habit

These two are where drafts most often go wrong, so they are here and not only in the writing
guide.

**Summary: 3–8 words naming the subject, nothing else.** The whole company knows this project
delivers automation and digitalisation, so repeating it in every title is redundant and makes
thirty backlog rows look identical. Ban *automatizace, automatický, automatizovaný,
digitalizace, robotizace, robot, bot, RPA, automation, automated* from the Summary, along with
the delivery technology, unless the artefact genuinely is the subject.

Not *Automatizované generování faktur*, just **Generování faktur**. Not *Automatické směrování
datových zpráv z podatelny (P8/ODOS)*, just **Směrování datových zpráv z podatelny**.

**Description opens with a `## Shrnutí` block.** Two to four sentences of prose, before any
other section, answering what the subject is, who does it today, and what should change.
Management reads this and nothing else, so it carries no volumes, no minutes, no system
details and no bullets.

**The Description has exactly three sections**, in this order: `## Shrnutí`, `## Aktuální
proces`, `## Cílový stav`. Do not add others. Scope limits and known blockers are bullets in
*Cílový stav*, and a caveat on a number goes in brackets beside that number. Assumptions you
derived rather than read stay out of Jira entirely and are shown to the user in Step 4.

**Business Case section titles are written normally, not in capitals** — `Proč to řešit`,
`Přínosy`, `Dopad při nerealizaci`.

Full guidance, structure and worked examples: `references/writing-guide.md`. Read it before
drafting either field.

## Step 4 — Assemble and present

Present the filled template in chat as three blocks: the descriptive fields, the scoring
inputs with the derived saving, then the two long text fields in full.
`assets/idea-template.md` holds the exact layout to follow.

List the empty fields explicitly in one line underneath, so gaps are visible rather than merely
absent, and list any number you derived or converted (team total → per person, daily → monthly,
quarterly → monthly, weighted averages) so the assumptions can be challenged. Do not annotate
individual fields with where they came from, the conversation already shows that.

Then ask for one of: approve and submit / change something / hold as draft.

**Consistency checks before presenting.** `references/fields.md` §2 holds the full list, four
hard stops and seventeen warnings. Read it and run **every** check. Anything that fires becomes
a question to the user, never a silent correction, and the user's number stands until they
change it themselves.

The two that catch the most bad business cases:

- **Saturation.** `Monthly Runs per Person × Minutes per Run ÷ 10 080` is the share of one
  person's working month this consumes. Above **1.0** is arithmetically impossible and must be
  resolved before presenting. Above **0.5** is implausible and must be raised, because it is
  very unusual for one automation to take over more than half of somebody's month. One affected
  person at 168 h/month means the Idea claims to replace that whole person.
- **Affected People counts the people who do the work**, never the people who receive the
  output. A report read by 50 people but produced by one is 1.

Raise what fires as one short question each with the number attached, not as a wall of
warnings, and do not re-raise anything the user has already answered.

**Optional as-is diagram.** If the current process has more than about four sequential steps or
any branching, offer a BPMN-style flow diagram of the *as-is* process, rendered in chat as a
visual, so the user can spot a missing branch. It is a validation aid for the user, not part of
the Jira description, since Jira will not render a diagram. Keep the Description itself high
level regardless of how detailed the diagram gets. Do not build it unasked, offer then build.

## Step 5 — Submit to Jira

Only after explicit approval. Full field mapping, custom field IDs, allowed values and the ADF
gotcha for the Business Case field are in `references/fields.md`. Read it before the first
`createJiraIssue` call, because passing a plain string to the wrong custom field type fails
with an unhelpful error.

Shape of the call:

- tool: `Atlassian Rovo:createJiraIssue`
- `cloudId`: `cetin.atlassian.net` works directly, `getAccessibleAtlassianResources` if it does not
- `projectKey`: `ACOE`, `issueTypeName`: `Idea`
- `summary`, `description` (markdown), `duedate` at the documented places
- everything else inside `additional_fields` keyed by `customfield_*`

Things that will silently produce a bad Idea if you get them wrong, so check them against
`references/fields.md` before the call rather than after:

- **Business Case (`customfield_10089`)** must be ADF made of one `paragraph` per section with
  lines joined by `hardBreak` and bullets drawn as `•` characters. Headings, lists and bold all
  come out as literal wiki markup on screen, and one paragraph per line comes out double-spaced.
- **Effort Estimation (`customfield_10080`)** must always be sent. Omitting it applies Jira's
  `XS (0-1 MD)` default and inflates every downstream number.
- **Never send Priority Override (`customfield_11263`).** Jira defaults it to `Standard`,
  which is what intake wants, and the ranking band is the backlog owner's control applied in the
  UI afterwards.
- **Never write the calculated fields.** Saved FTEs `customfield_10103`, Net Benefit 3Y
  `customfield_11296`, ROI 3Y `customfield_10083`, Payback Months `customfield_11297` and Idea
  Priority `customfield_10105` are computed by Jira from the inputs.
- **Team (`customfield_10001`)** is always Automation CoE
  `99e75e3e-d31e-4aae-941a-f60e8e548378`, passed as a bare UUID string. Set it on create and do
  not ask the user. Atlassian Team fields often do not appear in the create metadata even when
  settable, so send it regardless. Only if a create is rejected naming that field do you
  re-create without it and set Team with a follow-up `editJiraIssue`.
- **External ID (`customfield_10062`)** is a plain text string, sent bare:
  `"customfield_10062": "WP3560"`. Empty is normal and fine.

**`Backlog` is the initial status, so send no `transition` on create.** `New` was removed as
an initial status, and passing a transition that is not valid from the initial status fails the
whole call. Still check the `status` in the create response, and only if it came back as
anything other than `Backlog` follow up with `transitionJiraIssue` using `{"id": "2"}`. That
is the one case where a second call is warranted, so never fire it pre-emptively.

After creation, report the issue key and URL, and list any field that failed to set so the user
can fix it in the UI. If a field is rejected, do not silently drop it, say which one and why.

Attachments cannot be added through `createJiraIssue`. If the user wants the source document or
the diagram attached, tell them to attach it manually to the created issue.

Also out of scope: `labels` and `parent` are unused in ACOE, and `People Working On It`
(`customfield_11330`) is filled by delivery later, not at intake.

## Reference files

- `references/fields.md` — field-by-field mapping to Jira, custom field IDs, the scoring model,
  per-technology guidance for the four benefit fields, cached allowed-value lists, how to
  resolve Requestor, ADF handling, worked `createJiraIssue` payload, failure modes.
- `references/update-mode.md` — the full procedure for changing an Idea that already exists in
  Jira: reading it first, protecting populated fields, composing rather than replacing the text
  fields, and the old-against-new approval table. Read it instead of Steps 1–5 whenever the user
  points at an existing issue key.
- `references/writing-guide.md` — how to write the Summary, the `## Shrnutí` block, the
  Description and the Business Case, with worked before/after examples. Read this before
  drafting any of them.
- `assets/idea-template.md` — the presentation layout for Step 4.
