# 0007 V2 (Concordia rooftop stack, R-848 Configuration 1) setup

Date: 2026-10-12. Stack representation chosen by Saleh ("first": resolved stack at ten cells across
the diameter, the brief's rule). The other items follow V1 and Project.md and were presented as
defaults; any can be revoked.

| Item | Choice | Reason |
|---|---|---|
| Scale | Model scale 1:200 as tested: H = 0.075 m, building 0.25 x 0.25 m in plan, stack diameter 3 mm, U_H = 6.2 m/s, Re_H = 31,000 | Project.md section 5: V2 at tunnel scale, V2b at full scale |
| Geometry origin | As V1: x = 0 at the leeward wall, y = 0 on the centreline, z = 0 on the floor; wind along +x; building x in [-0.25, 0] | Same convention as V1 and the receptor distances (from the stack) |
| Stack | Vertical pipe of 3 mm diameter with its centre at x = -0.2475, i.e. the pipe wall 1 mm inside the upwind roof edge (Xs = 0 in the report means "at the upwind edge"; a centre exactly on the edge would leave half the pipe in the air, found by Saleh in ParaView 2026-10-12; 1 mm is 20 cm full scale, within the placement uncertainty, and receptor distances are measured from the stack), y = 0, tip at hs = 0.5 cm and 1.5 cm above the roof (1 and 3 m full scale); fixed uniform exit velocity Ve = M U_H with M = 1 and 3; resolved with 10 cells across the diameter | Project.md section 7 (10 cells across a flue); the applied flues are modelled the same way |
| Flow cases | 4: hs 1 m and 3 m, M 1 and 3 | The digitised data cover these |
| Domain | Inlet 5H upwind of the windward wall, outlet 15H downwind of the leeward wall, sides 6H from the building faces, top 8H: x -0.625..1.125, y +-0.575, z 0..0.6 m; blockage 2.7 % | AIJ guideline; sides and top widened over V1 because the building is 3.3H wide and blockage must stay below 3 % |
| Inlet | Digitised measured profile (Figure 3.1): U = (V/Vg) 14.2 m/s tabulated in z; k = 1.5 (I_u U)^2 from the turbulence intensity (isotropy assumed, flagged); epsilon from local equilibrium with the slope of the digitised profile; held constant above 95 cm | Decision 0003 pattern; the tunnel profile is the measured one |
| Closure, numerics, walls | Realizable k-epsilon, V1 numerics, smooth walls (building, floor, stack), medium-grid rule for the building (about 5 mm cells on it) with nested refinement to 0.3 mm at the stack | Decision 0006 baseline |
| Tracer | Passive scalar, volume fraction, exhaust s_e = 1 at the stack inlet; Sct 0.4 and 0.7 (0006); receptor concentration taken at the roof surface cell centres on the centreline at 2.5 cm steps (5 m full scale) | D_N = D_r Q / (U_H H^2) with D_r = 1/s_r |
| Acceptance | Correct ranking of hs = 1 m against 3 m at both M; FAC2 >= 0.5 over the 40 roof receptors, computed on D_N | Project.md section 5, fixed before the runs |
| Uncertainty carried | Tunnel repeatability 15 %, digitising 2.6 % (data README) | |
