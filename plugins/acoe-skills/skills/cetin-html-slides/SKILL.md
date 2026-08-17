---
name: cetin-html-slides
description: Build CETIN-branded HTML presentation decks — a fixed 16:9 stage, chapter-split files, a contents page with per-slide deep links, per-slide on/off switches, and markdown companions holding on-slide text, facilitator notes and the presenter storyline. Use when asked to create, extend, restyle or rebuild a CETIN training deck or slide set as HTML, to turn a content outline or .md into presentable slides, or to convert an existing PowerPoint into this format. Also use when editing slides in a deck that was built this way.
---

# CETIN HTML slide decks

Produces a presentable, self-contained deck: no build step for the audience, no npm, no CDN.
Open the HTML and present. Content lives in one markdown file so it survives past the event.

**Read `references/gotchas.md` before writing any slide.** Every item in it cost a rebuild.

**Building demo / case-study slides, or anything with screenshots?** Read
`references/slide-frame.md` and `references/media-patterns.md` too. Those two exist because
"the layout jumps when I page through" and "this screenshot is stretched" were the two most
expensive corrections in the deck this skill was hardened on.

**New to this skill or unsure the toolchain still works here?** Run
`python3 scripts/selftest.py` first — see step 0 below.

## The system

```
index.html                        contents page — chapter cards, per-slide deep links
<Name>_Topic1-2.html              one file per chapter (or chapter pair)
<Name>_Topic3.html                …
<Name>_slide_text.md              MASTER: on-slide text (verbatim) + facilitator notes + sources
<Name>_storyline.md               presenter cue cards: clock timings, per-slide beats, objections
assets/                           only if a deck references files rather than embedding them
<Name>_FULL.html                  optional: every chapter bundled into one shareable file — GENERATED, never hand-edited
```

Split by chapter. One 40-slide file is slow to open, slow to rebuild and awkward to hand to a
co-presenter. Chapters roll over into each other so it still presents as one continuous deck. If
attendees need a single file to double-click, generate it (step 7) rather than maintaining it by
hand — that is what keeps the split view and the shared file from ever disagreeing.

## Explain this to the user, once, before the first build

Most people using this skill haven't seen it before. Before writing any HTML, say — in plain
terms, not as a wall of text — the four things that are easy to assume wrongly:

1. **While editing, the deck is many files, on purpose.** One file per chapter, plus `index.html`
   as the table of contents. That's what makes it fast to rebuild a single chapter and easy to
   reorder or hand a chapter to a co-presenter. It is *already* a complete, presentable deck like
   this — nothing else needs to happen for someone to open it and present.
2. **Sharing as one file is a separate, deliberate step.** If attendees need a single file to
   email or double-click, say so explicitly ("bake this into one file to share") — the skill will
   never do this on its own, because merging always trails the split version by definition, and
   there's no reason to produce it before it's needed. That step is `bundle_deck.py` (step 8).
3. **Size, once bundled:** aim to stay near ~5 MB so the file is comfortably attachable and opens
   instantly. `bundle_deck.py` prints the final size and, past 5 MB, the concrete levers: link a
   video externally instead of embedding it, compress images harder, or just keep the split
   multi-file version — there's no size ceiling on that one, only on a single emailable file.
4. **It works anywhere.** Chrome, Edge, Firefox, Safari, and it scales to fit any screen including
   a phone (pinch-to-zoom works normally). See "Compatibility" near the end for the specifics and
   its limits.

## Workflow

### Before anything else: agree the storyline

**Do not write a single slide fragment, let alone build any HTML, until the storyline has been
shown to the user and they've said go.** The storyline is the high-level shape of the deck — topic
order, what each one covers, how it hangs together — captured as a short table or list at the top
of the master `.md` (see `references/master-md-template.md`). If it doesn't exist yet, write it
first, in the chat, as text — not as a file, not as slides — and wait for a confirmation or
changes before touching anything else. Reworking a storyline is a few edited lines; reworking
slides built against the wrong one is the whole deck. This gate applies every time content
changes meaningfully, not just at the very start — a materially different agenda gets shown again
before more HTML gets written.

