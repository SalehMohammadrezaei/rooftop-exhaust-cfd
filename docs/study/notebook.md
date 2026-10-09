# Study notebook: OpenFOAM and the rooftop re-entrainment project

Written for Saleh to read later, without the chat. Part A is the map and the story so far; read it
first, every time. Part B holds the entries, each tagged with the step of the story it belongs to.

---

# Part A. The map and where we are

## The project in one line
Which flue height and plant screen keep generator exhaust out of the fresh-air intake and hot
chiller air out of the chillers, for all wind directions, on a generic data hall?

## The road, from Project.md section 5 and 8 (you are at the bold step)

| Step | What it proves | Status |
|---|---|---|
| Smoke test | The ABL tools in OpenFOAM v2606 run and we understand them | done 2026-10-08 |
| V0 empty domain | The wind profile survives the trip from inlet to the building position | done 2026-10-08, decision 0002 |
| **V1 AIJ Case H** | **Separation, wake, scalar transport around a cube, against wind-tunnel data** | **next** |
| V2 Concordia stack | Roof-level dilution versus stack height, the applied design variable | not started |
| V2b | V2 at full scale with our ABL setup | not started |
| Applied blocks A to F | The actual design question on the data hall | not started |
| V3, V4, LES, blocks D to G | Finished-version extras | not started |

## The story so far (updated as we go)

1. We needed a wind that stays the same in an empty box. OpenFOAM has ready-made inlet conditions
   for that, so we first ran an official tutorial unchanged to see them work (entry 2) and learned how
   any OpenFOAM case is organised and run (entry 3) and how to read its log (entry 4).
2. Then we built V0, the same test on our own domain with our own numbers. To set it up we had to
   understand three things, in this order:
   - what the inlet sends in: the log-law wind and its turbulence (entries 5 and 6),
   - what the ground must do to agree with that inlet: the rough-wall function and how close to the
     ground the first cell may be (entries 7 and 8),
   - why the turbulence dissipation needs its own ground treatment (entry 9).
3. V0 was run 24 times (3 turbulence models, 2 ground treatments, 2 top conditions, 2 meshes).
   Result: the velocity profile holds everywhere; the turbulent kinetic energy k only holds when the
   ground treatment uses z0 consistently and the first cell is 1 m, not 4 m. Entries 7 and 9 contain
   the numbers.
4. Then the near-building question: are cells smaller than z0 acceptable? Mesh C (first cell 0.5 m,
   centre below z0) says yes, provided the z0-consistent wall set is used; it is in fact the best of
   the three meshes (entry 10).
5. V0 closed (decision 0002): ground = atm wall set with first cell at or below 1 m; top = fixed
   shear stress; realizable k-epsilon and SST both go on to V1 and V2, where the baseline is chosen.
6. Next: V1, the AIJ Case H cube in a wind tunnel, where a building appears for the first time and
   the results are compared with measured data. New things to learn there: snappyHexMesh, smooth
   walls (y+ rules return), a passive scalar, and validation metrics (hit rate, FAC2).

## How V0 is built (the files you would touch yourself)

```
params/V0_empty_domain.json     every input with its kind; the variant table is the experiment design
templates/V0/                   OpenFOAM dictionaries with @placeholders
workflow/make_case.py           fills the templates, computes u*, tau, grading, writes case_record.json
workflow/run_case.sh            blockMesh, checkMesh, simpleFoam, yPlus, run_record.json
validation/V0/metrics.py        the acceptance numbers from raw sample files
results/V0/summary.md           the table
docs/decisions/0002-v0-setup.md every setup choice and its reason
```
Generated cases live outside the repository in ~/scratch/openfoam_cases/V0/<closure>_<wallset>_<top>_<mesh>/.

---

# Part B. Entries

## 1. What the project is, in one paragraph (2026-10-08) (story step 0)

Wind blows over a data hall with chillers and generator flues on the roof. We want to know which flue
height and screen keep the exhaust out of the fresh-air intake and the hot air out of the chillers.
Before any building is simulated, we must prove the simulated wind itself is right: a neutral
atmospheric boundary layer (ABL) that enters the domain and stays the same until it reaches the
building. That proof is called V0 in Project.md. Everything after V0 stands on it.

## 2. What a smoke test is (2026-10-08) (story step 1)

A smoke test asks "does the machinery run and do I understand it", not "is the answer right". We ran
an official OpenFOAM v2606 tutorial (atmDownstreamDevelopment) unchanged: an empty 5 km box with an
ABL inlet, rough ground and a shear stress on the top. It reproduces Hargreaves & Wright (2007), who
showed that without three fixes the profile decays along an empty box:
1. a ground wall function that knows the roughness length z0,
2. the k-epsilon constant sigmaEps changed from 1.3 to 1.11,
3. a fixed shear stress u*^2 on the top boundary.
Result of our run: velocity held to 2.4 %, k to 2.2 % over 4 km with standard k-epsilon. The run was
converged by iteration 1000 of the tutorial's fixed 5000. Record: results/smoke/.

## 3. Anatomy of every OpenFOAM case (2026-10-08) (story step 1)

