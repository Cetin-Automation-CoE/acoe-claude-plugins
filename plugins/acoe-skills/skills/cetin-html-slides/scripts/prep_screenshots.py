#!/usr/bin/env python3
"""Prepare an app screenshot for a slide: resize, recompress, and crop to a target aspect.

Two screenshots sitting side by side only render at the same height if their aspect
ratios match. Fix that in the image — crop it — never by adding a per-slide CSS width
cap, and never by forcing both width and height (that stretches the picture).

    # plain ingest: cap the width, recompress
    python3 scripts/prep_screenshots.py raw.png assets/shot_app.jpg

    # crop so it pairs with an existing screenshot
    python3 scripts/prep_screenshots.py raw.png assets/shot_app.jpg --match assets/shot_other.jpg

    # crop to an explicit ratio, trimming a chosen edge
    python3 scripts/prep_screenshots.py phone.png assets/shot_phone.jpg --aspect 0.462 --trim right

    # just report what you have
    python3 scripts/prep_screenshots.py --info assets/*.jpg

Trim edge matters: on a phone capture the left edge usually holds the field labels, so
trim `right`. On a long table, trim `bottom`. Say which edge you trimmed in the handover
so the owner can re-capture if the lost rows mattered.
"""
import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit('needs Pillow:  pip install pillow')


def info(paths):
    for p in paths:
        with Image.open(p) as im:
            print('%-46s %5dx%-5d  aspect %.3f  %4d KB'
                  % (os.path.basename(p), im.width, im.height,
                     im.width / im.height, os.path.getsize(p) // 1024))


def crop_to(im, aspect, trim):
    """Crop (never squash) to the given width/height ratio."""
    have = im.width / im.height
    if abs(have - aspect) < 0.005:
        return im
    if have > aspect:                       # too wide -> take width off
        w = round(im.height * aspect)
        off = 0 if trim == 'right' else (im.width - w if trim == 'left' else (im.width - w) // 2)
        return im.crop((off, 0, off + w, im.height))
    h = round(im.width / aspect)            # too tall -> take height off
    off = 0 if trim == 'bottom' else (im.height - h if trim == 'top' else (im.height - h) // 2)
    return im.crop((0, off, im.width, off + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', nargs='?')
    ap.add_argument('dst', nargs='?')
    ap.add_argument('--info', nargs='*', help='print dimensions and aspect, then exit')
    ap.add_argument('--aspect', type=float, help='target width/height ratio')
    ap.add_argument('--match', help='crop to the aspect ratio of this existing image')
    ap.add_argument('--trim', default='auto',
                    choices=['auto', 'left', 'right', 'top', 'bottom'],
                    help='which edge to lose when cropping (default: centred)')
    ap.add_argument('--maxw', type=int, default=1400, help='max width in px (default 1400)')
    ap.add_argument('--quality', type=int, default=86)
    a = ap.parse_args()

    if a.info is not None:
        return info(a.info)
    if not (a.src and a.dst):
        ap.error('need src and dst (or --info)')

    aspect = a.aspect
    if a.match:
        with Image.open(a.match) as m:
            aspect = m.width / m.height

    with Image.open(a.src) as raw:
        im = raw.convert('RGB')
        before = (im.width, im.height)
        if aspect:
            im = crop_to(im, aspect, a.trim)
        if im.width > a.maxw:
            im = im.resize((a.maxw, round(im.height * a.maxw / im.width)), Image.LANCZOS)
        os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
        im.save(a.dst, 'JPEG', quality=a.quality, optimize=True)

    print('%s  %dx%d -> %dx%d  aspect %.3f  %d KB'
          % (os.path.basename(a.dst), before[0], before[1], im.width, im.height,
             im.width / im.height, os.path.getsize(a.dst) // 1024))
    if aspect and a.trim != 'auto':
        print('   trimmed the %s edge — mention it in the handover' % a.trim)


if __name__ == '__main__':
    main()
