#!/usr/bin/env python3
"""Verify a built deck: screenshots, overflow, overlap, images, distortion, switches, links.

Never hand over a deck that hasn't been through this. scrollHeight checks alone miss
panels that visually cover each other, so it also writes a PNG per slide — look at them.

    pip install playwright && playwright install chromium
    python3 verify_deck.py DunAI_Topic3.html --shots shots/
    python3 verify_deck.py index.html --index
"""
import argparse, asyncio, os, re, sys


async def verify_deck(path, shots, phone=True):
    from playwright.async_api import async_playwright
    url = 'file://' + os.path.abspath(path)
    if shots:
        os.makedirs(shots, exist_ok=True)
    problems = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox', '--font-render-hinting=none'])
        pg = await b.new_page(viewport={'width': 1280, 'height': 720}, device_scale_factor=1.4)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type == 'error' else None)
        await pg.goto(url)
        await pg.wait_for_timeout(2400)
        n = await pg.evaluate("() => document.querySelectorAll('.slide').length")

        # A bundled single file opens on its contents page, so there is no active
        # slide until we enter the deck — and stepping with ArrowRight would just
        # scroll that page. Detect it and drive by hash instead.
        bundled = await pg.evaluate("() => !!document.getElementById('home')")
        if bundled:
            await pg.evaluate("() => { location.hash = '1'; }")
            await pg.wait_for_timeout(900)
        print(f'{os.path.basename(path)}: {n} slides'
              + ('  (bundled single file)' if bundled else ''))

        # Every chapter deck's "Contents" button is a hardcoded href to index.html
        # (see references/deck-shell.html). If chapters get built without index.html
        # being (re)built alongside them, that button quietly 404s the moment someone
        # clicks it. A bundled file's home button is `#home` (an in-page anchor, not
        # a file) and is exempt.
        home_href = await pg.evaluate(
            "() => { const a = document.querySelector('.home-btn'); return a && a.getAttribute('href'); }")
        if home_href and not home_href.startswith('#'):
            target = os.path.join(os.path.dirname(os.path.abspath(path)), home_href.split('#')[0])
            if not os.path.exists(target):
                msg = (f'Contents button target missing: href="{home_href}" does not exist '
                      f'next to this file. Home navigation will error the moment someone clicks it '
                      f'— (re)build the contents page (build_all.py or make_index.py) before sharing.')
                print(f'  {msg}')
                problems.append(('home-btn', [msg]))

        for i in range(1, n + 1):
            if bundled:
                await pg.evaluate(f"() => {{ location.hash = '{i}'; }}")
                await pg.wait_for_timeout(700)
            if shots:
                await pg.screenshot(path=os.path.join(shots, f's{i:02d}.png'))
            d = await pg.evaluate("""() => {
              const s = document.querySelector('.slide.active');
              if (!s) return {n: '?', issues: ['no active slide'], past: null,
                              imgs: 0, broken: 0, chromeClash: false};
              const out = [];
              s.querySelectorAll('*').forEach(el => {
                if (el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0)
                  out.push('V ' + (el.className || el.tagName) + ' ' + el.scrollHeight + '>' + el.clientHeight);
                if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0)
                  out.push('H ' + (el.className || el.tagName) + ' ' + el.scrollWidth + '>' + el.clientWidth);
              });
              const pad = s.querySelector('.pad');
              let past = null;
              if (pad && pad.lastElementChild)
                past = Math.round(pad.lastElementChild.getBoundingClientRect().bottom
                                  - pad.getBoundingClientRect().bottom);
              const imgs = [...s.querySelectorAll('img')].filter(x =>
                !x.className.includes('logo-'));
              // an image whose rendered box does not match its natural aspect ratio has
              // been squashed — almost always a fixed height plus a max-width cap
              const squashed = imgs.filter(x => {
                if (!x.naturalWidth || !x.naturalHeight) return false;
                const r = x.getBoundingClientRect();
                if (r.width < 8 || r.height < 8) return false;
                // object-fit:contain / scale-down letterbox inside their box on purpose —
                // the box ratio is allowed to differ from the image's, nothing is stretched
                const fit = getComputedStyle(x).objectFit;
                if (fit === 'contain' || fit === 'scale-down' || fit === 'none') return false;
                return Math.abs((r.width / r.height) - (x.naturalWidth / x.naturalHeight)) > 0.03;
              }).map(x => {
                // images are embedded as data URIs, so the src tail is useless — use alt,
                // then the class, then the position on the slide
                const r = x.getBoundingClientRect();
                const who = x.alt || x.className || ('img ' + (imgs.indexOf(x) + 1));
                return who.slice(0, 30) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height);
              });
              const eb = s.querySelector('.eyebrow');
              const hb = document.querySelector('.home-btn');
              return {n: s.dataset.slide, issues: out.slice(0, 4), past, squashed,
                      imgs: imgs.length, broken: imgs.filter(x => !x.naturalWidth).length,
                      chromeClash: (eb && hb) ? hb.getBoundingClientRect().bottom
                                                > eb.getBoundingClientRect().top : false};
            }""")
            flags = []
            if d['issues']:            flags.append(f"overflow {d['issues']}")
            if d['past'] and d['past'] > 2: flags.append(f"content {d['past']}px past pad")
            if d['broken']:            flags.append(f"{d['broken']} broken image(s)")
            if d.get('squashed'):      flags.append(f"distorted image(s): {d['squashed']}")
            if d['chromeClash']:       flags.append('chrome overlaps eyebrow')
            line = f"  slide {d['n']:>3}  imgs={d['imgs']}"
            print(line + ('   <-- ' + ' | '.join(flags) if flags else ''))
            if flags:
                problems.append((d['n'], flags))
            if i < n and not bundled:
                await pg.keyboard.press('ArrowRight')
                await pg.wait_for_timeout(1150)
        if phone:
            await pg.set_viewport_size({'width': 390, 'height': 844})
            await pg.wait_for_timeout(600)
            if bundled:   # make sure we are measuring the stage, not the contents page
                await pg.evaluate("() => { location.hash = '1'; }")
                await pg.wait_for_timeout(500)
            r = await pg.evaluate("""() => {const b=document.getElementById('stage').getBoundingClientRect();
                                        return +(b.width/b.height).toFixed(4);}""")
            ok = abs(r - 1.7778) < 0.002
            print(f'  phone stage ratio {r} {"OK" if ok else "<-- NOT 16:9"}')
            if not ok:
                problems.append(('phone', [f'ratio {r}']))
            await pg.set_viewport_size({'width': 1280, 'height': 720})

        # Actually click Contents and confirm it lands somewhere real, rather
        # than just checking the file exists — a stale or empty index.html
        # would pass the file-exists check but still be a broken experience.
        if not bundled and home_href and not home_href.startswith('#') \
           and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(path)), home_href.split('#')[0])):
            await pg.evaluate("() => { location.hash = '1'; }")
            await pg.wait_for_timeout(300)
            nav_errs = []
            pg.on('requestfailed', lambda r: nav_errs.append(r.url))
            await pg.click('.home-btn')
            await pg.wait_for_timeout(500)
            landed = await pg.evaluate("() => !!document.querySelector('.hero, .decks, #home')")
            print(f'  Contents button -> {"OK, landed on a contents page" if landed else "FAILED"}')
            if not landed or nav_errs:
                problems.append(('home-btn-click', [f'landed={landed}', f'failed requests={nav_errs}']))
        sw = await pg.evaluate("""() => {
          if (!window.SLIDE_SWITCHES) return null;
          const cfg = window.SLIDE_SWITCHES;
          const live = [...document.querySelectorAll('section.slide')]
                         .map(s => s.getAttribute('data-key'));
          const off  = Object.keys(cfg).filter(k => cfg[k] === false);
          return {total: Object.keys(cfg).length, off,
                  ghosts: live.filter(k => cfg[k] === false)};
        }""")
        if sw:
            print(f"  slide switches: {sw['total']} keys, {len(sw['off'])} off"
                  + (f" ({', '.join(sw['off'])})" if sw['off'] else ''))
            if sw['ghosts']:
                print('  switched-off slides still in the DOM:', sw['ghosts'])
                problems.append(('switches', sw['ghosts']))

        if errs:
            print('  JS errors:', errs[:5]); problems.append(('js', errs[:5]))
        await b.close()
    return problems


