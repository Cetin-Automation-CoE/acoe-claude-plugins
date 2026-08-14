---
name: morning-brief
description: |
  Generates a personalized daily morning brief covering today's calendar, important email,
  Teams activity, Planner tasks, and (for managers) pending items from direct reports.
  Delivers an inline summary in chat with a deep link to the user's Planner kanban.
  Supports the user's preferred language and can be scheduled to run automatically.
  Use when the user says "daily summary", "morning summary", "daily brief", "morning brief",
  "give me my daily", "daily", "morning briefing", "what's on my plate today",
  "start my day", "what did I miss overnight", "brief me on today", or any equivalent in
  their language (e.g. Czech "ranní přehled", "denní souhrn", "co mě dnes čeká";
  German "Tagesüberblick", "Tageszusammenfassung"; Spanish "resumen del día",
  "resumen diario").
  Do NOT use for: full-week planning (use calendar-management), end-of-day wrap-ups
  (use daily-briefing), or meeting-specific prep (use meeting-intel).
cowork:
  category: productivity
  icon: Sparkle
---

# Morning Brief

A personalized daily morning briefing. Pulls from calendar, email, Teams, Planner, and
(for managers) direct-report activity, then delivers an inline summary tailored to the
user's role and preferred language. Includes a deep link to the Planner kanban.

## When NOT to Use
- "What's coming up next week" → calendar-management
- "Wrap up my day" / "what did I get done today" → daily-briefing
- "Prep me for the 2pm" → meeting-intel
- The user wants a long-form report or document — keep this inline only

## Workflow

### Step 1 — First-Run Setup (only if preferences are not yet known)

**Before asking any setup questions**, send a short introduction message so the user
knows what they're configuring. Keep it warm, under 5 lines, plain language — no jargon
or tool names. Translate to the user's profile language if it's not English.

Template (adapt to language; do not paste verbatim every time):

> Hi {first name}! I'm your **Morning Brief** — I'll pull together your day each morning:
> today's calendar, unread email and Teams chats, your Planner tasks (with a link to your
> kanban), and a pulse on what your team needs from you. Let me ask a few quick questions
> to tailor it to you — takes about 20 seconds.

Only show the intro on the very first setup pass in a session. If the user later says
"change my morning brief settings", skip the intro and go straight to the questions.

Then check conversation context and personal instructions for: **role**, **detail level**,
**has direct reports**, **output language**, **schedule**. If any are missing, ask the user once via
`AskUserQuestion` (single card, up to 4 questions — combine schedule into one of them):

