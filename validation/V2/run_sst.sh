#!/bin/bash
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
while ! grep -q "ALL DONE" run_rest.log 2>/dev/null; do sleep 30; done
( cd case_hs1_M3_SST; rm -rf 0 processor*; cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar 2>&1
  /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
  reconstructPar -latestTime > log.reconstructPar 2>&1
  simpleFoam -postProcess -func yPlus -latestTime > log.yPlus 2>&1
  simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
  echo "done SST: $(grep -c '^Time = ' log.simpleFoam) iterations" )
echo "SST DONE"
