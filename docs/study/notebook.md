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
| V1 AIJ Case H | Separation, wake, scalar transport around a cube, against wind-tunnel data | closed 2026-10-12, decision 0006: velocity mark not met (0.60 to 0.63 vs 0.66), FAC2 met for Sct <= 0.6, FB not met; carried as model-form uncertainty |
| **V2 Concordia stack** | **Roof-level dilution versus stack height, the applied design variable** | **next** |
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
6. V1, the AIJ Case H cube: Saleh built the case by hand (Part C), ran the coarse, medium and SST
   cases himself, and the remaining runs were queued: fine grid, log-law inlet, empty domain for
   both closures, rough floor, and the tracer with six Schmidt numbers. Outcome (C8 to C17): the
   velocity hit rate is 0.59 to 0.63 against the 0.66 mark on every grid and both closures, with
   a wake 0.5 m/s too slow that the mesh does not change (GCI confirms grid independence of drag
   and cavity velocity); the concentration FAC2 is met for Sct 0.4 to 0.6 but the fractional bias
   is not, because the same too-long recirculation holds the tracer near the building. The far
   wake is right for both velocity and concentration. The inflow turbulence accounts for about a
   quarter of the wake deficit; the rest is the eddy-viscosity model, which is what the V1-LES rung
   of the ladder exists to measure.
7. V1 closed by decision 0006: realizable k-epsilon with the medium-grid rule is the baseline,
   Sct 0.4 and 0.7 both go to V2, the unmet marks are reported as they are. Next: V2, the Concordia rooftop stack,
   which needs the IRSST report R-848 downloaded and digitised first.

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


## The universal recipe: running any OpenFOAM case, start to finish

Every case, every time, in this order. Angle brackets mark a placeholder: type your own word
there and leave the brackets out (<case> = the case folder, <name> = a name for the result file,
N = the agreed core count). Lines starting with # are comments, not commands.

```
# 1. Go to the case folder and load OpenFOAM (once per terminal)
cd /mnt/d/Saleh/openfoam_project/validation/V1/<case>
source ~/opt/openfoam2606.sh

# 2. Check the machine before using cores (CLAUDE.md rule 12)
cat /proc/loadavg          # first number = cores in use; the machine has 192
nproc

# 3. Mesh (skip if constant/polyMesh is already the mesh you want)
blockMesh                 > log.blockMesh 2>&1
surfaceFeatureExtract     > log.surfaceFeatureExtract 2>&1     # only if there is an STL
snappyHexMesh -overwrite  > log.snappyHexMesh 2>&1             # only if there is an STL; never forget -overwrite
checkMesh                 > log.checkMesh 2>&1
grep -E "Mesh OK|Failed|cells:" log.checkMesh                  # must say Mesh OK; note the cell count

# 4. Fresh fields and the initial guess
rm -rf 0 && cp -r 0.orig 0
setExprFields             > log.setExprFields 2>&1             # only if system/setExprFieldsDict exists

# 5. Split for parallel (N must match numberOfSubdomains in system/decomposeParDict)
decomposePar              > log.decomposePar 2>&1

# 6. Solve, in the background, output to a log
mpirun -np N simpleFoam -parallel > log.simpleFoam 2>&1 &

# 7. Watch it (second terminal; Ctrl+C stops the watching, not the solver)
watch -n 2 tail -n 12 log.simpleFoam
tail -n 2 postProcessing/probesWake/0/U                        # the primary quantity, every iteration

# 8. When "End" appears at the bottom of log.simpleFoam: merge, check, sample, score
reconstructPar -latestTime                   > log.reconstructPar 2>&1
simpleFoam -postProcess -func yPlus -latestTime        | grep "y+"
simpleFoam -postProcess -func samplePoints -latestTime > log.sample 2>&1
python3 ../metrics.py . --data ../../../data/raw/aij_caseH/RS_caseH.csv --out ../../../results/V1/<name>.json
```

What "converged" means before you trust step 8 (rule 5): the probe values at the last two written
iterations differ by less than 1 %, and the inlet and outlet flow sums in postProcessing/flowIn and
flowOut agree within 1 %. The line "SIMPLE solution converged in N iterations" is only the stop
signal.

To rerun the same case with one change: copy the folder (`cp -r <case> <newcase>`), in the copy
delete the old output (`rm -rf processor* [1-9]* postProcessing log.* constant/polyMesh`), change
the one number, and start the recipe again from step 3.

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

With the mesh built and every patch given its rule, the solver still needs to know three things:
what fluid this is, which turbulence model closes the equations, and how the equations are turned
into numbers and solved. Four files carry that, two in constant (the physics) and two in system
(the numerics).

### C6a. The fluid: constant/transportProperties

Two lines. `transportModel Newtonian` says the viscosity does not depend on the shear rate, which is
true for air. `nu 1.5e-05` is the kinematic viscosity in m2/s, air at about 20 C from standard tables
(a measured input). There is no density in the file because simpleFoam is an incompressible solver:
it divides the whole momentum equation by density, which is why its pressure is p/rho in m2/s2.
Density only comes back when a force in newtons is wanted, and then it is supplied to the force
monitor as `rhoInf 1.2`.

### C6b. The turbulence model: constant/turbulenceProperties

`simulationType RAS` selects Reynolds-averaged modelling, as the brief requires for every design
run. `RASModel realizableKE` picks the closure; the other candidate in Project.md section 6 is
`kOmegaSST`, and switching between them is this one word, because both the epsilon and the omega
files exist in 0.orig and each model reads the one it needs. `printCoeffs on` makes the solver
print the model constants at start-up, so the log records them; for realizableKE they are
A0 4, C2 1.9, sigmak 1, sigmaEps 1.2 (seen in the sampling run of 2026-10-09). Nothing is
changed from the defaults: the Hargreaves and Wright sigmaEps 1.11 belongs to the standard
k-epsilon model and the atmospheric inlet, not to this tunnel case.

### C6c. How each term is discretised: system/fvSchemes

Think of the equations term by term. Each kind of term has its own block in this file, and each
block says how that term becomes numbers on the mesh.

Time derivative, `ddtSchemes steadyState`: there is none. SIMPLE marches in iterations, not in
time, so the time derivative is simply switched off. A transient run would say Euler or backward.

Gradients, `gradSchemes Gauss linear`: a gradient is built from face values that are interpolated
linearly between the two cell centres. That is second order and the standard choice. For the
velocity we add `grad(U) cellLimited Gauss linear 1`: the same gradient but clipped so that it
never predicts a face value outside the range of the neighbouring cells. Without it the sharp
edges of the building produce overshoots in the first iterations.

Convection, the `divSchemes` block: this is the choice that decides accuracy, because convection
dominates the flow around a bluff body. `default none` is deliberate: it forces every convection
term to be listed explicitly, so none can silently fall back to first order.
- `div(phi,U) bounded Gauss linearUpwind limited`: momentum uses second-order upwind. Upwind means
  the face value comes from the cell the flow comes from, which is stable; linear means it is
  extrapolated with the gradient, which makes it second order; the gradient used is the limited one
  defined above.
