---
name: rfp-evaluation
description: |
  Evaluates SaaS vendor proposals for CETIN (telco) procurement. Builds a weighted
  scoring matrix, summarises vendor responses, produces an HTML dashboard, and drafts
  a shortlist memo. Always covers the four mandatory CETIN dimensions: Security &
  GDPR/data residency (EU), BSS/OSS & telco integration, SLA/support/operations,
  and Commercials & vendor viability.

  Use when the user asks to "evaluate vendor proposals", "score this RFP",
  "compare SaaS vendors", "build an RFP scorecard", "shortlist these vendors",
  "review the tender responses", "do a vendor evaluation", "compare proposals
  for [SaaS tool]", "which vendor should we pick", "summarise vendor responses",
  "rank the bids", "procurement evaluation", "sourcing evaluation",
  "evaluation matrix for [SaaS]", or any CETIN telco SaaS sourcing decision.

  Do NOT use for: drafting a new RFP document from scratch (no RFP-writing
  output is produced — ask the user to switch to a drafting workflow if needed),
  internal project prioritisation, non-SaaS procurement (hardware, professional
  services), or contract redlining.
cowork:
  category: analysis
  icon: ClipboardTaskListLtr
---

# RFP Evaluation (CETIN SaaS)

Evaluates SaaS vendor proposals against CETIN's mandatory dimensions and produces a
scorecard, vendor summary, HTML dashboard, and shortlist memo.

## When NOT to Use
- Drafting a new RFP from scratch — this skill evaluates responses, it does not write the RFP itself
- Hardware, network equipment, or professional-services sourcing (different evaluation framework)
- Single-vendor due diligence with no comparison (use `deep-research` instead)
- Contract negotiation, redlining, or legal review

## Inputs

Vendor proposals and RFP requirements are expected in a working folder.

**Always ask the user at the start of a new task: "Which folder are the proposals in?"**
Default to `input/` if they say "the usual" or do not specify. Accept any subfolder
under `input/` (e.g. `input/proposals/`, `input/rfp-crm-2026/`).

Expected file types: PDF, DOCX, XLSX, PPTX vendor responses; optional `requirements.xlsx`
or RFP document defining the criteria and weights.

If the folder is empty or unreadable, tell the user plainly and stop — do not invent vendor data.

## Mandatory Evaluation Dimensions

Every scorecard MUST include all four. Default weights shown — confirm with user before applying:

| Dimension | Default weight | Sub-criteria (examples) |
|-----------|----------------|-------------------------|
| **Security & GDPR / EU data residency** | 30% | ISO 27001, SOC 2 Type II, GDPR DPA, EU-only hosting option, encryption at rest/in transit, pen-test cadence, breach notification SLA, sub-processor list |
| **BSS/OSS & Telco Integration** | 25% | REST/GraphQL APIs, webhook support, pre-built BSS/OSS connectors, identity federation (SAML/OIDC), data-pipeline patterns, on-prem connector if needed, telco reference architectures |
| **SLA, Support & Operations** | 20% | Uptime % (target ≥99.9), RTO/RPO, multi-region failover, 24x7 support, incident response SLA, status page, EU-language support, roadmap transparency |
| **Commercials & Vendor Viability** | 25% | 3–5y TCO, pricing model (per-user, consumption, tiered), exit/data-portability clause, contract flexibility, vendor financials, EU/telco references, R&D investment |

Allow the user to add a 5th dimension (e.g. "AI/ML capabilities", "Sustainability") with weight redistribution, but never drop one of the four.

## Workflow

1. **Confirm working folder.** Ask which folder under `input/` holds the proposals. List what you find (filenames + sizes) before proceeding.
2. **Identify vendors.** From filenames or document headers, list the vendors found and confirm with the user.
3. **Extract requirements.** If `requirements.xlsx` or an RFP document is present, parse weighted criteria from it. Otherwise propose the default dimensions/weights above and ask the user to confirm or adjust.
4. **Read each proposal** with the `pdf` or `docx` skill (delegate via subagent if there are 3+ documents — run in parallel).
5. **Score each vendor** on every sub-criterion (1–5 scale). For each score, capture a one-line evidence quote with page/section reference. Mark gaps where the proposal is silent — never guess.
6. **Build the Excel scorecard** via the `xlsx` skill: one sheet per vendor + a summary sheet with weighted totals, ranking, and a heatmap.
7. **Build the HTML dashboard** via `cetin-design` branding: weighted totals, dimension breakdowns (radar or bar), top strengths/gaps per vendor, recommended shortlist. Save as `output/rfp-dashboard.html`.
8. **Draft the shortlist memo** via the `docx` skill using CETIN branding: 1-page executive memo — recommendation, rationale (top 3 reasons), risks, next steps, signatories (CETIN Head of Transformation Office + IT Strategy & PMO Director).
9. **Final summary in chat:** ranking, top recommendation, key risks, and links to all outputs.

## Outputs (always in `output/`)

| File | Purpose |
|------|---------|
| `output/rfp-scorecard.xlsx` | Weighted scoring matrix, per-vendor sheets, summary heatmap |
| `output/vendor-summary.md` (inline) | Side-by-side response comparison + gap analysis |
| `output/rfp-dashboard.html` | CETIN-branded executive dashboard |
| `output/rfp-shortlist-memo.docx` | 1-page exec memo with recommendation |

All four are produced by default. The user can ask for a subset.

## Tools to Use

- `xlsx` skill — for the scorecard
- `docx` skill — for the memo
- `cetin-design` — branding for HTML dashboard and Word memo (CETIN Blue + Red, Avenir/Arial)
- `pdf` / `docx` — to read vendor proposals
- `deep-research` agent — for vendor viability checks (financials, references, recent incidents)
- `render_ui` — for inline preview of ranking before generating the dashboard

## Guardrails

- **Never fabricate vendor data.** If a proposal does not address a criterion, score it as gap and flag it — do not infer.
- **Cite evidence.** Every score must have a quoted snippet + location.
- **Confirm weights before scoring.** The user owns the weighting decision — present defaults, get confirmation.
- **Numeric accuracy.** All weighted totals are computed in the xlsx skill, never by hand.
- **No vendor name in the file path** unless the user asks — keep filenames generic so memos can be reused.
- **Disclose when data is missing** (e.g. vendor did not respond to a section) — do not assume "no answer = fail" without telling the user.
- **Do not recommend a winner if the top two are within 5%.** Flag as "too close to call — request clarifications" and list the open questions.

## Quick Examples

| User says | Skill does |
|-----------|------------|
| "Evaluate the CRM vendor responses in input/crm-rfp" | Confirm folder → identify vendors → confirm weights → score → produce all 4 outputs |
| "Just give me the scorecard, skip the memo" | Same flow, only produce `rfp-scorecard.xlsx` and `vendor-summary.md` |
| "Compare these 3 ITSM SaaS proposals" | Same flow with auto-detected ITSM-relevant sub-criteria |
| "Which vendor wins?" (mid-conversation) | Use already-built scorecard; produce the dashboard + memo only |
