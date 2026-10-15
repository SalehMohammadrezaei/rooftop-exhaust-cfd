#!/usr/bin/env python3
"""Generate one applied run from the hand-built case and params/applied_design.json.

    make_applied_case.py --dir 30 --speed 10 --variant D0 --out ~/scratch/openfoam_cases/applied [--cores 32]

Case name: <variant>_dir<deg>_U<speed>. Steps: copy system/ and 0.orig/ from applied/case_by_hand;
regenerate the STL set rotated by <deg> with the variant's flue tip (geometry/make_hall.py); rotate
the building-fixed refinement boxes into searchableRotatedBox entries (the wake box stays
wind-aligned); set Uref in include/ABLConditions, tau on the top, the initial guess, and the probe
positions rotated with the building; write case_record.json. Meshing and running are done by
workflow/run_applied.sh.
"""
import argparse, json, math, os, re, shutil, subprocess
ap = argparse.ArgumentParser(); ap.add_argument("--dir", type=float, required=True); ap.add_argument("--speed", type=float, required=True)
ap.add_argument("--variant", default="D0"); ap.add_argument("--out", required=True); ap.add_argument("--cores", type=int, default=None)
ap.add_argument("--mesh-scale", type=float, default=1.0, help="multiply the background cell by this (0.709 = finer by 1.41, 1.41 = coarser); refinement levels and boxes unchanged (decision 0015)")
ap.add_argument("--name-suffix", default=""); a = ap.parse_args()
repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = json.load(open(os.path.join(repo, "params", "applied_design.json")))
src = os.path.join(repo, "applied", "case_by_hand"); name = f"{a.variant}_dir{int(round(a.dir)):03d}_U{a.speed:g}{a.name_suffix}"
C = os.path.join(os.path.expanduser(a.out), name); shutil.rmtree(C, ignore_errors=True); os.makedirs(os.path.join(C, "constant"))
shutil.copytree(os.path.join(src, "system"), os.path.join(C, "system")); shutil.copytree(os.path.join(src, "0.orig"), os.path.join(C, "0.orig"))
if a.mesh_scale != 1.0:   # decision 0015: scale the background cell, keep every level and box
    bp = os.path.join(C, "system", "blockMeshDict"); b = open(bp).read()
    b = re.sub(r"dx\s+([\d.]+);", lambda mm: f"dx      {float(mm.group(1)) * a.mesh_scale:.4g};", b, count=1)
    open(bp, "w").write(b)
for f in ("transportProperties", "turbulenceProperties"): shutil.copy(os.path.join(src, "constant", f), os.path.join(C, "constant", f))
tip = P["variants"][a.variant]["flue_tip_m"]
subprocess.run(["python3", os.path.join(repo, "geometry", "make_hall.py"), os.path.join(repo, "params", "hall_geometry.json"), os.path.join(C, "constant", "triSurface"), "--flue-tip", str(tip), "--rotate", str(a.dir)], check=True, capture_output=True)
# refinement boxes: rotate the building-fixed ones
s = open(os.path.join(C, "system", "snappyHexMeshDict")).read()
th = math.radians(a.dir); c, sn = math.cos(th), math.sin(th)
def rot(x, y): return (c * x - sn * y, sn * x + c * y)
def rotated_box(m):
    nm, x0, y0, z0, x1, y1, z1 = m.group(1), *map(float, m.group(2).split()), *map(float, m.group(3).split())
    if nm in ("groundLayer", "wakeBox"): return m.group(0)         # wind-aligned, unchanged
    if nm == "flueJets" or nm == "fluePipes":                      # follow the flue tip height
        z1 = z1 + (tip - 3.0)
    ox, oy = rot(x0, y0)
    return f"    {nm:16s} {{ type searchableRotatedBox; span ({x1-x0:g} {y1-y0:g} {z1-z0:g}); origin ({ox:.4g} {oy:.4g} {z0:g}); e1 ({c:.6f} {sn:.6f} 0); e3 (0 0 1); }}"
s = re.sub(r"    (\w+)\s+\{ type searchableBox; min \(([-\d. ]+)\);\s+max \(([-\d. ]+)\);\s*\}", rotated_box, s)
s = s.replace("locationInMesh (-100 100 60);", "locationInMesh (-140 150 100);")
open(os.path.join(C, "system", "snappyHexMeshDict"), "w").write(s)
# wind speed
W = P["wind"]; ustar = W["kappa"] * a.speed / math.log((W["Zref_m"] + W["z0_m"]) / W["z0_m"]); tau = ustar ** 2; kabl = ustar ** 2 / math.sqrt(W["Cmu"])
open(os.path.join(C, "0.orig", "include", "ABLConditions"), "w").write(f"// Applied ABL, decision 0002: U_H {a.speed} m/s at {W['Zref_m']} m, z0 {W['z0_m']} m; u* {ustar:.4f}\nkappa {W['kappa']}; Cmu {W['Cmu']}; flowDir (1 0 0); zDir (0 0 1); Uref {a.speed}; Zref {W['Zref_m']}; z0 uniform {W['z0_m']}; d uniform 0.0;\n")
u = open(os.path.join(C, "0.orig", "U")).read(); u = re.sub(r"tau \([-\d.e+]+ 0 0\)", f"tau ({tau:.6g} 0 0)", u); open(os.path.join(C, "0.orig", "U"), "w").write(u)
k = open(os.path.join(C, "0.orig", "k")).read(); k = re.sub(r"internalField   uniform [\d.e+-]+;", f"internalField   uniform {kabl:.3g};", k, count=1); open(os.path.join(C, "0.orig", "k"), "w").write(k)
e = open(os.path.join(C, "system", "setExprFieldsDict")).read(); e = re.sub(r'"ustar = [\d.]+"', f'"ustar = {ustar:.4f}"', e); open(os.path.join(C, "system", "setExprFieldsDict"), "w").write(e)
cd = open(os.path.join(C, "system", "controlDict")).read()
def rot_probes(m):
    pts = re.findall(r"\(([-\d. ]+)\)", m.group(1)); out = []
    for p in pts:
        x, y, z = map(float, p.split()); X, Y = rot(x, y); out.append(f"({X:.2f} {Y:.2f} {z:g})")
    return "probeLocations ( " + " ".join(out) + " );"
cd = re.sub(r"probeLocations \((.*?)\);", rot_probes, cd, flags=re.S); cd = re.sub(r"endTime\s+\d+;", f"endTime         {P['numerics']['flow_iters']};", cd)
cd = cd.replace('    #include "scalarTransport"\n', "")   # the flow stage carries no tracers; make_scalars.py adds them
open(os.path.join(C, "system", "controlDict"), "w").write(cd)
cores = a.cores or P["numerics"]["cores"]; open(os.path.join(C, "system", "decomposeParDict"), "w").write(f"FoamFile {{ version 2.0; format ascii; class dictionary; object decomposeParDict; }}\nnumberOfSubdomains {cores};\nmethod scotch;\n")
rec = {"case": name, "variant": a.variant, "direction_deg": a.dir, "U_H": a.speed, "flue_tip_m": tip, "ustar": ustar, "tau_top": tau, "k_abl": kabl, "cores": cores,
       "repo_commit": subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip(), "params": "params/applied_design.json", "flows": P["flows"]}
json.dump(rec, open(os.path.join(C, "case_record.json"), "w"), indent=1); print(name, "written:", C)
