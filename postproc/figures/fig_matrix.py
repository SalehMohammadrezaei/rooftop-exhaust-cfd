#!/usr/bin/env python3
"""Applied figure: the source-to-receptor matrix of one condition and what it means for the plant.

    python3 postproc/figures/fig_matrix.py results/applied/D0_dir000_U10.json --case applied/case_by_hand --out results/applied/figures/D0_dir000_U10_matrix.png

Left: F, the fraction of each receptor's intake air that came from each source (log colour).
Middle: chiller inlet temperature rise per unit from F with the 12 K discharge rise and feedback,
against the 2 K / 4 K limits. Right: receptor fractions against tracer iteration, the convergence
evidence (from postProcessing/recv_<receptor>/<time>/surfaceFieldValue.dat).
"""
import argparse, glob, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import style; style.use()

def history(case, recv):
    rows = []
    for d in sorted(glob.glob(os.path.join(case, "postProcessing", f"recv_{recv}", "*")), key=lambda p: float(os.path.basename(p))):
        f = os.path.join(d, "surfaceFieldValue.dat"); names = None
        for line in open(f):
            if line.startswith("# Time"): names = [re.sub(r"^\w+\((\w+)\)$", r"\1", h) for h in line[1:].split()][1:]; continue
            if line.startswith("#"): continue
            v = line.split(); rows.append((float(v[0]), dict(zip(names, map(float, v[1:])))))
    while rows and sum(rows[0][1].values()) == 0: rows.pop(0)      # the flow stage, before the tracers were released
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("json"); ap.add_argument("--case", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); r = json.load(open(a.json))
    S, R, F = r["sources"], r["receptors"], np.array(r["F"])
    slab = [s.replace("sC", "chiller ").replace("sF", "flues") for s in S]
    rlab = [x.replace("chiller_in_", "chiller ").replace("intake_louvre_pos", "intake +y").replace("intake_louvre_neg", "intake −y") for x in R]
    fig = plt.figure(figsize=(style.FULL, 3.6)); gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 0.9, 1.1], wspace=0.75)
    ax = fig.add_subplot(gs[0])
    im = ax.imshow(np.clip(F, 1e-6, 1), cmap=style.cmap("conc"), norm=LogNorm(1e-4, 1), aspect="auto")
    ax.set_xticks(range(len(S))); ax.set_xticklabels(slab, rotation=90); ax.set_yticks(range(len(R))); ax.set_yticklabels(rlab)
    ax.set_title("$F$: rows receptors, columns sources")
    for s in ("top", "right", "left", "bottom"): ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.05, pad=0.2, aspect=25); cb.outline.set_visible(False); cb.ax.tick_params(length=2)
    ax2 = fig.add_subplot(gs[1])
    rise = np.array(r["chiller_inlet_temperature_rise_K"]); n = len(rise); units = np.arange(1, n + 1)
    ax2.barh(units, rise, color=[style.CFD3 if v > 4 else style.CFD2 if v > 2 else style.CFD for v in rise], height=0.7)
    ax2.axvline(2, color=style.INK, lw=0.8, ls="--"); ax2.axvline(4, color=style.INK, lw=0.8, ls=":")
    ax2.set_yticks(units); ax2.set_yticklabels([f"chiller {u}" for u in units]); ax2.invert_yaxis()
    ax2.set_xlabel(f"inlet rise [K]\nmean {r['chiller_rise_mean_K']:.1f}, worst {r['chiller_rise_max_K']:.1f}\n- - 2 K mean limit   · · 4 K unit limit", fontsize=7.5); ax2.set_title("chiller inlet rise")
    ax2.set_xlim(0, max(12, rise.max() * 1.15))
    ax3 = fig.add_subplot(gs[2])
    worst = R[int(np.argmax(F[:len(rise), :n].sum(axis=1)))] if n else R[0]
    for recv, c in [(worst, style.CFD), ("intake_louvre_pos", style.CFD2)]:
        h = history(a.case, recv)
        if not h: continue
        t = np.array([q[0] for q in h]); tot = np.array([sum(v for k, v in q[1].items() if k.startswith("sC")) for q in h])
        t0 = t[0]; ax3.plot(t - t0, tot, color=c, label=recv.replace("chiller_in_", "chiller ").replace("intake_louvre_pos", "intake"))
    ax3.set_xlabel("tracer iteration"); ax3.set_ylabel("chiller-air fraction"); ax3.set_title("convergence", fontsize=8)
    ax3.legend(loc="lower right"); ax3.set_ylim(bottom=0)
    style.save(fig, a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
