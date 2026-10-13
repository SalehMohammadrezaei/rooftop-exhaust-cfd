#!/usr/bin/env python3
"""V0 figure: does the atmospheric boundary layer survive the empty domain?

    python3 postproc/figures/fig_v0_abl.py --case ~/scratch/openfoam_cases/V0/realizableKE_atm_fixedShear_B --out results/V0/figures/v0_profiles.png

Three panels: velocity, turbulent kinetic energy and eddy viscosity against height, at the inlet,
at the building position (x = 0) and at the outlet. Reads the raw line samples written by the
sets function object (postProcessing/samples_<field>/<time>/<line>_<field>.xy, columns z then
the field). The inlet is the analytical Richards-Hoxey profile the case imposes.
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import style; style.use()

def load(case, field, line):
    d = os.path.join(case, "postProcessing", f"samples_{field}"); t = sorted(os.listdir(d), key=float)[-1]
    v = np.loadtxt(os.path.join(d, t, f"{line}_{field}.xy"))
    return v[:, 0], (np.linalg.norm(v[:, 1:4], axis=1) if v.shape[1] >= 4 else v[:, 1])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--case", required=True); ap.add_argument("--out", default="results/V0/figures/v0_profiles.png")
    ap.add_argument("--H", type=float, default=15.0); ap.add_argument("--title", default=None); a = ap.parse_args()
    case = os.path.expanduser(a.case)
    fig, axs = plt.subplots(1, 3, figsize=(style.FULL, 2.9), sharey=True)
    for ax, (field, lab) in zip(axs, [("U", "$U$ [m/s]"), ("k", "$k$ [m$^2$/s$^2$]"), ("nut", "$\\nu_t$ [m$^2$/s]")]):
        for line, name, c, ls in [("inletPatch", "inlet (imposed)", style.INK, "-"), ("building", "building position", style.CFD, "-"), ("outlet", "outlet", style.CFD2, "--")]:
            try: z, v = load(case, field, line)
            except (OSError, IndexError): continue
            ax.plot(v, z / a.H, ls, color=c, label=name)
        ax.set_xlabel(lab); ax.set_ylim(0, 4)
        ax.axhline(1.0, color=style.LIGHT, lw=0.7, zorder=0)
    axs[0].set_ylabel("$z/H$"); axs[0].legend(loc="lower right"); axs[1].set_title(a.title or os.path.basename(case))
    fig.tight_layout(w_pad=0.8)
    style.save(fig, a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
