---
name: process-intake
description: Turn any transcript in which a process is described into an as-is process analysis, an importable BPMN 2.0 model, a branded HTML one-pager, and, where the process ends in stored data, a DBML data model with an ER diagram. Works on any process from any organisation — a recorded walkthrough, an interview, a workshop, a handover session, a support call, or written notes; the CETIN Automation CoE material (brand, org routing, stack) applies when the intake is for CETIN, which is the default when nothing says otherwise. Use whenever someone shares a meeting recording, Teams/.vtt/.srt/.docx transcript, or notes in which a person explains how a manual or recurring process is performed — a monthly report, a month-end close, a reconciliation, an invoice or claims workflow, an onboarding, an approval chain — and wants it analysed, mapped, documented, diagrammed, written up as BPMN, assessed for automation, or handed to an RPA team. Trigger it on vague asks too, like analyse this process, map this out, can we automate this, or make me a BPMN.
---

# Process intake: from process transcript to automation-ready specification

Someone has submitted a transcript in which a process is described — a recorded
walkthrough, an interview, a workshop, a handover session, or written notes. Your task is
to turn it into the artefacts an automation project can actually use:

1. **`<slug>_analysis.md`** — the as-is process, the automation assessment, the open
   decisions, the risks, and a timestamp index back into the recording
2. **`<slug>_process.bpmn`** — a BPMN 2.0 model that opens as a drawn diagram in Camunda
   Modeler or bpmn.io, plus `<slug>_process.svg` rendered from it
3. **`<slug>_visual.html`** — a CETIN-branded one-pager for the stakeholders who will
   never open the other two
4. **`<slug>_model.dbml`** + `<slug>_model.svg` — *when the process ends in stored data* —
   the target data model and its ER diagram

Produce the first three unless the person explicitly asks for fewer. They serve different
readers: the specification, the model, and the thing that gets shown in a meeting. The
fourth is **not** default — decide it deliberately against the test in step 7b, and skip it
with a one-line reason when it doesn't apply.

A recommendation is only useful if the receiving team can build it. When the intake is for
the **CETIN Automation CoE** — the default when nothing says otherwise — read
`references/acoe-stack.md` before writing the assessment: it covers what the CoE actually
has (RPA, Power Platform, Azure, Azure SQL / SQL Server / PostgreSQL, Power BI, PowerShell,
Python, TypeScript), the four target shapes most intakes resolve to, and the licensing and
lead-time facts worth flagging. For any other organisation, assess against the stack *they*
have — and if the transcript doesn't say what that is, that's a key question (step 2b), not
a licence to assume.

## What makes this hard, and where the value is

The mechanical steps in these processes are easy to write down. The value is in three
things that are easy to miss:

- **The parameters.** A row limit, a selection variant, a date convention, a formula that
  reformats a key before a lookup. These get summarised away and then cost a sprint to
  rediscover.
- **The exceptions.** Process owners describe the happy path when asked and mention the
  exceptions in asides. The asides are the reason the job is still manual.
- **The definition nobody states.** Most recurring outputs carry a semantic the author
  explains in person and no consumer has ever heard. See §2 of the analysis structure.

Assume the person demonstrating knows things they will not think to say, and that your job
is partly to notice what they assumed you already understood.

---

## Method

### 1. Extract the transcript

```bash
python scripts/extract_transcript.py <input.docx|.vtt|.srt|.txt> -o work/
```

Produces `work/transcript.txt` (line-numbered, one block per speaker turn),
`work/transcript.json` (same content, programmatically addressable), and `work/summary.txt`.

Work against `transcript.txt` from here — you will grep it many times, and every hit gives
you a timestamp for free. Reading a `.docx` directly gives you neither line numbers nor a
reliable turn structure.

### 2. Orient before reading in detail

Read `work/summary.txt` first. The word-count-per-speaker table identifies the process
owner immediately — they typically have 5–10× the words of anyone else. The 5-minute turn
index tells you roughly where the walkthrough starts, since the first several minutes are
usually scoping and negotiation rather than process content.

