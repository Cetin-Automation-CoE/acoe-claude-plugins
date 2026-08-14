#!/usr/bin/env python3
"""Assemble one chapter deck from fragments, substitute tokens, inline images.

Fragments keep each slide small enough to edit safely and let you rebuild in seconds.

    build.json
    {
      "out":    "DunAI_Topic3.html",
      "title":  "DunAI — AI Exec Training · Topic 3: Prompting",
      "shell":  "references/deck-shell.html",
      "js":     "references/deck.js",
      "css":    ["css/components.css", "css/topic3.css"],
      "slides": ["slides/t3_divider.html", "slides/t3_31.html"],
      "nav":    {"nextFile": "DunAI_Topic4.html",
                 "nextLabel": "Topic 4 · Limits",
                 "prevFile": "DunAI_Topic1-2.html#13"},
      "images": {"LOGO_LIGHT": "assets/logo_light.png",
                 "IMG_CHART":  "assets/chart.jpg"}
    }

    python3 build_deck.py build.json
"""
import json, mimetypes, os, re, sys, base64


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def build(cfg_path):
    cfg = json.load(open(cfg_path))
    root = os.path.dirname(os.path.abspath(cfg_path))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(root, p)

    shell = open(rel(cfg['shell']), encoding='utf-8').read()
    # split the shell on its markers
    head, rest = shell.split('<!-- ============================ BODY_OPEN ============================ -->')
    _, tail   = rest.split('<!-- ============================ BODY_CLOSE =========================== -->')
    # strip the shell's own leading comment block
    head = head[head.index('<!DOCTYPE html>'):]

    components = '\n'.join(open(rel(c), encoding='utf-8').read() for c in cfg.get('css', []))
    head = replace_once(head, '/* COMPONENT_CSS', components + '\n/* COMPONENT_CSS')

    body = ''.join(open(rel(s), encoding='utf-8').read() for s in cfg['slides'])

    js = open(rel(cfg['js']), encoding='utf-8').read()
    tail = replace_once(tail, '<script src="deck.js"></script>',
                        '<script>\n' + js + '\n</script>')
    tail = tail.replace('<!-- inline the contents of references/deck.js instead -->', '')

    html = head + body + tail

    nav = cfg.get('nav')
    nav_js = ('<script>window.DECK_NAV = ' + json.dumps(nav) + ';</script>') if nav else ''
    html = replace_once(html, 'DECK_NAV_CONFIG', nav_js)
    html = replace_once(html, 'DECK_TITLE', cfg['title'])

    # longest tokens first: IMG_A is a prefix of IMG_A2 and would eat it
    for token, path in sorted(cfg.get('images', {}).items(), key=lambda kv: -len(kv[0])):
        if token not in html:
            print(f'  note: image token {token} declared but unused')
            continue
        html = html.replace(token, data_uri(rel(path)))

    leftovers = set(re.findall(r'\b(?:IMG|LOGO)_[A-Z0-9_]+\b', html))
    if leftovers:
        sys.exit(f'ERROR unresolved tokens: {sorted(leftovers)}')

    n = len(re.findall(r'data-slide="\d+"', html))
    html = re.sub(r'<span class="pos" id="pos">[^<]*</span>',
                  f'<span class="pos" id="pos">1 / {n}</span>', html)

    out = rel(cfg['out'])
    open(out, 'w', encoding='utf-8').write(html)
    print(f'{cfg["out"]}: {n} slides, {len(html)//1024} KB')
    return out


def replace_once(text, old, new, all_occurrences=False):
    """Every substitution is asserted — a silent no-op ships a broken deck."""
    if old not in text:
        sys.exit(f'ERROR anchor not found: {old[:60]!r}')
    return text.replace(old, new) if all_occurrences else text.replace(old, new, 1)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'build.json')
