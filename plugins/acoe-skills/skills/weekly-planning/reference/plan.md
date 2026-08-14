# Next-Week Plan — Detailed Flow

## Inputs

- `tasks.md` (already updated by the recap if both flows ran)
- `preferences.md` — default sections, language, country
- Direct reports list from system context (13 names)
- Manager: `kukura.peter@cetin.cz`

Target window: Monday 00:00 → Sunday 23:59:59 of the upcoming ISO week, Europe/Prague.

## Step 1 — Confirm sections for this run

Read `preferences.md`. Show the user's defaults and offer one `AskUserQuestion` (multi-select) to add/remove sections:

- Carry-over tasks
- Public holidays & vacations
- Manager priorities
- Calendar overview + conflicts
- Team topics — Planner items
- Team topics — 1:1 meeting notes
- Team topics — Teams chats with direct reports
- Team topics — emails from direct reports

If invoked from a scheduled run, skip this question and use the defaults from `preferences.md`.

## Step 2 — Gather data (parallel `TaskCreate`)

### Carry-over tasks
Filter `tasks.md` for `status in {planned, in-progress, carried-over}` and `due` either missing or in the upcoming week.

### Public holidays & vacations
```
python scripts/holidays.py --country <ISO from preferences.md> --start <Mon> --end <Sun>
```
- Exit 0 → JSON list of `{date, name, country}`.
- Exit 3 → country not supported. Fall back to `AskUserQuestion` ("Add holidays for this week?") and offer to add the country permanently.
- `country: null` in preferences → skip this section entirely.

Plus team OOO:
- `ListCalendarView(start=Mon, end=Sun, show_as="oof")` for the user.
- For each direct report: `QueryGraph` path `/users/{upn}/calendarView` with `$filter=showAs eq 'oof'` and `startDateTime`/`endDateTime` query params. Skip silently on 403.
- Render OOO as `{displayName} — {start} → {end}`, never the event title.

### Manager priorities
Read `manager_upn` from `preferences.md`.
```
SearchM365(
  sources=["email","teams"],
  from_user=<manager_upn>,
  after=<7 days ago>,
  response_length="medium",
)
```
Extract any ask, deadline, or "please" sentences. Group into a short bullet list. If `manager_upn` is empty (no manager on file), skip this section.

### Calendar overview + conflicts
```
ListCalendarView(start=Mon00:00, end=Sun23:59, select="subject,start,end,attendees,showAs,isAllDay,responseStatus")
```
Identify:
- Overlapping events (start < other.end AND end > other.start, both accepted)
- Back-to-back stretches >3 hours with no break
- Days with >6h of meetings (over-booked flag)

### Team topics — Planner
```
CallGraph(method="GET", path="/me/planner/tasks", query_params={"$filter":"percentComplete lt 100"})
```
Then filter to tasks assigned to a direct-report user GUID. If `403`/`404`, skip and add note "Planner not available."

### Team topics — 1:1 notes
For each direct report, find last week's 1:1 event:
```
ListCalendarView(start=<last Mon>, end=<last Sun>, subject="1:1") + filter by attendee email
```
For events with a transcript, call `ListMeetingTranscripts` then `GetMeetingTranscript` (limit total transcripts pulled to 5 across the team).

### Team topics — Teams chats
```
ListChats(filter_member=<report-email>, top=3) per report (parallel)
ListChatMessages(chat_id, since=<7 days ago>, top=20) for each
```
Find messages from the report that contain a question mark or "?" or "could you" / "můžeš".

### Team topics — emails from reports
```
SearchM365(sources=["email"], from_user=<report-email>, after=<7 days ago>)
```
Or batch: `ListMessages(received_after=<7 days ago>, top=50)` and group by `from`.

## Step 3 — Build draft tasks

Compose the proposed week:
- Carry-over tasks at the top (these are real commitments)
- Manager asks become new tasks at `priority:high` minimum (`critical` if the manager used words like "urgent", "asap", "by Monday")
- Conflict-resolution actions (e.g., "decline X to protect Y") added as `#admin` tasks
- Team-topic asks become tasks tagged `#team` or `#1on1` with the report as `who:`

Tasks with `priority:critical` are rendered inside a `style=warning` container on the plan dashboard (see Step 5). No outbound emails or notifications are sent — visibility only.

## Step 4 — Write tasks.md

Merge: keep done/dropped items in `tasks.md` (under an "Archive" section if it grows long; or move to `archive/{YYYY-WW}.md`). Append new tasks. Upload via `scripts/upload_md.py`.

## Step 5 — Render plan dashboard

Invoke `render-ui` skill, then `render_ui`.

Body order:
1. **Header** — TextBlock "Plan — Week {ISO}, {Mon date} → {Sun date}"
2. **Holiday/OOO banner** — Container with `style=attention` if list non-empty:
   - TextBlock "🇨🇿 Holiday: {date} — {name}" per Czech holiday
   - TextBlock "OOO: {name} — {start} to {end}" per direct report OOO
   - If list empty: skip the container entirely (do not say "no holidays")
3. **Week-at-a-glance** — ColumnSet of 5 Columns (Mon–Fri):
   - Each Column: TextBlock header with day + date, then stacked TextBlocks per event (start–end + short subject)
   - Use color=attention on conflict cells
4. **Critical callout** — Container `style=warning` with TextBlock weight=Bolder listing critical tasks
5. **Priorities by category** — FactSet, one fact per category (`#transformation: 3 tasks`, etc.) with click-through expander (Accordion)
6. **Team topics** — Accordion with one AccordionPage per source (Planner / 1:1 notes / Teams / Email). Each page renders 3–5 bullets max.
7. **Manager asks** — FactSet (max 5)
8. **Footer** — "Updated `/Documents/Cowork/WeeklyPlanning/tasks.md`."

## Step 6 — Confirm with user

End message:
> "Your week is planned. {N} carry-overs, {M} new tasks, {K} critical. Holidays this week: {list or 'none'}. Tap any task in the file to edit details."
