#!/usr/bin/env python3
"""ABL homogeneity check from raw OpenFOAM sample-line files (no numpy).

Usage: abl_profiles.py <case_dir> <endTime> [--zref 6] [--zmax 100] [--dataset DIR]

Reads results/<setup>/postProcessing/samples_<field>/<endTime>/<set>_<field>.xy
(raw format: z, value[, value, value]) and reports, per field and station, the
maximum relative change w.r.t. the inlet-patch profile over 0<z<3*zref and
0<z<zmax, plus the mean absolute relative deviation from a digitised benchmark
where one exists. All numbers derive from the files; nothing is read from plots.
"""
import sys, os, math, glob, argparse, json

STATIONS = ["x_0mPatch", "x_0mCell", "x_2500m", "x_4000m", "x_5000mCell", "x_5000mPatch"]
XPOS = {"x_0mPatch": 0.0, "x_0mCell": 5.0, "x_2500m": 2500.0, "x_4000m": 4000.0,
        "x_5000mCell": 4995.0, "x_5000mPatch": 5000.0}

def read_xy(path):
    z, v = [], []
    with open(path) as f:
        for line in f:
            s = line.split()
            if not s or s[0].startswith("#"):
                continue
            vals = [float(x) for x in s]
            z.append(vals[0])
            v.append(vals[1] if len(vals) == 2 else vals[1:])   # scalar or vector
    return z, v

def read_dataset(path):
    """Digitised benchmark: 'value, z/zref' per line, '#' comments."""
    pts = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            a, b = line.replace(",", " ").split()[:2]
            pts.append((float(b), float(a)))   # (z/zref, value)
    return sorted(pts)

def interp(z, v, zq):
    """Linear interpolation of (z,v) at zq; clamps at ends."""
    if zq <= z[0]:
        return v[0]
    if zq >= z[-1]:
        return v[-1]
    lo, hi = 0, len(z) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if z[m] <= zq:
            lo = m
        else:
            hi = m
    t = (zq - z[lo]) / (z[hi] - z[lo])
    return v[lo] + t * (v[hi] - v[lo])

def rel_change(zref_prof, vref, z, v, zlo, zhi):
    """max |v(z)-vref(z)| / |vref(z)| over zlo<z<zhi, evaluated at z of the station."""
    worst, zworst = 0.0, None
    for zi, vi in zip(z, v):
        if zi <= zlo or zi >= zhi:
            continue
        r = interp(zref_prof, vref, zi)
        if abs(r) < 1e-12:
            continue
        e = abs(vi - r) / abs(r)
        if e > worst:
            worst, zworst = e, zi
    return worst, zworst

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("endTime")
    ap.add_argument("--zref", type=float, default=6.0)
    ap.add_argument("--zmax", type=float, default=100.0)
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    out = {"case": a.case, "endTime": a.endTime, "fields": {}}
    for field in ["U", "k", "epsilon", "omega", "nut"]:
        d = os.path.join(a.case, "postProcessing", "samples_" + ("u" if field == "U" else field), a.endTime)
        if not os.path.isdir(d):
            continue
        prof = {}
        for st in STATIONS:
            p = os.path.join(d, f"{st}_{field}.xy")
            if not os.path.exists(p):
                continue
            z, v = read_xy(p)
            if field == "U":
                v = [c[0] for c in v]     # streamwise component
            prof[st] = (z, v)
        if "x_0mPatch" not in prof:
            continue
        zr, vr = prof["x_0mPatch"]
        res = {}
        for st, (z, v) in prof.items():
            e3, z3 = rel_change(zr, vr, z, v, 0.0, 3.0 * a.zref)
            eA, zA = rel_change(zr, vr, z, v, 0.0, a.zmax)
            res[st] = {"x_m": XPOS[st],
                       "max_rel_change_below_3zref_pct": 100 * e3, "at_z_m": z3,
                       f"max_rel_change_below_{int(a.zmax)}m_pct": 100 * eA, "at_z_m_full": zA,
                       "value_at_zref": interp(z, v, a.zref),
                       "value_first_point": v[0], "z_first_point": z[0]}
        out["fields"][field] = res

        # benchmark comparison (k-epsilon only; HW figure 6)
        if a.dataset:
            bench = {"U": {"x_2500m": "Ux-HW-RH-Fig6a", "x_4000m": "Ux-HW-RH-Fig6a"},
                     "k": {"x_2500m": "k-HW-Fig6b-2500", "x_4000m": "k-HW-Fig6b-4000"},
                     "epsilon": {"x_2500m": "epsilon-HW-RH-Fig6c", "x_4000m": "epsilon-HW-RH-Fig6c"}}
            if field in bench:
                for st, fname in bench[field].items():
                    fp = os.path.join(a.dataset, fname)
                    if st not in prof or not os.path.exists(fp):
                        continue
                    pts = read_dataset(fp)
                    z, v = prof[st]
                    errs = []
                    for zn, val in pts:
                        zz = zn * a.zref
                        if zz <= 0 or zz > a.zmax or abs(val) < 1e-12:
                            continue
                        errs.append(abs(interp(z, v, zz) - val) / abs(val))
                    if errs:
                        res[st]["benchmark_file"] = fname
                        res[st]["benchmark_mean_abs_rel_dev_pct"] = 100 * sum(errs) / len(errs)
                        res[st]["benchmark_max_abs_rel_dev_pct"] = 100 * max(errs)
                        res[st]["benchmark_points_used"] = len(errs)

    # print a compact table
    print(f"# {a.case} @ t={a.endTime}; zref={a.zref} m; windows 0<z<{3*a.zref:g} m and 0<z<{a.zmax:g} m")
    for field, res in out["fields"].items():
        print(f"\n## {field}")
        print(f"{'station':14s} {'x[m]':>7s} {'max dU/U <3zref %':>18s} {'z':>7s} {'max dU/U <zmax %':>17s} {'z':>7s} {'val@zref':>10s} {'bench mean %':>13s} {'bench max %':>12s}")
        for st, r in res.items():
            bm = r.get("benchmark_mean_abs_rel_dev_pct")
            bx = r.get("benchmark_max_abs_rel_dev_pct")
            print(f"{st:14s} {r['x_m']:7.0f} {r['max_rel_change_below_3zref_pct']:18.3f} {str(r['at_z_m'])[:7]:>7s} "
                  f"{r[f'max_rel_change_below_{int(a.zmax)}m_pct']:17.3f} {str(r['at_z_m_full'])[:7]:>7s} {r['value_at_zref']:10.4g} "
                  f"{'' if bm is None else f'{bm:.2f}':>13s} {'' if bx is None else f'{bx:.2f}':>12s}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1)

if __name__ == "__main__":
    main()
