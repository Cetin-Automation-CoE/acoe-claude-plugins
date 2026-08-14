#!/usr/bin/env python3
"""Generate the CETIN-branded contents page from a manifest.

Driving it from data is what stops the index drifting from the files on disk.

    index.json
    {
      "out": "index.html", "programme": "DunAI", "training": "AI Exec Training",
      "date": "29 July 2026", "presenters": "Jiri Forman · Peter Kukura",
      "logo": "assets/logo_dark.png",
      "chapters": [
        {"num": "1–2", "title": "AI Intro &amp; Basic Terms", "sub": "…",
         "file": "DunAI_Topic1-2.html", "ready": true,
         "slides": [["Title — …", "", true], ["1.1  What is AI?", "", false]]}
      ],
      "resources": [{"title": "Master content reference",
                     "body": "<a href='x.md'>x.md</a> — every slide's text and notes."}]
    }
      slides entries are [label, tag, is_divider]

    python3 make_index.py index.json
"""
import base64, json, mimetypes, os, sys

CSS = """
:root{--cetin-blue:#300091;--cetin-red:#f12e49;--white:#fff;--ink:#1a1a1a;--mid-gray:#c7c9c7;
--panel:#f5f6fa;--rule:#d7dae1;--gray-text:#66678a;--font:Arial,"Avenir Next LT Pro",sans-serif}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}
body{font-family:var(--font);color:var(--ink);background:#fff;-webkit-font-smoothing:antialiased}
.hero{position:relative;overflow:hidden}
.hero-blue{position:relative;background:var(--cetin-blue);padding:54px 64px 76px;
clip-path:polygon(0 0,100% 0,100% calc(100% - 46px),0 100%)}
.hero-blue::after{content:'';position:absolute;inset:0;
background:linear-gradient(145deg,#70D1E2,#1F4D9A);opacity:.10;mix-blend-mode:screen}
.hero-inner{position:relative;z-index:2;max-width:1360px;margin:0 auto}
.kicker{font-size:13px;font-weight:700;letter-spacing:4.5px;text-transform:uppercase;color:#a7c8ff;margin-bottom:16px}
.hero h1{font-size:52px;font-weight:700;line-height:1.06;text-transform:uppercase;color:#fff;letter-spacing:-.5px}
.hero-rule{width:110px;height:6px;background:var(--cetin-red);margin:26px 0 22px}
.hero-meta{display:flex;gap:40px;flex-wrap:wrap;font-size:16px;color:#dfe4ff}
.hero-meta b{color:#fff}
.hero-logo{position:absolute;right:64px;top:50px;width:190px;z-index:3}
.wrap{max-width:1360px;margin:0 auto;padding:0 64px 90px}
.section-label{font-size:13px;font-weight:700;letter-spacing:3.4px;text-transform:uppercase;
color:var(--gray-text);margin:46px 0 20px}
.decks{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:24px}
.deck{border:1px solid var(--rule);border-radius:12px;background:#fff;box-shadow:0 2px 14px rgba(48,0,145,.06);
display:flex;flex-direction:column;overflow:hidden;transition:box-shadow .22s,transform .22s}
.deck:hover{box-shadow:0 12px 34px rgba(48,0,145,.14);transform:translateY(-3px)}
.deck.pending{opacity:.72}
.deck-head{display:flex;align-items:flex-start;gap:18px;padding:24px 26px 20px;border-bottom:1px solid var(--rule)}
.deck-num{font-size:40px;font-weight:700;line-height:.92;color:var(--cetin-blue);min-width:62px}
.deck.pending .deck-num{color:var(--mid-gray)}
.deck-titles h2{font-size:25px;font-weight:700;text-transform:uppercase;color:var(--cetin-blue);line-height:1.15}
.deck.pending .deck-titles h2{color:var(--gray-text)}
.deck-sub{margin-top:8px;font-size:15.5px;line-height:1.45;color:#44445a}
.badge{display:inline-block;margin-top:12px;font-size:12px;font-weight:700;letter-spacing:1.8px;
text-transform:uppercase;padding:5px 11px;border-radius:4px;background:var(--panel);color:var(--gray-text)}
.badge.ready{background:var(--cetin-blue);color:#fff}.badge.todo{background:var(--cetin-red);color:#fff}
.slides{list-style:none;padding:10px 12px 12px;flex:1}
.slides li a,.slides li span.dead{display:flex;align-items:baseline;gap:12px;padding:8px 14px;
border-radius:6px;font-size:15.5px;color:var(--ink);text-decoration:none;transition:background .15s}
.slides li a:hover{background:rgba(48,0,145,.06);color:var(--cetin-blue)}
.slides li a .n,.slides li span.dead .n{flex:0 0 46px;font-weight:700;font-size:13.5px;color:var(--cetin-red)}
.slides li span.dead{color:var(--gray-text)}.slides li span.dead .n{color:var(--mid-gray)}
.slides li.divider-row a,.slides li.divider-row span.dead{font-weight:700;color:var(--cetin-blue)}
.slides li .tag{margin-left:auto;font-size:11.5px;font-weight:700;letter-spacing:1.2px;
text-transform:uppercase;color:var(--gray-text);white-space:nowrap}
.deck-foot{padding:0 26px 24px}
.btn{display:inline-block;background:var(--cetin-red);color:#fff;text-decoration:none;font-weight:700;
text-transform:uppercase;letter-spacing:1.6px;font-size:14px;padding:13px 26px;border-radius:4px}
.btn:hover{background:#d41f39}
.btn.off{background:var(--mid-gray);color:#6b6d6b;pointer-events:none}
.res{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px}
.rescard{border:1px solid var(--rule);border-left:5px solid var(--cetin-blue);border-radius:8px;
padding:20px 24px;background:var(--panel)}
.rescard h3{font-size:17px;color:var(--cetin-blue);margin-bottom:6px}
.rescard p{font-size:14.5px;line-height:1.5;color:#44445a}
.rescard a{color:var(--cetin-blue);font-weight:700;text-decoration:none;border-bottom:1px solid rgba(48,0,145,.3)}
.rescard code{background:#fff;padding:1px 6px;border-radius:3px;font-size:13px}
.tips{background:var(--panel);border-radius:10px;padding:24px 28px}
.tips ul{list-style:none}
.tips li{position:relative;padding-left:26px;margin-bottom:10px;font-size:15.5px;line-height:1.5;color:#44445a}
.tips li::before{content:'';position:absolute;left:0;top:8px;width:0;height:0;
border-left:9px solid var(--cetin-red);border-top:6px solid transparent;border-bottom:6px solid transparent}
.tips kbd{background:#fff;border:1px solid var(--rule);border-bottom-width:2px;border-radius:4px;
padding:1px 7px;font-family:var(--font);font-size:13.5px;font-weight:700;color:var(--cetin-blue)}
footer{border-top:1px solid var(--rule);padding:26px 64px 40px;font-size:13.5px;color:var(--gray-text);text-align:center}
@media(max-width:820px){.hero-blue{padding:40px 28px 60px}.hero h1{font-size:34px}
.hero-logo{position:static;margin-bottom:22px;width:150px}.wrap{padding:0 28px 64px}.decks{grid-template-columns:1fr}}
"""