```
0/          initial and boundary conditions, one file per field: U, p, k, epsilon (or omega), nut
constant/   what the problem is: polyMesh/ (the mesh), transportProperties (nu),
            turbulenceProperties (which RANS model, which constants)
system/     how to solve it: controlDict (iterations, output, function objects = monitors),
            fvSchemes (discretisation), fvSolution (linear solvers, SIMPLE settings, relaxation,
            residualControl), blockMeshDict (the mesh definition), decomposeParDict (parallel split)
```
Written results go into numbered time directories (for a steady run the "time" is the iteration).
`0.orig/` is the pristine copy of `0/`; the run script restores it so a rerun never starts dirty.
`postProcessing/` holds function-object output. `log.<utility>` is each program's screen output.

Run sequence, always the same, and what Allrun scripts spell out:
```
blockMesh                          mesh from system/blockMeshDict
checkMesh                          quality report (look for "Mesh OK" and *** lines)
decomposePar                       split for N cores (optional)
simpleFoam                         steady incompressible RANS solver (mpirun -np N ... -parallel)
reconstructPar                     merge the cores (optional)
simpleFoam -postProcess -func X    run a function object on saved fields, e.g. yPlus
```

## 4. Reading the solver log: residuals (2026-10-08) (story step 1, used again in step 3)

One iteration block looks like:
```
smoothSolver:  Solving for Ux, Initial residual = 2.96e-09, Final residual = 2.96e-09, No Iterations 0
GAMG:          Solving for p,  Initial residual = 1.54e-05, Final residual = 1.23e-07, No Iterations 4
time step continuity errors : sum local = 1.42e-12, global = -6.4e-15, cumulative = -1.09e-06
```
- Initial residual: imbalance of the equation with the field from the previous outer iteration.
  This is the convergence measure of the nonlinear problem.
- Final residual: imbalance after the linear solver worked on this one system. Set by `tolerance`
  (absolute) and `relTol` (reduction factor) in fvSolution. Small every iteration by construction;
  never judge convergence by it.
- Continuity line: mass conservation of the pressure step. Not a residual.
- Trap: a residual is normalised by the size of its own field. The spanwise velocity Uy should be
  zero, so its residual looked bad (5e-3) while the actual max |Uy| was 1.6e-6 m/s. Check the field.
- `foamLog log.simpleFoam` writes one two-column file per quantity into `logs/`; plot those for a
  Fluent-style residual curve, or `foamMonitor -l logs/Ux_0` live (needs gnuplot).
- Rule 5 of CLAUDE.md: convergence is decided by the primary quantities being flat within 1 % and the
  balances closing, not by residuals. In V0 the 4 m-mesh cases stalled at a p residual of 7e-5 while
  the probe at roof height was identical to 11 digits between iterations 2000 and 3000. They are
  converged.
- `residualControl` in fvSolution stops the run when initial residuals drop below thresholds. It is a
  convenience, not the criterion.

## 5. The log-law inlet (2026-10-08) (story step 2, the inlet)

Theory. In a neutral ABL over uniform rough ground the mean wind follows
```
U(z) = (u*/kappa) ln((z + z0)/z0)
u*   = kappa Uref / ln((Zref + z0)/z0)
```
with kappa the von Karman constant (0.40 here), z0 the aerodynamic roughness length (the height at
which the log law extrapolates to zero; 0.3 m for suburban/industrial terrain), Uref the speed known at
height Zref. Richards & Hoxey (1993) showed the matching turbulence profiles that make this an exact
solution of standard k-epsilon:
```
k       = u*^2 / sqrt(Cmu)                     (constant with height)
epsilon = u*^3 / (kappa (z + z0))
omega   = u* / (kappa sqrt(Cmu) (z + z0))      (Yang et al. 2009, for SST)
```
Worked example, our V0 inputs: Uref 10 m/s at Zref 15 m, z0 0.3 m, kappa 0.4:
u* = 0.4 * 10 / ln(15.3/0.3) = 4 / 3.932 = 1.017 m/s. (Saleh computed this by hand: 1.017. Correct.)
k = 1.017^2 / 0.3 = 3.45 m2/s2.
For comparison the tutorial had z0 0.01 m and Zref 6 m, giving u* 0.625 and k 1.30: our boundary
layer is about three times more turbulent because the ground is 30 times rougher.

Where it lives. `0/include/ABLConditions` holds Uref, Zref, z0, d, kappa, Cmu once. `0/U`, `0/k`,
`0/epsilon` (or `0/omega`) include it into the inlet patch with
`type atmBoundaryLayerInletVelocity` / `...InletK` / `...InletEpsilon` / `...InletOmega`.
The code measures z from the lowest point of the inlet patch, not from absolute zero.
Source: src/atmosphericModels/derivedFvPatchFields/atmBoundaryLayer/.

## 6. Why the inlet k is constant with height (2026-10-08) (story step 2, the inlet)

In the surface layer the turbulent shear stress is nearly constant with height (constant-flux layer):
-u'w' = u*^2. Standard k-epsilon links stress to k through nu_t = Cmu k^2/epsilon and, in local
equilibrium (production = dissipation), -u'w' = sqrt(Cmu) k. Hence
```
k = u*^2 / sqrt(Cmu) = 1.017^2 / 0.3 = 3.45 m2/s2      (same at every height)
```
So constant k is what the model itself requires for a constant-stress layer, which is why the
Richards-Hoxey profiles are an exact solution of the model.

