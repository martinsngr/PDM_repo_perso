# study2c_nearSaturation — porous/free coupling next to a nearly saturated yarn wall (2026-10-29)

**Why.** REV_lowpc (job 3059, VG pc0 1000 Pa, m 0.4, θ 40°) diverged at 6.553 ms after fast currents from 0.5 ms
(free cells 7–16 m/s, REV 0.8 m/s). Diagnosis (`../../NOTES_cases.md`, REV_lowpc entry): most fast cells are air
(α ≤ 0.01, ~75 % of those above 1 m/s) next to partly wet yarn; the fastest few are partly filled gap cells (α
0.03–0.35) with 2–3 yarn faces; a locator found the dt-dip
episodes at the flank of yarn 2, where the gap holds a smeared band of α 0.05–0.6 and the surface cells drain and
refill (|dα/dt| up to 9.6e5 1/s). One-change variants: the low pc is the main trigger, θ 40° adds. The REV run with
the base pc (job 3058) shows the same pattern, weaker, from 15 ms, once its yarns approach saturation.
**Hypothesis:** the coupling misbehaves where a nearly saturated yarn, whose pc is about the gap meniscus suction,
faces a partly filled gap cell: the exchange through the yarn surface then depends on the free-cell pressure of a
smeared VOF interface. Suspects (all porous/free faces): G (pc jump, water flux from the free-cell pressure), the kr
of yarn/gap faces (taken from the gap cell's α through Brooks–Corey when water flows gap → yarn), H (contact angle on
a wet surface), F′, I. This study reproduces the state on the 2D bench (minutes per run) and switches the suspects
one at a time, in the spirit of Study 2b (`../PLAN.md`).

**Case.** `../standardOpenBC/bench_B`: 2D thick-wall slit, 2.0 × 0.48 mm, 100 × 1 × 24 cells of 20 µm: porous walls
8 cells (ε 0.5, K 1e-11, ending 3 cells before the outlet) | gap 8 cells (160 µm) | walls 8 cells; reservoir inlet
(J `waterOnlyPatches`, p `totalPressure` 0, α 1 on all inlet faces), outlet open (`totalPressure`), gravity −x;
G + H + F′ + I on, θ 60°; 2 ms, serial. Initial: gap pure air except the 0.1 mm water column at the inlet (bench_B).
**Changes (`makeCases.sh`):** every porous cell starts at the wall saturation S_w (no ramp), VG pc0 and m per run,
θ0 per run, the `dsLocator` function object (per step: porous cell of the largest |dα/dt|, fastest free cell).
**The state:** the gap meniscus suction is 2σcosθ/w = 2·0.072·0.5/160e-6 = **450 Pa** at θ 60°. Wall pc from the
solver's VG (pc = pc0·(Se^(−1/m) − 1)^(1−m), Se = S/0.999): low pc (1000 Pa, m 0.4) 448 Pa at S 0.91, 214 Pa at 0.97,
2.5 kPa at 0.5; base pc (5000 Pa, m 0.5) 2.26 kPa at 0.91, 448 Pa at 0.995.

**Solver:** installed `hybridPorousInterFoam` = of9-port `be1a3ab` (A–J with the H fix; repo HEAD `c3dbf48`, docs
only), laptop, serial. Function objects: `tools/` (copies of `../../meshing_strat_trial/tools` of 2026-10-29 and
`dsLocator`).

**Commands.** `./makeCases.sh [run ...]`, `./runAll.sh <run ...>` (parallel, one core each), then
`../../.venv/bin/python analyse.py` (table in `summary.md`).

## Phase 1 — reproduction and controls (keywords as the REV)

| Run | pc0 / m | S_w | wall pc | Prediction (written before the runs) |
|---|---|---|---|---|
| `N0_lowpc_S091` | 1000 / 0.4 | 0.91 | 448 Pa ≈ suction | **reproduces**: free cells > 5 m/s at the wall by 1 ms, growing; dt dips; smeared cells along the walls ≥ 3× N2; meniscus higher than bench_B (0.79 mm at 2 ms), towards the impermeable-wall rise (1.16 mm) |
| `N1_lowpc_S097` | 1000 / 0.4 | 0.97 | 214 Pa < suction | walls feed the gap (wall S decreases); fast currents as N0 or stronger |
| `N2_lowpc_S050` | 1000 / 0.4 | 0.50 | 2.5 kPa ≫ suction | **calm**: walls pull; max free \|U\| ≤ 1.5 m/s after 0.2 ms (bench_B 1.2 m/s) |
| `N3_REVpc_S091` | 5000 / 0.5 | 0.91 | 2.26 kPa ≫ suction | **calm**, as N2 |
| `N4_REVpc_S0995` | 5000 / 0.5 | 0.995 | 448 Pa ≈ suction | **decisive**: like N0 if the near-equilibrium state is the trigger (main hypothesis), calm like N3 if the low-pc curve itself is (dpc/dS: 56.5 kPa for the base pc at 0.995, 3.55 kPa for the low pc at 0.91, ×16) |