TIPS = """
      <li>Navigate with <kbd>&larr;</kbd> <kbd>&rarr;</kbd> or <kbd>Space</kbd>, or swipe on a tablet.
          <kbd>Home</kbd> and <kbd>End</kbd> jump to the ends of a chapter.</li>
      <li><b>Chapters roll over.</b> On the last slide a
          <span style="color:var(--cetin-red);font-weight:700">Next chapter</span> button appears top-right,
          and <kbd>&rarr;</kbd> once more jumps into the next file. <kbd>&larr;</kbd> on slide 1 goes back
          to the end of the previous chapter.</li>
      <li>The <b>Contents</b> button top-left returns to this page from any slide.</li>
      <li>Every slide has its own address &mdash; the URL updates as you move, so any slide can be
          bookmarked or shared.</li>
      <li><b>Edit mode:</b> press <kbd>E</kbd>, then click any text. This edits the page in the browser
          only &mdash; it does <b>not</b> write to the file. Press <kbd>&#8984;S</kbd> / <kbd>Ctrl+S</kbd>
          to download a copy with your edits baked in. Reloading without saving discards everything.</li>
      <li>Full screen (<kbd>F11</kbd>, or <kbd>&#8963;&#8984;F</kbd> on a Mac) gives the whole 16:9 stage
          with no browser chrome.</li>
"""


