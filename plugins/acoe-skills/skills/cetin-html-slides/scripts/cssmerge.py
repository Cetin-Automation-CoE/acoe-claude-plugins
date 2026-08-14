"""
CSS merging for the DunAI deck build.

Every chapter deck is authored as a standalone file, so they all repeat the same
base stage CSS and they are free to invent their own class names. Concatenating
them naively means chapter 8's `.viz` can silently restyle chapter 6's `.viz`.

So: emit the shared/global rules once, and scope every chapter-specific rule
under that chapter's own class (`.c1`, `.c3`, ...), which the build also stamps
onto each of that chapter's slides. After that, chapters cannot reach into each
other and new chapters can use any class name they like.
"""
import re

# Rules that must stay global — they target the document, the stage, or the
# browser chrome, none of which live inside a .slide.
GLOBAL_STARTS = (
    'html', 'body', ':root', '*',
    '.deck-viewport', '.deck-stage', '.deck-controls',
    '.rail', '.home-btn', '.next-chap', '.hint', '.pos',
    'img,', 'img ', 'video', 'canvas', 'svg',
)


def split_blocks(css):
    """Split a stylesheet into top-level (prelude, body, is_at_rule) chunks."""
    out, i, n = [], 0, len(css)
    while i < n:
        # skip whitespace and comments
        while i < n and css[i].isspace():
            i += 1
        if css.startswith('/*', i):
            j = css.find('*/', i)
            i = (j + 2) if j != -1 else n
            continue
        if i >= n:
            break
        # at-rules without a block, e.g. @import ...;
        j, depth = i, 0
        while j < n:
            if css.startswith('/*', j):
                k = css.find('*/', j)
                j = (k + 2) if k != -1 else n
                continue
            c = css[j]
            if c == ';' and depth == 0:
                out.append((css[i:j].strip(), None, css[i:j].lstrip().startswith('@')))
                j += 1
                break
            if c == '{':
                depth += 1
                if depth == 1:
                    prelude = css[i:j].strip()
                    start = j + 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    out.append((prelude, css[start:j], prelude.startswith('@')))
                    j += 1
                    break
            j += 1
        else:
            break
        i = j
    return out


def is_global(prelude):
    p = prelude.lstrip()
    return any(p.startswith(g) for g in GLOBAL_STARTS)


def scope_selector(sel, prefix, root_classes=frozenset()):
    """Scope one selector under `prefix`.

    `.slide` and friends ARE the scoping element, so they compound (`.c8.slide`);
    everything else is a descendant (`.c8 .appcard`). `.slide-no` must not be
    mistaken for `.slide` — it is a child, not the slide itself.

    `root_classes` are the OTHER classes that live on that same `<section
    class="slide …">` element in this chapter — e.g. `divider`, `title-slide`,
    `resources`. A rule like `.divider { background: … }` is not a descendant
    rule, it targets the slide itself, so it must compound too
    (`.c12.divider`) or it silently never matches anything once merged.
    """
    sel = sel.strip()
    if not sel:
        return sel
    if sel.startswith(('from', 'to')) or re.fullmatch(r'\d+%', sel):
        return sel  # keyframe stop
    if sel == '.slide' or sel.startswith(('.slide.', '.slide:', '.slide ', '.slide>', '.slide+', '.slide~')):
        return prefix + sel
    for rc in root_classes:
        tag = '.' + rc
        if sel == tag or sel.startswith((tag + '.', tag + ':', tag + ' ', tag + '>', tag + '+', tag + '~')):
            return prefix + sel
    return prefix + ' ' + sel


def scope_prelude(prelude, prefix, root_classes=frozenset()):
    return ', '.join(scope_selector(s, prefix, root_classes) for s in prelude.split(','))


def slide_root_classes(html):
    """Every class that shares a `<section class="slide …">` with `slide` itself
    in this chapter — e.g. {'divider', 'title-slide'}. Used so a rule like
    `.divider{…}` is recognised as targeting the slide, not a descendant of it.
    """
    classes = set()
    for m in re.finditer(r'<section\s+class="([^"]*\bslide\b[^"]*)"', html):
        classes |= set(m.group(1).split())
    classes.discard('slide')
    return classes


