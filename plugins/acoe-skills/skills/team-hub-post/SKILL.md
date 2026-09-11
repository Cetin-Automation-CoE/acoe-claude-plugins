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

Posts are published **through the Team Hub Posts library**: you write and
validate the folder, the author drops it into SharePoint and flips a status,
and a flow copies it into the portal's storage. See [Publishing](#publishing).
The old `az storage blob` route bypasses the validator and the library's
history — do not use it.

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
- an Idea whose **status is not `Deployed`** is not finished. Say so and
  stop — Team Hub shows delivered solutions only. `Rozpracováno` means the
  post can be drafted for review but must not be uploaded to the library.

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

Run it and fix everything it reports until it exits clean. The publish flow
checks only the folder's shape, not its content, so anything the validator
rejects here would otherwise reach the portal and silently vanish from the
listing — here the user is still in the conversation and a bad `category`
is a one-turn fix.

Do not describe a post as finished while the validator is unhappy.

## Publishing

The **Team Hub Posts** library in SharePoint is the source of truth for posts:
every version, author and timestamp is kept there, and a Power Automate flow
copies a post from the library into the portal's storage. Nothing here needs
a credential, a connected folder or any tool beyond the browser.

**Write the post folder locally. The author uploads it.**

1. Write `<slug>/` — the `.md`, the `.cz.md` and the media, flat — into this
   session's outputs so the author can download it.
2. Run the validator until it exits clean. Do this **before** telling them to
   upload; the flow checks only the folder's shape, not the content, so a bad
   `category` found here costs one turn and found later costs a failed publish.
3. Then tell them exactly this, with the slug filled in:

   > Download the **`<slug>` folder**, open
   > <https://czcetin.sharepoint.com/sites/AutomationCoE/Team_Hub_Posts> and
   > drag the folder in — the folder itself, not the files inside it. Then
   > open the row for `<slug>.md`, set **`PostStatus`** to **`Ready`**, and
   > wait a minute: the row shows **`Published-DEV`** with a **`DevUrl`** to
   > check the post on the DEV portal. When it looks right, set `PostStatus`
   > to **`Publish live`** — the row shows **`Published`** with the
   > **`LiveUrl`**.

That is the whole handover: one drag, two flips.

**Do not ask the author to fill in `Slug`, `IdeaKey`, `ArticleAuthor` or
`Title`.** The flow reads them out of `<slug>.md`'s frontmatter and writes them
onto the row — the frontmatter is the manifest, the columns are its projection
for people to look at.

What each status means:

| `PostStatus` | Who sets it | Meaning |
|---|---|---|
| `Draft` | default on upload | in the library, not published |
| `Ready` | author | publish to **DEV** now |
| `Published-DEV` | flow | on the DEV portal; `DevUrl` filled |
| `Publish live` | author | publish to **LIVE** now (DEV must have it first) |
| `Published` | flow | on the LIVE portal; `LiveUrl` filled |
| `Unpublish` | author | remove from both portals |
| `Unpublished` | flow | removed (storage keeps 14 days of undo) |
| `Failed` | flow | see `PostMessage` for the reason; fix, then flip `Ready` again |

**Update** an existing post the same way: same slug, upload over it, flip
`Ready` again (then `Publish live`). **Unpublish** by flipping `Unpublish`.
Never rename the folder — slug = URL.

If the Microsoft 365 connector is available in your session, upload the
folder into the library yourself instead of asking the author to; everything
after that is identical.

## Hosted HTML pages

A standalone page (strategy deck, workshop) is one **fully self-contained**
`.html` file (inline CSS/JS, images as data: URIs) uploaded to the
`html-pages` container; `<name>.html` is served at `/<name>`. It must carry
`portal:*` meta tags for the listing — copy
[references/html-page-template.html](references/html-page-template.html).

## Common mistakes

| Mistake | Reality |
|---|---|
| Uploading with `az storage blob upload-batch` | Bypasses the validator and the library's history; the post has no row, no author and no undo. Publish through the library. |
| Setting `PostStatus` on a media row | The flow reads the status from the `<slug>.md` row only; a flip on a screenshot is reported as `Failed` with a hint. |
| Handing back without running the validator | Team Hub fails *silently* — a broken post just vanishes from the listing. The validator is the only thing that turns that into an error. |
| Uploading the files loose instead of the folder | The slug folder *is* the post. Loose files scatter into the library root and publish nothing. |
| Asking the author to type `Slug` / `IdeaKey` / `ArticleAuthor` | The flow reads them from the frontmatter. Retyping is how the file and the columns drift apart. |
| Saying the post is published once it is uploaded | Uploading makes it a `Draft`. `Ready` publishes to DEV; `Publish live` is what puts it on the portal people use. |
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
