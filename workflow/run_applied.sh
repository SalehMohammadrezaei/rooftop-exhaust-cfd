#!/bin/bash
# Run one generated applied case end to end: mesh (parallel), flow, tagged scalars, matrix, record.
#   run_applied.sh <case_dir>
# Each stage is skipped when its log already shows it finished, so the same script resumes a case
# that stopped part-way (e.g. the driver was signalled while the solver was running).
source ~/opt/openfoam2606.sh >/dev/null 2>&1   # before set -e: OpenFOAM's bashrc is not clean under it
set -eo pipefail
trap '' HUP                                      # a closed terminal must not stop a queued run
trap 'echo "run_applied.sh: stage at line $LINENO failed (status $?)" >&2' ERR
REPO=$(cd "$(dirname "$0")/.." && pwd); C="$(cd "$1" && pwd)"; cd "$C"; N=$(grep numberOfSubdomains system/decomposeParDict | tr -dc 0-9)
t0=$(date +%s)
done_log() { [ -f "$1" ] && grep -q "$2" "$1"; }    # done_log <log> <pattern>: stage already finished?

# 1. mesh
if ! done_log log.snappyHexMesh '^End'; then
  blockMesh > log.blockMesh 2>&1; surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
  decomposePar > log.decomposePar 2>&1; mpirun -np $N snappyHexMesh -parallel -overwrite > log.snappyHexMesh 2>&1
  reconstructParMesh -constant > log.reconstructParMesh 2>&1; checkMesh > log.checkMesh 2>&1
fi
# gate: a failed mesh check stops the case unless ALLOW_FAILED_MESH=1 is set explicitly (the result is
# then preliminary; run_record.json carries mesh_ok=false and the summary flags it)
if ! grep -q 'Mesh OK' log.checkMesh; then
  [ "${ALLOW_FAILED_MESH:-0}" = 1 ] || { echo 'MESH CHECK FAILED, stopping before the solver'; exit 2; }
  echo 'MESH CHECK FAILED, continuing because ALLOW_FAILED_MESH=1 (preliminary result)'
fi
# 2. flow (the solver's own "End" line is the completion check, not mpirun's exit status)
if ! done_log log.simpleFoam '^End'; then
  rm -rf 0 processor*; cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar2 2>&1
  mpirun -np $N simpleFoam -parallel > log.simpleFoam 2>&1 || true
  grep -q '^End' log.simpleFoam || { echo 'FLOW SOLVER DID NOT FINISH'; exit 3; }
fi
# 3. tagged scalars on the frozen flow
if ! done_log log.simpleFoam_scalars '^End'; then
  if ! done_log log.makeScalars 'scalars written'; then
    T=$(ls -d processor0/[0-9]* | sed 's|.*/||' | sort -n | tail -1); reconstructPar -latestTime > log.reconstructPar 2>&1
    python3 $REPO/workflow/make_scalars.py . --time $T > log.makeScalars 2>&1
  fi
  rm -rf processor*; decomposePar -latestTime > log.decomposePar3 2>&1
  mpirun -np $N simpleFoam -parallel > log.simpleFoam_scalars 2>&1 || true
  grep -q '^End' log.simpleFoam_scalars || { echo 'SCALAR SOLVER DID NOT FINISH'; exit 4; }
fi
# 4. reconstruct, matrix, record
reconstructPar -latestTime > log.reconstructPar2 2>&1
python3 $REPO/postproc/matrix.py . --out $REPO/results/applied/$(basename "$C").json > log.matrix 2>&1
python3 $REPO/workflow/run_record.py "$C" "$t0" "$(date +%s)"
