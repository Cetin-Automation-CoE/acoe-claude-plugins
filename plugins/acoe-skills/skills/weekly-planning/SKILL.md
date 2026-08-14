---
name: weekly-planning
description: |
  Personal weekly planning assistant. Onboards the user, maintains a persistent task list and preferences
  in OneDrive, produces a past-week recap and a next-week plan rendered as concise interactive Adaptive
  Card dashboards, surfaces public holidays for the user's country and team OOO, and pulls priorities
  from the user's line manager and direct reports (resolved at runtime, not hardcoded).

  TRIGGERS: "weekly planning", "plan my week", "weekly recap", "week ahead", "Friday recap", "Monday plan",
  "wrap up the week", "start the week", "what did I get done last week", "what's on for next week",
  "team topics for the week", "review my tasks for the week".

  Do NOT use for: single-day briefings (use morning-brief), one-off meeting recaps (use meeting-intel),
  generic email triage, scheduling individual meetings (use schedule-meeting), or quarterly/OKR planning.
cowork:
  category: productivity
  icon: TaskListLtr
---

# Weekly Planning

End-to-end weekly planning loop. Onboards on first run, then on each invocation produces a **past-week recap** and/or a **next-week plan**, keeps `tasks.md` + `preferences.md` in the user's OneDrive up to date, and archives a snapshot per ISO week.

**Output style: concise + interactive.** Every dashboard uses Accordion / TabSet / Carousel for drill-down so the top view stays short; verbose text is replaced by tables, badges, charts, and progress bars.

## When NOT to Use

- "What's on for today" / "brief me on this morning" → `morning-brief`
- "Summarise that meeting" → `meeting-intel`
- "Schedule X" / "find a time with Y" → `schedule-meeting`
- "Clean up my calendar" without a planning frame → `calendar-management`
- OKR or quarterly planning → out of scope

## Resolve-At-Runtime Rule

The skill **never hardcodes personal details**. The following are resolved at runtime and stored in `preferences.md`:

| Item | How it's resolved |
|---|---|
| Line manager | `GetMyDetails` → `GetManagerDetails` (Graph). Drives the "Manager priorities" section. |
| Direct reports | `GetDirectReportsDetails` (Graph). Drives team-topic sections. |
| Country (for holidays) | First, infer from the user's email TLD (e.g. `.cz` → `CZ`, `.sk` → `SK`, `.de` → `DE`). If the TLD is ambiguous (`.com`, `.org`) or unsupported, `AskUserQuestion`. Save to `preferences.md`. |
| Time zone | From system context (already provided per turn). |
| Output language | Ask once during onboarding; default English. |

## Storage

- **Default folder (OneDrive):** `/Documents/Cowork/WeeklyPlanning`
- On first run, propose default and let user override via `AskUserQuestion`. Persist chosen path in `preferences.md`.
- Files:
  - `tasks.md` — single source of truth (see [tasks-template](reference/templates/tasks-template.md))
  - `preferences.md` — folder, country, default sections, schedule choices, language (see [preferences-template](reference/templates/preferences-template.md))
  - `archive/YYYY-WW.md` — one snapshot per ISO week

Reading: `ReadFileContent` via OneDrive MCP using `drive_id` from `GetDefaultDrive` + `item_path`.
Writing: `python scripts/upload_md.py <local-path> <onedrive-path>` (emits a `CallGraph` envelope).

## Quick-Start Decision Tree

```
Invoked
├── preferences.md missing?            → onboarding (reference/onboarding.md)
├── User said "recap" / past tense?    → recap only (reference/recap.md)
├── User said "plan" / "next week"?    → plan only (reference/plan.md)
└── No qualifier?
       ├── Mon morning  → recap last week THEN plan this week
       ├── Fri afternoon → recap this week THEN draft plan for next
       └── Otherwise    → AskUserQuestion: recap / plan / both
```

## Onboarding (first run only)

Trigger: `preferences.md` does not exist, OR user says "reset weekly planning".
Full script: [reference/onboarding.md](reference/onboarding.md).

