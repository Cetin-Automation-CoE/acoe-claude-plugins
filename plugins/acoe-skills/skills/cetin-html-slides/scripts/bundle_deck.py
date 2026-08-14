#!/usr/bin/env python3
"""Bundle the chapter decks into ONE shareable HTML file.

Why this exists: a presenter wants chapter files (fast to edit, easy to reorder,
easy to hand a co-presenter); an attendee wants one file they can double-click.
Maintaining both by hand guarantees they drift. So the chapter files stay the
source and this generates the single file from them — always, never by hand.

    bundle.json
    {
      "out":        "Deck_FULL.html",
      "title":      "DunAI — AI Exec Training · 29 July 2026",
      "home":       "index.html",
      "engine":     "references/bundle-engine.js",
      "global_css": ["references/bundle.css"],
      "chapters": [
        {"file": "Deck_Topics1-2.html", "prefix": "c12"},
        {"file": "Deck_Topic3.html",    "prefix": "c3"}
      ],
      "presenters": [{"name": "Jiri Forman", "linkedin": "https://…"}],
      "video_substitutions": [
        {"match_video": "demo.mp4", "anchor": "videowrap",
         "embed": "https://www.youtube.com/embed/ID", "poster": "assets/poster.jpg",
         "link": "https://youtu.be/ID", "link_text": "Watch the demo"},
        {"match_video": "assets/chart.mp4", "anchor": "vidcap",
         "still": "assets/chart-final.png",
         "link": "https://example.org/live", "link_text": "See the live chart"}
      ]
    }

    python3 bundle_deck.py bundle.json

Every `prefix` MUST be unique: it scopes that chapter's CSS so chapters cannot
restyle each other (see cssmerge.py). It is also stamped onto each slide element.
"""
import base64, io, json, mimetypes, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cssmerge

LI_ICON = ('<svg class="li-ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
           '<path d="M6.94 5a1.94 1.94 0 1 1-3.88 0 1.94 1.94 0 0 1 3.88 0zM3.3 8.4h3.4V21H3.3V8.4z'
           'm5.5 0h3.26v1.72h.05c.45-.86 1.56-1.77 3.21-1.77 3.43 0 4.06 2.26 4.06 5.2V21h-3.4v-6.06'
           'c0-1.44-.26-2.9-2-2.9-1.72 0-1.98 1.24-1.98 2.82V21H8.8V8.4z"/></svg>')
PLAY_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
             'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/>'
             '<path d="M10 8.5l6 3.5-6 3.5z"/></svg>')


def die(msg):
    sys.exit(f'BUNDLE FAILED — {msg}')


def must(ok, label):
    if not ok:
        die(label)


def slides_of(html):
    return re.findall(r'<section class="slide.*?</section>', html, re.S)


def styles_of(html):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.S))


