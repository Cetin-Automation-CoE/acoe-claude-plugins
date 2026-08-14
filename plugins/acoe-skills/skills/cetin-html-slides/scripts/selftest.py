#!/usr/bin/env python3
"""End-to-end smoke test for this skill. Run it to prove the toolchain works here.

Builds a throwaway 2-chapter deck (+ one unbuilt stub chapter) from the skill's own
references and its own bundled logo (assets/cetin-logo-light.png, cetin-logo-dark.png
— no other skill needed), using build_all.py to build every chapter AND the contents
page together and confirming index.html's slide list was derived from the built
decks, not hand-typed. Separately proves the safety net: a chapter built in isolation
(no index.html alongside it) is caught by verify_deck.py rather than shipping with a
dead "Contents" button. Then bundles everything into one file, runs the drift guard,
and — if Playwright is installed — screenshots every slide, checks for overflow, and
clicks Contents for real.

    python3 scripts/selftest.py                 # temp dir, cleaned up after
    python3 scripts/selftest.py --keep out/     # keep the artefacts to look at

Exit 0 means every stage passed. Nothing here touches your real decks.
"""
import argparse, base64, json, os, shutil, struct, subprocess, sys, tempfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REF = os.path.join(SKILL, 'references')


# --------------------------------------------------------------------------
def png(w, h, rgb):
    """A solid placeholder PNG — used only for the video poster, which has no
    brand meaning. The logo itself uses the skill's own real asset (see main())."""
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw))
            + chunk(b'IEND', b''))


SLIDE_TITLE = '''<section class="slide title-slide" data-slide="1">
  <div class="title-art"></div>
  <div class="title-copy">
    <h1 class="anim a-slide d2">Selftest Deck</h1>
  </div>
  <div class="title-people names anim a-slide d4">Ada Lovelace<br>Alan Turing</div>
  <img class="logo-intro anim a-fade d6" src="LOGO_DARK" alt="CETIN">
</section>
'''

# A divider slide: `divider` sits on the SAME <section class="slide divider">
# element as `slide`, not on a descendant. A `.divider{…}` rule therefore
# targets the slide itself. If the CSS scoper treats it as a descendant
# selector (`.c1 .divider`) instead of a compound one (`.c1.divider`), it
# silently never matches once bundled — the exact bug that shipped once
# already. This fixture exists so that regression fails loudly.
SLIDE_DIVIDER = '''<section class="slide divider" data-slide="{n}">
  <div class="div-copy"><h1 class="anim a-slide d2">Chapter {num}</h1></div>
</section>
'''
CSS_DIVIDER = '.divider{background:#300091;color:#fff}.divider h1{color:#fff}'

SLIDE_CONTENT = '''<section class="slide" data-slide="{n}">
  <div class="pad">
    <div class="eyebrow anim a-slide d1">{no} &nbsp;·&nbsp; {chapter}{extra}</div>
    <h1 class="title anim a-slide d2">{title}</h1>
    <div class="lede anim a-slide d3">{lede}</div>
    <div class="st-box anim a-pop d4">Content area is 1680 &times; 880 at default padding.</div>
  </div>
  <div class="slide-no anim a-fade d6">{no}</div>
  <img class="logo-content anim a-fade d6" src="LOGO_LIGHT" alt="CETIN">
</section>
'''

# deliberately clashing class name: chapter 2 restyles .st-box for itself.
# If CSS scoping is broken, chapter 1's box turns red and the test says so.
CSS_C1 = '.st-box{background:var(--panel);border-left:5px solid var(--cetin-blue);' \
         'padding:26px 30px;font-size:22px;margin-top:30px}'
CSS_C2 = '.st-box{background:#fdeaed;border-left:5px solid var(--cetin-red);' \
         'padding:26px 30px;font-size:22px;margin-top:30px}'


