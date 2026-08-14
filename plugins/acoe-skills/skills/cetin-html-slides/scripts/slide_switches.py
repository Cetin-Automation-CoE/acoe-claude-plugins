#!/usr/bin/env python3
"""Add per-slide on/off switches to every built HTML file in a deck.

Each file gets, at the very top of <head>:

    window.SLIDE_SWITCHES = { "1.1": true, "2.3": false, ... };

Flip a value to false and that slide disappears completely — from the deck, the
numbering, the arrows, the chapter divider's own agenda list, and the contents page.

    python3 scripts/slide_switches.py                 # every deck next to index.html
    python3 scripts/slide_switches.py --dir build/    # somewhere else
    python3 scripts/slide_switches.py --off 2.3 2.9   # ship these switched off

Run it after build_all.py (and after bundle_deck.py, if you bundled). It is
idempotent: running it again strips its own previous output first.

Defaults belong in DISABLED below, not only in the generated HTML — otherwise the
next rebuild silently switches everything back on.
"""
import argparse
import glob
import os
import re
import sys

# Slides that ship switched OFF for this deck. Editing the built HTML works too,
# but only this survives a rebuild.
DISABLED = set()

SECTION_RE = re.compile(r'<section class="slide([^"]*)" data-slide="(\d+)"([^>]*)>')

# The engine's own comment header contains the literal text "<script>", so anchoring
# on the last "<script>" lands the injection inside a comment and truncates the engine.
ENGINE_RE = re.compile(r'<script>\s*/\* =+\s*\n\s*(?:CETIN HTML DECK|SINGLE-FILE DECK ENGINE)')

CONFIG_HEAD = """
<!-- ============================================================
     SLIDE SWITCHES  —  flip any value to false to hide that slide
     completely (deck, numbering, arrows, divider agenda, contents).
     ============================================================ -->
<script>
window.SLIDE_SWITCHES = {
%s
};
</script>
"""

PRUNE_DECK = """<script>
/* drop switched-off slides before the engine runs, then renumber */
(function () {
  var cfg = window.SLIDE_SWITCHES || {}, n = 0;
  Array.prototype.slice.call(document.querySelectorAll('section.slide')).forEach(function (s) {
    if (cfg[s.getAttribute('data-key')] === false) { s.parentNode.removeChild(s); return; }
    s.setAttribute('data-slide', ++n);
  });
  /* the chapter dividers list their own slides — drop the switched-off rows too */
  Array.prototype.slice.call(document.querySelectorAll('.div-agenda .ag')).forEach(function (a) {
    if (cfg[a.getAttribute('data-key')] === false) { a.parentNode.removeChild(a); }
  });
  /* a bundled single file carries its own contents page */
  Array.prototype.slice.call(document.querySelectorAll('#home ul.slides > li')).forEach(function (li) {
    if (cfg[li.getAttribute('data-key')] === false) { li.parentNode.removeChild(li); }
  });
})();
</script>"""

PRUNE_INDEX = """<script>
/* hide switched-off slides from the contents page and repair the deep links */
(function () {
  var cfg = window.SLIDE_SWITCHES || {}, total = 0;
  Array.prototype.slice.call(document.querySelectorAll('.deck')).forEach(function (deck) {
    var kept = 0;
    Array.prototype.slice.call(deck.querySelectorAll('ul.slides > li')).forEach(function (li) {
      if (cfg[li.getAttribute('data-key')] === false) { li.parentNode.removeChild(li); return; }
      kept++;
      var a = li.querySelector('a'), num = li.querySelector('.n');
      if (a) { a.setAttribute('href', a.getAttribute('href').split('#')[0] + '#' + kept); }
      if (num) { num.textContent = (kept < 10 ? '0' : '') + kept; }
    });
    total += kept;
    var badge = deck.querySelector('.badge');
    if (badge) { badge.innerHTML = kept + ' slides &middot; ready'; }
    if (!kept) { deck.style.display = 'none'; }
  });
  var spans = document.querySelectorAll('.hero-meta span');
  for (var i = 0; i < spans.length; i++) {
    if (/slides/.test(spans[i].textContent)) {
      var b = spans[i].querySelector('b');
      if (b) { b.textContent = total; }
      break;
    }
  }
})();
</script>"""