### 0. Prove the toolchain works here (recommended, once per environment)

```bash
python3 scripts/selftest.py
```
Builds a throwaway 2-chapter deck from this skill's own references, generates its contents page,
bundles it into one file, runs the drift guard both ways (clean, then deliberately staled), and —
if Playwright is available — verifies it in a real browser. Nothing here touches your project
files; it works in a temp directory and cleans up after itself. Pass `--keep DIR` to inspect the
output instead. Exit 0 means every stage passed in this environment; a failure here means fix the
skill before using it on a real deck, not the other way round.

### 1. Establish the content first

If a master `.md` exists, it is the source of truth — read it and build from it. If not, create one
from `references/master-md-template.md`, storyline included, and get it agreed (see the gate
above) **before** building HTML. Rewriting slides is cheap; rewriting them after the wording has
been reviewed is not.

Confirm before building: **is this CETIN/work?** (if not, drop the branding entirely), how dense
the slides should be (speaker-led vs reading-first), and whether on-slide text must be verbatim
from a source document.

### 2. Logo

Already included, ready to use — no prep step needed:

| File | Use |
|---|---|
| `assets/cetin-logo-light.png` | for **light backgrounds** — CETIN-Blue wordmark + red triangle |
| `assets/cetin-logo-dark.png` | for **dark backgrounds** — white wordmark + red triangle |

Both are pre-cropped to their alpha bounding box and already have the "MEMBER OF PPF GROUP" claim
line removed — the international mark, wordmark only. If the claim line is wanted (standard for
some B2B material) or a different market variant (e.g. Czech) is needed, ask which before building;
`scripts/prep_logo.py` re-derives either from a fresh canonical source PNG (`--no-claim` is the flag
that strips the line; omit it to keep it). Never redraw the logo by hand.

### 3. Reuse existing artwork

If there's a PowerPoint or PDF to draw on, reuse its visuals rather than re-inventing them:

```bash
python3 scripts/crop_pptx.py inspect deck.pptx --out work/     # text, tables, embedded images
python3 scripts/crop_pptx.py render  deck.pptx --out work/     # LibreOffice → PNG per slide
python3 scripts/crop_pptx.py crop work/slide_2.png 0.045 0.125 0.955 0.815 art.jpg --maxw 2600
```

**Rebuild tables and text as HTML; crop only diagrams, screenshots and logo landscapes.** Table
text must stay real markup so it's editable, searchable and on-brand. Render-and-crop rather than
reading shape coordinates — see gotcha 14.

### 4. Write the slides as fragments

One file per slide in `slides/`, each a single `<section class="slide" data-slide="N">`. Compose
from `references/components.md`; add only the CSS you actually use.

Layout rules that matter:
- **Repeating slide types get a fixed frame, not content-driven sizing.** Same absolute box on
  every slide of that type, footer band in the same place. `references/slide-frame.md`.
- **Screenshots use a named media pattern** (`single` / `two-up` / `overlap` / `stack` /
  `cascade`) with the pattern's own constants. `references/media-patterns.md`. Never tune sizes
  per slide — crop the source instead (`scripts/prep_screenshots.py`).
- **A change asked for on one slide gets a modifier class**, never an edit to a shared rule.
- **Only render meta fields that have real values** (presenter, minutes, users). A row of
  "to be supplied" reads as an unfinished deck.
- **Light mode is the default.** White background, plain CETIN-Blue title type. No filled header
  bar, no rule under the title, no colour band stretched across a content slide.
- Dark mode (`#300091`) is for **title and chapter-divider slides only**.
- Logo bottom-left full size on dividers, bottom-right smaller on content.
- Max three brand colours per slide. Red is an accent — never a background.
- Content area at 1920×1080 with default padding is **1680 × 880**. Budget against that.

### 5. Build every chapter AND the contents page — together, always

