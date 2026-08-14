# Onboarding (first-run flow)

Triggered when `preferences.md` is missing, or user says "reset weekly planning".

## Resolve-at-runtime values (before asking any question)

Run these in parallel via `TaskCreate`:
- `GetMyDetails` — full user record
- `GetManagerDetails` — line manager UPN + display name
- `GetDirectReportsDetails` — list of reports (drives team-topic sections later)

From `GetMyDetails.mail` or `userPrincipalName`, take the TLD after the final dot. Map via `EMAIL_SUFFIX_HINTS` in `scripts/holidays.py`:
- `.cz` → `CZ`, `.sk` → `SK`, `.de` → `DE`, `.at` → `AT`, `.pl` → `PL`, `.co.uk`/`.uk` → `UK`
- `.com`, `.org`, anything else → `None` (must ask)

## Step 0 — Welcome

Post this message to chat verbatim before asking any question:

> **Weekly Planning — let's get you set up**
>
> I'll help you run a simple weekly loop:
>
> - **Every Friday (recap)** — I look back at the past week, mark which of your tasks got done / slipped / dropped, and archive a snapshot.
> - **Every Monday (plan)** — I draft the week ahead: carry-over tasks, your manager's recent asks, public holidays + team OOO, calendar conflicts, and topics from your direct reports (Planner, 1:1s, Teams, email).
>
> Everything lives in **one folder in your OneDrive** — a `tasks.md` you can hand-edit, a `preferences.md` with your settings, and a weekly archive. I never send emails or messages on your behalf; I just keep your task list current and show you a concise dashboard.
>
> Quick setup is **5 short questions** (folder, sections, schedule, country for holidays, language). Then I'll scan your last 14 days of email, Teams and meetings and propose an initial task list for you to confirm.

## Step 1 — Storage folder

`AskUserQuestion` (single-select):
- **OneDrive default — `Documents/Cowork/WeeklyPlanning`** *(Recommended)*
- Different OneDrive subfolder (list children of `/Documents/Cowork/` via `GetDriveChildren`)
- Custom path

`CreateFolder` if missing.

## Step 2 — Default sections in next-week plan

`AskUserQuestion` (multi-select, all checked by default):
- Carry-over tasks from last week
- Public holidays & team OOO
- Manager priorities
- Calendar overview + conflicts
- Team topics — Planner items *(checked only if direct reports exist)*
- Team topics — 1:1 meeting notes *(checked only if direct reports exist)*
- Team topics — Teams chats with direct reports *(checked only if direct reports exist)*
- Team topics — emails from direct reports *(checked only if direct reports exist)*

## Step 3 — Schedule

`AskUserQuestion` (single-select):
- **Friday 12:00 recap + Monday 08:00 plan** *(Recommended)*
- Friday recap only
- Monday plan only
- On-demand (no schedule)

For each scheduled cadence chosen, call `SetupScheduledPrompt`:

```
name="Weekly recap — Friday"
description="Run the weekly-planning skill to generate the past-week recap and update tasks."
frequency="Week"
weekDays=["Friday"]
hours=["12"]
minutes=["0"]
execution_mode="inline"
```

```
name="Weekly plan — Monday"
description="Run the weekly-planning skill to generate the next-week plan and update tasks."
frequency="Week"
weekDays=["Monday"]
hours=["8"]
minutes=["0"]
execution_mode="inline"
```

If matching task already exists, `GetScheduledPrompts` → `EditScheduledPrompt`.

## Step 4 — Country for holidays

If email TLD hint produced an ISO code:
- `AskUserQuestion` (single-select):
  - **{inferred country}** *(detected from your email — Recommended)*
  - Another country (single-select from supported list)
  - Skip — don't show public holidays

Else (ambiguous TLD):
- `AskUserQuestion` (single-select) listing supported countries: CZ, SK, DE, AT, PL, UK, US, plus "Skip".

Save ISO code (or `null`) to `preferences.md`.

## Step 5 — Output language

`AskUserQuestion` (single-select):
- **English** *(Recommended)*
- Local language matching the country (Czech / Slovak / German / Polish)
- Bilingual — EN + local

## Step 6 — Seed tasks.md

Parallel:
- `SearchM365(query="action item OR ask OR please OR deadline OR by Friday", sources=["email","teams"], after=<-14d>)`
- `ListMessages(folder_id="inbox", flagged_only=true, top=25)`
- `ListCalendarView(start=<-14d>, end=<today>, is_organizer=true)`

Build a starter list (max 15), grouped by category, with best-guess priority and stakeholder.

`AskUserQuestion` (multi-select): "Which to keep in `tasks.md`?"

For kept items, render the task lines and `scripts/upload_md.py` to OneDrive.

## Step 7 — Confirm

Single concise message:
> "Setup complete. Files are in `{folder}`. {if scheduled} Recap: Fri 12:00. Plan: Mon 08:00. Call me anytime with 'plan my week' or 'weekly recap'."