def slide_keys(html):
    """(key, label) for every slide in a built deck, in document order.

    Keys are the slide id (2.7) where the deck prints one, else topic-N for a chapter
    divider and title for the title slide. A deck whose slides carry no visible id still
    has to get unique keys — otherwise switching one off would hide several — so anything
    that would collide falls back to its position (s4, s5, ...).
    """
    out, used = [], set()
    for pos, chunk in enumerate(html.split('<section class="slide')[1:], start=1):
        body = chunk.split('</section>')[0]
        m = re.search(r'<div class="slide-no">([^<]*)</div>', body)
        no = (m.group(1).strip() if m else '')
        div = re.search(r'<div class="div-num">([^<]*)</div>', body)
        h1 = re.search(r'<h1 class="title[^"]*"[^>]*>(.*?)</h1>', body, re.S)
        label = re.sub(r'<[^>]+>', ' ', h1.group(1)) if h1 else ''
        label = ' '.join(re.sub(r'&[a-z]+;', ' ', label).split())
        if no:
            key = no
        elif div:
            key, label = 'topic-' + div.group(1).strip(), (label or 'chapter divider')
        elif pos == 1:
            key, label = 'title', (label or 'title slide')
        else:
            key = 's%d' % pos
        if key in used:
            key = 's%d' % pos
        used.add(key)
        out.append((key, label or ('slide %d' % pos)))
    return out


def _config_block(keys, disabled):
    width = max(len(k) for k, _ in keys) + 2
    return CONFIG_HEAD % '\n'.join(
        '  %-*s : %-6s%s' % (width, '"%s"' % k,
                             ('false,' if k in disabled else 'true,'),
                             ('   // ' + lab) if lab else '')
        for k, lab in keys)


def _strip_previous(html, li=False):
    html = re.sub(r'\n<!-- =+\n *SLIDE SWITCHES.*?</script>\n', '\n', html, flags=re.S)
    html = re.sub(r'<script>\n/\* (?:drop|hide) switched-off slides.*?</script>\n?', '', html, flags=re.S)
    if li:
        html = re.sub(r'(<li(?: class="[^"]*")?) data-key="[^"]*"', r'\1', html)
    return re.sub(r'(<section class="slide[^"]*" data-slide="\d+") data-key="[^"]*"', r'\1', html)


def patch_deck(path, keys, disabled):
    html = _strip_previous(open(path, encoding='utf-8').read())
    i = [0]

    def add_key(m):
        k = keys[i[0]][0]
        i[0] += 1
        return '<section class="slide%s" data-slide="%s" data-key="%s"%s>' % (
            m.group(1), m.group(2), k, m.group(3))

    html = SECTION_RE.sub(add_key, html)
    # the chapter dividers carry their own agenda list — tag each row with its slide
    html = re.sub(r'<div class="ag">(\d+\.\d+)',
                  lambda m: '<div class="ag" data-key="%s">%s' % (m.group(1), m.group(1)), html)
    html = html.replace('<head>', '<head>' + _config_block(keys, disabled), 1)

    m = ENGINE_RE.search(html)
    if not m:
        print('  skipped %s — no deck engine found' % os.path.basename(path))
        return 0
    html = html[:m.start()] + PRUNE_DECK + '\n' + html[m.start():]
    open(path, 'w', encoding='utf-8').write(html)
    return len(keys)


def patch_index(path, keys_by_file, disabled):
    html = _strip_previous(open(path, encoding='utf-8').read(), li=True)

    def add_key(m):
        li_open, href, num = m.group(1), m.group(2), int(m.group(3))
        keys = keys_by_file.get(os.path.basename(href), [])
        key = keys[num - 1][0] if num - 1 < len(keys) else ''
        return '%s data-key="%s"><a href="%s#%d"' % (li_open, key, href, num)

    html = re.sub(r'(<li(?: class="[^"]*")?)><a href="([^"#]+)#(\d+)"', add_key, html)

    all_keys, seen = [], set()
    for f in sorted(keys_by_file):
        for k, lab in keys_by_file[f]:
            if k not in seen:
                seen.add(k)
                all_keys.append((k, lab))
    html = html.replace('<head>', '<head>' + _config_block(all_keys, disabled), 1)
    html = html.replace('</body>', PRUNE_INDEX + '\n</body>', 1)
    open(path, 'w', encoding='utf-8').write(html)
    return len(all_keys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='.', help='folder holding the built HTML files')
    ap.add_argument('--off', nargs='*', default=[], help='slide keys to ship switched off')
    a = ap.parse_args()
    disabled = DISABLED | set(a.off)

    decks = [p for p in sorted(glob.glob(os.path.join(a.dir, '*.html')))
             if os.path.basename(p) != 'index.html']
    keys_by_file = {}
    for p in decks:
        html = open(p, encoding='utf-8').read()
        if '<section class="slide' not in html:
            continue
        keys_by_file[os.path.basename(p)] = slide_keys(html)
    for p in decks:
        name = os.path.basename(p)
        if name in keys_by_file:
            print('%-48s %2d switches' % (name, patch_deck(p, keys_by_file[name], disabled)))
    idx = os.path.join(a.dir, 'index.html')
    if os.path.exists(idx):
        print('%-48s %2d switches' % ('index.html', patch_index(idx, keys_by_file, disabled)))
    if disabled:
        print('switched off: ' + ', '.join(sorted(disabled)))


if __name__ == '__main__':
    main()
