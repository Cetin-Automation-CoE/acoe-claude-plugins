# Acoe Claude Skills

Shared [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) skills for Acoe engineers, distributed as a plugin marketplace.

Skills give Claude our conventions — review checklists, migration rules, house style — so you don't have to re-explain them in every session. Claude loads a skill automatically when a task matches its description.

## Install

Run these two commands inside Claude Code (they're slash commands, not shell commands):

```
/plugin marketplace add acoe/claude-plugins
/plugin install acoe-skills@acoe
```

That's it. Restart isn't required. Verify with `/plugin` — you should see `acoe-skills` listed as enabled.

## What's included

| Skill | Fires when |
|---|---|
| `pr-review` | Reviewing a PR or diff, or asking whether a change is ready to merge |

## Updating

New skills and fixes land here regularly. Pull them with:

```
/plugin marketplace update acoe
```

## Team rollout

Instead of asking everyone to run the install commands, commit a settings file to a project repo. Anyone who opens that project gets the skills automatically.

Create `.claude/settings.json` in the project repo:

```json
{
  "extraKnownMarketplaces": {
    "acoe": {
      "source": { "source": "github", "repo": "acoe/claude-plugins" }
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
```

Two `.claude-plugin` folders, doing different jobs. The root one declares the marketplace; the inner one declares a single plugin. The `name` in `plugin.json` must match the `plugins[].name` entry in `marketplace.json` — a mismatch there is the usual cause of an install failing while both files look fine on their own.

## Troubleshooting

**Install fails.** Check that `acoe-skills` in `plugin.json` matches the entry in `marketplace.json`, and that both files are valid JSON (GitHub's file view highlights a stray comma clearly).

**Skill never fires.** Almost always the `description`. Rewrite it to name the situations and vocabulary that should trigger it.

**Frontmatter ignored.** The `---` fences must be the first and last lines of the block, with no blank line above the opening one.

## Questions

`#claude-skills` on Slack, or open an issue.
