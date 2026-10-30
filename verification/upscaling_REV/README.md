# upscaling_REV — from the REV to a centimetre test (2026-10-30)

**Goal (user):** correlate the REV observations with cm-scale tests and use the REV as a prediction tool. The REV does not have to simulate a centimetre: it has to
give the fabric-scale law. **First check, on an existing run:** does the row-mean saturation of the REV collapse on y/√t, as a uniform 1D diffusive medium would?

**Data:** copy of job 3055/3058 (full REV, K 1e-11, VG 5000 / 0.5, θ 60°, solver `be1a3ab`, setup values), writes 2–20 ms (the front reaches the closed end at ~25 ms).
`../../.venv/bin/python boltzmann.py`. y origin 0.1 mm (top of the saturated rows), mean S over a 0.67 mm window (half a weave period along y).

| Row-mean yarn S | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|
| mean η = y/√t [mm/√s] | 16.2 | 14.4 | 12.9 | 11.7 | 10.4 | 9.0 | 7.6 | 5.8 | 3.5 |
| spread 2–20 ms (std/mean) | 6 % | 4 % | 2 % | 2 % | 2 % | 5 % | 8 % | 15 % | 26 % |

**Measured:** collapse within 2–8 % for S 0.1–0.7 (S ≥ 0.8 still drifting, near the inlet). Front 14.0 mm/√s·√t + 0.23 mm (1D yarn column 18.04: ×0.78); uptake per fabric
section 2.43 mm/√s·√t (1D column × yarn volume fraction 0.463 = 2.83: ×0.86). Yarns hold 30 % of the fabric pore space (free box cells 70 %). For the TexGen geometry, water
per fabric area: yarns full 65 g/m², yarns and all free box cells full 215 g/m² (upper bound: the box includes free space beside the crimped fabric).

**Not measured, extrapolated:** front 10 mm at 0.51 s, 20 mm at 2.0 s (setup values, no gravity).

**Limits:** one parameter set, not real yarn values; under 2 weave repeats along y; no gravity; S ≥ 0.8 not converged, and those levels govern the late stage; the gaps stay nearly
empty in this run, a late gap filling would add to the uptake; TexGen geometry, not the real fabric.

**Chain to a prediction:** (1) yarn inputs measured independently of the fabric test (K, pc(S), θ, ε); (2) REV with them: η(S), D_eff(S) by Bruce–Klute, uptake; (3) 1D model with
gravity to the height of the test; (4) comparison with a cm-scale test not used for any calibration, front and mass vs time. Done so far: the collapse check of step 2, on setup values.
