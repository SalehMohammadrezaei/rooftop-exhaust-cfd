#!/bin/bash
# Run one generated applied case end to end: mesh (parallel), flow, tagged scalars, matrix, record.
#   run_applied.sh <case_dir>
set -eo pipefail
source ~/opt/openfoam2606.sh >/dev/null 2>&1
REPO=$(cd "$(dirname "$0")/.." && pwd); C="$(cd "$1" && pwd)"; cd "$C"; N=$(grep numberOfSubdomains system/decomposeParDict | tr -dc 0-9)
t0=$(date +%s)
blockMesh > log.blockMesh 2>&1; surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
decomposePar > log.decomposePar 2>&1; mpirun -np $N snappyHexMesh -parallel -overwrite > log.snappyHexMesh 2>&1
reconstructParMesh -constant > log.reconstructParMesh 2>&1; checkMesh > log.checkMesh 2>&1
rm -rf 0 processor*; cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar2 2>&1
mpirun -np $N simpleFoam -parallel > log.simpleFoam 2>&1
T=$(ls -d processor0/[0-9]* | sed 's|.*/||' | sort -n | tail -1); reconstructPar -latestTime > log.reconstructPar 2>&1
python3 $REPO/workflow/make_scalars.py . --time $T > log.makeScalars 2>&1
rm -rf processor*; decomposePar -latestTime > log.decomposePar3 2>&1
mpirun -np $N simpleFoam -parallel > log.simpleFoam_scalars 2>&1
reconstructPar -latestTime > log.reconstructPar2 2>&1
python3 $REPO/postproc/matrix.py . --out $REPO/results/applied/$(basename "$C").json > log.matrix 2>&1
t1=$(date +%s)
python3 - "$C" "$t0" "$t1" <<'PY'
import json, re, sys, os
C, t0, t1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); r = json.load(open(f"{C}/case_record.json"))
r.update({"wall_time_s": t1 - t0, "cells": int(re.search(r"cells:\s+(\d+)", open(f"{C}/log.checkMesh").read()).group(1)),
          "mesh_ok": "Mesh OK" in open(f"{C}/log.checkMesh").read(), "flow_iterations": open(f"{C}/log.simpleFoam").read().count("\nTime = "),
          "scalar_iterations": open(f"{C}/log.simpleFoam_scalars").read().count("\nTime = "), "host": os.uname().nodename})
json.dump(r, open(f"{C}/run_record.json", "w"), indent=1); print("done", r["case"], r["cells"], "cells", r["wall_time_s"], "s")
PY
