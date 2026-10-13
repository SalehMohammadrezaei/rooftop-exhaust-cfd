#!/bin/bash
# Wait for the listed applied cases to finish, then rebuild the summary, the per-case figures and the
# 0-degree renders, so the results are ready for review when the runs are.
#   setsid nohup bash workflow/morning_after.sh D0_dir000_U10 D0_dir090_U10 ... > ~/scratch/openfoam_cases/applied/morning_after.log 2>&1 &
REPO=$(cd "$(dirname "$0")/.." && pwd); A=~/scratch/openfoam_cases/applied; cd "$REPO"
for c in "$@"; do
  until [ -f "$A/$c/run_record.json" ] || grep -q "DID NOT FINISH\|failed" "$A/$c/log.run_applied" 2>/dev/null; do sleep 600; done
  echo "$(date +%H:%M) $c: $(tail -1 "$A/$c/log.run_applied")"
done
python3 postproc/collect_applied.py results/applied --out results/applied/summary.md
python3 postproc/figures/fig_conditions.py results/applied --out results/applied/figures/conditions.png
for c in "$@"; do
  [ -f "results/applied/$c.json" ] || continue
  python3 postproc/figures/fig_matrix.py "results/applied/$c.json" --case "$A/$c" --out "results/applied/figures/matrix_$c.png"
  T=$(ls -d "$A/$c"/[0-9]* | sed 's|.*/||' | sort -n | tail -1)
  python3 postproc/slices.py "$A/$c" --time "$T" --fields U sAll sF --out "$A/$c/slices_tmp" --planes y0 zroof > "$A/$c/log.slices" 2>&1
  python3 postproc/figures/fig_slices.py "$A/$c" --time "$T" --out "results/applied/figures/fields_$c.png"
done
source ~/miniforge/etc/profile.d/conda.sh && conda activate viz && cd postproc/render
for c in "$@"; do
  [ -f "$REPO/results/applied/$c.json" ] || continue
  T=$(ls -d "$A/$c"/[0-9]* | sed 's|.*/||' | sort -n | tail -1)
  python flow.py "$A/$c" --time "$T" --out "$REPO/results/applied/figures/plume_$c.png" 2>&1 | grep -v WARN
done
echo "MORNING DONE $(date +%H:%M)"