- `div(phi,k)`, `div(phi,epsilon)`, `div(phi,omega)`, all `bounded Gauss limitedLinear 1`: the
  turbulence quantities use a central scheme with a limiter (a TVD scheme). Central is second
  order; the limiter switches toward upwind where the solution is steep so that k and epsilon can
  never go negative, which would crash the model. The 1 is the limiter strength, the usual value.
- The word `bounded` in front of every term subtracts the small continuity error of the current
  iteration from the equation. In a steady run the velocity field is not exactly divergence-free
  until the end, and this correction stops that error from acting like a false source. It helps
  convergence and does not change the converged answer.
- `div((nuEff*dev2(T(grad(U))))) Gauss linear`: the viscous stress term, central; it must be listed
  because of default none.
The AIJ guideline asks that the final result not be computed with first-order upwind, and these
settings meet it.

Diffusion, `laplacianSchemes Gauss linear limited corrected 0.33`: a laplacian needs the gradient
normal to each face. On a perfectly orthogonal mesh that is just the difference between the two
cell values divided by the distance. Our snappyHexMesh mesh has faces that are not perpendicular
to the line between cell centres, up to 26 degrees at the level transitions, and the `corrected`
part adds the missing component; `limited 0.33` caps that correction so it cannot destabilise the
run. This pair is the usual choice for snappyHexMesh meshes. `snGradSchemes` is the same thing for
the surface-normal gradient on its own, and `interpolationSchemes linear` is the plain face
interpolation used wherever nothing more specific is asked.

`wallDist meshWave`: the distance from each cell to the nearest wall, computed once at start.
The SST model needs it in its blending functions, and the y+ monitor uses it.

### C6d. How the systems are solved and the loop controlled: system/fvSolution

What the solver actually does in one SIMPLE iteration: it assembles the momentum equation with the
current pressure and solves it for U; from that U it builds a pressure equation and solves it for
p; it corrects U so that mass is conserved; then it solves the k and epsilon (or omega) equations
with the new velocity. Each of those is a linear system A x = b with one unknown per cell,
292,000 unknowns on the coarse grid. The `solvers` block says how each system is solved; the
`SIMPLE` block says how the outer loop around them is run; `relaxationFactors` says how much of each
new answer is accepted.

The linear solvers. Pressure uses `GAMG`, geometric agglomerated multigrid: the solver builds
coarser and coarser copies of the mesh, solves cheaply on them, and passes the corrections back.
The pressure equation couples the entire domain in one step, which a plain iterative solver handles
only with hundreds of sweeps, and multigrid handles in near-linear time; it is the standard choice
for p on any mesh above a few tens of thousands of cells. `smoother GaussSeidel` is the relaxation
used on each level. U, k, epsilon and omega use `smoothSolver` with the same Gauss-Seidel smoother:
these equations are dominated by convection, their matrices are strongly diagonal, and a few cheap
sweeps per iteration are enough. The alternatives are PCG for pressure (robust, slower, useful on
small meshes or if GAMG misbehaves) and PBiCGStab for the transport equations (more work per sweep,
converges where Gauss-Seidel stalls). The split follows the matrix type: pressure is symmetric, the
transport equations are not.

`tolerance` and `relTol`. The linear solver stops when either is met. `tolerance` is absolute, the
residual below which nothing more is gained: 1e-7 for p, 1e-8 for the others. `relTol` is the
target for this one call: stop when the residual has dropped by this factor since the call began,
0.01 for p and 0.1 for the rest. For a steady SIMPLE run that looseness is right, because the outer
loop will call the solver again next iteration anyway; solving each system to the bone wastes
time and buys nothing. A transient PISO run is different: there is no outer loop to clean up
after the last corrector, so relTol must be near zero there.

`SIMPLE` block. `nNonOrthogonalCorrectors 0`: extra pressure solves per iteration for
non-orthogonal meshes; zero is right below about 50 degrees when the laplacian already carries a
correction, 1 or 2 for 60 to 70 degrees, and above that the mesh should be fixed, not the solver.
`consistent yes` turns SIMPLE into SIMPLEC. Plain SIMPLE drops the neighbour influence when it
corrects the velocity for the new pressure and pays for that with heavy under-relaxation of p,
typically 0.3, with U at 0.7. SIMPLEC keeps part of that influence, so p needs no relaxation and
U can take 0.9; it converges faster to the same answer. `residualControl` lists thresholds; when
every initial residual is below its threshold in the same iteration, the run stops. Ours are
1e-5 for p and 1e-6 for the rest, set a decade tighter than one would stop by eye. It is a
convenience and a safety net; the judgement of convergence is the monitors in controlDict and the
1 percent rule (rule 5), as the 4 m V0 cases showed, which stalled on a p residual of 7e-5 while
the probe was identical to eleven digits.

`relaxationFactors`. The fraction of the new solution accepted each iteration: 0.9 for U, 0.7 for
the turbulence equations. 1.0 means no relaxation and usually diverges in a steady run; 0.5 is slow
but very safe. Relaxation changes the path to the solution, not the solution, so there is no
accuracy penalty in going lower. Rule for choosing: start with these values; if the residuals
oscillate or k blows up in the first hundred iterations, lower the turbulence factors to 0.5 first
and then U to 0.7; if the run is stable but slow, raise them. If a case will not start at all,
switch every convection scheme to upwind for about 200 iterations, then switch back with
`startFrom latestTime`.

### C6e. The alternatives in one table

| Scheme | Order | Character | When to use |
|---|---|---|---|
| upwind | 1 | very stable, very diffusive: smears gradients, shortens wakes, thickens plumes | the first few hundred iterations of a hard case, never the final answer |
| linearUpwind grad(U) | 2 | upwind-biased, stable, modest diffusion | momentum in steady RANS; our choice |
| limitedLinear 1 | 2 | central with a limiter that keeps the variable bounded | k, epsilon, omega, scalars; our choice |
| linear | 2 | pure central, no diffusion, can oscillate | LES, diffusion terms, and aligned flows like the V0 box |
| QUICK | 3 | more accurate, less stable | fine meshes with smooth flow |

| Solver | Use for | Why |
|---|---|---|
| GAMG | p | multigrid, near-linear cost for the equation that couples the whole domain |
| smoothSolver GaussSeidel | U, k, epsilon, omega | cheap sweeps on diagonally strong matrices |
| PCG | p on small meshes or when GAMG misbehaves | robust, slower |
| PBiCGStab | transport equations when smoothSolver stalls | more robust per sweep |

## C7a. Run control and monitors: system/controlDict

- `application simpleFoam`; `deltaT 1` so one time step = one SIMPLE iteration; `endTime 2000` is
  the cap (residualControl may stop earlier); `writeInterval 250` writes all fields every 250
  iterations (restart points, and the last two writes give the flatness check of rule 5).
  `startFrom latestTime` lets a restart continue. `runTimeModifiable yes`: the solver re-reads this
  file every iteration, so endTime can be raised while it runs.
- `functions` = monitors (function objects), each writes under postProcessing/<name>/:
  `probes` of U and k at three measured wake points (the primary convergence quantity: the wake
  settles last); `forces` on the building (convergence monitor only; `rhoInf 1.2` turns p/rho into
  newtons); `surfaceFieldValue` sum of phi on inlet and outlet (mass balance); `fieldMinMax`.
