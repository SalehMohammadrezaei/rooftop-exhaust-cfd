#!/usr/bin/env python3
"""Write the Case H measurement points as an OpenFOAM 'cloud' sampling set.

    make_sample_points.py data/raw/aij_caseH/RS_caseH.csv <case_dir>

Writes <case_dir>/system/samplePoints: a function-object dictionary that samples U, k (and c later)
at every measured point with a valid velocity, for `postProcess -func samplePoints -latestTime`.
Output: postProcessing/samplePoints/<time>/measured_k_U.xy (raw: x y z k Ux Uy Uz; fields sorted by name).
"""
import csv, os, sys
src, case = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src)))
pts = [(float(r["x (m)"]), float(r["y (m)"]), float(r["z (m)"])) for r in rows if float(r["U (m/s)"]) > -999]
with open(os.path.join(case, "system", "samplePoints"), "w") as f:
    f.write("/*  Step 8: sample the CFD at the wind-tunnel measurement points (generated, do not edit).  */\n")
    f.write("samplePoints\n{\n    type sets;\n    libs (sampling);\n    setFormat raw;\n")
    f.write("    interpolationScheme cellPoint;   // interpolate from cell centres to the exact point\n")
    f.write("    writeControl writeTime;\n    fields (U k);\n    sets\n    {\n        measured\n        {\n            type cloud;\n            axis xyz;\n            points\n            (\n")
    for x, y, z in pts:
        f.write(f"                ({x:g} {y:g} {z:g})\n")
    f.write("            );\n        }\n    }\n}\n")
print(f"{len(pts)} points written to {case}/system/samplePoints")
