#!/usr/bin/env python3
"""Digitise a marker series from an Excel-style chart rendered from the R-848 PDF (300 dpi).

    digitise_r848.py <page.png> --crop x0 y0 x1 y1 --xaxis 0 50 --yaxis 0.001 1000 --ylog \
        --colour 0 0 128 --name "fig5_1_isolated_hs1_M3" --out data/digitised/irsst_r848 [--xmin 4]

Method, so that it can be checked:
1. The plot frame is found as the rectangle of dark pixels inside the crop: the left and right
   frame lines give the x-axis range, the top and bottom lines the y-axis range (Excel draws the
   axis limits on the frame).
2. Pixels of the series colour (within a tolerance) are collected. The line is a few pixels thick;
   the markers are blobs 3 to 4 times taller. Columns whose colour extent is taller than the line
   are grouped into markers, and each marker's centre is the data point.
3. Pixel centres are converted with the frame calibration (log10 for a log axis).
4. An overlay PNG with red crosses at the extracted points is written beside the CSV for a visual
   check, and the CSV records the page, crop, calibration and colour used.
Points with x below --xmin are dropped and --exclude boxes (legend) are ignored. The marker centre is
taken from its widest columns, which also works for a half marker cut by the frame edge.
"""
import argparse, csv, math, os
from PIL import Image, ImageDraw
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page"); ap.add_argument("--crop", nargs=4, type=int, required=True)
    ap.add_argument("--xaxis", nargs=2, type=float, required=True); ap.add_argument("--yaxis", nargs=2, type=float, required=True)
    ap.add_argument("--ylog", action="store_true"); ap.add_argument("--colour", nargs=3, type=int, required=True)
    ap.add_argument("--tol", type=int, default=60); ap.add_argument("--name", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--xmin", type=float, default=None); ap.add_argument("--minheight", type=int, default=12)
    ap.add_argument("--exclude", nargs=4, type=int, action="append", default=[], help="crop-pixel box x0 y0 x1 y1 to ignore (legend)")
    ap.add_argument("--mode", choices=["columns", "line"], default="columns",
                    help="columns: markers from column extents (single series of this colour). line: track the thick continuous line "
                         "of this colour across the frame, ignoring thin or broken series of the same colour; markers where it thickens")
    ap.add_argument("--step", type=float, default=5.0, help="line mode fallback: sample spacing in axis units")
    ap.add_argument("--linewidth", nargs=2, type=int, default=[4, 10], help="line mode: accepted run thickness range (px) for the line")
    a = ap.parse_args()
    im = Image.open(a.page).convert("RGB"); x0, y0, x1, y1 = a.crop
    sub = np.asarray(im.crop((x0, y0, x1, y1))).astype(int); H, W, _ = sub.shape
    dark = sub.sum(axis=2) < 200
    # frame: rows/cols with long dark runs
    rowlen = dark.sum(axis=1); collen = dark.sum(axis=0)
    rows = np.where(rowlen > 0.6 * W)[0]; cols = np.where(collen > 0.6 * H)[0]
    top, bottom, left, right = rows.min(), rows.max(), cols.min(), cols.max()
    # series pixels
    col = np.array(a.colour); dist = np.abs(sub - col).sum(axis=2)
    ser = dist < a.tol
    ser[:, :left + 2] = False; ser[:, right + 15:] = False; ser[:top + 2, :] = False; ser[bottom + 15:, :] = False
    for ex0, ey0, ex1, ey1 in a.exclude: ser[ey0:ey1, ex0:ex1] = False
    ext = []
    if a.mode == "line":
        # runs per column
        lo, hi = a.linewidth
        def runs_at(x):
            ys = np.where(ser[:, x])[0]; runs = []
            if len(ys):
                st = ys[0]; pv = ys[0]
                for y in ys[1:]:
                    if y != pv + 1: runs.append((st, pv)); st = y
                    pv = y
                runs.append((st, pv))
            return [r for r in runs if lo <= (r[1] - r[0] + 1) <= 6 * hi]
        allruns = [runs_at(x) for x in range(W)]
        def continuity(x, yc, n=40):
            """fraction of the next n columns that have a run within 4 px of yc: ~1 for a solid line, lower for dotted"""
            ok = 0; cnt = 0
            for xx in range(x + 1, min(W, x + 1 + n)):
                cnt += 1
                if any(abs((r[0] + r[1]) / 2 - yc) <= 4 for r in allruns[xx]): ok += 1
            return ok / cnt if cnt else 0
        prev = None; started = False
        for x in range(W):
            cand = allruns[x]
            if not started:
                xin = a.xaxis[0] + (x - left) / (right - left) * (a.xaxis[1] - a.xaxis[0])
                if x > left + 2 and cand and (a.xmin is None or xin >= a.xmin):
                    c2 = [r for r in cand if (r[1] - r[0] + 1) <= hi]
                    c2 = [r for r in c2 if continuity(x, (r[0] + r[1]) / 2) >= 0.9]
                    if c2: prev = (c2[0][0] + c2[0][1]) / 2; started = True; ext.append(c2[0]); continue
                ext.append(None); continue
            near = [r for r in cand if abs((r[0] + r[1]) / 2 - prev) <= 3 * hi]
            if near:
                if len(near) > 1:
                    # ambiguity: prefer the run that continues as a solid line
                    near.sort(key=lambda r: (-round(continuity(x, (r[0] + r[1]) / 2, 25), 1), abs((r[0] + r[1]) / 2 - prev)))
                    r = near[0]
                else:
                    r = near[0]
                prev = (r[0] + r[1]) / 2; ext.append(r); continue
            ext.append(None)
    else:
        for x in range(W):
            ys = np.where(ser[:, x])[0]
            ext.append((ys.min(), ys.max()) if len(ys) else None)
    # line thickness = median extent where present
    heights = [e[1] - e[0] + 1 for e in ext if e]
    line_h = int(np.median(heights)) if heights else 0
    thr = max(a.minheight, int(2.2 * line_h)) if a.mode == "columns" else max(a.minheight, int(1.6 * line_h))
    markers = []; cur = []
    for x, e in enumerate(ext):
        if e and (e[1] - e[0] + 1) >= thr:
            cur.append((x, e))
        elif cur:
            markers.append(cur); cur = []
    if cur: markers.append(cur)
    pts = []
    for m in markers:
        if len(m) < 4: continue
        hmax = max(e[1] - e[0] for _, e in m)
        widest = [(x, e) for x, e in m if e[1] - e[0] >= hmax - 1]      # the diamond's widest columns = its centre
        xc = np.mean([x for x, _ in widest]); yc = np.mean([(e[0] + e[1]) / 2 for _, e in widest])
        X = a.xaxis[0] + (xc - left) / (right - left) * (a.xaxis[1] - a.xaxis[0])
        if a.ylog:
            ly0, ly1 = math.log10(a.yaxis[0]), math.log10(a.yaxis[1])
            Y = 10 ** (ly1 - (yc - top) / (bottom - top) * (ly1 - ly0))
        else:
            Y = a.yaxis[1] - (yc - top) / (bottom - top) * (a.yaxis[1] - a.yaxis[0])
        if a.xmin is not None and X < a.xmin: continue
        pts.append((X, Y, xc, yc))
    if a.mode == "line" and not pts:
        # fallback: sample the tracked line at the receptor spacing
        hist = sorted(heights); print(f"  no markers above {thr} px; thickness percentiles 50/90/99/max: {hist[len(hist)//2]} {hist[int(0.9*len(hist))]} {hist[int(0.99*len(hist))]} {hist[-1]}; sampling the line every {a.step} units")
        X = a.xaxis[0] + a.step
        while X <= a.xaxis[1] + 1e-9:
            xc = left + (X - a.xaxis[0]) / (a.xaxis[1] - a.xaxis[0]) * (right - left)
            near = [(x, e) for x, e in enumerate(ext) if e and abs(x - xc) <= 3]
            if near and (a.xmin is None or X >= a.xmin):
                yc = np.mean([(e[0] + e[1]) / 2 for _, e in near])
                if a.ylog:
                    ly0, ly1 = math.log10(a.yaxis[0]), math.log10(a.yaxis[1]); Y = 10 ** (ly1 - (yc - top) / (bottom - top) * (ly1 - ly0))
                else:
                    Y = a.yaxis[1] - (yc - top) / (bottom - top) * (a.yaxis[1] - a.yaxis[0])
                pts.append((X, Y, xc, yc))
            X += a.step
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, a.name + ".csv"), "w") as f:
        f.write(f"# digitised from {os.path.basename(a.page)} crop {a.crop}; frame px left {left} right {right} top {top} bottom {bottom}; "
                f"x {a.xaxis}, y {a.yaxis}{' log' if a.ylog else ''}; colour {a.colour} tol {a.tol}; line thickness px {line_h}; marker threshold px {thr}\n")
        f.write("x,y\n")
        for X, Y, _, _ in pts: f.write(f"{X:.3f},{Y:.4g}\n")
    ov = im.crop((x0, y0, x1, y1)).copy(); d = ImageDraw.Draw(ov)
    for _, _, xc, yc in pts:
        d.line([(xc - 12, yc), (xc + 12, yc)], fill=(255, 0, 0), width=3); d.line([(xc, yc - 12), (xc, yc + 12)], fill=(255, 0, 0), width=3)
    d.rectangle([left, top, right, bottom], outline=(0, 160, 0), width=2)
    if a.mode == "line":
        for x, e in enumerate(ext):
            if e: d.point((x, (e[0] + e[1]) / 2), fill=(255, 140, 0))
    ov.save(os.path.join(a.out, a.name + "_overlay.png"))
    print(f"{a.name}: frame left {left} right {right} top {top} bottom {bottom}; line {line_h} px; {len(pts)} points")
    for X, Y, _, _ in pts: print(f"  x = {X:6.2f}   y = {Y:.3g}")

if __name__ == "__main__":
    main()