- Why probes in the wake: the recirculating air is slow and the roof separation point wanders for
  many iterations; residuals can be flat while the wake is still moving.

## C7b. Parallel run: decomposeParDict and the run sequence

- GPU: no; the standard solvers are CPU only (Project.md section 10 cost trap).
- Cores: speed-up stops paying below ~20,000 cells per core. 292k cells -> 16 cores (~18k each).
  Check the load first (rule 12): `cat /proc/loadavg`, `nproc`.
- system/decomposeParDict: `numberOfSubdomains 16; method scotch;` (scotch balances cells and
  minimises the interface between pieces; hierarchical/simple need a manual n (nx ny nz)).
- Sequence: `rm -rf 0 && cp -r 0.orig 0` -> `setExprFields` -> `decomposePar` ->
  `mpirun -np 16 simpleFoam -parallel > log.simpleFoam 2>&1` -> `reconstructPar`.
  Watch the log in a second terminal: `tail -f log.simpleFoam`; stop watching with Ctrl+C
  (that stops tail, not the solver).

## C7c. First V1 run (coarse grid, realizableKE, 16 cores, 2026-10-09, run by Saleh)

- 0.3 s per iteration; residualControl met at iteration 397 (cap 2000).
- Probes (rule 5 check) between the writes at 250 and 397: wake-cavity Ux -0.454 -> -0.455 m/s
  (0.2 %), reattachment Ux 0.470 -> 0.469 (0.3 %), drag 0.11027 -> 0.11026 N. Converged.
- Reversed flow at the cavity probe = the recirculation behind the block.
- `tail -f` on /mnt/d can fail ("No data available") because D: is a Windows bridge mount; use
  `watch -n 2 tail -n 12 log.simpleFoam`. Large runs go on native Linux storage for this reason.
- After the run: `reconstructPar -latestTime` (merge the processor pieces),
  `simpleFoam -postProcess -func yPlus -latestTime` (y+ per wall patch; building must be 30..300).

## C8a. Comparing with the tunnel: sampling at the measured points

- validation/V1/make_sample_points.py writes system/samplePoints: a `sets` function object of
  `type cloud` with the 826 measured (x y z), `interpolationScheme cellPoint` (interpolates to the
  exact point), fields U and k. Included in controlDict's functions block, so future runs write it
  at every write time; for an existing result run `simpleFoam -postProcess -func samplePoints -latestTime`.
  Output: postProcessing/samplePoints/<time>/measured_U.xy (x y z Ux Uy Uz) and measured_k.xy.
- validation/V1/metrics.py: hit rate q = fraction of points with |CFD - exp| <= 0.25 |exp| or
  |CFD - exp| <= 0.05 U_H (VDI 3783/9 values), per component. Acceptance q(U) >= 0.66, fixed in
  Project.md section 5. FAC2 and fractional bias for concentration come when the scalar is added.

## C8b. First validation result (coarse grid, realizableKE, measured inlet, run 1, 2026-10-09)

- y+: building min 24, mean 98, max 288 (inside 30..300 except a few bottom-corner faces);
  ground max 414 in the 40 mm far field (outside the window, upstream floor only; noted).
- Sampling: the raw writer puts all fields of one set in one file, columns sorted by field name:
  measured_k_U.xy = x y z k Ux Uy Uz. (The metrics script was corrected for this.)
- Hit rate (VDI 3783/9, D = 0.25, W = 0.05 U_H), 826 points:
  U 0.59 (pass mark 0.66: NOT MET), V 0.68, W 0.71, all components 0.66, k 0.21.
  Reported as it stands; the pass mark does not move (CLAUDE.md rule 4).
- File: results/V1/coarse_realizableKE_run1.json.

## C9. Repeating the run on a finer grid: lessons from the medium-grid attempt (2026-10-09)

- To refine everything by 1.43: change only `dx` in blockMeshDict (0.04 -> 0.028). The snappy
  levels are relative to the background, so nothing there changes. Cells: 168,300 -> 495,962
  background (2.95x), 292,563 -> 843,456 after snapping (2.9x).
- Copy the case before changing it and delete the old run's output in the copy (processor*,
  numbered folders, postProcessing, logs, constant/polyMesh).
- `snappyHexMesh` without `-overwrite` does NOT replace constant/polyMesh: it writes the
  castellated mesh to a folder `1` and the snapped mesh to `2`, as if they were time steps. The
  solver would then start from "time 2". Always `snappyHexMesh -overwrite`, and redirect long
  programs to a log: `snappyHexMesh -overwrite > log.snappyHexMesh 2>&1`.
- Two people (or a person and a script) must not touch the same case folder at the same time.

## C10. Coarse against medium: the first row of the grid study (2026-10-09, medium run by Saleh)

The medium grid has every cell 1.43 times smaller than the coarse one: 843,456 cells against
292,563. It converged at iteration 595 in 6.5 minutes on 16 cores, and the wake-cavity probe was
identical at the last two writes, so it is converged by the 1 percent rule. The building y+ fell
from an average of 98 to 67, by the same factor the cells shrank, because y+ is proportional to
the first cell height; it stays inside the 30 to 300 window.

The score moved very little: hit rate on U 0.59 on the coarse grid, 0.60 on the medium, pass mark
0.66, not met on either. Region by region the picture is the same on both grids:

| Region | Points | Coarse | Medium | Mean CFD minus tunnel, medium |
|---|---|---|---|---|
| upstream | 181 | 0.81 | 0.78 | -0.02 m/s |
| above roof | 25 | 0.64 | 0.72 | +0.05 m/s |
| beside building | 120 | 0.72 | 0.76 | -0.42 m/s |
| near wake, up to 1H | 350 | 0.49 | 0.51 | -0.51 m/s |
| far wake, beyond 1H | 150 | 0.44 | 0.47 | -0.62 m/s |

What that tells us. Refining the mesh by 1.43 changed the wake velocities by a few hundredths of a
metre per second, while the wake is 0.5 to 0.6 m/s too slow on both grids. The error is therefore
not a mesh error: the solution is already close to grid-independent, and the deficit belongs to
the turbulence model. This is the expected behaviour of realizable k-epsilon behind a sharp-edged
block: it under-produces turbulent mixing in the separated shear layers, so the recirculation is
too long and the wake recovers too slowly. A finer grid resolves that wrong answer more precisely;
it does not fix it. The levers that can change the wake are the closure (k-omega SST is the other
candidate in Project.md section 6) and the inflow turbulence (decision 0003 asks for the log-law
inlet as a sensitivity). The grid study is still completed with the fine grid, because the brief
asks for three levels and the grid convergence index needs them, but the expectation is set: it
will confirm grid independence, not pass the validation.

Results: results/V1/coarse_realizableKE_run1.json, results/V1/medium_realizableKE_run1.json.

## C11. The second closure: k-omega SST on the medium grid (2026-10-09, set up and run by Saleh)

