# Rooftop exhaust and heat re-entrainment at a data-centre hall

Technical report, 2026-10-16. Repository: github.com/SalehMohammadrezaei/rooftop-exhaust-cfd.

## 1. Summary

A generic data hall, 60 x 40 x 15 m, carries ten air-cooled chillers in two rows, four
standby-generator flues and one fresh-air intake on its roof. Steady RANS simulations in
OpenFOAM v2606 with one passive scalar per source give, for each wind condition, the fraction of
every receptor's air that came from every source. Two acceptance limits were fixed before the
runs: exhaust dilution at the intake of at least 2,000, and a chiller inlet temperature rise of
at most 2 K mean and 4 K on the worst unit.

The chiller limit fails at every condition by three to six times; the cause is the row layout,
each downwind unit drawing 13 to 17 % of its air from its nearest neighbour. The intake limit
fails whenever the flues are upwind of the intake. Raising the flue tip from 3 to 6 m clears
the limit across the wind (dilution 1,190 to 4,900) but not along the wind from the flue end,
where even 9 m leaves a shortfall of 2.4; that direction needs the intake or the flues moved.
The modelling chain was validated against two wind-tunnel datasets; its one known weakness,
over-mixing of a strong vertical jet, is stated and bounds the last result.

## 2. Question and scope

Which wind directions, speeds and flue heights keep generator exhaust out of the fresh-air
intake and chiller discharge out of the chiller inlets. In scope: external flow around the
isolated hall in a neutral atmospheric boundary layer, dispersion of exhaust with source
momentum, thermal re-ingestion in the passive limit. Out of scope: structural loading, internal
airflow, non-neutral stability, neighbouring buildings, plant screens, buoyancy of the flue
gas, fan and louvre detail.

## 3. Geometry and operating conditions

| element | definition | model |
|---|---|---|
| hall | 60 (x) x 40 (y) x 15 m, flat roof, sharp edges | smooth walls, wall functions |
| parapet | 1.2 m high, 0.5 m thick (decision 0012) | solid ring |
| chillers | 10 units, 2 rows of 5, 12 x 2.4 x 2.5 m, 4.5 m pitch, 3 m between rows, centred at x = -12 m | solid boxes; 90 m3/s drawn through the two long side faces, discharged at 8 m/s through a top strip |
| flues | 4, 0.6 m diameter, 2 m apart, 5 m in from the +x parapet; tip 3, 6 or 9 m above the roof | cylinders, 4.85 m3/s each at 17.2 m/s (momentum-matched to a 2 MW set at 415 C) |
| intake | 6 x 4 x 3 m enclosure at x = +12 m, 3 x 1.5 m louvre on each side face | solid box, 2.5 m3/s drawn through each louvre |

Wind: neutral log-law profile, z0 = 0.3 m, U_H = 10 m/s at roof height (3 m/s at one
direction); directions 0 (along the hall, chillers upwind), 90 and 180 degrees. Flows are from
decision 0010; the chiller values are the brief's indicative figures, consistent with 1.3 MW
rejected at a 12 K air temperature rise.

## 4. Method

Realizable k-epsilon with atmospheric wall functions on the ground, log-law inlet with constant
k and the Hargreaves-Wright dissipation constant, fixed shear stress at the top, slip sides,
fixed-pressure outlet. Domain 500 x 376 x 136 m (8H upwind, 20H downwind, 10H to each side,
9H high; blockage below 2 %). snappyHexMesh from a 4 m background through six refinement levels
to 0.125 m at the chiller discharge and 0.0625 m across the flues, 2.6 million cells. SIMPLE,
second-order upwind convection, 2,000 iterations for the flow; convergence judged on the probe
velocities, the building force and the mass balance being flat within 1 %.

Tagged scalars: twelve passive scalars (one per chiller, one for the flues, one for all sources)
solved on the frozen flow with Sct = 0.4 for 5,000 iterations, each 1 at its source and 0 at
the inlet. The area average of each scalar on each receptor patch gives the matrix F. The
chiller inlet rise follows from (I - F_cc) theta = F_cc dT 1 with dT = 12 K; the intake
dilution is 1 / F(intake, flues). Receptor fractions are accepted when flat within 1 % over the
last 200 iterations and the sum of the tagged scalars matches the all-sources scalar within
1 %.

Every case is generated from `params/` by script, run by one driver, and recorded with its
mesh statistics, iterations, wall time, commit and build. Every number in `results/` is
computed by script from the raw function-object output.

## 5. Validation

| stage | reference | acceptance | result |
|---|---|---|---|
| V0 empty domain | analytical profiles | U, k change < 5 % to the building | met: 2.1 %, 3.7 % |
| V1 isolated building | AIJ Case H wind tunnel | hit rate U >= 0.66; FAC2 >= 0.5, abs(FB) <= 0.3 | 0.60 (not met, grid-independent); FAC2 0.57 met, FB -0.56 not met |
| V2 rooftop stack | IRSST R-848 wind tunnel | ranking correct; FAC2 >= 0.5 | M = 1 met (FAC2 1.0, 0.8); M = 3 not met (FAC2 0) |
| V2b full scale | V2 at 1:200 | within 18 % | met: 3 % |

