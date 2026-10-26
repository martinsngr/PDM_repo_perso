# Failures that motivated each solver change (A, B, C, E, F, G, H, F′, I)

One figure per change, made only from runs done during the development (2026-10-07 to 2026-10-13). No new runs.
The runs are **copies** (originals left in place, since other scripts and notes point to them). Change
descriptions and the reasoning behind them: `../../NOTES_solver.md`; code: `git show <commit>` in the solver repo.

```
../../.venv/bin/python plot_AB.py      # A, B
../../.venv/bin/python plot_C.py       # C
../../.venv/bin/python plot_E.py       # E
../../.venv/bin/python plot_FG.py      # F, G
../../.venv/bin/python plot_HFpI.py    # H, F', I
```
Each script prints the numbers it plots. `foamio.py` holds the readers (fields, polyMesh, logs, csv).

**What the scripts do to the data:** they plot cell values as written, solver-log values per step, and the
`liquidBalance.csv` / `waterBudget.csv` columns written by the function objects during the runs. There is no
smoothing, filtering, fitting or rescaling. The derived quantities are:
- the transverse spread, printed by a function object during the run;
- for F, `reconstruct(φ)` (OpenFOAM's `fvc::reconstruct` formula, recomputed from the written φ);
- for the slit, the meniscus height (gap-averaged α = 0.5, linear interpolation between two cells, as
  `slit_test/slitReport.py`), the stray-water count (as `2D_bench/check.py`) and max |U|;
- for G(b), the yarn water as % change from t = 0;
- the Bosanquet slit rise, computed from the inputs.

## Figures

| Change | Figure | Case (copy in `cases/`) | Compared runs (binary) | What it shows |
|---|---|---|---|---|
| A | `A_original_vs_A.png` | `bench5x172/` (1D column widened to 5 × 172 × 3 cells, symmetry sides, fixed dt 1e-7); `wicking1D/` (1D column, 172 × 20 µm) | (a) original `be54696` vs original + A; (b) original vs A+B+C `b995db5` vs impesFoam | (a) original diverges at step 351 (3.5e-5 s, spread 1e55); with A it runs to 0.2 ms. (b) original 1D profile at 1 ms has cell-pair steps (5 cells where α increases upward below 0.8 mm; 0 for A+B+C and impesFoam) |
| B | `B_Aonly_vs_ABC.png` | `bench5x172/` | A only; A + ddtCorr × 0 / × 0.1; A + tight p tolerance (GAMG, PCG 1e-12); A+B+C `b995db5` | with A alone the transverse spread grows from ~1e-5 to 0.14–0.20 within 0.02 ms in every variant; with A+B+C it stays ≤ 1.3e-7 |
| C | `C_1D_foot.png` | `wicking1D/` | original `be54696` (linear kr) vs A+B+C `b995db5` vs impesFoam (upwind kr) | original: a foot of S 0.003–0.07 ahead of the front (highest cell with S > 0.01 at 3.24 mm at 20 ms vs 2.76 mm A+B+C and 2.78 mm impesFoam; S > 0.1 front at 2.55 / 2.53 / 2.57 mm) |
| E | `E_solidf_step1.png` | `strip/` (porous slab between free layers, 50 × 1 × 15 cells, reservoir at x = 0) | pre-E debug build of `b995db5` (face dump, step 1) vs E `c3a2e6e` (`base_steps`, step 1) | pre-E: Solidf = 0.5 on yarn/gap faces (1 inside the yarn), relative flux 1.6e4 vs 1e-26–1e-9 on yarn faces; the edge cells go 0.94 / 0.84 / 0.15 → 0.002 in one step, the gap cells above take 0.47 / 0.42 / 0.08. With E: edge cells unchanged (0.94 / 0.84 / 0.15), gap 0.002 |
| F | `F_mixed_cell_velocity.png` | `strip/` | E `c3a2e6e` (`base_steps`, `base_run`) vs E + F (`base_run_F`: F/G build, G off) | (a) E: max \|U − reconstruct(φ)\| in the yarn edge cells 2.3 → 72 m/s over 10 steps (interior yarn ≤ 5e-5); (b) E: dt collapses at 1.8e-5 s (464 steps), E + F reaches 0.2 ms (1135 steps); (c) E + F: mismatch bounded at 41–51 m/s, not zero |
| G | `G_yarn_drains.png` | `strip/` | E + F (`base_run_F`, G off) vs E + F + G (`base_run_G`) vs no-gap slab (`fullSlabClosed_run`, E); referee R3 (all patches closed) with E vs E + F + G, plus no-gap slabs | (a) yarn mean saturation 0.101 → 0.017 at 0.2 ms with gaps and no G (no-gap reference 0.101 → 0.197; with G 0.312); (b) R3: the yarn loses 42 % of its water to the gaps with E, −0.04 % with G; no-gap slabs 0 % |
| H | `H_contact_angle.png` | `slit/` (thick-wall slit: porous walls 8 cells, gap 8, 20 µm, θ 60°, 2 ms) | original porous contact angle (`1b007d8`, `B_*`) vs H (scratch build, `H_*`), wall K 1e-11 and 1e-20 | K 1e-11: water films along the walls ahead of the meniscus (up to 54 gap cells with α > 0.05), max \|U\| 5.1 m/s → none, 1.8 m/s with H. K 1e-20: H alone does not help (95 cells, 67 m/s) |
| F′ | `Fp_near_wall_velocity.png` | `slit/` | H (`H_nw8_w8_K1e-20`) vs H + F′ (`HF_nw8_w8_K1e-20`), K 1e-20 walls | H: wall-normal velocity in the gap cells next to the walls 0.56 m/s vs tangential 0.38 at 0.05 ms, up to 4.2 m/s later; droplets; gap max \|U\| 67 m/s. H + F′: wall-normal ≤ 5e-3 m/s, no stray water, ≤ 1.15 m/s |
| I | `I_no_slip.png` | `slit/` | H + F′ (`HF_*`) vs H + F′ + I (`P_w8_t60_K1e-20`) vs real walls (`S0_w8_t60`) and Bosanquet | H + F′: meniscus 1.474 mm at 2 ms vs real walls 1.245 (+18 %), wall-cell velocity / gap mean 0.80 vs 0.43. With I: 1.252 mm, 0.46 |

## Run inventory (source of each copy, binary from the log)

| Copy | Source | Binary | Run date |
|---|---|---|---|
| `bench5x172/log.i_original` | `verification/bench_ddtCorr/` | `hybridPorousInterFoam_be54696` | 2026-10-07 |
| `bench5x172/log.ii_A_c1`, `iii_A_c0`, `iv_A_c0.1`, `T2a_GAMGtight`, `T2b_PCGtight` | same | scratch `hybridPorousInterFoam_A_ddtCoeff` = `b0c0f67` (A) + `variant_A_ddtCorrCoeff.patch` (ddtCorr × coefficient; × 1 = A as committed) | 2026-10-07 |
| `bench5x172/log.v_modified` | same | `hybridPorousInterFoam` = `b995db5` (installed then) | 2026-10-07 |
| `bench5x172/case/` | same | the bench case (transverseSpread function object in `system/controlDict`) | |
| `wicking1D/{port,ABC,impes}` | `verification/wicking1D/` | `be54696` / `b995db5` / impesFoam | 2026-10-07 |
| `strip/debug_faceDump_preE/` | `meshing_strat_trial/2D_bench_strip/debug_faceDump/` | debug build of `b995db5` (prints only) | 2026-10-12 |
| `strip/base_steps`, `base_run`, `fullSlabClosed_run`, `R3closedRamp_run`, `R3closedRampSlab_run` | `meshing_strat_trial/2D_bench_strip/variants/old_variants/` | `hybridPorousInterFoam` = E `c3a2e6e` (installed 11:02, runs 11:21–12:27 on 2026-10-12; F/G committed 14:22) | 2026-10-12 |
| `strip/base_run_F` | same | scratch `hybridPorousInterFoamFG` (E + F + G), `porousFreeDarcyFaces` absent = E + F | 2026-10-12 |
| `strip/base_run_G`, `R3closedRamp_run_G`, `R3closedRampSlab_run_G` | same | scratch `hybridPorousInterFoamFG`, `porousFreeDarcyFaces on` = E + F + G | 2026-10-12 |
| `slit/B_nw8_w8_K1e-11`, `B_nw8_w8_K1e-20` | `meshing_strat_trial/slit_test/` | `hybridPorousInterFoam` = `1b007d8` (A–G) | 2026-10-13 |
| `slit/H_*`, `HF_*`, `P_*` | same | scratch `hybridPorousInterFoamH` with `porousContactAngleWallLike 1` / + `porousFreeFluxForce 1` / + `porousFreeNoSlip 1` (P = committed `b525086`, checked bit-identical by the `V_*` runs) | 2026-10-13 |
| `slit/S0_w8_t60` | same | installed `hybridPorousInterFoam` of that day; real walls, no porous cells, so A–G do not act | 2026-10-12 |

`dynamicCode/` was not copied (compiled coded BCs, regenerated on a rerun). `cases/` is git-ignored (results).

## Limits of this evidence (read before quoting it)

- **A, 1D panel and C are not isolated:** no 1D run exists with A alone or A + B without C. The 1D comparison is the
  original against A+B+C. Attributing the cell-pair steps to A and the foot to C rests on the mechanisms in
  `NOTES_solver.md`, not on these runs. The scratch bench that showed C alone (leading edge 0.134/0.076 →
  0.184/0.130 mm, 2026-10-01) no longer exists.
- **B:** the reference run (v) also has C; C changes kr only, and the four "A + …" variants show the mode is not a
  ddtCorr or solver-tolerance effect. Whether A + B without C also suppresses it was not run.
- **E:** the pre-E side comes only from the step-1 face dump (the pre-E bench run folders were deleted on 2026-10-12).
  The debug build adds print statements to `b995db5`, no numerical change. `base_steps` is identified as E by its run
  time and by its step 1 (the edge cells stay wet, unlike pre-E).
- **F:** F stops the growth and the collapse but does not make the mixed-cell U equal to `reconstruct(φ)`
  (41–51 m/s mismatch remains in (c), free cells 4–12 m/s). The single-yarn evidence quoted in `NOTES_solver.md`
  (written U 2.3e4 → 18.9 m/s) came from scratch copies that no longer exist.
- **G:** `base_run_G` starts with the gaps at α 0.002 (before the "free cells pure air" rule), and reservoir water
  climbs the gaps and feeds the yarn sideways. Its higher saturation than the no-gap reference is that effect, not a
  validation. The mechanism (yarn air pressure α·pc above the gap air, 4.1–5.1 kPa) was measured on
  `old_variants/airZero0_run_adc`, which is not plotted here.
- **H, F′:** the scratch build `hybridPorousInterFoamH` (obsolete, still installed) is not the committed code byte for
  byte; only its H + F′ + I configuration was checked bit-identical to `b525086`.
- **I:** the committed I is the bounded version (never below the old coupling). The unbounded version that produced
  10–60 m/s air currents along wet walls is not shown.
- All runs: 20 µm cells, one mesh. These are failure demonstrations, not validations of the modified solver.