Reality: measured k decreases with height; constant k holds only in the surface layer (lowest ~10 %
of a ~1 km deep ABL, i.e. ~100 m). Our box is 135 m high and the building 15 m, so we stay inside
that range. For tall structures use the Yang et al. (2009) form: entries `C1`, `C2` in the same inlet
condition make k and epsilon vary with height; defaults `C1 0`, `C2 1` give the constant form.

Sanity check by turbulence intensity I = sqrt(2k/3)/U(z), u_rms = sqrt(2*3.45/3) = 1.52 m/s:
| z | U | I |
|---|---|---|
| 15 m (roof) | 10.0 m/s | 15 % |
| 135 m (top) | 15.5 m/s | 10 % |
15 % at roof height over suburban terrain is in the normal wind-tunnel ABL range.

## 7. The rough-ground wall function and the first-cell question (2026-10-08) (story step 2 and 3, the ground)

The solver does not resolve the flow between the ground and the first cell centre at height y. The
wall function runs the log law backwards: from the first-cell velocity it infers u* for a log law
with roughness z0 and sets an artificial viscosity on the wall face so the shear stress is u*^2.
v2606 source (src/atmosphericModels/.../atmNutkWallFunction):
```
nut_wall = nu * ( yPlus*kappa / ln((y + z0)/z0) - 1 ),   yPlus = Cmu^(1/4) sqrt(k) y / nu
```
The only roughness information is z0 inside the logarithm. Inlet profile and wall function must use
the same z0, kappa and Cmu. In the case files: `0/nut` ground patch, `type atmNutkWallFunction`,
with `z0`, `kappa`, `Cmu` taken from `include/ABLConditions`.

Two opposite requirements on the first cell height y:
- Log law validity wants y well above z0 (the formula is derived for y >> z0).
- The k equation wants y small, because production and dissipation of k change steeply in the
  first metres and a big cell averages them into one number.

V0 measured which wins (z0-consistent wall set, fixed-shear top, max k deviation below 3H at the
building position relative to the inlet; U was within 2.4 % in all six):
| Closure | Mesh A, y = 2 m (y/z0 = 6.7) | Mesh B, y = 0.5 m (y/z0 = 1.7) |
|---|---|---|
| kEpsilon + HW sigmaEps 1.11 | 4.2 % | 0.9 % |
| realizableKE | 10.8 % | 3.7 % |
| kOmegaSST | 9.0 % | 3.3 % |
The deviation sits in the first two cells and decays with height (realizableKE at roof height 15 m:
2 % on A, 0.3 % on B). Conclusion: for our closures k resolution wins; keep the 1 m first cell.

Still open: next to the building the brief wants 0.5 m and 0.25 m cells, so y = 0.25 and 0.125 m,
below z0 = 0.3 m. The formula still returns a value (it uses y + z0) but V0 says nothing about its
accuracy there. Test: generate mesh C (first cell 0.5 m) and repeat the table.

## 8. Why "30 < y+ < 300" does not apply to the rough ground (2026-10-08) (story step 2, the ground)

Smooth wall: y+ = u* y / nu; the log law U+ = (1/kappa) ln(y+) + B holds between the buffer layer
(y+ ~ 30) and the outer layer (y+ ~ a few hundred in lab boundary layers). A wall function assuming
the log law needs the first cell centre in that window. That is where the rule of thumb comes from.

Rough ABL ground: the anchor length is z0, not nu/u*. Roughness Reynolds number
```
u* z0 / nu = 1.017 * 0.3 / 1.5e-5 ~ 2e4      (fully rough for anything above ~2)
```
In the fully rough regime viscosity drops out of the law of the wall and the log law takes the z0
form we use. Conditions on the first cell become: y above z0, and y inside the surface layer
(below ~100 m). Our y of 0.5 to 2 m satisfies both. The relevant dimensionless numbers are y/z0 and
y/delta, not y+.

OpenFOAM's `yPlus` function object still uses nu, so it reports y+ of 2e4 to 1.4e5 here. Not a
warning: it means nu is irrelevant. The low-Re fallback inside atmEpsilonWallFunction (y+ below the
laminar limit ~11) can never trigger on this ground.

For the smooth walls of the building, parapet and chiller boxes the 30 < y+ < 300 rule returns and is
a separate decision when the building is meshed.

## 9. Why epsilon and omega need z0-aware wall functions (2026-10-08) (story step 2 and 3, the ground)

In the wall-adjacent cell the epsilon equation is not solved: the code overwrites epsilon and the k
production term G with their log-law equilibrium values. Smooth wall (epsilonWallFunction):
```
epsilon_P = Cmu^(3/4) k^(3/2) / (kappa y)
G_P       = (nu_t + nu) |dU/dy| Cmu^(1/4) sqrt(k) / (kappa y)
```
k has no formula of its own: kqRWallFunction is zero gradient, so first-cell k is what production
and dissipation leave.

