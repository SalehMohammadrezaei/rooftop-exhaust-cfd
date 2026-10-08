# Project Brief v1.0: Rooftop Exhaust and Heat Re-entrainment at a Data-Centre-Type Facility

Oct 7, 2026 · @Saleh

## 1. Purpose and decision question

The study answers one design question: for a data-centre-type hall with rooftop chillers and standby generator flues, which flue height and plant-screen arrangement keeps generator exhaust dilution at the fresh-air intake, and chiller inlet temperature rise, within stated limits for all wind directions at the governing wind speeds?

The second purpose is to show a defensible external-CFD process: ABL setup, verification, validation against wind-tunnel data, stated uncertainty and automated runs. That process is what transfers to wind, dispersion, thermal and general aerodynamics roles.

The intended reader is an experienced CFD engineer reviewing a portfolio. Anything that does not serve the decision or the evidence behind it is out of scope.

## 2. Scope and deliberate exclusions

In scope: external flow around one isolated hall in a neutral atmospheric boundary layer, dispersion of exhaust with source momentum, thermal re-ingestion in the passive limit with a limited buoyant check, and one scale-resolving run on a validation case.

Out of scope, and stated as such in the report:

- Structural wind loading, peak pressures and building force coefficients as deliverables. Forces are a convergence monitor only.
- Internal data-hall airflow, pedestrian wind comfort, acoustics, fire and smoke.
- Non-neutral atmospheric stability, humidity, wet cooling and visible plumes.
- Neighbouring buildings and terrain (stretch goal only).
- Any real site or proprietary layout, and any claim of regulatory air-quality compliance.
- Fan-blade, coil or louvre-blade resolved models.

## 3. Scenario and geometry

A generic single data hall with rooftop air-cooled chillers, standby generator flues at one end and a rooftop fresh-air intake between them. Origin at the building centre on the ground; x along the long axis, positive towards the flue end. The layout is symmetric about the long axis, so wind directions 0 to 180 degrees cover the full rose.

| Element | Definition | How it is modelled |
| --- | --- | --- |
| Hall | 60 m (x) by 40 m (y) by 15 m high, flat roof, sharp edges, isolated | Smooth walls with wall functions |
| Parapet | 1.2 m high around the roof perimeter | Zero-thickness baffle |
| Chiller compound | 10 units in 2 rows of 5, centred at x = -12 m. Unit envelope 12 m (y) by 2.4 m (x) by 2.5 m high, 4.5 m pitch in x, 3 m gap between rows | Solid boxes. Intake on the two long side faces as fixed-flow sinks. Discharge on top through a strip sized to the total fan area, so mass flow and momentum flux are both right |
| Generator flues | 4 vertical flues, 0.6 m diameter, 2 m apart in y, 5 m in from the positive-x parapet. Baseline tip 3 m above the roof | Cylinders with a fixed-flow exit. Isothermal in the MVP with the momentum ratio matched |
| Fresh-air intake | Rooftop plant enclosure 6 m by 4 m by 3 m high at x = +12 m, with a 3 m by 1.5 m louvre on each side face | Solid box. Each louvre is a fixed-flow sink |
| Plant screen (variant only) | 4 m high around the chiller compound, 2 m clear of the units. Solid, or 50 percent free area | Baffle, or porous baffle with a loss coefficient from a published correlation |

Indicative equipment values, to be replaced with public datasheet values and cited: about 90 m3/s and 12 K air temperature rise per chiller (roughly 1.3 MW rejected), fan discharge 7 to 9 m/s; generator flue exit 25 to 35 m/s at 450 to 500 C.

Operating mode: all chillers at design flow and all four generators running. The generators-off case comes for free from the tagged-scalar method in section 4.

Omitted on purpose: fan blades and swirl, coil geometry, pipework, cable trays, stairs, support steelwork, louvre blades, facade detail, generator radiator airflow, flue routing below roof level.

## 4. Operating and boundary conditions

| Item | Setting |
| --- | --- |
| Approach flow | Neutral log-law ABL, roughness length z0 = 0.3 m (suburban or industrial estate), reference speed U\_H at roof height 15 m |
| Wind speeds | U\_H = 3 and 10 m/s for the sweep; 6 and 14 m/s added at the governing directions to locate the critical speed |
| Wind directions | 0 to 180 degrees in 30 degree steps (7 runs give 12 sectors by symmetry). 0 degrees blows along +x, chillers upwind of the flues |
| Direction change | Rotate the building assembly inside a fixed domain and remesh by script, with refinement regions that rotate with it |
| Domain | About 8H upstream, 20H downstream, 10H each side, 9H high. Blockage below 3 percent at the worst angle |
| Inlet | OpenFOAM atmospheric boundary layer profiles for U, k and epsilon or omega |
| Ground | Rough-wall function consistent with z0, with a documented treatment of the near-building strip where the mesh is finer than z0 allows |
| Top and sides | Slip or fixed-shear, chosen by the empty-domain test |
| Outlet | Fixed pressure |
| Sources and sinks | Fixed volume flow on every chiller intake, chiller discharge, flue exit and fresh-air louvre |