**Check coverage before you commit to anything.** The summary reports words per minute and
flags silent gaps of two minutes or more. Teams transcription drops out during screen-share,
and exports get truncated — so a file can look complete, open normally, and contain only the
greeting and the goodbye. A walkthrough runs at roughly 100–150 words per minute; anything
under ~40 means most of the meeting is missing.

If a gap covers the demonstration, **stop and say so**. There is no analysis to write, and
producing a plausible-looking one from the fragments is the worst possible outcome: it looks
like a deliverable and it is invented. Report what the fragments do establish (participants,
scope, actions agreed), name the gap with its timestamps, and ask for the full transcript or
the recording. That is the honest and far more useful answer.

### 2b. Ask the key questions before you build

Some facts change what you produce, and guessing them wrong wastes the whole pass. After
orienting — and again after the full read if new gaps surfaced — check whether you actually
know:

- **Who the intake is for.** Which organisation, and which team will build the automation?
  This decides the stack the assessment is written against and whether the CETIN references
  apply at all.
- **Which deliverables are wanted.** The default set is analysis + BPMN + one-pager; a data
  model only per the step 7b test. If the ask was vague ("can we automate this?"), confirm
  the set rather than producing everything.
- **Whether the process ends in stored data** — when the transcript leaves the 7b test
  genuinely undecidable.
- **What a load-bearing ambiguity actually means.** A system name you can't decode, a figure
  the whole assessment hinges on, an acronym with two plausible expansions, who the process
  owner actually is.
- **Coverage.** If step 2 flagged a gap or a truncation, that question outranks all others.

If any of these are unclear, **ask now — once, batched, and concretely** (a handful of
questions at most, each with the options you see). Do not drip-feed questions one per turn,
and do not ask what the transcript already answers — re-grep first. Minor uncertainties
that don't change the shape of the deliverables are not questions: mark them `**(verify)**`
in the analysis and keep going. If the user is unavailable, state the assumption you're
proceeding on in the analysis header and continue.

### 3. Read the whole transcript

Not a sample. Machine transcripts bury critical statements in the middle of rambling
turns, and the structural traps — a double-counted value, a definition stated once — will
not survive skimming. For a 90-minute recording this is a few thousand lines; read it.

While reading, note against line numbers:

- every system, transaction, report or file touched, **and its parameters**
- every point where the owner says "then I look it up by hand" or "I have to check"
- every artefact that lives outside a system: a personal register, a hand-kept codelist,
  a mapping spreadsheet on a shared drive
- every fallback ladder ("if it's not there, I run it again as at…")
- every moment a consumer says they don't use part of the output — that is free scope
  reduction
- every figure, and how confidently it was spoken

For CETIN recordings, read `references/cetin-context.md` at this point. It covers decoding
SAP transaction codes out of Czech phonetic garble, how to tell a hesitated number from a
large one, who is usually in the room, and the structural traps that have appeared in more
than one intake.

### 4. Classify each step

- **Green** — deterministic. Extraction, joins, lookups, arithmetic.
- **Amber** — the logic exists but only in someone's judgement. Name the missing decision.
- **Red** — blocked or genuinely manual: missing authorization, no key to join on,
  case-by-case negotiation, judgement about a past that was never recorded.

The honest finding is usually that most of the *elapsed time* is green while most of the
*meaning* is amber. Say that — it tells the project where to spend specification effort.

### 5. Write the analysis

Follow `references/analysis-structure.md`. It gives the section-by-section template and
explains why each section exists.

Timestamp discipline, which the whole document depends on:

- A marker points at the **start of the speaker turn** containing the topic. Inside a long
  monologue the exact moment can be a minute or two later — state this caveat in the header.
- Use `~` for a position inferred from content position rather than a turn marker (`~[11:38]`).
- Mark every phonetic reconstruction `**(verify)**`.

### 6. Build the BPMN

Write a `process.json` spec, then:

