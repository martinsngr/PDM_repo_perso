# Is B needed? Long run without B on the porous strip (2026-10-15)

**Question:** with A (and C) but without B, the strip bench develops a transverse pattern (spread 0.06–0.13, transverse
U 0.1–1 m/s) and 9 % less uptake than A+B+C at 2e-4 s (`../bench_ddtCorr`, runs stopped at 2e-4 s = 2000 steps).
Does the pattern decay and the uptake converge on a longer run, i.e. is it a start-up transient?

**Case:** `case/` = `../bench_ddtCorr/case` (5 × 172 × 3, all porous, K 1e-11, ε 0.5, VG pc0 5000 m 0.5, BC n 3,
dry 0.002 + 0.2 mm ramp, reservoir inlet, symmetry sides, fixed dt 1e-7, `transverseSpread` per step).
Runs: end time 2e-3 s (20,000 steps), fields every 1e-4 s.

**Solver:** installed `hybridPorousInterFoam` = `b525086`, both runs. Only difference: `darcyFaceMaxDa`.
| Run | `darcyFaceMaxDa` | acting changes |
|---|---|---|
| AC | absent | A, C (E: no free cells, bit-identical; F only with B; G–I keywords off) |
| ABC | 0.1 | A, B, C (+ F, inactive with every face Darcy) |
So AC vs ABC isolates B (no C confound, unlike the 10-07 comparison A only vs A+B+C).

## Predictions (before the runs)
- AC: the pattern persists to 2 ms (spread 0.05–0.15 following the front), uptake stays below ABC by a growing
  amount; no crash (A-only runs bounded to 2e-4 s). ABC: spread ≤ 1e-6, smooth front.
- **Decision:**
  - spread in AC decays below 1e-3 and uptake within 1 % of ABC by 2 ms → transient: B not needed *for stability on
    this strip* (it stays needed for the Darcy limit, the step count and as the base of F/G/F′);
  - spread stays ≥ 0.01 or uptake gap ≥ 3 % → B needed here;
  - in between → inconclusive, run to 5 ms.

## Results (2026-10-15, laptop, serial)

**AC (no B): crashed at 1.284e-4 s** (`sigFpe`; log `AC/log.AC` every 10th step + `log.AC.tail`). Prediction "no
crash" wrong.

| t (s) | spread | max transverse U | min α | Courant max | mean α |
|---|---|---|---|---|---|
| 1e-5 | 0.24 | 0.5 m/s | ≥ 0.0019 | 0.002 | 0.0314 |
| 5e-5 | 0.33 | 2.7 m/s | | 0.015 | 0.0356 |
| 1.1e-4 | 0.25 | 4.9 m/s | | 0.006 | 0.0422 |
| 1.26e-4 | 0.21 | 49 m/s | 0.0019 | 0.03 | 0.0439 |
| 1.276e-4 | 0.30 | 312 m/s | −1e-5 | 0.24 | 0.0441 |
| 1.281e-4 | 2.2 | 6e5 m/s | −2.1 (max 2.16) | 10 | |

- The transverse pattern appears within 8 µs (spread 0.11, vs 0.04 at 10 µs for A only on 10-07), stays at 0.2–0.33
  following the front (rows 6–15), and the transverse velocity grows steadily (0.5 → 5 → 50 → 300 m/s) until α leaves
  [0, 1] and the run diverges within ~5 steps.
- **A + C without B is worse than A alone** (A alone: spread ≤ 0.14, bounded to 2e-4 s, `../bench_ddtCorr/log.ii_A_c1`).
  C (upwinded kr) is part of the installed solver, so without B the installed solver does not run this case.
- **Decision: B needed on this strip** (crash; spread ≥ 0.01 from 8 µs).

**ABC (with B):** stopped by hand at 8.5e-4 s (the reference was not needed after the AC crash; log `ABC/log.ABC`,
every 10th step). Spread ≤ 2.7e-7, transverse U ≤ 5e-7 m/s throughout. Mean α at 1e-4 s 0.04356 = `../bench_ddtCorr/
log.v_modified` (b995db5) to 4 digits, as expected (no free cells: E–I do not act).

| t (s) | AC spread | ABC spread | AC max transverse U | ABC | AC mean α | ABC mean α | AC uptake deficit |
|---|---|---|---|---|---|---|---|
| 1e-5 | 0.24 | 3e-8 | 0.51 m/s | 2e-7 | 0.03139 | 0.03216 | −2.4 % |
| 2e-5 | 0.25 | 6e-8 | 0.67 | 2e-7 | 0.03246 | 0.03356 | −3.3 % |
| 5e-5 | 0.33 | 9e-8 | 2.7 | 4e-7 | 0.03561 | 0.03754 | −5.1 % |
| 1e-4 | 0.22 | 1.2e-7 | 4.2 | 3e-7 | 0.04106 | 0.04356 | −5.7 % |
| 1.2e-4 | 0.21 | 1.3e-7 | 2.2 | 2e-7 | 0.04324 | 0.04579 | −5.6 % |

(Mean α includes the initial 0.2 mm ramp; the deficit on the water taken up since t = 0 is larger.)

**Conclusion:** without B the installed solver produces a transverse pattern from the first microseconds, 3–6 % less
uptake and diverges at 1.28e-4 s; with B nothing of it. B is needed on this strip, not a start-up transient. Its
mechanism (why the momentum-path flux in porous faces amplifies the pattern) is still not identified.
