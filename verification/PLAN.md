# Verification plan (written 2026-10-13, nothing run yet)

Studies 1, 2a, 2b, 3 proposed by the independent review and agreed with the user, plus additions (EQ0m-dt). Status:
**prepared, not started.** Start the next session here; run one study at a time and stop after each for review.

## Rules (from the review, agreed)
- Do not modify the installed solver. Variants are built under a new name in a scratch area, **with the patch saved
  in the study folder** (`verification/<study>/solver/`).
- One fixed, recorded solver version per study (commit hash + patch); write it in the study's README and table.
- **Predictions before runs:** before launching a study, copy its prediction/decision table below into
  `../NOTES_solver.md` (Studies 1, 2a, 2b) or `../NOTES_cases.md` (Study 3), then add the results next to them.
- Numbers in tables; figures saved in the study folder under `verification/`; every result marked
  **pass / fail / inconclusive**. A crash is a result (record time, last max |U|, last dt).
- Stop after each study and show the results to the user.
- Logs through `runTools.sh` (this folder: `. ../../runTools.sh` from `verification/<study>/<run>/`), never in the workspace.

## Folder layout
`verification/` = all verification evidence (moved from `trialWicking/verification/` on 2026-10-13: paper tutorials
`BL_*`, `eq_BC`, `wicking1D`, `bench_ddtCorr`, `inlet_eps1e-8`, analysis scripts, `setupCases`, `README.md`).
New studies: `verification/study1_equilibrium/`, `study2a_ablation/`, `study2b_faces/`, `study3_sensitivity/`, each
with `README.md` (solver version, commands, results), `solver/` (patches), run folders, figures.

## Solver versions
- Installed: `hybridPorousInterFoam` = `of9-port` `b525086` (A–I). Repo `~/OpenFOAM/martin_sng-9/run/hybridPorousInterFoam`.
- **Strict original (EQ0):** build `be54696` (tag `of9-port-before-porous-fixes`) with its own libraries in scratch:
  `git worktree add <scratch>/hpif_be54696 be54696`; in `OpenFoamV8/libraries/*/Make/files` and
  `solvers/hybridPorousInterFoam/Make/{files,options}` rename `LIB`/`EXE` and `-l` flags with a suffix (e.g. `_orig`,
  as done for the H scratch build), `wmake libso` the 3 libraries (porousModels, porousInterfaceProperties,
  porousImmiscibleIncompressibleTwoPhaseMixture), then `wmake` the solver → `hybridPorousInterFoam_orig`.
  (The backup binary `hybridPorousInterFoam_be54696` links today's shared libraries: equivalent in principle, H is
  inactive without its keyword, but not strictly the original.)
- **A only (EQ4):** same recipe from commit `b0c0f67`.
- **Solver-only variants (EQ2, EQ3):** copy `OpenFoamV8/solvers/hybridPorousInterFoam` (at `b525086`) to scratch, apply
  the change, new `EXE` in `Make/files`, `../../libraries` include paths in `Make/options` made absolute, `wmake`.
  Libraries unchanged → shared ones are fine. Save `git diff`-style patch to `study1_equilibrium/solver/`.
  Check bit-identity of each variant with its switch in the default position before use.

## STUDY 1 — cause of the equilibrium oscillation (EQ0–EQ4 + EQ0m-dt)
**Why:** A+B+C (`b995db5`, `darcyFaceMaxDa 0.1`) gives a ±0.9 cell-to-cell oscillation in the gravity–capillarity
equilibrium (counter-current, zero net flux; `NOTES_solver.md`, Verification). Same flow type at yarn surfaces.
**Case:** `eq_BC` (paper 4.1.3, Brooks–Corey, built by `setupCases` from the committed tutorial
`gravity_Capillarity_BrooksCorey`): 1 m column, 1 × 1500 cells (`system/blockMeshDict`), lower half at S 0.5
(`setFieldsDict`), pc0 1000 Pa, exponent 0.5, kr n 2, `maxCo 0.01`, `maxAlphaCo 0.01`, `maxDeltaT 0.1`, endTime 30,000 s,
write 250 s. Existing references: `eq_BC/port` (be54696) and `eq_BC/ABC` (b995db5), 1500 cells, 30,000 s
(1.7 h / 2.2 h). **Coarse mesh 1 × 300** (blockMeshDict `(1 300 1)`): first confirm the oscillation reproduces with EQ0m;
if not, use 1 × 1500. End time: the oscillation reached roughness 0.29 at 250 s and 0.89 by 10,000 s → **5,000 s** for
all runs (same for all; EQ1 is slow, see below), writes every 250 s.
**Runs** (identical case, only solver/keywords change):

