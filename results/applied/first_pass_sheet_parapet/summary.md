# Applied runs: primary quantities per condition

Limits (decision 0011): intake dilution of flue exhaust >= 2000; chiller inlet rise mean <= 2 K, worst unit <= 4 K. Convergence: last-200-iteration amplitude of the receptor fractions; balance: sum of tagged scalars against the all-sources scalar.

| variant | dir [deg] | U_H [m/s] | intake dilution | flue fraction at intake | chiller rise mean [K] | worst unit [K] (which) | max self-recirc. | balance [%] | conv. amp. [%] | dilution ok | chiller ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D0 | 0 | 3 | 5.47e+03 | 1.83e-04 | 8.87 | 11.53 (4) | 0.202 | 0.30 | 19.94 | yes | NO |
| D0 | 0 | 10 | 7.58e+07 | 1.32e-08 | 5.95 | 8.03 (9) | 0.163 | 0.39 | 0.02 | yes | NO |
| D0 | 60 | 10 | 3.34e+05 | 3.00e-06 | 7.11 | 11.67 (4) | 0.198 | 0.21 | 18.49 | yes | NO |
| D0 | 90 | 10 | 1.18e+03 | 8.46e-04 | 5.69 | 8.77 (3) | 0.162 | 0.41 | 26.36 | NO | NO |

Governing condition for intake dilution (D0): 90 deg at 10 m/s, dilution 1.18e+03.
Governing condition for chiller inlet rise (D0): 60 deg at 10 m/s, worst unit 11.67 K, mean 7.11 K.
