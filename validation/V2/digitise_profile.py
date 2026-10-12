#!/usr/bin/env python3
"""Digitise the measured profile markers of an axes-only Excel chart (R-848 Figure 3.1).

    digitise_profile.py <page.png> --crop x0 y0 x1 y1 --xaxis 0 1.2 --yaxis 0 100 --colour 0 0 128 --name ... --out ...

Calibration: x from the first and last tick marks under the x-axis line; y from the x-axis line (y = 0) and
the top end of the vertical axis line (y max). The vertical axis line extends below the x-axis in these
charts, so its bottom end must not be used. The connecting line is removed by a morphological opening (erode then dilate, --open px)
and the remaining markers of the series colour are found as connected blobs; the centroid of each blob is a point. Overlapping markers near the floor merge into
one blob and are reported with their pixel height so they can be flagged. Legend markers are removed
with --exclude boxes. An overlay with red crosses is written for checking.
"""
import argparse, os
from PIL import Image, ImageDraw
import numpy as np
from collections import deque

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page"); ap.add_argument("--crop", nargs=4, type=int, required=True)
    ap.add_argument("--xaxis", nargs=2, type=float, required=True); ap.add_argument("--yaxis", nargs=2, type=float, required=True)
    ap.add_argument("--colour", nargs=3, type=int, required=True); ap.add_argument("--tol", type=int, default=60)
    ap.add_argument("--name", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--exclude", nargs=4, type=int, action="append", default=[])
    ap.add_argument("--open", type=int, default=5, help="morphological opening size (px) to remove the connecting line, keeping the markers")
    a = ap.parse_args()
    im = Image.open(a.page).convert("RGB"); x0, y0, x1, y1 = a.crop
    sub = np.asarray(im.crop((x0, y0, x1, y1))).astype(int); H, W, _ = sub.shape
    dark = sub.sum(axis=2) < 250
    # axis lines: the longest dark horizontal run and vertical run
    best_h = max(((dark[y].sum(), y) for y in range(H)), key=lambda t: t[0]); yax = best_h[1]
    best_v = max(((dark[:, x].sum(), x) for x in range(W)), key=lambda t: t[0]); xax = best_v[1]
    # x calibration from the tick marks below the x-axis line (first tick = xaxis[0], last tick = xaxis[1])
    xt = [x for x in range(W) if dark[yax + 2:yax + 12, x].sum() >= 8]
    g = []
    for x in xt:
        if g and x - g[-1][-1] <= 2: g[-1].append(x)
        else: g.append([x])
    ticks = [int(np.mean(t)) for t in g if len(t) <= 6]
    xl = min(ticks, key=lambda t: abs(t - xax)); xr = ticks[-1]     # the zero tick coincides with the vertical axis
    # y calibration: the x-axis line is y = yaxis[0]; the top end of the vertical axis line is yaxis[1]
    ys = np.where(dark[:, xax])[0]; yt = ys.min(); yb = yax
    print(f"x ticks at px {ticks} -> {a.xaxis[0]} at {xl}, {a.xaxis[1]} at {xr}; y: {a.yaxis[0]} at row {yb}, {a.yaxis[1]} at row {yt}")
    # series blobs
    col = np.array(a.colour); ser = np.abs(sub - col).sum(axis=2) < a.tol
    for ex0, ey0, ex1, ey1 in a.exclude: ser[ey0:ey1, ex0:ex1] = False
    if a.open > 1:
        from PIL import ImageFilter
        m = Image.fromarray((ser * 255).astype(np.uint8))
        m = m.filter(ImageFilter.MinFilter(a.open)).filter(ImageFilter.MaxFilter(a.open))   # opening: erode then dilate
        ser = np.asarray(m) > 127
    seen = np.zeros_like(ser, dtype=bool); blobs = []
    for yy in range(H):
        for xx in range(W):
            if ser[yy, xx] and not seen[yy, xx]:
                q = deque([(yy, xx)]); seen[yy, xx] = True; pix = []
                while q:
                    cy, cx = q.popleft(); pix.append((cy, cx))
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and ser[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if len(pix) >= 25: blobs.append(pix)
    pts = []
    for pix in blobs:
        cy = np.mean([p[0] for p in pix]); cx = np.mean([p[1] for p in pix])
        hgt = max(p[0] for p in pix) - min(p[0] for p in pix) + 1; wid = max(p[1] for p in pix) - min(p[1] for p in pix) + 1
        X = a.xaxis[0] + (cx - xl) / (xr - xl) * (a.xaxis[1] - a.xaxis[0])
        Y = a.yaxis[0] + (yb - cy) / (yb - yt) * (a.yaxis[1] - a.yaxis[0])
        pts.append((Y, X, cx, cy, hgt, wid, len(pix)))
    pts.sort()
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, a.name + ".csv"), "w") as f:
        f.write(f"# digitised from {os.path.basename(a.page)} crop {a.crop}; x axis px {xl}-{xr} = {a.xaxis}; y axis px {yb}-{yt} = {a.yaxis}; colour {a.colour}\n")
        f.write("z,value,blob_height_px,blob_width_px\n")
        for Y, X, _, _, h, w, n in pts: f.write(f"{Y:.3f},{X:.4g},{h},{w}\n")
    ov = im.crop((x0, y0, x1, y1)).copy(); d = ImageDraw.Draw(ov)
    d.line([(xl, yax), (xr, yax)], fill=(0, 160, 0), width=2); d.line([(xax, yt), (xax, yb)], fill=(0, 160, 0), width=2)
    for _, _, cx, cy, _, _, _ in pts:
        d.line([(cx - 10, cy), (cx + 10, cy)], fill=(255, 0, 0), width=2); d.line([(cx, cy - 10), (cx, cy + 10)], fill=(255, 0, 0), width=2)
    ov.save(os.path.join(a.out, a.name + "_overlay.png"))
    print(f"{a.name}: x axis px {xl}-{xr}, y axis px {yb}-{yt}; {len(pts)} blobs")
    for Y, X, _, _, h, w, n in pts: print(f"  z = {Y:6.2f}  value = {X:.4g}   blob {w}x{h} px")

if __name__ == "__main__":
    main()
