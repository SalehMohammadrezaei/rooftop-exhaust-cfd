# Run record: Phase-0 smoke test, atmDownstreamDevelopment (official v2606 tutorial)

| Item | Value |
|---|---|
| Date started | 2026-10-08T10:35:25Z |
| OpenFOAM | v2606, OpenCFD build  |
| MPI | mpirun (Open MPI) 4.1.6 |
| Repository commit | bf0211dde90dbba332d2b5448f0812d159084a63 (clean tree) |
| Host | b-11uxx6xvs954, 192 logical cores, WSL2 |
| Load average at launch | 155.98 156.00 156.01 |
| Agreed cores | 4 per closure, closures sequential |
| Source | /home/impres/opt/openfoam2606-root/usr/lib/openfoam/openfoam2606/tutorials/verificationAndValidation/atmosphericModels/atmDownstreamDevelopment |
| Sandbox | /home/impres/scratch/smoke/atmDownstreamDevelopment (ext4, outside the repo) |
| Edits to tutorial | decomposeParDict: numberOfSubdomains 8 -> 4, n (8 1 1) -> (4 1 1). Nothing else. |
| Closures | kEpsilon, kOmegaSST (tutorial defaults) |
| gnuplot | not installed; tutorial plot step will be skipped; profiles post-processed by own script |

## Completion (2026-10-08T10:55:00Z)

| Item | Value |
|---|---|
| Allrun wall clock, both closures incl. mesh | 19 min 09 s |
| kEpsilon simpleFoam | 5000 iterations, ExecutionTime 463 s on 4 cores |
| kOmegaSST simpleFoam | 5000 iterations, ExecutionTime 653 s on 4 cores |
| Mesh | 125000 cells; checkMesh: 24 cells with determinant < 0.001 (top row), all other checks OK |
| Allrun exit code | 1, caused only by the missing gnuplot in the final plot step |
| Load average at completion | 159.57 159.80 158.68 |

## Results against the fixed criteria (post-processed by scripts/abl_profiles.py and OpenFOAM function objects, from raw files)

Windows: 0 < z < 18 m (3 Zref) and 0 < z < 100 m; relative change is w.r.t. the inlet patch profile at the same z.

| Criterion | kEpsilon | kOmegaSST | Pass mark | Result |
|---|---|---|---|---|
| Completes 5000 iterations, no FPE | yes | yes | required | pass |
| Mass imbalance inlet vs outlet | 2e-6 m3/s of 767428.5 (3e-10 %) | 0 of 767426.4 | < 1 % | pass |
| Max dU/U, inlet to x=4000 m, z<100 m | 2.40 % at z=1.0 m | 0.73 % at z=7.3 m | kEps < 5 % | pass (SST reported only) |
| Max dk/k, inlet to x=4000 m, z<100 m | 2.16 % at z=29 m | 11.7 % at z=1.0 m | kEps < 10 % | pass (SST reported only) |
| Max d(eps or omega), inlet to x=4000 m | eps 11.7 % at z=2.1 m | omega 12.8 % at z=1.0 m | none set | reported |
| Ground y+ (min / mean / max) | 20723 / 20752 / 21114 | 20760 / 20795 / 20833 | none set | fully rough regime |
| Whole-field change 4500 -> 5000, U | 1.0e-5 m/s (6e-5 % of max) | 2.0e-8 m/s | flat to 1 % | pass |
| Whole-field change 4500 -> 5000, k | 7.0e-6 m2/s2 (5e-4 % of max) | 0 | flat to 1 % | pass |
| Initial residuals at 5000 (Ux, p, k, eps) | 3e-9, 1.5e-5, 1.9e-7, 5.5e-9 | see logs/ | supporting only | flat from iteration ~1000 |
| Mean abs deviation from HW/RH digitised U, x=4000 m | 6.0 % (max 29.9 %) | 7.2 % | none set | see note |

Notes:
- The first-cell station (x=5 m) differs from the inlet patch by 12 % in U and 47 to 50 % in epsilon/nut at z=0.5 m. That is the wall-function cell adjusting the patch profile to the discrete log-law and is expected; it is excluded from the criteria.
- The digitised file Ux-HW-RH-Fig6a mixes the Richards-Hoxey analytical points with the HW x=2500 and x=4000 points in one file, so the benchmark deviation mixes three curves. The large max (30 %) comes from near-ground HW points where HW themselves report drift. A per-series comparison would need the file split; not done for the smoke test.
- The SST setup maintains U better (0.7 %) but k drifts 11.7 % in the first cell, consistent with the tutorial's omega wall function not being z0-aware.
- The runs were converged by iteration ~1000; 5000 is the tutorial's fixed count.