Rough ground: the inlet profile has epsilon = u*^3/(kappa (z + z0)), and with u* = Cmu^(1/4) sqrt(k)
this is the formula above with y replaced by y + z0 (mixing length grows from the roughness height).
atmEpsilonWallFunction and atmOmegaWallFunction (Parente et al. 2011) make that substitution;
the standard ones do not, so they over-dissipate the first cell by the factor (y + z0)/y:
1.6 on mesh B (y = 0.5 m), 1.15 on mesh A (y = 2 m).

V0 check, first-cell k at the building (inlet 3.45 m2/s2):
| Wall set | Mesh B | Mesh A |
|---|---|---|
| std (plain epsilon/omega WF) | 2.92 to 3.02 (about 13 % low) | 3.37 to 3.46 (within 2 %) |
| atm (y + z0) | 3.45 to 3.67 | 3.47 to 3.61 |
The std set fails on the fine mesh for the predicted reason; the atm set is consistent with the inlet
on both. omega: omega_P = sqrt(k)/(Cmu^(1/4) kappa (y + z0)), same behaviour with SST.

In the files: one word on the ground patch of `0/epsilon` or `0/omega`, `atmEpsilonWallFunction` /
`atmOmegaWallFunction` plus `z0`. The official tutorial uses the standard ones (the inconsistency
flagged in docs/decisions/0001); V0 quantified it.

## 10. Mesh C: the first cell below z0 (2026-10-08) (story step 4, the near-building question)

Question: next to the building the mesh will be 0.5 m and 0.25 m, so the first cell centre sits at
0.25 or 0.125 m, below z0 = 0.3 m. Does the rough-wall treatment still hold there?
Test: mesh C, first cell 0.5 m (y = 0.25 m, y/z0 = 0.83), fixed-shear top, three closures, both wall
sets. Predictions from entries 7 and 9: the atm set keeps the inlet and wall consistent whatever y;
the std set over-dissipates the first cell by (y + z0)/y = 2.2, worse than on mesh B.

Result (max deviation from the inlet below 3H at the building position; pass mark 5 %):
| Closure | Wall set | Mesh A y=2 m | Mesh B y=0.5 m | Mesh C y=0.25 m |
|---|---|---|---|---|
| kEpsilon + HW | atm | U 1.1, k 4.2 | U 2.3, k 0.9 | U 1.8, k 0.8 |
| realizableKE | atm | U 0.0, k 10.8 | U 2.1, k 3.7 | U 0.9, k 1.9 |
| kOmegaSST | atm | U 0.2, k 9.0 | U 2.1, k 3.3 | U 1.1, k 1.7 |
| kEpsilon + HW | std | U 0.9, k 1.1 | U 3.4, k 10.6 | U 12.1, k 18.8 |
| realizableKE | std | U 0.3, k 5.8 | U 3.8, k 9.7 | U 12.2, k 17.6 |
| kOmegaSST | std | U 0.3, k 5.1 | U 3.8, k 11.8 | U 11.8, k 21.1 |

First-cell k on mesh C (inlet 3.45): atm 3.52 to 3.61; std 2.74 to 2.82, i.e. 20 % low, as the
factor 2.2 predicted. With the std set even U now fails (12 %), because the drained k feeds back into
the wall viscosity.

Reading: with the z0-consistent (atm) wall set, a first cell below z0 is not a problem; it is the best
of the three meshes, because the near-ground k balance is resolved best and the wall formula stays
consistent with the inlet. The "y must exceed z0" worry applies to the std set, which has no z0 in
its dissipation and therefore gets worse the closer the cell is to the ground. Mesh at 0.25 m
(y/z0 = 0.4) was not run; the trend from A to C gives no reason to expect a reversal, and it can be
run with one line in the parameter file if the building mesh needs it.

Numbers: results/V0/summary.md. All 30 cases: mass closed to 1e-6 %, profiles flat between the last
two written times to better than 1e-3 %.

## 11. Why we validate when OpenFOAM is "already validated" (2026-10-08) (story step 6, entering V1)

Verification: does the code solve the equations it claims to solve? OpenFOAM has that; the smoke
test was a small piece of it (the ABL inlet reproduced its own analytical profile).
Validation: do the equations and settings we chose reproduce reality for this class of flow? That
depends on our choices, so nobody can do it for us:
- RANS closure: calibrated on simple shear flows; around a bluff building the roof separation bubble
  and wake length are known to be wrong by model-dependent amounts. V0 had no building.
- Turbulent Schmidt number: free constant 0.3 to 1.0 in the literature; scales plume spread
  directly. Fixed in V1 against measured concentration.
- Mesh and wall treatment on smooth walls (y+ rules of entry 8 return).
- Our inflow: V0 showed it survives an empty box; V1 shows whether a building sees the right
  approach flow.
What validation buys: (1) a model-form uncertainty band (e.g. hit rate, FAC2) that every applied
result inherits; (2) a calibrated setup frozen and carried unchanged to the data hall.
Rule: acceptance numbers fixed before the run, reported whether met or not. A validation tuned until
it passes validates nothing.
Ladder: V1 (AIJ Case H) separation, wake, scalar transport; V2 (Concordia stack) roof-level dilution
versus stack height, the design variable; V2b the tunnel-to-full-scale jump. Chiller
self-recirculation has no public data; its credibility rests on V1 and V2 and the report says so.

