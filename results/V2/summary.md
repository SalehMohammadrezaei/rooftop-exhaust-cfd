# V2 (Concordia rooftop stack, R-848 Configuration 1) summary, 2026-10-12
Acceptance fixed in Project.md section 5: correct ranking of stack heights; FAC2 >= 0.5 at the roof receptors. Baseline realizable k-epsilon, medium-grid rule, 10 cells across the stack exit, measured inlet; all four cases on their own base mesh, 2500 iterations, tracer probes flat to < 0.5 % over the last 500.

## Normalised dilution D_N at the roof receptors (tunnel / CFD at Sct 0.4)

| x [m] | hs1 M1 | hs1 M3 | hs3 M1 | hs3 M3 |
|---|---|---|---|---|
| 5 | 0.24 / 0.13 | 1.82 / 0.17 | 0.26 / 0.42 | 3.90 / 0.57 |
| 10 | 0.24 / 0.30 | 2.03 / 0.29 | 0.26 / 0.49 | 4.10 / 0.53 |
| 15 | 0.29 / 0.50 | 2.98 / 0.46 | 0.29 / 0.68 | 5.19 / 0.65 |
| 20 | 0.39 / 0.73 | 3.91 / 0.65 | 0.45 / 0.92 | 5.36 / 0.82 |
| 25 | 0.60 / 0.98 | 4.37 / 0.88 | 0.78 / 1.18 | 7.29 / 1.02 |
| 30 | 0.95 / 1.25 | 4.86 / 1.12 | 1.27 / 1.46 | 7.29 / 1.25 |
| 35 | 1.22 / 1.54 | 5.13 / 1.39 | 1.39 / 1.76 | 7.88 / 1.51 |
| 40 | 1.59 / 1.84 | 5.43 / 1.67 | 1.98 / 2.08 | 8.84 / 1.79 |
| 45 | 2.01 / 2.16 | 5.75 / 1.98 | 2.84 / 2.42 | 9.35 / 2.10 |
| 50 | 3.69 / 2.80 | 6.06 / 2.58 | 4.11 / 3.10 | 9.31 / 2.73 |

## FAC2 (Sct 0.4 / 0.7) and geometric mean CFD/tunnel

| case | FAC2 0.4 | FAC2 0.7 | MG 0.4 | verdict |
|---|---|---|---|---|
| hs1 M1 | 1.0 | 0.5 | 1.196 | met |
| hs1 M3 | 0.0 | 0.0 | 0.213 | not met |
| hs3 M1 | 0.8 | 0.6 | 1.37 | met |
| hs3 M3 | 0.0 | 0.0 | 0.172 | not met |
| hs1 M3, kOmegaSST (sensitivity) | 0.0 | 0.0 | 0.135 | not met |
| hs1 M3, jet-resolved mesh 1.41M cells (grid check) | 0.1 | 0.0 | 0.278 | not met; same as base mesh |

## Ranking test (tunnel: 10/10 receptors in every comparison)

| comparison | CFD receptors ranked correctly |
|---|---|
| taller stack better at M = 1 | 10/10 |
| faster exhaust better at hs = 1 m | 1/10 |
| taller stack better at M = 3 | 10/10 |
| faster exhaust better at hs = 3 m | 2/10 |

Diagnosis (notebook D8, D9): the eddy-viscosity closures destroy the M = 3 jet within three diameters (k of 23 m2/s2 in the shear layer, ambient nut 2000 nu from the 22 % approach turbulence); the plume reaches 7 mm above the tip instead of the ~27 mm of the ASHRAE momentum-rise estimate, and is pulled into the leading-edge roof bubble. Mesh ruled out by the jet-resolved grid check; SST no better. Uncertainties carried: tunnel repeatability 15 %, digitising 2.6 %.
