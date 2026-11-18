# Is the high capillary pressure the cause of the transverse mode? pc0 and K series on the porous bench (2026-11-18)

**Question (user):** the original solver diverged on the yarn in 2D/3D. A removed the front inversion, but with A alone a
transverse α pattern still grows on the all-porous bench, and only B removes it (`NOTES_solver.md`, "A, B"). Is the large
capillary pressure (VG pc0 5000 Pa) what drives it? Lower pc0 by 10 and 100, and K by 10 and 100 for comparison, and check
whether the transverse spread still grows. A curiosity run, not on the critical path; also a candidate figure for justifying B in
the thesis.

**Case:** `case/` = `../bench_ddtCorr/case` (copied unchanged): column 0.55 × 3.446 × 0.237 mm, 5 × 172 × 3 cells (110 × 20 ×
79 µm), all porous, ε 0.5, K 1e-11 m², VG pc0 5000 Pa m 0.5, Brooks–Corey n 3, water/air, gravity −y, dry 0.002 with the
0.2 mm ramp, reservoir inlet (α 0.99, air at 0 Pa), symmetry sides, fixed dt, `transverseSpread` printed every step (max over
the 172 rows of max − min α across the 15 cells of the row; max |Ux|, |Uz|; mean α).
`./makeRun.sh <name> <pcDiv> <KDiv> <dtMul>`: pc0 = 5000/pcDiv, K = 1e-11/KDiv, dt = 1e-7·dtMul, end 2e-4·dtMul (2,000 steps
in every run), the uniform initial p (first guess) scaled with pc0. Nothing else changes: gravity, fluids, mesh, tolerances
(OpenFOAM normalises the residuals by the field scale, so the p tolerance needs no scaling).

**Solver:** `hybridPorousInterFoam_b0c0f67` = commit `b0c0f67` (A only, on the OF9 port `be54696`), built 2026-11-18 from a
`git archive` export in the session scratchpad (`EXE` renamed, nothing written in the solver repo); it links today's shared
libraries, whose only change since `b0c0f67` is H in `porousInterfaceProperties.C` (inactive without its keyword; class
layout unchanged). Check: run A0 must reproduce `../bench_ddtCorr/log.ii_A_c1` (scratch build `b0c0f67` + the ddtCorr
coefficient patch at × 1).

## Design: two numbers set the discrete problem

Without the momentum equation (Darcy limit), pc0 and K would act only through the capillary diffusivity D ∝ K·pc0/(μ·ε): a
run with pc0 ÷ 10 would be the base run at a time scale × 10, and so would a run with K ÷ 10. The momentum equation of the A
build, (1/ε)·ρ·∂U/∂t + Drag·U = …, Drag = 1/(K·λt) (`UEqn.H`, `updateVariables.H`), adds the ratio of inertia to drag per
step. With the fluid properties, ε and the mesh fixed, two numbers set the discrete problem:
- **Co**, the capillary step size, ∝ dt·K·pc0 (the Coats number of the explicit capillary update; the 1D column at 20 µm
  runs at ~6e-7 s for Coats 0.5, so dt 1e-7 s is below that limit);
- **Λ = ρK/(μ·ε·dt)**, inertia over drag per step: 200 in water cells at the base (11 in air-filled cells, ρ 1 and μ 1.76e-5).

(pc0 enters only through Co; a third group, K·√(ρ·pc0)/(μ·ε·Δx), the inertial capillary oscillation over the drag damping, is
√(Co·Λ), not independent. Gravity is the exception: it scales with K but not with pc0, so in the pc0 runs it weighs × 10 / × 100
more against the capillary forces, at most ~10 % of the front-scale pressure gradient at pc0 50 Pa, much less at the grid scale.)

