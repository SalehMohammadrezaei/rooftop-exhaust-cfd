# Teaser storyboard, version 3 (about 40 s, 1920 × 1080, dark stage)

The story runs in five chapters (layout, design checks, method, results, close), one idea per scene, each scene with a kicker word and one short
line. The engineering question comes before the method, the method before the result, and the film
ends on the method keywords and the contacts. Captions are technical labels, not slogans.

| # | chapter | time | scene | on screen |
|---|---|---|---|---|
| 1 | hook | 0–3 s | Flow streaks race over the roof past the lens; the plumes rise; pull back to the hall. | OPENFOAM · EXTERNAL CFD · Rooftop exhaust re-entrainment |
| 2 | problem | 3–6 s | Clean roof on a slow orbit; the three kinds of plant labelled. | LAYOUT · Roof plant |
| 3 | question | 6–10 s | Two arrows draw themselves: warm discharge curling back into the next chiller, exhaust arcing from the flues to the intake. | DESIGN CHECKS · 1 chiller discharge recirculation · 2 exhaust ingestion at the fresh-air intake |
| 4 | method | 10–14 s | Building fixed with its dimensions drawn on the ground; the wind arrow swings 0° → 90° → 180° and the plume follows. | LOAD CASES · wind 0°, 90°, 180°, U = 10 m/s at roof height |
| 5 | method | 14–16.2 s | Snapped surface mesh on hall and plant. | MESH · snappyHexMesh, 2.6 M cells, 95 % hex |
| 6 | method | 16.2–18.5 s | Vertical cut wipes across a chiller row, cells finest at the plant. | MESH · 6 refinement levels, 4 m to 0.06 m |
| 7 | method | 18.5–21.5 s | Arrow rake builds the inflow profile; roof height marked. | BOUNDARY CONDITIONS · neutral ABL inlet, log law, z0 = 0.3 m |
| 8 | method | 21.5–26.5 s | Streaks over a velocity plane, then the plane turns to turbulent kinetic energy. | TURBULENCE MODEL · steady RANS, realizable k-ε; turbulent kinetic energy |
| 9 | method | 26.5–30 s | Ten chiller plumes switch on one by one, then the flue. | SCALAR TRANSPORT · passive scalar per source, Sct = 0.4 |
| 10 | result | 30–33.2 s | Close on the chillers, each tinted by its inlet temperature rise, numbers above. | RESULT · chiller inlet temperature rise, mean 6.0 K, criterion 2 K |
| 11 | result | 33.2–36.4 s | Wind from the flue side: the exhaust plume wraps the intake, which turns red. | RESULT · exhaust dilution at the intake, 58, criterion 2,000 |
| 12 | close | 36.4–40.2 s | Scene dims under the method keywords and the contacts. | turbulence · inflow · grid · validation · transport · LinkedIn · GitHub |

Every number on screen is quoted from `results/` or the case logs.
