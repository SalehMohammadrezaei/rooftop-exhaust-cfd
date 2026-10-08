#!/usr/bin/env python3
"""V0 acceptance metrics, computed from raw sample files of every generated case.

    metrics.py <cases_root>/V0 --params params/V0_empty_domain.json --out results/V0

For each case: max relative change of U and k between the inlet patch and the building
station over 0 < z < 3H, flatness between the last two written times, mass imbalance,
y+ and iteration count. Writes summary.json and summary.md. Pass/fail against the limit
fixed in the parameter file.
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "postproc"))
from abl_profiles import read_xy, rel_change   # noqa: E402

def profile(case, field, time, station):
    d = "samples_" + field
    z, v = read_xy(os.path.join(case, "postProcessing", d, time, f"{station}_{field}.xy"))
    if field == "U":
        v = [c[0] for c in v]
    return z, v

def flow(case, name, time):
    f = os.path.join(case, "postProcessing", name, "0", "surfaceFieldValue.dat")
    val = None
    for line in open(f):
        s = line.split()
        if s and not s[0].startswith("#") and float(s[0]) <= float(time):
            val = float(s[1])
    return val

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--params", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = json.load(open(a.params))
    H = P["inputs"]["H_m"]["value"]
    limit = P["acceptance"]["limit_pct"]
    rows = []
    for case in sorted(glob.glob(os.path.join(a.root, "*"))):
        rr = os.path.join(case, "run_record.json")
        if not os.path.exists(rr):
            continue
        R = json.load(open(rr)); C = json.load(open(os.path.join(case, "case_record.json")))
        times = sorted(os.listdir(os.path.join(case, "postProcessing", "samples_U")), key=float)
        t, tprev = times[-1], (times[-2] if len(times) > 1 else times[-1])
        row = dict(case=os.path.basename(case), **C["variant"], iterations=R["final_iteration"],
                   converged=R["converged_by_residualControl"], cells=R["cells"], wall_s=R["wall_time_s"],
                   y_over_z0=round(C["derived"]["y_over_z0"]["value"], 2), yplus=R["yplus_ground"])
        for f in ["U", "k"]:
            zr, vr = profile(case, f, t, "inletPatch")
            z, v = profile(case, f, t, "building")
            e, ze = rel_change(zr, vr, z, v, 0.0, 3 * H)
            row[f"d{f}_building_pct"] = round(100 * e, 2); row[f"d{f}_at_z"] = round(ze, 2) if ze is not None else None
            z2, v2 = profile(case, f, t, "outlet")
            e2, _ = rel_change(zr, vr, z2, v2, 0.0, 3 * H)
            row[f"d{f}_outlet_pct"] = round(100 * e2, 2)
            zp, vp = profile(case, f, tprev, "building")
            ef, _ = rel_change(zp, vp, z, v, 0.0, 3 * H)
            row[f"flat_{f}_prev_last_pct"] = round(100 * ef, 4)
        qi, qo = flow(case, "flowIn", t), flow(case, "flowOut", t)
        row["mass_imbalance_pct"] = round(100 * abs(qi + qo) / abs(qi), 6)
        # CLAUDE.md rule 5: converged = primary quantities flat within 1 % over the monitoring
        # window and balances closed within 1 %. residualControl is reported, not used.
        row["flat_ok"] = bool(row["flat_U_prev_last_pct"] < 1.0 and row["flat_k_prev_last_pct"] < 1.0)
        row["pass"] = bool(row["dU_building_pct"] < limit and row["dk_building_pct"] < limit
                           and row["mass_imbalance_pct"] < 1.0 and row["flat_ok"])
        rows.append(row)
    os.makedirs(a.out, exist_ok=True)
    json.dump(rows, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    cols = ["case", "iterations", "flat_ok", "y_over_z0", "dU_building_pct", "dk_building_pct", "dk_at_z",
            "dU_outlet_pct", "dk_outlet_pct", "mass_imbalance_pct", "pass"]
    with open(os.path.join(a.out, "summary.md"), "w") as f:
        f.write(f"# V0 summary. Acceptance: {P['acceptance']['quantity']} < {limit} %\n\n")
        f.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
    print(open(os.path.join(a.out, "summary.md")).read())

if __name__ == "__main__":
    main()
