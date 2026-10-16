# Grid convergence, D0_dir180_U10 (decision 0015)

Cells: coarse 1,051,942, base 2,604,946, fine 6,697,868; mean refinement ratio r = 1.361. GCI_fine = 1.25 |f_base - f_fine| / (f_fine (r^p - 1)), p the observed order (Celik et al. 2008).

| quantity | coarse | base | fine | p | GCI fine | fine-base change |
|---|---|---|---|---|---|---|
| intake dilution | 56.7 | 58.1 | 59.9 | undefined | n/a | 3.0 % |
| chiller rise, mean [K] | 6.17 | 6.14 | 6.16 | undefined | n/a | 0.3 % |
| chiller rise, worst unit [K] | 8.42 | 8.31 | 8.29 | 5.31 | 0.1 % | 0.3 % |
| flue fraction at the louvres | 0.0176 | 0.0172 | 0.0167 | undefined | n/a | 3.1 % |
| chiller-air fraction at the intake | 3.03e-05 | 2.78e-05 | 2.49e-05 | undefined | n/a | 11.8 % |

Receptor-fraction amplitude over the last window: coarse 0.00 %, base 0.01 %, fine 1.04 %.

Where p is undefined the three solutions do not converge monotonically at a measurable order (the base-to-fine change is as large as or larger than the coarse-to-base change), so no Richardson estimate exists; the fine-base change is then the band quoted for that quantity.
