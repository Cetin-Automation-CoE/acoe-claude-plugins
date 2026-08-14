# ACOE Claude Skills

Shared [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) skills for Acoe engineers, distributed as a plugin marketplace. The same plugin also installs into the Claude app (claude.ai web and Claude Desktop) — see [Install in the Claude app](#install-in-the-claude-app-claudeai--desktop).

Skills give Claude our conventions — review checklists, migration rules, house style — so you don't have to re-explain them in every session. Claude loads a skill automatically when a task matches its description.

## Install in Claude Code

Run these two commands inside Claude Code (they're slash commands, not shell commands):

```
/plugin marketplace add Cetin-Automation-CoE/acoe-claude-plugins
/plugin install acoe-skills@acoe
```

That's it. Restart isn't required. Verify with `/plugin` — you should see `acoe-skills` listed as enabled.

## Install in the Claude app (claude.ai / Desktop)

Plugins work in chat on the web, the Chat tab in Claude Desktop, and Claude Cowork. Requires a paid plan (Pro, Max, Team, Enterprise).

As a personal plugin:

1. In claude.ai, open the **Customize** menu in the left sidebar and go to the **Plugins** tab.
2. In **Personal plugins**, click **+** and select **Add marketplace**.
3. Choose **GitHub** as the source and enter `Cetin-Automation-CoE/acoe-claude-plugins`.
4. Install **Automation CoE** (`acoe-skills`) from the marketplace and leave **Sync automatically** on.

The [Claude GitHub App](https://github.com/apps/claude) must be installed on this repository for syncing to work.

Org-wide (Team/Enterprise): an Owner can instead add the same repository under **Organization settings > Plugins**, which provisions the plugin for everyone.

### How the app picks up updates

- **Automatic sync** fires only when a **merged pull request** on `main` contains a **version bump** in `.claude-plugin/marketplace.json` / `plugin.json`. Direct pushes to `main` do not trigger a sync — this is why changes here should land via PR with a version bump.
- **Manual sync** is available anytime from the Plugins page if you don't want to wait.
- Either way, a sync can take up to 30 minutes to propagate.

## What's included

| Skill | Fires when |
|---|---|
| `cetin-design` | Producing CETIN business deliverables (presentations, artifacts, dashboards, documents) — applies CETIN brand colors, fonts, and logos |
| `cetin-html-slides` | Building or editing a CETIN training deck as self-contained HTML slides — fixed 16:9 stage, chapter files, contents page, markdown companions; also converting a PowerPoint or outline into that format |
| `company-design` | Producing work-related visual output for any company — learns the brand once (website, logos, guidelines), then applies it automatically |
| `critique` | Asking for feedback on emails, slides, documents, or messages — "critique this", "is this clear", "poke holes in this" (Czech and English) |
| `gantt` | "Udělej gantt", "harmonogram projektu" — builds a roadmap-style Gantt PowerPoint from a Microsoft Planner export (.xlsx) |
| `idea-forge` | "Draft a PRD", "run idea forge" — guided 8-phase business analyst interview producing a Markdown PRD with As-Is/To-Be diagrams |
| `morning-brief` | "Morning brief", "what's on my plate today" — daily summary of calendar, email, Teams, and Planner tasks |
| `pr-review` | Reviewing a PR or diff, or asking whether a change is ready to merge |
| `projektovy-status-pmo` | "Připrav projektový status" — builds an R/A/G project status for PMO from recent emails, meetings, and Teams activity |
| `rfp-evaluation` | "Evaluate vendor proposals", "score this RFP" — weighted scoring matrix, HTML dashboard, and shortlist memo for CETIN procurement |
| `skill-explorer` | "Which skills should I use" — onboarding interview that recommends a personalised skill set for the user's role |
| `weekly-planning` | "Plan my week", "weekly recap" — persistent weekly planning with task list in OneDrive and Adaptive Card dashboards |

## Updating

New skills and fixes land here regularly. In Claude Code, pull them with:

```
/plugin marketplace update acoe
```

The Claude app updates itself via GitHub sync — see [How the app picks up updates](#how-the-app-picks-up-updates).

## Team rollout

Instead of asking everyone to run the install commands, commit a settings file to a project repo. Anyone who opens that project gets the skills automatically.

Create `.claude/settings.json` in the project repo:

```json
{
  "extraKnownMarketplaces": {
    "acoe": {
      "source": { "source": "github", "repo": "Cetin-Automation-CoE/acoe-claude-plugins" }
    }
  },
  "enabledPlugins": {
    "acoe-skills@acoe": true
  }
}
```

`extraKnownMarketplaces` registers this repo as a trusted plugin source. `enabledPlugins` turns on a specific plugin from it. You need both — registering alone only makes the plugin available, it won't load.

Scope depends on where the file lives:

| Location | Applies to |
|---|---|
| `.claude/settings.json` in a project repo | Everyone working in that project |
| `~/.claude/settings.json` | Just you, in every project |
| Managed settings file (pushed by IT) | Everyone, org-wide, not locally overridable |

Open a PR for this rather than committing to `main` directly — it changes Claude's behavior for everyone on the project.

## Contributing a skill

1. Create `plugins/acoe-skills/skills/<your-skill>/SKILL.md`
2. Bump `version` in `.claude-plugin/marketplace.json` and `plugins/acoe-skills/.claude-plugin/plugin.json`
3. Open a PR

A skill is a folder with a `SKILL.md` at its root:

```markdown
---
name: your-skill
description: Use when the user is doing X, asks about Y, or mentions Z. Covers A, B, and C.
---

# Your Skill

Instructions for Claude go here.
```

**The `description` is the most important line in the file.** Claude reads only the name and description up front and uses them to decide whether to load the skill at all. Write it as trigger conditions — when to use it, what it covers, what words the user might use — not as a title. "PR review guidelines" gets skipped; "Use when reviewing a pull request or diff…" gets picked up.

Other conventions:

- Keep `SKILL.md` under a few hundred lines. Split longer reference material into sibling files (`checklist.md`, `reference.md`) and point to them from `SKILL.md` so they're only read when needed.
- Test before opening the PR: symlink your skill folder into `~/.claude/skills/` for live editing, then ask Claude something that should trigger it. If it doesn't fire, rewrite the description — that's the cause nearly every time.
- Remove the symlink once you're done, or you'll have two copies competing.

## Repo layout

```
.claude-plugin/
  marketplace.json              ← the catalog
plugins/
  acoe-skills/
    .claude-plugin/
      plugin.json               ← this installable plugin
    skills/
      pr-review/
        SKILL.md
      critique/
        SKILL.md
      …one folder per skill
```

Two `.claude-plugin` folders, doing different jobs. The root one declares the marketplace; the inner one declares a single plugin. The `name` in `plugin.json` must match the `plugins[].name` entry in `marketplace.json` — a mismatch there is the usual cause of an install failing while both files look fine on their own.

## Troubleshooting

**Install fails.** Check that `acoe-skills` in `plugin.json` matches the entry in `marketplace.json`, and that both files are valid JSON (GitHub's file view highlights a stray comma clearly).

**Skill never fires.** Almost always the `description`. Rewrite it to name the situations and vocabulary that should trigger it.

**Frontmatter ignored.** The `---` fences must be the first and last lines of the block, with no blank line above the opening one.

## Questions

`#claude-skills` on Slack, or open an issue.
