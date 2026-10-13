# Results

One folder per stage. Each holds the JSON record of every run (inputs, mesh statistics, metrics,
Git commit), a `summary.md` written by script, and `figures/` drawn by `postproc/figures`.
Fields, meshes and logs are never committed; the cases that produced these records are
regenerated from `params/` by the scripts in `workflow/` and `validation/`.

| folder | stage | acceptance (fixed before the runs) |
|---|---|---|
| `smoke/` | official ABL tutorial, unmodified | run completes, profiles hold |
| `V0/` | empty domain | U and k change < 5 % inlet to building |
| `V1/` | AIJ Case H, isolated building | hit rate U >= 0.66; FAC2 >= 0.5 and \|FB\| <= 0.3 |
| `V2/` | IRSST R-848 rooftop stack | stack-height ranking correct; FAC2 >= 0.5 |
| `V2b/` | V2 at full scale | dilution within 18 % of the model-scale result |
| `applied/` | data hall matrix | intake dilution >= 2000; chiller rise <= 2 K mean, 4 K worst |
