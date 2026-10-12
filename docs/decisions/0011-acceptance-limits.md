# 0011 Acceptance limits for the two primary quantities (taken under autopilot 2026-10-12, for Saleh's review)

Project.md section 9 requires both limits to be set and cited before block A. They are fixed here
and are not adjusted afterwards (CLAUDE.md rule 4).

## Fresh-air intake dilution of generator exhaust
- Target at the intake: NO2 below the UK/EU one-hour limit of 200 ug/m3, about 0.1 ppm at 20 C
  (The Air Quality Standards Regulations 2010, Directive 2008/50/EC). Kind: regulatory, cited.
- Exhaust NO2: a standby diesel at EPA Tier 2 emits about 6 to 9 g NOx per kWh, of which the NO2
  fraction is 0.01 to 0.20 for engines without oxidation catalysts (CDC/NIOSH mining study,
  stacks.cdc.gov/view/cdc/180333); with the Kohler KD2000 exhaust flow of 7.38 m3/s at 2000 kW
  this gives NOx of order 1,000 to 1,500 ppm and NO2 of order 100 to 300 ppm in the stack.
  Taken: 200 ppm NO2 in the exhaust. Kind: derived from cited ranges; an indicative value.
- Required dilution D = C_e / C_r = 200 / 0.1 = 2,000. LIMIT: minimum intake dilution of the flue
  scalar, flow-weighted over both louvres, worst case over directions and speeds, >= 2,000.
  Note: the one-hour average in a steady RANS result is the mean field; peak-to-mean ratios come
  from the V1-LES rung in the finished version (Project.md section 6).

## Chiller inlet temperature rise
- Derating of air-cooled chillers: about 1.3 percent of capacity per kelvin of ambient above the
  rating point (US patent 10684616 calculation by AHRI methods; Polyscience selection guidance);
  manufacturer correction tables were sought and not retrieved. Kind: empirical, cited, indicative.
- LIMIT: array-mean inlet rise <= 2 K (2.6 percent capacity loss) and worst single unit <= 4 K
  (5.2 percent), from the source-to-receptor matrix with feedback. Kind: design choice from the
  cited derating.

Both limits are provisional until Saleh confirms or replaces them; the runs report the quantities
either way.
