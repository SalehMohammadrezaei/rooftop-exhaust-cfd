# Hand check: ASHRAE minimum-dilution method against the CFD

U_H = 10 m/s, V_e = 17.2 m/s (Q = 4.85 m3/s per flue, d = 0.6 m), M = 1.72. Stretched-string distance S from the nearest flue tip to the nearest louvre point; four flues combined by adding concentrations.

| flue tip | S [m] | D_min Wilson & Chiu 1994 | D_min ASHRAE 1997 | D_min Wilson & Lamb 1994 | CFD 180 deg | CFD 90 deg |
|---|---|---|---|---|---|---|
| 3 m (D0) | 11.6 | 19 | 26 | 23 | 58 | 1185 |
| 6 m (D1) | 12.1 | 20 | 28 | 24 | 112 | 4901 |
| 9 m (D2) | 13.4 | 22 | 30 | 26 | 822 | 21909 |

Briggs momentum rise used by the ASHRAE geometric method: h_r = 3 d_e V_e / U_H = 3.1 m, so the plume centreline passes 3.8 m above the louvre top with the 3 m tip. Kind: empirical (ASHRAE Handbook HVAC Applications, Building Air Intake and Exhaust Design chapter; Briggs 1984), quoted from secondary sources, not from the chapter text.

Reading: the hand method is a lower bound for the worst direction and carries no stack-height credit beyond S, so it should sit below the CFD at 180 deg and should not follow the CFD's gain with flue height. Where the CFD at 180 deg lies below the hand lower bound, the CFD is the more conservative of the two; where it lies far above, the RANS plume rise is doing what the hand method cannot.
