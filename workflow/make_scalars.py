#!/usr/bin/env python3
"""Add the tagged passive scalars to a converged applied-case flow (Project.md section 4).

    make_scalars.py <case_dir> --time <converged_time> [--sct 0.4] [--iters 1500]

Writes into <case_dir>/<time>/ one scalar field per source: sC01..sC10 (one per chiller discharge
strip), sF (the flue group), sAll (every source at once, the balance check), each 1 on its own
source patch and 0 on every other inflow, zeroGradient on walls and sinks; adds a scalarTransport
function object per scalar (D = nu + nut/Sct), area averages of every scalar on every sink patch
(chiller intakes, louvres) written every iteration as the source-to-receptor monitors, and the
outlet area average for the balance. Extends endTime by --iters with residualControl removed.
"""
import argparse, os, re
ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--time", required=True)
ap.add_argument("--sct", type=float, default=0.4); ap.add_argument("--iters", type=int, default=3000); a = ap.parse_args()
C = a.case; t = a.time
sources = {f"sC{i:02d}": f"chiller_out_{i:02d}" for i in range(1, 11)}; sources["sF"] = "flue_exit"
scalars = dict(sources); scalars["sAll"] = None
sinks = [f"chiller_in_{i:02d}" for i in range(1, 11)] + ["intake_louvre_pos", "intake_louvre_neg"]
src_patches = list(sources.values())
for name, own in scalars.items():
    lines = [f"/*  Tagged scalar {name}: 1 at {own or 'every source'}, 0 at every other inflow; solved on the frozen flow (Sct {a.sct}).  */",
             f"FoamFile {{ version 2.0; format ascii; class volScalarField; object {name}; }}",
             "dimensions      [0 0 0 0 0 0 0];", "internalField   uniform 0;", "boundaryField", "{",
             "    inlet           { type fixedValue; value uniform 0; }",
             "    outlet          { type inletOutlet; inletValue uniform 0; value uniform 0; }"]
    for p in src_patches:
        v = 1 if (own is None or p == own) else 0
        lines.append(f"    {p:16s} {{ type fixedValue; value uniform {v}; }}")
    lines.append('    ".*"            { type zeroGradient; }      // walls, sinks, top, sides')
    lines.append("}")
    open(os.path.join(C, t, name), "w").write("\n".join(lines) + "\n")
fo = [f"/*  Tagged scalars on the frozen flow: {len(scalars)} scalarTransport objects, Sct {a.sct}, and the receptor monitors.  */"]
for name in scalars:
    fo.append(f"{name}T {{ type scalarTransport; libs (solverFunctionObjects); field {name}; schemesField s; alphaD 1; alphaDt {1/a.sct:.6f}; bounded01 false; resetOnStartUp false; writeControl writeTime; }}")
for p in sinks + ["outlet"]:
    fo.append(f"recv_{p} {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name {p}; operation areaAverage; fields ({' '.join(scalars)}); writeControl timeStep; writeInterval 10; writeFields false; log false; }}   // uniform normal velocity on the sink, so the area average is the flow-weighted mean")
open(os.path.join(C, "system", "scalarTransport"), "w").write("\n".join(fo) + "\n")
c = open(os.path.join(C, "system", "controlDict")).read()
if '#include "scalarTransport"' not in c: c = c.replace("functions\n{", 'functions\n{\n    #include "scalarTransport"')
c = re.sub(r"endTime\s+\d+;", f"endTime         {int(t) + a.iters};", c)
open(os.path.join(C, "system", "controlDict"), "w").write(c)
f = open(os.path.join(C, "system", "fvSolution")).read()
if '"(s|s' not in f and '"s.*"' not in f:
    f = f.replace('    "(U|k|epsilon|omega)"', '    "s.*"\n    {\n        solver          PBiCGStab;\n        preconditioner  DILU;\n        tolerance       1e-10;\n        relTol          0.01;\n    }\n\n    "(U|k|epsilon|omega)"')
    f = f.replace('        "(k|epsilon|omega)" 0.7;', '        "(k|epsilon|omega)" 0.7;\n        s               0.7;')
f = re.sub(r"    residualControl.*?\n    \{\n.*?\n    \}\n", "", f, flags=re.S)
open(os.path.join(C, "system", "fvSolution"), "w").write(f)
s = open(os.path.join(C, "system", "fvSchemes")).read()
if "div(phi,s)" not in s: s = s.replace("    div(phi,omega)  bounded Gauss limitedLinear 1;", "    div(phi,omega)  bounded Gauss limitedLinear 1;\n    div(phi,s)      bounded Gauss limitedLinear 1;")
open(os.path.join(C, "system", "fvSchemes"), "w").write(s)
print(f"{len(scalars)} scalars written into {C}/{t}; monitors on {len(sinks)} sinks + outlet; endTime {int(t)+a.iters}")
