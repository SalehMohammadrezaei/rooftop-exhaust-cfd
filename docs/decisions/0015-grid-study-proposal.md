# 0015 Grid study of the applied case (proposal, drafted under autopilot 2026-10-14, for Saleh's decision)

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
