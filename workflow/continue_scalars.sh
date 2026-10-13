#!/bin/bash
# Continue the tagged-scalar stage of an applied case to <endTime> and recompute the matrix.
#   continue_scalars.sh <case_dir> <endTime>
source ~/opt/openfoam2606.sh >/dev/null 2>&1; set -eo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd); C="$(cd "$1" && pwd)"; cd "$C"; N=$(grep numberOfSubdomains system/decomposeParDict | tr -dc 0-9)
sed -i "s/^endTime .*/endTime         $2;/" system/controlDict
rm -rf processor*; decomposePar -latestTime > log.decomposeParC 2>&1
mpirun -np $N simpleFoam -parallel > log.simpleFoam_scalars_cont 2>&1
reconstructPar -latestTime > log.reconstructParC 2>&1
python3 $REPO/postproc/matrix.py . --out $REPO/results/applied/$(basename "$C").json > log.matrix 2>&1
echo "continued $(basename "$C") to $2"
