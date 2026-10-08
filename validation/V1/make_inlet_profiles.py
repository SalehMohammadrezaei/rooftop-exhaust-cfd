#!/usr/bin/env python3
"""Convert the Case H approach-flow measurements into inlet profile tables for OpenFOAM.

    make_inlet_profiles.py data/raw/aij_caseH/AF_caseH.csv <case_dir>

Writes <case_dir>/constant/inletProfiles/{U,k,epsilon,omega}.csv, one row per height:
  U       measured (V, W set to 0: the tunnel values are small and of measurement-noise size)
  k       measured
  epsilon sqrt(Cmu) * k * dU/dz      (local equilibrium, decision 0003). dU/dz is taken from the
          log-law fit of the measured U (u* = 0.448 m/s, z0 = 11.7 mm, entry 13), dU/dz = u*/(kappa (z+z0)),
          because finite differences of the measured points are dominated by measurement noise
          (approved by Saleh 2026-10-08). Measured U and k are used unchanged.
  omega   epsilon / (Cmu * k)
Rows are added at z = 0 (U = 0) and at z = zTop (values held constant) so the table covers the
whole inlet patch; the fixedProfile condition clamps outside the table anyway.
"""
import csv, math, os, sys
src, case = sys.argv[1], sys.argv[2]
Cmu, zTop, epsMin = 0.09, 1.2, 1e-4
rows = [r for r in csv.reader(open(src))][1:]
z = [float(r[2]) for r in rows]; U = [float(r[3]) for r in rows]; k = [float(r[11]) for r in rows]
# dU/dz from the log-law fit of the measured profile (smooth), not from point differences (noisy)
ustar, z0, kappa = 0.448, 0.0117, 0.4
dUdz = [ustar/(kappa*(zi+z0)) for zi in z]
eps = [max(math.sqrt(Cmu)*kk*g, epsMin) for kk, g in zip(k, dUdz)]
om  = [e/(Cmu*kk) for e, kk in zip(eps, k)]
out = os.path.join(case, "constant", "inletProfiles"); os.makedirs(out, exist_ok=True)
def write(name, header, data):
    with open(os.path.join(out, name + ".csv"), "w") as f:
        f.write(header + "\n")
        for line in data: f.write(",".join(f"{v:.6g}" for v in line) + "\n")
write("U",       "z,Ux,Uy,Uz", [(0,0,0,0)] + [(zi,Ui,0,0) for zi,Ui in zip(z,U)] + [(zTop,U[-1],0,0)])
write("k",       "z,k",        [(0,k[0])]  + list(zip(z,k))   + [(zTop,k[-1])])
write("epsilon", "z,epsilon",  [(0,eps[0])]+ list(zip(z,eps)) + [(zTop,eps[-1])])
write("omega",   "z,omega",    [(0,om[0])] + list(zip(z,om))  + [(zTop,om[-1])])
print(f"{'z':>6s} {'U':>6s} {'k':>6s} {'dU/dz':>7s} {'epsilon':>8s} {'omega':>7s}")
for zi,Ui,kk,g,e,o in zip(z,U,k,dUdz,eps,om): print(f"{zi:6.3f} {Ui:6.2f} {kk:6.3f} {g:7.2f} {e:8.4f} {o:7.2f}")
print("wrote", out)
