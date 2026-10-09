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

def read_cloud(path):
    """raw cloud file written by the sets function object with fields (U k): the writer sorts the
    field names, so the columns are x y z k Ux Uy Uz.  Returns {(x,y,z): (k, [Ux,Uy,Uz])}."""
    out = {}
    for line in open(path):
        s = line.split()
        if not s or s[0].startswith("#"): continue
        v = [float(x) for x in s]
        out[(round(v[0], 5), round(v[1], 5), round(v[2], 5))] = (v[3], v[4:7])
    return out

def hit_rate(pairs):
    hits = sum(1 for e, c in pairs if abs(c - e) <= D * abs(e) or abs(c - e) <= W_FRAC * UH)
    return hits / len(pairs) if pairs else float("nan"), len(pairs)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--data", required=True)
    ap.add_argument("--time", default="latest"); ap.add_argument("--out", default=None); a = ap.parse_args()
    d = os.path.join(a.case, "postProcessing", "samplePoints")
    t = sorted(os.listdir(d), key=float)[-1] if a.time == "latest" else a.time
    S = read_cloud(os.path.join(d, t, "measured_k_U.xy"))
    exp = list(csv.DictReader(open(a.data)))
    pairs = {c: [] for c in ("U", "V", "W", "k")}; missing = 0
    for r in exp:
        key = (round(float(r["x (m)"]), 5), round(float(r["y (m)"]), 5), round(float(r["z (m)"]), 5))
        if float(r["U (m/s)"]) <= -999: continue
        if key not in S: missing += 1; continue
        kc, Uc = S[key]
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
    print(json.dumps(res, indent=1))
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
