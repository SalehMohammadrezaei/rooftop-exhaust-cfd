#!/usr/bin/env python3
"""The validation ladder as one diagram: what each stage tests, what it was compared with, and the verdict.

    python3 postproc/figures/fig_ladder.py --out docs/figures/ladder.png
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import style; style.use()

STEPS = [("V0", "empty domain", "ABL profiles hold\nfrom inlet to building", "analytical profiles", "met"),
         ("V1", "isolated building", "wake and roof\nseparation", "AIJ Case H\nwind tunnel", "velocity 0.60 (0.66)\nnot met, grid-\nindependent"),
         ("V2", "rooftop stack", "plume dilution\nalong the roof", "IRSST R-848\nwind tunnel", "M = 1 met\nM = 3 not met (jet)"),
         ("V2b", "full scale", "Re independence,\ninflow sensitivity", "V2 at 1:200", "met, 3 %\ninflow effect −40 %"),
         ("applied", "data hall", "intake dilution,\nchiller inlet rise", "acceptance limits\n(decision 0011)", "8-case matrix")]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="docs/figures/ladder.png"); a = ap.parse_args()
    fig, ax = plt.subplots(figsize=(style.FULL, 2.9)); ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 3.7)
    w, gap = 1.75, 0.3125
    for i, (tag, name, tests, against, verdict) in enumerate(STEPS):
        x = 0.1 + i * (w + gap)
        col = style.CFD if i < 4 else style.CFD2
        ax.add_patch(FancyBboxPatch((x, 1.6), w, 2.0, boxstyle="round,pad=0.02,rounding_size=0.08", fc="white", ec=col, lw=1.2))
        ax.text(x + 0.12, 3.45, tag, fontsize=10, fontweight="bold", color=col, va="top")
        ax.text(x + 0.12, 3.08, name, fontsize=7.5, color=style.GREY, va="top")
        ax.text(x + 0.12, 2.65, tests, fontsize=6.6, va="top", color=style.INK, linespacing=1.25)
        ax.text(x + 0.12, 1.4, "against", fontsize=6.5, color=style.GREY, va="top")
        ax.text(x + 0.12, 1.18, against, fontsize=7, va="top", color=style.INK)
        ax.text(x + 0.12, 0.55, verdict, fontsize=7, va="top", color=style.CFD3 if "not met" in verdict else style.INK)
        if i < 4: ax.add_patch(FancyArrowPatch((x + w + 0.03, 2.6), (x + w + gap - 0.03, 2.6), arrowstyle="-|>", mutation_scale=9, color=style.GREY, lw=0.9))
    style.save(fig, a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
