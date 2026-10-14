# V1: isolated building, AIJ Case H

**Question.** Does the closure reproduce the separation on the roof and the wake behind a sharp-
edged building, and the spread of a ground-level tracer behind it, well enough for a roof-plant
study?

**Reference.** AIJ UWE Benchmark Case H: a 1:1:2 building (H = 0.2 m) in a wind tunnel,
U_H = 3.23 m/s, velocity and k at 876 points, tracer at 490 points. CC BY 4.0, Zenodo 15429872,
under `data/raw/aij_caseH`.

**Setup.** Measured inlet profile imposed by table (decision 0003); realizable k-ε, k-ω SST and
a log-law inlet as sensitivities; three grids at ratio 1.41 (coarse, medium, fine); Sct scan
0.4 to 0.9 for the tracer (0004); a rough-floor variant (0005).

**Acceptance.** Hit rate on U ≥ 0.66 (VDI 3783/9: 25 % or 0.05 U_H); tracer FAC2 ≥ 0.5 and
|FB| ≤ 0.3 (COST 732).

**Answer.** Not met on velocity, met on FAC2, not met on FB. Hit rate 0.60 (medium), 0.61
(fine), 0.62 (SST), 0.63 (log-law inlet). The misses are all in the wake below roof height,
where the eddy-viscosity closures recover the flow about 0.5 m/s too slowly; grid refinement does
not move it, so it is model form, not resolution. The tracer: FAC2 0.57 at Sct 0.4, the CFD
over-predicts near the ground (FB −0.56). Carried forward (decision 0006): realizable k-ε, the
medium-grid rule, Sct 0.4, and the wake deficit stated as a known limit.

![velocity](../../results/V1/figures/v1_velocity.png)

**Files.** `case_by_hand/` (the template, built by hand and explained in the notebook, Part C),
`case_medium`, `case_fine`, variants; `metrics.py`, `tracer_report.py`, `gci.py`,
`make_inlet_profiles.py`, `make_sample_points.py`; results in `results/V1/`.
