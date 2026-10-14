# Workflow

Every case is generated from a parameter file and run by one driver; nothing in a case
directory is edited by hand after generation.

| script | does |
|---|---|
| `make_case.py <params.json> <out>` | V0 family: dictionaries from `templates/V0` with the placeholders filled |
| `run_case.sh <case>` / `run_family.sh <root>` | V0 runs, serial |
| `make_applied_case.py --dir D --speed U [--variant D0] --out <root>` | applied case from `applied/case_by_hand` and `params/applied_design.json`: rotated STL set, rotated refinement boxes, inlet profile, flows, probes, `case_record.json` |
| `run_applied.sh <case>` | mesh (parallel snappyHexMesh, checkMesh gate), flow, tagged scalars (`make_scalars.py`), reconstruct, matrix, `run_record.json`. Each stage is skipped when its log shows it finished, so the same command resumes a stopped case. `ALLOW_FAILED_MESH=1` overrides the gate and marks the result preliminary |
| `make_scalars.py <case> --time T` | writes the 12 tagged scalars into time T, the scalarTransport function objects and the receptor monitors; Sct and iteration count from the parameter file |
| `continue_scalars.sh <case> <endTime>` | extends a finished scalar stage |
| `queue_applied.sh <maxjobs> <case>...` | runs cases up to N at a time |
| `morning_after.sh <case>...` | waits for cases to finish, then rebuilds the summary, the per-case figures and the renders |
| `run_record.py <case> t0 t1` | the run record (build, commit, cells, iterations, wall time) |

Cases live outside the repository (`~/scratch/openfoam_cases/applied/<name>`); only their JSON
records, summaries and figures come back into `results/`.
