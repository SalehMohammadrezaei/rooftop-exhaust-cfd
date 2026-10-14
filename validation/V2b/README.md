# V2b: the stack cases at full scale

**Question.** The tunnel is at 1:200 and the applied case is at full scale with a different
inflow. Does the dilution the model gives change with scale alone, and how much does the inflow
change it?

**Setup.** The two M = 1 cases of V2 (the ones the model represents) rebuilt 200 times larger
by `make_cases.py`, run twice: with the tunnel inflow scaled up (scale alone) and with the
applied ABL (z0 = 0.3 m, 15 % intensity at roof height, rough ground, fixed shear at the top).
Base mesh rule, 2500 iterations, Sct 0.4.

**Acceptance.** Dimensionless dilution within the V2 uncertainty band of the model-scale result
(tunnel repeatability 15 % plus digitising 2.6 %, taken as 18 %).

**Answer.** Met. Scale alone changes the dilution by 3 % (geometric mean ratio 1.03 and 1.02,
every receptor within 18 %); Reynolds-number independence holds for this sharp-edged geometry from
Re 31,000 to 6 million. The inflow is the larger effect: the applied ABL gives about 40 % less
roof dilution than the tunnel inflow, so the applied results are conservative in the direction
of higher concentrations. Carried as the inflow part of the uncertainty band.

**Files.** `make_cases.py`, `run_all.sh`, `run_tunnelinflow.sh`; cases are generated under
`~/scratch/openfoam_cases/V2b`; results in `results/V2b/`.