Five short steps, each as one `AskUserQuestion`:

1. **Storage folder** — default `/Documents/Cowork/WeeklyPlanning`, allow override.
2. **Default sections** for the next-week plan (multi-select).
3. **Schedule** — default Friday 12:00 recap + Monday 08:00 plan (both `inline` execution).
4. **Country for public holidays** — inferred from email TLD when unambiguous; otherwise asked from the list of supported countries (`scripts/holidays.py` exit status 3 names them). Save ISO code to `preferences.md`.
5. **Output language** — default English; offer Czech, German, Polish, Slovak, "bilingual EN + local".

Then seed `tasks.md` by scanning last 14 days of email / Teams / meetings and ask the user to keep, drop, or rewrite each candidate.

If schedules chosen, call `SetupScheduledPrompt` per cadence (see onboarding.md for exact arguments).

## Task Model

Each task in `tasks.md` is one bullet with inline attributes:

```
- [ ] **Title** — `priority:high` `due:2026-05-22` `cat:#transformation` `status:planned` `who:user@example.com` `src:email`
  Notes: short context, evidence links.
```

Status: `planned | in-progress | done | dropped | carried-over`.
Priority: `critical | high | medium | low`.
Category tags are user-defined; common defaults: `#transformation`, `#team`, `#admin`, `#1on1`, `#governance`.

Critical tasks are surfaced in a dedicated `style=warning` container on the plan dashboard. No outbound emails or notifications are sent — visibility only.

## Weekly Run Flow

### A. Past-Week Recap

Full detail: [reference/recap.md](reference/recap.md).

