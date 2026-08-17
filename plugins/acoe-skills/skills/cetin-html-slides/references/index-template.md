# Contents page (`index.html`)

A CETIN-branded, scrollable HTML page — not a slide. It is the entry point: chapter cards, every
slide deep-linked, the asset list, and presenting notes.

## Structure

```
header .hero
  .hero-blue           CETIN-blue band, clip-path bevel at the bottom edge
    .kicker            PROGRAMME · CONTENTS
    h1                 training name, ALL CAPS, white
    .hero-rule         red rule
    .hero-meta         date · presenters · slide and chapter counts
  .hero-logo           negative logo, top-right
.wrap
  .section-label       "CHAPTER DECKS — CLICK ANY SLIDE TO OPEN IT DIRECTLY"
  .decks               responsive grid, minmax(400px, 1fr)
    .deck              one card per chapter file
      .deck-head       .deck-num · h2 · .deck-sub · .badge
      ul.slides        one <li><a href="file.html#N"> per slide
      .deck-foot       .btn "Open deck"
  .section-label       "SOURCE & ASSETS"
  .res                 .rescard grid — master .md, videos, asset folders, open items
  .section-label       "PRESENTING"
  .tips                keyboard, roll-over, deep links, edit mode + save caveat, full screen
footer
```

## Card states

- **Ready** — `.badge.ready` (CETIN Blue), slides are `<a>` links, red "Open deck" button.
- **Not built** — `.deck.pending`, `.badge.todo` (CETIN Red), slides are `<span class="dead">`
  (visible but not clickable), button becomes `.btn.off` "Content still needed". Listing the
  slide titles of an unbuilt chapter is useful — it shows the shape of what's coming.

## Per-slide tags

A small right-aligned `.tag` on a row is worth adding for anything that behaves differently:
`divider`, `video`, `chart`, `1:1 art`, `activity`, `hands-on`, `demo`.

## Generate it, don't hand-write it

Drive the page from a manifest so it can never drift from the files on disk — see
`scripts/make_index.py`. After building, verify every `href` resolves to a real file and that no
deep link exceeds that deck's slide count.
