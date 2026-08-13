---
name: pr-review
description: Use when reviewing a pull request or diff in an ACOE repo, or when the user asks for a code review, PR feedback, or whether a change is ready to merge. Covers our review checklist, required approvals, and migration-safety rules for services touching the payments DB.
---

# ACOE PR Review

## Checklist
1. Does the PR description link a ticket?
2. Are there tests covering every new branch?
3. Any new env vars documented in the runbook?

## Migration safety
Any PR touching `payments.*` tables requires sign-off from #data-platform
and a reversible migration.