```bash
python scripts/build_bpmn.py work/process.json --check      # validate first
python scripts/build_bpmn.py work/process.json -o <slug>_process.bpmn
```

The schema and modelling conventions are in `references/bpmn-spec.md`; a full worked
example is `references/example-process.json`. The two conventions that matter most: keep
the happy path on `row: 0` and drop exceptions to `row: 1`, and give every task a `ts` so a
reviewer can jump from a box to the moment in the recording that justifies it.

**Render-check it.** A file that parses is not necessarily a file that draws. If Node is
available, import it with `bpmn-js` headlessly and confirm zero warnings; the script's
built-in parse-back check catches malformed XML but not a broken diagram. Then export the
SVG for people who won't install a modeller.

**Give every exported SVG an explicit white background.** bpmn-js exports transparent SVGs,
and a transparent diagram viewed in a dark-mode Markdown preview or browser renders as
black-on-black. After exporting, insert
`<rect x="…" y="…" width="…" height="…" fill="#ffffff"/>` matching the `viewBox` as the
first child of the `<svg>` element (or add `style="background:#ffffff"` to the root tag).
The same rule applies to any SVG you ship — the ER diagram script already emits
`bgcolor="white"`, so check rather than re-fix.

### 7. Build the visual

Copy `assets/visual_template.html` and replace the placeholders. The CSS is complete,
already carries the CETIN brand tokens (CETIN Blue `#300091`, Avenir Next LT Pro → Arial),
and renders on a **white page by default** — dark mode exists but is opt-in via
`<html data-theme="dark">`, only when someone asks for it. You should not need to touch the
CSS.

Branding applies: an automation intake is work output. For a CETIN intake,
`references/cetin-brand.md` has the palette, the type stack, the logo files in
`assets/logos/`, and the reasoning behind the RAG scale (green and amber sit deliberately
outside the brand palette, because CETIN Blue and Red carry brand meaning, not status
meaning). If the `cetin-design` skill from the ACoE plugin is installed alongside this one,
prefer it as the source of truth. For a **non-CETIN** intake, keep the template's structure
but swap the brand tokens and logo for the client organisation's — or, lacking those, drop
the logo and use the neutral ink/rule colours; never ship another organisation's report
under CETIN branding. Skip branding entirely only if the user asks for plain output.

The one part that carries real information is the timeline in section 1: set each
segment's `flex` to its length **in seconds**, so the bar is genuinely proportional. That
is what makes it evidence rather than decoration — it shows at a glance that forty minutes
went on one topic and ninety seconds on the step that turns out to matter most.

Keep the RAG colours consistent with the analysis. Exactly one step gets the `hero` class.

### 7b. Decide whether a data model is warranted — then draft it

Do not produce the DBML/ER diagram by reflex. Produce it when **at least one** of these
holds:

- the to-be solution persists data in a new or changed store (a report that should become a
  table, a register that should become a database)
- a hand-kept artefact — a personal spreadsheet, a mapping file on a shared drive — is doing
  a database's job and the recommendation moves it into one
- the owner or a consumer asked for history, audit, or "being able to look back"

Skip it — with a one-line reason in the analysis — when none holds: a process that only
moves documents, sends notifications, or writes into an existing system's existing tables
does not need a target data model, and shipping one anyway buries the deliverables that
matter. If the transcript leaves the test genuinely undecidable, that was a step 2b
question; if it's still open, say the model is conditional and on what.

When it is warranted, draft it in DBML and render it:

```bash
python scripts/build_dbml_diagram.py work/<slug>_model.dbml --check
python scripts/build_dbml_diagram.py work/<slug>_model.dbml
```

`references/dbml-data-model.md` covers when a model is warranted, the modelling decisions
that matter in intake work (grain, historisation, staging for external files, recording the
source system so a double-count stays visible), and a sketch to adapt. Ship the `.dbml` and
the rendered `.svg` — the file is what engineers work from, the picture is what gets
discussed. The `.dbml` also pastes straight into dbdiagram.io.