| Run | Solver | Keywords / change |
|---|---|---|
| EQ0 | strict original `be54696` | — |
| EQ0m | installed `b525086` | `darcyFaceMaxDa 0.1` (expected: oscillation) |
| **EQ0m-dt** (added) | installed `b525086` | as EQ0m + capillary time-step limit (Coats CFL 0.5, see below) |
| EQ1 | installed `b525086` | `darcyFaceMaxDa` removed (A + C, no B) |
| EQ2 | scratch: C switchable | `darcyFaceMaxDa 0.1`, C off (linear kr) |
| EQ3 | scratch: phase-potential upwinding | `darcyFaceMaxDa 0.1`, kr upwinded by the current phase potential |
| EQ4 (optional) | build of `b0c0f67` | A only |

- **EQ0m-dt rationale (hypothesis to test first):** a cell-to-cell sign alternation is the signature of an explicit
  diffusion term above its stability limit. The tutorial limits dt by Courant numbers only (dt reaches 0.1 s with B);
  nothing limits the explicit capillary diffusion. The original's wide stencil (cell gradients) cannot amplify an
  odd-even mode, A's compact stencil can. If EQ0m-dt is smooth, the cause is the time step. Also print the Coats CFL of
  EQ0m (expect > 1 where it oscillates).
  **Needs a Brooks–Corey version of `meshing_strat_trial/tools/coatsTimeStep`** (it hard-codes Van Genuchten pc). Library
  formulas (`libraries/porousModels/capillarityModels/BrooksAndCorey/pcBrooksAndCorey.H:108–113`): Se = (S − Sminpc)/(Smaxpc −
  Sminpc) clipped to [1e-4, 1 − 1e-4], pc = pc0·Se^(−α), dpc/dS = −α·pc0·Se^(−α−1)/(Smaxpc − Sminpc); coefficients in
  `BrooksAndCoreyCoeffs` (`n 2`, `pc0 1000`, `alpha 0.5`, `Sbminpc 0`, `Sbmaxpc 0.999`). kr Brooks–Corey with `n`.
  Keep `CoatsMaxCo 0.5`, `dSmax 0.01`; no capillary-wave limit (no free cells).
- **EQ1 cost:** without B the tutorial's spurious currents limited dt to ~4e-3 s (record 2026-10-07): 5,000 s ≈ 1.2M
  steps on 300 cells — affordable on the coarse mesh; if not, shorten EQ1 and compare at equal times only.
- **EQ2 code:** `solvers/hybridPorousInterFoam/updateVariables.H`, the two lines
  `kr1f = (1. - porousFace)*kr1f + porousFace*upwind<scalar>(mesh, phiWettingUp).interpolate(kr1);` (same for kr2):
  multiply the upwind part by a switch `krUpwind` (new keyword, default 1 = unchanged; 0 = keep linear `kr1f`).
  Read it in `createPorousMediaFields.H` next to the other keywords. Bit-identity check with 1.
- **EQ3 code:** same lines; replace `phiWettingUp`/`phiNonWettingUp` by the sign of the current phase potentials, i.e. the
  brackets of `phiWetting`/`phiNonWetting` in `alphaEqn.H` (lines ~86–110) evaluated with the current p, pc, α:
  water: `(-snGrad(p) + (1-α_f)*snGrad(pc) - pc_f*snGrad(α))*|Sf| + rho1*(g & Sf)`;
  air: `(-snGrad(p) - α_f*snGrad(pc) - pc_f*snGrad(α))*|Sf| + rho2*(g & Sf)`.
  Use `upwind<scalar>(mesh, potential).interpolate(kr)`. (Phase-potential upwinding; if it still flip-flops, the
  follow-up is hybrid upwinding: viscous part by the total flux, gravity/capillary part separately.)
