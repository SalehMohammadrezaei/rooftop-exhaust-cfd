#!/bin/bash
# Remaining V1 runs, sequential on 16 cores, started after the fine run has released its cores.
# Each: fields, initial guess, decompose, solve, reconstruct, y+, sample, score.
cd "$(dirname "$0")"; source ~/opt/openfoam2606.sh >/dev/null 2>&1
DATA=../../../data/raw/aij_caseH/RS_caseH.csv
while pgrep -f "simpleFoam -parallel" >/dev/null; do sleep 30; done
run_one() {   # $1 case dir, $2 result name, $3 mesh (yes = blockMesh only for empty cases), $4 sample FO name
    c=$1; name=$2
    ( cd "$c" || exit 1
      [ "$3" = "blockMesh" ] && { blockMesh > log.blockMesh 2>&1; checkMesh > log.checkMesh 2>&1; }
      rm -rf 0 && cp -r 0.orig 0
      setExprFields > log.setExprFields 2>&1
      decomposePar > log.decomposePar 2>&1
      /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
      reconstructPar -latestTime > log.reconstructPar 2>&1
      simpleFoam -postProcess -func yPlus -latestTime > log.yPlus 2>&1
      simpleFoam -postProcess -func "$4" -latestTime > log.sample 2>&1
      [ "$4" = "samplePoints" ] && python3 ../metrics.py . --data $DATA --out ../../../results/V1/$name.json > metrics.out 2>&1
      echo "done $name: $(grep -c '^Time = ' log.simpleFoam) iterations" )
}
run_one case_medium_loglaw            medium_realizableKE_loglaw_run1  none      samplePoints
run_one case_empty_medium_realizableKE empty_medium_realizableKE       blockMesh sampleProfiles
run_one case_empty_medium_kOmegaSST    empty_medium_kOmegaSST          blockMesh sampleProfiles
# tracer: continues from the converged flow in 595/, no decomposition needed? (parallel: decompose with -latestTime)
( cd case_medium_scalar
  decomposePar -latestTime > log.decomposePar 2>&1
  /usr/bin/time -v -o time_simpleFoam.txt mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1
  reconstructPar -latestTime > log.reconstructPar 2>&1
  simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
  python3 ../metrics.py . --data $DATA --out ../../../results/V1/medium_realizableKE_tracer_run1.json > metrics.out 2>&1
  echo "done tracer: $(grep -c '^Time = ' log.simpleFoam) iterations" )
echo "ALL DONE"