Saleh copied the medium case, changed the one word RASModel to kOmegaSST, and ran it; the log
confirms the model and the run started from clean fields. The run behaved differently from the two
k-epsilon runs. It did not meet the residual targets and stopped at the 2000-iteration cap, with
the pressure residual flat at about 9e-4 from iteration 1000 onward instead of falling. The probes
explain why. The wake-cavity probe settled at -0.70 m/s by iteration 750 and stayed within 0.1
percent, and the reattachment probe at 0.267 m/s within 0.6 percent. The roof probe did not settle:
between iterations 1000 and 2000 it cycled slowly between 0.40 and 0.47 m/s, mean 0.436, amplitude
plus or minus 8 percent. That is the roof separation bubble breathing, a known behaviour of SST on
sharp-edged roofs in a steady solver: the model predicts a larger, more unsteady bubble than
k-epsilon, and SIMPLE cannot find a steady state for it. Rule 5 applies: the roof quantity is
reported as cycle average and amplitude, the rest as converged. If a steady run will not settle,
the brief's answer is to run it transient and average (section 6, no URANS stage as a design tool,
but as a numerical necessity).

The sampled result, with y+ on the building averaging 49 (SST computes a smaller wall friction):

| Metric | realizable k-epsilon | k-omega SST | Pass mark |
|---|---|---|---|
| Hit rate on U | 0.60 | 0.62 | 0.66, not met by either |
| Hit rate on V, W | 0.71, 0.71 | 0.71, 0.67 | reported |
| Hit rate on k | 0.22 | 0.29 | reported |

By region the two models fail in different places:

| Region | rKE hit rate | SST hit rate | rKE bias | SST bias |
|---|---|---|---|---|
| upstream | 0.78 | 0.87 | -0.02 | -0.13 |
| above roof | 0.72 | 0.60 | +0.05 | -0.56 |
| beside building | 0.76 | 0.79 | -0.42 | -0.40 |
| near wake | 0.51 | 0.48 | -0.51 | -0.60 |
| far wake | 0.47 | 0.50 | -0.62 | -0.61 |

Reading. Both models leave the wake 0.5 to 0.6 m/s too slow; SST adds a too-large roof bubble (the
roof points are 0.56 m/s slow) and a stronger reversed flow in the cavity (-0.70 against -0.40).
The wake deficit is therefore common to both linear eddy-viscosity closures and is not a mesh
effect (C10). This is the model-form limitation the brief expects RANS to have in a bluff-body
wake, and the reason the ladder includes a scale-resolving run of this same case (V1-LES) to
measure it. Before concluding, the remaining planned runs are the fine grid (grid convergence
index), the inflow sensitivity with the log-law inlet (decision 0003), and the empty-domain drift
check; none of them is expected to move the wake by half a metre per second.

Results: results/V1/medium_kOmegaSST_run1.json.

## C12. The remaining V1 runs and how each was set up (2026-10-09, run by the queue script)

After the three building runs, four more cases close the velocity part of V1 and open the
concentration part. Saleh asked for these to be run and reported in one go. Each is a copy of an
existing case with one deliberate change, which is the pattern for every sensitivity study: change
one thing, keep everything else, so the difference in the result has one cause.

The fine grid (case_fine). Built from the hand-built files with dx = 0.02 m: 2,318,750 cells,
2.75 times the medium grid, same snappy settings, Mesh OK. It completes the three-level grid study
the brief asks for. With three grids the grid convergence index can be computed
(validation/V1/gci.py): from three values of a quantity on grids with a constant refinement ratio
r, the observed order of convergence is p = ln((f_coarse - f_medium)/(f_medium - f_fine)) / ln r,
and the uncertainty of the fine value is GCI = 1.25 |f_medium - f_fine| / |f_fine| / (r^p - 1).
The quantities used are the two wake probes, the drag force and the hit rate.

The inflow sensitivity (case_medium_loglaw). The medium case with the inlet switched from the
measured tables to the V0 log-law family, atmBoundaryLayerInletVelocity, InletK, InletEpsilon,
with the fitted z0 = 11.7 mm and Uref 3.23 m/s at 0.2 m in an include/ABLConditions file, exactly
as in V0. Velocity is the same within 3 percent; k is 0.67 instead of 0.45, 49 percent more
inflow turbulence. The ground stays the smooth wall function, because it is the tunnel floor. Its
purpose is to measure how much of the wake deficit is inflow turbulence rather than model.

The empty-domain drift check (case_empty_medium_realizableKE and _kOmegaSST). The medium case
with the building removed: blockMesh only, no snappyHexMesh, and the building entry deleted from
every field file, since a patch that does not exist in the mesh must not appear in the fields.
The force monitor and the point sampling are removed too, and a sampleProfiles function object
writes vertical lines of U and k at the inlet, at the tunnel measurement station 2.5H upstream, at
1H upstream, at the windward wall position, at the building origin and at 2H downstream. The
comparison is the same as V0: how much the measured inlet profile has changed by the time it
reaches where the building would be. This is safeguard 1 of decision 0003.

The tracer (case_medium_scalar). The converged medium-grid realizable k-epsilon flow, continued
for 500 more iterations with residualControl removed, so the flow is effectively frozen while six
passive scalars are solved on it by the scalarTransport function object, one per turbulent Schmidt
number from 0.4 to 0.9. Each scalar is a volume fraction with diffusivity D = nu + nut/Sct, a
source of Q = 5.83e-6 m3/s placed in the cell containing the floor hole, clean air at the inlet
and zero flux through every wall. The dimensionless concentration C* = c U_H H^2 / Q is compared
with the tunnel on points where the measured concentration exceeds the 1 ppm noise floor, with
FAC2 and fractional bias as the metrics. All of this is decision 0004, written for Saleh to
confirm or revoke. In OpenFOAM terms, a function object that solves an equation lives in
controlDict like any monitor; its field files sit in the restart time folder (595/s04 and so on),
its convection scheme is div(phi,s) in fvSchemes through the schemesField entry, and its linear
solver is the "s.*" entry in fvSolution. The source is an fvOptions block inside the function
object with selectionMode points and volumeMode absolute, meaning the number given is the total
rate in field units times cubic metres per second.

## C13. The fine grid and the grid convergence index (2026-10-09)

The fine grid, 2,318,750 cells, converged at iteration 985 in 22 minutes on 16 cores, with the
wake-cavity probe flat to 0.2 percent between the writes at 750 and 985. Building y+ averages 45
with a minimum of 3 on a few corner faces: the finer the cells, the lower y+, and on the next
refinement the wall-function assumption would start to break at the corners. This is the practical
floor of the wall-function approach on this geometry.

The hit rate on U moved from 0.59 to 0.60 to 0.61 across the three grids. The grid convergence
index (validation/V1/gci.py, Celik et al. 2008) with a mean refinement ratio of 1.41:

| Quantity | coarse | medium | fine | observed order p | GCI of the fine value |
|---|---|---|---|---|---|
| wake-cavity probe Ux, m/s | -0.455 | -0.399 | -0.385 | 3.9 | 1.6 % |
| reattachment probe Ux, m/s | 0.469 | 0.641 | 0.772 | 0.8 | 66 % |
| drag force, N | 0.1103 | 0.1157 | 0.1164 | 5.8 | 0.1 % |

