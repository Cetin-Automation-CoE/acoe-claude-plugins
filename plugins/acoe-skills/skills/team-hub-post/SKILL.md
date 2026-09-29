---
name: team-hub-post
description: |
  Use when creating, writing, translating, updating or publishing a solution post or a hosted HTML page for Team Hub — the ACOE portal (the site calls itself AI Hub) with the /automation-solutions listing. Triggers: "write a Team Hub post", "add a solution to Team Hub", "showcase post", "publish the post to DEV / LIVE", "napiš příspěvek na Team Hub", "publikuj řešení", "post z ACOE-1234", writing up a delivered solution from its ACOE Jira Idea, or a post that does not show up on the portal after it was uploaded.
  Do NOT use for fetching an existing SharePoint showcase page into the team-hub repo — that repo's publish-solution skill does that. Do NOT use for PRD/idea intake — use idea-forge or acoe-jira-idea-intake.
cowork:
  category: productivity
  icon: Newspaper
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__Atlassian_Rovo__getJiraIssue, mcp__Atlassian_Rovo__searchJiraIssuesUsingJql, mcp__Atlassian_Rovo__getAccessibleAtlassianResources
---

# ACOE Team Hub post

Author and publish content for **Team Hub**, the ACOE portal. A post is a
**self-describing folder of files** — there is **no central index, no
database, no deploy and no pipeline**: the portal reads the `articles`
container of its storage account and derives the /automation-solutions listing
from each post's frontmatter. Publishing puts the folder into that container —
through the Team Hub Posts library, where a Logic App does the copying, or by
a direct upload from the CETIN network — see [Publishing](#publishing). There
are two portals, **DEV** and **LIVE**, one storage account each.

## Two ways in

**From an ACOE Idea** — the normal case for a delivered solution. The user
names an issue key (`ACOE-2440`) or pastes a Jira link. Read the Idea and write
the post from it: see [Writing from an Idea](#writing-from-an-idea).

**From a description** — a walkthrough in chat, a demo recording's notes, a
Teams thread. Write from that, and ask for the Idea key anyway: it sets the
slug and links the post back to its business case.

Either way the deliverable is the same folder, validated the same way, landing
in the same place.

## Folder contract

Folder name = slug = URL (`/automation-solutions/#/<slug>`) = the stem of both
markdown files. Kebab-case ASCII, never renamed after publishing. All files
flat inside — no subfolders.

```
<slug>/
├── <slug>.md        ← English post (required)
├── <slug>.cz.md     ← Czech post (required when a person is writing)
├── screenshot-1.png ← media next to the .md
├── demo.mp4         ← optional short demo video (≤ ~100 MB, H.264)
└── demo-poster.jpg  ← optional thumbnail shown before demo.mp4 plays
```

The portal lists a post only when the folder and the file are named alike:
`acoe-1415-capex-reporting/acoe-1415-capex-reporting.md` is a post,
`capex-report/acoe-1415-capex-reporting.md` is invisible.

**Slug convention:** `acoe-<idea-number>-<short-name>` — e.g.
`acoe-2440-analytics-hub`. Deriving it from the Idea key is what makes a
second run an update rather than a duplicate, and it keeps the post traceable
to its business case from the URL alone.

Start from [references/post-template.md](references/post-template.md) and
[references/post-template.cz.md](references/post-template.cz.md).

## Frontmatter (drives the listing and filters)

| Field      | Required | Rules | From the Idea |
|------------|----------|-------|---------------|
| `title`    | yes      | In `.cz.md` this IS the Czech listing title. | Summary, `[FIS]`-style prefixes stripped |
| `desc`     | yes      | **One whole sentence, at most 120 characters**, not a copy of the opening paragraph. It is the listing card's text and the deck under the title in the post's band — three lines at most; what does not fit runs on in the body. Czech in `.cz.md`. | written from Description + Business Case |
| `category` | yes      | Exactly one technology, **spelled as the listing already spells it**: `Power Apps`, `Power BI`, `RPA`, `Reporting`, `Power Automate`, `SharePoint`, `AI`, `Code`, `Excel`, `Copilot Studio`, `n8n`. A new spelling is a new filter pill — `RPA (UiPath)` would sit next to `RPA`. | Components (see mapping below) |
| `business` | yes      | One area, as on the listing: `Finance`, `Sales`, `HR`, `PMO`, `Network Deployment`, `Network Operations`, `Legal`, `Procurement`, `IT`, `Wholesale`, `Regulatory`, `Automation CoE`. | Department |
| `author`   | yes      | `Surname Firstname` (e.g. `Horák Dominik`). | **Assignee**, not the Requestor |
| `added`    | yes      | `YYYY-MM-DD`; listing sorts newest first. | resolution date, else today |
| `tags`     | no       | Extra filter pills, comma-separated. **If the solution uses AI in any form, set `tags: AI`.** | Components + Used Applications |
| `role`     | no       | Author role override. | — |

Single-line `key: value` pairs only. Broken frontmatter = post silently
missing from the listing. Run the validator (below) rather than eyeballing it.

## Writing from an Idea

**Jira is read-only from this skill. Never create, edit, transition, comment
on, or attach to an issue** — whatever connector is installed. This skill reads
the Idea and nothing else. Intake and field maintenance belong to
`acoe-jira-idea-intake`.

**Read [references/jira-fields.md](references/jira-fields.md) first.** The
ACOE business-case fields are custom fields, so the API returns them as
`customfield_11363`, not "Affected People" — that file has the ids, the exact
`fields` list to request, and what each one feeds. Without it the benefit
numbers come back invisible and the post comes out hollow without erroring.

Take from the issue:

- **Description** and **Business Case Description** → the ORIGINAL STATE and
  the substance of the write-up
- **Saved FTEs**, **ROI 3Y**, **Net Benefit 3Y**, **Payback Months** → the
  BENEFITS section. These are Jira-calculated, so quoting them keeps the post
  consistent with the backlog ranking and the business case. **Prefer them to
  doing the arithmetic yourself** — a post that multiplies people × runs ×
  minutes its own way will eventually disagree with the Idea it came from, and
  the post is the version the whole company reads.
- **Affected People**, **Monthly Runs per Person**, **Minutes per Run** → the
  scale of the old process, for ORIGINAL STATE. All three are **per person**;
  the Idea author already divided team totals by headcount, so do not divide
  again.
- **Used Applications** → the systems named in the story, and the
  disambiguator for `category`
- **Components** → `category`
- **Department** → `business`
- **Assignee** → `author`
- **Image attachments** → the gallery, saved as `screenshot-1.png`,
  `screenshot-2.png`… in filename order. A video attachment becomes `demo.mp4`.

### Component → category

| Jira component | `category` |
|---|---|
| `RPA` | `RPA` |
| `Power BI` | `Power BI` |
| `AI` | `AI` |
| `Excel` | `Excel` |
| `Code` | `Code` |
| `Power Platform` | **ambiguous** — resolve from Used Applications |

`Power Platform` covers Power Apps, Power Automate and sometimes Power BI,
while Team Hub wants exactly one technology. Read Used Applications: a canvas
app or Dataverse means `Power Apps`, a flow alone means `Power Automate`, a
report or dataset means `Power BI`. **If it does not disambiguate, ask the
user.** Do not guess — the category is a filter pill people browse by.

### The rule that outranks everything else

**Never invent a fact.** Every number, system name, person and claim in the
post must be traceable to the Idea or to what the user told you. This is a
showcase read by sceptical stakeholders; one invented FTE saving costs the CoE
more credibility than a thin post ever would.

Where the Idea is silent, write around the gap:

- no benefit numbers → write BENEFITS qualitatively ("the monthly rebuild step
  is gone") and manufacture no hours or crowns. An empty `Saved FTEs` means
  the Idea's inputs were incomplete; that is a reason to quote nothing, not a
  reason to compute a replacement.
- no named department → leave it out rather than guessing who benefits
- an Idea whose **Delivery Type is not `New Functionalities`** has no business
  case at all. Say so and stop — there is nothing to showcase.
- an Idea whose **status is not `Deployed`** is not finished. Team Hub shows
  delivered solutions only: draft the post for review, but do not publish it.

## Body conventions the renderer understands

- Open with a **bold lead paragraph** (`**…**`) — the elevator pitch. Not a heading.
- The storyline block is keyed off exact headings, and **each language has its
  own set**:
  - `<slug>.md` — `### ORIGINAL STATE`, `### CURRENT STATE`, `### BENEFITS`
  - `<slug>.cz.md` — `### PŮVODNÍ STAV`, `### SOUČASNÝ STAV`, `### PŘÍNOSY`

  All three must be present or the three-column block does not render. Use
  bullets under each.
- Media by absolute path: `![](/solutions/<slug>/<file>)`. Two or more
  consecutive images become a two-column lightbox gallery.
- **A video in the folder is embedded, not linked**: write
  `![](/solutions/<slug>/demo.mp4)` and Team Hub renders an inline player
  (with `demo-poster.jpg` as its thumbnail if present). Only use a
  `[▶ Watch the demo video](https://…)` link for externally hosted videos —
  and host those in a shared SharePoint/Stream location, never personal
  OneDrive (personal links 403 for other users).
- `> quote` blockquotes are **user comments**. The portal gathers them,
  wherever they sit in the post, into a closing "What users say" / „Ohlasy
  uživatelů" section, each quote in full — there is no length to trim to. Put
  the attribution on its own line starting with a dash,
  `> — Name Surname, Role (Department)`: the dash marks it, the first comma
  splits the name from the rest, which is shown as the role exactly as given —
  the department in brackets is welcome, not required. In `.cz.md` the role
  is Czech, the name is not.
- Close the body with the source link:
  `_Source: [ACOE-2440](https://cetin.atlassian.net/browse/ACOE-2440)_`
- Keep each language to roughly 250–450 words. This is a showcase card, not a
  specification.

**Czech is required when a person is writing.** The audience is a Czech
company and the Czech listing takes its title and description from
`<slug>.cz.md`'s own frontmatter. Write Czech that reads as though a Czech
colleague wrote it, not as a translation — same facts, native phrasing. Never
use `titleCz`/`descCz`; they are dead keys.

**No screenshots is allowed, but only deliberately.** If the Idea has no image
attachments, say so, offer to publish gallery-less, and let the user decide.
Never reference an image that is not in the folder — a broken `<img>` is worse
than no gallery.

## Validate before you hand back

```bash
python3 scripts/validate_post.py <path-to-post-folder>
```

Nothing between the upload and the portal checks a post: a broken one does
not fail, it silently vanishes from the listing. The validator is the only
thing that turns that into an error — and here the user is still in the
conversation and a bad `category` is a one-turn fix.

An **error** means the post will not publish correctly: fix it, always. A
**warning** is a judgment the author owns (a `desc` over 120, a video without
a poster): fix it, or say what it costs and let the user choose. `--strict`
turns warnings into errors for an unattended run.

Do not describe a post as finished with an error outstanding, or with a
warning the user has not seen.

## Publishing

A post is published when its folder sits in the **`articles` container** of
the target portal's storage account: the portal reads the container directly,
and there is no git, no pipeline and no deploy. Two routes put it there — the
Team Hub Posts library, where a Logic App does the copying, and a direct
upload from the CETIN network. Same container, same result.

| Portal | Storage account | Address | Logic App |
|---|---|---|---|
| **DEV** — check here first | `stacoenpwebhubgwc` | https://webapp-acoe-nonprod-team-hub-gwc.azurewebsites.net | `logapp-acoe-nonprod-team-hub-gwc` |
| **LIVE** — what the company reads | `stacoepwebhubgwc` | https://webapp-acoe-prod-team-hub-gwc.azurewebsites.net | `logapp-acoe-prod-team-hub-gwc` |

The two account names differ by one character (`np` = non-production). Read
them twice. Both addresses answer only from the CETIN network — elsewhere
they return 403 — so from home the library's On DEV / On LIVE flags are the
proof that a post is up, not the page.

### Route 1 — the Team Hub Posts library (a browser is enough)

The document library **Team Hub Posts** (`Team_Hub_Posts`) on
<https://czcetin.sharepoint.com/sites/AutomationCoETeamHub> is the author's
drop zone. Each environment's Logic App runs `publish-posts` every 5 minutes
and carries out the command written on a folder.

1. Drag the **`<slug>` folder** into the library (or *Upload → Folder*) — the
   folder itself, not the files inside it.
2. On the **folder's** row set **Post status** to **`Publish to DEV`**. Within
   five minutes the DEV Logic App copies the folder into `articles/<slug>/`
   (media first, then `.cz.md`, then `.md`, so the listing never shows a post
   whose images are still on the way), sets **On DEV** to Yes and **Last
   published**, and puts Post status back to `Idle`; the portal's listing
   follows within a minute more. `Failed` means the command did not
   complete: **Publish message** says why; set the command again to retry
   the whole folder.
3. Check the DEV address, then set **`Publish to LIVE`** the same way.
   `Unpublish from DEV` / `Unpublish from LIVE` remove the post from that
   portal's container.

Post status is an **instruction, not a record**: On DEV and On LIVE say where
the post actually is. An update is the changed files uploaded over the old
ones and the command issued again. Only the folder row carries the command —
a status set on a file row is marked `Failed`.

**Is the route wired?** Before issuing a command, look at the Post status
choices in the library: the route works once they read exactly `Draft`,
`Publish to DEV`, `Publish to LIVE`, `Unpublish from DEV`, `Unpublish from
LIVE`, `Idle`, `Failed` and the folder row shows **On DEV** and **On LIVE**
columns. Other values there (`Published on DEV`, `Unpublished`, …) mean the
library still carries an earlier draft of the schema. After a command, fifteen
minutes with no `Idle`, no `Failed` and no On DEV / On LIVE flip mean that
environment's Logic App is not running the workflow. Either way: publish by
route 2 and tell the CoE — the Logic App and the library schema are theirs
to fix, not the author's.

### Route 2 — upload from the CETIN network

**What the upload needs:** a machine on the **CETIN network** (the storage
firewall admits CETIN addresses only; from anywhere else every command fails
with *"blocked by network rules"*), `az login`, and the **Storage Blob Data
Contributor** role on the account. There are no account keys — always
`--auth-mode login`.

If this session has none of that (Cowork, off-network, no `az`): **write the
post folder where the colleague can pick it up — the session's outputs folder
in Cowork, otherwise a path they named — and hand them route 1, or, where
route 1 is not wired, the steps below with the slug filled in.** That is the
whole handover.

1. Validate until clean (above).
2. **DEV** — from inside the folder's parent directory:

   ```bash
   az storage blob upload-batch --auth-mode login --overwrite \
     --account-name stacoenpwebhubgwc -d articles --destination-path <slug> -s <slug>
   ```

   `-d` takes the container name alone; the slug goes in `--destination-path`
   (`-d articles/<slug>` is rejected). `--overwrite` makes the same command an
   update.
3. **Check** `https://webapp-acoe-nonprod-team-hub-gwc.azurewebsites.net/automation-solutions/#/<slug>`.
   The post itself is served the moment the upload ends; the **listing shows
   it within 60 seconds** — the portal caches the derived listing for a
   minute. Not there after a minute → the folder name, the file name or the
   frontmatter (see [Common mistakes](#common-mistakes)).
4. **LIVE** — the same command with `--account-name stacoepwebhubgwc`, then
   the same check on the LIVE address.

**Update** = the same upload; `--overwrite` replaces what is there.
**Unpublish**:

```bash
az storage blob delete-batch --auth-mode login --account-name <account> \
  -s articles --pattern '<slug>/*' --dryrun     # read the list, then run it without --dryrun
```

Soft delete and versioning are on: a deleted or overwritten file can be
restored for **14 days on DEV and 30 days on LIVE** (Azure portal or Storage
Explorer: *Show deleted blobs* → *Undelete*).

Inside the team-hub repo, `acoe-team-hub/solutions/` is the seed copy of the
container and `tools/seed-blob-content.sh <account>` uploads the whole tree
the same way. When you are working in that repo, add the post folder there
too, so the seed stays complete.

## Hosted HTML pages

A standalone page (strategy deck, workshop) is one **fully self-contained**
`.html` file (inline CSS/JS, images as data: URIs) in the `html-pages`
container of the same accounts — put there through the **Team Hub Pages**
library (`Team_Hub_Pages`: one file per page, the same Post status commands,
carried out by `publish-pages`) or with the upload below. `<name>.html` is
served raw at `/<name>`,
inside the portal chrome at `/presentations/<name>/`, and listed under
Presentations automatically: its `<title>` is the listing title and its
upload date is its date — no meta tags are read. Start from
[references/html-page-template.html](references/html-page-template.html) and
upload with

```bash
az storage blob upload --auth-mode login --overwrite \
  --account-name <account> -c html-pages -f <name>.html -n <name>.html
```

## Common mistakes

| Mistake | Reality |
|---|---|
| Uploading to the wrong account | `stacoenpwebhubgwc` is DEV, `stacoepwebhubgwc` is LIVE — one letter apart. Check the address the post appeared on. |
| `-d articles/<slug>` | az rejects it: `-d articles --destination-path <slug>`. |
| Uploading from outside the CETIN network | The storage firewall blocks it ("blocked by network rules"). Hand the folder and the commands to someone on the network. |
| Folder named differently from the file (`capex-report/acoe-1415-capex-reporting.md`) | The listing takes `<slug>/<slug>.md` only. Both carry the slug. |
| Expecting the listing to show the post at once | The listing refreshes within 60 s; the post's own URL works immediately. |
| Asking for a deploy, a pipeline run or a git push | None exists for posts. The container is the source; the library command or the upload is the publish. |
| Setting Post status on a file row instead of the folder | The workflow acts on folders only; a file row is marked `Failed`. |
| Waiting on a library command that never completes | Fifteen minutes with no `Idle`, no `Failed` and no On DEV / On LIVE flip means that environment's Logic App is not running the workflow. Publish by upload. |
| `category: RPA (UiPath)` or another new spelling | The listing spells it `RPA`; a new spelling is a second filter pill. Use the spellings in the frontmatter table. |
| A `desc` over 120 characters | The band shows three lines and pushes the rest into the body; the card clamps at four. One whole sentence. |
| Handing back without running the validator | Team Hub fails *silently* — a broken post just vanishes from the listing. The validator is the only thing that turns that into an error. |
| Uploading the files loose instead of the folder | `<slug>/` is the post: files at the container root belong to nothing. |
| English storyline headings in the `.cz.md` | The Czech post needs `### PŮVODNÍ STAV` / `### SOUČASNÝ STAV` / `### PŘÍNOSY`. |
| Editing or commenting on the Jira Idea | This skill reads Jira only. Intake belongs to `acoe-jira-idea-intake`. |
| Guessing `category` from `Power Platform` | Resolve it from Used Applications, or ask. It is a filter pill people browse by. |
| Using the Requestor as `author` | `author` is the Assignee — the CoE person who delivered it. |
| Creating or editing `solutions/index.json` | Obsolete. The listing is derived from frontmatter; a stray `index.json` is ignored dead weight. Never write one. |
| Linking a local `demo.mp4` as `[▶ Watch…](…)` | Local videos are embedded with image syntax `![](…demo.mp4)` → inline player. |
| Omitting `tags: AI` on an AI-flavored solution | The AI pill/filter comes only from `tags`. AI Builder, Copilot, GPT — all count. |
| Opening with a `###` heading instead of a bold paragraph | The renderer expects a bold lead; headings start at the storyline sections. |
| Czech texts only in the EN file (`titleCz`/`descCz`) | Czech listing texts come from the `.cz.md` file's own `title`/`desc`. |
| Renaming the folder after publishing | Slug = URL; renaming breaks links. Pick the slug once. |
