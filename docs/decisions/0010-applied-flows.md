# 0010 Applied case: the fixed flows at the openings

Date: 2026-10-12. Numbers researched by Claude at Saleh's request; each labelled by kind (CLAUDE.md
rule 7). To be confirmed by Saleh when he writes the U file.

| Opening | Value | Kind and source |
|---|---|---|
| Chiller intake, each unit, both side faces together | 90 m3/s drawn out of the domain | derived: 1.3 MW rejected at a 12 K air temperature rise, m = Q/(cp dT) = 1.3e6/(1005 x 12) = 108 kg/s = 90 m3/s at 1.2 kg/m3; the brief's indicative values, consistent with each other. A manufacturer airflow figure was sought (Carrier 30XA, Systemair SYSCREW) but no datasheet with airflow was retrievable; remains indicative |
| Chiller discharge, each unit, top strip | 90 m3/s into the domain through 11.2 m2, i.e. 8 m/s | derived, same source; strip sized as flow / speed |
| Generator flue exit, each | hot exhaust 7.38 m3/s at 415 C: Kohler KD2000, 2000 kW standby rating, "exhaust flow at rated kW 443 m3/min, exhaust temperature 415 C" | measured (datasheet, Kohler G5626) |
| Flue exit velocity, hot | 7.38 / (pi 0.3^2) = 26.1 m/s through the 0.6 m flue | derived |
| Flue exit in the isothermal model | 17.2 m/s, i.e. 4.86 m3/s per flue, 19.4 m3/s on the flue_exit patch (four flues) | derived: momentum-flux matching, Ve_iso = Ve_hot sqrt(rho_hot/rho_amb) with rho ratio 298/688 = 0.433 (R-848 eq. 3.1; Project.md section 3 "isothermal in the MVP with the momentum ratio matched") |
| Momentum ratio M of the flues | 1.7 at U_H = 10 m/s, 5.7 at 3 m/s | derived; note V2 showed the closure does not credit M above about 1 |
| Fresh-air intake, both louvres together | 10 m3/s drawn out of the domain, 5 per louvre, face velocity 1.1 m/s over 4.5 m2 | assumption: one air change per hour of the 36,000 m3 hall for pressurisation and occupancy; data halls need little outdoor air (sensible load only, no CO2 source); sensitivity band 5 to 20 m3/s to be run; to be replaced by a cited design figure |

Boundary condition: flowRateInletVelocity with volumetricFlowRate, positive into the domain for
sources, negative for sinks; the velocity is normal to the patch and uniform over it, so the flow
is exact whatever the meshed patch area.
