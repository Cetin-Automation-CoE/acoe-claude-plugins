#!/usr/bin/env python3
"""Crop a CETIN logo PNG to its alpha bounding box, optionally dropping the claim line.

The canonical files ship at ~5477x1653 with heavy transparent padding; embedded raw the
visible mark renders tiny inside its box. The international PNGs also include
"MEMBER OF PPF GROUP" below the wordmark — pass --no-claim to keep only the wordmark.

    python3 prep_logo.py CETIN_CMYK_pozitiv_international.png logo_light.png --no-claim
    python3 prep_logo.py CETIN_CMYK_negativ_international.png  logo_dark.png  --no-claim
"""
import argparse, base64, sys
from PIL import Image
import numpy as np


def crop_logo(src, dst, drop_claim=False, width=900, emit_b64=None):
    im = Image.open(src).convert('RGBA')
    im = im.crop(im.getbbox())                       # trim the transparent padding

    if drop_claim:
        alpha = np.array(im)[:, :, 3]
        filled = (alpha > 10).sum(axis=1)
        runs, start = [], None
        for i, blank in enumerate(filled == 0):
            if blank and start is None:
                start = i
            elif not blank and start is not None:
                runs.append((start, i)); start = None
        if start is not None:
            runs.append((start, len(filled)))
        # the wordmark ends at the first blank band taller than 3% of the image
        gaps = [r for r in runs if r[1] - r[0] > im.size[1] * 0.03]
        if gaps:
            im = im.crop((0, 0, im.size[0], gaps[0][0]))
            im = im.crop(im.getbbox())

    if width and im.size[0] > width:
        im = im.resize((width, int(width * im.size[1] / im.size[0])), Image.LANCZOS)

    im.save(dst, optimize=True)
    print(f'{dst}: {im.size[0]}x{im.size[1]}  aspect {im.size[0]/im.size[1]:.2f}:1')

    if emit_b64:
        with open(emit_b64, 'w') as fh:
            fh.write(base64.b64encode(open(dst, 'rb').read()).decode())
        print(f'  base64 -> {emit_b64}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('src'); p.add_argument('dst')
    p.add_argument('--no-claim', action='store_true', help='drop MEMBER OF PPF GROUP')
    p.add_argument('--width', type=int, default=900)
    p.add_argument('--b64', help='also write a base64 sidecar for inlining')
    a = p.parse_args()
    crop_logo(a.src, a.dst, a.no_claim, a.width, a.b64)