- **Diagnostics** (coded function object, every step, written every N = 100 steps; no solver change):
  odd-even indicator max_i |α_i − (α_{i−1} + α_{i+1})/2| (1D column: cells ordered along y); time when it first exceeds
  1e-2; per face, the number of sign changes of `phiWettingUp` and `phiNonWettingUp` (registered fields, created in
  `createPorousMediaFields.H:21–22`; check `foundObject` at start), list of the faces that flip most; dt and Coats CFL.
  Profiles vs EQ0 **and vs the analytical static profile** (`analyseEquilibrium.py` reference) at equal times
  (250, 1000, 2500, 5000 s): EQ0 itself is not converged and is 0.034 off the analytical profile in the transition band.
- **Decision table (copy to NOTES_solver.md before running):**

  | Observation | Conclusion | Action |
  |---|---|---|
  | EQ0m-dt smooth | explicit time-step instability of the capillary term | add a capillary dt limit to the solver (or require the function object) |
  | oscillation only with C on, EQ3 smooth | lagged upwind direction | adopt EQ3's rule |
  | oscillation with C on even in EQ3 | upwinding itself in counter-current flow | kr linear (or hybrid upwinding) on such faces |
  | oscillation only with B | Mf with upwinded kr in the pressure equation | investigate B's mobility |
  | oscillation in EQ4 | A involved | revisit A |
- **Draft predictions (to confirm before running):** EQ0 smooth (roughness ≤ 0.07 as on 1500 cells); EQ0m oscillates on
  1 × 300 too (the mode is cell-scale); EQ0m Coats CFL ≫ 1 in the oscillating zone; **EQ0m-dt smooth** (main hypothesis);
  EQ1 smooth but slow (small dt from spurious currents keeps it stable); EQ2/EQ3 depend on whether dt or upwinding is the cause.
- **Pass:** odd-even indicator < 1e-3 and profile within 1e-2 of EQ0 at equal times.

## STUDY 2a — clean ablation of G, H, F′, I
**Case:** slit, gap 15 cells, walls 8 cells (as `meshing_strat_trial/slit_test/P_w15_t60_K1e-11`), 2 ms, θ 60°, two wall
types: K 1e-11 (yarn) and K 1e-20 (impermeable); for K 1e-20 also real walls (`--walls real --w 15`) and the analytical
slit rise (`slitReport.analytic(15*20e-6, theta)`). Generator `meshing_strat_trial/slit_test/makeSlit.py` (run from a frozen
copy, output folders under `verification/study2a_ablation/`: set `HERE`/case path accordingly). Base command:
`makeSlit.py <name> --walls porous --nw 8 --w 15 --K <K> --theta 60 --add porousContactAngleWallLike=1 --add porousFreeFluxForce=1 --add porousFreeNoSlip=1 --run`

| Config | Change from the base command | Note |
|---|---|---|
| all on | — | |
| G off | `--set porousFreeDarcyFaces=off` | **also disables F′ and I** (they act only on porous/free Darcy faces): only H remains |
| H off (a) | omit `porousContactAngleWallLike` | original `correctContactAngleDB` (makeSlit sets `activatePorousContactAngle 1`) |
| H off (b, optional) | (a) + `--set activatePorousContactAngle=0` | no porous contact angle at all (ill-defined physically) |
| F′ off | omit `porousFreeFluxForce` | |
| I off | omit `porousFreeNoSlip` | |
| θ 90° | `--theta 90` | double-counting test: K 1e-20 → no rise; K 1e-11 → gap rise only from wall imbibition |

12 runs (6 configs × 2 walls) + real walls + optional H off (b) ×2. ~3–5 min each at 20 µm; run in parallel.
**Outputs:** h(t) (gap-averaged α 0.5) and vs analytical (K 1e-20); wall front vs t (K 1e-11; `benchSlit.py` gives
surface/back/mean fronts and wall water); **cumulative water flux through the yarn/gap faces into the walls** (new
coded function object: sum of `alphaPhi0.wetting` over faces whose two cells have different `Solid`, signed into the
porous cell, integrated in time); spurious currents = max |U| in cells with 0.05 < α < 0.95 vs the meniscus speed dh/dt;
max |U| in gap and walls; water budget (`waterBudget.csv`). One summary table, rows = configurations.
**Draft predictions** (from the 8-cell development runs `B_`, `H_`, `HF_`, `I_`, `P_`): all on: K 1e-20 = real walls ±2 %
(P_w15: 1.01 vs 0.99 mm), ~0.8 m/s; F′ off: K 1e-20 spurious 14–49 m/s, droplets; I off: rise +12–18 % (HF_w15 1.11 mm);
H off (a): K 1e-20 25–68 m/s and film/droplets, K 1e-11 3–5 m/s; G off with K 1e-11: the yarn walls do not take water from
the gap properly / drain (strip-bench evidence), possibly unstable; θ 90° K 1e-20: column stays ~0.1 mm; θ 90° K 1e-11: walls
wick from the reservoir and the column, gap meniscus drops.