## 12. V1: what the AIJ Case H experiment measured (2026-10-08) (story step 6, V1 starts)

Source: data/raw/aij_caseH (Zenodo 15429872, CC BY 4.0; Yoshie 2016).
Geometry: 0.1 x 0.1 x 0.2 m block (H = 0.2 m). Origin at the base of the leeward wall on the centre
line: building x in [-0.1, 0], y in [-0.05, 0.05], z in [0, 0.2].
Source: 4 mm floor hole at 0.25H behind the leeward wall, x = +0.05, y = 0; ethylene,
Q = 5.83e-6 m3/s. Re = 43,000 on H and U_H.
Measurements (RS_caseH.csv, 876 points, 826 with both U and c): vertical plane y = 0, horizontal
planes z/H = 1/16, 1/4, 1/2; x from -1H to +2H; mean U, V, W, rms, k, <c> in ppm, c_rms.
Missing value -999.9.
Approach flow (AF_caseH.csv, 18 heights at x = -2.5H, no building):
| Quantity | Value |
|---|---|
| U_H | 3.23 m/s |
| power-law exponent (z/H 0.4 to 2) | about 0.27 |
| I_u at H | 22 % |
| k at H | 0.45 m2/s2, nearly constant from 0.1H to 1.75H |
| u* from -u'w' | about 0.44 m/s |
Observation: k is nearly constant over the building height (the constant-k form of entry 6 in a real
tunnel). But u*^2/sqrt(Cmu) = 0.65 overestimates the measured 0.45 by ~45 %: Cmu = 0.09 does not
fit atmospheric turbulence (stress/k ratio lower than 0.3). V1 inlet decision follows from this.
What V1 reproduces: mean velocity at the measured points (hit rate >= 0.66) and mean concentration
(FAC2 >= 0.5, fractional bias within 0.3), Project.md section 5. Dimensionless concentration
C* = c U_H H^2 / Q makes tunnel and CFD comparable.

## 13. V1 inlet decision: measured profiles, and why no inlet can be fully consistent (2026-10-08) (story step 6)

Fit of the V0 log-law family to the tunnel approach flow: z0 = 11.7 mm, u* = 0.448 m/s, U within
2.9 % rms; u* agrees with sqrt(-u'w') = 0.44 from the data. But k = u*^2/sqrt(Cmu) = 0.67 against
measured 0.45, because the measured -u'w'/k = 0.415, not sqrt(0.09) = 0.3. With Cmu = 0.09 no inlet
matches U, k and the ground wall function at once; one must choose what gives.
Decision 0003: measured U and k tabulated; epsilon = sqrt(Cmu) k dU/dz (local equilibrium, AIJ
guideline); omega = epsilon/(Cmu k). The ground inconsistency is measured by an empty-domain run of
the V1 box (V0 tooling), and the log-law inlet is run once as the inflow sensitivity.
In OpenFOAM a tabulated inlet profile is `timeVaryingMappedFixedValue` reading
constant/boundaryData/inlet/points and the field files, or, for a 1-D profile, a `codedFixedValue`
or `tableFile` Function1 on a uniformFixedValue; the choice is made when the case is built.
Benchmark standing: AIJ cases are the reference set for urban flow and dispersion CFD (AIJ
guidelines 2008); COST 732 and VDI 3783/9 are the European counterparts and the source of the pass
marks. Case H is openly licensed (CC BY 4.0).

---

# Part C. Building a case by hand: V1 step by step (started 2026-10-08)

Format from here on: each step says what the program is, where it is, what file it reads, what
each number means, the exact command, what comes out, and what to check. The case being built is
validation/V1/case_by_hand. The order of building any OpenFOAM case:
1. the box of air and its outer faces (blockMesh)
2. the building cut out of the box (STL, surfaceFeatureExtract, snappyHexMesh)
3. list the patches and decide what each one does physically
4. boundary conditions, one field file at a time (0/U, 0/p, 0/k, ...)
5. initial values inside the domain
6. constants and models (constant/transportProperties, turbulenceProperties, system/fvSchemes, fvSolution)
7. run control and monitors (system/controlDict), then run
8. inspect: log, checkMesh, residuals, monitors, pictures

Before any command in a new terminal: `source ~/opt/openfoam2606.sh` (puts every OpenFOAM program
on the path for that terminal).

## C1. The box of air: blockMesh

- Program: blockMesh. Reads system/blockMeshDict. Writes constant/polyMesh (the mesh).
- Needs system/controlDict, fvSchemes and fvSolution to exist, even if they are placeholders,
  because every OpenFOAM program loads the case the way the solver does.
- File: validation/V1/case_by_hand/system/blockMeshDict. Numbers: xMin..zMax are the corners of
  the air box in metres (inlet 5H upstream of the building, outlet 15H downstream, sides 5H, top
  6H); dx is the cell size (0.04 m = coarse grid); nx, ny, nz are computed from them.
