# 0002 V0 empty-domain setup

Date: 2026-10-08. Decision 1 (ground wall functions: run both, choose by numbers) approved
explicitly ("C"). The remaining setup choices were delegated in writing the same day
("decide yourself until we reach to our project then explain to me"), and are listed here so he can
revoke any of them. Parameter file: params/V0_empty_domain.json. Every input there carries its kind.

| Item | Choice | Reason |
|---|---|---|
| Domain | x -8H..+20H, z 9H, from Project.md section 4; y a 3-cell 12 m slab with symmetry sides | No building in V0, so the span is irrelevant; one cell fails checkMesh's determinant test |
| Inlet | atmBoundaryLayerInlet{Velocity,K,Epsilon,Omega}; Uref 10 m/s at Zref 15 m, z0 0.3 m, d 0 | Project.md section 4 |
| kappa, Cmu | 0.40, 0.09 | 0.40 is the value for which sigmaEps 1.11 makes the Richards-Hoxey profiles an exact k-eps solution (HW 2007) |
| Closures | kEpsilonHW (standard k-eps, sigmaEps 1.11) as reference; realizableKE and kOmegaSST stock | Project.md section 6 names the latter two; the first is known to maintain the profile |
| Ground wall sets | std (epsilon/omegaWallFunction) and atm (atmEpsilon/atmOmegaWallFunction), nut always atmNutkWallFunction | Decision 1: measure, then choose |
| Top | fixedShearStress tau = u*^2, and slip | Project.md section 4: "chosen by the empty-domain test" |
| Meshes | A: 4 m uniform (y/z0 = 6.7); B: first cell 1 m graded (y/z0 = 1.7); C: first cell 0.5 m graded (y/z0 = 0.8), added after A and B, fixed-shear top only | Measures the sensitivity to first-cell height versus z0, including the near-building case |
| Schemes, solvers, relaxation | Unchanged from the tutorial (numerical) | Known-good baseline; applied cases get their own decision |
| Stopping | residualControl 1e-6 all equations, endTime 3000 | Smoke test: flat by ~1000 |
| Monitors | Profiles at inlet, first cell, -4H, 0, +10H, outlet; probe of U,k at (0, 6, 15); fieldMinMax; inlet/outlet flow | Primary quantity for V0 is the profile at x = 0 |
| Acceptance | max relative change of U and of k, inlet patch to x = 0, 0 < z < 3H, below 5 % | Project.md section 5, fixed before the runs |

## Outcome (2026-10-08, 30 runs, results/V0/summary.md)
- U held within 2.4 % at the building position in every case with the atm wall set.
- k held within 5 % only with the atm wall set on meshes B and C (first cell 1 m and 0.5 m); on the
  4 m mesh realizableKE and SST drift 9 to 11 % in the first cell. The std set fails on B and C.
- Fixed shear on top beats slip at the outlet (k drift 3 to 4 % versus 7 to 11 %); at the building
  the difference is under 1 %.
- Mesh C (first cell centre below z0) is the best mesh with the atm set, so the near-building strip
  needs no special treatment beyond using the atm wall functions. The 0.25 m cell was not run.
- realizableKE and kOmegaSST are not separated by V0 (k within 1.7 to 1.9 % on mesh C).

## Closing decision (2026-10-08)
1. Ground baseline for V1 onward: atmNutkWallFunction with atmEpsilonWallFunction / atmOmegaWallFunction
   (the "atm" set), first ground cell 1 m or smaller.
2. Top boundary: fixedShearStress with tau = u*^2.
3. Closure: realizable k-epsilon and k-omega SST both carried to V1 and V2; the baseline is chosen
   there by the written criteria of Project.md section 6.
V0 acceptance (Project.md section 5): met for both closures with the baseline above (k within 3.7 % on
mesh B, 1.9 % on mesh C; U within 2.4 %).
