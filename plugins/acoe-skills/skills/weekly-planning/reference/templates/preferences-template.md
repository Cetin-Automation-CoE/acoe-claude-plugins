# Preferences — Weekly Planning

> Auto-managed by the `weekly-planning` skill. Hand-edits honoured on next run.
> All personal references are resolved at runtime and saved here on first onboarding.

## Storage

- folder: `{{FOLDER_PATH}}`   # e.g. /Documents/Cowork/WeeklyPlanning

## Country (drives public holidays)

- country: `{{ISO_CODE_OR_NULL}}`   # CZ, SK, DE, AT, PL, UK, US, or null = skip holidays
- inferred_from: `{{email_tld | user_selection}}`

## Default sections (next-week plan)

- carry_over_tasks: true
- public_holidays_and_ooo: true
- manager_priorities: true
- calendar_overview_and_conflicts: true
- team_topics_planner: {{true_if_user_has_reports}}
- team_topics_1on1_notes: {{true_if_user_has_reports}}
- team_topics_chats: {{true_if_user_has_reports}}
- team_topics_emails: {{true_if_user_has_reports}}

## Schedule

- friday_recap_enabled: {{true|false}}
- monday_plan_enabled: {{true|false}}
- recap_local_time: "12:00"
- plan_local_time: "08:00"

## Manager + reports (cached, refresh on demand)

- manager_upn: `{{LINE_MANAGER_UPN}}`
- manager_display_name: `{{LINE_MANAGER_DISPLAY_NAME}}`
- direct_reports_count: `{{N}}`
- direct_reports_cached_at: `{{ISO_TIMESTAMP}}`

## Output language

- dashboard: `{{en|cs|sk|de|pl|bilingual}}`
- task_list: `{{en|cs|sk|de|pl|bilingual}}`

## Audit

- onboarded_at: `{{ISO_TIMESTAMP}}`
- last_run: `{{ISO_TIMESTAMP}}`
