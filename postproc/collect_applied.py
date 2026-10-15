#!/usr/bin/env python3
"""Collect the applied-run results into the design table (Project.md sections 8 and 9).

    collect_applied.py results/applied --limits docs/decisions/0011-acceptance-limits.md --out results/applied/summary.md

Reads every <variant>_dir<deg>_U<speed>.json written by postproc/matrix.py, tabulates intake
dilution of the flue scalar, the chiller array-mean and worst-unit inlet temperature rise, and the
convergence and balance checks; finds the governing condition for each primary quantity (the
worst over directions and speeds) and marks each run against the limits (intake dilution >= 2000;
mean rise <= 2 K, worst unit <= 4 K).
"""
import argparse, glob, json, os, re
ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--out", default=None); a = ap.parse_args()
LIM = {"dilution": 2000.0, "mean_K": 2.0, "max_K": 4.0}
rows = []
for f in sorted(glob.glob(os.path.join(a.root, "*.json"))):
    r = json.load(open(f)); m = re.match(r"(D\d)_dir(\d+)_U([\d.]+)$", r["case"])   # grid-study cases carry a suffix and are summarised by gci_applied.py
    if not m: continue
    rows.append({"variant": m.group(1), "dir": int(m.group(2)), "U": float(m.group(3)), "dilution": r["intake_dilution_flues"], "F_flue": r["intake_fraction_from_flues"],
                 "mean_K": r["chiller_rise_mean_K"], "max_K": r["chiller_rise_max_K"], "worst_unit": r["chiller_rise_argmax"], "self": max(r["chiller_self_recirculation_diag"]),
                 "balance_pct": r["sumF_vs_sAll_max_rel_diff_pct"], "conv_pct": r["convergence_max_rel_amplitude_pct_last_window"]})
rows.sort(key=lambda x: (x["variant"], x["U"], x["dir"]))
lines = ["# Applied runs: primary quantities per condition", "", "Limits (decision 0011): intake dilution of flue exhaust >= 2000; chiller inlet rise mean <= 2 K, worst unit <= 4 K. Convergence: last-200-iteration amplitude of the receptor fractions; balance: sum of tagged scalars against the all-sources scalar.", "",
         "| variant | dir [deg] | U_H [m/s] | intake dilution | flue fraction at intake | chiller rise mean [K] | worst unit [K] (which) | max self-recirc. | balance [%] | conv. amp. [%] | dilution ok | chiller ok |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for x in rows:
    lines.append(f"| {x['variant']} | {x['dir']} | {x['U']:g} | {x['dilution']:.3g} | {x['F_flue']:.2e} | {x['mean_K']:.2f} | {x['max_K']:.2f} ({x['worst_unit']}) | {x['self']:.3f} | {x['balance_pct']:.2f} | {x['conv_pct']:.2f} | {'yes' if x['dilution']>=LIM['dilution'] else 'NO'} | {'yes' if x['mean_K']<=LIM['mean_K'] and x['max_K']<=LIM['max_K'] else 'NO'} |")
d0 = [x for x in rows if x["variant"] == "D0"]
if d0:
    g1 = min(d0, key=lambda x: x["dilution"]); g2 = max(d0, key=lambda x: x["max_K"])
    lines += ["", f"Governing condition for intake dilution (D0): {g1['dir']} deg at {g1['U']:g} m/s, dilution {g1['dilution']:.3g}.",
              f"Governing condition for chiller inlet rise (D0): {g2['dir']} deg at {g2['U']:g} m/s, worst unit {g2['max_K']:.2f} K, mean {g2['mean_K']:.2f} K."]
txt = "\n".join(lines) + "\n"; print(txt)
if a.out: open(a.out, "w").write(txt)
