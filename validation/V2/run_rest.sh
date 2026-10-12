#!/bin/bash
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
while pgrep -f "simpleFoam -parallel" >/dev/null; do sleep 30; done
for C in case_hs3_M3 case_hs1_M1 case_hs3_M1; do
  ( cd $C; rm -rf 0 processor*; cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar 2>&1
    /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
    reconstructPar -latestTime > log.reconstructPar 2>&1
    simpleFoam -postProcess -func yPlus -latestTime > log.yPlus 2>&1
    simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
    echo "done $C: $(grep -c '^Time = ' log.simpleFoam) iterations" )
done
echo "ALL DONE"