Dimensionless groups reported for every run: building Reynolds number, momentum ratio M = exit speed / U\_H for flues and chillers, and a densimetric Froude number for each discharge.

Tagged scalars: solve one passive scalar per chiller discharge and one for the flue group on the converged, frozen flow field. This gives a source-to-receptor matrix F, where F\_ij is the fraction of intake air at receptor i that came from source j.

Thermal result in the passive limit: with each chiller adding a fixed temperature rise to whatever it ingests, inlet temperature rise follows from F by linear algebra, including the feedback of re-ingested air. No energy equation is needed for this step.

## 5. Validation ladder

Each step tests one piece of physics the applied case depends on. Acceptance numbers are fixed before the runs and reported whether met or not.

| Step | Case | What it tests | Data | Stage | Acceptance |
| --- | --- | --- | --- | --- | --- |
| V0 | Empty domain | ABL profiles hold from inlet to the building position | None needed | MVP | U and k change by less than 5 percent below 3H |
| V1 | [AIJ Case H](https://zenodo.org/records/15429872): isolated 1:1:2 building, near-ground point source, neutral | Separation, wake recirculation and scalar transport in a building wake | Open wind-tunnel dataset, velocity and concentration | MVP | Velocity hit rate at least 0.66; concentration FAC2 at least 0.5 and fractional bias within 0.3 |
| V2 | Concordia isolated low-rise building with rooftop stack, [IRSST report R-848](https://pharesst.irsst.qc.ca/rapports-scientifique/226) | Roof-level dilution versus stack height and momentum ratio, the applied design variable | Published tracer-gas results, digitised; ASHRAE dilution estimate as a second reference | MVP | Correct ranking of stack heights; roof-receptor FAC2 at least 0.5 |
| V2b | V2 geometry rerun at full scale with the applied ABL setup | Whether the result survives the jump from tunnel scale to full scale | Own model-scale result | MVP | Dimensionless dilution within the V2 uncertainty band |
| V3 | Flat-roof low-rise model from the [TPU aerodynamic database](https://www.wind.arch.t-kougei.ac.jp/system/eng/contents/code/tpu) | Mean roof and wall pressure coefficients at 0 and 45 degrees | Public wind-tunnel pressure data | Finished | Report mean Cp error by zone; no pass or fail on peaks |
| V4 | Buoyant jet in crossflow | Plume trajectory with the buoyant solver setup | Standard plume-rise correlation | Finished, before any buoyant applied run | Trajectory within the scatter of the correlation |
| V1-LES | AIJ Case H, scale-resolving | Mean and fluctuating concentration that RANS cannot give | Same dataset | Finished | Resolved turbulent kinetic energy above 80 percent in the wake |

[AIJ Case J](https://zenodo.org/records/15447888) is not on the ladder. It is the same building with a near-ground source under an unstable approach flow, so it validates stratified ABL physics, not hot discharge from rooftop plant. Use it only if the non-neutral stretch goal is taken.

The chiller self-recirculation result has no public validation data. It is supported by V1, V2 and verification checks, and the report says so.

## 6. Modelling approach

Steady incompressible RANS carries every design run. Transient and buoyant runs exist only to test whether the RANS conclusion holds.

- **Turbulence closure.** Realizable k-epsilon and k-omega SST both run V0 to V2. The baseline is chosen by written criteria: ABL homogeneity, V1 and V2 metrics, robustness. The other model is rerun at the governing conditions as a sensitivity. GEKO is an optional third, not a dependency.
- **Turbulent Schmidt number.** One value is fixed from V1 and V2 and carried unchanged to the applied case. The governing conditions are rerun over 0.4 to 0.9 to give a sensitivity band.
- **Scalars.** Tagged passive scalars on the frozen flow field, as in section 4.
- **Buoyant runs.** Two applied conditions only: the low-wind governing direction for the baseline and for the final design. Chiller discharge temperature is coupled to its own intake temperature, and flue gas is treated as variable density, not Boussinesq. The purpose is to measure how conservative the passive limit is.
- **Scale-resolving run.** One LES or IDDES of AIJ Case H with synthetic turbulent inflow. It gives the peak-to-mean concentration ratio and the RANS bias in wake spread, which are applied as model-form uncertainty to the applied results.
- **No URANS stage.** If a steady case will not converge, it is run transient and averaged, and reported as a numerical necessity.
- **No scale-resolving run on the applied case** in the MVP or finished version.

## 7. Mesh and verification requirements

- **Mesher.** snappyHexMesh. Indicative sizes: 4 m far field, 0.5 m on the building, 0.25 m in the rooftop plant zone, at least 10 cells across a flue diameter and 8 across a chiller discharge strip. Medium mesh target 5 to 7 million cells.
- **Thin features.** Parapet and screens are baffles, not thin solids.
- **Near-wall treatment.** Wall functions throughout. Separation is fixed by sharp edges, so full prism-layer coverage is not a goal. Report the y+ distribution and the layer coverage achieved.
- **Grid study.** Three levels at a refinement ratio near 1.4 for V1 and for one governing applied condition. Grid convergence index reported on the primary quantities, not on contour plots.
- **Iterative convergence.** Primary quantities monitored every iteration and flat to within 1 percent. If they oscillate, average over the cycle and report the amplitude.
- **Balances.** Mass at every patch; scalar flux in equals flux out within 1 percent; the sum of tagged scalars equals a single all-sources scalar.
- **Input uncertainty.** Turbulent Schmidt number, inflow turbulence level and closure choice are combined into one band on each primary quantity.
- **Reproducibility.** Every case generated by script from one parameter file; the software version, mesh statistics and run time are logged per case.

## 8. Design matrix

The matrix is 24 steady runs for the MVP and 46 for the finished version, plus 2 buoyant runs. Variants are tested only at the governing conditions, then the chosen design is confirmed over the full sweep.

Design variants:

| ID | Flue tip above roof | Plant screen |
| --- | --- | --- |
| D0 baseline | 3 m | None |
| D1 | 6 m | None |
| D2 | 9 m | None |
| D3 | 3 m | Solid, 4 m |
| D4 | 3 m | 50 percent free area, 4 m |
| D5 | Best of D0 to D2 | Best of D3 and D4, or none |

Run blocks:

| Block | Purpose | Variants | Conditions | Runs | Stage |
| --- | --- | --- | --- | --- | --- |
| A | Find governing direction and speed | D0 | 7 directions at U\_H = 3 and 10 m/s | 14 | MVP |
| B | Locate the critical wind speed | D0 | 2 governing directions at 6 and 14 m/s | 4 | MVP |
| C | Flue height effect on intake dilution | D1, D2 | 2 governing conditions | 4 | MVP |
| F | Grid study | D0 | 1 governing condition, coarse and fine | 2 | MVP |
| D | Screen effect on chiller recirculation and on the flue plume | D3, D4 | 3 governing conditions | 6 | Finished |
| E | Confirm the chosen design | D5 | Full sweep as block A | 14 | Finished |
| S | Closure sensitivity | D0 | 2 governing conditions, second closure | 2 | Finished |
| G | Buoyancy check | D0, D5 | Low-wind governing condition | 2 buoyant | Finished |

Schmidt-number sensitivity reuses the frozen flow fields and needs no new flow runs.

A published wind-tunnel study of [architectural screens around short stacks](https://www.aivc.org/sites/default/files/airbase_11907.pdf) gives an independent trend to compare block D against.

## 9. Quantities of interest

Four primary quantities carry the decision. Each is reported with a grid, model and input uncertainty band.

| Primary quantity | Definition | Acceptance limit |
| --- | --- | --- |
| Fresh-air intake dilution | Flue exit concentration divided by flow-weighted concentration at the louvres; minimum over all directions and speeds | Project limit derived from a stated exhaust pollutant level and target. To be set and cited before block A |
| Chiller inlet temperature rise | Array mean and worst single unit, from the source-to-receptor matrix | Project limits taken from a public chiller derating curve. To be set and cited before block A |
| Governing condition | Wind direction and speed at which each of the two quantities above is worst | Not a limit; an output |
| Design effect | Change in the first two quantities for D1 to D5 relative to D0 | Effect must exceed the uncertainty band to count |

Secondary quantities, reported as supporting evidence:

- Source-to-receptor matrix F for each run.
- Roof separation and reattachment length, and mean roof pressure coefficient.
- Plume centreline trajectory for flues and chiller discharge.
- Validation metrics, grid convergence index and cost per run.

Not reported as results: building drag or lift, peak pressures, pedestrian-level speeds.

## 10. Compute budget and cost traps

The MVP is about 30 cost units and the finished version about 70, where one unit is one applied steady RANS run on the medium mesh. These are order-of-magnitude estimates. One unit is expected to be near 100 core-hours and must be measured on the first applied run, then the table rescaled.

| Item | Approximate cost (units) |
| --- | --- |
| V0, V1, V2 and V2b, both closures, with V1 grid study | 5 |
| MVP applied blocks A, B, C, F | 26 |
| Finished RANS blocks D, E, S | 22 |
| V3 pressure comparison | 0.5 |
| Buoyant runs, block G and V4 | 8 to 10 |
| LES or IDDES of AIJ Case H | 5 to 15 |
| Scale-resolving run of the applied case (stretch) | 300 or more |

Cost traps to avoid:

- Scale-resolving simulation of the full-scale applied case. Small fast cells at the flue exits set the time step for a domain that needs minutes of physical time.
- A three-level grid study on every applied condition. One governing condition is enough.
- Thirty-six wind directions for every design variant.
- Chasing full prism-layer coverage on every rooftop box.
- Steady buoyant runs that never converge. Budget them as pseudo-transient from the start.
- Planning around a GPU. The standard OpenFOAM solvers used here run on CPU cores.

## 11. Deliverables

The MVP is a complete, publishable study on its own: validated dispersion model, baseline sweep and a flue-height recommendation.

| Level | Content | Done when |
| --- | --- | --- |
| MVP | V0, V1, V2, V2b. Blocks A, B, C, F. Tagged-scalar matrix and passive-limit temperature rise. Scripted pipeline. Report v1 | A flue-height recommendation is stated with its uncertainty band, and anyone can rerun one case from the repository |
| Finished | V3, V4, V1-LES. Blocks D, E, S, G. Combined uncertainty band. Final design confirmed over the full sweep | The report answers the section 1 question for both intake dilution and chiller temperature rise, and shows whether buoyancy or unsteadiness changes the answer |
| Stretch, pick at most one | A second identical hall upwind. Generator radiator discharge. Wind-rose weighting to hours per year above the limits. Non-neutral approach flow using AIJ Case J. Scale-resolving run of the governing applied case | Only after the finished version is published |

Artefacts:

- Repository with validation, applied, workflow, post-processing and test folders, a README that states the question and the result, and a coarse regression case.
- Technical report of at most 25 pages: summary and decision, problem and limits, method, verification, validation, applied results, recommendation, limitations.
- One-page summary with the design chart, for LinkedIn and interviews.

A separate small repository covers force and pressure prediction on a standard open-data vehicle body. It is not part of this brief.

## 12. Open items before the scope is frozen

These eight checks decide whether the brief stands as written. None needs a production run.

- [ ] Read the AIJ Case H readme: source position, measured planes, approach-flow profile, licence terms.
- [ ] Download IRSST R-848 and confirm the isolated-building cases, model dimensions, receptor positions and the definition of momentum ratio. Decide which figures to digitise.
- [ ] Pick the TPU flat-roof model closest in proportion to the hall.
- [ ] Replace the indicative chiller and generator values with public datasheet values and cite them.
- [ ] Set and cite the two acceptance limits in section 9.
- [ ] Smoke-test in OpenFOAM v2606: ABL inlet and rough-wall conditions with both closures, several passive scalars on a frozen flow, a porous baffle, and an inlet temperature mapped from an outlet patch.
- [ ] Decide the ground-roughness treatment next to the building.
- [ ] Time one applied run on the medium mesh and rescale section 10.

## Sources

- [AIJ benchmark Case H dataset](https://zenodo.org/records/15429872) and [Case J dataset](https://zenodo.org/records/15447888), Zenodo, open data.
- [IRSST report R-848](https://pharesst.irsst.qc.ca/rapports-scientifique/226), Concordia wind-tunnel study of rooftop stack dispersion, free download.
- [TPU aerodynamic database](https://www.wind.arch.t-kougei.ac.jp/system/eng/contents/code/tpu), Tokyo Polytechnic University.
- [Screens and short stacks wind-tunnel paper](https://www.aivc.org/sites/default/files/airbase_11907.pdf), AIVC archive.
- [OpenFOAM v2606 release notes](https://www.openfoam.com/news/main-news/openfoam-v2606) and [atmospheric boundary condition documentation](https://doc.openfoam.com/2312/tools/processing/boundary-conditions/rtm/derived/atmospheric/atmBoundaryLayerInletVelocity/).
