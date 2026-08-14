# Slide switches — hiding a slide without deleting it

A run of the same deck rarely uses every slide. Cutting slides out of the source and pasting them
back later loses content and desyncs the master `.md`. Instead every built file carries a switch
block, and `scripts/slide_switches.py` injects it after each build.

## What the user sees

At the very top of `<head>`, in every built HTML file:

```html
<!-- ============================================================
     SLIDE SWITCHES  —  flip any value to false to hide that slide
     completely (deck, numbering, arrows, divider agenda, contents).
     ============================================================ -->
<script>
window.SLIDE_SWITCHES = {
  "title"   : true ,   // Power Platform Workshop
  "topic-1" : true ,   // Power Platform foundations
  "1.1"     : true ,   // What is Power Platform
  "2.3"     : false,   // Standby Duty
  ...
};
</script>
```

Flip a value, save, reload. Nothing else to run.

## What must be hidden — all five, or it looks broken

1. **The slide itself**, removed from the DOM before the engine initialises.
2. **The numbering** — remaining slides renumber, so `12 / 30` stays truthful.
3. **Navigation** — arrows, swipe, deep links and chapter roll-over all skip it for free once
   it is out of the DOM.
4. **The chapter divider's agenda list** — the row naming that slide disappears too. *This is
   the one that gets forgotten.*
5. **The contents page** — the row goes, remaining `#N` deep links repoint, the per-chapter badge
   and the header total both recount, and a chapter emptied completely hides itself.

## How it works

`scripts/slide_switches.py`, run after `build_all.py` (and after `bundle_deck.py` if used):

- adds `data-key` to every `<section class="slide">` — the slide id (`2.7`) if it has one,
  otherwise `topic-N` for a chapter divider or `title` for the title slide;
- adds the same `data-key` to each `.div-agenda .ag` row and each contents-page `<li>`;
- writes the config block into `<head>`;
- injects the prune script **immediately before the engine `<script>`**, so slides are gone
  before anything counts them.

```bash
python3 scripts/slide_switches.py            # after every build
```

Defaults live in `DISABLED` at the top of that script, not only in the HTML — otherwise the next
rebuild silently switches everything back on.

## Two traps

- **Anchor the injected script on a unique marker.** The literal string `<script>` appears inside
  the engine's own comment header, so `rindex('<script>')` lands the injection *inside* a comment
  and truncates the engine. Match the engine's banner instead.
- **Each file carries its own switches.** To hide a slide across a split deck, flip the same key
  in the chapter file *and* `index.html` — or work in the bundled single file, where one edit
  covers everything. Say this in the handover.

## "Remove" is ambiguous once switches exist

Once a deck has switches, "remove slide 2.17" can mean *disable* or *delete*. **Default to
disabling** and say what you did in one line. Deleting content the user only wanted hidden costs
far more than the extra sentence.
