#!/usr/bin/env python3
"""Tracer convergence and scoring report for a V1 scalar case.

    tracer_report.py <case_dir> --data data/raw/aij_caseH/RS_caseH.csv [--out results/V1/tracer_report.json]

1. Balance: tracer flux out of the outlet (sum of phi * s over outlet faces, from the reconstructed
   field files) at every written time, as a fraction of the injected Q. Converged when within 1 %.
2. Probe flatness: tracer value at the wake probes over the last 500 iterations (max relative change).
3. Scores per Schmidt number on points with measured c > 1 ppm: FAC2, fractional bias FB,
   geometric mean bias MG, and the breakdown by region and plane.
"""
import argparse, csv, json, math, os, re, collections
UH, H, Q = 3.23, 0.2, 5.83e-6; FAC = UH * H * H / Q

def patch_values(path, patch):
    s = open(path).read()
    m = re.search(r"\n\s+" + patch + r"\s*\{(.*?)\n\s+\}", s, re.S); blk = m.group(1)
    v = re.search(r"value\s+nonuniform List<scalar>\s*\n?(\d+)\s*\n\((.*?)\n\)", blk, re.S)
    if v: return [float(x) for x in v.group(2).split()]
    u = re.search(r"value\s+uniform\s+([-\d.e+]+)", blk); return None if not u else float(u.group(1))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--data", required=True); ap.add_argument("--out", default=None)
    a = ap.parse_args(); c = a.case
    times = sorted([d for d in os.listdir(c) if d.isdigit()], key=int)
    scalars = sorted([f for f in os.listdir(os.path.join(c, times[-1])) if re.fullmatch(r"s\d\d", f)])
    rep = {"case": os.path.basename(os.path.abspath(c)), "times": times, "scalars": scalars, "balance": {}}
    for t in times:
        phi = patch_values(os.path.join(c, t, "phi"), "outlet")
        if not isinstance(phi, list): continue
        rep["balance"][t] = {}
        for sn in scalars:
            s = patch_values(os.path.join(c, t, sn), "outlet")
            if isinstance(s, list): rep["balance"][t][sn] = round(100 * sum(p * q for p, q in zip(phi, s)) / Q, 2)
    # probes
    pdirs = sorted([d for d in os.listdir(os.path.join(c, "postProcessing", "probesWake"))], key=int)
    rep["probe_flatness_last500_pct"] = {}
    for sn in scalars:
        f = os.path.join(c, "postProcessing", "probesWake", pdirs[-1], sn)
        if not os.path.exists(f): continue
        rows = [[float(x) for x in l.split()] for l in open(f) if not l.startswith("#")]
        last = rows[-1][0]; win = [r for r in rows if r[0] >= last - 500]
        fl = []
        for i in (1, 2, 3):
            vals = [r[i] for r in win]; m = sum(vals) / len(vals)
            fl.append(round(100 * (max(vals) - min(vals)) / abs(m), 3) if m else None)
        rep["probe_flatness_last500_pct"][sn] = fl
    # scores
    d = os.path.join(c, "postProcessing", "samplePoints"); t = sorted(os.listdir(d), key=float)[-1]
    fname = [x for x in os.listdir(os.path.join(d, t)) if x.endswith(".xy")][0]
    names = [w for w in fname[len("measured_"):-3].split("_") if re.fullmatch(r"s\d\d", w)]
    S = {}
    for line in open(os.path.join(d, t, fname)):
        v = [float(x) for x in line.split()]; S[(round(v[0], 5), round(v[1], 5), round(v[2], 5))] = dict(zip(names, v[4:4 + len(names)]))
    exp = [r for r in csv.DictReader(open(a.data)) if float(r["<c> (ppm)"]) > 1.0]
    def region(x, z):
        if x <= 0: return "beside/above building"
        if x <= 0.2: return "near wake <=1H"
        return "far wake >1H"
    def stats(p):
        n = len(p); me = sum(e for e, _ in p) / n; mc = sum(m for _, m in p) / n
        return {"n": n, "FAC2": round(sum(1 for e, m in p if 0.5 <= m / e <= 2) / n, 3), "FB": round(2 * (me - mc) / (me + mc), 3),
                "MG": round(math.exp(sum(math.log(m / e) for e, m in p) / n), 3), "mean_exp": round(me, 3), "mean_cfd": round(mc, 3)}
    rep["scores"] = {}
    for sn in names:
        allp, reg, pl = [], collections.defaultdict(list), collections.defaultdict(list)
        for r in exp:
            key = (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5))
            if key not in S: continue
            e = float(r["<c> (ppm)"]) * 1e-6 * FAC; m = max(S[key][sn] * FAC, 1e-9)
            allp.append((e, m)); reg[region(key[0], key[2])].append((e, m))
            pl["y=0" if abs(key[1]) < 1e-6 else f"z={key[2]:g}"].append((e, m))
        rep["scores"][sn] = {"Sct": int(sn[1:]) / 10, "all": stats(allp), "by_region": {k: stats(v) for k, v in reg.items()},
                             "by_plane": {k: stats(v) for k, v in sorted(pl.items())},
                             "pass": bool(stats(allp)["FAC2"] >= 0.5 and abs(stats(allp)["FB"]) <= 0.3)}
    print(json.dumps(rep, indent=1))
    if a.out: json.dump(rep, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
