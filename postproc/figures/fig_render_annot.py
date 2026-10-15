#!/usr/bin/env python3
"""Annotate a headless render in the house style: crop the margins, pad a sky strip for the labels,
add labels with leader lines and a wind arrow, using the projected anchor points the render
script exported.

    python3 postproc/figures/fig_render_annot.py <render.png> <anchors.json> --out <out.png> \
        --label chillers "ten chillers, two rows" 0.25 0.10  --label flues "four flues" 0.85 0.12 ...
        [--wind "wind, 10 m/s"] [--pad 0.18 0.06]

Each label gives the anchor name, the text and the text position as fractions of the final
image (x from the left, y from the top). The wind arrow follows the projected wind direction and
is drawn from the left edge at the height of the roof corner. Output is a PNG at README width.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image, ImageChops, ImageOps
import style; style.use()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("png"); ap.add_argument("anchors"); ap.add_argument("--out", required=True)
    ap.add_argument("--label", nargs=4, action="append", default=[], metavar=("ANCHOR", "TEXT", "FX", "FY"))
    ap.add_argument("--wind", default=None); ap.add_argument("--margin", type=int, default=40)
    ap.add_argument("--pad", nargs=2, type=float, default=[0.16, 0.0], help="white strip added on top and on the left, as fractions of the cropped size")
    ap.add_argument("--width", type=float, default=style.FULL); a = ap.parse_args()
    im = Image.open(a.png).convert("RGB"); A = json.load(open(a.anchors))
    bg = Image.new("RGB", im.size, (255, 255, 255)); box = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 8 else 0).getbbox()
    l, t, r, b = box; l, t = max(l - a.margin, 0), max(t - a.margin, 0); r, b = min(r + a.margin, im.width), min(b + a.margin, im.height)
    im = im.crop((l, t, r, b)); pt, pl = int(a.pad[0] * im.height), int(a.pad[1] * im.width)
    im = ImageOps.expand(im, border=(pl, pt, 0, 0), fill=(255, 255, 255)); W, H = im.size
    P = lambda k: (A[k][0] - l + pl, A[k][1] - t + pt)
    fig = plt.figure(figsize=(a.width, a.width * H / W)); ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(im); ax.set_axis_off()
    for k, text, fx, fy in a.label:
        x, y = P(k); tx, ty = float(fx) * W, float(fy) * H
        ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=8, color=style.INK, ha="center", va="center",
                    arrowprops=dict(arrowstyle="-", color=style.INK, lw=0.6, shrinkA=1, shrinkB=2))
    if a.wind:
        (x1, y1), (x2, y2) = P("wind_a"), P("wind_b"); d = np.array([x2 - x1, y2 - y1]); d = d / np.linalg.norm(d)
        rc = P("roof_corner"); s = np.array([pl + 0.03 * W, rc[1] - 0.10 * H]); e = s + d * 0.11 * W
        ax.annotate("", xy=e, xytext=s, arrowprops=dict(arrowstyle="-|>", color=style.INK, lw=1.3, mutation_scale=12))
        ax.text(s[0], s[1] - 0.06 * H, a.wind, fontsize=8, color=style.INK, ha="left", va="bottom")
    ax.set_xlim(0, W); ax.set_ylim(H, 0)
    os.makedirs(os.path.dirname(a.out), exist_ok=True); fig.savefig(a.out, dpi=220); plt.close(fig); print("wrote", a.out, W, H)

if __name__ == "__main__":
    main()
