#!/usr/bin/env python3
"""Applied figure: velocity and tracer fields on two planes of one condition.

    python3 postproc/figures/fig_slices.py <case_dir> --time 5000 --out results/applied/figures/D0_dir000_U10_fields.png

Reads the raw cutting-plane files written by postproc/slices.py (postProcessing/slicePlanes/<time>/
<field>_<plane>.raw). Top row: |U| and the all-sources tracer on the horizontal plane 1 m above
the roof. Bottom row: the same on the vertical centre plane. The tracer is on a log scale between
1e-4 and 1 (1 = undiluted source air).
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.tri as mtri
from matplotlib.colors import LogNorm
import style; style.use()

def load(case, t, field, plane):
    d = np.loadtxt(os.path.join(case, "postProcessing", "slicePlanes", str(t), f"{field}_{plane}.raw"), comments="#")
    x, y, z = d[:, 0], d[:, 1], d[:, 2]; v = d[:, 3:]
    mag = np.linalg.norm(v, axis=1) if v.shape[1] == 3 else v[:, 0]
    h, w = (x, z) if plane == "y0" else (x, y)
    tri = mtri.Triangulation(h, w)
    cx, cy = h[tri.triangles].mean(axis=1), w[tri.triangles].mean(axis=1)
    if plane == "y0": tri.set_mask((np.abs(cx) < 30) & (cy < 15))          # the building's hole
    return tri, mag

def outline(ax, plane):
    if plane == "y0":
        ax.add_patch(plt.Rectangle((-30, 0), 60, 15, fc="#efede9", ec=style.INK, lw=0.6))
    else:
        ax.add_patch(plt.Rectangle((-30, -20), 60, 40, fill=False, ec=style.INK, lw=0.6))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--time", default="5000"); ap.add_argument("--out", required=True)
    ap.add_argument("--xlim", nargs=2, type=float, default=[-60, 120]); ap.add_argument("--title", default=""); ap.add_argument("--umax", type=float, default=12.0)
    a = ap.parse_args()
    fig, axs = plt.subplots(2, 2, figsize=(style.FULL, 3.9), gridspec_kw={"height_ratios": [1.0, 0.55], "wspace": 0.18, "hspace": 0.25})
    for row, plane in enumerate(("zroof", "y0")):
        for col, (field, cm, norm, lab) in enumerate([("U", style.cmap("vel"), None, "$|U|$ [m/s]"),
                                                       ("sAll", style.cmap("conc"), LogNorm(1e-4, 1), "roof-source air fraction")]):
            ax = axs[row, col]; tri, v = load(a.case, a.time, field, plane)
            if norm is None: cf = ax.tripcolor(tri, v, cmap=cm, shading="gouraud", vmin=0, vmax=a.umax)
            else: cf = ax.tripcolor(tri, np.clip(v, 1e-4, 1), cmap=cm, shading="gouraud", norm=norm)
            outline(ax, plane); ax.set_xlim(a.xlim); ax.set_aspect("equal")
            if plane == "zroof": ax.set_ylim(-45, 45)
            else: ax.set_ylim(0, 45)
            for s in ax.spines.values(): s.set_visible(False)
            ax.tick_params(length=2)
            if row == 0:
                ax.set_title(lab)
                cb = fig.colorbar(cf, ax=axs[:, col], orientation="vertical", fraction=0.025, pad=0.02, aspect=30)
                cb.outline.set_visible(False); cb.ax.tick_params(length=2)
            if col: ax.tick_params(labelleft=False, left=False)
    axs[0, 0].set_ylabel("$y$ [m]   (1 m above the roof)"); axs[1, 0].set_ylabel("$z$ [m]   (centre plane)")
    axs[1, 0].set_xlabel("$x$ [m]"); axs[1, 1].set_xlabel("$x$ [m]")
    if a.title: fig.suptitle(a.title, x=0.01, ha="left", fontsize=9)
    style.save(fig, a.out, pdf=False)   # a filled-contour PDF is several MB; print("wrote", a.out)

if __name__ == "__main__":
    main()
