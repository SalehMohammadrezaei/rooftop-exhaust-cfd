# 0006 V1 closing decisions

Date: 2026-10-12. Approved ("yes to all").

## Outcome of V1 (AIJ Case H), reported as it stands
- Velocity: hit rate on U 0.59 (coarse), 0.60 (medium), 0.61 (fine) with realizable k-epsilon,
  0.62 with k-omega SST, 0.63 with the log-law inlet; pass mark 0.66 not met. Drag and cavity
  velocity grid-converged (GCI 0.1 % and 1.6 %); the recirculation behind the block is too long and
  too slow by about 0.5 m/s on every grid and both closures. Upstream, roof and far wake correct.
- Concentration (medium grid, realizable k-epsilon): FAC2 0.57 / 0.55 / 0.51 at Sct 0.4 / 0.5 / 0.6
  (mark 0.5 met), fractional bias -0.56 at best (mark 0.3 not met); far wake FAC2 0.90, FB +0.07;
  the excess sits in the near wake and beside the building, where the too-long recirculation holds
  the tracer.
- Inflow turbulence accounts for about a quarter of the wake deficit; the remainder is the
  eddy-viscosity model form. Results: results/V1/summary.md; notebook C8 to C17.

## Decisions
1. Baseline for V2 and the applied case: medium-grid resolution rule (10 cells per building
   width is the coarse floor; the medium rule, 14, is the baseline), realizable k-epsilon, smooth
   walls where the surface is smooth, measured or log-law inlet as the case requires, fixed-shear
   top, atm wall set on rough ground (0002). SST is retained as the closure sensitivity (Project.md
   block S), not as a second baseline.
2. Turbulent Schmidt number: not fixed on V1 alone. 0.4 and 0.7 are both carried into V2; the
   single value is fixed on V1 and V2 together and recorded then. The V1 sweep 0.4 to 0.9 is the
   Schmidt sensitivity band.
3. The unmet marks are carried, not adjusted: the report states the numbers, the cause (model-form
   limitation of linear eddy-viscosity RANS in the near wake of a sharp-edged body, grid-independent),
   the inflow share, and the consequence that applied near-wake concentrations are conservative
   (too little dilution). The V1-LES rung stays where Project.md section 5 puts it, after the applied
   MVP runs; it is the planned measurement of this model-form error.

## Confirmed in passing
Decisions 0004 (tracer setup) and 0005 (rough-floor sensitivity, negative) stand as written.
