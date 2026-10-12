#!/usr/bin/env python3
"""V2 inlet tables from the digitised R-848 approach flow (Figure 3.1).

    make_inlet_profiles.py data/digitised/irsst_r848 <case_dir>

U(z)   = (V/Vg)_digitised * Vg, Vg = 14.2 m/s, z in metres (chart gives cm)
k(z)   = 1.5 (I_u U)^2 with I_u from the digitised turbulence-intensity profile (isotropy assumed:
         the report gives only the streamwise intensity; flagged in decision 0007)
eps(z) = sqrt(Cmu) k dU/dz with dU/dz from the power law U = Vg (z/zg)^alpha, alpha 0.31, zg 0.95 m,
         which the digitised profile follows within 3 % above 10 cm (smooth slope, as in V1)
omega  = eps / (Cmu k)
The two digitised profiles have different z points; both are interpolated onto one z list.
Rows are added at z = 0 (U = 0) and at z = 0.95 m (gradient height, values held above it).
"""
import csv, math, os, sys
src, case = sys.argv[1], sys.argv[2]
Cmu, Vg, zg, alpha = 0.09, 14.2, 0.95, 0.31
def rd(name):
    rows = [l for l in open(os.path.join(src, name)) if not l.startswith("#") and not l.startswith("z")]
    return sorted((float(l.split(",")[0]) / 100.0, float(l.split(",")[1])) for l in rows)
u = rd("fig3_1a_measured_UoverUg.csv"); ti = rd("fig3_1b_measured_TI.csv")
def interp(tab, z):
    if z <= tab[0][0]: return tab[0][1]
    if z >= tab[-1][0]: return tab[-1][1]
    for (z0, v0), (z1, v1) in zip(tab, tab[1:]):
        if z0 <= z <= z1: return v0 + (v1 - v0) * (z - z0) / (z1 - z0)
zs = sorted(set([z for z, _ in u] + [z for z, _ in ti]))
out = os.path.join(case, "constant", "inletProfiles"); os.makedirs(out, exist_ok=True)
U, K, E, W = [(0, 0, 0, 0)], [(0, None)], [(0, None)], [(0, None)]
rows = []
for z in zs:
    Uz = interp(u, z) * Vg; I = interp(ti, z) / 100.0
    k = 1.5 * (I * Uz) ** 2
    dUdz = Vg * alpha / zg * (max(z, 0.005) / zg) ** (alpha - 1)
    eps = max(math.sqrt(Cmu) * k * dUdz, 1e-4); om = eps / (Cmu * k)
    rows.append((z, Uz, k, eps, om, I))
first = rows[0]; last = rows[-1]
def write(name, header, data):
    with open(os.path.join(out, name + ".csv"), "w") as f:
        f.write(header + "\n")
        for line in data: f.write(",".join(f"{v:.6g}" for v in line) + "\n")
write("U", "z,Ux,Uy,Uz", [(0, 0, 0, 0)] + [(z, Uz, 0, 0) for z, Uz, *_ in rows] + [(1.2, last[1], 0, 0)])
write("k", "z,k", [(0, first[2])] + [(z, k) for z, _, k, *_ in rows] + [(1.2, last[2])])
write("epsilon", "z,epsilon", [(0, first[3])] + [(z, e) for z, _, _, e, *_ in rows] + [(1.2, last[3])])
write("omega", "z,omega", [(0, first[4])] + [(z, w) for z, _, _, _, w, _ in rows] + [(1.2, last[4])])
print(f"{'z m':>6s} {'U':>6s} {'I %':>5s} {'k':>6s} {'eps':>7s} {'omega':>7s}")
for z, Uz, k, e, w, I in rows: print(f"{z:6.3f} {Uz:6.2f} {100*I:5.1f} {k:6.3f} {e:7.2f} {w:7.1f}")
zH = 0.075; print(f"\nat building height {zH} m: U = {interp(u, zH)*Vg:.2f} m/s (report table: 6.2), I = {interp(ti, zH):.1f} %, k = {1.5*(interp(ti, zH)/100*interp(u, zH)*Vg)**2:.3f}")
print("wrote", out)
