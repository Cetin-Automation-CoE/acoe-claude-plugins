#!/usr/bin/env python3
"""Build every chapter deck AND the contents page together, in one call.

Why this exists: every chapter deck's "Contents" button is a hardcoded
`href="index.html"` (see references/deck-shell.html). If chapters get built
without also (re)building `index.html` — a forgotten step, not a deliberate
one — that button 404s or opens a stale page the moment someone clicks it.
This script makes that impossible: there is no path through it that produces
chapter decks without also producing a matching, up-to-date index.

    manifest.json
    {
      "index": {
        "out": "index.html", "programme": "DunAI", "training": "AI Exec Training",
        "date": "29 July 2026", "presenters": "Jiri Forman · Peter Kukura",
        "logo": "assets/cetin-logo-dark.png",
        "resources": [{"title": "Master content reference",
                       "body": "<a href='x.md'>x.md</a> — every slide's text and notes."}]
      },
      "chapters": [
        {"build": "build_topic1-2.json", "num": "1", "title": "AI Intro", "sub": "…"},
        {"num": "9", "title": "Wrap-up", "sub": "…", "ready": false,
         "file": "Deck_Topic9.html", "slides": [["9.1  Placeholder", "", false]]}
      ]
    }

    python3 build_all.py manifest.json

Each chapter is EITHER:
  - `"build": "<build_deck.json path>"` — an already-authored chapter, built via
    build_deck.py. Its slide list for the contents page (label / tag / divider)
    is derived automatically from the slides it just built, not hand-typed —
    so the index card can't say something different from the deck itself.
  - or a hand-written stub (no "build" key, matching make_index.py's existing
    "not built yet" card shape) for a chapter that doesn't exist as HTML yet.

Fails loudly and stops before writing the index if ANY "build" chapter fails,
so you never end up with an index describing decks that didn't actually build.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_deck, make_index  # noqa: E402


def slides_of(html):
    return re.findall(r'<section class="slide.*?</section>', html, re.S)


def slide_classes(section):
    m = re.match(r'<section\s+class="([^"]*)"', section)
    return set(m.group(1).split()) if m else set()


def title_of(section):
    for pat in (r'<h1[^>]*class="title[^"]*"[^>]*>(.*?)</h1>',
                r'<div class="abig[^"]*"[^>]*>(.*?)</div>',
                r'<h1[^>]*>(.*?)</h1>'):
        m = re.search(pat, section, re.S)
        if m:
            t = re.sub(r'<br\s*/?>', ' ', m.group(1))
            t = re.sub(r'<[^>]+>', '', t)
            return re.sub(r'\s+', ' ', t).replace('&amp;', '&').strip()
    return ''


def eyebrow_of(section):
    m = re.search(r'class="eyebrow[^"]*"[^>]*>(.*?)</div>', section, re.S)
    if not m:
        return ''
    t = re.sub(r'<[^>]+>', '', m.group(1)).replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def derive_slide_row(section):
    """One [label, tag, is_divider] row for the contents page, read straight
    off the built slide so it can never say something the deck doesn't."""
    classes = slide_classes(section)
    is_divider = 'divider' in classes
    title = title_of(section)
    eyebrow = eyebrow_of(section)

    tag = ''
    if re.search(r'\bDemo\b', eyebrow) or title.startswith('Demo'):
        tag = 'demo'
    elif re.search(r'Hands[ -]?on', eyebrow, re.I) or title.lower().startswith('hands on'):
        tag = 'hands-on'
    elif 'activity' in classes:
        tag = 'activity'
    elif '<video' in section or 'ytbox' in section:
        tag = 'video'

    if is_divider:
        label = title or 'Chapter divider'
    else:
        num = (re.match(r'([\d.]+)', eyebrow) or [None, None])[1]
        label = f'{num}  {title}' if num else (title or 'Slide')
    return [label, tag, is_divider]


def build_one_chapter(entry, root):
    """Build a chapter that has a `build` pointer, and derive its index card
    data from the HTML it just produced."""
    cfg_path = entry['build'] if os.path.isabs(entry['build']) else os.path.join(root, entry['build'])
    out_path = build_deck.build(cfg_path)   # build_deck.build() sys.exit()s loudly on any failure
    html = open(out_path, encoding='utf-8').read()
    slides = [derive_slide_row(s) for s in slides_of(html)]
    if not slides:
        sys.exit(f'BUILD FAILED — {entry["build"]} produced no slides')
    return {
        'num': entry['num'], 'title': entry['title'], 'sub': entry.get('sub', ''),
        'file': os.path.basename(out_path), 'ready': True, 'slides': slides,
    }


def main(manifest_path):
    manifest = json.load(open(manifest_path, encoding='utf-8'))
    root = os.path.dirname(os.path.abspath(manifest_path)) or '.'

    if 'chapters' not in manifest or not manifest['chapters']:
        sys.exit('BUILD FAILED — manifest has no "chapters"')
    if 'index' not in manifest:
        sys.exit('BUILD FAILED — manifest has no "index" section; the contents page '
                 'has nowhere to get its title/date/presenters from')

    print(f'Building {len(manifest["chapters"])} chapter(s)...')
    chapters = []
    for entry in manifest['chapters']:
        if 'build' in entry:
            chapters.append(build_one_chapter(entry, root))
            print(f'  built  {entry["build"]:<34} -> {chapters[-1]["file"]} '
                 f'({len(chapters[-1]["slides"])} slides)')
        else:
            stub = dict(entry)
            stub.setdefault('ready', False)
            stub.setdefault('slides', [])
            chapters.append(stub)
            print(f'  stub   {entry.get("title", "?"):<34} (not built yet — placeholder card only)')

    index_cfg = dict(manifest['index'])
    index_cfg['chapters'] = chapters
    out = make_index.build_from_cfg(index_cfg, root)
    print(f'\nindex.html and every chapter deck are now in sync. '
         f'The "Contents" button on every deck resolves.')
    return out


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