- `vertices`: the 8 corners. `blocks`: one hex block split into nx*ny*nz uniform cells
  (simpleGrading 1 1 1 = no stretching). `edges ()`: empty because every edge is straight; filled
  only for arcs or splines. `boundary`: the outer faces grouped and named; each face is four vertex
  numbers ordered so the normal points outwards. Types: patch (generic), wall (solid, needed for
  wall functions), symmetry, empty (2-D), cyclic (periodic).
- Command: `blockMesh`, then `checkMesh`. Result 2026-10-08: 168,300 cells, 5 patches, Mesh OK.
- No building yet: blockMesh only makes blocks. The building's faces are made by snappyHexMesh.

## C2a. The building shape: an STL file

- STL = plain-text list of triangles, the universal CAD export format. OpenFOAM reads STL, never
  makes it. For a box we write it with our own script geometry/make_box_stl.py.
- Command: `python3 geometry/make_box_stl.py -0.1 -0.05 0  0 0.05 0.2  building  validation/V1/case_by_hand/constant/triSurface/building.stl`
  Arguments: min corner (x y z), max corner (x y z), name inside the file, output path.
- The folder constant/triSurface is where snappyHexMesh looks for surfaces; the name is fixed.
- Inside: 12 `facet` blocks, each one triangle with 3 `vertex` lines in metres and a `normal`
  pointing outwards. STL files are ignored by Git; the script is what is kept.

## C2b. The sharp edges: surfaceFeatureExtract

- Program: surfaceFeatureExtract. Reads system/surfaceFeatureExtractDict and the STL. Writes
  constant/triSurface/building.eMesh and constant/extendedFeatureEdgeMesh/ (both ignored by Git).
- Why: the mesher keeps corners sharp only where it knows an edge is. A box has 8 corners, 12 edges.
- Numbers: `includedAngle 150` means an edge counts as sharp if its two faces meet at less than 150
  degrees (a box has 90). `extractionMethod extractFromSurface` means find edges from the triangle
  angles.
- Command: `surfaceFeatureExtract`. Check in the output: 8 feature points, 12 feature edges.

## C2c. The mesher: snappyHexMesh, and how its numbers were chosen

- Program: snappyHexMesh. Reads system/snappyHexMeshDict, the STL, the feature edges and
  constant/polyMesh from blockMesh. `-overwrite` replaces constant/polyMesh in place.
- Stages, switched at the top of the file: castellatedMesh (refine and remove cells inside the
  building), snap (move cut faces onto the surface and corners onto the edges), addLayers (prism
  layers; off for V1, Project.md section 7).
- Block `geometry`: `building` is the STL (its name becomes the patch name). `nearBox` and
  `wakeBox` are invisible searchableBox regions used only to say "refine inside me".
- Block `castellatedMeshControls`: a level n cell is the background cell halved n times
  (40, 20, 10, 5, 2.5 mm for levels 0 to 4). `refinementSurfaces building level (2 2)` and
  `patchInfo type wall`: 10 mm cells on the building, and the cut faces become patch "building" of
  type wall. `features ... level 2`: same on the sharp edges. `refinementRegions`: nearBox level 2
  (10 mm), wakeBox level 1 (20 mm); the 1e15 is a distance the "inside" mode ignores.
  `nCellsBetweenLevels 3`: three cells of each level between two sizes (gentle transition).
  `locationInMesh`: a point in open air; cells connected to it are kept, the building interior is
  deleted.
- Block `snapControls`: `explicitFeatureSnap true` uses the extracted edges. `meshQualityControls`
  are limits the snapper may not violate.
- Command: `snappyHexMesh -overwrite` then `checkMesh`. Result 2026-10-08: 292,556 cells, 6 patches
  (building: wall, 850 faces), max non-orthogonality 25 deg, Mesh OK. About one minute serial.

How the numbers were chosen (rule for any case):
1. Smallest feature and cells across it (AIJ: 10 across the building width 0.1 m -> 10 mm). That is
   the finest cell. Level 2 here is the coarsest acceptable grid, right for the coarse level of a
   grid study.
2. Background so the finest size is reached in 2 or 3 levels (40 mm -> 10 mm in 2). Each level
   costs 8x cells in the refined volume: nearBox at level 2 ~84k cells, level 3 ~670k, level 4
   ~5.4M. Level 4 also puts y+ near 40 (first cell 1.25 mm), closing the wall-function window.
3. Refinement regions around gradients and measurements with margin; far field at background.
4. Domain from the guideline (AIJ: 5H in, 15H out, 5H sides, 6H top).
5. locationInMesh in open air.
6. y+ from the finest wall cell against the intended wall treatment (10 mm -> y = 5 mm -> y+ ~150).
7. checkMesh: if non-orthogonality or skewness are high, raise nCellsBetweenLevels or grow the boxes.
Grid study: shrink the background (40 -> 28 -> 20 mm) keeping the levels, so every zone refines by
the same ratio 1.4. Changing the level instead refines by 2 and only locally.

## C2d. Looking at the mesh: ParaView client-server from another PC

- The workstation has no display, so the heavy part (pvserver) runs there and the ParaView GUI
  runs on the PC. Both must be the same version (workstation: 5.11.2).
- On the workstation: `pvserver --force-offscreen-rendering --server-port=11111` (prints
  "Waiting for client..."; one client at a time; exits when the client disconnects).