1. Load `tasks.md`, pick planned/in-progress tasks for the past ISO week.
2. Auto-detect completion signals in parallel (calendar, outbound email, user's Teams messages, Planner if reachable).
3. Propose `done | in-progress | dropped` per task with evidence, batch-confirm via `AskUserQuestion`.
4. Write updated `tasks.md`.
5. Compute KPIs: completion rate, time-by-category, meetings attended, focus hours, critical closed.
6. Render concise interactive dashboard (skeleton below).
7. Archive `archive/YYYY-WW.md`.

### B. Next-Week Plan

Full detail: [reference/plan.md](reference/plan.md).

1. Load default sections from `preferences.md`. One `AskUserQuestion` to add/remove sections for this run (skipped on scheduled runs).
2. Gather in parallel:
   - Carry-overs from `tasks.md`
   - Public holidays via `python scripts/holidays.py --country <ISO> --start <Mon> --end <Sun>` — exit status 3 → fallback to `AskUserQuestion` for country
   - Team OOO via `ListCalendarView` (own) + `QueryGraph` against direct reports' calendars (filter `showAs=oof`)
   - Manager priorities — `SearchM365(from_user=<manager from preferences.md>, after=<-7d>)`
   - Calendar Mon–Fri + conflict detection (overlaps, >3h back-to-back)
   - Team topics — Planner, 1:1 notes, Teams chats, direct-report emails
3. Draft tasks (critical/high first). Critical tasks get the warning container in the dashboard.
4. Write updated `tasks.md`.
5. Render concise interactive plan dashboard.

## Output Rules — Concise + Interactive

- **Always render via `render-ui` skill → `render_ui` tool.** Never substitute plain markdown for the recap/plan.
- **Top view ≤ 12 elements.** Drill-down goes into Accordion / TabSet / Carousel.
- **Numbers in tiles, not paragraphs.** KPI ColumnSet at the top; one line per KPI.
- **Tables over prose.** When listing tasks, decisions, holidays, OOO, use Table or FactSet with width-balanced columns.
- **Badges for status.** `Good` = done/positive, `Warning` = at risk, `Attention` = blocked/critical, `Informative` = neutral.
- **One sentence of follow-up chat after the card.** No re-stating the card content.
- **Branding:** when the rendered surface needs corporate styling (PDF/PPT export), invoke the `cetin-design` skill explicitly. The default chat card remains in the Cowork visual language.

## Adaptive Card Skeleton — Past-Week (concise)

```
AdaptiveCard 1.6
├── TextBlock        "Week N — {start} → {end}"  (Large, Bolder)
├── ColumnSet (4 KPI tiles)
│   ├── Completion %  + ProgressRing
│   ├── Meetings attended
│   ├── Focus hours
│   └── Critical closed
├── TabSet (Default tab: Overview)
│   ├── Overview     → Chart.Donut "Time by category" + Chart.HorizontalBar "Completed vs planned"
│   ├── Decisions    → FactSet (top 3)
│   ├── Unresolved   → FactSet (top 5)
│   └── Completed    → Table (Title | Category | Stakeholder)
└── TextBlock        "Snapshot archived." (isSubtle)
```

## Adaptive Card Skeleton — Next-Week (concise)

```
AdaptiveCard 1.6
├── TextBlock        "Plan — Week N, {start} → {end}"
├── Container (style=attention) if holidays OR OOO present
│   └── FactSet of {date — name} or {person — OOO window}
├── ColumnSet (Mon..Fri week-at-a-glance, conflict cells coloured)
├── Container (style=warning) "Critical this week" — only if any
├── TabSet
│   ├── Priorities by category → FactSet
│   ├── Manager asks → FactSet
│   └── Team topics → Accordion (Planner | 1:1s | Teams | Email)
└── TextBlock        "tasks.md updated." (isSubtle)
```

## Tool Inventory

`TaskCreate`, `TaskUpdate`, `TaskList`, `AskUserQuestion`,
`GetMyDetails`, `GetManagerDetails`, `GetDirectReportsDetails`, `SearchPeople`, `GetUserDetails`,
`ListCalendarView`, `ListEvents`, `GetMeetingTranscript`, `ListMeetingTranscripts`,
`SearchM365`, `ListMessages`, `GetMessage`,
`ListChatMessages`, `ListChats`,
`GetDefaultDrive`, `GetDriveChildren`, `GetDriveItem`, `ReadFileContent`, `CreateFolder`,
`SetupScheduledPrompt`, `GetScheduledPrompts`, `EditScheduledPrompt`,
`QueryGraph`, `CallGraph` (Planner queries, OneDrive content PUT),
`render_ui` — always preceded by invoking the `render-ui` skill.

## Helper Scripts

- `scripts/holidays.py` — public holidays for a country (`CZ`, `SK`, `DE`, `AT`, `PL`, `UK`, `US` built in; extend the dict for more). Exit code 3 = country unsupported → caller asks user.
- `scripts/upload_md.py` — emits a CallGraph PUT envelope for OneDrive uploads.

## Defaults & Edge Cases

| Situation | Behaviour |
|---|---|
| Invoked outside Fri/Mon | `AskUserQuestion`: recap / plan / both |
| `preferences.md` missing | Onboarding flow |
| Manager lookup returns nothing | Skip "Manager priorities" section silently |
| Email TLD ambiguous (`.com`, `.org`) | Ask user for country (multi-select supported list) |
| Country unsupported by `holidays.py` | Ask user to list public holidays manually for this period; offer to add the country permanently |
| Planner unreachable | Skip Planner subsection; one-line note in dashboard |
| Direct report calendar private | Use only `showAs=oof` window, never event titles |
| Schedule already exists at onboarding | `GetScheduledPrompts` → `EditScheduledPrompt` (no duplicates) |
| Output language ≠ English | Render dashboard labels in chosen language; keep task list bilingual if preferred |

## Guardrails

- Never fabricate tasks, decisions, stakeholders, or holidays. If a source returns nothing, say so.
- Never hardcode an organisation, manager, or country in `preferences.md` from skill code — always derive from the runtime user.
- For direct reports' OOO, never reveal private event subjects — only busy/OOO window.
- Never send outbound emails, Teams messages, or any notification on the user's behalf. This skill is read-only towards other people — it only updates the user's own task file and renders dashboards.
- Cap `GetMeetingTranscript` at 5 calls per recap.
- All times stored ISO 8601 with the user's local offset.