```bash
python3 scripts/build_all.py manifest.json      # see the docstring for the config shape
```
**Use this, not `build_deck.py` on its own.** Every chapter deck's "Contents" button is a
hardcoded `href="index.html"` (in `references/deck-shell.html`) — build chapters without also
(re)building the index and that button 404s or opens a stale page the instant someone clicks it.
`build_all.py` makes that structurally impossible: it builds each chapter (assembling shell +
component CSS + slides + engine, substituting tokens, inlining images as data URIs, failing loudly
on any unresolved token or missing anchor — this part is `build_deck.py`, which it calls for you),
then derives that chapter's slide list for the contents page straight from the HTML it just
produced — title, slide number, tag (`demo`/`hands-on`/`video`/…), divider or not — rather than
from a hand-typed duplicate that can silently say something different. Mark a chapter not yet
built with `"ready": false` and no `"build"` key; it still renders as a card, greyed and unlinked,
showing the shape of what's coming.

If you build one chapter alone mid-edit for a quick look, that's fine — just rerun `build_all.py`
before verifying or sharing anything. `verify_deck.py` (step 7) checks the Contents button
actually resolves, so a forgotten index rebuild is caught there too, not just here.

**Embed images; reference video.** A 50 MB mp4 becomes ~70 MB of base64. Keep video as a sibling
file and say so in the handover.

### 5b. Add the slide switches

```bash
python3 scripts/slide_switches.py --off 2.3 2.9      # after every build
```
Injects a `window.SLIDE_SWITCHES` block at the top of every built file: one line per slide, the
slide name as a comment, flip to `false` to hide it. Hidden slides vanish from the deck, the
numbering, the navigation, **the chapter divider's agenda list** and the contents page.
Defaults live in `DISABLED` inside the script, so a rebuild doesn't switch things back on.
Details and the two traps: `references/slide-switches.md`.

Once a deck has switches, **"remove slide X" almost always means disable it** — default to that
and say so in one line rather than deleting content that has to be rebuilt later.

### 6. Reference: `build_deck.py` and `make_index.py` on their own

`build_all.py` calls these two directly (`build_deck.build(cfg_path)`, `make_index.build_from_cfg`)
— reach for them individually only for a fast one-chapter preview while editing, never as the last
step before sharing:

```bash
python3 scripts/build_deck.py build.json      # one chapter only
python3 scripts/make_index.py index.json      # the contents page, from a hand-written manifest
```

### 7. Optional, and only when the user asks: bundle every chapter into one shareable file

**Only when the user asks for a single shareable file.** Don't build this proactively — the
chapter files plus `index.html` are already a complete, presentable deck, and a bundle produced
before it's needed is just one more thing that can go stale. Wait for something like "bake this
into one file" or "give me something I can email."

```bash
python3 scripts/bundle_deck.py bundle.json      # see the docstring for the config shape
python3 scripts/check_drift.py bundle.json      # the two views must agree before you share
```
**The chapter files stay the source. The bundle is generated — never hand-edit it.** That is what
stops the split view and the single file silently disagreeing: there is nothing to hand-edit out
of sync, because the bundle has no state of its own. `check_drift.py` fails if any chapter was
edited after the bundle was built, if slide counts diverge, if any slide's title differs between
the two views, or if a demo/exercise title breaks whatever naming convention you pass it
(`--demo-pattern`, `--handson-pattern`). Run it before every share, not just the first time.

`bundle_deck.py` also: scopes each chapter's CSS under its own prefix so chapters can't restyle
each other (gotcha 18 covers the one sharp edge — divider-style rules that target the slide
itself); deduplicates and recompresses every embedded image into one `window.IMAGES` map (typically
a 60–65% size cut, since the logo alone repeats on every slide); and can swap a local `<video>` for
a click-to-play poster linking to YouTube, so the file doesn't have to carry the raw footage
(gotcha 19).

