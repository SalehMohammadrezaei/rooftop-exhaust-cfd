#!/usr/bin/env python3
"""V1 figure: AIJ Case H (isolated 1:1:2 building) measured against CFD.

    python3 postproc/figures/fig_v1_aij.py --out results/V1/figures/v1_velocity.png

Top: streamwise velocity on the centre plane at five stations, measured (AIJ wind tunnel) against
the medium and fine grids. Bottom left: every measured point with a valid velocity, CFD against
measured, with the VDI 3783/9 hit-rate band (25 % of the measured value or 0.05 U_H, whichever is
larger). Reads the raw sample clouds the sets function object wrote
(postProcessing/samplePoints/<time>/measured_k_U.xy) and the AIJ CSV.
"""
import argparse, csv, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import style; style.use()
UH, H = 3.23, 0.2
STATIONS = [-0.15, 0.0, 0.075, 0.25, 0.4]     # x in m; building from -0.05 to 0.05, roof at z = 0.2

def read_cloud(path):
    d = {}
    for line in open(path):
        s = line.split()
        if not s or s[0].startswith("#"): continue
        v = [float(x) for x in s]; d[(round(v[0], 5), round(v[1], 5), round(v[2], 5))] = v[4]   # Ux
    return d

def latest(case):
    d = os.path.join(case, "postProcessing", "samplePoints"); t = sorted(os.listdir(d), key=float)[-1]
    return read_cloud(os.path.join(d, t, "measured_k_U.xy"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="data/raw/aij_caseH/RS_caseH.csv")
    ap.add_argument("--medium", default="validation/V1/case_medium"); ap.add_argument("--fine", default="validation/V1/case_fine")
    ap.add_argument("--out", default="results/V1/figures/v1_velocity.png"); a = ap.parse_args()
    exp = [r for r in csv.DictReader(open(a.data)) if float(r["U (m/s)"]) > -999]
    med, fin = latest(a.medium), latest(a.fine)
    fig = plt.figure(figsize=(style.FULL, 5.0))
    gs = fig.add_gridspec(2, 5, height_ratios=[1, 1.15], hspace=0.55, wspace=0.25)
    axs = [fig.add_subplot(gs[0, i]) for i in range(5)]
    for i, (ax, xs) in enumerate(zip(axs, STATIONS)):
        rows = sorted([r for r in exp if abs(float(r["x (m)"]) - xs) < 1e-6 and float(r["y (m)"]) == 0], key=lambda r: float(r["z (m)"]))
        z = np.array([float(r["z (m)"]) for r in rows]) / H; ue = np.array([float(r["U (m/s)"]) for r in rows]) / UH
        key = [(round(float(r["x (m)"]), 5), 0.0, round(float(r["z (m)"]), 5)) for r in rows]
        um = np.array([med.get(k, np.nan) for k in key]) / UH; uf = np.array([fin.get(k, np.nan) for k in key]) / UH
        ax.plot(ue, z, "o", color=style.INK, ms=3, label="measured")
        ax.plot(um, z, "-", color=style.CFD, label="CFD, medium grid")
        ax.plot(uf, z, "--", color=style.CFD2, label="CFD, fine grid")
        if abs(xs) <= 0.05: ax.axhspan(0, 1, color=style.GREY, alpha=0.3, lw=0)
        ax.axvline(0, color=style.LIGHT, lw=0.7, zorder=0)
        ax.set_xlim(-0.5, 1.5); ax.set_ylim(0, 2.6); ax.set_title(f"$x/H$ = {xs / H:g}")
        if i: ax.tick_params(labelleft=False)
        ax.set_xticks([0, 0.5, 1.0, 1.5])
    axs[0].set_ylabel("$z/H$"); axs[2].set_xlabel("$U/U_H$"); axs[1].legend(loc="lower left", fontsize=6.5, handlelength=1.3, frameon=True, framealpha=0.9, edgecolor="none")
    # scatter
    ax2 = fig.add_subplot(gs[1, 0:2])
    pe, pm = [], []
    for r in exp:
        k = (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5))
        if k in med: pe.append(float(r["U (m/s)"]) / UH); pm.append(med[k] / UH)
    pe, pm = np.array(pe), np.array(pm)
    lim = np.array([-0.6, 1.5]); e = np.linspace(*lim, 200); tol = np.maximum(0.25 * np.abs(e), 0.05)
    ax2.fill_between(e, e - tol, e + tol, color=style.LIGHT, lw=0, label="hit-rate band")
    ax2.plot(lim, lim, "-", color=style.GREY, lw=0.8)
    ax2.plot(pe, pm, "o", color=style.CFD, ms=2.2, alpha=0.75, mew=0)
    hit = np.mean((np.abs(pm - pe) <= 0.25 * np.abs(pe)) | (np.abs(pm - pe) <= 0.05))
    ax2.text(0.04, 0.96, f"hit rate {hit:.2f}  (limit 0.66)\n{len(pe)} points", transform=ax2.transAxes, va="top", fontsize=8)
    ax2.set_xlim(lim); ax2.set_ylim(lim); ax2.set_aspect("equal")
    ax2.set_xlabel("measured $U/U_H$"); ax2.set_ylabel("CFD $U/U_H$"); ax2.set_title("all measured points, medium grid")
    # error against height class: where the model misses
    ax3 = fig.add_subplot(gs[1, 2:5])
    zc = np.array([float(r["z (m)"]) for r in exp if (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5)) in med]) / H
    xc = np.array([float(r["x (m)"]) for r in exp if (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5)) in med]) / H
    hitp = (np.abs(pm - pe) <= 0.25 * np.abs(pe)) | (np.abs(pm - pe) <= 0.05)
    ax3.scatter(xc[hitp], zc[hitp], s=6, color=style.CFD, lw=0, label="within band")
    ax3.scatter(xc[~hitp], zc[~hitp], s=9, color=style.CFD3, lw=0, label="outside band")
    ax3.add_patch(plt.Rectangle((-0.25, 0), 0.5, 1.0, color=style.GREY, alpha=0.3, lw=0))
    ax3.set_xlabel("$x/H$"); ax3.set_ylabel("$z/H$"); ax3.set_title("where the misses are (centre plane and off-centre points)")
    ax3.legend(loc="upper right", fontsize=7, markerscale=1.5); ax3.set_ylim(0, 2.6); ax3.set_xlim(-1.1, 2.1)
    style.save(fig, a.out); print("wrote", a.out, "hit", round(hit, 3))

if __name__ == "__main__":
    main()