- Tunnel the port over the SSH connection VS Code already uses: Ports tab -> Forward a Port -> 11111,
  or on the PC `ssh -L 11111:localhost:11111 <ssh host name>`.
- ParaView on the PC: File -> Connect -> Add Server: Client / Server, host localhost, port 11111,
  Configure -> Manual -> Save -> Connect. Then File -> Open the case's `case.foam` (an empty file
  that tells ParaView "this folder is an OpenFOAM case"), Apply.
- First look: representation "Surface With Edges"; Filters -> Slice, normal Y, Apply: shows the
  three cell sizes and the building hole with sharp corners.
- Result of C2 on 2026-10-08 (Saleh's own run): 292,563 cells (161,085 at 40 mm, 46,926 at 20 mm,
  84,552 at 10 mm), 6 patches, 4,640 polyhedra on the level transitions (normal), Mesh OK.

## C3. What each patch does physically (the plan for the field files)

| Patch | Physical rule | OpenFOAM pattern |
|---|---|---|
| inlet | measured profile of U and k enters | fixedProfile from a CSV table |
| outlet | air leaves, pressure uniform | p fixedValue 0; others inletOutlet (zeroGradient with a backflow guard) |
| ground, building | smooth solid walls | noSlip + wall functions |
| top, sides | far away, no friction, nothing crosses | slip |
Pressure is fixed only at the outlet; everywhere else it floats (zeroGradient).

## C4a. The inlet tables: validation/V1/make_inlet_profiles.py

- Reads data/raw/aij_caseH/AF_caseH.csv (18 heights). Writes constant/inletProfiles/U.csv
  (z,Ux,Uy,Uz), k.csv, epsilon.csv, omega.csv in the case. A row at z = 0 and one at z = 1.2 m
  (domain top, values held) are added so the table spans the inlet patch.
- epsilon = sqrt(Cmu) k dU/dz with dU/dz = u*/(kappa (z + z0)) from the log-law fit (u* 0.448,
  z0 0.0117). Lesson: finite differences of measured points give noise (slopes 1.2 to 6.5 1/s
  between neighbours near z = H, epsilon jumping 5x). Use a fitted, smooth slope. Decision 0003 addendum.
- omega = epsilon/(Cmu k). Values at z = H: U 3.23, k 0.453, epsilon 0.72, omega 17.7.
- Command: `python3 validation/V1/make_inlet_profiles.py data/raw/aij_caseH/AF_caseH.csv validation/V1/case_by_hand`

## C4b. The velocity file 0.orig/U

- Every field file: header `class` (volVectorField for vectors, volScalarField for scalars),
  `dimensions [kg m s K mol A cd]` ([0 1 -1 0 0 0 0] = m/s; OpenFOAM checks units),
  `internalField` (starting guess in every cell), `boundaryField` with one block per patch whose
  names must match constant/polyMesh/boundary exactly.
- inlet `fixedProfile` + `profile csvFile`: value varies along `direction (0 0 1)` from the table
  `<constant>/inletProfiles/U.csv` (`nHeaderLine 1`, `refColumn 0` = z, `componentColumns (1 2 3)`
  = Ux Uy Uz, `outOfBounds clamp` holds the last row above the table). `<constant>` expands to the
  case's constant folder.
- outlet `inletOutlet`: zeroGradient where air leaves; where it would enter, `inletValue` (0 0 0)
  is imposed. The backflow guard.
- ground, building `noSlip`. top, sides `slip`.
- 0.orig is the clean copy; the run copies it to 0. Git keeps 0.orig only.

## C4c. The pressure file 0.orig/p

- simpleFoam is incompressible: p is pressure/density, dimensions [0 2 -2 0 0 0 0] (m2/s2);
  multiply by rho = 1.2 for Pa. Only differences matter, so one patch pins the level.
- outlet `fixedValue 0` (the pin). inlet `zeroGradient`. Walls, top, sides `zeroGradient`
  (no flow through them -> no normal gradient).
- Rule: where U is fixed, p is free; where p is fixed, U is free. Never both on one patch.

## C4d. The turbulence files 0.orig/k, epsilon, omega, nut

- k, epsilon, omega: twins of U in scalar form. Inlet `fixedProfile csvFile` with
  `componentColumns (1)`; outlet `inletOutlet` with `inletValue $internalField` (the `$` macro
  pastes the internalField value); top, sides `slip`.
- Walls: k `kqRWallFunction` (zero gradient; k in the first cell is what production and
  dissipation leave). epsilon `epsilonWallFunction`, omega `omegaWallFunction`: smooth-wall log-law
  equilibrium in the first cell, plain wall distance y (the atm versions with z0 are for rough
  ground, not the tunnel). Both dissipation files exist; the model reads the one it needs.
- Units: k m2/s2, epsilon m2/s3, omega 1/s. Never start k at zero (the model divides by it).
- nut is not solved; the model computes it from k and epsilon/omega. Its file carries the velocity
  wall function: `nutkWallFunction` on walls (smooth log law, u* = Cmu^1/4 sqrt(k), needs
  30 < y+ < 300; our 10 mm building cells give y+ ~150). Elsewhere `calculated`.
- Step 4 pattern for all 30 entries: table at the inlet, guard at the outlet, wall function on the
  two walls, slip or calculated on the rest.

