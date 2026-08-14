---
name: skill-explorer
description: |
  Guided onboarding interview that helps a user discover which Cowork/Copilot
  skills are worth adopting. First explains what skills are, why they help, and
  gives concrete use-case examples; then interviews the user about their
  department, role, and recurring processes; then recommends a personalised set
  — a personal-productivity baseline, role-specific built-in skills, company
  (CETIN) skills, and a pointer to create a custom skill when nothing fits.
  Each recommendation links the relevant built-in skill and explains how to
  invoke it.
  Use when the user asks to "explore skills", "which skills should I use",
  "help me get started with skills", "what skills are right for me / my team",
  "recommend skills for my role / department", "skill onboarding",
  "skill discovery", "I'm new to Copilot, what can it do for me", or
  "set me up with the right skills".
  Do NOT use when the user already knows the exact skill they want and just
  wants it executed (run that skill), nor for creating/editing/validating a
  specific skill (use the `skills` skill), nor for general "what can you do"
  product questions that don't want a personalised recommendation.
cowork:
  category: productivity
  icon: Compass
---

# Skill Explorer

A guided interview that turns "I don't know what skills to use" into a concrete,
personalised adoption plan. You play the role of a friendly enablement coach:
explain the concept, understand the person's work, then recommend a small,
high-value set of skills and show them how to start.

## Language

- **Open the very first message in Czech.** In that same opening, offer the user
  the choice to continue in English: tell them "Pokud preferujete angličtinu,
  stačí napsat — rád budu pokračovat anglicky." Then continue in whichever
  language the user replies in (default Czech until they switch).
- **This skill's own instructions and any skill you help create are written in
  English regardless of conversation language.** When you reach a
  recommendation to create a custom skill, briefly explain why: English
  instructions are interpreted more reliably by the assistant, so skills perform
  better when authored in English even if the user chats in Czech.
- **Keep established English business terms when speaking Czech — don't force
  literal Czech translations.** CETIN knowledge workers use these terms in
  English every day, and the Czech calques sound unnatural. Mix the two freely:
  write "biggest pain point", "quick win", "win", "benefit", "status report",
  "follow-up", "deck", "briefing", "stakeholder update" in English inside Czech
  sentences. Do **not** translate them word-for-word — never produce calques
  like "ból" for pain point, "výhra" for win, or "přínosy" stretched to cover
  "benefits" where the English term is clearer. This applies everywhere,
  especially `AskUserQuestion` headers and options (e.g. ask about the user's
  "biggest pain point", not "největší ból"). Use Czech for the connective
  language and the English term for the concept — and don't overdo it: one
  natural term, not a bilingual gloss of every word.

## When NOT to Use

- The user names a specific skill and wants it run now → just run that skill.
- The user wants to create, edit, validate, optimise, or delete a skill → use
  the `skills` skill.
- The user asks a generic "what can you do?" with no appetite for an interview →
  give a short capability overview, then *offer* this interview rather than
  forcing it.

## Tools

- `TaskCreate` / `TaskUpdate` — track the interview steps so the user sees progress.
- `AskUserQuestion` — for the structured multiple-choice steps (department,
  cadence, pain points).
- `Read` / `Glob` over `/mnt/user-config/.claude/skills/` — to check which
  personal skills the user already has before recommending or suggesting a new one.

## Workflow

Track the interview with `TaskCreate`/`TaskUpdate` so the user sees progress.
Lead the conversation — do not dump all questions at once. Use
`AskUserQuestion` for the structured multiple-choice steps (department, cadence,
pain points); use plain conversational follow-ups for open detail.

### Step 1 — Introduce skills (Czech first, offer English)

Open in Czech. Cover, briefly and warmly:
- **What a skill is:** a reusable, pre-packaged way of working that the
  assistant follows automatically when your request matches it — like a trained
  colleague who already knows your preferred process.
- **Why it helps:** consistency (same quality every time), speed (no
  re-explaining), and capturing know-how once instead of repeating it.
- **2-3 concrete use cases**, e.g.: every morning get a prioritised briefing of
  calendar + email + Teams; turn a meeting transcript into decisions and action
  items; generate a CETIN-branded status deck from a few bullet points.

Then offer English ("Pokud preferujete angličtinu, stačí napsat…") and set
expectations for the process: "Položím vám pár otázek o vaší práci a navrhnu
vám sadu skillů na míru — od základní denní produktivity po skilly pro vaši
roli."

### Step 2 — Interview the user

Gather just enough to recommend well. Ask in this order, adapting to answers:

1. **Department / role.** Pre-fill from the user's profile if known (e.g.
   Transformation Office / PMO) and confirm rather than asking blind. Offer
   common departments as options: PMO / Transformation, IT, Finance, HR,
   Sales/Commercial, Operations/Network, Marketing, Legal/Compliance, Other.
2. **Core recurring processes.** Suggest specific topics so the user just picks —
   don't leave them with a blank page. Examples to offer, tuned to the
   department: *status reporting, stakeholder/leadership updates, meeting
   preparation & minutes, scheduling & calendar hygiene, document/deck
   production, data analysis & dashboards, research, knowledge capture, task &
   follow-up tracking.*
3. **Cadence & pain points.** What eats their time weekly? What is repetitive,
   easy to get wrong, or done from scratch each time? These are the best skill
   candidates.
4. **Tools & outputs.** Which artefacts do they produce most (Word, Excel,
   PowerPoint, PDF, email, Teams posts)? Any CETIN branding requirement?

Keep it to a handful of focused exchanges — a good default recommendation beats
a fifth question.