How to read this. The drag and the cavity velocity are grid-converged: the three values approach
a limit at a high observed order and the remaining uncertainty is small. The reattachment probe
is not: at that point, 1.5H behind the building at half height, the velocity keeps rising with
refinement at first order, which means the end of the recirculation zone is moving upstream as the
mesh gets finer. A GCI of 66 percent is not a defect of the index; it is the index doing its job,
saying that a single-point value in a steep gradient on the edge of the recirculation is not
resolved on these grids. The point-by-point hit rate, however, barely moves, because the wake is
too slow by 0.5 to 0.6 m/s on every grid:

| Region | hit rate coarse / medium / fine | bias coarse / medium / fine, m/s |
|---|---|---|
| upstream | 0.81 / 0.78 / 0.77 | -0.05 / -0.02 / -0.02 |
| above roof | 0.64 / 0.72 / 0.72 | +0.03 / +0.05 / +0.12 |
| beside building | 0.72 / 0.76 / 0.78 | -0.45 / -0.42 / -0.41 |
| near wake | 0.49 / 0.51 / 0.52 | -0.53 / -0.51 / -0.47 |
| far wake | 0.44 / 0.47 / 0.47 | -0.68 / -0.62 / -0.58 |

So the picture from C10 stands with one refinement: the recirculation length does shorten with
grid resolution, by a few percent per level, but extrapolating the trend would not close a half
metre per second gap, and the hit rate would need a different model to reach 0.66. Results:
results/V1/fine_realizableKE_run1.json and results/V1/gci_realizableKE.json.

## C14. Inflow sensitivity and the empty-domain drift check (2026-10-09)

Inflow sensitivity. The same medium case with the log-law inlet family instead of the measured
tables, so with 49 percent more inflow turbulence, converged at iteration 1255 with the probes
flat from 750. The hit rate on U rose from 0.60 to 0.63, still short of 0.66, and the wake bias
shrank from -0.51 to -0.38 m/s in the near wake and from -0.62 to -0.44 in the far wake. The roof
went the other way, from +0.05 to +0.19 m/s, because more inflow turbulence shortens the roof
bubble too. So inflow turbulence is part of the wake story, worth about a quarter of the deficit,
and the measured value, being the tunnel's, is the right baseline; the difference between the two
runs is the inflow contribution to the uncertainty band that Project.md section 7 asks for.

Empty-domain drift check. The same box without the building, measured inlet, realizable
k-epsilon, 2000 iterations with the profile at the windward-wall position flat to 0.5 percent in U
between the last two writes. Above z = 0.075 m the profile is maintained: at the tunnel station
2.5H upstream the CFD velocity matches the measurement within 0.05 m/s at every height from 0.075
to 0.6 m, and k within 0.05 m2/s2 at roof height. Below 0.075 m it is not: the measured profile has
0.65 m/s at 10 mm and 1.13 m/s at 25 mm, while the CFD has 1.8 to 2.0 m/s there. The reason is the
floor. The tunnel's near-floor deficit was created by roughness elements upstream of the test
section; our floor is a smooth wall function that knows nothing about them, so it accelerates the
lowest cells toward a smooth-wall profile over the 5H fetch. Measured in the same way as V0, the
maximum relative change below 3H is 29 percent at the tunnel station and 40 percent at the
windward-wall position, all of it in the first cell. This is a real inconsistency between the
inlet and the floor, of the kind entry 7 warned about, and 312 of the 826 measured points sit at
2.5 mm above the floor, inside it. Decision 0005 adds one sensitivity run with the rough-wall set
on the floor at the fitted z0 of 11.7 mm, queued behind the tracer.

### C14 addendum: the empty-domain check for both closures, and a tracer lesson

With the first cells excluded (z above 0.075 m), both closures keep the measured velocity profile
within 3 to 4 percent all the way to the building position. k is another matter: it decays by
about 13 percent at roof height over the 5H fetch with both models, 0.453 at the inlet to 0.393
at the building position, and by 20 to 23 percent at its worst height. The measured k profile is
not an equilibrium solution of either model with Cmu = 0.09, which is the same mismatch entry 13
predicted from the stress-to-k ratio: the model dissipates the tunnel's turbulence faster than
the tunnel did. Both numbers, the 3 percent on U and the 13 percent on k at roof height, go into
the V1 record as the inflow part of the uncertainty; they are not corrected for, because any
correction would be tuning.

The tracer run crashed on its first scalar solve with a floating point exception. The serial test
without exception trapping showed the linear solver diverging to NaN within one call. Cause: the
scalarTransport function object applies under-relaxation only if fvSolution lists a factor for
its schemesField name, and none was listed, so the steady convection-diffusion matrix was solved
unrelaxed; without relaxation that matrix is not diagonally dominant and Gauss-Seidel diverges.
Fix, recorded in the case: a relaxation factor of 0.7 for s under relaxationFactors.equations,
and PBiCGStab with DILU instead of the smoothSolver for the tracers. A two-iteration serial test
then showed the residuals falling by two orders per call. Two general lessons: every transported
quantity in a steady run needs a relaxation factor, including ones added by function objects; and
when a run dies with a signal, rerun it serially with FOAM_SIGFPE=false to see the numbers instead
of a stack trace.

## C15. The rough-floor sensitivity: a clear negative (2026-10-09)

Decision 0005 asked whether a rough floor at the fitted z0 of 11.7 mm would hold the tunnel's
near-floor velocity deficit better than the smooth wall. The answer is no, and strongly so. With
the rough-wall set on the whole floor the hit rate on U fell from 0.60 to 0.34. The lowest
measurement plane, 2.5 mm above the floor, dropped from 0.51 to 0.05, and the upstream region from
0.78 to 0.44 with a bias of -0.40 m/s; the wake became slower still. The roof plane at z/H = 0.5
was unaffected (0.69 against 0.77).

Why. The z0 fitted to the approach flow describes the roughness elements upstream of the test
section, which built the boundary layer over a long fetch. The test-section floor itself is
smooth, and the measurements at 2.5 mm sit in a thin smooth-wall layer that re-forms quickly on it.
Putting the upstream roughness under the model drags the whole lower flow down by 0.4 to 0.8 m/s
everywhere. The right description is the one in decision V1-2: measured profile at the inlet,
smooth floor, and the near-floor inconsistency of C14 accepted and reported as it is. The
sensitivity is kept in the record as evidence for that choice, not as a candidate.
Result: results/V1/medium_realizableKE_roughfloor_run1.json. The smooth floor remains the baseline.

## C16. The tracer: first pass and the balance check (2026-10-09)

The six tracers ran for 500 iterations on the converged flow in 4.5 minutes. The first scores
looked encouraging: FAC2 of 0.60 at Sct = 0.4 falling to 0.47 at 0.9, with a fractional bias of
-0.53 to -0.82, meaning the CFD concentrations average 1.7 to 2.3 times the measured ones. But
before reading anything into that, the balance check of rule 5 was applied: the tracer flux leaving
the outlet, computed from phi times s over the outlet faces, was only 62 percent of the injected
Q at Sct = 0.4 and 91 percent at 0.9. A converged passive scalar with no sinks must leave at
exactly the rate it enters. The run was therefore not converged, and the FAC2 and FB numbers from
it are not results.

