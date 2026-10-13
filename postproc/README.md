# Post-processing

Every number in `results/` comes from one of these scripts reading raw function-object output.

| script | reads | writes |
|---|---|---|
| `matrix.py <case> --out <json>` | `postProcessing/recv_*/` area averages of the tagged scalars | source-to-receptor matrix F, intake dilution, chiller rise, balance and convergence amplitude |
| `collect_applied.py <results_dir> --out summary.md` | the JSON records | the summary table and the governing conditions |
| `slices.py <case> --time T --fields ...` | the case (runs `postProcess -func slicePlanes`) | raw cutting-plane files under `postProcessing/slicePlanes/T/` |
| `abl_profiles.py` | V0 line samples | profile homogeneity numbers |
| `style.py` | | the figure style every `figures/fig_*.py` imports |
| `figures/fig_v0_abl.py`, `fig_v1_aij.py`, `fig_v2_irsst.py` | V0 samples, V1 sample cloud + AIJ CSV, V2 JSON records | validation figures |
| `figures/fig_slices.py`, `fig_matrix.py` | slice files, matrix JSON + receptor histories | applied figures |
| `figures/fig_ladder.py` | | the validation-ladder diagram |
| `render/*.py` | STL set, case | 3D renders (see `render/README.md`) |

Figures are written as PNG (README) and PDF (report) with the same basename.