V1 selected the closure, the mesh rule and Sct. V2 identified the model-form limit: at
momentum ratios of 3 and above the closure mixes the jet out within three stack diameters.
Finer meshes, k-omega SST and the SSG Reynolds-stress closure did not change it. V2b showed
Reynolds-number independence from Re 31,000 to 6 million and quantified the inflow effect: the
applied ABL gives about 40 % less roof dilution than the tunnel inflow, so the applied results
err towards higher concentrations.

## 6. Results

| wind | U_H | flue tip | intake dilution | chiller rise mean / worst | balance | amplitude |
|---|---|---|---|---|---|---|
| 0 deg | 10 m/s | 3 m | 9.6e7 | 6.00 / 8.08 K | 0.38 % | 0.00 % |
| 90 deg | 10 m/s | 3 m | 1,190 | 5.86 / 9.25 K | 0.51 % | 0.00 % |
| 90 deg | 10 m/s | 6 m | 4,900 | 5.86 / 9.25 K | 0.51 % | 0.00 % |
| 90 deg | 10 m/s | 9 m | 21,900 | 5.86 / 9.25 K | 0.51 % | 0.00 % |
| 90 deg | 3 m/s | 3 m | 9,580 | 7.34 / 12.96 K | 0.27 % | 1.60 % |
| 180 deg | 10 m/s | 3 m | 58 | 6.14 / 8.31 K | 0.23 % | 0.01 % |
| 180 deg | 10 m/s | 6 m | 112 | 6.51 / 8.81 K | 0.25 % | 0.00 % |
| 180 deg | 10 m/s | 9 m | 822 | 6.77 / 9.19 K | 0.27 % | 0.00 % |

Chillers. The worst unit is a downwind unit of each row at every condition (unit 4 or 9 along
the hall, unit 2 or 3 across it); the upwind unit of each row sits at 2.3 K. The low-wind case
is the worst, 13 K on unit 2. About 28 % of the intake's air is chiller discharge at 0 degrees,
which does not matter for the limits but shows how far the plant-deck air travels.

Intake. At 0 degrees the flues are downwind of the intake and nothing arrives. At 90 degrees
the 3 m tip is a near miss and each 3 m of height buys a factor of four to five. At 180 degrees
the flues stand 13 m straight upwind of the louvres; each 3 m buys two to seven and 9 m still
fails.

Grid band (decision 0015, 180 degrees, 1.05 / 2.60 / 6.70 million cells): chiller rise 6.17 /
6.14 / 6.16 K mean, 8.42 / 8.31 / 8.29 K worst, grid-independent; intake dilution 56.7 / 58.1 /
59.9, a 3 % band without a measurable convergence order.

Hand check (ASHRAE minimum-dilution method, Wilson and Lamb): 19 to 30 at the worst direction
for the 3 m tip against 58 from the CFD, the relation expected of a lower bound. The hand
method carries no plume-rise credit and stays near 25 for the taller tips where the CFD
climbs to 822.

## 7. Uncertainty

| source | size | effect on the verdicts |
|---|---|---|
| grid | 0.3 % on chiller rise, 3 % on dilution | none |
| tracer convergence | below 0.01 %, 1.6 % at 3 m/s | none |
| inflow (V2b) | about 40 % on roof dilution, conservative direction | none |
| model form, jet (V2) | factor 3 or more on dilution near a strong jet | the 180 deg, 9 m result (822 against 2,000) cannot be settled by this closure; carried as uncertain by at least its own margin (decision 0014) |
| inputs | chiller and flue flows indicative from the brief | chiller rise scales with the 12 K discharge rise; dilution scales with flue flow |

## 8. Conclusions

1. The chiller arrangement fails the inlet-rise limit under every wind. The fix is spacing,
   taller discharge or ducted inlets, and the matrix says which units to treat first.
2. A 6 m flue tip meets the air-quality limit for every direction except the one with the
   flues straight upwind of the intake; for that direction the intake or the flues move.
3. The closure is adequate for the chiller problem and for the intake at moderate momentum
   ratio; its jet over-mixing bounds the one near-limit result, and a scale-resolving check
   would be the next step if that result had to carry a design.

## 9. Not done

Oblique wind directions (the mesh fails a skewness check at two chiller corners at 30 to 150
degrees); the plant-screen variant; the buoyant check; the scale-resolving jet check.

## 10. References

AIJ UWE Benchmark Case H, Zenodo 15429872 (CC BY 4.0). Stathopoulos, Hajra, Chavez, Bahloul,
IRSST report R-848 (2014). Hargreaves and Wright (2007), J. Wind Eng. Ind. Aerodyn. 95.
Richards and Hoxey (1993), J. Wind Eng. Ind. Aerodyn. 46-47. Celik et al. (2008), J. Fluids
Eng. 130. VDI 3783 Part 9 (2017). COST Action 732 (2007). Petersen and Ritter, ASHRAE RP-1635
(2016). The Air Quality Standards Regulations 2010.
