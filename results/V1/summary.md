# V1 (AIJ Case H) summary, 2026-10-09. Acceptance fixed in Project.md section 5: hit rate on U >= 0.66; FAC2 >= 0.5 and |FB| <= 0.3.

## Velocity

| run | final iteration | hit rate U | hit rate k | pass |
|---|---|---|---|---|
| coarse_realizableKE_run1 | 397 | 0.59 | 0.214 | not met |
| fine_realizableKE_run1 | 985 | 0.609 | 0.23 | not met |
| medium_kOmegaSST_run1 | 2000 | 0.617 | 0.293 | not met |
| medium_realizableKE_loglaw_run1 | 1255 | 0.632 | 0.243 | not met |
| medium_realizableKE_roughfloor_run1 | 600 | 0.338 | 0.356 | not met |
| medium_realizableKE_run1 | 595 | 0.604 | 0.224 | not met |
| medium_realizableKE_tracer_run1 | 3595 | 0.604 | 0.224 | not met |

## Grid convergence index (realizable k-epsilon, r = 1.41)

| quantity | coarse | medium | fine | p | GCI fine |
|---|---|---|---|---|---|
| cavity_Ux | -0.4546 | -0.3993 | -0.385 | 3.92 | 1.62 % |
| reattach_Ux | 0.4687 | 0.6412 | 0.7719 | 0.8 | 66.17 % |
| drag_N | 0.1103 | 0.1157 | 0.1164 | 5.82 | 0.12 % |

## Concentration (medium grid, realizable k-epsilon, measured inlet; 490 points with c > 1 ppm; balance closed to 0.05 %)

| Sct | FAC2 | FB | MG (geometric mean CFD/exp) | pass |
|---|---|---|---|---|
| 0.4 | 0.571 | -0.558 | 1.204 | not met |
| 0.5 | 0.547 | -0.649 | 1.221 | not met |
| 0.6 | 0.506 | -0.712 | 1.213 | not met |
| 0.7 | 0.498 | -0.76 | 1.19 | not met |
| 0.8 | 0.484 | -0.798 | 1.16 | not met |
| 0.9 | 0.467 | -0.828 | 1.126 | not met |

## Empty-domain drift (measured inlet, medium grid): U within 3-4 % above z = 0.075 m at the building position for both closures; k decays 13 % at roof height. Below 0.075 m the smooth floor accelerates the flow (C14). Rough floor sensitivity: hit rate 0.34 (C15).
