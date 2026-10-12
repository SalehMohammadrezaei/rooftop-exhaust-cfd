#!/usr/bin/env python3
"""V2 metrics: normalised dilution at the roof receptors against the digitised R-848 curve.

    metrics.py <case_dir> --ref data/digitised/irsst_r848/<curve>.csv --M 3 [--out results/V2/<name>.json]

D_N = D_r Q / (U_H H^2), D_r = C_e / C_r = 1 / s_r (exhaust s = 1), Q = Ve * pi d^2 / 4, Ve = M U_H.
Receptor x is the distance behind the stack in full-scale metres (model x * 200).
FAC2 = fraction of receptors with 0.5 <= D_cfd / D_exp <= 2 (acceptance >= 0.5, Project.md s.5).
"""
import argparse, csv, json, math, os

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--ref", required=True); ap.add_argument("--M", type=float, required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--UH", type=float, default=6.2); ap.add_argument("--H", type=float, default=0.075); ap.add_argument("--d", type=float, default=0.003)
    ap.add_argument("--xs", type=float, default=-0.2475); ap.add_argument("--scale", type=float, default=200.0, help="model x to full-scale metres")
    a = ap.parse_args(); UH, H, d, XS, SCALE = a.UH, a.H, a.d, a.xs, a.scale
    Ve = a.M * UH; Q = Ve * math.pi * d * d / 4
    dd = os.path.join(a.case, "postProcessing", "samplePoints"); t = sorted(os.listdir(dd), key=float)[-1]
    f = [x for x in os.listdir(os.path.join(dd, t)) if x.endswith(".xy")][0]
    names = [w for w in f[len("receptors_"):-3].split("_") if w.startswith("s") and w[1:].isdigit()]
    cfd = {}
    for line in open(os.path.join(dd, t, f)):
        v = [float(x) for x in line.split()]
        x_full = round((v[0] - XS) * SCALE)
        cfd[x_full] = dict(zip(names, v[4:4 + len(names)]))
    ref = {round(float(l.split(",")[0]) / 5) * 5: float(l.split(",")[1]) for l in open(a.ref) if not l.startswith("#") and not l.startswith("x")}
    res = {"case": os.path.basename(os.path.abspath(a.case)), "time": t, "M": a.M, "Ve": Ve, "Q_m3ps": Q, "ref": os.path.basename(a.ref), "receptors": {}, "scores": {}}
    for sn in names:
        rows = []
        for x in sorted(ref):
            if x not in cfd: continue
            s = cfd[x][sn]; DN = Q / (max(s, 1e-12) * UH * H * H)
            rows.append((x, ref[x], DN, DN / ref[x]))
        res["receptors"][sn] = [{"x_m": x, "DN_exp": round(e, 3), "DN_cfd": round(c, 3), "ratio": round(r, 3)} for x, e, c, r in rows]
        fac2 = sum(1 for *_, r in rows if 0.5 <= r <= 2) / len(rows)
        mg = math.exp(sum(math.log(r) for *_, r in rows) / len(rows))
        res["scores"][sn] = {"Sct": int(sn[1:]) / 10, "FAC2": round(fac2, 3), "geometric_mean_ratio": round(mg, 3), "n": len(rows), "pass_FAC2": bool(fac2 >= 0.5)}
    print(json.dumps(res["scores"], indent=1))
    for sn in names:
        print(f"\n{sn}: x[m]  D_exp  D_cfd  ratio"); [print(f"   {r['x_m']:3d}  {r['DN_exp']:6.2f} {r['DN_cfd']:6.2f} {r['ratio']:6.2f}") for r in res["receptors"][sn]]
    if a.out: os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
