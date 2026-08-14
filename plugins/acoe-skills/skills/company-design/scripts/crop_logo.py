#!/usr/bin/env python3
"""Crop a logo image to its visible content, removing transparent padding.

Logo PNGs are often exported on a large canvas with lots of transparent margin.
Embedded raw, the visible mark ends up tiny inside its placement box. This crops
to the alpha bounding box (plus a small breathing margin) so the logo fills its
box properly.

Usage:
    python crop_logo.py <input.png> <output.png> [--margin 0.02]

--margin is a fraction of the smaller image dimension added back as padding
(default 0.02 = 2%). Pass --margin 0 for a tight crop.

If the image has no alpha channel (e.g. a JPG, or a PNG on a solid background),
there is nothing transparent to crop; the image is copied through unchanged and
a note is printed so the caller knows to crop it another way if needed.
"""

import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow --break-system-packages")


def crop_logo(input_path, output_path, margin_frac=0.02):
    img = Image.open(input_path)

    if img.mode != "RGBA":
        # No transparency to crop against — pass the image through unchanged.
        img.convert("RGBA").save(output_path)
        print(f"NOTE: {input_path} has no usable alpha channel; copied unchanged.")
        print(f"Saved: {output_path}  (size {img.size[0]}x{img.size[1]})")
        return

    bbox = img.getbbox()  # bounding box of all non-zero (non-transparent) pixels
    if bbox is None:
        sys.exit(f"ERROR: {input_path} appears to be fully transparent.")

    margin = int(min(img.size) * margin_frac)
    left   = max(0, bbox[0] - margin)
    top    = max(0, bbox[1] - margin)
    right  = min(img.size[0], bbox[2] + margin)
    bottom = min(img.size[1], bbox[3] + margin)

    cropped = img.crop((left, top, right, bottom))
    cropped.save(output_path)

    w, h = cropped.size
    ratio = w / h if h else 0
    print(f"Saved: {output_path}")
    print(f"  cropped size: {w}x{h}  (aspect ratio ~{ratio:.2f}:1)")
    print(f"  was: {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Crop a logo image to its visible content (remove transparent padding).")
    parser.add_argument("input", help="input image path")
    parser.add_argument("output", help="output image path (.png)")
    parser.add_argument("--margin", type=float, default=0.02,
                        help="breathing margin as a fraction of the smaller dimension "
                             "(default 0.02; use 0 for a tight crop)")
    ns = parser.parse_args()

    crop_logo(ns.input, ns.output, ns.margin)
