#!/bin/bash
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
while ! grep -q "SST DONE" run_sst.log 2>/dev/null; do sleep 30; done
( cd case_by_hand; rm -rf processor*; decomposePar -latestTime > log.decomposePar2 2>&1
  /usr/bin/time -v -o time_simpleFoam2.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam2 2>&1
  reconstructPar -latestTime > log.reconstructPar 2>&1
  simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
  echo "done continuation: last time $(ls -d [0-9]* | sort -n | tail -1)" )
echo "CONT DONE"