## C5. Initial guess inside the domain

- A steady solver iterates from the guess; closer guess = fewer iterations, smaller start-up
  transient. Guess must not contradict the boundary conditions; uniform turbulence is fine.
- Program: setExprFields. Reads system/setExprFieldsDict, overwrites the internalField of a field
  in 0/ with an expression. Here U = log-law fit (ustar/kappa * ln((z+z0)/z0), 0, 0).
  `pos()` is the cell centre; `#{ ... #}` delimits the expression.
- Command (at run time, after `cp -r 0.orig 0`): `setExprFields`.

## C6. Physics and numerics: four files

- constant/transportProperties: `Newtonian`, `nu 1.5e-05` (air, m2/s). No density: simpleFoam is
  incompressible.
- constant/turbulenceProperties: `simulationType RAS`, `RASModel realizableKE` or `kOmegaSST`;
  `printCoeffs on` writes the constants to the log. Switching closure = one word here.
- system/fvSchemes (discretisation):
  `ddtSchemes steadyState` (no time derivative; SIMPLE iterates).
  `gradSchemes Gauss linear`; `grad(U) cellLimited Gauss linear 1` (bounded gradient for U).
  `divSchemes default none` forces every convection term to be listed:
  `div(phi,U) bounded Gauss linearUpwind limited` (second-order upwind for momentum);
  `div(phi,k|epsilon|omega) bounded Gauss limitedLinear 1` (second-order TVD for turbulence);
  the `bounded` prefix subtracts the continuity error, helping steady convergence.
  `laplacianSchemes Gauss linear limited corrected 0.33` (diffusion with non-orthogonal correction;
  our max non-orthogonality is 26 deg). `wallDist meshWave` (wall distance for SST and y+).
  AIJ guideline: no first-order upwind for the final result.
- system/fvSolution (linear solvers and loop control):
  `p GAMG tolerance 1e-7 relTol 0.01` (multigrid for pressure); `U k epsilon omega smoothSolver
  GaussSeidel tolerance 1e-8 relTol 0.1`. tolerance is absolute, relTol is the per-iteration
  reduction (entry 4).
  `SIMPLE consistent yes` (SIMPLEC) with `relaxationFactors U 0.9, turbulence 0.7`.
  `residualControl p 1e-5, U 1e-6, k/epsilon/omega 1e-6`: stops the run when all initial residuals
  are below; a convenience, the real convergence check is the monitors (rule 5).

### C6 extended: how to choose the numerics (fvSolution and fvSchemes)

One SIMPLE iteration: solve momentum for U with the current p; build and solve the pressure
equation; correct U for continuity; solve k and epsilon/omega. Four or five linear systems
A x = b with one unknown per cell.

Linear solvers:
| Solver | Use for | Why |
|---|---|---|
| GAMG (multigrid) | p | pressure couples the whole domain; multigrid is near-linear in cost |
| smoothSolver GaussSeidel | U, k, epsilon, omega | convection-dominated, diagonally strong; a few sweeps suffice |
| PCG | p on small meshes or if GAMG misbehaves | robust, slower |
| PBiCGStab | transport equations if smoothSolver stalls | converges where Gauss-Seidel does not |
Pressure is symmetric (GAMG/PCG); transport equations are not (smoothSolver/PBiCGStab).

tolerance = absolute stop; relTol = stop when reduced by this factor in this call. Steady SIMPLE:
relTol 0.01 (p) and 0.1 (others) because the outer loop repeats. Transient PISO: relTol near 0 in
the final corrector.

consistent yes = SIMPLEC: keeps neighbour influence in the velocity correction, so p needs no
relaxation and U can use 0.9. Plain SIMPLE: p 0.3, U 0.7.

relaxationFactors: fraction of the new value accepted. Changes the path, not the answer. If
residuals oscillate or k blows up early: turbulence to 0.5, then U to 0.7. Stable but slow: raise.

nNonOrthogonalCorrectors: 0 below ~50 deg non-orthogonality with a corrected laplacian; 1 to 2 for
60 to 70 deg; above that fix the mesh.

residualControl: stops the run when all initial residuals are below the thresholds; set a decade
tighter than you would stop by eye. The convergence judgement is the monitors (rule 5).

Convection schemes:
| Scheme | Order | Character | When |
|---|---|---|---|
| upwind | 1 | stable, diffusive (smears wakes and plumes) | start-up only, never the final result |
| linearUpwind grad(U) | 2 | upwind-biased, stable | momentum in steady RANS (ours) |
| limitedLinear 1 | 2 | central + limiter, keeps positivity | k, epsilon, omega, scalars (ours) |
| linear | 2 | pure central, may oscillate | LES; diffusion terms; aligned flows |
| QUICK | 3 | more accurate, less stable | fine meshes, smooth flow |
`bounded` prefix on every convection term in a steady run. Hard start: all div schemes upwind
for ~200 iterations, then switch back with `startFrom latestTime`.
Gradients: Gauss linear; cellLimited on U against overshoots at sharp edges. Laplacians: Gauss
linear corrected on orthogonal meshes; limited corrected 0.33 on snappyHexMesh meshes.