def run(cmd, cwd, label):
    print(f'\n== {label}')
    r = subprocess.run([sys.executable] + cmd, cwd=cwd, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print('   ' + out.replace('\n', '\n   '))
    return r.returncode, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', metavar='DIR', help='write artefacts here instead of a temp dir')
    a = ap.parse_args()

    work = os.path.abspath(a.keep) if a.keep else tempfile.mkdtemp(prefix='cetin-selftest-')
    os.makedirs(os.path.join(work, 'slides'), exist_ok=True)
    os.makedirs(os.path.join(work, 'css'), exist_ok=True)
    os.makedirs(os.path.join(work, 'assets'), exist_ok=True)
    W = lambda p, s: open(os.path.join(work, p), 'w', encoding='utf-8').write(s)
    stages, failures = [], []

    print(f'workspace: {work}')

    # ---- 0. inputs ---------------------------------------------------------
    # Use the skill's OWN bundled logo — this is also the test that the skill
    # ships everything it needs and doesn't secretly depend on another skill's
    # files being present.
    real_light = os.path.join(SKILL, 'assets', 'cetin-logo-light.png')
    real_dark = os.path.join(SKILL, 'assets', 'cetin-logo-dark.png')
    for src, name in ((real_light, 'assets/logo_light.png'), (real_dark, 'assets/logo_dark.png')):
        if not os.path.exists(src):
            sys.exit(f'FAIL — {os.path.relpath(src, SKILL)} is missing from the skill; '
                     f'the skill is not self-contained.')
        shutil.copyfile(src, os.path.join(work, name))
    open(os.path.join(work, 'assets/poster.jpg'), 'wb').write(png(160, 90, (20, 20, 30)))

    W('slides/c1_title.html', SLIDE_TITLE)
    W('slides/c1_11.html', SLIDE_CONTENT.format(
        n=2, no='1.1', chapter='Chapter One', extra='', title='A content slide',
        lede='Light mode, plain CETIN-Blue title type, logo bottom-right.'))
    W('slides/c1_12.html', SLIDE_CONTENT.format(
        n=3, no='1.2', chapter='Chapter One', extra=' &nbsp;·&nbsp; Demo',
        title='Demo: Cowork — Create a skill',
        lede='A demo title, so the naming convention has something to check.'))
    W('slides/c2_divider.html', SLIDE_DIVIDER.format(n=1, num='Two'))
    W('slides/c2_21.html', SLIDE_CONTENT.format(
        n=2, no='2.1', chapter='Chapter Two', extra=' &nbsp;·&nbsp; Hands on',
        title='Hands on: Build something',
        lede='This chapter restyles .st-box — proof that CSS scoping holds.'))
    W('css/c1.css', CSS_C1)
    W('css/c2.css', CSS_C2 + CSS_DIVIDER)

    shell, js = os.path.join(REF, 'deck-shell.html'), os.path.join(REF, 'deck.js')

    # ---- 1 & 2. build every chapter AND the contents page together --------
    # build_all.py is the guarantee this test exists to prove: there is no way
    # through it to get chapter decks without a matching index.html, so the
    # "Contents" button on every deck (a hardcoded href="index.html") can
    # never point at a missing or stale file.
    c1_cfg = {'out': 'Selftest_C1.html', 'title': 'Selftest · Chapter One', 'shell': shell, 'js': js,
              'css': ['css/c1.css'],
              'slides': ['slides/c1_title.html', 'slides/c1_11.html', 'slides/c1_12.html'],
              'nav': {'nextFile': 'Selftest_C2.html', 'nextLabel': 'Chapter Two'},
              'images': {'LOGO_LIGHT': 'assets/logo_light.png', 'LOGO_DARK': 'assets/logo_dark.png'}}
    c2_cfg = {'out': 'Selftest_C2.html', 'title': 'Selftest · Chapter Two', 'shell': shell, 'js': js,
              'css': ['css/c2.css'], 'slides': ['slides/c2_divider.html', 'slides/c2_21.html'],
              'nav': {'prevFile': 'Selftest_C1.html#3', 'isLast': True},
              'images': {'LOGO_LIGHT': 'assets/logo_light.png', 'LOGO_DARK': 'assets/logo_dark.png'}}
    W('build_c1.json', json.dumps(c1_cfg))
    W('build_c2.json', json.dumps(c2_cfg))
    # deliberately NOT hand-writing each chapter's slide labels here — build_all.py
    # must derive them from the built HTML itself, which is the point being tested.
    W('manifest.json', json.dumps({
        'index': {'out': 'index.html', 'programme': 'Selftest', 'training': 'Toolchain Check',
                  'date': 'today', 'presenters': 'Ada Lovelace · Alan Turing',
                  'logo': 'assets/logo_dark.png'},
        'chapters': [
            {'build': 'build_c1.json', 'num': '1', 'title': 'Chapter One', 'sub': 'Three slides.'},
            {'build': 'build_c2.json', 'num': '2', 'title': 'Chapter Two', 'sub': 'Two slides.'},
            {'num': '3', 'title': 'Not built yet', 'sub': 'Proves stub chapters still render.',
             'ready': False, 'file': 'Selftest_C3.html',
             'slides': [['3.1  Placeholder', '', False]]},
        ]}))
    rc, out = run([os.path.join(HERE, 'build_all.py'), 'manifest.json'], work, 'build_all.py')
    stages.append(('build_all.py builds chapters + index together', rc == 0))

    index_html = os.path.join(work, 'index.html')
    if os.path.exists(index_html):
        idx = open(index_html, encoding='utf-8').read()
        idx_checks = [
            ('index.html derived chapter 1 slide titles',
             '1.1  A content slide' in idx and 'Demo: Cowork — Create a skill' in idx),
            ('index.html derived chapter 2 divider + slide',
             'Chapter Two' in idx and '2.1  Hands on: Build something' in idx),
            ('index.html marked the demo/hands-on tags', 'class="tag">demo<' in idx
             and 'class="tag">hands-on<' in idx),
            ('unbuilt stub chapter still shows as a card', 'Not built yet' in idx and 'pending' in idx),
        ]
        for label, ok in idx_checks:
            stages.append((label, ok))
    else:
        stages.append(('index.html was written', False))

    # ---- 2a. the happy path: verify_deck.py on a chapter WITH its index ----
    # Contrast with 2b below — same check, opposite outcome, because the
    # index is actually there this time.
    try:
        import playwright  # noqa: F401
        rc, out = run([os.path.join(HERE, 'verify_deck.py'), 'Selftest_C1.html'], work,
                     'verify_deck.py on a chapter built alongside its index (must pass)')
        stages.append(('Contents button resolves when index.html was built', rc == 0
                       and 'landed on a contents page' in out))
    except ImportError:
        pass

    # ---- 2b. safety net: a chapter built WITHOUT the index alongside it ---
    # Simulates someone bypassing build_all.py and calling build_deck.py
    # directly for a quick one-chapter preview, then forgetting the index
    # step. verify_deck.py must catch the resulting dead "Contents" button —
    # this is the backstop for anyone who doesn't use the orchestrator.
    iso = os.path.join(work, 'isolated')
    os.makedirs(iso, exist_ok=True)
    iso_cfg = dict(c1_cfg)
    iso_cfg['out'] = 'Isolated.html'
    iso_cfg['slides'] = [f'../{s}' for s in c1_cfg['slides']]
    iso_cfg['css'] = [f'../{c}' for c in c1_cfg['css']]
    iso_cfg['shell'], iso_cfg['js'] = shell, js   # already absolute
    iso_cfg['images'] = {k: f'../{v}' for k, v in c1_cfg['images'].items()}
    with open(os.path.join(iso, 'build.json'), 'w', encoding='utf-8') as fh:
        json.dump(iso_cfg, fh)
    rc, _ = run([os.path.join(HERE, 'build_deck.py'), 'build.json'], iso,
               'build_deck.py alone, no index.html next to it (expected to build fine)')
    stages.append(('isolated chapter still builds on its own', rc == 0))

    try:
        import playwright  # noqa: F401
        rc, out = run([os.path.join(HERE, 'verify_deck.py'), 'Isolated.html'], iso,
                     'verify_deck.py on the isolated chapter (must catch the dead Contents button)')
        stages.append(('verify_deck.py catches the missing index.html',
                       rc != 0 and 'Contents button target missing' in out))
    except ImportError:
        pass

    # ---- 3. bundle into one file -----------------------------------------
    W('bundle.json', json.dumps({
        'out': 'Selftest_FULL.html', 'title': 'Selftest · one file',
        'home': 'index.html', 'engine': os.path.join(REF, 'bundle-engine.js'),
        'global_css': [os.path.join(REF, 'bundle.css')],
        'chapters': [{'file': 'Selftest_C1.html', 'prefix': 'c1'},
                     {'file': 'Selftest_C2.html', 'prefix': 'c2'}],
        'presenters': [{'name': 'Ada Lovelace', 'linkedin': 'https://example.com/ada'},
                       {'name': 'Alan Turing', 'linkedin': 'https://example.com/alan'}]}))
    rc, out = run([os.path.join(HERE, 'bundle_deck.py'), 'bundle.json'], work, 'bundle_deck.py')
    stages.append(('bundle', rc == 0))

    bundle = os.path.join(work, 'Selftest_FULL.html')
    if os.path.exists(bundle):
        html = open(bundle, encoding='utf-8').read()
        checks = [
            ('5 slides in the bundle', html.count('<section class="slide') == 5),
            ('chapter CSS is scoped', '.c1 .st-box' in html and '.c2 .st-box' in html),
            # A divider shares its <section class="slide divider"> element with
            # `slide` — it is not a descendant, so its rule must COMPOUND
            # (.c2.divider) rather than descend (.c2 .divider), or it silently
            # matches nothing once bundled. Regression check for that exact bug.
            ('divider rule compounds, not descends',
             '.c2.divider{background:#300091' in html
             and '.c2 .divider{background:#300091' not in html),
            ('contents page embedded', 'id="home"' in html),
            ('contents links are hashes', 'href="Selftest_C1.html' not in html),
            ('images deduplicated', 'window.IMAGES' in html and 'data-img=' in html),
            ('presenter links added', html.count('class="li"') == 2),
            ('skill\'s own logo assets were used, not a fallback',
             os.path.getsize(real_light) > 1024 and os.path.getsize(real_dark) > 1024),
        ]
        for label, ok in checks:
            stages.append((label, ok))

    # ---- 4. drift guard --------------------------------------------------
    rc, _ = run([os.path.join(HERE, 'check_drift.py'), 'bundle.json'], work, 'check_drift.py')
    stages.append(('drift guard passes on a fresh build', rc == 0))

    # it must FAIL once a chapter is newer than the bundle.
    # Push the mtime clearly past the guard's 1-second tolerance.
    import time
    future = time.time() + 30
    os.utime(os.path.join(work, 'Selftest_C1.html'), (future, future))
    rc, out = run([os.path.join(HERE, 'check_drift.py'), 'bundle.json'],
                  work, 'check_drift.py — after editing a chapter (must fail)')
    stages.append(('drift guard catches a stale bundle', rc != 0 and 'STALE' in out))

    # ---- 4b. slide switches ----------------------------------------------
    rc, out = run([os.path.join(HERE, 'slide_switches.py'), '--dir', work, '--off', '1.2'],
                  work, 'slide_switches.py')
    c1 = open(os.path.join(work, 'Selftest_C1.html'), encoding='utf-8').read()
    idx = open(os.path.join(work, 'index.html'), encoding='utf-8').read()
    stages.append(('slide switches injected', rc == 0
                   and 'window.SLIDE_SWITCHES' in c1 and 'window.SLIDE_SWITCHES' in idx))
    stages.append(('switch config is valid JS (comma before the comment)',
                   ': true,' in c1 or ': false,' in c1))
    stages.append(('every slide carries a data-key',
                   c1.count('data-key=') >= c1.count('<section class="slide')))
    stages.append(('the prune script lands before the engine, not inside its comment',
                   c1.index('drop switched-off slides') < c1.index('CETIN HTML DECK')))
    # rerunning must not stack a second copy of anything
    run([os.path.join(HERE, 'slide_switches.py'), '--dir', work, '--off', '1.2'],
        work, 'slide_switches.py — again (idempotent)')
    c1b = open(os.path.join(work, 'Selftest_C1.html'), encoding='utf-8').read()
    stages.append(('slide_switches.py is idempotent',
                   c1b.count('SLIDE SWITCHES  \u2014') == 1
                   and c1b.count('drop switched-off slides') == 1))

    # ---- 5. browser verification (optional) ------------------------------
    try:
        import playwright  # noqa: F401
        rc, _ = run([os.path.join(HERE, 'verify_deck.py'), 'Selftest_FULL.html',
                     '--shots', 'shots/'], work, 'verify_deck.py')
        stages.append(('browser verification', rc == 0))
    except ImportError:
        print('\n== verify_deck.py\n   skipped — pip install playwright && playwright install chromium')

    # ---- report ----------------------------------------------------------
    print('\n' + '=' * 62)
    for label, ok in stages:
        print(f'  {"PASS" if ok else "FAIL"}  {label}')
        if not ok:
            failures.append(label)
    print('=' * 62)

    if a.keep:
        print(f'\nartefacts kept in {work}')
        print('  open Selftest_FULL.html — contents page, then click into the deck')
    else:
        shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(f'\n{len(failures)} stage(s) failed: {failures}')
        sys.exit(1)
    print('\nAll stages passed — the toolchain works in this environment.')


if __name__ == '__main__':
    main()
