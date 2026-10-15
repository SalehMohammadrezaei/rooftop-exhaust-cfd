#!/usr/bin/env python3
"""Grid convergence index for the applied case (decision 0015): three meshes of one condition.

    python3 postproc/gci_applied.py results/applied/D0_dir180_U10_coarse.json results/applied/D0_dir180_U10.json results/applied/D0_dir180_U10_fine.json --out results/applied/gci_D0_dir180_U10.md

Quantities: intake dilution of flue exhaust, chiller inlet rise (mean and worst unit), flue
fraction at the louvres and the total chiller-air fraction at the intake. Refinement ratio from
the cube root of the cell-count ratio (run_record cells). Observed order p and GCI_fine with the
safety factor 1.25 (Celik et al. 2008), same formulae as validation/V1/gci.py. Where the three
values are not monotone, p is undefined and the fine-base difference is reported instead.
"""
import argparse, json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))

Q = [("intake_dilution_flues", "intake dilution"), ("chiller_rise_mean_K", "chiller rise, mean [K]"), ("chiller_rise_max_K", "chiller rise, worst unit [K]"),
     ("intake_fraction_from_flues", "flue fraction at the louvres"), ("intake_fraction_from_chillers_total", "chiller-air fraction at the intake")]

def gci(f1, f2, f3, r):
    e21, e32 = f2 - f1, f3 - f2
    out = {"fine": f1, "base": f2, "coarse": f3, "rel_change_fine_base_pct": 100 * abs(e21) / abs(f1)}
    if e21 == 0 or e32 == 0 or (e32 / e21) <= 0:
        out["order_p"] = None; out["GCI_fine_pct"] = None; out["note"] = "not monotone; GCI undefined, fine-base difference reported"; return out
    p = math.log(abs(e32 / e21)) / math.log(r)
    out.update({"order_p": p, "GCI_fine_pct": 100 * 1.25 * abs(e21 / f1) / (r ** p - 1), "richardson": f1 - e21 / (r ** p - 1)})
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("coarse"); ap.add_argument("base"); ap.add_argument("fine"); ap.add_argument("--out", default=None); a = ap.parse_args()
    R = {k: json.load(open(getattr(a, k))) for k in ("coarse", "base", "fine")}
    cells = {k: R[k].get("cells") for k in R}
    if any(v is None for v in cells.values()):
        for k in R:
            rr = os.path.join(os.path.expanduser("~/scratch/openfoam_cases/applied"), R[k]["case"], "run_record.json")
            if os.path.exists(rr): cells[k] = json.load(open(rr))["cells"]
    r = ((cells["fine"] / cells["base"]) ** (1 / 3) + (cells["base"] / cells["coarse"]) ** (1 / 3)) / 2
    lines = [f"# Grid convergence, {R['base']['case']} (decision 0015)", "",
             f"Cells: coarse {cells['coarse']:,}, base {cells['base']:,}, fine {cells['fine']:,}; mean refinement ratio r = {r:.3f}. "
             "GCI_fine = 1.25 |f_base - f_fine| / (f_fine (r^p - 1)), p the observed order (Celik et al. 2008).", "",
             "| quantity | coarse | base | fine | p | GCI fine | fine-base change |", "|---|---|---|---|---|---|---|"]
    res = {"cells": cells, "r": r}
    for key, lab in Q:
        g = gci(R["fine"][key], R["base"][key], R["coarse"][key], r); res[key] = g
        fmt = (lambda v: f"{v:.3g}") if "fraction" in key or "dilution" in key else (lambda v: f"{v:.2f}")
        lines.append(f"| {lab} | {fmt(g['coarse'])} | {fmt(g['base'])} | {fmt(g['fine'])} | " + (f"{g['order_p']:.2f}" if g["order_p"] else "undefined") +
                     " | " + (f"{g['GCI_fine_pct']:.1f} %" if g["GCI_fine_pct"] is not None else "n/a") + f" | {g['rel_change_fine_base_pct']:.1f} % |")
    amps = {k: R[k].get("convergence_max_rel_amplitude_pct_last_window") for k in R}
    lines += ["", "Receptor-fraction amplitude over the last window: " + ", ".join(f"{k} {v:.2f} %" for k, v in amps.items() if v is not None) + "."]
    txt = "\n".join(lines) + "\n"; print(txt)
    if a.out: open(a.out, "w").write(txt); json.dump(res, open(a.out.replace(".md", ".json"), "w"), indent=1)

if __name__ == "__main__":
    main()