Why 500 iterations was too few. In a steady solver the scalar is not marched in time; each
iteration relaxes the field toward the solution of the transport equation, and with a factor of
0.7 the information about the source spreads across the domain over many iterations. The lower
the Schmidt number, the more diffusive the plume, the larger the volume it fills, and the longer
it takes. The velocity residuals say nothing about this, because the velocity was converged
before the tracers started.

What was changed. The run continues from iteration 1095 for 2500 more, with two monitors added
to controlDict: a surfaceFieldValue on the outlet with weightField sXX, which writes the tracer
flux every iteration, and the six tracers added to the wake probes. Convergence is then judged
on the outlet flux reaching Q within 1 percent and the probe values being flat, exactly as for the
velocity. The scalarTransport entry resetOnStartUp was set to false so the continuation keeps the
fields instead of zeroing them. General lesson: every transported quantity gets its own balance
and its own monitor; a scalar added by a function object is no exception.

## C17. The tracer result (2026-10-09)

With 3000 iterations the tracers are converged by every test: the outlet flux equals the injected
Q within 0.05 percent for all six Schmidt numbers from iteration 2600 on, having been 62 to 91
percent at 500 iterations, and the tracer values at the three wake probes changed by less than
0.002 percent over the last 500 iterations. The scores on the 490 points where the tunnel
measured more than 1 ppm:

| Sct | FAC2 | FB | MG | pass |
|---|---|---|---|---|
| 0.4 | 0.57 | -0.56 | 1.20 | FAC2 met, FB not met |
| 0.5 | 0.55 | -0.65 | 1.22 | FAC2 met, FB not met |
| 0.6 | 0.51 | -0.71 | 1.21 | FAC2 met, FB not met |
| 0.7 | 0.50 | -0.76 | 1.19 | FAC2 marginal, FB not met |
| 0.8 | 0.48 | -0.80 | 1.16 | not met |
| 0.9 | 0.47 | -0.83 | 1.13 | not met |

Reading the two bias measures together. FB is the fractional bias of the arithmetic means, and
it is dominated by the high-concentration points near the source: negative FB means the CFD mean
is higher, here 1.8 to 2.3 times the measured mean. MG is the geometric mean of the point ratios
and says what a typical point does: the CFD is 13 to 22 percent high. So most points are close and
a few near-source points are far too high. Where, by region at Sct 0.4: the far wake beyond 1H is
excellent, FAC2 0.90 and FB +0.07; the near wake within 1H has the CFD mean 1.8 times the measured;
and the points beside and above the building have it 3.5 times too high. On the centre plane the
CFD mean is 2.5 times the measurement. The picture is the velocity story seen from the scalar
side: the recirculation behind the block is too long and too strong, so the tracer released into
it accumulates there and is carried up the leeward wall and around the sides instead of being
swept downstream and spread laterally. Where the flow is right, beyond 1H, the concentration is
right too.

On the Schmidt number. Lower Sct means more turbulent diffusion of the scalar, and it improves
every metric here because it partly compensates the missing mixing of the flow model. That is
exactly why a Sct fixed on V1 alone would be a tuned number: 0.4 looks best because the wake is
wrong. Project.md section 6 fixes one value from V1 and V2 together; V2 has a rooftop stack with
momentum, a different flow, and will say whether 0.4 is a property of the scalar closure or a
patch on this wake. The whole sweep is kept as the Schmidt sensitivity band.
Results: results/V1/tracer_report_medium_realizableKE.json, results/V1/summary.md.

## 14. V2: what the Concordia rooftop-stack experiment measured (2026-10-12) (story step 7, V2 starts)

Source: IRSST report R-848, Stathopoulos, Hajra, Chavez and Bahloul (2014), "A wind tunnel study of
the effect of adjacent buildings on near-field pollutant dispersion from rooftop emissions".
Licence CC BY-NC-ND 4.0; the PDF stays out of the repository, digitised values are published as
derived data with citation (data/raw/SOURCES.md).

The report is mostly about neighbouring buildings. Our V2 case is its reference, Configuration 1,
the isolated emitting building B1, which appears as a curve in several figures. That is enough,
and it is exactly the brief's question: how does roof-level dilution depend on stack height and
exhaust momentum.

The tunnel and the approach flow. Concordia's boundary-layer wind tunnel, 1.8 m square section,
12.2 m long, spires and 5 cm cube roughness elements upstream. The flow is an urban boundary
layer: power-law exponent 0.31, roughness length 3.5 mm at model scale, gradient height 95 cm,
gradient speed 14.2 m/s, speed at building height U_H = 6.2 m/s, friction velocity about 1 m/s,
turbulence length scale 40 cm. The measured velocity and turbulence-intensity profiles are in
Figure 3.1 (pdf page 26), compared with ESDU 1974; they must be digitised for the V2 inlet, as the
Case H table was used for V1. Repeatability of the concentration measurements is quoted as
plus or minus 15 percent; the gas chromatograph precision is 5 percent.

The building and the stack. Scale 1:200. B1 is 15 m high, 50 m wide and 50 m long at full scale,
so 7.5 cm by 25 cm by 25 cm in the tunnel, a flat-roofed box like our data hall in proportion
(ours is 15 by 40 by 60 m). The stack is 3 mm in diameter (0.6 m full scale, the same as our
flues), placed on the roof centreline either at the upwind edge, Xs = 0, or 20 m downwind of it.
Stack height hs is 1, 3 or 5 m full scale (0.5, 1.5, 2.5 cm model). The exhaust momentum ratio
M = Ve/U_H is 1, 2 or 3; the exhaust is non-buoyant, so this is the only exhaust parameter. The
building Reynolds number is about 31,000 on H and U_H; the stack Reynolds number is 1,900, a
little below the usual criterion of 2,000, which the authors argue does not affect the
concentration results. Wind azimuth 0 degrees for all data shown.

What was measured. Tracer gas (SF6 in nitrogen) released from the stack; one-minute samples
drawn through tubes at receptors on the roof centreline, downwind of the stack, at roughly 5 m
intervals to 50 m, plus walls in the adjacent-building cases. Results are reported as normalised
dilution, equation A.13 of the report:
```
D_N = D_r Q / (U_H H^2),   D_r = C_e / C_r
```
where C_e is the exhaust concentration, C_r the receptor concentration, Q the exhaust volume flow
and H the building height. D_N is dimensionless, so tunnel and CFD compare directly, and a higher
value means cleaner air at the receptor. Typical values on the roof of the isolated building are
0.3 to 3 at hs = 1 m and M = 1, and 1 to 10 at M = 3; dilution increases with distance from the
stack because the plume rises and spreads.

Where the isolated-building data are. Configuration 1 curves exist for: hs = 1 m, Xs = 0, M = 1
and 3 (Figures 4.3, 4.4, E2, and 5.1 for M = 3); hs = 3 m, Xs = 0, M = 1 and 3 (Figure D2);
hs = 1 m, Xs = 20 m, M = 1 and 3 (Figure 4.1); hs = 3 m, Xs = 20 m (Figure E1). The hs = 5 m
case is mentioned in the text but no isolated-building curve for it was found in the figures.

