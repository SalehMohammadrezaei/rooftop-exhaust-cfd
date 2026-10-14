# Applied runs: primary quantities per condition

Limits (decision 0011): intake dilution of flue exhaust >= 2000; chiller inlet rise mean <= 2 K, worst unit <= 4 K. Convergence: last-200-iteration amplitude of the receptor fractions; balance: sum of tagged scalars against the all-sources scalar.

| variant | dir [deg] | U_H [m/s] | intake dilution | flue fraction at intake | chiller rise mean [K] | worst unit [K] (which) | max self-recirc. | balance [%] | conv. amp. [%] | dilution ok | chiller ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D0 | 90 | 3 | 9.58e+03 | 1.04e-04 | 7.34 | 12.96 (2) | 0.192 | 0.27 | 1.60 | yes | NO |
| D0 | 0 | 10 | 9.57e+07 | 1.04e-08 | 6.00 | 8.08 (4) | 0.164 | 0.38 | 0.00 | yes | NO |
| D0 | 90 | 10 | 1.19e+03 | 8.44e-04 | 5.86 | 9.25 (3) | 0.163 | 0.51 | 0.00 | NO | NO |
| D0 | 180 | 10 | 58.1 | 1.72e-02 | 6.14 | 8.31 (2) | 0.169 | 0.23 | 0.01 | NO | NO |

Governing condition for intake dilution (D0): 180 deg at 10 m/s, dilution 58.1.
Governing condition for chiller inlet rise (D0): 90 deg at 3 m/s, worst unit 12.96 K, mean 7.34 K.
