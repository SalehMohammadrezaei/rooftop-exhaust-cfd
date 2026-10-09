#!/bin/bash
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
while ! grep -q "ROUGH DONE" run_rough.log; do sleep 30; done
( cd case_medium_scalar
  rm -rf processor*; decomposePar -latestTime > log.decomposePar 2>&1
  /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
  reconstructPar -latestTime > log.reconstructPar 2>&1
  simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
  python3 ../metrics.py . --data ../../../data/raw/aij_caseH/RS_caseH.csv --out ../../../results/V1/medium_realizableKE_tracer_run1.json > metrics.out 2>&1
  echo "done tracer: $(grep -c '^Time = ' log.simpleFoam) iterations" )
echo "TRACER DONE"