What V2 must reproduce, from Project.md section 5: the correct ranking of stack heights (hs = 1
against 3 m, at Xs = 0 and M = 1 and 3), and FAC2 of at least 0.5 on the roof receptors. The
ASHRAE 2011 model is the second reference: the report shows it under-predicting the tunnel
dilution by a factor of about 5 near the leeward edge.

The step that comes first. The report gives curves, not tables, so the roof dilutions and the
approach-flow profile must be digitised from the figures. Digitising adds its own uncertainty on
top of the tunnel's 15 percent, and the record must say how it was done: which figure, which
curve, how many points, and a check of a few points read independently.

## 15. Digitising a published figure, and checking that you did it right (2026-10-12) (story step 7)

The R-848 report gives its results as charts, not tables, so the tunnel data for V2 had to be read
off the figures. This is common in validation work and it is where quiet errors enter, so the
method is written down here with its checks.

The method. The PDF pages were rendered at 300 dots per inch with Ghostscript. For each chart the
plot frame was found as the rectangle of dark pixels; in these Excel charts the frame edges are the
axis limits, x from 0 to 50 m and y from 0.001 to 1000 on a logarithmic scale, which is six decades,
not seven, an arithmetic slip that was caught by the next check. The chart's own horizontal axis
line, drawn at a dilution of 1, was then located and converted with the calibration: it must come
out as 1.00, and it did in every crop. The series of interest, Configuration 1, is drawn in navy
with diamond markers. Where it is the only navy series (Figure 5.1) each diamond was located as the
widest group of navy columns and its centre taken as the point. Where other navy series share the
chart (Figures 4.4 and D2, dotted lines with smaller markers), the solid line was tracked from left
to right, choosing at every ambiguity the run that continues as a solid line over the next columns,
and read at the receptor spacing of 5 m. Every extraction wrote an overlay image with red crosses at
the extracted points, and each overlay was looked at; three of the first attempts were wrong in
ways that were obvious in the overlay (a legend symbol taken as a point, a dotted series followed
for five points, a crossing at the last point) and would not have been obvious in the numbers.

The checks. The same case appears in two figures, hs = 1 m and M = 3 in Figures 5.1 and 4.4b;
the two readings agree within 2.6 percent at every receptor from 5 to 50 m, which is taken as the
digitising uncertainty and sits well inside the tunnel repeatability of 15 percent quoted in the
report. The measured velocity profile, read from Figure 3.1, follows the power law quoted on the
chart, exponent 0.31 and gradient height 95 cm, within 3 percent above 10 cm and within 7 percent
in the crowded band near the floor where markers overlap and only their centroid can be read.

What the data say before any CFD. At every receptor the 3 m stack dilutes more than the 1 m stack
at the same momentum ratio, and M = 3 dilutes more than M = 1 at the same height; the ranking
that V2 must reproduce is in the data. Dilution grows with distance from the stack because the
plume rises and spreads. The velocity at building height from the profile is 6.5 m/s against the
6.2 m/s in the report's table, a 4 percent difference, which is within the reading uncertainty of
the merged markers.

Two things the report itself gets inconsistent, recorded in the data folder's README: its text
says the ESDU velocity estimate is 1.2 times the tunnel data between 10 and 60 cm while its figure
shows the opposite ordering, and the hs = 5 m isolated case appears in the test matrix but in no
isolated-building figure. Files: data/digitised/irsst_r848/, scripts validation/V2/.

---

# Part D. Building V2 by hand: the rooftop stack (started 2026-10-12)

Same format as Part C. The case is validation/V2/case_by_hand; decision record 0007 lists every
setup choice and its reason.

## D0. What this simulation is, and the plan

The experiment, in one picture: wind over a wide flat-roofed box in a wind tunnel, a thin pipe at
the upwind edge of the roof blowing tracer straight up, and sample points along the roof behind
it. The question is how much cleaner the roof air gets with distance, and how that changes when
the pipe is taller or blows harder. In the tunnel the box was 7.5 cm high and 25 cm square, the
pipe 3 mm across, the wind 6.2 m/s at roof height; we simulate exactly that size, because a
tunnel model obeys the same equations as the full-scale hall only if the Reynolds number is high
enough, and V2b later repeats the case at full scale to show that it is.

What happens in the flow. The approach wind separates at the upwind roof edge and forms a
recirculation bubble on the roof. The stack exit sits inside or just above that bubble. At M = 1
the exhaust leaves at wind speed, is bent over at once and partly trapped in the bubble, so roof
concentrations are high and dilution low. At M = 3 the jet rises clear of the bubble before
bending, so the roof sees far less. A taller stack does the same thing by geometry. The CFD has to
get three things right for the ranking to come out: the bubble height, the jet rise, and the
mixing of the plume into the roof flow. V1 told us the first and third are where RANS is weak.

The plan, the same eight steps as Part C, with what is new in each:
1. Box of air (blockMesh): same as V1 but at the tunnel scale and wider, because the building is
   3.3 times wider than it is tall and blockage must stay below 3 percent.
2. Building and stack (STL, surfaceFeatureExtract, snappyHexMesh): two shapes now, and the stack
   needs cells of 0.3 mm, so the refinement is nested: 5 mm on the building, finer boxes stepping
   down to 0.3 mm around the pipe. The stack top is a patch of its own: it is an inlet, not a wall.
3. Patches: inlet, outlet, floor, building, stack walls, stack exit, top, sides. Eight.
4. Boundary conditions: the stack exit is a second inlet with a fixed velocity straight up and a
   tracer concentration of one. Everything else as V1.
5. Initial guess, 6. physics and numerics, 7. monitors and run: as V1, with the tracer solved in
   the same run as the flow this time, because the source is a boundary, not a volume term, and
   the plume is part of the flow near the stack.
8. Compare: D_N at the roof receptors against the digitised curves; ranking and FAC2.

Four runs: stack height 1 and 3 m by momentum ratio 1 and 3; Saleh builds the first (hs = 1 m,
M = 3, the Figure 5.1 case), the other three are copies with two numbers changed.

## D1. The box of air at tunnel scale (Saleh, 2026-10-12)

Same file as C1 with eight numbers changed: H = 0.075 m; x from -0.625 (inlet 5H upwind of the
windward wall at -0.25) to 1.125 (15H downwind of the leeward wall at 0); y from -0.575 to 0.575
(6H beyond the building faces at +-0.125); z to 0.6 (8H); background cell 20 mm. The sides and top
are further away than in V1 because the building is 3.3 times wider than it is tall, and the
blockage, building frontal area over domain cross-section, must stay below 3 percent: 0.25 x
0.075 over 1.15 x 0.6 is 2.7 percent. Result: 150,480 cells, Mesh OK.

One trap met on the way: the controlDict copied from V1 was the finished one, with the monitors
block that includes a file that does not exist yet in V2, and blockMesh refused to start because
every OpenFOAM program reads controlDict first. The monitors block was removed; V2 gets its own at
step 7. Lesson: when copying a case, copy the placeholder versions of system files, or strip the
functions block before meshing.

## D2a. Two shapes: the building and the stack

