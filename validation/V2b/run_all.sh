#!/bin/bash
# V2b: mesh, run and score both full-scale cases sequentially on 16 cores.
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
REPO=$(cd ../.. && pwd); ROOT=~/scratch/openfoam_cases/V2b
while pgrep -f "simpleFoam -parallel" >/dev/null; do sleep 30; done
for spec in "case_hs1_M1 fig4_4a_isolated_hs1_M1_Xs0 hs1_M1" "case_hs3_M1 figD2a_isolated_hs3_M1_Xs0 hs3_M1"; do set -- $spec
  ( cd $ROOT/$1
    blockMesh > log.blockMesh 2>&1; surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1; snappyHexMesh -overwrite > log.snappyHexMesh 2>&1; checkMesh > log.checkMesh 2>&1
    rm -rf 0 processor*; cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar 2>&1
    /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
    reconstructPar -latestTime > log.reconstructPar 2>&1
    simpleFoam -postProcess -func yPlus -latestTime > log.yPlus 2>&1
    simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
    python3 $REPO/validation/V2/metrics.py . --ref $REPO/data/digitised/irsst_r848/$2.csv --M 1 --UH 10 --H 15 --d 0.6 --xs -49.5 --scale 1 --out $REPO/results/V2b/$3_run1.json > metrics.out 2>&1
    echo "done $1: $(grep -o 'nCells:[0-9]*' constant/polyMesh/owner | head -1), $(grep -c '^Time = ' log.simpleFoam) iterations, $(grep -E 'Mesh OK|Failed' log.checkMesh)" )
done
echo "V2B DONE"