async def verify_index(path):
    from playwright.async_api import async_playwright
    root = os.path.dirname(os.path.abspath(path))
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 1440, 'height': 1000})
        await pg.goto('file://' + os.path.abspath(path))
        await pg.wait_for_timeout(800)
        links = await pg.evaluate("() => [...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))")
        bad = [h for h in links if h and not h.startswith(('http', 'mailto'))
               and not os.path.exists(os.path.join(root, h.split('#')[0]))]
        print(f'{os.path.basename(path)}: {len(links)} links, broken: {bad or "none"}')
        # deep links must be inside each deck's range
        over = []
        for f in {h.split('#')[0] for h in links if '#' in h}:
            fp = os.path.join(root, f)
            if not os.path.exists(fp):
                continue
            total = len(re.findall(r'data-slide="\d+"', open(fp, encoding='utf-8').read()))
            for h in [x for x in links if x.startswith(f + '#')]:
                if int(h.split('#')[1]) > total:
                    over.append(h)
        print('  out-of-range deep links:', over or 'none')
        await b.close()
    return bad + over


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--shots'); ap.add_argument('--index', action='store_true')
    a = ap.parse_args()
    issues = asyncio.run(verify_index(a.file) if a.index else verify_deck(a.file, a.shots))
    if issues:
        print('\nFAILED — fix the above, rebuild, re-verify.'); sys.exit(1)
    print('\nAll checks passed.')