"Reproduces": per-step max free |U| > 5 m/s on ≥ 10 % of the steps after 0.2 ms, or a stopGuard stop. "Calm": max
free |U| ≤ 1.5 m/s after 0.2 ms and no dt dips below half the median dt. Otherwise: inconclusive.

**Decision table:**

| Observation | Conclusion | Next |
|---|---|---|
| N0 and N4 reproduce, N2 and N3 calm | the near-equilibrium state triggers it, for any pc curve | phase 2 on N0 and N4 |
| N0 reproduces, N4 calm | specific to the low-pc curve at that S (dpc/dS, kr) | compare the face terms of N0 and N4 |
| N0 calm | the bench does not reproduce the REV state (3D, crossing yarns, gap water from below) | try N1, θ 40°, a 15-cell gap, a saturation gradient along the wall; else a REV subdomain |
| N2 or N3 not calm | not specific to near equilibrium: the coupling with wet walls in general | revise the hypothesis |

## Phase 1b — what the bench lacks (one change each from N0; predictions written before the runs)
| Run | Change from N0 | Prediction |
|---|---|---|
| `N5_lowpc_prof` | wall S along x as the REV flank of yarn 2 at 6.5 ms: 0.98 (x 0) → 0.96 (0.2 mm) → 0.83 (0.35) → 0.6 (0.6) → 0.1 (0.97 mm and above); wall pc = suction at x ≈ 0.29 mm | **reproduces** (main candidate: the meniscus meets the equilibrium point while water flows along the wall) |
| `N6_lowpc_S084_t40` | θ 40°, S_w 0.84 (suction 690 Pa = wall pc 693 Pa) | calm (REV `lowpc_t60` had fast currents at θ 60°: θ 40° not needed) |
| `N7_lowpc_S078_g4` | gap 4 cells (walls 10), S_w 0.78 (suction 900 Pa = wall pc 911 Pa) | inconclusive guess: calm |
| `N8_lowpc_S091_dt` | dt capped at 2.5e-7 s (`maxDeltaTCoats`; REV dt 1.2–4e-7) | calm |

### Phase 1b results (2026-10-29, `be1a3ab`, laptop serial)

| Run | max free \|U\| per step > 0.2 ms | steps > 5 m/s | dt median / dips | max free \|U\| at writes | smeared cells 0.5 / 1 / 2 ms | meniscus 1 / 2 ms | wall S 0 → 2 ms | imbalance / water | Prediction |
|---|---|---|---|---|---|---|---|---|---|
| N5_lowpc_prof | 0.99 m/s | 0 % | 7.4e-7 s / 0 | 0.99 | 6 / 26 / 64 | 0.64 / 1.02 mm | 0.378 → 0.532 (mean) | 5.0e-15 | reproduces: **fail** |
| N6_lowpc_S084_t40 | 1.45 | 0 % | 1.4e-6 / 0 | 1.65 | 24 / 56 / 99 | 0.82 / 1.48 | 0.840 → 0.881 | −8.3e-15 | calm: **pass** (1.65 m/s at one write, the faster θ 40° rise) |
| N7_lowpc_S078_g4 | 1.54 | 0 % | 8.1e-7 / 0 | 1.54 | 26 / 56 / 92 | 0.76 / 1.22 | 0.780 → 0.832 | 2.1e-14 | calm: **pass** (marginal) |
| N8_lowpc_S091_dt | 1.07 | 0 % | 2.5e-7 / 0 | 1.07 | 12 / 20 / 38 | 0.68 / 1.22 | 0.910 → 0.922 | −1.7e-14 | calm: **pass** (= N0: dt does not matter) |

**Conclusion of phases 1 and 1b: none of the nine 2D configurations reproduces the fast currents** (per-step max free
|U| 0.99–1.54 m/s, no step above 5 m/s): not the near-equilibrium wall saturation for either pc curve, not a
saturation gradient along the wall, not θ 40°, not a 4-cell gap, not dt. What the bench cannot represent: the 3D
geometry (staircase edges and corners of the yarn surfaces, crossings, gap water arriving around the half crossing
yarn 5). Next: phase 1c, the truncated REV.