1. **Role / focus area** — Manager, Individual contributor, Executive, Project lead (free text via Other)
2. **Detail level** — Quick / Standard / Detailed
3. **Direct reports** — Yes (surface team's pending items) / No
4. **Output language** — English / User's profile language / Other

Then, in a **second** `AskUserQuestion` call, ask about scheduling:

5. **Auto-schedule** — Recommend **"Weekdays at 08:30 (Recommended)"** as the first option. Other options: "Every day at 08:30", "Custom time", "No — run only on demand".

If the user picks any scheduled option, immediately call `SetupScheduledPrompt` per Step 6 — do NOT wait for a second confirmation. If "Custom time", briefly ask which days and time, then set it up. If "No", skip scheduling.

If the user says "use defaults": Standard detail, no team section, language = profile language, schedule = weekdays 08:30.

Acknowledge: "Got it — I'll use these settings and your brief will run {schedule summary}. Say 'change my morning brief settings' anytime."

### Step 2 — Gather Data (in parallel)

Run all of these concurrently via `TaskCreate` + subagents or parallel tool calls:

- **Calendar**: `ListCalendarView` for today (00:00 → 23:59 in user's TZ).
- **Email**: `ListMessages(unread_only=true, received_after=<yesterday 18:00>, top=25)`
  plus `ListMessages(flagged_only=true, top=10)`.
- **Teams**: `ListChats(chat_filter='unread', top=20)`.
- **Planner tasks**: `QueryGraph(path='/me/planner/tasks')`. Filter to tasks where
  `percentComplete < 100` and `dueDateTime` is today, overdue, or within 3 days.
  For each task, capture `id`, `title`, `dueDateTime`, `percentComplete`, `planId`, `bucketId`.
- **Plan metadata**: for each unique `planId` in the task list, call
  `QueryGraph(path='/planner/plans/{planId}')` in parallel to get the plan title.
  Construct the kanban link as `https://tasks.office.com/{tenant}/Home/PlanViews/{planId}`
  using the user's tenant (extract from their UPN domain).
- **Direct reports** (only if has_reports = yes): for each report from user context,
  `SearchM365(from_user=<email>, sources=['email','teams'], after=<yesterday>, response_length='short')`
  in parallel. Surface pending asks, blockers, or @mentions.

Run lookups in parallel — never sequentially. If any source fails, note the gap in
plain language and keep going.

### Step 3 — Compose the Brief

Structure depends on detail level:

**Quick** (≤10 lines):
- Headline: "{N} meetings, {N} unread, {N} tasks due"
- Today's meetings: time + title (use context-link aliases)
- Top 3 things needing attention (email/chat/task)
- Planner link: "[Open your board](https://tasks.office.com/...)"

**Standard** (default):
- **Today's schedule** — accepted events with times and titles. Flag conflicts and
  back-to-back stretches.
- **Tasks** — Planner items due today or overdue, with % complete. Show each as
  "{title} — due {date}, {pct}%". One line per task.
- **Needs your attention** — unread/flagged messages and unread Teams chats,
  ranked by sender importance and topic urgency.
- **Team pulse** (only if has_reports = yes) — pending items, blockers, or @mentions
  from direct reports.
- **Your kanban**: single link line — "Open your Planner board: {url}".

**Detailed**: same as Standard plus a 1-2 sentence rationale for each prioritization
and explicit suggested actions ("Reply to X by 10:00", "Mark task Y complete — it's done").

### Step 4 — Language

Render the entire brief in the user's chosen output language. Section headers,
narrative, and labels all translate. Keep proper nouns (names, task titles, plan
names) verbatim. Context-link aliases (`[evt_1]`, `[msg_3]`) stay in brackets.

### Step 5 — Updating Tasks (only if user asks)

If the user replies with "mark X done", "close task Y", "I finished Z":
1. Identify the matching task from the brief (use task title fuzzy match)
2. Confirm: "Marking '{title}' as complete?"
3. After confirmation, PATCH the task:
   `CallGraph(method='PATCH', path='/planner/tasks/{id}', body={'percentComplete': 100})`
   with the required `If-Match` header — first GET the task to capture `@odata.etag`.
4. Confirm: "Done — '{title}' is marked complete in {plan name}."

For status changes other than complete: `percentComplete: 50` for in-progress, `0` for not started.

### Step 6 — Scheduling

Triggered automatically from the Step 1 setup question, or whenever the user later says
"schedule this", "every morning at 8:30", "send to Teams daily":

- `SetupScheduledPrompt` with `frequency: "Week"` + `weekDays: ["Monday","Tuesday","Wednesday","Thursday","Friday"]` for the recommended weekdays default, or `"Day"` for everyday.
- `hours` and `minutes` from the request (default 08:30).
- `execution_mode: "inline"` so saved preferences persist.
- Name: "Morning brief".
- Description (self-contained): "Generate the user's morning brief using their saved preferences from memory. Cover today's calendar, unread email, unread Teams chats, and team pulse for direct reports. Deliver the brief inline in this Cowork conversation so the user can interact with it (ask follow-ups, decline conflicts, draft replies). Do NOT post it to Teams."

Confirm: "Done — your morning brief will run weekdays at 08:30 and appear right here in Cowork so you can act on it directly."

## Guardrails

- **Never fabricate**: if a data source returns nothing, say so plainly — never invent tasks, emails, or meetings.
- **Calendar density**: count only `accepted` events when claiming "busy" or "back-to-back".
- **Planner failures**: if `/me/planner/tasks` returns 4xx or empty, skip the Tasks section gracefully — don't block the rest of the brief.
- **Privacy on scheduled runs**: when auto-posting to Teams, prefer subject lines and senders over full body excerpts.
- **Task updates need confirmation**: never PATCH a Planner task without the user's explicit go-ahead — even if the user says "mark them all done", echo the list first.
- **One setup ask per session**: don't re-ask preferences mid-session.
- **Tenant resolution**: extract tenant from user's UPN domain (e.g. `cetin.cz` → `cetin.cz`) for the kanban URL. If unsure, use the generic `https://tasks.office.com` and let the user navigate.

## Examples

**"Daily summary"** (first run)
→ Ask 4 setup questions → parallel data fetch → Standard brief in English with kanban link

**"Ranní přehled"** (Czech, preferences saved)
→ Skip setup → parallel data fetch → brief in Czech

**"Mark the budget review task done"** (after brief shown)
→ Identify task → confirm → PATCH percentComplete=100 → confirm

**"Send this every weekday at 8:30 to Teams"**
→ `SetupScheduledPrompt` with Week / Mon-Fri / 08:30 → confirm
