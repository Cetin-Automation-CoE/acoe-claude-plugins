# Past-Week Recap — Detailed Flow

## Inputs

- `tasks.md` from OneDrive (`ReadFileContent`)
- `preferences.md` for default sections + language
- ISO week start/end (Mon 00:00 → Sun 23:59:59 Europe/Prague)

## Step 1 — Load planned tasks

Parse `tasks.md`. Filter to items where `status` is `planned` or `in-progress` AND (`due` falls in the past ISO week OR the task has no due date but was added in the past 14 days).

## Step 2 — Auto-detect signals (parallel)

Run these in parallel via `TaskCreate` to keep latency low:

| Signal | Tool call | What to extract |
|---|---|---|
| Meetings attended | `ListCalendarView(start, end)` + filter `responseStatus.response in {organizer, accepted}` and `isCancelled=false` | event subject, duration, attendees, category guess |
| Decisions | `GetMeetingTranscript` for up to 5 of the longest/most-attended events that have transcripts (`ListMeetingTranscripts` first) | bullet of decisions per meeting |
| Outbound emails | `SearchM365(sources=["email"], from_user=user, after=monday)` | subject lines matching task title keywords |
| Outbound Teams | `ListChatMessages(person=stakeholder, since=monday)` for tasks with `who:` | last user message that references the deliverable |
| Planner status | `CallGraph` GET `/me/planner/tasks?$filter=assignments/* and percentComplete eq 100 and completedDateTime ge {monday}` | completed Planner items; skip on 404/403 |
| Unresolved | `ListMessages(unread_only=false, received_after=monday-7, flagged_only=true, top=25)` AND `SearchM365(sources=["email","teams"], query="?")` | top 5 threads with no outbound reply in 48h |

## Step 3 — Propose status per task

Build a list `[{task, proposed_status, evidence}]`. Heuristics:
- Outbound email matching task title → propose `done`
- Planner item completed → `done`
- Meeting happened + no outbound deliverable → `in-progress`
- No signal at all + due date passed → ask (likely `dropped`)

Batch into a single `AskUserQuestion` call (max 4 questions per call — group remaining tasks). Each question shows the task title, evidence snippet, and 3 options: Done / In-progress / Dropped. If >12 tasks, summarise low-confidence ones in one "bulk-confirm" question.

## Step 4 — Update tasks.md

Apply confirmed statuses. For tasks marked `in-progress`, change to `carried-over` so the next-week flow picks them up automatically.

Write to local `working/weekly-planning/tasks.md` then `python scripts/upload_md.py working/weekly-planning/tasks.md "/Documents/Cowork/WeeklyPlanning/tasks.md"`.

## Step 5 — Metrics

```python
completion_rate = done_count / planned_count if planned_count else 0
time_by_category = sum_minutes_per_cat from attended meetings
focus_hours = total_calendar_window - busy_minutes (treat any free slot >= 60 min as focus)
critical_closed = count tasks with priority=critical and status=done
```

For untagged meetings, infer category via subject keywords:
- "1:1" / "1on1" / direct report name → `#1on1`
- "steering" / "board" / "council" → `#governance`
- project name from transformation portfolio → `#transformation`
- "admin" / "expense" / "HR" → `#admin`
- fallback → `#other`

## Step 6 — Render dashboard

Invoke `render-ui` skill, then call `render_ui`.

Card body order:
1. **Header** — TextBlock "Week {ISO} recap — {Mon date} → {Sun date}", Large, Bolder
2. **KPI ColumnSet** (4 columns):
   - Completion rate — TextBlock big number + ProgressRing
   - Meetings attended — count + average duration as small text
   - Focus hours — count + delta vs prior week if archive exists
   - Critical tasks closed — count
3. **Charts ColumnSet** (2 columns):
   - Chart.Donut — time by category (legend = cat, value = minutes)
   - Chart.HorizontalBar — completed vs planned per category (grouped)
4. **FactSet — Top decisions** (max 3, sourced from transcripts)
5. **FactSet — Top unresolved items** (max 5, with stakeholder)
6. **Table — Completed tasks** (Title | Category | Stakeholder)
7. **Footer** — TextBlock "Snapshot saved to /Documents/Cowork/WeeklyPlanning/archive/{YYYY-WW}.md", isSubtle=true

## Step 7 — Archive snapshot

Render the same data to `archive/{YYYY-WW}.md`:

```
# Week {ISO} — {Mon date} → {Sun date}

## KPIs
- Completion rate: {x}%
- Meetings attended: {n} ({hours}h)
- Focus hours: {h}
- Critical tasks closed: {n}

## Time by category
- #transformation: {h}h
- #team: {h}h
- ...

## Decisions
- ...

## Completed
- ...

## Unresolved
- ...
```

Upload via `scripts/upload_md.py`.

## Edge cases

- **No transcripts available** — omit Decisions FactSet (do not invent decisions).
- **No planned tasks** — render a "first recap" card with a note that next week will have meaningful comparisons.
- **Calendar empty** — note "no meetings recorded" and skip time-by-category chart.
- **Archive folder missing** — create via `CreateFolder` under the chosen folder.
