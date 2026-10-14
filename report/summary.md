# Rooftop exhaust re-entrainment at a data hall: one-page summary

Draft of 2026-10-14. Numbers are from `results/applied/summary.md`; the study is in progress
(flue tips at 90 degrees running, grid study and jet check pending).

## Question
For a 60 x 40 x 15 m data hall with ten rooftop chillers, four generator flues and one fresh-air
intake, which wind conditions put chiller discharge back into the chiller inlets and generator
exhaust into the intake, and does raising the flues fix the second.

## Limits, fixed before the runs
Exhaust dilution at the intake at least 2,000 (200 ppm NO2 in the flue against the 0.1 ppm UK
hourly limit). Chiller inlet temperature rise at most 2 K on average and 4 K on the worst unit
(about 3 and 5 % of capacity at 1.3 %/K).

## Method
Steady RANS (realizable k-epsilon, atmospheric wall functions), neutral log-law boundary layer
with z0 = 0.3 m, 2.6 million cells, one passive scalar per source carried on the converged flow.
The scalars give the fraction of each receptor's air that came from each source; chiller rise
and intake dilution follow from that matrix. Validated on an empty domain, the AIJ Case H
building and the IRSST rooftop stack before use; the closure's known weakness is that it
over-mixes a vertical jet at momentum ratios above 3.

## Results

| wind | speed | flue tip | intake dilution | chiller rise mean / worst |
|---|---|---|---|---|
| 0 deg | 10 m/s | 3 m | 9.6e7 | 6.0 / 8.1 K |
| 90 deg | 10 m/s | 3 m | 1,190 | 5.9 / 9.3 K |
| 90 deg | 3 m/s | 3 m | 9,580 | 7.3 / 13.0 K |
| 180 deg | 10 m/s | 3 m | 58 | 6.1 / 8.3 K |
| 180 deg | 10 m/s | 6 m | 112 | 6.5 / 8.8 K |
| 180 deg | 10 m/s | 9 m | 822 | 6.8 / 9.2 K |

## Findings
1. The chiller limit fails at every condition by three to six times. The matrix shows each
   downwind unit taking 13 to 17 % of its intake air from the single nearest neighbour alone,
   40 % from all chillers together; the upwind unit of each row is the only one near the limit. This is the row layout, not the wind, and the fix is spacing,
   taller discharge or ducted intakes.
2. The intake limit fails whenever the flues are upwind of it. At 180 degrees the 3 m tip misses
   by a factor of 35; 6 m by 18; 9 m by 2.4. Flue height alone does not reach the limit at this
   layout with the flues 13 m from the intake.
3. The 9 m result sits in the band where the RANS jet cannot decide the verdict; a
   scale-resolving check is proposed (decision 0014).

## Not covered
Oblique wind directions (mesh quality at the chiller corners), a plant screen, buoyancy of the
flue gas, neighbouring buildings.
