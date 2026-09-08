---
name: team-hub-post
description: |
  Use when creating, writing, translating, or updating a solution post or a hosted HTML page for Team Hub — the internal ACOE showcase site with the /solutions listing. Triggers: "write a Team Hub post", "add a solution to Team Hub", "team hub post", "showcase post", "napiš příspěvek na Team Hub", "napiš článek na portál", "publikuj řešení", "solution showcase", "post z ACOE-1234", writing up a delivered solution from its ACOE Jira Idea, or converting a description of a Power Apps / Power BI / Power Automate / RPA solution into Team Hub content.
  Do NOT use for fetching an existing SharePoint showcase page into the team-hub repo — that repo's publish-solution skill does that. Do NOT use for PRD/idea intake — use idea-forge or acoe-jira-idea-intake.
cowork:
  category: productivity
  icon: Newspaper
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__Atlassian_Rovo__getJiraIssue, mcp__Atlassian_Rovo__searchJiraIssuesUsingJql, mcp__Atlassian_Rovo__getAccessibleAtlassianResources
---

# ACOE Team Hub post

Author content for **Team Hub**, the ACOE showcase site. A post is a
**self-describing folder of files** — there is **no central index or database
to edit**: Team Hub derives the /solutions listing automatically from each
post's frontmatter.

Posts are published **through git**, not by uploading to storage. See
[Publishing](#publishing) — that changed, and the old `az storage blob` route
now breaks the audit trail.

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

Folder name = slug = URL (`/solutions/<slug>`). Kebab-case ASCII, never
renamed after publishing. All files flat inside — no subfolders.

```
<slug>/
├── <slug>.md        ← English post (required)
├── <slug>.cz.md     ← Czech post (required when a person is writing)
├── screenshot-1.png ← media next to the .md
├── demo.mp4         ← optional short demo video (≤ ~100 MB, H.264)
└── demo-poster.jpg  ← optional thumbnail shown before demo.mp4 plays
```

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
| `desc`     | yes      | 1–2 sentences for the listing card. Czech in `.cz.md`. | written from Description + Business Case |
| `category` | yes      | Exactly one technology: `Power Apps`, `Power BI`, `Power Automate`, `RPA (UiPath)`, `SharePoint`, … | Components (see mapping below) |
| `business` | yes      | One area: `Finance`, `Sales`, `HR`, `PMO`, `Network Deployment`, `Legal`, … | Department |
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
| `RPA` | `RPA (UiPath)` |
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
- `> quote` blockquotes render as styled testimonials.
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
python scripts/validate_post.py <path-to-post-folder>
```

Run it and fix everything it reports until it exits clean. This is the same
script the publish pipeline runs, so anything it rejects here would have
failed there twenty minutes later — except here the user is still in the
conversation and a bad `category` is a one-turn fix.

Do not describe a post as finished while the validator is unhappy.

## Publishing

Publishing goes **through git**, not straight to storage. The `articles`
container is a projection of `content/articles/` in the **team-hub** repo: a
pipeline makes the container match git and deletes what git does not have.
Uploading a blob by hand is not a shortcut — the next sync removes it, and the
change has no history, no diff and no author.

**Write the post folder locally. The author uploads it.** Nothing here needs
SharePoint sync, a connected library, or any credential.

1. Write `<slug>/` — the `.md`, the `.cz.md` and the media, flat — somewhere
   the author can get at it: a connected folder in this session if there is
   one, otherwise hand the files over for download.
2. Run the validator until it exits clean. Do this **before** telling them to
   upload; a rejected post is much cheaper to fix while you are still holding
   the material.
3. Then tell them exactly this, with the folder path filled in:

   > Open <https://czcetin.sharepoint.com/sites/AutomationCoE/Team_Hub_Posts>
   > and drag the **`<slug>` folder** into the library — the folder itself,
   > not the files inside it. Then open the row for `<slug>.md`, set
   > **`PostStatus`** to **`Ready`**, and you are done.

That is the whole handover. Two actions, no typing.

**Do not ask the author to fill in `Slug`, `IdeaKey`, `ArticleAuthor` or
`Title`.** The flow reads them out of the post's own frontmatter — the
frontmatter is the manifest, the columns are only its projection for people to
look at. Asking someone to retype what is already in the file is how the two
drift apart.

Flipping `PostStatus` to `Ready` is the publish decision, and the only human
gate before the post reaches the whole company. From there a flow commits the
folder to the team-hub repo in one push, the pipeline validates it and syncs
it to the container media-first, and the library shows `Published` with the
live URL — or `Failed` with the reason in `PostMessage`. Live within ~60 s.

**Update** an existing post the same way: same slug, upload over it, flip
`Ready` again. **Unpublish** by deleting the folder from `content/articles/`
in git; the pipeline prunes the blobs (14 days of soft delete undo).

## Hosted HTML pages

A standalone page (strategy deck, workshop) is one **fully self-contained**
`.html` file (inline CSS/JS, images as data: URIs) uploaded to the
`html-pages` container; `<name>.html` is served at `/<name>`. It must carry
`portal:*` meta tags for the listing — copy
[references/html-page-template.html](references/html-page-template.html).

## Common mistakes

| Mistake | Reality |
|---|---|
| Uploading with `az storage blob upload-batch` | Bypasses git, the validator and the audit trail, and the next sync deletes it. Publish through the library. |
| Handing back without running the validator | Team Hub fails *silently* — a broken post just vanishes from the listing. The validator is the only thing that turns that into an error. |
| Uploading the files loose instead of the folder | The slug folder *is* the post. Loose files scatter into the library root and publish nothing. |
| Asking the author to type `Slug` / `IdeaKey` / `ArticleAuthor` | The flow reads them from the frontmatter. Retyping is how the file and the columns drift apart. |
| Saying the post is published once it is uploaded | Uploading makes it a `Draft`. The `Ready` flip is what publishes it. |
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
