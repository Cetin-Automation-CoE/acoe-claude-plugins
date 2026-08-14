#!/usr/bin/env python3
"""Extract the dominant colors from an image (logo, screenshot, branded visual).

Used during onboarding to draft a candidate brand palette. The output is a
ranked list of colors with the share of the image each one covers, so the
caller can tell a brand color (a large, saturated region) from neutrals
(near-white / near-black backgrounds).

Usage:
    python extract_colors.py <image> [--colors 8]

--colors is how many palette entries to quantize down to (default 8).

Output is one line per color:
    #1B3A8F   34.1%   saturated      <- likely a brand color
    #FFFFFF   48.0%   near-white     <- background / neutral
    #1A1A1A    9.2%   near-black     <- text / neutral

This is a heuristic starting point, not a final answer. Always confirm the
palette with the user, and prefer exact values from a brand manual when one
exists.
"""

import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow --break-system-packages")


def classify(r, g, b):
    """Rough bucket so the caller can separate brand colors from neutrals."""
    mx, mn = max(r, g, b), min(r, g, b)
    if mn > 235:
        return "near-white"
    if mx < 30:
        return "near-black"
    saturation = (mx - mn) / mx if mx else 0
    if saturation < 0.12:
        return "gray / neutral"
    if saturation >= 0.45:
        return "saturated"
    return "muted color"


def extract(image_path, n_colors=8):
    img = Image.open(image_path).convert("RGBA")

    # Drop fully/mostly transparent pixels onto a flat list of opaque RGB pixels.
    opaque = [(r, g, b) for (r, g, b, a) in img.getdata() if a > 200]
    if not opaque:
        sys.exit("ERROR: image is fully transparent — nothing to sample.")

    flat = Image.new("RGB", (len(opaque), 1))
    flat.putdata(opaque)

    # Quantize to a small palette, then count how many pixels map to each entry.
    quant = flat.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    palette = quant.getpalette()
    counts = quant.getcolors()  # list of (count, palette_index)
    total = sum(c for c, _ in counts)

    rows = []
    for count, idx in counts:
        r, g, b = palette[idx * 3 : idx * 3 + 3]
        rows.append((count / total, r, g, b))
    rows.sort(reverse=True)

    print(f"Dominant colors in {image_path}  ({len(opaque)} opaque pixels sampled):\n")
    for share, r, g, b in rows:
        hexv = f"#{r:02X}{g:02X}{b:02X}"
        print(f"  {hexv}   {share * 100:5.1f}%   {classify(r, g, b)}")
    print(
        "\nHeuristic: 'saturated' / 'muted color' entries are brand-color candidates;"
        "\n'near-white', 'near-black', and 'gray' are neutrals/background."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract the dominant colors from an image.")
    parser.add_argument("image", help="image path")
    parser.add_argument("--colors", type=int, default=8,
                        help="number of palette entries to quantize to (default 8)")
    ns = parser.parse_args()

    extract(ns.image, ns.colors)