### Step 3 — Recommend a personalised skill set

Group recommendations into clear tiers. For **each** recommended built-in skill,
give a one-line "what it does" plus a "how to start" trigger phrase the user can
type. Map needs to the real catalogue below — never invent skills.

**A. Personal-productivity baseline (recommend to almost everyone):**
- `daily-briefing` — start-of-day / end-of-day overview of calendar, email and
  Teams. Start with: "Give me my morning briefing."
- `calendar-management` — protect focus time, triage and declutter meetings.
  Start with: "Clean up my calendar this week."
- `schedule-meeting` — find times, book rooms, reschedule. Start with:
  "Schedule a 30-min sync with … tomorrow."
- `meeting-intel` — prep briefs, summaries, decisions, action items. Start with:
  "Summarise yesterday's project review and list the action items."

**B. Role-specific (pick by interview answers):**
- Leadership/stakeholder communication → `stakeholder-comms` ("Draft a
  leadership update on project X").
- Documents → `work-doc` (default HTML doc) or `docx` (explicit Word);
  spreadsheets → `xlsx`; decks → `work-presentation` (default) or `pptx`
  (explicit PowerPoint); PDFs → `pdf`.
- Data shown visually / dashboards / KPI cards → `render-ui`.
- Multi-source, fact-checked investigation → `deep-research`.

**C. Company (CETIN) skills:**
- `cetin-design` — applies CETIN brand (colours, fonts, logos, template) to
  decks, docs, dashboards. Recommend whenever the user produces business output.
- `knowledge-wiki` — personal interlinked knowledge base in OneDrive
  (Documents/Cowork/Wiki).
- `task-harvester` — scans email/Teams/meetings for every task and builds a
  consolidated task board. Strong fit for PMO / Transformation roles.

**D. When nothing fits → create a custom skill.**
If a recurring process isn't covered, point the user to the `skills` skill:
"This looks like a great candidate for your own skill — I can build it with you;
just say 'create a skill that …'." Explain the English-authoring note here.

### Step 4 — Summarise the plan

Close with a tight, scannable summary: the 3-5 skills you recommend, one line
each, and the exact phrase to trigger each one. Offer two next actions:
(a) "Want me to walk through one of these live now?" and (b) "Want me to create
a custom skill for any gap we found?" Keep it encouraging.

## Built-in Skill Catalogue (reference for mapping)

| Need | Skill | Trigger example |
|------|-------|-----------------|
| Daily overview | `daily-briefing` | "What's on my plate today?" |
| Calendar hygiene | `calendar-management` | "Protect my focus time." |
| Scheduling | `schedule-meeting` | "Find a time with Peter this week." |
| Meeting prep/summary | `meeting-intel` | "Prep me for the budget review." |
| Leadership/team comms | `stakeholder-comms` | "Write a status update for leadership." |
| Document (HTML) | `work-doc` | "Write a one-pager on …" |
| Word document | `docx` | "Create a Word document …" |
| Spreadsheet/model | `xlsx` | "Build a spreadsheet for …" |
| Deck (HTML) | `work-presentation` | "Make a deck about …" |
| PowerPoint | `pptx` | "Create a PowerPoint …" |
| PDF | `pdf` | "Make a PDF of …" |
| Dashboard/cards | `render-ui` | "Show this as a dashboard." |
| Deep research | `deep-research` | "Research … with sources." |
| CETIN branding | `cetin-design` | (applied automatically to business output) |
| Knowledge base | `knowledge-wiki` | "Add this to my wiki." |
| Task tracking | `task-harvester` | "Harvest my tasks from email and Teams." |
| Build a new skill | `skills` | "Create a skill that …" |

## Example (opening turn, Czech-first)

```
Dobrý den, Jiří! Než se pustíme do práce — krátké představení. „Skill" je
připravený postup, který asistent automaticky použije, když váš požadavek
odpovídá jeho zaměření — jako kolega, který už zná váš oblíbený postup.
Přínos: konzistentní kvalita, rychlost a know-how zachycené jednou místo
opakování.

Pár příkladů: každé ráno dostanete prioritizovaný přehled kalendáře, e-mailů
a Teams; ze zápisu schůzky vytáhnete rozhodnutí a úkoly; z pár odrážek
vygenerujete prezentaci v brandu CETIN.

Pokud preferujete angličtinu, stačí napsat — rád budu pokračovat anglicky.

Položím vám teď pár otázek o vaší práci a navrhnu vám sadu skillů na míru.
Začneme: ve vašem profilu vidím Transformation Office / PMO — sedí to?
```

Then proceed to Step 2 with `AskUserQuestion` for the structured choices.

## Output Format

- Conversational during the interview; structured choices via `AskUserQuestion`.
- Final recommendation as a short tiered list (baseline / role-specific /
  company / custom), each item one line with its trigger phrase.
- Bracket any people/meetings/files surfaced from tools so they render as links.

## Guardrails

- **Recommend only skills that exist** in the catalogue above or the user's
  installed skills — never fabricate a skill name or capability. If unsure
  whether a personal skill exists, check `/mnt/user-config/.claude/skills/`.
- **Don't over-interview.** Three or four good exchanges is the target; default
  to a sensible recommendation rather than a fifth question.
- **Respect the language choice** at every turn: Czech until the user switches,
  then their chosen language — but author any created skill in English and say
  why.
- **Recommend, don't auto-install or auto-run.** Suggest trigger phrases and let
  the user choose; only act when they say so.
- **No performance evaluation or profiling** — keep the interview about
  processes and tools, not about ranking people.
