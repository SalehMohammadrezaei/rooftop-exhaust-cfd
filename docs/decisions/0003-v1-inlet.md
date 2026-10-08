# 0003 V1 (AIJ Case H) inlet profiles

Date: 2026-10-08. Approved by Saleh ("ok C then").

## Decision
Inlet U and k are the measured approach-flow profiles (data/raw/aij_caseH/AF_caseH.csv, x = -2.5H),
tabulated point by point and interpolated in z. epsilon is derived from local equilibrium,
epsilon = sqrt(Cmu) k dU/dz, the AIJ guideline practice (Tominaga et al. 2008); omega = epsilon/(Cmu k).
Two safeguards are part of the decision:
1. An empty-domain run of the V1 box with the V0 tooling quantifies the profile drift over the
   2.5H fetch to the building position. The number goes into the V1 record.
2. The V0 log-law family (option A: atmBoundaryLayerInlet*, fitted z0 = 11.7 mm, Uref 3.23 m/s at
   0.2 m) is run once as an inflow sensitivity. Its effect on hit rate and FAC2 is the inflow part of
   the uncertainty band (Project.md section 7).

## Why
A log law fits the measured U within 2.9 % rms (z0 = 11.7 mm, u* = 0.448 m/s, consistent with u*
from the measured shear stress). But the measured stress-to-k ratio is 0.415 against the model's
sqrt(Cmu) = 0.3, so the log-law family's k (0.67 m2/s2) is 49 % above the measured 0.45. No inlet
satisfies U, k and the ground wall function simultaneously with Cmu = 0.09. Option C keeps the
measured turbulence, which controls separation and plume spread, and measures the drift instead of
assuming consistency.

## Rejected
A (log-law family as is): k 49 % high. B (log-law family with C2 = 0.45): same drift issue as C with
no benefit over the measured profiles.

## Also confirmed
Case H stays as the V1 benchmark (AIJ set; hit rate 0.66 per VDI 3783/9, FAC2 0.5 and FB 0.3 per
COST 732). CEDVAL A1-1 noted as a possible stretch item, not on the ladder.

## Addendum (Saleh, 2026-10-08): slope for epsilon
dU/dz in epsilon = sqrt(Cmu) k dU/dz is taken from the log-law fit of the measured U
(u* = 0.448 m/s, z0 = 11.7 mm), not from finite differences of the 18 measured points, which are
dominated by measurement noise (slopes jumping 1.2 to 6.5 1/s between neighbouring heights near z = H).
Measured U and k are used unchanged. Script: validation/V1/make_inlet_profiles.py.