## Phase 1c — truncated REV (3D, the real geometry; `makeREVcut.sh`)
The REV_lowpc mesh and initial fields (built by `../../meshing_strat_trial/REV_lowpc/Allpre`; source used: the copy
of job 3059, `~/PDM_results/REV_lowpc_run3059`, `0/` = its Allpre output) cut to the first 35 of 133 rows along y
(y < 0.70 mm; `topoSet` box + `subsetMesh -patch outlet`: the cut faces join the closed `outlet` patch, U noSlip, p
fixedFluxPressure, α zeroGradient). 91 × 35 × 20 cells. 4 cores, 0.5 ms, writes every 0.1 ms, `dsLocator`.
| Run | pc0 / m / θ | Prediction (before the runs) |
|---|---|---|
| `T0_cut_lowpc_t60` | 1000 / 0.4 / 60° | **reproduces** the full-REV `lowpc_t60` (scratch run, 2026-10-29): per-step max free \|U\| rising to ~8 m/s at 0.4–0.5 ms, fast cells at y 0.2–0.5 mm, mirror pairs across x = 0.909 mm (if the closed cut at 0.7 mm changes it: inconclusive) |
| `T1_cut_REVpc_t60` | 5000 / 0.5 / 60° | calm: max free \|U\| ≤ 1.5 m/s (full REV with the current BCs, job 3055: 0.77 m/s at 0.5 ms) |

### Phase 1c results (2026-10-29, `be1a3ab`, laptop 4 cores; `summaryCut.md`, `cellFaces.py`)
**T0 reproduces: pass.** T0 = the full-REV `lowpc_t60` to 2 digits: per-step max free |U| per 0.05 ms 37.9 (start-up)
/ 1.9 / 1.4 / 1.4 / 2.9 / 3.3 / 3.3 / 4.9 / 8.6 / 8.6 m/s (full REV 34.4 / 1.9 / 1.4 / 1.4 / 2.8 / 3.2 / 3.3 / 4.9 / 8.6 /
8.6), every step above 5 m/s from 0.40 ms in both; y-yarn front 0.331 / 0.371 / 0.391 / 0.431 / 0.431 mm and gap water
928 / 620 / 498 / 437 / 395 cells at 0.1–0.5 ms in both; 1,703 steps, dt median 2.7e-7 s, budget 5.5e-11 of the water.
**Onset (dsLocator):** at t ≈ 0.395 ms the free cell at (1.668, 0.231, 0.060) mm (and its mirror (0.150, 0.231, 0.060))
becomes the fastest and stays so on 193 of the 198 steps after 0.40 ms; α 0.12 → 0.245 and |U| 3.3 → 8.3 m/s over
0.04 ms. The cell has 3 porous neighbours (z−, x+, y+: yarn α 0.55–0.61) and 3 free ones (x−, z+, y−).
**Its face fluxes** (signed into the cell, as velocities over 4e-10 m²):

| t | cell α / p | x− free | z+ free | y− free | z− yarn | x+ yarn | y+ yarn | water in (y−) / out (3 yarn faces) |
|---|---|---|---|---|---|---|---|---|
| 0.3 ms | 0.009 / 2 Pa | −0.23 | −0.19 | +0.43 | +0.01 | +0.02 | −0.03 | +0.005 / ~0 m/s |
| 0.4 ms | 0.148 / 231 Pa | +2.52 | +2.98 | +1.48 | −1.74 | −1.96 | −3.27 | +0.14 / −0.02 |
| 0.5 ms | 0.285 / 517 Pa | +4.73 | +4.85 | +1.62 | −3.05 | −3.39 | −4.78 | +0.13 / −0.14 |

