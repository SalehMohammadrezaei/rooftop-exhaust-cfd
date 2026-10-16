# 0004 V1 tracer (concentration) setup

Date: 2026-10-09. Made under the standing instruction "do all remaining runs and report to finish V1";
listed here for confirmation or revocation.

| Item | Choice | Reason |
|---|---|---|
| Method | Passive scalars solved by the scalarTransport function object on the converged medium-grid realizable k-epsilon flow, continued 500 iterations with residualControl removed | Project.md section 4 and 6: tagged scalars on the frozen flow; the converged flow does not change further |
| Diffusivity | D = nu + nut/Sct | Standard gradient-diffusion closure |
| Schmidt sweep | Sct = 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, six scalars in one run | Project.md section 6: one value fixed from V1 and V2, 0.4 to 0.9 as the sensitivity band |
| Source | Volume source of Q = 5.83e-6 m3/s in the cell containing the floor hole at (0.05, 0, 0.003) | Hole diameter 4 mm is below the 7 mm cell; exit velocity Q/A = 0.46 m/s is 14 % of U_H, so source momentum is negligible (passive point source, as the readme describes) |
| Scalar boundary conditions | inlet 0, outlet inletOutlet 0, all walls and top/sides zeroGradient | Clean air in, no flux through solid or far boundaries |
| Comparison variable | C* = c U_H H^2 / Q, tunnel c in ppm converted to volume fraction; CFD scalar is volume fraction directly | Dimensionless, scale-independent |
| Metrics | FAC2 (fraction of points with 0.5 <= C*cfd/C*exp <= 2) and fractional bias FB = 2 (mean exp - mean cfd)/(mean exp + mean cfd), on points where the measured c exceeds 1 ppm; the threshold and the count of excluded points are reported | COST 732 practice: pairs below the measurement noise floor are excluded; the tunnel data contain negative readings down to the noise level |
| Acceptance | FAC2 >= 0.5 and |FB| <= 0.3, Project.md section 5, fixed before the runs | |
| Sct selection rule | The Sct with the best FAC2 and |FB| on V1 is carried to V2; if V2 prefers another value, the choice is made on the two together and recorded | Project.md section 6 |

Not done: scalar on the SST flow (the velocity validation did not separate the closures; the
tracer sweep is run on one flow field and the closure sensitivity is reported on velocity).
