# Decision records

One dated file per modelling decision: what was decided, the options considered, the reason,
and what it changes. Numbers fixed before a run (acceptance limits, mesh rules) live here and are
not edited after the result is known; a later check is appended under its own heading.

| no. | decision | outcome |
|---|---|---|
| 0001 | Phase-0 smoke test on the official ABL tutorial | run as shipped; kEpsilon holds the profile, kOmegaSST drifts in k |
| 0002 | V0 empty-domain setup and closing | realizable k-ε with atmospheric wall functions and fixed shear at the top; profiles hold within 2 % |
| 0003 | V1 inlet profiles for AIJ Case H | measured profile imposed by table; log-law slope from a fit (addendum) |
| 0004 | V1 tracer setup | scalarTransport on the frozen flow, Sct scan 0.4 to 0.9 |
| 0005 | V1 floor roughness | rough floor rejected (hit rate fell to 0.34) |
| 0006 | V1 closing | baseline realizable k-ε and the medium-grid rule; velocity 0.60 of 0.66 not met and carried as model form |
| 0007 | V2 setup (IRSST R-848 stack) | stack centre 1 mm inside the roof edge; 10 cells across the exit |
| 0008 | V2 closing | Sct 0.4 fixed; M = 3 jet over-mixing carried as a model limit |
| 0009 | Stretch: real geometry (Manchester) and presentation standard | after the applied study |
| 0010 | Applied flows at the openings | chiller ±90 m³/s derived from 1.3 MW at 12 K; flue 19.4 m³/s momentum-matched to a 2 MW set; louvres 5 m³/s |
| 0011 | Acceptance limits | intake dilution ≥ 2000 (NO2 hourly limit); chiller rise ≤ 2 K mean, ≤ 4 K worst unit |
| 0012 | Parapet thickness | 0.5 m solid ring instead of a baffle; check at 0 deg moved the chiller numbers by 0.05 K |
| 0013 | Flue jet treatment | RANS accepted with a stated caveat; scale-resolving check only if a result lands within a factor of 3 of the limit |
| 0014 | Scale-resolving jet check (proposal) | triggered by the 9 m tip at 180 deg (822); DDES on the governing case proposed, awaiting decision |
| 0015 | Grid study (proposal) | three meshes at ratio 1.41 on the governing condition, awaiting decision |
