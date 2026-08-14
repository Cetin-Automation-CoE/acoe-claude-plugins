# Storyline file — `<Name>_storyline.md`

The master `.md` says **what is on the slides**. The storyline says **what the presenter does**.
They are different jobs and they belong in different files: presenters read the storyline the
morning of the event and never open the master.

Produce it for any deck with more than one presenter, or any deck with a timed agenda.

## Rules

- **Cue cards, not prose.** A presenter glances at this between slides. Tables beat paragraphs.
- **One line per slide, maximum.** If a beat needs a paragraph, it belongs in the master `.md`
  facilitator notes.
- **Give every block a clock time**, not a duration. "0:35 – 0:40" is usable while presenting;
  "5 min" requires arithmetic under pressure.
- **Name the line that lands** for each demo — the single sentence worth saying out loud.
- Regenerate it whenever slides move. It goes stale faster than anything else in the deck.

## Structure

```markdown
# <Deck> — Storyline

Cue cards, not a script. Glance, don't read.
**Audience: <who>.** Everything below aims at one outcome — <the outcome>.

## The N things they must leave with
| # | Say it like this |

## Timing
| Clock | Block | Min | Who |
| 0:00 – 0:10 | Topic 1 — the toolbox | 10 | Minarovič |
...
**Total NNN minutes**, leaving NN minutes of buffer in a <length> slot.
- Which slides are switched off for this run.

## <Topic> — <n> min · <presenter>
| Slide | The one thing to land |

## The beats every demo follows
| Beat | Roughly |
1. Business first — what people did before, by hand. No technology yet.
2. Effort & stack — high level, and what it cost.
3. Live demo — narrate business value while clicking, not features.
4. Punchline — the "built over a coffee, solved a problem worth millions" line.
5. Questions.

## The demos
| Demo | Level · effort · scale | Presenter | Before | The line that lands |

## If someone asks…
| They ask | You answer |
```

## The objection table earns its place

Every workshop gets the same six questions. Writing the answers down once means every presenter
gives the same one:

| They ask | You answer |
|---|---|
| "How long would ours take?" | Small app: hours to days. Cross-system with SAP or robots: weeks. |
| "What does it cost?" | Mostly nothing extra — it's in M365. It costs when you need premium connectors, robots or a model-driven app for many users. |
| "Who builds it?" | Someone in your team, with the CoE alongside. Not an IT project. |
| "Is it safe?" | Same licensing, DLP and permissions rules as everything else in M365. |
| "Isn't AI better?" | For fuzzy work, yes. For a fixed repeatable process, low-code is cheaper, faster and more stable. |
| "Where do I start?" | Come to the CoE. Bring one annoying spreadsheet. |
