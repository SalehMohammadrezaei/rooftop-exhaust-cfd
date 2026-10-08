#!/usr/bin/env python3
"""Generate every OpenFOAM case of a family from one parameter file.

    make_case.py params/V0_empty_domain.json --out ~/scratch/openfoam_cases [--only NAME]

Each variant combination becomes <out>/<family>/<closure>_<wallset>_<top>_<mesh>/ with
0.orig/, constant/, system/ filled from templates/<family>/ and a case_record.json that
holds every derived number (u*, tau, grading ratio, cell count) with its formula.
Templates use @name placeholders; OpenFOAM's own $macros are left untouched.
"""
import argparse, itertools, json, math, os, shutil, subprocess
from string import Template

class T(Template):
    delimiter = "@"
    idpattern = r"[A-Za-z][A-Za-z0-9_]*"

def git_commit(repo):
    try:
        return subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"

def grading_ratio(L, n, h0):
    """simpleGrading ratio r = last/first such that n geometric cells of first height h0 sum to L.
    f(q) = h0*(q^n-1)/(q-1) - L is monotone increasing in q, so bisect for its root."""
    def f(q):
        if abs(q - 1.0) < 1e-12:
            return h0 * n - L
        return h0 * (q ** n - 1) / (q - 1) - L
    lo, hi = 0.5, 10.0
    if f(lo) > 0 or f(hi) < 0:
        raise ValueError(f"no geometric grading for L={L}, n={n}, h0={h0}")
    for _ in range(200):
        q = 0.5 * (lo + hi)
        if f(q) < 0:
            lo = q
        else:
            hi = q
    return q ** (n - 1)

def render(src, dst, mapping):
    with open(src) as f:
        txt = T(f.read()).substitute(mapping)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(txt)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("params")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="generate only this case name")
    a = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = json.load(open(a.params))
    fam = P["family"]
    tdir = os.path.join(repo, "templates", fam)
    I = {k: v["value"] for k, v in P["inputs"].items()}
    D, N, M = P["domain"], P["numerics"], P["monitor"]
    H = I["H_m"]

    ustar = I["kappa"] * I["Uref_mps"] / math.log((I["Zref_m"] + I["z0_m"]) / I["z0_m"])
    tau = ustar ** 2
    kInit = ustar ** 2 / math.sqrt(I["Cmu"])
    zmid = 0.5 * D["z_top_H"] * H
    epsInit = ustar ** 3 / (I["kappa"] * (zmid + I["z0_m"]))
    omegaInit = ustar / (I["kappa"] * math.sqrt(I["Cmu"]) * (zmid + I["z0_m"]))
    xMin, xMax, zMax = -D["x_upstream_H"] * H, D["x_downstream_H"] * H, D["z_top_H"] * H
    nx = int(round((xMax - xMin) / N["dx_m"]))

    V = P["variants"]
    combos = itertools.product(V["closure"], V["wallset"], V["top"], V["mesh"])
    made = []
    for cl, ws, tp, me in combos:
        name = f"{cl}_{ws}_{tp}_{me}"
        if a.only and name != a.only:
            continue
        C, W, Me = V["closure"][cl], V["wallset"][ws], V["mesh"][me]
        diss = C["dissipation"]
        nz, h0 = Me["nz"], Me["first_cell_m"]
        zg = grading_ratio(zMax, nz, h0)
        stations = ""
        for xH, nm in zip(M["stations_x_H"], M["station_names"]):
            x = xH * H
            stype = "midPoint" if nm == "inletCell" else "face"
            stations += f"        {nm} {{ type {stype}; axis z; start ({x:.6g} {D['y_width_m']/2:g} 0); end ({x:.6g} {D['y_width_m']/2:g} {zMax:g}); }}\n"
        topU = ("        type fixedShearStress;\n        tau (%.9g 0 0);\n        value uniform (0 0 0);" % tau
                if tp == "fixedShear" else "        type slip;")
        coeffs = f"    {C['model']}Coeffs {{ {C['coeffs']}; }}" if C["coeffs"] else ""
        mp = dict(
            paramsFile=os.path.relpath(a.params, repo),
            kappa=I["kappa"], Cmu=I["Cmu"], Uref=I["Uref_mps"], Zref=I["Zref_m"], z0=I["z0_m"], d=I["d_m"],
            nu=I["nu_m2ps"], kInit=f"{kInit:.6g}", epsInit=f"{epsInit:.6g}", omegaInit=f"{omegaInit:.6g}",
            topU=topU, epsilonWF=W["epsilonWF"], omegaWF=W["omegaWF"],
            xMin=xMin, xMax=xMax, yMax=D["y_width_m"], zMax=zMax, nx=nx, ny=D["ny"], nz=nz, zGrading=f"{zg:.9g}",
            endTime=N["endTime"], writeInterval=N["writeInterval"], residualControl=N["residualControl"],
            probeX=M["probe_xyz"][0], probeY=M["probe_xyz"][1], probeZ=M["probe_xyz"][2],
            stationSets=stations.rstrip("\n"), dissipation=diss, model=C["model"], coeffsBlock=coeffs,
        )
        case = os.path.join(os.path.expanduser(a.out), fam, name)
        if os.path.exists(case):
            shutil.rmtree(case)
        for f in ["U", "p", "k", "nut", diss, "include/ABLConditions"]:
            render(os.path.join(tdir, f), os.path.join(case, "0.orig", f), mp)
        for f in ["turbulenceProperties", "transportProperties"]:
            render(os.path.join(tdir, f), os.path.join(case, "constant", f), mp)
        for f in ["blockMeshDict", "controlDict", "fvSchemes", "fvSolution", "sampleLines"]:
            render(os.path.join(tdir, f), os.path.join(case, "system", f), mp)
        rec = dict(
            case=name, family=fam, params=os.path.relpath(a.params, repo), repo_commit=git_commit(repo),
            variant=dict(closure=cl, wallset=ws, top=tp, mesh=me),
            derived={
                "ustar_mps": {"value": ustar, "formula": "kappa*Uref/ln((Zref+z0)/z0)"},
                "tau_top_m2ps2": {"value": tau, "formula": "ustar^2 (used only for top=fixedShear)"},
                "k_init_m2ps2": {"value": kInit, "formula": "ustar^2/sqrt(Cmu)"},
                "eps_init": {"value": epsInit, "formula": "ustar^3/(kappa*(z_mid+z0)), z_mid = half domain height"},
                "omega_init": {"value": omegaInit, "formula": "ustar/(kappa*sqrt(Cmu)*(z_mid+z0))"},
                "z_grading_ratio": {"value": zg, "formula": "last/first cell height for nz geometric cells of first height h0 summing to zMax"},
                "first_cell_centre_m": {"value": 0.5 * h0, "formula": "h0/2"},
                "y_over_z0": {"value": 0.5 * h0 / I["z0_m"], "formula": "first_cell_centre/z0"},
                "cells": {"value": nx * D["ny"] * nz, "formula": "nx*ny*nz"},
            },
            acceptance=P["acceptance"], inputs=P["inputs"],
        )
        with open(os.path.join(case, "case_record.json"), "w") as f:
            json.dump(rec, f, indent=1)
        made.append(name)
    print(f"{len(made)} cases written under {os.path.join(os.path.expanduser(a.out), fam)}")
    for m in made:
        print("  " + m)

if __name__ == "__main__":
    main()
