#!/usr/bin/env python3
"""Trim the white margins of rendered PNGs in place, leaving a small border.

    python3 postproc/crop.py results/applied/figures/plume_*.png [--margin 40]
"""
import argparse
from PIL import Image, ImageChops

def crop(path, margin):
    im = Image.open(path).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255)); diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 8 else 0)
    box = diff.getbbox()
    if not box: return
    l, t, r, b = box; l, t = max(l - margin, 0), max(t - margin, 0); r, b = min(r + margin, im.width), min(b + margin, im.height)
    im.crop((l, t, r, b)).save(path); print(path, im.size, "->", (r - l, b - t))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--margin", type=int, default=40); a = ap.parse_args()
    for f in a.files: crop(f, a.margin)

if __name__ == "__main__":
    main()
