#!/usr/bin/env python3
"""Grid convergence index (Roache / Celik et al. 2008) for the V1 three-grid study.

    gci.py <coarse_case> <medium_case> <fine_case> [--out results/V1/gci.json]

Quantities: wake-cavity probe Ux, reattachment probe Ux (last iteration of each run), drag force
on the building, and the hit rate on U from results/V1. The refinement ratio is the cube root of
the cell-count ratio. Observed order p from the three solutions; GCI_fine = 1.25 |e21| / (r^p - 1)
with e21 the relative difference fine-medium. Where the three values are not monotone, p is
reported as undefined and the plain fine-medium difference is given instead.
"""
import argparse, json, math, os, re

def last_probe(case, idx):
    for line in reversed(open(os.path.join(case, "postProcessing", "probesWake", "0", "U")).readlines()):
        if line.startswith("#"): continue
        v = [float(x) for x in re.sub(r"[()]", " ", line).split()]
        return v[1 + 3 * idx]
def last_force(case):
    for line in reversed(open(os.path.join(case, "postProcessing", "forcesBuilding", "0", "force.dat")).readlines()):
        if not line.startswith("#"): return float(line.split()[1])
def cells(case):
    return int(re.search(r"nCells:(\d+)", open(os.path.join(case, "constant", "polyMesh", "owner")).read()).group(1))

def gci(f1, f2, f3, r):
    """f1 fine, f2 medium, f3 coarse; equal r assumed (Celik eq. with r21 = r32)."""
    e21, e32 = f2 - f1, f3 - f2
    out = {"fine": f1, "medium": f2, "coarse": f3, "rel_change_fine_medium_pct": 100 * abs(e21) / abs(f1) if f1 else None}
    if e21 == 0 or e32 == 0 or (e32 / e21) <= 0:
        out["order_p"] = None; out["note"] = "not monotone or converged to machine precision; GCI undefined"
        return out
    p = math.log(abs(e32 / e21)) / math.log(r)
    gci_f = 1.25 * abs(e21 / f1) / (r ** p - 1) if f1 else None
    f_ext = f1 + e21 / (1 - r ** p) * (-1)  # Richardson extrapolate: f_ext = f1 - e21/(r^p - 1)... keep explicit below
    f_ext = f1 - e21 / (r ** p - 1)
    out.update({"order_p": round(p, 2), "GCI_fine_pct": round(100 * gci_f, 2), "richardson_extrapolated": f_ext})
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("coarse"); ap.add_argument("medium"); ap.add_argument("fine")
    ap.add_argument("--out", default=None); a = ap.parse_args()
    n3, n2, n1 = cells(a.coarse), cells(a.medium), cells(a.fine)
    r = ((n1 / n2) ** (1 / 3) + (n2 / n3) ** (1 / 3)) / 2
    res = {"cells": {"coarse": n3, "medium": n2, "fine": n1}, "refinement_ratio_mean": round(r, 3)}
    for name, fn in (("cavity_Ux", lambda c: last_probe(c, 1)), ("reattach_Ux", lambda c: last_probe(c, 2)), ("drag_N", last_force)):
        res[name] = gci(fn(a.fine), fn(a.medium), fn(a.coarse), r)
    hr = {}
    for g in ("coarse", "medium", "fine"):
        p = f"results/V1/{g}_realizableKE_run1.json"
        if os.path.exists(p): hr[g] = json.load(open(p))["hit_rate_U"]
    res["hit_rate_U"] = hr
    print(json.dumps(res, indent=1))
    if a.out: json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