def card(ch):
    ready = ch.get('ready', True)
    n = len(ch['slides'])
    badge = (f'<span class="badge ready">{n} slides &middot; ready</span>' if ready
             else f'<span class="badge todo">{n} slides &middot; not built yet</span>')
    rows = []
    for i, (label, tag, is_div) in enumerate(ch['slides'], start=1):
        cls = ' class="divider-row"' if is_div else ''
        t = f'<span class="tag">{tag}</span>' if tag else ''
        inner = f'<span class="n">{i:02d}</span><span>{label}</span>{t}'
        rows.append(f'          <li{cls}>' +
                    (f'<a href="{ch["file"]}#{i}">{inner}</a>' if ready
                     else f'<span class="dead">{inner}</span>') + '</li>')
    btn = (f'<a class="btn" href="{ch["file"]}">Open deck</a>' if ready
           else '<span class="btn off">Content still needed</span>')
    return f'''    <section class="deck{'' if ready else ' pending'}">
      <div class="deck-head">
        <div class="deck-num">{ch['num']}</div>
        <div class="deck-titles">
          <h2>{ch['title']}</h2>
          <div class="deck-sub">{ch.get('sub','')}</div>
          {badge}
        </div>
      </div>
      <ul class="slides">
{chr(10).join(rows)}
      </ul>
      <div class="deck-foot">{btn}</div>
    </section>'''


def build(cfg_path):
    cfg = json.load(open(cfg_path))
    root = os.path.dirname(os.path.abspath(cfg_path))
    return build_from_cfg(cfg, root)


def build_from_cfg(cfg, root):
    """Same as build(), but takes an already-loaded config dict and its base
    directory. Used by build_all.py, which assembles the config in memory
    (chapter slide lists derived from the just-built decks) rather than
    reading it from a hand-written index.json.
    """
    total = sum(len(c['slides']) for c in cfg['chapters'])
    built = sum(1 for c in cfg['chapters'] if c.get('ready', True))
    logo = ''
    if cfg.get('logo'):
        p = os.path.join(root, cfg['logo'])
        mime = mimetypes.guess_type(p)[0] or 'image/png'
        logo = (f'<img class="hero-logo" alt="CETIN" src="data:{mime};base64,'
                + base64.b64encode(open(p, 'rb').read()).decode() + '">')
    res = '\n'.join(f'    <div class="rescard"><h3>{r["title"]}</h3><p>{r["body"]}</p></div>'
                    for r in cfg.get('resources', []))
    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{cfg['training']} &middot; Contents</title>
<style>{CSS}</style></head><body>
<header class="hero"><div class="hero-blue">{logo}
  <div class="hero-inner">
    <div class="kicker">{cfg['programme']} &middot; Contents</div>
    <h1>{cfg['training']}</h1>
    <div class="hero-rule"></div>
    <div class="hero-meta">
      <span><b>{cfg.get('date','')}</b></span>
      <span>{cfg.get('presenters','')}</span>
      <span><b>{total}</b> slides &middot; <b>{len(cfg['chapters'])}</b> chapters &middot; {built} built</span>
    </div>
  </div></div></header>
<div class="wrap">
  <div class="section-label">Chapter decks &mdash; click any slide to open it directly</div>
  <div class="decks">
{chr(10).join(card(c) for c in cfg['chapters'])}
  </div>
  <div class="section-label">Source &amp; assets</div>
  <div class="res">
{res}
  </div>
  <div class="section-label">Presenting</div>
  <div class="tips"><ul>{TIPS}</ul></div>
</div>
<footer>{cfg['programme']} &middot; {cfg['training']} &middot; CETIN &middot; {cfg.get('date','')}</footer>
</body></html>'''
    out = os.path.join(root, cfg.get('out', 'index.html'))
    open(out, 'w', encoding='utf-8').write(html)
    print(f'{cfg.get("out","index.html")}: {len(cfg["chapters"])} chapters, {total} slides')
    return out


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'index.json')