(total flux in m/s; at 0.4 and 0.5 ms > 97 % of it is air). Air enters from the free neighbours (p −11 to −51 Pa)
against the pressure difference (cell 231 / 517 Pa) and leaves through the three yarn faces at 3–5 m/s Darcy velocity
into cells that are 55–61 % water; the cell pressure and the through-flow grow together while the cell fills.
**Hypothesis (not tested):** a feedback in a free cell with several Darcy faces: water collects in a corner pocket
(the low-pc yarn drains it slowly), surface tension raises the cell pressure, the Darcy faces let air out into the
yarn with the air mobility of the gap cell (C upwinds kr by each phase's flux: air from the gap cell → kr_air from
the gap cell's α, (1 − 0.28)³ ≈ 0.37, vs ~0.07 for the yarn cell), F′ builds the cell velocity from those Darcy
fluxes (8 m/s into the corner), and the momentum step carries that velocity onto the free faces (air pulled in). A
flat 2D wall gives a cell one Darcy face only.

### Phase 2 on the truncated REV (keyword edits from T0; predictions written before the runs)
| Run | Change from T0 | Prediction |
|---|---|---|
| `T2_cut_noFp` | F′ off (`-porousFreeFluxForce`) | **calm**: no through-flow at the corner cell (max free \|U\| ≤ 1.5 m/s at 0.5 ms) |
| `T3_cut_t90` | θ 90° | weaker: corner pressure smaller, max free \|U\| ≤ half of T0 (4.2 m/s) |
| `T4_cut_noG` | G off (`porousFreeDarcyFaces=off`, also disables F′ and I) | inconclusive: original coupling (yarn drains, strip-bench evidence) |
| `T5_cut_noH` | H off (`-porousContactAngleWallLike`) | inconclusive: original contact-angle model has its own spurious currents (Study 2a) |
| `T6_cut_noI` | I off (`-porousFreeNoSlip`) | as T0 within 20 % (I acts on the tangential coupling only) |

### Phase 3 on the truncated REV — kr of the yarn/gap faces (scratch variants, `solver/`; predictions before the runs)
K1 (`solver/K1_porousFreeKrPorous.patch`, binary `hybridPorousInterFoam_K1`, keyword `porousFreeKrPorous on`): on
porous/free Darcy faces both kr from the porous cell instead of the upstream cell of each phase. K2 (`solver/K2_porousFreeKrAirPorous.patch`, binary
`hybridPorousInterFoam_K2`, keyword `porousFreeKrAirPorous on`): the air kr only, water kr upwinded as now. Keyword
off: K1 and K2 bit-identical to the installed solver (bench N0, 90 steps, 11 fields at 2 writes; 2026-10-29).
| Run | Change from T0 | Prediction |
|---|---|---|
| `T7_cut_K1` | K1 | corner pump suppressed: corner-cell air through-flow < 0.5 m/s and max free \|U\| ≤ 1.5 m/s at 0.5 ms; side effect: gap water drains more slowly into the drier yarn (water kr from the yarn), more gap water than T0 |
| `T8_cut_K2` | K2 | corner pump suppressed as T7; gap water as T0 within 10 % |

### Results phases 2 and 3 on the truncated REV (2026-10-29)
- **T1 (base pc): calm, pass.** Per-step max free |U| 3.3 (start-up) / 2.2 / 1.6 / 1.9 / 1.7 / 2.0 / 1.1 / 1.0 / 0.8 / 0.7
  / 0.7 m/s per 0.05 ms; 0.72 m/s at 0.5 ms, no free cell above 1 m/s from 0.4 ms; gap water 289 cells at 0.5 ms (full
  REV job 3055: 289). The corner cell stays almost dry (α 0.006, |U| 0.03 m/s); the yarn cell below it is at α 0.87 (T0:
  0.61).
- **T2 (F′ off): calm prediction fails.** 1,481–2,151 free cells above 1 m/s at the writes (T0: 40–58), max 13 m/s
  (pure-air cells near the inlet from 0.02 ms: the spurious air currents at porous surfaces that F′ was introduced to
  remove). The corner cell fills as in T0 (α 0.278 at 0.5 ms) and **still pumps air**, steady: in through its free
  faces at +0.3 / +1.8 / +2.1 m/s, out through its yarn faces at −1.1 / −1.1 / −2.0 m/s (0.5 ms; 0.4 ms the same),
  cell p 227 Pa, |U| 1.3 m/s (T0: +1.6 / +4.7 / +4.9, −3.0 / −3.4 / −4.8, 517 Pa, 8.5 m/s, growing). The air enters
  against the pressure difference (free neighbours −9 to −46 Pa) in both: a force other than pressure (surface
  tension) drives it; F′ amplifies it ×2–3 and makes it grow.
- **T7 (K1, both kr of the yarn/gap faces from the yarn): pump absent, but its precondition too.** Per-step max free
  |U| 1.7–2.0 m/s from 0.2 ms (fastest cells in the inlet row); the corner cell stays dry (α 0.0000, face velocities
  ≤ 0.17 m/s); the gaps drain much faster into the yarns: gap water 839 / 480 / 312 / 206 / 139 cells at 0.1–0.5 ms (T0
  928 / 620 / 498 / 437 / 395). Prediction ("more gap water") fails: K1 changes the gap–yarn water exchange itself,
  not a candidate fix; inconclusive for the air leak (K2 tests it).
- **T3 (θ 90°): prediction (weaker) fails; inconclusive for the corner.** Much worse everywhere: per-step max free
  |U| 9.2 / 10.3 / 14.1 / 14.0 / 15.2 / 16.8 / 21.9 / 19.5 / 21.5 / 21.5 m/s per 0.05 ms from 0.05 ms, 2,153 → 8,312 free
  cells above 1 m/s at 0.1 → 0.5 ms (T0: 40–58), 3,992 steps (dt median 1.1e-7 s). The gap water does not climb (top
  0.09–0.21 mm, 154 cells at 0.5 ms) and the corner cell stays dry (α 1e-4). θ 90° on the porous surfaces is strongly
  unstable here (cf. `2D_bench_t120`, stopGuard at 1.71 ms).
- **T8 (K2, air kr of the yarn/gap faces from the yarn, water kr upwinded): pump suppressed, pass; gap water as T0,
  pass.** Per-step max free |U| after 0.2 ms 0.9–2.0 m/s, no step above 5 m/s (T0: 8.6 m/s, 32 %); free cells above
  1 m/s 58 / 22 / 0 / 5 / 2 at 0.1–0.5 ms; gap water 918 / 624 / 506 / 446 / 407 cells (T0 928 / 620 / 498 / 437 / 395,
  within 3 %); y-yarn front identical; 1,306 steps, dt median 3.9e-7 s (T0 2.7e-7); budget 2.7e-10 of the water. The
  corner cell still fills, slower (α 0.019 / 0.070 at 0.4 / 0.5 ms; T0 0.148 / 0.285), p 3 / 35 Pa, face velocities
  ≤ 0.4 m/s; the free cell below it (y 0.211 mm) builds pressure (96 / 249 Pa) without fast flow. **The air leak
  through the yarn/gap faces with the gap cell's air mobility feeds the pump.**
  **Continued to 1 ms** (from its 0.5 ms processor writes, `log.hybridPorousInterFoam.cont`): per-step max free |U|
  per 0.05 ms 1.7 / 2.6 / 2.6 / 2.3 / 2.1 / 1.9 / 1.8 / 1.7 / 1.6 / 1.6 / 1.6 m/s (0.5–1.0 ms); the corner cell fills to
  α 0.21 (0.8–1.0 ms) and builds p 416 Pa (T0: 517 Pa at α 0.28), |U| 1.77 → 1.36 m/s (0.8 → 1.0 ms), the fastest free
  cell at 0.6–0.8 ms; gap water 380 → 345 cells, y-yarn front 0.45 → 0.51 mm. K2 keeps the corner pressure but not the
  leak: no growing pump, a steady and decaying ~1.5–2.6 m/s at the corner (×4–5 below T0 at 0.5 ms).
- **Bench regressions (`N10_bench_ref`, `N11_bench_K2`, `N12_bench_G2`: `../standardOpenBC/bench_B` with its own dry
  walls and 0.2 mm ramp, 2 ms; `meshing_strat_trial/2D_bench/check.py` run on each).** N10 (installed solver) is
  bit-identical to the stored bench_B (α, U, p, φ, alphaPhi0 at 1 and 2 ms). All 10 bench checks pass in all three.

  | 2 ms | N10 installed | N11 K2 | N12 G2 |
  |---|---|---|---|
  | meniscus 1 / 2 ms | 0.430 / 0.790 mm | 0.430 / 0.790 | 0.450 / 0.810 |
  | wall front 1 / 2 ms | 0.750 / 1.170 mm | 0.750 / 1.170 | 0.770 / 1.170 |
  | wall water 2 ms | 372.4 cell vol. | 372.4 | 368.6 (−1.0 %) |
  | max \|U\| | 1.19 m/s | 1.19 | 1.21 |
  | imbalance / stored | 4.6e-15 | 6.1e-15 | 5.3e-15 |

  K2: no visible change (air only leaves the walls here). G2: meniscus +1 cell (+2.5 % at 2 ms), wall water −1 %:
  prediction (within 5 %) passes, direction opposite to the guess (the wetting meniscus's own suction, κ < 0, lowers
  the water pressure the wall faces see in the meniscus cells).
- **T9 (G2, α_min 1e-3): fails, stopped at 46 µs** (1,100 steps in 444 s). dt held at 1–6e-8 s by the dSmax limit
  (Coats 2–3e-7 s): yarn cells at the inlet (y 0.01–0.03 mm, x 0.45–0.47 mm, z −0.06 mm) swing α 0.86–0.90 at up to
  3e5 1/s; the fastest free cells (3–4 m/s) hold α ≈ 0.001, just inside the band. In a cell with a trace of water the
  curvature is meaningless, but G2 gives it the water pressure p + (1 − α)σκ: a strongly negative κ there pulls
  water out of the adjacent wet yarn. The VOF capillary pressure must be restricted to cells with a real interface:
  variant G2b (below).
- **T10 (G2b, α-weighted VOF capillary pressure): corner pump removed.** Per-step max free |U| per 0.05 ms 37.9
  (start-up) / 3.8 / 3.4 / 1.8 / 2.5 / 2.2 / 2.3 / 2.0 / 1.7 / 1.1 / 1.1 m/s (T0: … 4.9 / 8.6 / 8.6); no step above 5 m/s;
  free cells above 1 m/s 75 / 27 / 4 / 4 / 2 at 0.1–0.5 ms; corner cell α 0.029 / 0.041 at 0.4 / 0.5 ms, **p −13 Pa**
  (T0 231 / 517 Pa; K2 3 / 35 Pa), face velocities ≤ 0.53 m/s; gap water 925 / 609 / 466 / 429 / 405 cells (T0 928 /
  620 / 498 / 437 / 395), gap water top 0.19 mm (T0 0.17), y-yarn front 0.451 mm at 0.5 ms (T0 0.431); 2,144 steps,
  dt median 3.3e-7 s, budget 4.1e-12 of the water. Predictions: no dSmax collapse **pass**; corner face velocities
  < 0.5 m/s **marginal** (0.53); per-step max ≤ 2 m/s after 0.2 ms **fails narrowly** (2.5 at 0.2–0.35 ms, 1.1 at
  the end); gap water within 30 % **pass**. **New effect: 370 dt dips** (below half the median, min 1.8e-8 s; 15
  episodes at 0.10–0.14 and 0.29–0.37 ms): dSmax set by yarn cells next to the top of the initial gap water column
  (y 0.09–0.13 mm, α 0.55–0.87, |dα/dt| 3–6e5 1/s, |U| 0.1–0.3 m/s): a stiff, bounded water exchange at gap menisci
  touching a yarn (the face now feels the meniscus curvature, explicit in time).
- **N13 (G2b, bench): all 10 checks pass**, as G2 (N12): meniscus 0.450 / 0.810 mm at 1 / 2 ms, wall front 0.770 /
  1.170 mm, wall water 374.5 cell volumes (N10 372.4, +0.6 %), max |U| 1.21 m/s, budget 5.1e-15: prediction **pass**.

**Summary of the candidate fixes (2026-10-29):** K2 (air kr of yarn/gap faces from the yarn) weakens the corner pump
to a steady, decaying ~1.5–2.6 m/s to 1 ms (the corner pressure still builds to 416 Pa), no other change seen (bench
identical, gap water within 3 %, no dt dips, 23 % fewer steps than T0). G2b (pc = −w(α)σκ in free interface cells)
removes the pressure build-up (corner p at the air level), bench meniscus +1 cell, gap water within 7 %, but adds
stiff exchange episodes at gap menisci touching yarns (dt dips on 17 % of the steps, 26 % more steps than T0).
Untested: K2 + G2b together, the full REV_lowpc past 6.5 ms, the base REV past 15 ms (its weaker corner pattern),
the slit regression (K 1e-20 walls carry almost no Darcy flux: expected unchanged).
- Code checked (`pEqn.H:38`, `:65`, solver `be1a3ab`): the surface-tension force enters `phiHbyA` on all non-solid
  faces, and the flux of every Darcy face (porous/free faces with G) is then replaced by the Darcy flux, which has no
  surface-tension term; free cells have pc = 0 (G), so the yarn/gap faces use the free cell's VOF pressure as both
  phase pressures.

### Phase 4 — variant G2: the VOF capillary pressure in free interface cells (predictions before the runs)
**Why** (phases 1c–3, `pEqn.H:38/:65`): the surface-tension force acts on free faces only; the yarn/gap Darcy faces use
the free cell's VOF pressure as both phase pressures (G: pc = 0 in free cells). In a partly filled free cell the VOF
pressure holds part of the Laplace jump (p ≈ p_air + α·σκ across a CSF band), so the Darcy faces see a wrong air and
water pressure and bleed the jump off: no balanced-force state. **Change** (`solver/G2_porousFreeVofPc.patch`, binary
`hybridPorousInterFoam_G2`, keyword `porousFreeVofPc on`, `porousFreeVofPcAlphaMin` 1e-3): in free cells with
α_min < α < 1 − α_min, pc = −σκ (`mixture.sigmaK()`, κ = −∇·n̂, p_water − p_air = σκ) instead of 0, in the same mixture
form as the yarns (p = p_air − α·pc): the porous/free Darcy faces (`phiDarcyExplicit`, `phiWetting`,
`phiNonWetting`) then use p_air = p − α·σκ and p_water = p + (1 − α)·σκ on the free side. Nothing else uses pc in
free cells (free/free faces: CSF; porous/porous faces: porous pc). Outside the band pc = 0 as G.
| Run | Change | Prediction |
|---|---|---|
| bit-identity | G2 binary, keyword off, bench N0 90 steps | identical to the installed solver |
| `T9_cut_G2` | T0 + G2 | **corner pump removed**: corner-cell face velocities < 0.5 m/s at 0.5 ms, per-step max free \|U\| ≤ 2 m/s after 0.2 ms (T0 8.6); the water collecting in the corner is absorbed by the yarn (water pressure p + (1 − α)σκ high if κ > 0); gap water within 30 % of T0 |
| `N9_G2_bench` (later) | `../standardOpenBC/bench_B` + G2 | regression: meniscus and wall front at 2 ms within 5 % of bench_B (the meniscus suction now acts on the yarn surface: wall front possibly ahead, meniscus possibly lower) |

### Phase 4b — variant G2b: G2 weighted by α (predictions before the runs)
pc_free = −w(α)·σκ with w = clamp((α − α_min)/Δ, 0, 1)·clamp((1 − α_min − α)/Δ, 0, 1), α_min 0.05, Δ 0.1
(`porousFreeVofPcAlphaMin`, `porousFreeVofPcAlphaRamp`): 0 below α 0.05 and above 0.95, 1 for 0.15–0.85 (the corner
cell pumped at α 0.12–0.28). `solver/G2b_porousFreeVofPc.patch`, binary `hybridPorousInterFoam_G2b`.
| Run | Change | Prediction |
|---|---|---|
| bit-identity | G2b binary, keyword off, bench N0 90 steps | identical to the installed solver |
| `T10_cut_G2b` | T0 + G2b | no dSmax collapse (dt median ≥ 1.5e-7 s); corner pump removed (corner face velocities < 0.5 m/s, per-step max free \|U\| ≤ 2 m/s after 0.2 ms); gap water within 30 % of T0 |
| `N13_bench_G2b` | bench_B + G2b | all 10 bench checks pass, meniscus and wall front within 5 % of N10 |

**K2 regressions on the validated cases (2026-10-29, scratch copies, keyword on vs the installed solver):** 1D column
(`../standardOpenBC/1D_ref`, 2 ms, 3,445 steps): bit-identical (11 fields at 1 and 2 ms; no porous/free faces). Slit
with impermeable porous walls (`meshing_strat_trial/slit_test/P_w8_t60_K1e-20`, 2 ms, 1,382 steps): U, p, φ, Uwetting,
UnonWetting bit-identical, α within 1.1e-25, alphaPhi0 within 1e-32 (K 1e-20 walls carry no Darcy flux). Bench with
K 1e-11 walls (N11): identical numbers (above).

### Phase 5 — K2 in the original failing configuration (θ 40°; decided with the user 2026-10-29: continue with K2)
| Run | Change | Prediction (before the runs) |
|---|---|---|
| `T11_cut_lowpc_t40` | cut REV, VG 1000 Pa / 0.4, θ 40° (= job 3059 cut), installed solver, to 1 ms | reproduces 3059: per-step max free \|U\| > 5 m/s by 0.5 ms; gap water grows above T0's (3059 full REV 1,228 cells at 0.5 ms vs 395 at θ 60°); gap water top past 0.17 mm by 1 ms |
| `T12_cut_t40_K2` | T11 + K2, to 2 ms | no pump growth: per-step max free \|U\| ≤ 3 m/s after 0.2 ms to 2 ms, no stopGuard; gap water within 10 % of T11 at 0.5 and 1 ms |

### Phase 5 results, final (2026-10-29; T11 to 1 ms, T12 to 2 ms, both ended normally)
| | T11 θ 40°, installed | T12 θ 40° + K2 |
|---|---|---|
| steps / dt median / dips | 3,678 / 2.68e-7 s / 0 | 5,311 / 3.86e-7 s / 0 |
| per-step max free \|U\| after 0.2 ms, steps > 5 m/s | 14.0 m/s, 66 % | 3.55 m/s (0.4–0.55 ms), 0 % |
| per-step max free \|U\| from 0.6 ms | 6.9–14.0 m/s (every step > 5) | 1.3–1.6 m/s to 2 ms |
| free cells > 1 / > 5 m/s at 0.5 / 1 ms | 124 / 2, 285 / 16 | 91 / 0, 67 / 0 |
| gap water at 0.5 / 1 ms | 1,221 / 1,461 cells | 1,257 / 1,505 (+3 %) |
| y-yarn front, mean porous S at 1 ms | 0.531 mm, 0.4554 | 0.511 mm, 0.4579 |
| imbalance / water | 9.6e-9 | 2.4e-9 |

T11 = job 3059 (full REV at 1 ms: gap water 1,461.1, y-yarn front 0.511 mm, max free |U| 14.9 m/s at the write).
T12 from 1 to 2 ms: gap water 1,505 → 1,848 cells, gap water top 0.211 → 0.231 mm (past the θ 60° valve, as at θ 40°
in 3059), y-yarn front 0.511 → 0.632 mm, mean porous S 0.458 → 0.527, max free |U| at the writes 1.25–1.50 m/s.
Predictions: T11 reproduces 3059 **pass**; T12 no stopGuard **pass**, gap water within 10 % of T11 **pass** (3 %),
≤ 3 m/s after 0.2 ms **missed at 0.4–0.55 ms** (3.3–3.5 m/s transients at partly filled cells), **pass** from 0.6 ms
to 2 ms. **K2 suppresses the failure mode of job 3059 in its own configuration.**

### Phase 5 results (preliminary, superseded above, 2026-10-29 17:30: T11 at 0.93 of 1 ms, T12 at 1.27 of 2 ms; locator, per 0.1 ms)
| per-step max free \|U\| (steps > 5 m/s) | 0.1–0.4 ms | 0.4–0.5 | 0.5–0.6 | 0.6–0.7 | 0.7–1.0 | 1.0–1.3 |
|---|---|---|---|---|---|---|
| T11 θ 40°, installed | 3.0–4.4 m/s (0) | 7.9 (205 of 415) | 7.9 (all) | 14.0 (all) | 11.8–12.6 (all) | — |
| T12 θ 40° + K2 | 1.4–3.1 (0) | 3.3 (0) | 3.5 (0) | 1.5 (0) | 1.4–1.5 (0) | 1.4–1.5 (0) |

T11 reproduces job 3059 (full REV: 7.9 m/s at 0.5 ms, 14.9 at 1 ms): prediction **pass**. T12: never above 5 m/s,
steady 1.4–1.5 m/s from 0.6 ms, ~270 steps per 0.1 ms (T11 320–430); prediction (≤ 3 m/s after 0.2 ms) **narrowly
missed at 0.4–0.6 ms** (3.3 / 3.5 m/s, transient peaks at partly filled cells, α 0.09–0.38, each 0.03–0.07 ms), pass
after; final verdict and gap water at the end of T12 (watcher, `log.watch`).

## Phase 2 — ablations (planned; on the runs that reproduce, keyword edits only)
| Run | Change | Tests |
|---|---|---|
| A1 | θ 90° | no meniscus suction at the wall (H still imposes 90°): the near-equilibrium state moves to pc ≈ 0 |
| A2 | θ 20° | closer to the apparent angle on a wet textured surface (Cassie, wet pores) |
| A3 | `-porousContactAngleWallLike` | H off (original contact-angle model; has its own spurious currents, Study 2a predictions) |
| A4 | `-porousFreeFluxForce` | F′ off |
| A5 | `-porousFreeNoSlip` | I off |
| A6 | `porousFreeDarcyFaces=off` | G off (also disables F′ and I) |

## Phase 3 — kr of the yarn/gap faces (planned; needs scratch solver variants, patch saved in `solver/`)
`updateVariables.H` upwinds kr1f/kr2f by each phase's flux (C) on all porous faces; on a yarn/gap face with water
flowing gap → yarn the water kr comes from the gap cell's VOF α through Brooks–Corey. Variants: K1 kr from the yarn
cell on yarn/gap faces; K2 kr = 1 for the phase that fills the gap cell. Built as in `../PLAN.md` ("Solver
versions"), bit-identity checked with the switch off. To decide after phases 1–2.

## Results
### Phase 1 (2026-10-29, `be1a3ab`, laptop serial, ~4 min per run; `summary.md` from `analyse.py`)

| Run | max free \|U\| per step > 0.2 ms | steps > 5 m/s | dt median / dips / min | max free \|U\| at writes | smeared cells 0.5 / 1 / 2 ms | meniscus 1 / 2 ms | wall S 0 → 2 ms | imbalance / water | Prediction |
|---|---|---|---|---|---|---|---|---|---|
| N0_lowpc_S091 | 1.08 m/s | 0 % | 1.47e-6 s / 0 / 1.5e-6 | 1.08 | 12 / 18 / 40 | 0.68 / 1.22 mm | 0.910 → 0.922 | −1.4e-14 | reproduces: **fail** (calm) |
| N1_lowpc_S097 | 1.07 | 0 % | 1.47e-6 / 0 / 1.5e-6 | 1.07 | 6 / 6 / 6 | 0.68 / 1.22 | 0.970 → 0.968 | 9.9e-15 | fast, walls feed the gap: **fail** (calm, wall S −0.002) |
| N2_lowpc_S050 | 1.28 | 0 % | 6.9e-7 / 426 / 1.0e-7 | 1.33 | 16 / 38 / 78 | 0.52 / 0.98 | 0.500 → 0.687 | −1.5e-14 | calm: \|U\| **pass**; dips (Coats limit while the walls imbibe, free Courant low) → **inconclusive** by the written criterion |
| N3_REVpc_S091 | 1.28 | 0 % | 1.47e-6 / 3 / 5.9e-7 | 1.25 | 6 / 26 / 46 | 0.66 / 1.20 | 0.910 → 0.946 | −1.6e-14 | calm: \|U\| **pass**, 3 dips → **inconclusive** by the written criterion |
| N4_REVpc_S0995 | 1.18 | 0 % | 1.47e-6 / 0 / 1.5e-6 | 1.18 | 6 / 6 / 8 | 0.68 / 1.22 | 0.995 → 0.995 | −1.4e-14 | decisive: not informative (N0 calm) |

"Free > 1 m/s" reaches 156–160 cells at a write in N0, N1, N3, N4: the water column in the gap during the fast early
rise (meniscus 0.68 mm at 1 ms, mean speed ~0.6 m/s), not interface cells. Meniscus: N0 1.22 mm at 2 ms (predicted
between bench_B 0.79 and the impermeable-wall rise 1.16, towards 1.16: slightly above it). dt: the capillary-wave
limit (1.47e-6 s) in all runs but N2 (Coats, walls imbibing); the REV ran at 1.2–4e-7 s.
**Conclusion (decision table row 3): the near-equilibrium state alone, on a flat 2D wall with uniform saturation and
a straight 8-cell gap, does not produce the fast currents, for either pc curve.** Differences from the REV site, to
test next: a saturation gradient along the wall (REV flank 0.97 → 0.83 over 0.16 mm, water flowing along the yarn);
θ 40°; the gap width (REV gaps 4–15 cells); 3D staircase edges and corners (the REV fast cells have 1–3 porous
neighbours; H, F′, I on 3D edges/corners are untested, `../../NOTES_solver.md`); gap water arriving from below
through a crossing; dt (REV 5–10× smaller).
