#!/bin/bash
# Regenerate every figure in results/ and docs/figures from the raw output. Run from the repo root.
#   bash postproc/make_figures.sh [applied_case_dir_for_0deg]
# 2D figures use the default python3; the 3D renders need the viz conda environment (postproc/render/README.md).
set -e
CASE0=${1:-applied/case_by_hand}
python3 postproc/figures/fig_ladder.py --out docs/figures/ladder.png
python3 postproc/figures/fig_v0_abl.py --case ~/scratch/openfoam_cases/V0/realizableKE_atm_fixedShear_B --title "empty domain, realizable k-ε, ABL wall functions"
python3 postproc/figures/fig_v1_aij.py
python3 postproc/figures/fig_v2_irsst.py
python3 postproc/figures/fig_conditions.py results/applied --out results/applied/figures/conditions.png
for j in results/applied/D0_*.json; do
  n=$(basename "$j" .json); c=~/scratch/openfoam_cases/applied/$n; [ "$n" = D0_dir000_U10 ] && [ -d "$CASE0" ] && c=$CASE0
  [ -d "$c/postProcessing" ] && python3 postproc/figures/fig_matrix.py "$j" --case "$c" --out results/applied/figures/matrix_$n.png
  [ -d "$c/postProcessing/slicePlanes" ] && python3 postproc/figures/fig_slices.py "$c" --time "$(ls "$c/postProcessing/slicePlanes" | sort -n | tail -1)" --out results/applied/figures/fields_$n.png
done
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate viz
  ( cd postproc/render
    python geometry.py "$OLDPWD/$CASE0/constant/triSurface" --out "$OLDPWD/results/applied/figures/geometry.png"
    python mesh.py "$OLDPWD/$CASE0" --out "$OLDPWD/results/applied/figures/mesh_cut.png"
    python flow.py "$OLDPWD/$CASE0" --time "$(ls -d "$OLDPWD/$CASE0"/[0-9]* | sed 's|.*/||' | sort -n | tail -1)" --out "$OLDPWD/results/applied/figures/plume_D0_dir000_U10.png" )
fi
python3 postproc/crop.py results/applied/figures/plume_*.png results/applied/figures/geometry.png --margin 60 >/dev/null