def scope_all(css, container):
    """Scope an entire stylesheet under `container`.

    Used for the contents page, whose markup becomes a `<div id="home">` inside
    the deck file. `html`/`body` rules become rules on the container itself;
    keyframes and font faces stay global.
    """
    out = []
    for prelude, body, at in split_blocks(css):
        if body is None:
            out.append(prelude + ';')
            continue
        if at:
            head = prelude.split()[0].lower()
            if head in ('@keyframes', '@-webkit-keyframes', '@font-face', '@import'):
                out.append(prelude + '{' + body + '}')
            elif head in ('@media', '@supports'):
                out.append(prelude + '{' + scope_all(body, container) + '}')
            else:
                out.append(prelude + '{' + body + '}')
            continue
        sels = []
        for sel in prelude.split(','):
            s = sel.strip()
            if not s:
                continue
            if s in ('html', 'body', 'html, body') or s.startswith(('html ', 'body ')):
                rest = s.split(' ', 1)
                sels.append(container if len(rest) == 1 else f'{container} {rest[1]}')
            elif s == '*' or s.startswith('*'):
                sels.append(f'{container} {s}')
            elif s.startswith(':root'):
                sels.append(container)
            else:
                sels.append(f'{container} {s}')
        if sels:
            out.append(', '.join(sels) + '{' + body + '}')
    return '\n'.join(out)


def collect(chapters):
    """chapters: list of (prefix, css_text) OR (prefix, css_text, root_classes).

    root_classes (optional 3rd element) are the other classes sharing the
    `<section class="slide …">` element in that chapter — see
    `slide_root_classes()`. Without it, a rule like `.divider{background:…}`
    scopes as a descendant selector and silently never matches anything.
    """
    global_out, keyframes, scoped_out = [], {}, []
    seen_global = set()

    for idx, entry in enumerate(chapters):
        prefix, css = entry[0], entry[1]
        root_classes = entry[2] if len(entry) > 2 else frozenset()
        for prelude, body, at in split_blocks(css):
            if body is None:
                if prelude not in seen_global:
                    seen_global.add(prelude)
                    global_out.append(prelude + ';')
                continue

            if at:
                head = prelude.split()[0].lower()
                if head in ('@keyframes', '@-webkit-keyframes'):
                    name = prelude.split()[1] if len(prelude.split()) > 1 else '?'
                    norm = re.sub(r'\s+', ' ', body).strip()
                    if name in keyframes and keyframes[name][0] != norm:
                        print(f'    ! keyframes "{name}" differ between chapters '
                              f'({keyframes[name][1]} vs {prefix}) — keeping the first')
                    keyframes.setdefault(name, (norm, prefix, prelude, body))
                elif head in ('@media', '@supports'):
                    # recurse into the block
                    inner_global, inner_scoped = [], []
                    for p2, b2, _ in split_blocks(body):
                        if b2 is None:
                            continue
                        (inner_global if is_global(p2) else inner_scoped).append(
                            (p2 if is_global(p2) else scope_prelude(p2, prefix, root_classes), b2))
                    if inner_global and idx == 0:
                        global_out.append(prelude + '{' + ''.join(
                            f'{p}{{{b}}}' for p, b in inner_global) + '}')
                    if inner_scoped:
                        scoped_out.append(prelude + '{' + ''.join(
                            f'{p}{{{b}}}' for p, b in inner_scoped) + '}')
                else:
                    if prelude not in seen_global:
                        seen_global.add(prelude)
                        global_out.append(prelude + '{' + body + '}')
                continue

            if is_global(prelude):
                key = re.sub(r'\s+', ' ', prelude + '{' + body + '}')
                if key not in seen_global:
                    seen_global.add(key)
                    global_out.append(prelude + '{' + body + '}')
            else:
                scoped_out.append((scope_prelude(prelude, prefix, root_classes), body))

    parts = ['/* ---- shared base ---- */']
    parts += global_out
    parts.append('/* ---- keyframes ---- */')
    parts += [f'{pre}{{{body}}}' for _, (_, _, pre, body) in keyframes.items()]
    parts.append('/* ---- per-chapter, scoped ---- */')
    parts += [f'{p}{{{b}}}' if isinstance(p, str) and b is not None else p
              for p, b in [(x if isinstance(x, tuple) else (x, None)) for x in scoped_out]]
    return '\n'.join(parts)