**Size.** `bundle_deck.py` prints the final size and, past 5 MB, prints its own concrete
suggestions — you don't have to remember to check by hand. The levers, in the order they're
usually worth trying: link a video externally instead of embedding it (`video_substitutions` in
the manifest — already the default for anything that was a local `.mp4`); compress images harder
(lower JPEG quality or a smaller max width in `bundle_deck.py`'s `recompress()`); or, if the deck
is simply large, keep the split multi-file version instead of insisting on one file — there's no
size ceiling on that, only on something meant to be emailed as one attachment. Raise this with the
user as a choice, not something to silently decide for them.

### 8. Verify — not optional

```bash
python3 scripts/verify_deck.py <Name>_Topic3.html --shots shots/
python3 scripts/verify_deck.py index.html --index
python3 scripts/verify_deck.py <Name>_FULL.html --shots shots/     # if you bundled
```
Checks slide count, overflow, content past the padding box, broken images, **images rendered at
the wrong aspect ratio** (the squashed-screenshot check), **the switch config** (every key
resolves, nothing switched off is still in the DOM), chrome-vs-eyebrow collision, JS errors, that the **Contents button actually resolves and lands on a real contents
page** (not just that a file happens to exist next to it — it clicks it and checks), and that the
phone stage is still exactly 16:9. `--index` checks every link resolves and no deep link exceeds
its deck's slide count. Against a bundled file it detects the contents-page shell automatically and
drives by hash instead of arrow keys.

**Then look at the screenshots.** Overflow checks pass on panels that visually cover each other.
Judge vertical balance by eye: a block pinned to the floor with a large gap above it usually wants
a fixed frame instead of `margin-top:auto`.

**Page through a run of same-type slides and watch what moves.** If the text column or the images
shift between two demo slides, the template isn't fixed — fix the template, not the slide.

### 9. Close the loop

Update **both** markdown files:
- the master `.md` — asset table, slide index, and any slide whose on-slide text changed;
- the storyline `.md` — timings, presenters, which slides are switched off for this run.

Renumbering is one operation across five places: slide ids, the divider agenda, the contents
page, the master `.md` and the storyline. Doing four of the five is how a deck ends up with a
divider announcing a slide that no longer exists.

Then tell the user plainly which files must travel together (video, `assets/`), and — if they
edited in the browser with `E` — that those edits live only in their downloaded copy and should
be sent back so they can be folded into the source.

### 10. Content integrity

**If a supplied description contradicts the screenshots, stop and ask before building it.**
Copy-paste errors between app descriptions are common and produce two slides claiming the same
numbers. One question costs a minute; the correction in front of an audience costs more.

## Compatibility

**Browsers.** Built from standard CSS and DOM APIs only — `transform`, `clip-path`,
`aspect-ratio`, `mix-blend-mode`, `classList`, `addEventListener` — nothing that only one engine
implements. The one exception, `backdrop-filter` on the Contents button and slide counter, ships
with the `-webkit-` prefix Safari needs alongside the unprefixed rule. Automated verification here
(`verify_deck.py`, `selftest.py`) runs on Chromium, since that's the only browser engine installed
in this environment — Firefox and Safari correctness rests on sticking to the standard, broadly
supported subset above rather than on an automated multi-browser test run. If either is available
wherever this actually gets used, a manual look is worth it before a high-stakes share.

**Mobile.** The stage is a fixed 1920×1080 design scaled uniformly to fit whatever viewport it's
in (`fitStage()` in the engine) — same layout, letterboxed, on a phone as on a projector. Pinch and
double-tap zoom work normally (the viewport meta tag doesn't disable them). `verify_deck.py` checks
the scaled stage is still exactly 16:9 at 390×844 every time. There's no separate reflowed "mobile
view" — dense slides are still dense on a small screen, just zoomable — so say so if the audience
is expected to read this primarily on a phone; it may be worth a lighter layout for that slide.

## Navigation, built in

Common to every deck, so a presenter learns it once:

| | |
|---|---|
| Arrows / Space / swipe | move through slides |
| Arrow at either end | **rolls over** into the next/previous chapter file |
| Last slide | **Next chapter** button appears top-right, naming where it goes |
| **Contents** button top-left | back to `index.html` |
| `file.html#9` | opens slide 9; the URL tracks as you navigate |
| `E` | edit mode — **browser only, does not write to the file** |
| `⌘S` / `Ctrl+S` | downloads `…-edited.html` with the edits baked in |

Say the edit-mode caveat out loud when handing over. People assume `E` then `S` saves their work,
and it does not touch the original — nor does it flow back to the master `.md`.

## The storyline file

Any deck with more than one presenter or a timed agenda gets a second markdown companion,
`<Name>_storyline.md`: clock-time table, one line per slide, the sentence worth saying out loud
for each demo, and an objection table. Cue cards, not prose — presenters read it the morning of
the event and never open the master `.md`. Structure and rules:
`references/storyline-template.md`.

## Slide-count honesty

If a slide's content isn't ready, build it with a visible `.pending-note` saying what's missing.
Never ship a slide that looks finished and isn't, and never invent content to fill one — mark it
and tell the user which slides are still open.

## Files

| File | Use |
|---|---|
| `references/gotchas.md` | **read first** — traps with fixes |
| `references/deck-shell.html` | boilerplate: stage CSS, brand tokens, chrome, transition |
| `references/deck.js` | the engine for a standalone chapter deck — inline it, don't link it |
| `references/bundle-engine.js` | the engine for a *bundled* single file — home ↔ deck routing, click-to-play video, image lookup |
| `references/bundle.css` | cross-chapter utilities + the single-file shell (contents page as a scrolling layer) — always global, never scoped |
| `references/components.md` | component catalogue: archetypes, text, tables, cards, charts |
| `references/slide-frame.md` | **read for any repeating slide type** — the fixed frame, legend columns, the demo template, change-scoping |
| `references/media-patterns.md` | **read before placing any screenshot** — the five named layouts and their constants |
| `references/slide-switches.md` | per-slide on/off switches: what gets hidden, how, and the traps |
| `references/storyline-template.md` | presenter cue-card file: structure and rules |
| `references/master-md-template.md` | master content file structure and its rules |
| `references/index-template.md` | contents page anatomy and card states |
| `scripts/build_all.py` | **the primary build command** — every chapter + the contents page, together, always |
| `scripts/build_deck.py` | assemble one chapter deck (called by `build_all.py`; use alone only for a quick preview) |
| `scripts/make_index.py` | generate the contents page (called by `build_all.py`; use alone only with a hand-written manifest) |
| `scripts/bundle_deck.py` | merge every chapter into one shareable file — generated, never hand-edited |
| `scripts/cssmerge.py` | scopes each chapter's CSS so chapters can't collide (used by `bundle_deck.py`) |
| `scripts/check_drift.py` | fails the build if the chapters and the bundle can tell attendees different things |
| `scripts/slide_switches.py` | inject the per-slide on/off switches — run after every build |
| `scripts/prep_screenshots.py` | ingest a screenshot: resize, recompress, crop to a target aspect so pairs match |
| `scripts/verify_deck.py` | screenshots + overflow/overlap/distortion/switch/link checks — chapter deck or bundle |
| `scripts/selftest.py` | proves this whole toolchain works in the current environment — run it first |
| `scripts/crop_pptx.py` | inspect / render / crop an existing PowerPoint |
| `scripts/prep_logo.py` | re-crop the CETIN logo from a fresh source PNG, optionally drop the PPF claim |
| `assets/cetin-logo-light.png` | CETIN logo for light backgrounds, ready to embed |
| `assets/cetin-logo-dark.png` | CETIN logo for dark backgrounds, ready to embed |

This skill is self-contained — the brand spec it needs (palette, type, logo rules) is captured
below and baked into `references/deck-shell.html`; nothing else needs to be installed.

## Brand reference

| | |
|---|---|
| CETIN Blue | `#300091` — call it Blue, never "purple" |
| CETIN Red | `#f12e49` — an accent, never a slide background |
| Type | Arial / "Avenir Next LT Pro" / Helvetica Neue, sans-serif |
| Default mode | **light** — white background, plain CETIN-Blue title type, no header bar |
| Dark mode | title and chapter-divider slides only (`#300091` background, white type) |
| Logo, dividers | bottom-left, full size (`.logo-intro`, ~300px) |
| Logo, content slides | bottom-right, smaller (`.logo-content`, ~168px) |
| Max brand colours per slide | three |

These are already the defaults in `references/deck-shell.html` — the table above is a quick check,
not something to re-derive.