| Run | pc0 (Pa) | K (m²) | dt (s) | end (s) | Co / Co_base | Λ (water) | what it varies |
|---|---|---|---|---|---|---|---|
| A0 | 5000 | 1e-11 | 1e-7 | 2e-4 | 1 | 200 | base, = `log.ii_A_c1` |
| FP10 | 500 | 1e-11 | 1e-7 | 2e-4 | 0.1 | 200 | Co only (the user's hypothesis, cleanly) |
| FP100 | 50 | 1e-11 | 1e-7 | 2e-4 | 0.01 | 200 | Co only |
| FK10 | 5000 | 1e-12 | 1e-7 | 2e-4 | 0.1 | 20 | Co and Λ |
| FK100 | 5000 | 1e-13 | 1e-7 | 2e-4 | 0.01 | 2 | Co and Λ |
| SP10 | 500 | 1e-11 | 1e-6 | 2e-3 | 1 | 20 | Λ only |
| SP100 | 50 | 1e-11 | 1e-5 | 2e-2 | 1 | 2 | Λ only |
| SK10 | 5000 | 1e-12 | 1e-6 | 2e-3 | 1 | 2 | Λ only; **twin of SP100** (same Co, same Λ; not an exact twin, see Results) |
| SK100 | 5000 | 1e-13 | 1e-5 | 2e-2 | 1 | 0.02 | Λ only, near the steady (no-inertia) limit |

F = fixed dt (as written in the user's question), S = dt scaled with 1/(K·pc0) (same Co, same front travel per step, same
2,000 steps). In wicking time t* = t·(K·pc0)/(K·pc0)_base the S runs end at the base's 2e-4 s, the F runs at 2e-5 / 2e-6 s.

**Earlier runs on the same bench with A (`../bench_ddtCorr`, `benchDdtCorr.py`):**

| Run | Co / Co_base | Λ | growth / step | rate (1/s) | spread > 1e-2 at | max spread | end |
|---|---|---|---|---|---|---|---|
| (ii) A, ddtCorr × 1 | 1 | 200 | 1.064 | 6.2e5 | 9.4e-6 s | 0.20 | 2e-4 s |
| (e) A, ddtCorr × 0, dt 5e-8 | 0.5 | 400 | 1.44 | 7.3e6 | 4.9e-6 s | 0.27 | 2e-4 s |
| T1a, ddt(ρU) steadyState | 1 | 0 | — | — | 7e-7 s | 5e44 | crash, step 137 |
| T1b, steadyState + ddtCorr × 0 | 1 | 0 | 2.98 | 1.1e7 | 9e-7 s | 4e37 | crash, step 71 |
| (v) A + B + C (Darcy faces) | 1 | — | — | — | never | 1.3e-7 | 2e-4 s |

Removing inertia (Λ → 0) made the mode much faster and fatal; halving dt (Co ÷ 2, Λ × 2) made it faster too.

## Predictions (written before the runs, 2026-11-18)

Two candidate controls:
- **M1, the capillary forcing per step (user's hypothesis):** the mode is an explicit-capillary instability of the
  momentum-path flux, set by Co. Then FP10/FP100 and FK10/FK100 are calm and the S runs grow as A0 per step.
- **M2, the inertia/drag balance of the momentum path:** set by Λ, worst at Λ → 0 (T1a/T1b). Then the S runs grow faster as Λ
  drops, and FP10/FP100 (Λ unchanged) still grow.

The earlier runs point to M2 (Λ → 0 is the most violent case on record, and B, which removes the momentum path from the
porous faces, is the only fix). Predictions:
1. **Twins:** SP100 and SK10 give the same growth per step within ± 0.02 and the same outcome (both crash or both reach the
   end). Otherwise the two-number picture misses something (gravity at pc0 50 Pa, the Se clipping, the solver tolerances), to
   settle before reading the rest.
2. **SK100 (Λ 0.02) crashes within 300 steps**, as T1b (71 steps).
3. **S series ordered by Λ:** growth per step SK100 > SP100 ≈ SK10 > SP10 > A0 (1.064).
4. **FP10 still grows past spread 1e-2 before 2e-4 s; FP100 past 1e-3.** Lowering pc0 alone (Λ kept) slows the mode in seconds
   but does not remove it; in wicking time t* it appears no later than in A0.
5. FK10, FK100 (Co and Λ lowered together) grow faster per step than FP10, FP100 at the same Co.
6. A0 = `log.ii_A_c1` (all `transverse:` lines identical).

**Reading:**
- FP10 and FP100 stay ≤ 1e-3 with no growth phase, and the S runs grow as A0 per step → M1: the large pc per step is the
  cause; the hypothesis holds.
- FP10/FP100 still grow and the S runs get worse as Λ drops → M2: not the pc magnitude but the inertia/drag balance of the
  momentum-path flux; lowering pc0 only slows the mode in seconds. B is needed whatever pc0.
- FP calm and S worse → both: the mode needs both a strong capillary forcing per step and weak inertia.
- Any S run calm → a Λ window where A alone is enough on this bench (would matter for the B argument).

**Measured per run:** steps reached, crash or end, spread at step 2 (seed), growth per step and rate (1/s) in the exponential
window 1e-5 < spread < 1e-2 (as `benchDdtCorr.py`), first time with spread > 1e-2 (s and t*), max spread, max transverse |U|
over the Darcy velocity scale (∝ K·pc0), water taken up against the Darcy-limit reference (v) at the same t* (exact for the K
runs; for the pc0 runs gravity breaks the rescaling).

## Results (2026-11-18, laptop, serial, `hybridPorousInterFoam_b0c0f67`, ~1 min per run)

`../../.venv/bin/python benchPcK.py` (table, `bench_pcK_spread.png`). Logs `<run>/log.<run>` (git-ignored).

| Run | Co / Co_base | Λ | τ_I / τ_D | end | spread at step 2 | growth / step | spread > 1e-2 at step | max spread | spread at step 1000 / 2000 | max transverse U (base units) | uptake / (v) at t* |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1 | 200 | 5 | End | 2.9e-5 | 1.064 | 94 (9.4e-6 s) | 0.203 | 0.11 / 0.053 | 1.79 | 0.789 |
| FP10 | 0.1 | 200 | 0.5 | End | 4.6e-7 | — | never | 5.6e-7 | 2.8e-7 / 1.8e-7 | 5e-5 | 0.944 |
| FP100 | 0.01 | 200 | 0.05 | End | 5.5e-9 | — | never | 4.4e-8 | 4.0e-8 / 3.9e-8 | 2e-5 | 1.003 |
| FK10 | 0.1 | 20 | 0.05 | End | 3.1e-7 | — | never | 3.3e-7 | 1.4e-7 / 1.1e-7 | 2e-4 | 0.970 |
| FK100 | 0.01 | 2 | 5e-4 | End | 3.8e-10 | — | never | 3.1e-8 | 2.0e-8 / 3.1e-8 | 7e-6 | 1.070 |
| SP10 | 1 | 20 | 0.5 | End | 2.2e-5 | 0.991 (decay) | never | 2.3e-5 | 1.4e-6 / 9.0e-7 | 8e-4 | 0.967 |
| SP100 | 1 | 2 | 0.05 | End | 7.6e-6 | — | never | 8.0e-6 | 4.5e-6 / 2.9e-6 | 5e-3 | 0.953 |
| SK10 | 1 | 2 | 0.05 | End | 3.4e-6 | — | never | 3.4e-6 | 5.3e-7 / 3.5e-7 | 5e-4 | 0.967 |
| SK100 | 1 | 0.02 | 5e-4 | End | 4.1e-8 | — | never | 1.7e-7 | 1.3e-7 / 1.7e-7 | 9e-6 | 0.967 |
| (v) A + B + C | 1 | — | — | End | 2.5e-10 | — | never | 1.3e-7 | 1.25e-7 / 1.27e-7 | 1e-6 | 1 |

τ_I / τ_D defined below. Growth per step "—": the spread never runs through the window 1e-5–1e-2. Max transverse U in units of
the run's own velocity scale (÷ (K·pc0)/(K·pc0)_base). Uptake: water taken up since t = 0 over that of (v) at the same t*; (v)
also has C (upwinded kr, faster front), so the 3–5 % deficit of the calm S runs is mostly C, not the mode; A0's 21 % includes
the mode.

- **A0 = `log.ii_A_c1`:** all 2,001 `transverse:` lines identical (the build is the A of the 10-07 runs).
- **Only A0 shows the mode.** Every variant stays between 3e-8 and 2.3e-5 for 2,000 steps: seven decay from their step-2 seed
  or stay flat (×0.62–0.97 per 1,000 steps over the second half); FK100 and SK100 still creep up (×1.55 and ×1.23 per 1,000
  steps), to 3e-8 and 1.7e-7, the level of the A + B + C run, which creeps up the same way (2.5e-10 → 1.3e-7). A0 grows ×1.064
  per step (×1e27 per 1,000 steps) to 0.2. No crash anywhere, transverse velocities ≤ 5e-3 of the run's own velocity scale (A0:
  1.8).

**Correction to the design (found after the runs):** the momentum equation also has the Brinkman term (μ/ε)∇²U, whose ratio to
the drag μ/K is Da = K/Δx², set by K alone. With ρ, μ, ε and the mesh fixed the discrete problem has three numbers (Co, Λ, Da),
not two: SP100 and SK10 share Co and Λ but differ ×10 in Da, so they are not exact twins. The pc0 runs keep Da; the K runs lower
it.

**Scoring:**
1. Twins SP100 / SK10, same growth and outcome: same outcome (both calm, seed 7.6e-6 / 3.4e-6, no growth window); not an exact
   twin test (Da, above).
2. SK100 crashes within 300 steps: **fails** (calm to 2,000 steps, spread ≤ 1.7e-7).
3. S series ordered by Λ, all faster than A0: **fails** (all calm).
4. FP10 past 1e-2, FP100 past 1e-3: **fails** (max 5.6e-7 and 4.4e-8).
5. FK faster than FP at the same Co: **fails** (no growth in either).
6. A0 = `log.ii_A_c1`: passes.

M2 (Λ alone) is refuted: lowering Λ at fixed Co (S series) removes the mode instead of making it worse. M1 (Co alone) is refuted
too: SP10, SK10, SP100 and SK100 keep Co and are calm. The reading table's last row applies: there is a parameter range where A
alone is enough on this bench.

**What the data fit (interpretation, not tested on its own):** the mode needs both Co and Λ high, i.e. their product, which does
not contain dt: Co·Λ ∝ K²·pc0. Written as two times,
- τ_I = ρK/(μ·ε), the inertial relaxation time of the momentum-path velocity (2e-5 s at the base, water: 200 steps of 1e-7 s),
- τ_D = Δy²·μ·ε/(K·pc0), the capillary diffusion time over one cell (4e-6 s at the base, D = K·pc0/(μ·ε) = 1e-4 m²/s),

τ_I / τ_D = ρK²pc0/(μ²ε²Δy²) = 5 at the base and ≤ 0.5 in every variant. Every A run on this bench at 5 grows (A0, the ddtCorr
× 0 / × 0.1 runs, dt ÷ 2, the tight pressure solves: max spread 0.14–0.27, panel (c)); every run at ≤ 0.5 is calm. Read this
way, the mode appears when the momentum-path velocity relaxes more slowly than the capillary front crosses a cell: the flux lags
the capillary forcing (the lag found 2026-10-15 in `../bench_refinement`, Darcy model with the momentum path). dt does not
enter, which fits dt ÷ 2 not helping; Δy² does, which fits the earlier divergence on the refined mesh (`../bench_refinement`,
original solver, not A). Threshold between 0.5 and 5, not located.
- **Exception, not explained:** T1a/T1b (time derivative removed, `steadyState`) crashed within 71–137 steps, while SK100 (Λ 0.02,
  inertia 2 % of the drag) is calm. So T1 is not the Λ → 0 limit of this series; another failure (hypothesis, not tested: a
  steady pressure–velocity loop with relaxation factors 1). This also takes back the basis of predictions 2–3.

**Answer to the question:** the high capillary pressure is part of the cause, not the cause on its own. pc0 ÷ 10 removes the mode
at fixed dt (FP10) and at the same capillary step size (SP10), but K ÷ 10 does the same, and K counts twice: what matters is
K²·pc0 (over Δy²), not pc0 (every run at τ_I / τ_D = 5 grows, every run at ≤ 0.5 stays calm over its 2,000 steps; where in
between the mode starts is not located, and no run shows that A alone suffices below some value, see "Claims for the thesis"
at the end). **For B:** with the planned yarn values the number sits at or above the unknown threshold at 20 µm
(Gebart Kpar 4.2e-12 with pc0 5000 Pa: 0.9; with the fibre-bundle estimate pc0 ≈ 10–19 kPa: 1.7–3.4) and above it at 10 µm
(× 4), so A alone would not be safe on the REV meshes; B removes the momentum path from the porous faces, so the question does
not arise with B (and B is needed anyway for the Darcy limit and as the base of F and G).

**Not done (proposals, predictions to write first):** (1) direct test of the group: K ÷ 10 with pc0 × 100 (τ_I / τ_D = 5 again,
Co × 10 at fixed dt, Λ ÷ 10, Da ÷ 10): should grow as A0 if K²·pc0 is the control; (2) the threshold: pc0 ÷ 2, ÷ 3 (2.5, 1.7);
(3) T1 against SK100: SK100's K and dt with the time derivative removed. ~1 min each.

## Follow-up 1: high pc with low K (asked by the user, 2026-11-18)

Does a high pc0 work with A alone when K is low enough? Two runs, same build, same bench:

| Run | pc0 (Pa) | K (m²) | dt (s) | end (s) | Co / Co_base | Λ | Da / Da_base | τ_I / τ_D |
|---|---|---|---|---|---|---|---|---|
| HP10_K10 | 50,000 | 1e-12 | 1e-7 | 2e-4 | 1 | 20 | 0.1 | 0.5 |
| HP100_K10 | 500,000 | 1e-12 | 1e-8 | 2e-5 | 1 | 200 | 0.1 | 5 |

HP10_K10 is the user's case (high pc, low K: K·pc0 as the base, so the same wicking time scale). HP100_K10 is the direct test of
the K²·pc0 reading: dt ÷ 10 keeps Co and Λ exactly at A0's values, so it differs from A0 only by Da (÷ 10) and the gravity weight
(÷ 100 against the capillary forces).

**Predictions (before the runs):**
- HP10_K10 calm: no growth window, max spread ≤ 1e-4, no crash (as FP10 and SP10, the other runs at 0.5).
- HP100_K10 grows as A0: spread > 1e-2 within 300 steps, growth per step 1.03–1.10, max spread ≥ 0.05.
**Reading:** both as predicted → K²·pc0 (over Δy²) holds also with high pc, and a high pc is safe with A alone if K is low
enough. HP100_K10 calm → the reading is wrong; since Co and Λ are A0's, the Brinkman number Da (lower: calmer) would then matter,
and the calm K runs of the series may be due to Da rather than to K²·pc0. HP10_K10 growing → the threshold is below 0.5 or Da
matters the other way.

**Results (2026-11-18, same build, ~1 min each):**

| Run | τ_I / τ_D | end | spread at step 2 | growth / step | spread > 1e-2 at step | max spread | spread at step 500 / 1000 / 2000 | max transverse U (base units) | mean α at end |
|---|---|---|---|---|---|---|---|---|---|
| A0 | 5 | End | 2.9e-5 | 1.064 | 94 | 0.203 | 0.125 / 0.111 / 0.053 | 1.79 | 0.04904 |
| HP100_K10 | 5 | End | 2.9e-5 | 1.065 | 77 | 0.244 | 0.131 / 0.103 / 0.057 | 1.79 | 0.04904 |
| HP10_K10 | 0.5 | End | 2.2e-5 | 0.991 (decay) | never | 2.2e-5 | 2.3e-6 / 1.4e-6 / 8.9e-7 | 9e-4 | 0.05319 |
| SP10 (series) | 0.5 | End | 2.2e-5 | 0.991 (decay) | never | 2.3e-5 | 2.3e-6 / 1.4e-6 / 9.0e-7 | 8e-4 | 0.05322 |

- **Both predictions pass.** HP100_K10 is A0 again: same growth per step, same saturation level, same transverse velocity in
  the run's own scale, same mean α to 5 digits, with pc0 × 100 and K ÷ 10. HP10_K10 (pc0 50 kPa, K 1e-12) is calm and follows
  SP10 to 2 digits.
- **Da does not matter here:** HP100_K10 differs from A0 only by Da ÷ 10 (and gravity), HP10_K10 from SP10 only by Da ÷ 10 (and
  the gravity weight): both pairs match. The Brinkman term is negligible at Da ≤ 0.025, so the problem is set by Co and Λ after
  all (the design's two numbers hold in practice), and the mode by their product, τ_I / τ_D ∝ K²·pc0/Δy².
- **Answer:** on this bench pc0 50 kPa with K 1e-12 (τ_I / τ_D 0.5) stays calm over the base's whole wicking time (Co as the base,
  2,000 steps), and pc0 500 kPa with K 1e-12 grows as the base: K²·pc0 (over Δy²) controls the mode, not pc0 alone. This is not
  shown to be a safe range for A alone (threshold not located, ÷ 100 runs at Δt 1e-7 s not covered over the stretched time); B
  stays in every run (claims at the end).

## Follow-up 2: the slit with the original solver (asked by the user, 2026-11-18)

Does the original solver (momentum equation as built, none of B, E, G, H wall-like, F′, I) run the slit bench when K²·pc0 is in
the calm range? Case: `meshing_strat_trial/2D_bench` (porous wall 8 cells | free gap 8 cells | porous wall 8 cells, 100 × 1 × 24
cells of 20 µm, θ 60°, walls dry 0.002 with the 0.2 mm ramp, 0.1 mm water column in the gap, Coats dt, 2 ms), copied by
`slit/makeSlit.sh <name> <pcMul> <KDiv> <solver> [orig]` (pc0 and the wall K changed; with `orig` the keywords of the modified
solver commented out; includes pointed at `meshing_strat_trial/tools`). Safe values: pc0 × 10, K ÷ 10 (50 kPa, 1e-12: τ_I/τ_D
0.5, HP10_K10; K·pc0 unchanged, so the wall wicking has the same time scale and the same Coats dt as the base).

| Run | Solver | pc0 (Pa) | wall K (m²) | τ_I / τ_D |
|---|---|---|---|---|
| O_base | `be54696` (original) | 5,000 | 1e-11 | 5 |
| O_safe | `be54696` | 50,000 | 1e-12 | 0.5 |
| A_base | `b0c0f67` (original + A) | 5,000 | 1e-11 | 5 |
| A_safe | `b0c0f67` | 50,000 | 1e-12 | 0.5 |
| R_safe | installed `4bb5d2e`, all keywords of `2D_bench` | 50,000 | 1e-12 | 0.5 |

R_safe is the reference at the safe values (the base values with the installed solver = `2D_bench`, 2026-10-13: all 10 checks
pass, meniscus 0.79 mm, wall front 1.15 mm at 2 ms).

**Predictions (before the runs):**
- **All four O_/A_ runs fail within the first ~20 steps, independent of τ_I/τ_D**, by the Solidf bug that E fixed (both builds
  recompute Solidf = interpolate(Solid) without clipping, so the porous/free faces carry half the porous capillary flux with K_f
  ≈ 0.5 m² and the gap cell's VG pc, ~1e4·pc0 at α 0): the wall cells next to the gap empty in one step, then p and dt collapse
  (stopGuard at dt 1e-14 or a crash), as the strip bench on 2026-10-12. The safe runs fail no later than the base runs (that
  bug flux scales with pc0, × 10).
- R_safe runs to 2 ms without stopGuard, budget closed, α bounded; wall front within 15 % of 1.15 mm (same K·pc0); meniscus
  below the base 0.79 mm (the walls' suction at the surface is × 10, the gap meniscus suction is unchanged, so the walls draw
  more water out of the gap).
**Reading:** the four fail early, alike → the original solver cannot run a porous/free case at any pc or K: the first failure
is the Solidf bug, not the transverse mode, and the pc question on a slit needs at least E (and G, without which the 2026-10-12
strip drained). The safe runs last clearly longer than the base runs → K²·pc0 matters there too, to look at.

**Results (2026-11-18):**

| Run | Solver | τ_I / τ_D | steps | end |
|---|---|---|---|---|
| O_base | `be54696` | 5 | 6 | stopGuard at t = 1.23e-8 s (dt 3.5e-15 s, dSmax limit 8e-16 s) |
| O_safe | `be54696` | 0.5 | 6 | stopGuard at t = 1.23e-8 s (dt 3.4e-15 s) |
| A_base | `b0c0f67` | 5 | 5 | stopGuard at t = 1.23e-8 s (dt 3.3e-15 s) |
| A_safe | `b0c0f67` | 0.5 | 5 | stopGuard at t = 1.23e-8 s (dt 3.3e-15 s) |
| R_safe | installed, all keywords | 0.5 | 8,501 | 2 ms, all 10 `check.py` checks pass |

- **The four old-solver runs fail at step 5–6, base and safe alike** (prediction 1 passes). Located with a write per step (scratch
  reruns of O_base and A_base): in step 1 only the wall cells touching the gap jump, at the edge of the wetted ramp (x cells 3–6):
  O_base empties them (α 0.45 → 0) while the gap cell beside them fills (0 → 0.27); A_base swings them 0.55 → 1.0 and back the next
  step. Elsewhere in the walls α changes ≤ 0.1 (O_base) and ≤ 3e-4 (A_base) in that step. Same pattern as the 2026-10-12 strip
  (Solidf bug, fixed by E). The dSmax limit then takes dt to ~1e-16 s and stopGuard ends the run.
- **R_safe = the base `2D_bench`** (installed solver, 2026-10-13: `b525086`, keyword-off paths bit-identical since): meniscus
  0.11 / 0.21 / 0.41 / 0.61 / 0.79 mm at 0.25 / 0.5 / 1 / 1.5 / 2 ms (base 0.43 at 1 ms, otherwise identical), wall front 1.150 mm
  at 2 ms (identical), wall water 372 against 369 cell volumes (+0.8 %), max |U| 1.18 m/s, budget 4.8e-15. Prediction 2 (meniscus
  below the base) fails: with G the wall/gap exchange is a Darcy flux, K_f × the yarn pc (the gap's 450 Pa meniscus suction is
  small next to it at either pc0), so K ÷ 10 with pc0 × 10 leaves it unchanged; the slit is set by K·pc0, as the walls alone.
- **Answer:** the original solver cannot run the slit: at both points tested (τ_I / τ_D 5 and 0.5) it fails in the first steps
  at the porous/free faces, before any transverse mode could grow. That it fails at any K²·pc0 is an argument, not a sweep: the
  bad face permeability of the Solidf bug comes from K_VOID (1 m², half-weighted: ~0.5 m²), not from the yarn K, so lowering K
  does not touch it, and lowering pc0 only scales the bad flux down. The cause (E) is attributed by the failure pattern: Solidf on
  those faces was not checked. The question "is B needed in the walls of a slit" can only be asked of a build that has at least E
  and G (with E alone the walls drain: strip bench, A + B + C + E, 2026-10-12; a different bench).

## Review of the controls (user's reviewer, 2026-11-18)

1. *Same fixed Δt as the failing runs (1e-7 s), no adaptive Δt:* the bench runs all use a fixed Δt (`adjustTimeStep no`). FP10,
   FP100, FK10, FK100 and HP10_K10 run at 1e-7 s exactly and are calm; HP10_K10 (Δt 1e-7 s) and SP10 (Δt 1e-6 s) give the same
   curve to 2 digits, so the larger Δt of the S runs is not what calms them. Only the slit runs use the adaptive Coats Δt; there
   K·pc0 is unchanged, so the Coats Δt is the base one, and the old-solver failure comes at step 1.
2. *Run long enough, compare per step and over a stretched time:* same metrics as `benchDdtCorr.py` (same parser). The S runs cover
   the base's whole wicking time (t* = t·K·pc0 up to the base's 2e-4 s, 2,000 steps, A0's mode at step 94, t* 9.4e-6 s); FP10 and
   FK10 reach t* = 2e-5 s at Δt 1e-7 s (twice A0's onset). **Gap:** FP100 and FK100 at Δt 1e-7 s reach only t* = 2e-6 s, before A0's
   onset: at fixed Δt 1e-7 s the ÷ 100 runs are not covered over the stretched time (that needs 200,000 steps, ~1.5–2 h each).
   **Not run (user, 2026-11-18): no thesis claim needs them; the claim that would (A alone suffices below some K²·pc0) is not
   made.**
3. *Separate K from pc0:* done (FP100: pc0 ÷ 100, K unchanged; FK100: K ÷ 100, pc0 unchanged; also ÷ 10, both Δt series): both
   calm. Neither "only K" nor "only pc0": HP100_K10 (pc0 × 100, K ÷ 10) grows exactly as A0, HP10_K10 (pc0 × 10, K ÷ 10) is calm,
   so the control is K²·pc0. Da (stiffness of the porous cells, K/Δx²) itself does not matter (HP100_K10 has Da ÷ 10 and = A0).
   On the phiPc / face-operator mismatch: a pure mismatch acting in the Darcy limit would depend on Co alone, and the S runs at
   A0's Co are calm once Λ is lower; so if the mismatch is the forcing, the inertial lag of the momentum path is the amplifier
   (interpretation, not tested).

## Claims for the thesis (user, 2026-11-18, with the solver freeze)

The study ends here: the ÷ 100 runs at Δt 1e-7 s over the stretched time and an A–C + E (`c3a2e6e`) slit check are not run.
What the runs above support, worded as shown:
- **The original solver cannot run a porous/free case** (the slit at two points, the strip bench on 2026-10-12). Caveat: E is
  identified as the cause from the failure pattern, not checked directly; G's necessity comes from the strip bench (A + B + C + E).
- **B is needed at the base parameters and kept for robustness over the range.** On the all-porous bench the A-only transverse
  mode is controlled by K²·pc0 (τ_I / τ_D = ρK²pc0/(μ²ε²Δy²)), not by K alone, pc0 alone or the Darcy number: figure
  `bench_pcK_spread.png` (four panels). A clean result without a mechanism.
- **Not claimed:** that B is unnecessary below some K²·pc0 (threshold not located; the ÷ 100 runs not covered over the stretched
  time at Δt 1e-7 s).
