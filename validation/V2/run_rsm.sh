#!/bin/bash
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1; REPO=$(cd ../.. && pwd)
while pgrep -x simpleFoam >/dev/null; do sleep 60; done   # -x: exact process name, not the command lines of monitoring shells
for M in SSG LRR; do C=case_hs1_M3_$M
  ( cd $C; rm -rf 0 processor*; cp -r 0.orig 0; setExprFields > log.setExprFields 2>&1; decomposePar > log.decomposePar 2>&1
    /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
    reconstructPar -latestTime > log.reconstructPar 2>&1; postProcess -func samplePoints -latestTime > log.sample 2>&1
    python3 $REPO/validation/V2/metrics.py . --ref $REPO/data/digitised/irsst_r848/fig5_1_isolated_hs1_M3_Xs0.csv --M 3 --out $REPO/results/V2/hs1_M3_${M}_run1.json > metrics.out 2>&1
    echo "done $M: $(grep -c '^Time = ' log.simpleFoam) iterations; $(grep -c 'FATAL\|nan' log.simpleFoam) fatal/nan lines" )
done; echo "RSM DONE"
