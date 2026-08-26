# Structure of the analysis document

The written analysis is the artefact that survives the project. The BPMN is the
specification and the visual is the thing people look at, but the Markdown is where the
reasoning lives — and it is what protects the organisation when the process owner is on
holiday, changes role, or leaves.

Use these sections. Skip one only when the recording genuinely gave you nothing for it,
and say so rather than padding.

---

## Header block

Source (recording title, date, duration), who presented, what example they worked
through, and two standing caveats:

- **Source quality.** If the transcript is machine-generated, say so plainly and state
  that codes, names and figures are phonetic reconstructions. Mark every uncertain item
  `**(verify)**` inline. This is not hedging — it tells the reader which items need a
  five-minute confirmation before they become a specification.
- **Timestamps.** Explain that a marker points at the start of the speaker turn
  containing the topic, so inside a long monologue the exact moment may fall a minute or
  two later. Use `~` for positions inferred from content rather than a turn marker.

## §0 Accompanying diagrams

A short table: the BPMN file, the rendered SVG, the HTML one-pager — what each is and
what to do with it. Readers who open the Markdown first need to know the other files
exist and which one to send to whom.

## §1 Executive summary

One paragraph of what the process is and what it costs in effort, then **three findings
that dominate**, then any single structural defect that must be fixed before automation
ships. Write this last, after you know what you actually found.

Resist the urge to make the summary a table of contents. It should be readable on its own
by someone who will never open the rest.

## §2 Semantics of the output

**This section is the one most often missing and most often expensive.**

Almost every recurring report carries a definition its author states casually and its
consumers never hear. "These aren't July costs, they're what was *posted* in July." "The
headcount is at contract start, not FTE." Today the author is in the room to explain it.
An automated feed into a dashboard is read at face value by people who were never told.

If the walkthrough contains such a definition, give it its own section, quote it, cite the
timestamp, and spell out the consequences. If you're confident there isn't one, say so
explicitly — that is itself a finding.

## §3 As-is process map

Stage by stage. For each stage: a recording range, then a table of steps.

For system extractions, the columns that matter are: **transaction / report name, likely
real code, recording timestamp, purpose, parameters and manual handling**. Parameters are
where the automation actually lives — a row limit, a selection variant, a date convention,
a reformatting formula. These are the details that get lost in a summary and then cost a
sprint to rediscover.

Also capture, in prose after the table:

- **Artefacts maintained outside any system** — the personal register, the hand-kept
  codelist, the mapping spreadsheet on a shared drive. Enumerate them. They are invisible
  to a systems inventory and they are single points of failure.
- **Every fallback and exception path**, with its trigger condition.
- **What downstream consumers do by hand** after they receive the output. This is often
  automatable in the same pass and is routinely left out of scope because nobody asked.

## §4 Automation assessment

Three buckets. Be honest about which is which; an over-optimistic green list is the
fastest way to lose credibility in the follow-up meeting.

- **Green — deterministic, automate as-is.** Extraction, joins, lookups, arithmetic.
- **Amber — automatable once a rule is agreed.** The logic exists but lives in someone's
  judgement and has never been written down. Say precisely what decision is missing.
- **Red — blocked or genuinely manual.** Missing authorizations, sources with no key to
  join on, case-by-case negotiation, judgement about the past that no data can
  reconstruct.

Close with a **coverage judgement** in prose. Usually most of the *elapsed time* is green
while most of the *meaning* is amber — say that, because it reframes where the
specification effort should go. Avoid inventing a percentage the recording doesn't
support; a defensible qualitative statement beats a fake number.

## §5 Open decisions

Numbered, each phrased as a question with the options and, where the recording gives one,
the process owner's own recommendation. Include the decisions nobody framed as decisions —
the report's actual purpose, which of two conflicting sources wins, whether a block that
one party says is unused should simply be dropped.

Be careful to distinguish *a preference someone stated* from *a decision the group made*.
Writing "agreed direction: X" when one person said X and then deferred will be read back
in a steering meeting as consensus that never existed.

## §6 Risks

A table. The recurring ones worth checking for every time:

- single point of knowledge, and the undocumented side files that go with it
- semantic misinterpretation once the output is automated
- double counting, where the same value reaches the output by two paths
- timing dependencies automation cannot shorten
- volatility in the supplier or source landscape
- access dependencies that gate testing
- data-permission questions the owner themselves raised
- the quality of your own source, if it is a machine transcript

## §7 Agreed actions

A table of who does what, taken from the recording — not invented. If an action was
implied but never assigned, say it is unassigned. That gap is useful information.

## §8 Recommended sequence

Your view of the order of work, with reasons. The two recommendations that hold almost
universally:

1. Write down and get sign-off on the as-is specification, independent of whether
   automation ships — it is the mitigation for the knowledge-concentration risk.
2. Reproduce one historical period exactly, cell for cell, as a regression test. Every
   difference is either a bug or an undocumented rule, and both are findings.

## §9 Timestamp index

Three parts:

1. **Quick lookup** — a table of every system, transaction or artefact against the
   timestamp where it is demonstrated. This is what people actually use the document for
   in week three.
2. **Chronological walkthrough** — every topic change with its timestamp. Aim for a row
   roughly every 1–3 minutes of recording.
3. **The highest-value minutes to re-watch** — five or so, with why. Someone joining the
   project later has a 95-minute recording and no idea where to start; this is the answer.
