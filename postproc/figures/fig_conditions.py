#!/usr/bin/env python3
"""Applied figure: the two primary quantities across every condition in results/applied.

    python3 postproc/figures/fig_conditions.py results/applied --out results/applied/figures/conditions.png

Left: flue dilution at the intake per condition on a log axis against the limit of 2000.
Right: chiller inlet rise, mean (bar) and worst unit (marker), against the 2 K and 4 K limits.
Conditions whose tracer stage had not settled (last-window amplitude above 1 %) are hatched.
"""
import argparse, glob, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import style; style.use()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("results"); ap.add_argument("--out", required=True); a = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(a.results, "*.json"))):
        r = json.load(open(f)); m = re.match(r"(D\d)_dir(\d+)_U([\d.]+)$", r["case"])   # grid-study cases carry a suffix and are summarised by gci_applied.py
        if not m: continue
        rows.append((m.group(1), int(m.group(2)), float(m.group(3)), r))
    rows.sort(key=lambda t: (t[2], t[1], t[0]))
    lab = [f"{v}  {d}°  {u:g} m/s" for v, d, u, _ in rows]
    dil = np.array([r["intake_dilution_flues"] for *_, r in rows]); mean = np.array([r["chiller_rise_mean_K"] for *_, r in rows])
    worst = np.array([r["chiller_rise_max_K"] for *_, r in rows]); amp = np.array([r.get("convergence_max_rel_amplitude_pct_last_window", 0) for *_, r in rows])
    y = np.arange(len(rows))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(style.FULL, 0.36 * len(rows) + 1.1), sharey=True, gridspec_kw={"wspace": 0.12})
    for ax in (ax1, ax2):
        ax.set_yticks(y); ax.set_ylim(len(rows) - 0.5, -0.5); ax.tick_params(axis="y", length=0)
    ax1.set_yticklabels(lab)
    for i in y:
        h = "////" if amp[i] > 1 else None
        ax1.barh(i, dil[i], color=style.CFD if dil[i] >= 2000 else style.CFD3, height=0.62, hatch=h, edgecolor="white", lw=0)
        ax2.barh(i, mean[i], color=style.CFD if mean[i] <= 2 else style.CFD3, height=0.6, hatch=h, edgecolor="white", lw=0)
    ax2.plot(worst, y, "o", color=style.INK, ms=4, label="worst unit")
    for i in y:
        ax1.text(dil[i] * 1.4, i, f"{dil[i]:,.0f}" if dil[i] < 1e5 else f"{dil[i]:.0e}", va="center", fontsize=6.5, color=style.GREY)
        ax2.text(worst[i] + 0.35, i, f"{mean[i]:.1f} / {worst[i]:.1f}", va="center", fontsize=6.5, color=style.GREY)
    ax1.set_xscale("log"); ax1.axvline(2000, color=style.INK, lw=0.8, ls="--"); ax1.text(2000, 1.02, "limit 2000", ha="center", fontsize=7, transform=ax1.get_xaxis_transform())
    ax1.set_xlabel("flue dilution at the intake"); ax1.set_xlim(1e1, 1e9)
    ax2.axvline(2, color=style.INK, lw=0.8, ls="--"); ax2.axvline(4, color=style.INK, lw=0.8, ls=":")
    ax2.text(1.85, 1.02, "mean 2 K", ha="right", fontsize=7, transform=ax2.get_xaxis_transform()); ax2.text(4.15, 1.02, "unit 4 K", ha="left", fontsize=7, transform=ax2.get_xaxis_transform())
    ax2.set_xlabel("chiller inlet rise [K]"); ax2.set_xlim(0, max(15, worst.max() * 1.25)); ax2.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), fontsize=7, handletextpad=0.3)
    if (amp > 1).any(): fig.text(0.01, 0.0, "hatched: tracer stage not settled (amplitude above 1 % over the last window)", fontsize=7, color=style.GREY, va="top")
    style.save(fig, a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
