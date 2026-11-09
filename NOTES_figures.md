# Figures for the thesis

One entry per figure: what it shows, the data it needs, the script that makes it, its status (**exists**, **planned**:
data kept, script to write; **needs a run**). Started 2026-11-09. Companion files: `NOTES_cases.md` (cases, results),
`NOTES_solver.md` (solver changes, verification). Kept result copies live in `~/PDM_results/` (outside the repo).

## Planned

### F1. First contact of dry yarn with water: failure and fix (study 2f, horizontal REV)
Status: **planned** (data kept for A and C; B time-matched needs a short run). Source: `verification/study2f_horizontalAir/README.md`.
Message: a dry yarn cell touching free water gets the Van Genuchten dry-end capillary pressure (2.5 MPa at S 0.002) across one
face; the suction tears the bath surface beside the crests, air collects under them and a partly filled bath cell runs away (the
study 2c pump). A wet contact zone (the start of the vertical cases) removes it, with the unchanged solver. Argument for a measured
yarn pc curve with a bounded dry end.
- **A. Mechanism (R0, dry start):** vertical x–z slice through the crest of the runaway site (y = 2.055 mm, x ≈ 1.39 mm), zoomed on
  the bath and the bottom fabric layers (~0.4 × 0.25 mm); colour: water fraction in free cells, saturation in yarn cells (yarn
  outline); arrows: U in free cells. Three times: ~1 µs (bath cells beside the crest emptied by the crest's suction, air coming
  down from above the bath surface), ~5 µs (all 747 bath cells under crests mostly air, crests no longer taking water), ~29.5 µs
  (one partly filled bath cell under the crest, ~86 m/s and growing).
- **B. Fix (R3b, wet contact zone):** the same slice: bath intact under the crest, the wet ramp in the yarn above, water rising
  into the gaps. R3b's first write is at 50 µs: a time-matched panel (1 / 5 / 30 µs) needs a rerun of its first 30 µs with writes
  every 5 µs (~10 min on 4 laptop cores, `REV_pipeline/cases/horizontal` as it is now, `maxSteps` / `writeInterval` changed).
- **C. Time series, R0 against R3b:** bath cells under crests still water (747 → 0 within 5 µs; 747 throughout); air in the bath
  (R0 growing to the collapse, 373 → 1,710 cell volumes by 31 µs; R3b a transient sag, peak 2,358 at 150 µs, refilled by 350 µs);
  fastest free cell on a log scale (R0 exponential runaway to 9×10⁴ m/s; R3b ≤ 5 m/s).
- Data: `~/PDM_results/study2f_R0_dry` (15 writes, 0.01–30.8 µs, log with `dsLocator` lines every step), `~/PDM_results/
  study2f_R3b_ramp` (10 writes, 50–500 µs, same log content). Per-write numbers: `verification/study2f_horizontalAir/analyse.py`.
- Script: to write (slices from the cell centres `0/C` and the fields, per-step series from the logs).

### F2. Through-thickness uptake of the horizontal REV (R3b)
Status: **planned** (data kept). Uptake above the bath against time, split yarns / gaps (6.9 → 135.9 g/m² at 50–500 µs; at
0.5 ms yarns 55.7, gaps 80.2), with the yarn mean S and the share of the fabric's free cells full; optionally the per-layer state
at 0.5 ms (yarns S 0.91–0.93 in every layer, gaps full in layers 5–8, 65–88 % in 9–13, 8 % in 14, dry above the yarn crests). Data:
`~/PDM_results/study2f_R3b_ramp` (numbers in the study 2f README). Script: to write.

## Existing (in the repo)

### Why each solver change (one figure per change, from the original failing runs)
`verification/solver_failures/figures/`: `A_original_vs_A.png`, `B_Aonly_vs_ABC.png`, `C_1D_foot.png`, `E_solidf_step1.png`,
`F_mixed_cell_velocity.png`, `Fp_near_wall_velocity.png`, `G_yarn_drains.png`, `H_contact_angle.png`, `I_no_slip.png`; scripts
`plot_AB.py`, `plot_C.py`, `plot_E.py`, `plot_FG.py`, `plot_HFpI.py` in the same folder (its README gives each piece of
evidence and its limits). Status: **exists** (2026-10-14).

### Verification against analytical solutions and the paper
- `verification/buckleyLeverett_flow_BC.png`, `buckleyLeverett_gravity_BC.png`, `buckleyLeverett_gravity_BC_FFP.png`:
  Buckley–Leverett (paper 4.1.1, 4.1.2).
- `verification/gravityCapillarityEquilibrium_BC.png`, `gravityCapillarityEquilibrium_BC_evolution.png`: paper 4.1.3 (the
  oscillation of A+B+C, open issue).
- `verification/wicking1D.png`, `verification/wicking1D_pressures.png`: 1D capillary wicking against the similarity solution,
  and the air/water pressure split.
- `verification/oddEvenScan.png`: local-extremum scan of the 1D and single-yarn fields.
- `verification/bench_ddtCorr/bench_ddtCorr_spread.png`, `bench_inertia_psolver_spread.png`: is B needed (ddtCorr, inertia,
  pressure tolerance).
- `verification/slit_freeSurface/slit_verification.png`: slit rise against Bosanquet, porous walls against real walls.
Status: **exists**.

### Benches and slits (`meshing_strat_trial/`)
- `slit_test/figures/slit_angles.png`, `slit_permeability.png`, `slit_widths.png`.
- `2D_bench_strip/variants/figures/`: `bench_alpha_maps.png`, `bench_front_sqrt_t.png`, `bench_pressure_jump.png`,
  `bench_profiles.png`, `bench_referees.png`, `bench_water_budget.png`; `2D_bench_strip/debug_faceDump/solidfBug_bench_alpha.png`,
  `solidfBug_bench_p.png` (the Solidf bug, change E).
- `2D_bench_long/check.png`, `2D_bench_t120/check.png` (bench checks; `2D_bench/check.py` writes `check.png`).
Status: **exists**.

### 1D and single yarn (`trialWicking/`)
- `animation wicking/animation_wicking.*.png`: frames of a wicking animation.
- `wickingFront.ipynb`: front against √t, profiles, p_air / p_water (figures inside the notebook).
Status: **exists**.