def after_div(html, cls):
    """Index just past the BALANCED </div> closing <div class="cls…">.

    A non-greedy `.*?</div>` stops at the first nested close instead, which
    silently drops whatever you are inserting INSIDE the wrapper — it then lays
    out as a flex sibling of the media rather than beneath it. Costly to spot.
    """
    m = re.search(r'<div class="' + cls + r'[^"]*"[^>]*>', html)
    if not m:
        return None
    depth = 1
    for t in re.finditer(r'<(/?)div\b[^>]*>', html[m.end():]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return m.end() + t.end()
    return None


def inline_assets(html, root, who):
    """Turn assets/foo.png references into data URIs so the file stands alone."""
    def rep(m):
        pre, path, post = m.group(1), m.group(2), m.group(3)
        p = os.path.join(root, path)
        if not os.path.exists(p):
            die(f'{who} references a missing asset: {path}')
        mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(p, 'rb') as fh:
            return f'{pre}data:{mime};base64,{base64.b64encode(fh.read()).decode()}{post}'
    return re.sub(r'(src=")((?!data:|https?:|#)[^"]+\.(?:png|jpe?g|gif|svg|webp))(")', rep, html)


def substitute_videos(slide, subs, root):
    """Swap local <video> for something that survives having no network.

    A bare YouTube iframe is a blank white box the moment the room's network
    blocks it — so ship a local poster with a play badge and only create the
    iframe on click (bundle-engine.js does that).
    """
    for sub in subs:
        if sub['match_video'] not in slide:
            continue
        link = (f'<a class="vidlink anim a-fade d6" href="{sub["link"]}" target="_blank" '
                f'rel="noopener">{PLAY_ICON}<span>{sub["link_text"]}</span></a>')

        if 'embed' in sub:
            with open(os.path.join(root, sub['poster']), 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode()
            mime = mimetypes.guess_type(sub['poster'])[0]
            slide, k = re.subn(
                r'<video[^>]*>(?:.*?</video>)?',
                f'<div class="ytbox" data-embed="{sub["embed"]}">'
                f'<img src="data:{mime};base64,{b64}" alt="{sub["link_text"]}">'
                f'<button class="ytplay" type="button" aria-label="{sub["link_text"]}">'
                f'<svg viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="38"/>'
                f'<path d="M32 25l24 15-24 15z"/></svg></button></div>',
                slide, count=1, flags=re.S)
            must(k == 1, f'no <video> to replace for {sub["match_video"]}')
        else:
            with open(os.path.join(root, sub['still']), 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode()
            mime = mimetypes.guess_type(sub['still'])[0]
            # replace only the inner media block; the outer wrapper must stay closed
            slide, k = re.subn(
                r'<div class="vidreal"[^>]*>\s*<video.*?</video>\s*</div>|<video.*?</video>',
                f'<img src="data:{mime};base64,{b64}" alt="{sub["link_text"]}" '
                f'style="width:100%;height:100%;object-fit:contain">',
                slide, count=1, flags=re.S)
            must(k == 1, f'no <video> to replace for {sub["match_video"]}')

        at = after_div(slide, sub['anchor'])
        must(at is not None, f'anchor .{sub["anchor"]} not found for {sub["match_video"]}')
        slide = slide[:at] + '\n        ' + link + slide[at:]
    return slide


def recompress(raw):
    """Shrink an image, keeping alpha only for small marks like the logo."""
    try:
        from PIL import Image
    except ImportError:
        return raw, None
    try:
        im = Image.open(io.BytesIO(raw))
    except Exception:
        return raw, None
    alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    if im.size[0] > 1500:
        im = im.resize((1500, round(1500 * im.size[1] / im.size[0])), Image.LANCZOS)
    buf = io.BytesIO()
    if alpha and im.size[0] <= 1000:
        im.convert('RGBA').save(buf, 'PNG', optimize=True)
        mime = 'image/png'
    else:
        if alpha:
            bg = Image.new('RGB', im.size, (255, 255, 255))
            rgba = im.convert('RGBA')
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        im.convert('RGB').save(buf, 'JPEG', quality=72, optimize=True, progressive=True)
        mime = 'image/jpeg'
    out = buf.getvalue()
    return (out, mime) if len(out) < len(raw) else (raw, None)


def externalise_images(slides):
    """Deduplicate every data: URI into one JS map.

    The logo alone repeats on every slide; at 50 slides that is most of the file.
    """
    store, order, before, after = {}, [], 0, 0

    def rep(m):
        nonlocal before, after
        head, _, b64 = m.group(1).partition(',')
        raw = base64.b64decode(b64)
        key = hash(raw)
        if key not in store:
            new, mime = recompress(raw)
            before += len(raw)
            after += len(new)
            token = f'IMG{len(order)}'
            uri = (f'data:{mime};base64,' + base64.b64encode(new).decode()) if mime \
                else head + ',' + base64.b64encode(new).decode()
            store[key] = token
            order.append((token, uri))
        return f'data-img="{store[key]}" src=""'

    out = [re.sub(r'src="(data:image/[^"]+)"', rep, s) for s in slides]
    if before:
        print(f'  images: {len(order)} unique, {before // 1024} kB -> {after // 1024} kB '
              f'({100 - after * 100 // before}% smaller)')
    return out, order


def main(cfg_path):
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    root = os.path.dirname(os.path.abspath(cfg_path)) or '.'
    rel = lambda p: p if os.path.isabs(p) else os.path.join(root, p)

    prefixes = [c['prefix'] for c in cfg['chapters']]
    must(len(prefixes) == len(set(prefixes)), f'duplicate chapter prefix in {prefixes}')

    # ---- read the chapters ------------------------------------------------
    chapters, abs_map, total = [], {}, 0
    for ch in cfg['chapters']:
        p = rel(ch['file'])
        if not os.path.exists(p):
            die(f'chapter file missing: {ch["file"]}')
        html = inline_assets(open(p, encoding='utf-8').read(), root, ch['file'])
        sl = slides_of(html)
        must(bool(sl), f'no slides found in {ch["file"]}')
        for i in range(len(sl)):
            total += 1
            abs_map[(ch['file'], i + 1)] = total
        chapters.append((ch, sl, html))
        print(f'  {ch["file"]:<44} {len(sl):>2} slides  -> .{ch["prefix"]}')
    print(f'  total: {total} slides')

    # ---- CSS: chapter styles scoped, shared sheets global -----------------
    # root_classes covers rules like `.divider{…}` that target the slide
    # element itself (its <section class="slide divider">) rather than a
    # descendant — without this a divider rule scopes as `.c1 .divider`, a
    # descendant selector that can never match, and silently loses its
    # background/title colour the moment it is bundled.
    css = cssmerge.collect([(f'.{ch["prefix"]}', styles_of(html), cssmerge.slide_root_classes(html))
                            for ch, _, html in chapters])
    for extra in cfg.get('global_css', []):
        css += '\n' + open(rel(extra), encoding='utf-8').read()

    # ---- slides: stamp chapter class, renumber, substitute video ----------
    subs = cfg.get('video_substitutions', [])
    all_slides, n = [], 0
    for ch, sl, _ in chapters:
        for s in sl:
            n += 1
            s = re.sub(r'<section class="slide', f'<section class="slide {ch["prefix"]}', s, count=1)
            s = re.sub(r'data-slide="\d+"', f'data-slide="{n}"', s, count=1)
            all_slides.append(substitute_videos(s, subs, root))

    # ---- presenter LinkedIn links (idempotent) ----------------------------
    people = cfg.get('presenters', [])
    if people:
        for i, s in enumerate(all_slides):
            # `names` may sit anywhere in the class list, e.g. "title-people names anim"
            m = re.search(r'<div class="[^"]*\bnames\b[^"]*"[^>]*>(.*?)</div>', s, re.S)
            if not m:
                continue
            if 'class="li"' in m.group(0):
                for person in people:
                    must(person['linkedin'] in m.group(0),
                         f'title slide is missing the LinkedIn URL for {person["name"]}')
                print('  presenter links: already in the chapter source, verified')
            else:
                block = m.group(1)
                for person in people:
                    must(person['name'] in block, f'{person["name"]} not on the title slide')
                    block = block.replace(
                        person['name'],
                        f'<a class="li" href="{person["linkedin"]}" target="_blank" '
                        f'rel="noopener"><span>{person["name"]}</span>{LI_ICON}</a>', 1)
                all_slides[i] = s.replace(m.group(1), block, 1)
                print('  presenter links: injected')
            break

    all_slides, images = externalise_images(all_slides)

    # ---- home view: reuse the contents page, rewrite its links to #abs ----
    home_body = home_css = ''
    if cfg.get('home'):
        idx = open(rel(cfg['home']), encoding='utf-8').read()
        idx = inline_assets(idx, root, cfg['home'])
        home_body = re.search(r'<body[^>]*>(.*)</body>', idx, re.S).group(1)
        home_css = cssmerge.scope_all(
            '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', idx, re.S)), '#home')
        home_body = re.sub(
            r'href="([^"#]+\.html)#(\d+)"',
            lambda m: f'href="#{abs_map[(m.group(1), int(m.group(2)))]}"'
            if (m.group(1), int(m.group(2))) in abs_map else m.group(0), home_body)
        home_body = re.sub(
            r'href="([^"#]+\.html)"',
            lambda m: f'href="#{abs_map.get((m.group(1), 1), 1)}"', home_body)
        left = re.findall(r'href="[^"#]+\.html', home_body)
        if left:
            print(f'  ! {len(left)} contents link(s) still point at a file: {left[:3]}')

    # ---- shell ------------------------------------------------------------
    first = chapters[0][2]
    chrome = re.search(r'(<div class="rail".*?)<div class="deck-viewport"', first, re.S)
    chrome = re.sub(r'<a class="home-btn".*?</a>', '', chrome.group(1), flags=re.S) if chrome else ''
    controls = re.search(r'(<div class="deck-controls".*?</div>\s*</div>)', first, re.S)
    engine = open(rel(cfg['engine']), encoding='utf-8').read()
    imgs = ',\n'.join(f'  {t}: {json.dumps(u)}' for t, u in images)

    # Assemble these OUTSIDE the f-string. Nesting a triple-quoted string inside
    # an f-string expression terminates the f-string early on Python < 3.12.
    HOME_BTN = (
        '<a class="home-btn" href="#home" id="homeBtn" title="Back to contents">\n'
        '  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1"\n'
        '       stroke-linecap="round" stroke-linejoin="round">\n'
        '    <path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V20h13V9.5"/>'
        '<path d="M10 20v-6h4v6"/>\n'
        '  </svg>\n  Contents\n</a>')
    body_class = ' class="home-open"' if home_body else ''
    home_div = f'<div id="home">{home_body}</div>' if home_body else ''
    home_btn = HOME_BTN if home_body else ''
    home_block = ('/* ---- contents page ---- */\n' + home_css) if home_css else ''
    controls_html = controls.group(1) if controls else ''
    slides_html = ''.join(all_slides)

    out = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{cfg["title"]}</title>
<style>
{css}
{home_block}
</style>
</head>
<body{body_class}>
{home_div}
{home_btn}
{chrome}
<div class="deck-viewport" id="viewport">
  <div class="deck-stage" id="stage">
{slides_html}
  </div>
</div>
{controls_html}
<script>
window.IMAGES = {{
{imgs}
}};
</script>
<script>
{engine}
</script>
</body>
</html>
'''
    dest = rel(cfg['out'])
    with open(dest, 'w', encoding='utf-8') as fh:
        fh.write(out)
    size_mb = os.path.getsize(dest) / 1048576
    print(f'  {os.path.basename(dest)}  {size_mb:.2f} MB  ({total} slides, {len(images)} images)')
    print('  generated — do not hand-edit; rerun this script instead.')

    # A file this size is awkward to email and slow to open. 5 MB is a rough
    # line: comfortably attachable, opens instantly. Flag it rather than
    # silently shipping something unwieldy, and name the concrete levers.
    if size_mb > 5:
        print(f'\n  ! {size_mb:.1f} MB is over the ~5 MB comfort line for a single emailable file. Options:')
        print('    - link video externally instead of embedding it (video_substitutions in the manifest —')
        print('      already the default for anything that was a local .mp4)')
        print('    - compress images harder: lower JPEG quality or a smaller max width in recompress()')
        print('    - keep the split per-chapter files + index.html instead of one bundle — no size limit,')
        print('      just not a single file to email')
    elif size_mb > 3:
        print(f'\n  note: {size_mb:.1f} MB — comfortably under 5 MB, no action needed.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
