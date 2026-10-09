#!/bin/bash
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
while ! grep -q "ALL DONE" run_rest.log; do sleep 30; done
( cd case_medium_roughfloor
  rm -rf 0 && cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar 2>&1
  /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
  reconstructPar -latestTime > log.reconstructPar 2>&1
  simpleFoam -postProcess -func yPlus -latestTime > log.yPlus 2>&1
  simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
  python3 ../metrics.py . --data ../../../data/raw/aij_caseH/RS_caseH.csv --out ../../../results/V1/medium_realizableKE_roughfloor_run1.json > metrics.out 2>&1
  echo "done roughfloor: $(grep -c '^Time = ' log.simpleFoam) iterations" )
echo "ROUGH DONE"
