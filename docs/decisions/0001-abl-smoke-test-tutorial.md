# 0001 Phase-0 smoke test: ABL inlet and rough ground on an official v2606 tutorial

Date: 2026-10-08. Approved by Saleh (plan approval, same day).

## Decision
Use `tutorials/verificationAndValidation/atmosphericModels/atmDownstreamDevelopment` (Hargreaves &
Wright 2007 empty fetch, kEpsilon and kOmegaSST setups) as the smoke-test base, run exactly as
shipped except the core count (8 to 4). `turbineSiting` is demoted to a reference for the
snappyHexMesh-on-terrain pattern only.

## Why
- Same physical question as V0 (profile maintenance over an empty fetch) with a published benchmark.
- turbineSiting adds terrain, actuator disks and UTM coordinates, has no benchmark, and mixes
  kappa = 0.41 (inlet, nut wall function defaults) with 0.40 (epsilon wall function).

## Findings recorded for later decisions
- The tutorial pairs the z0-aware `atmNutkWallFunction` with the standard `epsilonWallFunction` /
  `omegaWallFunction`; v2606 also ships `atmEpsilonWallFunction` and `atmOmegaWallFunction`.
  In the smoke test SST held U to 0.7 % but k drifted 11.7 % in the first ground cell.
- All residuals were flat by iteration ~1000 of the fixed 5000.
- The shipped digitised dataset mixes three curves in one file; not usable as a per-series benchmark.
- Results: results/smoke/atmDownstreamDevelopment_run_record.md.

## What was skipped
gnuplot plots (not installed); per-series benchmark comparison.
