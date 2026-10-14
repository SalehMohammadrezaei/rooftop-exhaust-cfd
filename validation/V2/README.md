# V2: rooftop stack, IRSST R-848

**Question.** Does the closure carry a stack plume along a roof with the right dilution, for a
stack height and an exhaust speed that bracket the applied flues?

**Reference.** IRSST report R-848 (Stathopoulos, Hajra, Chavez, Bahloul, 2014), Configuration 1:
an isolated low building at 1:200 with a stack of 3 mm diameter, roof receptors 5 to 50 m
downwind at full scale, stack heights 1 and 3 m and momentum ratios M = 1 and 3. Curves
digitised from the report's figures with overlays and cross-checks under
`data/digitised/irsst_r848`; the report is CC BY-NC-ND and not included.

**Setup.** Model scale, measured tunnel inflow (22 % turbulence intensity), stack centred 1 mm
inside the roof edge (decision 0007), 10 cells across the stack exit, realizable k-ε, Sct 0.4 and
0.7. Sensitivities: k-ω SST, a jet-resolved mesh (1.41 M cells), SSG and LRR Reynolds-stress
closures.

**Acceptance.** Correct ranking of the stack heights; FAC2 ≥ 0.5 at the roof receptors.

**Answer.** Met at M = 1 (FAC2 1.0 and 0.8, ranking 10/10), not met at M = 3 (FAC2 0, dilution
five times too low). The closure destroys the M = 3 jet within three stack diameters: the
turbulent kinetic energy in the shear layer reaches 23 m²/s² and the eddy viscosity is 2000 times
the molecular value. Finer mesh, SST and SSG did not change it; LRR diverged. Carried as a model
limit (decision 0008) and into the applied study's flue caveat (0013).

![dilution](../../results/V2/figures/v2_dilution.png)

**Files.** `case_by_hand/` (template), `case_hs1_M1`, `case_hs1_M3`, `case_hs3_M1`,
`case_hs3_M3` and the sensitivity cases; `digitise_r848.py`, `digitise_profile.py`,
`make_inlet_profiles.py`, `metrics.py`, `run_rsm.sh`; results in `results/V2/`.
