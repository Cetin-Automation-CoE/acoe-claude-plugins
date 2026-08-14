#!/usr/bin/env python3
"""Drift guard — run before sharing anything.

Answers one question: can the chapter files and the bundled single file be
telling the audience different things? Four ways:

  1. STALENESS   is the bundle older than any chapter it was built from?
  2. COVERAGE    does the bundle hold exactly the chapters' slides?
  3. CONTENT     is every slide title identical in both views?
  4. CONVENTION  do demo / exercise titles follow the agreed naming?

    python3 check_drift.py bundle.json
    python3 check_drift.py bundle.json --demo-pattern '^Demo: .+ [—-] .+' \\
                                       --handson-pattern '^Hands on: .+'

Exit 0 = the two views agree. Non-zero = rebuild or fix before you send it.
"""
import argparse, json, os, re, sys

DEMO_DEFAULT = r'^Demo: .+ [—-] .+'      # Demo: <technology> — <case name>
HANDS_DEFAULT = r'^Hands on: .+'         # Hands on: <name>


def slides_of(html):
    return re.findall(r'<section class="slide.*?</section>', html, re.S)


def title_of(slide):
    """The visible headline, whatever element carries it on that layout."""
    for pat in (r'<h1[^>]*class="title[^"]*"[^>]*>(.*?)</h1>',
                r'<div class="abig[^"]*"[^>]*>(.*?)</div>',
                r'<h1[^>]*>(.*?)</h1>'):
        m = re.search(pat, slide, re.S)
        if m:
            t = re.sub(r'<br\s*/?>', ' ', m.group(1))
            t = re.sub(r'<[^>]+>', '', t)
            return re.sub(r'\s+', ' ', t).replace('&amp;', '&').strip()
    return ''


def eyebrow_of(slide):
    m = re.search(r'class="eyebrow[^"]*"[^>]*>(.*?)</div>', slide, re.S)
    if not m:
        return ''
    t = re.sub(r'<[^>]+>', '', m.group(1)).replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--demo-pattern', default=DEMO_DEFAULT)
    ap.add_argument('--handson-pattern', default=HANDS_DEFAULT)
    ap.add_argument('--no-convention', action='store_true',
                    help='skip the naming check (decks without demos/exercises)')
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding='utf-8'))
    root = os.path.dirname(os.path.abspath(a.config)) or '.'
    rel = lambda p: p if os.path.isabs(p) else os.path.join(root, p)
    problems = []

    # ---------------------------------------------------------- 1. staleness
    bundle_path = rel(cfg['out'])
    if not os.path.exists(bundle_path):
        problems.append(f'{cfg["out"]} does not exist — run bundle_deck.py')
        bundle = ''
    else:
        bundle = open(bundle_path, encoding='utf-8').read()
        b_mtime = os.path.getmtime(bundle_path)
        for ch in cfg['chapters']:
            p = rel(ch['file'])
            if not os.path.exists(p):
                problems.append(f'chapter file missing: {ch["file"]}')
            elif os.path.getmtime(p) > b_mtime + 1:
                problems.append(f'STALE: {ch["file"]} was edited after {cfg["out"]} was built '
                                f'— rerun bundle_deck.py')

    # ---------------------------------------------------------- 2. coverage
    chapter_titles, per_chapter = [], {}
    for ch in cfg['chapters']:
        p = rel(ch['file'])
        if not os.path.exists(p):
            continue
        sl = slides_of(open(p, encoding='utf-8').read())
        per_chapter[ch['file']] = sl
        chapter_titles += [title_of(s) for s in sl]

    bundle_slides = slides_of(bundle)
    bundle_titles = [title_of(s) for s in bundle_slides]

    if bundle and len(bundle_slides) != len(chapter_titles):
        problems.append(f'COVERAGE: bundle has {len(bundle_slides)} slides, '
                        f'the chapters have {len(chapter_titles)}')

    # ---------------------------------------------------------- 3. content
    if bundle and len(bundle_slides) == len(chapter_titles):
        for i, (x, y) in enumerate(zip(chapter_titles, bundle_titles), 1):
            if x != y:
                problems.append(f'CONTENT: slide {i} differs\n'
                                f'    chapter: {x!r}\n'
                                f'    bundle : {y!r}')

    # ---------------------------------------------------------- 4. convention
    if not a.no_convention:
        demo_re, hands_re = re.compile(a.demo_pattern), re.compile(a.handson_pattern)
        rows = []
        for ch in cfg['chapters']:
            for s in per_chapter.get(ch['file'], []):
                eb, t = eyebrow_of(s), title_of(s)
                kind = None
                if re.search(r'\bDemo\b', eb) or t.startswith('Demo'):
                    kind = 'demo'
                elif re.search(r'Hands[ -]on', eb) or t.lower().startswith('hands'):
                    kind = 'hands-on'
                if not kind:
                    continue
                no = (re.match(r'([\d.]+)', eb) or [None, '?'])[1]
                ok = (demo_re if kind == 'demo' else hands_re).match(t)
                rows.append((no, kind, bool(ok), t))
                if not ok:
                    want = a.demo_pattern if kind == 'demo' else a.handson_pattern
                    problems.append(f'CONVENTION: slide {no} is a {kind} but its title does not '
                                    f'match {want}: {t!r}')
        if rows:
            print('demo / hands-on naming')
            print('-' * 62)
            for no, kind, ok, t in rows:
                print(f'  {no:<6} {kind:<9} {"ok " if ok else "BAD"}  {t}')
            print()

    if problems:
        print(f'FAILED — {len(problems)} problem(s):')
        for p in problems:
            print('  x', p)
        sys.exit(1)
    print(f'OK — {len(bundle_slides)} slides, chapters and bundle agree.')


if __name__ == '__main__':
    main()
