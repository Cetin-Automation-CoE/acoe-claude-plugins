# ACOE Idea fields — the read side

This skill **reads** these and writes none of them. Field *names* drift the
moment somebody renames one in the Jira UI; ids do not, so address them by id.
The write-side table, option lists and validation rules live in
`acoe-jira-idea-intake/references/fields.md` — that skill owns the Idea; this
one only quotes it.

Project `ACOE` · issue type `Idea` (id `10016`) · site `cetin.atlassian.net`

## Ask for these fields explicitly

`getJiraIssue` returns a lean default set, so name what you need:

```
summary, description, status, resolutiondate, components, labels, assignee,
attachment, customfield_10089, customfield_10079, customfield_10106,
customfield_11363, customfield_10081, customfield_10082, customfield_11261,
customfield_10090, customfield_11396, customfield_10062, customfield_10103,
customfield_10083, customfield_11296, customfield_11297
```

## What each one is for

| Field | id | Used for |
|---|---|---|
| Summary | `summary` | `title`, minus any `[FIS]`-style prefix |
| Status | `status` | **gate** — `status.name` must be `Deployed` before the post may be uploaded |
| Description | `description` | ORIGINAL STATE and the body |
| Business Case Description | `customfield_10089` | the substance of the write-up |
| Department | `customfield_10079` | `business` |
| Components | `components` | `category` (see SKILL.md mapping) |
| Used Applications | `customfield_10106` | systems named in the story; disambiguates `Power Platform` |
| Assignee | `assignee` | `author` |
| Resolution date | `resolutiondate` | `added` |
| Attachments | `attachment` | the gallery — images in filename order, video → `demo.mp4` |
| Labels | `labels` | `teamhub-skip`, AI hints |
| External ID | `customfield_10062` | a Clooney work package etc., if worth mentioning |
| Delivery Type | `customfield_11396` | **gate** — must be `New Functionalities` |

## The benefit numbers

Raw inputs, all **per person** — the Idea author already divided team totals
by headcount, so do not divide again:

| Field | id |
|---|---|
| Affected People | `customfield_11363` |
| Monthly Runs per Person | `customfield_10081` |
| Minutes per Run | `customfield_10082` |
| Monthly Run Cost | `customfield_11261` |
| Other Cash Saved / Month | `customfield_10090` |

## Prefer the calculated fields

Jira computes these from the inputs above, and they are what the CoE's backlog
ranking already uses:

| Field | id |
|---|---|
| Saved FTEs | `customfield_10103` |
| ROI 3Y | `customfield_10083` |
| Net Benefit 3Y | `customfield_11296` |
| Payback Months | `customfield_11297` |

**Quote these rather than doing the arithmetic yourself.** A post that says
"0.4 FTE released" using `Saved FTEs` agrees with every other CoE number for
that solution. A post that multiplies people × runs × minutes in its own way
will eventually disagree with the business case it was written from, and the
post is the version the whole company reads.

If a calculated field is empty the Idea's inputs were incomplete — say what
changed qualitatively and quote nothing.

## Never write

This skill has no write tools by design. Do not create, edit, transition,
comment on or attach to an issue, and never touch the calculated fields —
writing to them corrupts the backlog ranking.