## STUDY 2b — face checks at the yarn surface
**Cases:** `meshing_strat_trial/2D_bench` (as is, 2 ms) and R2 (dry yarn, water-filled gap above; strip bench variant
`R2waterGap` of `meshing_strat_trial/2D_bench_strip/variants/makeVariant.sh`). **R2 must run with the current keywords and
contact angle:** `ADD=` appends keywords, but `activatePorousContactAngle 0;` and `theta0 90;` already exist in that
template → add a variant (e.g. `R2waterGapHFI`) that edits those two lines with sed (as `ca90` does) and adds the
H/F′/I keywords, instead of relying on duplicate entries.
**Diagnostics** (coded function object, every step): for each yarn/gap face, sign series of `phiWettingUp` and
`phiNonWettingUp`; sign-change counts; faces flipping on > 10 % of steps; number of faces with simultaneous water in /
air out (confirms the counter-current regime); odd-even indicator along the yarn row next to the gap and in the yarn
interior (2D: along x within each row).
**Pass:** flips only at physically explainable reversals; odd-even indicator < 1e-3.

## STUDY 3 — sensitivity (contact angle, then K and pc0)
**First on the bench** (`2D_bench` setup via `makeSlit.py --walls porous --nw 8 --w 8 --K 1e-11` + H/F′/I keywords, which is
bit-identical to `2D_bench`), then the REV if affordable (estimate first, tell the user).
- θ = 20, 40, 60, 80° (`--theta`). θ 20° is outside the validated 40–80° range (meniscus ~3 cells deep at 160 µm: resolved).
- Recommended addition, one at a time: K × 0.5 / × 2 (`--K 5e-12`, `--K 2e-11`; Da stays < 0.1) and pc0 × 0.5 / × 2.
  **`--set pc0=...` does not work** (makeSlit's `--set` only matches unindented keywords; `pc0` sits indented in
  `VanGenuchtenCoeffs` as `pc0 pc0 [1 -1 -2 0 0 0 0] 5000;`): add an option or edit the generated
  `constant/transportProperties` before running. The Coats dt scales as 1/(K·pc0): ×2 cases take ~2× longer.
  Note: for the yarn alone the front depends on K·pc0 only (similarity solution), so K × 2 and pc0 × 2 should match for
  yarn-only observables; differences come from the gap coupling, gravity and the Darcy number — report that.
- **Outputs (thesis observables):** total water uptake vs t (`waterBudget.csv` / `liquidBalance.csv`), wicking front
  height vs t (wall front, gap meniscus), fraction of water in gaps vs yarns (`liquidBalance` columns `porousLiquid_mL`,
  `freeLiquid_mL`), time to a given saturation. Relative change of each output per change in cos θ (and per factor in
  K, pc0); rank the parameters.
- **REV:** not runnable yet (no `run`/`job.slurm`, open decisions: top/bottom, outlet, gap water column, keywords, θ; see
  `NOTES_cases.md`, REV case status). Rough scaling from the bench (70× more cells, similar dt): ~3–4 h serial per
  simulated ms → hours to a day per run on mini01. Measure with a short test once the REV runs, report before launching.

## Order and estimated cost
1. Study 1: builds (orig, EQ2, EQ3, optional EQ4) ~15 min; BC Coats function object + diagnostics function object;
   runs on 1 × 300 to 5,000 s: minutes each except EQ1 (~1M steps). EQ0m-dt first.
2. Study 2a: two function objects (wall flux, spurious currents) + ~15 runs, < 1 h in parallel.
3. Study 2b: face-sign function object (shared with Study 1) + 2 runs + the R2 variant.
4. Study 3: 4 θ + 4 K/pc0 runs on the bench (~3–6 min each); REV only after its setup and a cost measurement.