The building is the same box script as V1 with new numbers. The stack is new: a vertical cylinder
3 mm across, whose side is a wall and whose top disc is where the exhaust enters the domain. Those
must be two different patches, so the script geometry/make_cylinder_stl.py writes two STL files,
<name>_wall.stl for the side and <name>_exit.stl for the top. The cylinder is open at the bottom,
because it stands on the roof inside the building, where there is no fluid. 48 segments around the
circumference make a 3 mm circle smooth enough for 0.3 mm cells.

## 16. Reference: mesh sizing rules for external flow around buildings (2026-10-12)

For any bluff body of height H. Sources: AIJ guidelines (Tominaga et al. 2008), COST 732 best
practice (Franke et al. 2007), Project.md section 7, and our own V0/V1 runs.

| Region | Feature | Extent to cover | Cells across it |
|---|---|---|---|
| Domain upstream | undisturbed approach | 5H from the windward face | |
| Domain downstream | wake recovery, outlet | 10H minimum, 15H better | |
| Domain sides and top | blockage below 3 % | 5H each, more for wide bodies | |
| Building surfaces | edge separation | the surfaces | at least 10 per side (AIJ), 15 to 20 better |
| Near-building box | roof bubble, side vortices, near wake | 0.5 to 1H beyond each face, 1H above the roof | 15 to 20 per H (bubble 0.2 to 0.3H thick needs 5+) |
| Wake box | recirculation and recovery | 3 to 5H behind the leeward face (low wide box), 2 to 3H high | 8 to 10 per H |
| Jet or plume near source | jet bending over | source to 1.5 to 2H downstream, a few diameters wide | 10 across the exit diameter (brief); 5 is the floor |
| Scalar path to receptors | plume along the receptor line | whole receptor line, as narrow as the plume | 20 to 30 per H in height |
| Ground far field | approach-flow layer | everywhere | first cell by y+ or y/z0 (entries 7, 8) |
| Level transitions | mesh quality | between every two levels | 2 to 3 cells per level; growth ratio under 1.3 |

Principles: the smallest feature in each region sets its cell size; budget = volume / cell^3, and
each level costs 8x per volume, so boxes must shrink by more than 2 in every direction per level;
write the budget into the dictionary. The rules are verified for a given case by the three-level
grid study (ratio about 1.4) and the y+ report, never assumed.

## D2b. How an OpenFOAM program knows what to do, and the V2 mesher files

How the programs find their input. OpenFOAM is a few hundred small programs in one folder of
the installation; `source ~/opt/openfoam2606.sh` puts that folder on the shell's search path, so
typing a program's name runs it like any command (`which snappyHexMesh` shows the file). No program
takes the mesh or its settings as arguments. Each assumes it is started inside a case folder and
reads fixed names from fixed places: system/controlDict first, always; then its own dictionary,
named after itself, system/<program>Dict; then the inputs that dictionary names, STL files in
constant/triSurface, the mesh in constant/polyMesh. Outputs go to fixed places too. That is why
the folder names 0, constant and system and the dictionary names are not free. To find out what a
program wants: `<program> -help` for its options, `<program> -doc` for its source documentation,
and the tutorials under $FOAM_TUTORIALS for a working dictionary to copy from.

The two mesher dictionaries for V2. surfaceFeatureExtractDict has three entries, one per STL. The
building gives its 12 edges. The pipe side is a 48-facet cylinder whose facets meet at 172 degrees,
so nothing on it counts as sharp; its top rim does, because the side file and the exit file end
there and `openEdges yes` collects that open rim; the rim is where the jet leaves, so it must stay
a clean circle. snappyHexMeshDict names three surfaces that become three patches: building and
stack_wall of type wall, stack_exit of type patch, because it is an inlet and must not get wall
functions. This is the first time a patch type is set inside the mesher file rather than in
blockMeshDict.

The refinement boxes, with the reasoning behind each number (H = 0.075 m, background 20 mm,
level n = 20 mm / 2^n):
- wakeBox, level 1, 10 mm. The wake behind a low wide box reattaches 3 to 5H behind the leeward
  wall and V1's was still recovering at 2H; 5H is 0.375 m, rounded up to 0.6 m because 10 mm cells
  are cheap. It starts 1H ahead of the windward wall (-0.35), reaches 2.7H high (0.2 m) to hold the
  roof bubble and the rising jet, and 1H beyond each side (+-0.25). 0.095 m3 at 10 mm: 95,000 cells.
- nearBox, level 2, 5 mm. The building itself: 15 cells per H; half an H of margin beyond the
  walls (x -0.30 to 0.10, y +-0.17) and almost one H above the roof (z to 0.14). About 150,000.
- roofBox, level 3, 2.5 mm. The plume along the roof at receptor height: the whole roof length,
  +-0.05 m wide because the receptor line is at y = 0 and the plume is a few centimetres wide, from
  just below the roof to half an H above it. About 83,000.
- plumeBox, level 4, 1.25 mm. The jet bending over, from the stack to 1.5H downstream. About 70,000.
- stackBox, level 5, 0.625 mm, and pipeBox, level 6, 0.31 mm: the jet. Ten cells across the 3 mm
  exit is the brief's rule, level 6; the box is a centimetre across because 0.3 mm cells cost
  30,000 per cubic centimetre. Level 5 is the stepping stone around it.
Principle: each level costs eight times more per volume, so the boxes must shrink by more than a
factor of two in every direction per level; the budget is written in the file's header comment.
`nCellsBetweenLevels 3` makes the staircase from 0.3 mm to 20 mm about twenty cells long.

Commands (case folder, OpenFOAM loaded): `surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1`,
`snappyHexMesh -overwrite > log.snappyHexMesh 2>&1`, `checkMesh > log.checkMesh 2>&1`. Check:
cells per level against the budget, "Finished meshing without any errors", eight patches in
constant/polyMesh/boundary, Mesh OK. Then a slice at y = 0 in ParaView through the stack to see the
six cell sizes closing in on the pipe.

## D2c. snappyHexMeshDict: what is decided per case and what is left alone

Decided for every case (the top third of the file): the shapes in `geometry` and the refinement
boxes (sizes from entry 16); the level and patch type of each surface in `refinementSurfaces`
(cells across the smallest feature of that surface; wall for solids, patch for inlets and
outlets); one `features` line per edge file at the same level as its surface; the level of each
box in `refinementRegions` from the cell budget; `locationInMesh`, a point in the air, moved when
the geometry moves; `nCellsBetweenLevels` 3 unless cost forces 2; the three switches at the top,
with `addLayers` on only when the wall treatment needs a controlled first-cell height.

Left at standard values unless the log says otherwise: `maxLocalCells` and `maxGlobalCells`
(raise if refinement stops at the limit); `resolveFeatureAngle` 30 (lower to 20 for curved
surfaces that come out faceted); the `snapControls` iteration counts (raise if faces remain
unsnapped or edges look rounded); `meshQualityControls` (only `minVol` must be set below the
smallest cell volume, 1e-16 for 0.3 mm cells; the rest only when snapping fails and the log names
the limit); `addLayersControls` only if layers are on.

Procedure: list the shapes; patch type per surface; level per surface from its smallest feature;
boxes from the outside in with their budget; the point in the air; run; the three checks (cells
per level, "Finished meshing without any errors", patches and Mesh OK). If quality fails, grow the
box around the failing region or raise nCellsBetweenLevels first; touch the quality limits last.
