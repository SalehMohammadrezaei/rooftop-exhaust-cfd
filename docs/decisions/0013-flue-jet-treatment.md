# 0013 How the flue jets are treated in the applied matrix (decided 2026-10-13)

## Background
V2 (decision 0008) showed that the realizable k-epsilon closure mixes a vertical stack jet out
within about three stack diameters at momentum ratios of 3 and above, where the IRSST wind-tunnel
data show the plume surviving further. Finer meshes and other eddy-viscosity closures (k-omega SST)
and the SSG Reynolds-stress closure did not change this; LRR crashed. The applied flues run at
momentum ratios of 1.7 to 5.7, so the intake dilution of flue exhaust carries this model-form
uncertainty. The chiller discharge (8 m/s into 3 to 10 m/s wind, M below 3) is in the regime V2
validated, so the chiller rise is not affected.

## Options considered
- A. Accept the closure as validated, finish the matrix, declare the over-mixing in every report of
  the intake dilution. No extra cost.
- B. After the matrix, run the governing condition (90 degrees, 10 m/s, and the D1/D2 tips) with a
  scale-resolving model and compare. Expensive; a new simulation type.
- C. Replace the flue by an effective taller stack from a plume-rise correlation. Cheap; a hand
  correction needing its own justification.

## Decision
A now. B is taken up only if the intake dilution at the governing condition, or at the taller flue
variants D1/D2, lands within a factor of 3 of the limit of 2000 (that is, between about 700 and
6,000), because then the over-mixing could change the verdict. Outside that band the verdict is
robust to the uncertainty and the extra run is not made. This trigger is fixed now so the choice
is not made after seeing which answer is convenient. C is not used.

## Consequences
- Every intake-dilution number in results and the final report carries the note "RANS jet,
  over-mixed at M >= 3 (V2); dilution uncertain in the direction of too much dilution near the
  stack and too little far from it".
- results/applied/summary.md gains that note in its header.
