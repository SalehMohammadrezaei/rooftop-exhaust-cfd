# 0005 V1 tunnel-floor roughness sensitivity

Date: 2026-10-09. Made under Saleh's instruction to finish the V1 runs; listed for confirmation or
revocation. It adds one run; it does not change the baseline decided in V1 decision 2 (smooth floor).

## What was found
The empty-domain check (decision 0003, safeguard 1; notebook C14) shows the measured inlet profile
is maintained within a few percent above z = 0.075 m (0.37H) all the way to the building position,
but in the lowest cells the smooth-wall function accelerates the flow: measured 0.65 to 1.13 m/s
below 0.025 m, CFD 1.8 to 2.0 m/s at the tunnel station. The tunnel's near-floor velocity deficit
was produced by upstream roughness elements; a smooth wall cannot sustain it. 312 of the 826
measured points lie at z = 0.0125 m, inside that layer.

## Sensitivity run
Medium grid, realizable k-epsilon, measured inlet, ground patch switched to the z0-consistent
rough-wall set: atmNutkWallFunction, atmEpsilonWallFunction (atmOmegaWallFunction for SST) with
z0 = 11.7 mm, the value fitted to the measured approach flow (notebook entry 13), kappa 0.4,
Cmu 0.09. The building stays smooth. First cell centre on the floor is 14 mm, so y/z0 = 1.2, inside
the range V0 showed to be fine with this wall set.

## Rule
The result is a sensitivity on the velocity hit rate, reported beside the smooth-floor baseline.
If it is adopted as the V1 baseline, that is a new decision for Saleh, not a consequence of this one.
