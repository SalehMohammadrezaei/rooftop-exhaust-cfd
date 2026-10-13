#!/usr/bin/env python3
"""Source-to-receptor matrix F and the two primary quantities (Project.md sections 4 and 9).

    matrix.py <case_dir> [--out results/applied/<name>.json] [--dT 12] [--window 200]

Reads postProcessing/recv_<sink>/<time>/surfaceFieldValue.dat (area-averaged tagged scalars on
each sink patch), takes the mean over the last --window iterations and the amplitude as the
convergence record, and builds F_ij = fraction of the air entering receptor i that came from
source j (j = chillers 1..10, flues). Checks sum_j F_ij against sAll (must agree within 1 %).
Intake dilution D = 1 / F_(intake, flue) with the two louvres flow-weighted (equal flows).
Chiller inlet temperature rise with feedback: each chiller discharges at its own inlet
temperature plus dT; theta_i = sum_j F_ij (theta_j + dT) over chillers only (flues are not heat
sources in the passive limit; their heat is a separate statement) -> (I - F_cc) theta = F_cc dT 1.
"""
import argparse, json, os, re
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--out", default=None); ap.add_argument("--dT", type=float, default=12.0); ap.add_argument("--window", type=int, default=200); a = ap.parse_args()
sinks = [f"chiller_in_{i:02d}" for i in range(1, 11)] + ["intake_louvre_pos", "intake_louvre_neg"]
names = [f"sC{i:02d}" for i in range(1, 11)] + ["sF", "sAll"]
def read(p):
    d = os.path.join(a.case, "postProcessing", f"recv_{p}"); t = sorted(os.listdir(d), key=float)[-1]
    rows = []; hdr = None
    for l in open(os.path.join(d, t, "surfaceFieldValue.dat")):
        if l.startswith("#"):
            if "Time" in l: hdr = [re.sub(r"^\w+\((\w+)\)$", r"\1", h) for h in l.strip("# \n").split()]   # areaAverage(sC01) -> sC01
            continue
        rows.append([float(x) for x in l.split()])
    rows = np.array(rows); cols = {h: i for i, h in enumerate(hdr)}
    win = rows[rows[:, 0] >= rows[-1, 0] - a.window]
    return {n: (win[:, cols[n]].mean(), win[:, cols[n]].max() - win[:, cols[n]].min()) for n in names if n in cols}
R = {p: read(p) for p in sinks}
F = np.array([[R[p][n][0] for n in names[:11]] for p in sinks]); S = np.array([R[p]["sAll"][0] for p in sinks])
amp = max(R[p][n][1] / max(R[p][n][0], 1e-12) for p in sinks for n in names if R[p][n][0] > 1e-6)
F_cc = F[:10, :10]; theta = np.linalg.solve(np.eye(10) - F_cc, F_cc @ (a.dT * np.ones(10)))
intake_F = F[10:12].mean(axis=0)   # equal louvre flows
res = {"case": os.path.basename(os.path.abspath(a.case)), "sources": names[:11], "receptors": sinks,
       "F": F.round(6).tolist(), "sumF_vs_sAll_max_rel_diff_pct": float(100 * np.max(np.abs(F.sum(axis=1) - S) / np.maximum(S, 1e-12))),
       "convergence_max_rel_amplitude_pct_last_window": float(100 * amp),
       "intake_fraction_from_flues": float(intake_F[10]), "intake_dilution_flues": float(1 / max(intake_F[10], 1e-12)),
       "intake_fraction_from_chillers_total": float(intake_F[:10].sum()),
       "chiller_inlet_temperature_rise_K": theta.round(3).tolist(), "chiller_rise_mean_K": float(theta.mean()), "chiller_rise_max_K": float(theta.max()), "chiller_rise_argmax": int(theta.argmax()) + 1,
       "chiller_self_recirculation_diag": np.diag(F_cc).round(4).tolist()}
print(json.dumps({k: v for k, v in res.items() if k != "F"}, indent=1))
if a.out: os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)
