# Digitised data from IRSST report R-848 (Stathopoulos, Hajra, Chavez, Bahloul 2014)

Derived values read from the report's figures by script; the report itself (CC BY-NC-ND 4.0) is
not redistributed. Cite the report for any use. Scripts: validation/V2/digitise_r848.py (dilution
charts) and validation/V2/digitise_profile.py (approach-flow profiles). Each CSV's first line
records the page image, crop, pixel calibration and colour used; each *_overlay.png shows the
extracted points as red crosses on the figure for visual checking (checked 2026-10-12).

## Files

| File | Figure | Case | Points | Notes |
|---|---|---|---|---|
| fig5_1_isolated_hs1_M3_Xs0.csv | 5.1 (pdf p41) | isolated building, hs = 1 m, M = 3, stack at upwind edge | 10, x = 5..50 m | PRIMARY for this case; markers located individually |
| fig4_4b_isolated_hs1_M3_Xs0.csv | 4.4b (pdf p39) | same case | 10 | cross-check only (line tracked) |
| fig4_4a_isolated_hs1_M1_Xs0.csv | 4.4a (pdf p39) | isolated, hs = 1 m, M = 1, Xs = 0 | 10 | line tracked, read at 5 m spacing |
| figD2a_isolated_hs3_M1_Xs0.csv | D2a (pdf p71) | isolated, hs = 3 m, M = 1, Xs = 0 | 10 | line tracked |
| figD2b_isolated_hs3_M3_Xs0.csv | D2b (pdf p71) | isolated, hs = 3 m, M = 3, Xs = 0 | 10 | line tracked |
| fig3_1a_measured_UoverUg.csv | 3.1 left (pdf p26) | approach flow, V/Vg against z (cm) | 19 | markers overlap below 15 cm: those rows are blob centroids (blob size column) |
| fig3_1b_measured_TI.csv | 3.1 right (pdf p26) | approach flow, turbulence intensity % against z (cm) | 20 | same |
| crosschecks.txt | | | | the checks below |

Quantities: normalised dilution D_N = D_r Q / (U_H H^2) with D_r = C_e / C_r (report eq. A.13),
x = receptor distance from the stack along the roof centreline, full-scale metres. Profiles: z in
cm at model scale (1:200), V/Vg with Vg = 14.2 m/s at zg = 95 cm, TI in percent.

## How the charts were read
Dilution charts: the plot frame gives the axis ranges (x 0 to 50 m; y 0.001 to 1000, log, six
decades); the chart's own horizontal axis line at y = 1 was used as a calibration check and lands
at 1.00 in every crop. Figure 5.1 has one navy series, so each diamond was located individually.
Figures 4.4 and D2 contain other series in the same navy colour (dotted lines, smaller markers),
so the solid Configuration 1 line was tracked across the frame: only runs of the solid line's thickness
(5 to 8 px) are followed, a thicker run is accepted only when centred on the line (its own marker),
and at each ambiguity the run that continues as a solid line is preferred. Values are read at the
receptor spacing of 5 m. Zoomed crops were inspected where series cross (D2b at 30 m).
Profiles: x calibrated from the tick marks (zero tick at the vertical axis), y from the x-axis line
and the top of the vertical axis; the connecting line removed by a morphological opening; each
marker a blob centroid.

## Checks and uncertainty
- Same case from two figures (hs = 1 m, M = 3): Figure 5.1 against Figure 4.4b agree within the
  value in crosschecks.txt over 5 to 45 m. That is the digitising uncertainty for the dilution
  curves, on top of the tunnel repeatability of 15 percent quoted in the report.
- Velocity profile against the power law (z/95)^0.31 quoted on the chart: see crosschecks.txt.
- Stack-height ranking in the data: at every receptor the 3 m stack gives higher dilution than
  the 1 m stack for the same M, and M = 3 higher than M = 1 for the same height.

## Caveats found in the report
- The report text says ESDU 1974 velocities are about 1.2 times higher than the tunnel data
  between 10 and 60 cm; in Figure 3.1 the curve labelled Measured lies above the ESDU curve in
  that range and follows the quoted power law. The legend was taken as correct (Measured = navy
  diamonds, consistent with Table 3.1's measured exponent 0.31); the inconsistency is noted.
- No isolated-building curve for hs = 5 m was found in the figures, although hs = 5 m is in the
  test matrix. The ranking test uses hs = 1 and 3 m.
- The ASHRAE curves were not digitised; ASHRAE 2011 can be computed from Appendix A if needed.
