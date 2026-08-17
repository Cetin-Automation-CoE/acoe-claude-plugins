---
name: portal-article
description: |
  Use when creating, writing, translating, or updating a solution article or a hosted HTML page for the ACOE portal — the internal showcase site with the /solutions listing. Triggers: "write a portal article", "add a solution to the portal", "showcase article", "napiš článek na portál", "publikuj řešení", "solution showcase", or converting a description of a Power Apps / Power BI / Power Automate / RPA solution into portal content.
  Do NOT use for fetching an existing SharePoint showcase page into the portal repo — the portal repo's publish-solution skill does that. Do NOT use for PRD/idea intake — use idea-forge.
cowork:
  category: productivity
  icon: Newspaper
allowed-tools: Read, Write, Edit, Bash
---

# ACOE Portal Article

Author content for the ACOE portal. An article is a **self-describing folder
of files** — there is **no central index or database to edit**: the portal
derives the /solutions listing automatically from each article's frontmatter.

## Folder contract

Folder name = slug = URL (`/solutions/<slug>`). Kebab-case ASCII, never
renamed after publishing. All files flat inside — no subfolders.

```
<slug>/
├── <slug>.md        ← English article (required)
├── <slug>.cz.md     ← Czech article (expected; same structure, Czech text)
├── screenshot-1.png ← media next to the .md
├── demo.mp4         ← optional short demo video (≤ ~100 MB, H.264)
└── demo-poster.jpg  ← optional thumbnail shown before demo.mp4 plays
```

Start from [references/article-template.md](references/article-template.md)
and [references/article-template.cz.md](references/article-template.cz.md).

## Frontmatter (drives the listing and filters)

| Field      | Required | Rules |
|------------|----------|-------|
| `title`    | yes      | In `.cz.md` this IS the Czech listing title. |
| `desc`     | yes      | 1–2 sentences for the listing card. Czech in `.cz.md`. |
| `category` | yes      | Exactly one technology: `Power Apps`, `Power BI`, `Power Automate`, `RPA (UiPath)`, `SharePoint`, … |
| `business` | yes      | One area: `Finance`, `Sales`, `HR`, `PMO`, `Network Deployment`, `Legal`, … |
| `author`   | yes      | `Surname Firstname` (e.g. `Horák Dominik`). |
| `added`    | yes      | `YYYY-MM-DD`; listing sorts newest first. |
| `tags`     | no       | Extra filter pills, comma-separated. **If the solution uses AI in any form, set `tags: AI`.** |
| `role`     | no       | Author role override. |

Single-line `key: value` pairs only. Broken frontmatter = article silently
missing from the listing.

## Body conventions the renderer understands

- Open with a **bold lead paragraph** (`**…**`) — the elevator pitch. Not a heading.
- `### ORIGINAL STATE`, `### CURRENT STATE`, `### BENEFITS` — these exact
  headings render as a three-column storyline block. Use bullets under each.
- Media by absolute path: `![](/solutions/<slug>/<file>)`. Two or more
  consecutive images become a two-column lightbox gallery.
- **A video in the folder is embedded, not linked**: write
  `![](/solutions/<slug>/demo.mp4)` and the portal renders an inline player
  (with `demo-poster.jpg` as its thumbnail if present). Only use a
  `[▶ Watch the demo video](https://…)` link for externally hosted videos —
  and host those in a shared SharePoint/Stream location, never personal
  OneDrive (personal links 403 for other users).
- `> quote` blockquotes render as styled testimonials.

## Publishing

Publish = upload the folder into the `articles` container of storage account
`stacoenpwebhubgwc` (CETIN network required) — media files first, `.md` last:

```bash
az storage blob upload-batch --account-name stacoenpwebhubgwc --auth-mode login \
  -d "articles/<slug>" -s <local-folder>
```

Live within ~60 s. Update = overwrite the file. Unpublish = delete the
folder (soft delete keeps 14 days of undo). If working inside the portal
repo, prefer its `tools/publish-solution.py <slug>`.

## Hosted HTML pages

A standalone page (strategy deck, workshop) is one **fully self-contained**
`.html` file (inline CSS/JS, images as data: URIs) uploaded to the
`html-pages` container; `<name>.html` is served at `/<name>`. It must carry
`portal:*` meta tags for the listing — copy
[references/html-page-template.html](references/html-page-template.html).

## Common mistakes

| Mistake | Reality |
|---|---|
| Creating or editing `solutions/index.json` | Obsolete. The listing is derived from frontmatter; a stray `index.json` is ignored dead weight. Never write one. |
| Linking a local `demo.mp4` as `[▶ Watch…](…)` | Local videos are embedded with image syntax `![](…demo.mp4)` → inline player. |
| Omitting `tags: AI` on an AI-flavored solution | The AI pill/filter comes only from `tags`. AI Builder, Copilot, GPT — all count. |
| Opening with a `###` heading instead of a bold paragraph | The renderer expects a bold lead; headings start at the storyline sections. |
| Czech texts only in the EN file (`titleCz`/`descCz`) | Czech listing texts come from the `.cz.md` file's own `title`/`desc`. |
| Renaming the folder after publishing | Slug = URL; renaming breaks links. Pick the slug once. |
