# 0012 The parapet gets a thickness (decided 2026-10-13)

## Problem
The parapet was a zero-thickness sheet on the roof perimeter, meshed as a snappyHexMesh baffle
(faceZone + faceType baffle, giving the patches parapet and parapet_slave). With the building
rotated to 30, 60, 120 or 150 degrees the sheet crosses the background grid at a shallow angle and
two faces at one parapet corner come out at skewness 4.5 against the checkMesh limit of 4. The
pipeline stops on a failed mesh check (rule: no solver on a failed mesh), so four of the seven
directions in block A have no result. Retries with more snapping iterations and a finer parapet
level were queued but had not succeeded when this decision was taken.

## Options considered
- A. Keep the sheet, keep tuning snap settings. No geometry change; may fail again.
- B. Give the parapet a thickness so it is a closed solid ring like every other roof object.
  Removes the baffle machinery entirely. Real parapets have thickness (0.2 to 0.5 m).

## Decision
B. Thickness 0.5 m, measured inward from the roof edge, height 1.2 m unchanged. Kind: model
assumption (the brief gives no parapet thickness). 0.5 m is chosen so that the wall is two cells
thick at the parapet refinement level 4 (cell 0.25 m); a thinner wall of one cell would recreate
the thin-sheet problem in a different form.

## Consequences
- geometry/make_hall.py builds the parapet as a ring (outer walls, inner walls, top), normals
  outward; params/hall_geometry.json gains "thickness": 0.5.
- snappyHexMeshDict: parapet is a normal wall surface, level (4 4), no faceZone / faceType baffle.
- 0.orig: the patch parapet_slave no longer exists; it is removed from the wall regex.
- The 0-degree 10 m/s case is re-run on the new geometry and compared with the sheet result
  (chiller rise mean 5.95 K, worst 8.03 K, intake dilution 7.6e7). The change is accepted as
  small if both chiller numbers move by less than 0.3 K; if they move more, the difference is
  reported as a model-form effect of the parapet, not hidden.
- All block A directions are regenerated from the parameter file and re-run; the sheet results
  are kept in the record as the first pass.

## Check (2026-10-14, 0 degrees 10 m/s, 5,000 tracer iterations on both geometries)

| quantity | sheet parapet | solid 0.5 m parapet | change |
|---|---|---|---|
| chiller rise, mean | 5.95 K | 6.00 K | +0.05 K |
| chiller rise, worst unit (4 and 9) | 8.03 K | 8.08 K | +0.06 K |
| chiller air at the louvres | 27.6 % | 27.8 % | +0.2 points |
| flue dilution at the intake | 7.6e7 | 9.6e7 | both far above 2000 |

Both chiller numbers move by less than the 0.3 K agreed above: the change is accepted as small,
and the solid parapet is the geometry of record for every applied result from here on.
