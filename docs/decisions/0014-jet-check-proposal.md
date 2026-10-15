# 0014 Scale-resolving check of the flue jet (proposed 2026-10-14; decided 2026-10-15: option C, no check)

## Why now
Decision 0013 fixed a trigger: if an intake dilution lands within a factor of 3 of the limit
(700 to 6,000), the RANS jet is not trusted for the verdict and one scale-resolving run is made.
The 9 m tip at 180 degrees, 10 m/s gives 822. The trigger has fired.

## What the check must answer
Whether the plume from a 0.6 m flue at M = 1.7 (17.2 m/s exit into a 10 m/s wind) keeps enough
momentum to clear the intake 13 m downwind, which the realizable k-epsilon closure says it does
not (V2: jets at M >= 3 destroyed within three diameters; at M = 1 the closure was within the
tunnel band). The quantity compared is the flue fraction at the louvres, time-averaged, against
the RANS value of 1.22e-3.

## Options
- A. Detached-eddy simulation (kOmegaSSTDDES) on the existing 2.6 M mesh with the flue-jet box
  refined one level (about 4 M cells), pimpleFoam, time step from a Courant number of 1 in the
  jet (about 5 ms), 60 s of physical time after a 30 s spin-up: roughly 18,000 steps. Cost
  estimate at 10 s per step on 64 cores: 50 hours wall, 3,200 core-hours. The ABL inflow stays
  steady (no synthetic turbulence), which under-represents the approach-flow mixing; the jet
  itself is resolved, which is the point.
- B. The same with synthetic inflow turbulence (turbulentDFSEMInlet). Honest for the whole flow,
  about the same cost, but a new inflow method to validate first.
- C. No check; report the 822 with the caveat and the direction of the likely error (RANS
  over-mixes the jet, so the true dilution at the intake could be higher or lower depending on
  where the plume centreline sits relative to the louvres; V2 at M = 3 showed the RANS plume
  reaching the roof too early).

## Recommendation
A, limited to the single governing case, with the result reported as a band around the RANS
value rather than a replacement for it. B is the better method but doubles the learning cost.
C is acceptable for a portfolio if the reasoning is written out, but the brief's section 7 asks
for the uncertainty to be quantified where it matters, and here it matters.

## What Saleh decides
Option; core count and the 3,200 core-hour budget (rule 12); whether the 60 s averaging window
is enough (checked by comparing the two halves of the window, flat within 5 % or run on).

## Decision (2026-10-15)
Option C. No scale-resolving run. The 180-degree, 9 m result (822) is reported with the caveat
of decision 0013, and the report states the direction of the likely error: the RANS closure
over-mixes the jet (V2), so near the stack the modelled plume is wider and lower than a resolved
one would be, and the dilution at a receptor 13 m away can be either higher or lower than 822
depending on where the true plume centreline sits relative to the louvres. The verdict at that
condition is "fails by 2.4 on the model used, uncertain by at least that factor"; the design
conclusion (move the intake or the flues for the flue-end wind) does not depend on it, since the
3 m and 6 m tips fail by 35 and 18.
