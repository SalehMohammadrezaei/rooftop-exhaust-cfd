#!/usr/bin/env python3
"""V2 figure: normalised dilution along the roof, wind tunnel (IRSST R-848) against CFD.

    python3 postproc/figures/fig_v2_irsst.py --out results/V2/figures/v2_dilution.png

Reads results/V2/*.json written by validation/V2/metrics.py. Four panels: stack height 1 and 3 m
(model scale 5 and 15 mm) at momentum ratios 1 and 3. Tunnel points are the digitised curve,
CFD is the Sct 0.4 line; the grey band is the factor-of-two envelope that defines FAC2.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import style; style.use()

CASES = [("hs1_M1_run1", "$h_s$ = 1 m, M = 1", "met"), ("hs1_M3_run1", "$h_s$ = 1 m, M = 3", "not met"),
         ("hs3_M1_run1", "$h_s$ = 3 m, M = 1", "met"), ("hs3_M3_run1", "$h_s$ = 3 m, M = 3", "not met")]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--results", default="results/V2"); ap.add_argument("--out", default="results/V2/figures/v2_dilution.png")
    a = ap.parse_args()
    fig, axs = plt.subplots(2, 2, figsize=(style.FULL, 4.6), sharex=True, sharey=True)
    for ax, (name, title, verdict) in zip(axs.flat, CASES):
        r = json.load(open(os.path.join(a.results, name + ".json")))
        rec = r["receptors"]["s04"]
        x = np.array([q["x_m"] for q in rec]); e = np.array([q["DN_exp"] for q in rec]); c = np.array([q["DN_cfd"] for q in rec])
        ax.fill_between(x, e / 2, e * 2, color=style.LIGHT, lw=0, label="tunnel, factor 2")
        ax.plot(x, e, "o", color=style.INK, ms=4, label="wind tunnel")
        ax.plot(x, c, "-", color=style.CFD, label="CFD, realizable $k$-$\\varepsilon$")
        ax.set_yscale("log"); ax.set_ylim(0.05, 20); ax.set_xlim(0, 52)
        ax.set_title(title)
        fac2 = r["scores"]["s04"]["FAC2"]
        ax.text(0.97, 0.06, f"FAC2 = {fac2:.1f}  ({verdict})", transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
                color=style.INK if verdict == "met" else style.CFD3)
    for ax in axs[1]: ax.set_xlabel("distance downwind of the stack, full scale [m]")
    for ax in axs[:, 0]: ax.set_ylabel("normalised dilution $D_N$")
    axs[0, 0].legend(loc="upper left", ncol=1)
    fig.tight_layout(h_pad=1.2, w_pad=1.0)
    style.save(fig, a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
