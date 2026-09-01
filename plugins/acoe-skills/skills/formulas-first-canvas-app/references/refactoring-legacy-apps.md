# Refactoring a legacy Canvas App into formulas-first shape

A ladder of six rungs. **The app compiles green and is committable at the top of every
rung.** There is no big-bang rewrite of a canvas app: there is no test suite to catch
you, the compiler misses whole classes of error, and a broken `App.Formulas` blob takes
every screen down at once.

Order is not arbitrary. Each rung is ordered by **blast radius and guardability** — the
boundary that is cheapest to protect with a script goes first, so that every later
sweep runs on ground that cannot silently move.

---

## Rung 0 — Get the source under version control

Unpack to YAML and commit before touching anything.

```bash
pac solution export --name <Solution> --path ./out --managed false
pac solution unpack --zipfile ./out/<Solution>.zip --folder . \
  --packagetype Unmanaged --processCanvasApps
git add -A && git commit -m "chore: unpacked baseline before refactor"
```

Git is the only rollback that exists. Studio's version history is coarse, and a stale
studio tab can write its in-memory document back over your changes — when that happens,
`git checkout` is the recovery.

**Gate:** a clean tree containing the untouched app.

---

## Rung 1 — Inventory (mechanical, read-only)

```bash
python3 scripts/inventory.py --src <path/to/Src> --out docs/inventory.md
```

Produces a census: colour literals by frequency, font sizes, spacing values,
data-source references by file, duplicated formula bodies, `Switch` arms per
discriminator, control counts per screen.

**Counts are the signal.** A colour used 129 times is load-bearing and gets a token
named after its role. A colour used once is either a mistake or a one-off, and the
difference matters — the census tells you which values you are allowed to touch
cheaply. Typo-twins fall out here too: `RGBA(241,46,73)` used 40 times beside
`RGBA(241,46,76)` used once is a typo, not a design decision.

**Gate: no file has been modified.** Commit the inventory as documentation.

---

## Rung 2 — Audit (judgement, read-only, own branch)

Read the inventory plus the source and write findings. Every finding gets an ID
(`F-001`), a file:line, a severity, and a proposed fix. Template:
`templates/findings.csv`.

Separate three categories and do not let them mix:

| Category | Handling |
|---|---|
| **Defect** — wrong behaviour, wrong arithmetic, wrong sign | Fix in rung 3. Highest priority; refactoring around a bug preserves the bug. |
| **Structural** — duplication, literals, screen-level data access | The refactor itself, rungs 4–6. |
| **Ambiguity** — the code does something the docs don't explain | **Ask the human. Number the questions. Do not guess.** |

That third row is the one that gets skipped under time pressure, and it is the one that
causes damage: an agent that guesses at an undocumented business rule writes a
confident, plausible, wrong app. If nobody can answer, the finding stays open and the
code stays as-is.

**Gate: still no code changed, and the human has signed off on the findings list.**
Rungs 3+ do not begin without that sign-off.

---

## Rung 3 — Fix defects first, one finding per commit

Commit messages carry the finding ID: `fix(app): savings sign per spec §6.1 (F-001)`.

Defects before structure, because a structural sweep that moves buggy code around makes
the bug harder to find and impossible to bisect.

**Gate:** each commit compiles green. Commit *the moment* a compile is green — canvas
sessions fail in ways that lose work, and a green commit is a checkpoint you cannot
reconstruct later.

---

## Rung 4 — Extract the data-access boundary

The largest blast radius, so it goes first among the structural rungs, and it is the
one a grep-level script can guard completely.

1. Open the region in `App.Formulas` with banner comments.
2. Move every read into `funcLoadX(): Void`; every write into
   `funcSaveX(...)` / `funcDeleteX(...)`.
3. Translate shapes **at the boundary only** — choice wrappers, lookup records, claims
   objects, per-entity physical resolution. Screens get flat scalars.
4. Repoint screens to the flat collections and the `func*` calls.
5. Write the guard and run it:

```bash
python3 scripts/check_data_layer.py --src <Src> --datasource-pattern '<YourPrefix>'
```

Detail and the backend-switch procedure: `references/data-access-layer.md`.

**Gate:** `check_data_layer.py` passes and compile is green.

---

## Rung 5 — Token layer, then screens — never in one commit

**Commit A: define the tokens.** Roles, not values: `constInkColor` not
`constDarkGrey`. Fold typo-twins into the real token. Give status colours AA-safe text
variants (`references/design-system.md`) — status colour as small text on white is the
single most common contrast failure in business canvas apps.

**Commit B: repoint screens to them.** Mechanical substitution, no judgement.

Then the guard:

```bash
python3 scripts/check_tokens.py --src <Src>
```

Keeping A and B separate is what makes the sweep bisectable: if the app looks wrong
afterwards, one commit changed meaning and the other changed references, and you can
tell which. A combined commit is a wall of diff nobody can review.

**Honest exception:** components without `AccessAppScope: true` cannot see app tokens.
Either flip the flag, or pass tokens in as input properties, or leave the literals and
**record the exemption in the inventory**. Do not hide them.

**Gate:** `check_tokens.py` passes, or every remaining literal is a recorded exemption.

---

## Rung 6 — Deduplicate into registries and components

Last, because it is the rung with the most judgement and the least mechanical safety.

- `Switch` arms that grow with the data model → registry rows (`constEntities`,
  `constScreens`), iterated by a component.
- Repeated control blocks → a canvas component. Watch the `AccessAppScope` trap and the
  whole-record output resolution trap in `SKILL.md`.
- Repeated expressions → `func*` or `const*`.

**Gate:** all four scripts pass, compile is green, and the app checker's finding count
has gone down rather than up.

---

## The three rules that decide whether this survives

**1. One axis per pass.** Colour, or layout, or naming, or logic — never two. A pass
that changes two axes cannot be reviewed, because no reviewer can tell which change
caused which visual difference.

**2. Normalization commits alone.** Studio Save rewrites the YAML — strips comments,
alphabetizes properties, elides defaults. That diff is large, behaviour-preserving, and
must land by itself as `chore: server round-trip normalization`. Mixed into a semantic
commit it hides the real change completely.

**3. Commit on green.** Not at the end of the session, not once the feature is done.
The moment compile passes.

---

## Rationalizations to refuse

| Excuse | Reality |
|---|---|
| "The inventory is obvious, I'll skip to fixing" | The inventory is what tells you which literals are load-bearing. Without counts you will token-ize a typo and inline a real value. It takes one script run. |
| "I can see the bug, I'll fix it while I'm in here" | That is two axes in one pass. Note the finding, finish the rung, fix it in its own commit. |
| "This literal is obviously just white" | `RGBA(255,255,255,1)` appearing 44 times means it has at least two different *roles* — paper, and structural transparent-ish fill. Tokenize by role or you will repaint the wrong things. |
| "Tokens and screens in one commit is fewer commits" | And zero bisectability. The split costs 30 seconds. |
| "The app compiles, the refactor is done" | Compile does not check collection columns or string column names. Run all four scripts. |
| "I'll add the guard script after the sweep" | Then the sweep is the only thing holding the convention, and it rots by the next sprint. Guard first. |
| "The human isn't around to answer the ambiguity" | The finding stays open and the code stays as-is. A guessed business rule is worse than a documented gap. |
| "It's a small app, the ladder is overkill" | Then the rungs take an hour each instead of a day. The order is the value, not the ceremony. |