### 7c. Name the owners

An analysis that ends without naming who has to act is a document; one that names them is a
demand. For a CETIN intake, use `references/cetin-organisation.md` to identify the
accountable department head, the delivery tribe that owns each system involved, and who
grants the access that is blocking. A reporting intake typically crosses four owners (SAP,
IT Platforms, DWH/BI, IT Office) — discovering that one owner at a time is what makes these
projects slow. For any other organisation, name the owners the transcript itself names, and
list the ownership questions the transcript leaves open (who owns each system, who grants
access) as explicit open items rather than guessing.

### 8. Verify — do not skip this

**Spawn a fresh subagent to check your document against the transcript.** This step
routinely finds real errors, and it only works if the checker is independent: you already
believe your own reconstruction, so you will read past your own mistakes.

Give the checker the transcript path and the document path, and ask it to report **only
errors, with line numbers and the quoted source text that proves each one**. Have it check:

- every explicit timestamp — does the claimed topic actually appear in that turn or the
  next one? Off-by-one-turn errors are the single most common defect.
- every figure, against how it was spoken
- the substantive claims: is each one actually supported?
- names, at the confidence level you stated them
- anywhere you wrote that something was *agreed* when the transcript shows only a stated
  preference followed by deferral

Tell it explicitly to report only errors and not to reassure you about what is correct.

### 9. Propagate corrections to every artefact

Corrections found in step 8 apply to the Markdown, the BPMN labels, the HTML **and** the
data model. It is easy to fix the document and ship a diagram with the old timestamps —
check each file. If you generated the BPMN from `process.json`, fix the spec and regenerate
rather than editing the XML.

### 10. Deliver

Send all files together. Lead with the visual, since it's the one most people will open.
Say in one or two sentences what the analysis found that goes beyond documentation — the
structural defect, the unresolved decision, the thing nobody had noticed. Note the items
marked `**(verify)**` that need a quick confirmation from the process owner.

---

## Judgement calls worth getting right

**Report what was said, not what would be sensible.** If the process has a round trip
through Excel because a row limit forces it, that round trip is a step. Tidying it away in
the model hides exactly the thing automation removes.

**Distinguish a preference from a decision.** "Agreed direction: X" written up from one
person saying X and then deferring to the room will be read back in a steering meeting as
consensus that never existed. Write "no agreement was reached" when that is what happened.

**Don't invent precision.** A defensible qualitative statement beats a fabricated
percentage. If the recording doesn't support a number, say what it does support.

**Name the single-point-of-knowledge risk explicitly.** These processes almost always live
entirely with one person plus two or three undocumented files on a shared drive. That is
usually the strongest argument for the project regardless of the efficiency case, and the
process owner will rarely raise it about themselves.

**Look downstream.** What consumers do by hand after they receive the output is often
automatable in the same pass, and is routinely left out of scope because nobody asked.

---

## Files in this skill

| Path | Read / run it when |
|---|---|
| `scripts/extract_transcript.py` | first, on the raw recording transcript |
| `scripts/build_bpmn.py` | to turn a `process.json` spec into a laid-out BPMN 2.0 file |
| `scripts/build_dbml_diagram.py` | to validate a `.dbml` model and render its ER diagram |
| `references/cetin-context.md` | while reconstructing a CETIN / SAP / Czech-language process |
| `references/analysis-structure.md` | before writing the analysis document |
| `references/acoe-stack.md` | before writing the automation assessment |
| `references/cetin-organisation.md` | when naming owners, tribes and approval chains |
| `references/bpmn-spec.md` | before writing `process.json` |
| `references/dbml-data-model.md` | when the intake ends in stored data |
| `references/cetin-brand.md` | when building any visual deliverable |
| `references/example-process.json` | a full worked spec, if you'd rather see the conventions than read them |
| `assets/visual_template.html` | to build the one-pager |
| `assets/logos/` | CETIN logo files to embed (never redraw) |
