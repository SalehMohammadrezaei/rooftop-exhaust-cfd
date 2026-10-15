#!/bin/bash
# Run one generated case serially: mesh, check, solve, y+, log extraction, run record.
#   run_case.sh <case_dir>
# Serial on purpose: V0 cases are a few thousand cells. Parallel runs need an agreed core count (working rule 12).
# OpenFOAM's bashrc is not clean under "set -u", so source it first.
source "$HOME/opt/openfoam2606.sh" >/dev/null 2>&1
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
set -eo pipefail   # no -u: OpenFOAM RunFunctions use unset variables
case_dir="$(cd "$1" && pwd)"
cd "$case_dir"

start=$(date +%s)
rm -rf 0 && cp -r 0.orig 0
runApplication blockMesh
runApplication checkMesh -allGeometry -allTopology
runApplication simpleFoam
runApplication -s yPlus simpleFoam -postProcess -func yPlus -latestTime
foamLog log.simpleFoam >/dev/null 2>&1 || true
end=$(date +%s)

lastTime=$(ls -d [0-9]* | sort -n | tail -1)
cells=$(grep -m1 "cells:" log.checkMesh | awk '{print $2}')
meshOK=$(grep -c "Mesh OK" log.checkMesh || true)
yplus=$(grep "patch ground y+" log.simpleFoam.yPlus | tail -1 | sed 's/.*y+ : //')
cat > run_record.json <<JSON
{
 "case": "$(basename "$case_dir")",
 "openfoam": "$WM_PROJECT_VERSION",
 "host": "$(hostname)",
 "cores": 1,
 "started_utc": "$(date -u -d @$start +%Y-%m-%dT%H:%M:%SZ)",
 "wall_time_s": $((end - start)),
 "cells": ${cells:-null},
 "checkMesh_ok": $([ "${meshOK:-0}" -gt 0 ] && echo true || echo false),
 "final_iteration": $lastTime,
 "converged_by_residualControl": $(grep -q "solution converged in" log.simpleFoam && echo true || echo false),
 "yplus_ground": "$yplus",
 "load_avg_at_start": "$(cut -d' ' -f1-3 /proc/loadavg)"
}
JSON
echo "done: $(basename "$case_dir") iter=$lastTime wall=$((end - start))s cells=$cells"
