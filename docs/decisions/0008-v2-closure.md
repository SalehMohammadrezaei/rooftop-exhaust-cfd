# 0008 V2 closing decisions

Date: 2026-10-12. Approved by Saleh ("ok", with the request to run V2b in the background and start the applied case).

## Outcome, as it stands (results/V2/summary.md, notebook D3 to D12)
- Low-momentum cases, M = 1: FAC2 1.0 and 0.8 at Sct 0.4 (0.5 and 0.6 at Sct 0.7); mark met.
- High-momentum cases, M = 3: FAC2 0 at both heights; CFD dilution 5 to 10 times too low near
  the stack, 2 to 3 times at the far receptors; mark not met.
- Stack-height ranking: correct at both M (10 of 10 receptors). Exhaust-momentum ranking: wrong
  (the CFD gives nearly the same dilution at M = 3 as at M = 1).
- Cause, measured: the eddy-viscosity closure destroys the jet within three diameters; mesh ruled
  out by a jet-resolved grid check (1.41 M cells, identical result); SST closure no better.
- Schmidt number: 0.4 scores better than 0.7 in every case, as in V1.

## Decisions (all four as recommended)
1. Treatment of the momentum cases in the report: state the numbers, the cause, and that RANS
   eddy-viscosity closures under-predict jet rise at this scale, so the applied flues' exhaust
   momentum (M 3 to 10) is not credited; stack height is ranked correctly and under-credited.
   (Recommended: this is the honest statement and matches V1's treatment.)
2. Whether to add a test of a jet-preserving model before V2b: options are (a) a scale-resolving
   run of the 1 m, M 3 case (cost several units, outside the MVP plan), (b) a RANS variant with a
   limiter on the eddy viscosity in the jet region (a new modelling decision, needs its own
   justification and sensitivity), (c) none now, carry the limitation and revisit at V4 where the
   buoyant jet in crossflow is validated against a plume-rise correlation. (Recommended: c for the
   MVP; a for the finished version, folded into the V1-LES rung as a second scale-resolving case.)
3. Schmidt number for the applied case: 0.4, supported by both V1 and V2 (Project.md section 6
   asks for one value fixed from V1 and V2). Sensitivity band 0.4 to 0.9 from V1.
4. V2b (full scale with the applied ABL): proceed on the two M = 1 cases, which the model
   represents, to test the scale jump as the brief intends; the M = 3 cases at full scale would
   test nothing new. (Recommended.)

## Scope note
V3, V4 and V1-LES remain listed as finished-version items, not done. The MVP validation story is
V0, V1, V2 and V2b. Saleh builds the applied case himself with guidance (Part E of the notebook).
