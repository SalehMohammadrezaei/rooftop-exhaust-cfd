# Working rules for this project

(kept at docs/working-rules.md; rule numbers are referenced from the notebook and the decision records)

Project: rooftop exhaust and heat re-entrainment at a data-centre-type facility (Project.md is the
governing brief). Software: OpenFOAM v2606 (OpenCFD), sourced with `source ~/opt/openfoam2606.sh`.

## Decisions are human decisions

1. Every new CFD modelling decision needs written approval before it is implemented:
   turbulence model, boundary conditions, mesh strategy and sizes, numerical schemes, wall
   treatment, validation cases and acceptance criteria, physical models (buoyancy, scalar
   transport, source treatment), domain size, and anything that changes what a result means.
2. No silent changes. A change to any item in rule 1 is never made as a side effect of another
   task. If a run cannot proceed without such a change, stop, state the change and the reason,
   and wait.
3. Explain the first occurrence, automate the repetitions. The first time a case type, script
   or post-processing step is built, it is explained in prose with the choices spelled out. After
   it is approved it is scripted and reused without re-explanation, but never silently altered.
4. The validation acceptance numbers in Project.md section 5 are fixed before a run and reported
   whether met or not. They are not adjusted after the fact.

## Evidence standards

5. Convergence is quantitative. A run is converged when the primary quantities in section 9 are
   flat to within 1 percent over the monitoring window and the mass and scalar balances close
   within 1 percent. Residual levels alone never establish convergence. If a quantity oscillates,
   the cycle average and the amplitude are reported.
6. No claim rests on residuals or contour plots only. Every stated result carries a number, its
   definition, and the grid, model and input uncertainty bands where they exist.
7. Every input is labelled by its kind: measured (from a dataset or datasheet, with citation),
   derived (computed from measured inputs, with the formula), empirical or model (a correlation,
   closure constant or assumption, with source), or numerical (a scheme, tolerance or mesh
   setting). Indicative values from the brief are labelled as such until replaced.
8. Validation metrics are computed by script from the raw dataset files, never read off a plot.

## Repository discipline

9. Small, reviewable Git commits: one case, script or decision per commit, with a message that
   says what changed and why. Nothing is force-pushed. Mesh files, processor directories,
   time directories and logs are never committed; parameter files, dictionaries and scripts are.
10. Every case is generated from one parameter file by script. A case directory that cannot be
    regenerated from the repository is not a result.
11. Every run logs the OpenFOAM build, the Git commit, mesh statistics, decomposition, wall time
    and core count into the case's results record.
12. Production runs are not started without an agreed cost estimate (section 10) and an agreed
    core count. On this shared workstation, check the load first; use at most the agreed cores.

## Working style

13. Say what was done, what was skipped and what failed, in that order, with the evidence.
14. When something is uncertain, say so and name the test that would settle it.
