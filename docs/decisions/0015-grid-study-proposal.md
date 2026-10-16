# 0015 Grid study of the applied case (proposed 2026-10-14; approved 2026-10-15 as proposed: 180 deg, 10 m/s, D0, ratio 1.41)

## Purpose
Every applied number is quoted without a grid band. Project.md section 7 asks for one; the
reduced matrix (R4) reserved two extra meshes at the governing condition for it.

## Proposal
Governing condition: 180 degrees, 10 m/s, D0 (intake dilution 58, chiller rise 6.1 / 8.3 K).
Three meshes at a refinement ratio of 1.41 in every direction, obtained by scaling the
background cell and keeping every refinement level and box unchanged, so the level ladder is
the same and only the absolute cell size moves:

| mesh | background cell | finest cell (flue pipes, L6) | cells (estimate) | cost (estimate) |
|---|---|---|---|---|
| coarse | 5.66 m | 0.088 m | 0.95 M | 0.4 of base |
| base | 4.0 m | 0.0625 m | 2.6 M | 1 (12 h on 32 cores, 380 core-hours) |
| fine | 2.83 m | 0.044 m | 7.3 M | 2.8 of base, 64 cores |

The GCI (Celik et al. 2008, as in validation/V1/gci.py) is computed on the two primary
quantities and on the flue fraction at the louvres. Expected: the chiller rise is grid-insensitive
(V1 drag and cavity velocity gave GCI of 0.1 to 2 %); the intake dilution is the sensitive one
because the flue plume is one cell wide at the exit.

## Alternative
Refine only the plant-deck and flue boxes (levels 4 to 6) and leave the background: cheaper, but
it changes the level ladder between meshes and the GCI assumption of uniform refinement does not
hold. Not recommended.

## What Saleh decides
The condition (180 degrees as proposed, or 90 where the 3 m tip was a near miss), the ratio
(1.41 or 1.26 for a cheaper fine mesh at 5.2 M cells), and the budget (about 1,300 core-hours
for the two extra meshes).

## Result (2026-10-16)

| quantity | coarse 1.05 M | base 2.60 M | fine 6.70 M | band quoted |
|---|---|---|---|---|
| intake dilution | 56.7 | 58.1 | 59.9 | 3 % (fine-base change; order not measurable) |
| chiller rise, mean | 6.17 K | 6.14 K | 6.16 K | 0.3 % |
| chiller rise, worst unit | 8.42 K | 8.31 K | 8.29 K | 0.1 % (GCI, p = 5.3) |

The chiller numbers are grid-independent at the base mesh. The intake dilution moves 3 % from
base to fine and 2.5 % from coarse to base, the same size, so no convergence order can be
fitted; the 3 % is reported as the grid band on dilution. It is far smaller than the model-form
uncertainty on the jet (decision 0013) and does not affect any verdict. Full table in
results/applied/gci_D0_dir180_U10.md. Cost: coarse 7.1 h on 32 cores, fine 21 h on 64.
