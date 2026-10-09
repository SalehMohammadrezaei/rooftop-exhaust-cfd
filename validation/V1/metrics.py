#!/usr/bin/env python3
"""V1 validation metrics from the raw files: hit rate for velocity (VDI 3783/9), and, once a
concentration field exists, FAC2 and fractional bias (COST 732).

    metrics.py <case_dir> --data data/raw/aij_caseH/RS_caseH.csv [--time latest] [--out results/V1/<name>.json]

Hit rate q = fraction of points where |CFD - exp| / |exp| <= D (0.25) OR |CFD - exp| <= W (0.05 * U_H),
computed on the velocity component, per component and overall. Acceptance: q >= 0.66 (Project.md s.5).
Both tolerances are the VDI 3783/9 values; W uses the wind-tunnel reference speed U_H = 3.23 m/s.
"""
import argparse, csv, json, os, math
UH, H, D, W_FRAC = 3.23, 0.2, 0.25, 0.05

def read_cloud(path, scalars):
    """raw cloud file written by the sets function object: the writer sorts the field names, so
    with fields (U k) the columns are x y z k Ux Uy Uz, and with extra tracers s04.. they sit
    between k and U: x y z k s04 ... Ux Uy Uz.  Returns {(x,y,z): (k, {sname: value}, [Ux,Uy,Uz])}."""
    out = {}
    ns = len(scalars)
    for line in open(path):
        s = line.split()
        if not s or s[0].startswith("#"): continue
        v = [float(x) for x in s]
        out[(round(v[0], 5), round(v[1], 5), round(v[2], 5))] = (v[3], dict(zip(scalars, v[4:4+ns])), v[4+ns:7+ns])
    return out

def hit_rate(pairs):
    hits = sum(1 for e, c in pairs if abs(c - e) <= D * abs(e) or abs(c - e) <= W_FRAC * UH)
    return hits / len(pairs) if pairs else float("nan"), len(pairs)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--data", required=True)
    ap.add_argument("--time", default="latest"); ap.add_argument("--out", default=None); a = ap.parse_args()
    d = os.path.join(a.case, "postProcessing", "samplePoints")
    t = sorted(os.listdir(d), key=float)[-1] if a.time == "latest" else a.time
    files = [f for f in os.listdir(os.path.join(d, t)) if f.startswith("measured_") and f.endswith(".xy")]
    fname = files[0]
    scalars = [w for w in fname[len("measured_"):-3].split("_") if w.startswith("s") and w[1:].isdigit()]
    S = read_cloud(os.path.join(d, t, fname), scalars)
    exp = list(csv.DictReader(open(a.data)))
    pairs = {c: [] for c in ("U", "V", "W", "k")}; missing = 0
    for r in exp:
        key = (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5))
        if float(r["U (m/s)"]) <= -999: continue
        if key not in S: missing += 1; continue
        kc, sc, Uc = S[key]
        for i, c in enumerate(("U", "V", "W")): pairs[c].append((float(r[f"{c} (m/s)"]), Uc[i]))
        pairs["k"].append((float(r["k (m2/s2)"]), kc))
    res = {"case": os.path.basename(os.path.abspath(a.case)), "time": t, "points_missing": missing}
    allUVW = []
    for c in ("U", "V", "W", "k"):
        q, n = hit_rate(pairs[c]); res[f"hit_rate_{c}"] = round(q, 3); res[f"n_{c}"] = n
        if c in ("U", "V", "W"): allUVW += pairs[c]
    q, n = hit_rate(allUVW); res["hit_rate_UVW"] = round(q, 3)
    res["pass_velocity"] = bool(res["hit_rate_U"] >= 0.66)
    res["acceptance"] = "hit rate on U >= 0.66 (VDI 3783/9: D = 0.25, W = 0.05 U_H)"

    # concentration: C* = c U_H H^2 / Q; tunnel c in ppm -> volume fraction; CFD tracer is a volume fraction
    if scalars:
        Q = 5.83e-6; fac = UH * H * H / Q
        thr_ppm = 1.0
        res["conc_threshold_ppm"] = thr_ppm
        res["conc_acceptance"] = "FAC2 >= 0.5 and |FB| <= 0.3 on points with measured c > threshold (COST 732)"
        for sname in scalars:
            pairs = []
            for r in exp:
                key = (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5))
                c = float(r["<c> (ppm)"])
                if c <= -999 or c <= thr_ppm or key not in S: continue
                pairs.append((c * 1e-6 * fac, S[key][1][sname] * fac))
            n = len(pairs)
            fac2 = sum(1 for e, m in pairs if 0.5 <= m / e <= 2.0) / n
            me, mm = sum(e for e, _ in pairs) / n, sum(m for _, m in pairs) / n
            fb = 2 * (me - mm) / (me + mm)
            sct = int(sname[1:]) / 10
            res[f"FAC2_Sct{sct}"] = round(fac2, 3); res[f"FB_Sct{sct}"] = round(fb, 3)
            res[f"pass_conc_Sct{sct}"] = bool(fac2 >= 0.5 and abs(fb) <= 0.3)
            res["conc_points_used"] = n; res["conc_Cstar_mean_exp"] = round(me, 3)
    print(json.dumps(res, indent=1))
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
