# REV_pipeline: fabric REV, from the TexGen geometry to a run

Self-contained folder for the fabric REV runs from 2026-11-09 on: the geometry, every script and function object the
cases use, and the cases themselves. Target (user, 2026-11-09): **one main script** where the REV inputs are given,
which builds the STL, makes a case folder from a reference one, builds the mesh and the fields, writes the simulation
set-up and launches the run. That script is not written yet (plan at the end); the three cases below are the first
set, built by hand with the tools it will call.

Background, decisions and results: `../NOTES_cases.md` (REV case status, Next steps), `../NOTES_solver.md` (solver,
change T for the tensor K). Rules as everywhere in the repo: predictions before runs, logs never in the workspace
(`tools/runTools.sh`), `sbatch job.slurm` only on the cluster.

## Layout

| Path | What it is |
|---|---|
| `geometry/funge.py` | TexGen script that writes the STL (`Textiles/<weave>-<D1>-<D2>-<v>-<rf>.stl`); needs TexGen's Python (`TexGen.Core`), today only inside the TexGen GUI on Windows |
| `geometry/Textiles/PW-22-15-0.4-0.5.stl` | the plain weave of all REV runs so far (cm; scale 0.01) |
| `geometry/Textiles/TW-22-15-0.4-0.5.stl` | twill 1/3, same yarns and densities (`twillA`); regenerated 2026-11-10 with the fixed twill block of `funge.py` (the first version was not periodic: Weave test below) |
| `geometry/inspect_stl.py` | REV box of an STL → `rev_domain.json` (in metres) |
| `geometry/rev_domain.json` | REV box of `inspect_stl.py`: x 0–1.818, y 0–2.667, z −0.0705–0.2115 mm (exactly periodic in x and y) |
| `geometry/rev_domain_midbath.json` | the same box moved by half a crossing-yarn spacing along y (y 0.333–3.0 mm): bath plane mid-gap, job 3068 |
| `geometry/rev_domain_TW.json`, `rev_domain_TW_midbath.json` | the same two boxes for the twill STL (z −0.080–0.227 mm) |
| `geometry/check_periodicity.py` | checks that the x and y planes of a built REV are periodic (first = last cell layer: valid only for a weave mirror-symmetric about the box planes, as the plain weave) |
| `geometry/stl_periodicity.py` | checks that an STL is periodic over its REV box, any weave: STL vertices near the box planes moved by one period, distance to the surface, per yarn (2026-11-10) |
| `tools/build_fields.py` | mesh (`system/blockMeshDict`) + eps, K, fYarn, yarnID from the STL and a REV box |
| `tools/initFields.py` | initial `alpha.wetting` (bath water, dry yarns, ramps) and its boundary field |
| `tools/runTools.sh` | `runTmpLog`: solver log outside the workspace, `LOG_EVERY` filtering |
| `tools/coatsTimeStep`, `liquidBalance`, `stopGuard`, `waterBudget` | function objects included by every `system/controlDict` |
| `tools/check.py` | per-write checks of a REV run along y (fronts, gaps, |U|, budget) |
| `tools/compare3068.py` (+ `analyseCut.py`) | a run against job 3068 on the cells above the bath plane |
| `tools/conductance.py` | saturated Darcy conductance of the yarn network of a built case (periodic, harmonic face K), K variants from the yarn axes: effective K and w_sat in seconds |
| `tools/compareAniso.py` | `anisoA` / `anisoA_mu100` against `tensorA`, cell by cell (the aniso mesh keeps `tensorA`'s yarn cells in order): front, yarn water, crossing-yarn S, row profiles, log statistics |
| `tools/compareTensor.py` | `tensorA` and `tensorB` against job 3068 (same mesh): per-write table with each crossing yarn's S, fits, the B2 time scaling, log statistics (dt limit, implied |U|, cost) |
| `tools/zLayers.py` | water per z layer of the free cells (through-thickness runs) |
| `tools/toAnisoImpes.py` | after `subsetMesh`: a tensor-K hybrid case → an anisoImpesFoam case of its yarns (`cases/anisoA`) |
| `cases/<case>` | one OpenFOAM case per run: `0.orig`, `constant`, `system`, `caseSetup` (N cores), `Allpre`, `run`, `clean`, `job.slurm`, `job_restart.slurm` |

Where the tools come from (copied 2026-11-09; the originals stay where they were, for the older cases):
- `build_fields.py`: `meshing_strat_trial/REV/build_fields.py` (step 7 of change T: `--k-par`/`--k-perp`) with two
  additions: `--stl`/`--domain` (the STL and the REV box given as paths; default as before, next to the script) and
  `--wick-axis z` (x and y both cyclic: `sideA`/`sideB`, `frontA`/`frontB`; `inlet` = bottom face, `top` = top face; with
  `--zpad N` the N layers below the box are the bath side, no `inletPad`). Checked: with job 3068's options it writes
  job 3068's `blockMeshDict`, eps, K, fYarn and yarnID byte for byte.
- `initFields.py`, `runTools.sh` and the four function objects: `meshing_strat_trial/tools/`, unchanged (the
  `coatsTimeStep` with the tensor branch of change T, `7593c42`).
- `check.py`: `meshing_strat_trial/REV_midbath/check.py`; `compare3068.py`: `verification/study2e_bathLayer/`;
  `analyseCut.py`: `verification/study2c_nearSaturation/`; `zLayers.py`: `verification/study2d_gapRise/` (the last two
  import `analyseCut.py` from this folder now). Geometry files: `meshing_strat_trial/REV/` and `REV_midbath/`.

Paths inside a case: tools `../../tools`, geometry `../../geometry`, the repo `.venv` `../../../.venv`, function objects
`../../../tools/<name>` (from `system/`). `Allpre`, `system/blockMeshDict`, `0/`, logs and csv files are rebuilt or
written per run (`.gitignore`).

## Cases (set up 2026-11-09, decided with the user the same day)

All on the solver of9-port `4bb5d2e` (change T), REV values unless stated: Brooks–Corey n 3, Van Genuchten pc0 5000 Pa,
m 0.5, ε 0.5, water/air, σ 0.072, G + H + F′ + I, J (`waterOnlyPatches`), L (`porousFreeAirKrPorous on`), 20 µm cells.

| Case | Set-up | One change against | Cores, end, writes |
|---|---|---|---|
| `tensorA` | vertical wicking along y, bath plane mid-gap (job 3068's mesh, BCs and initial state) | job 3068: K diagonal in the yarn axes, Kpar 1e-11, Kperp 2.2e-12 (Gebart ratio 4.55): **anisotropy alone**, study (a) | 8 (job 3068's decomposition), 30 ms, every 0.5 ms |
| `tensorB` | the same | job 3068: K from Gebart (hex, Vf 0.5, fibre radius 7.5 µm): Kpar 4.245e-12, Kperp 9.20e-13, study (b) | 8, 60 ms, every 1 ms |
| `twillA` | as `tensorA`, on the twill 1/3 STL (box `rev_domain_TW_midbath.json`, its own mesh and decomposition) | `tensorA`: **the weave alone** (set up 2026-11-10, Weave test below) | 8, 20 ms, every 0.5 ms |
| `horizontal` | the previous student's set-up with our model: the fabric lying flat on a bath at rest, water rising through the thickness (z); x and y cyclic; 5 water rows (0.1 mm) under the fabric box fed from the bottom face (J, totalPressure 0.988 Pa = ρg·5Δz: water at 0 Pa at the bath surface), 5 air rows above it, top open; gravity −z; θ 40° (her value); gaps air, yarns 0.002 except a **wet contact zone** (yarn cells of the bottom four fabric layers on a ramp S 0.84 / 0.64 / 0.35 / 0.15, +6.3 % of the yarn capacity, adopted 2026-11-09 after study 2f) | new (her case: interFoam, impermeable body-fitted yarns, θ 40°, symmetry sides, g 0, inflow fixed at 1e-4 m/s; ours: bath at rest) | 16, 5 ms, every 0.1 ms |

The horizontal case is the REV box of `inspect_stl.py` (91 × 133 × 14 cells, its cells identical to job 3051's box)
with 5 + 5 free layers: 290,472 cells, 78,528 porous; `inlet` and `top` 12,103 faces each, all free (the bath touches
the yarn crests: 747 of the 12,103 faces of the first box layer are porous). The bath surface has no edge (x, y cyclic):
none of the outer-bath problems of study 2e.

**Runs:** `tensorA` job 3107 and `tensorB` job 3108 on mini03 (8 cores each, submitted 2026-11-09); `anisoA` job 3109 and
`anisoA_mu100` job 3110 (4 cores each, submitted the same day, ~30 min later); `horizontal` ready since 2026-11-09 (wet contact
zone, hold lifted), not submitted. `twillA` ready since 2026-11-10 (8 cores, 20 ms), not submitted.

### Laptop checks (2026-11-09, scratch copies, installed `4bb5d2e`)
- `tensorA`, `tensorB`: `Allpre` from this folder; mesh (`blockMeshDict`, points, faces, owner, neighbour, boundary)
  and `0/` eps, fYarn, yarnID, alpha.wetting, U, p, Uwetting, UnonWetting byte-identical to job 3068's; dictionaries =
  job 3068's except the comments, `endTime`, `writeInterval`. K: volTensorField, no off-diagonal term, free cells 1·I,
  yarns 0–4 (43,410 cells) diag(Kperp, Kpar, Kperp), yarns 5–9 (35,079) diag(Kpar, Kperp, Kperp). Smoke tests (30
  steps, 4 cores): the solver reads the tensor (`Tensor K: normal component on the faces, harmonic where it differs`),
  guard passed (all 39,115 porous/free faces Darcy faces), J and L active; dt at the Coats limit 2.74e-7 s (a) and
  6.41e-7 s (b) (job 3068 1.25e-7: ×2.2, ×5.1); α in [−5e-19, 1.0013]; imbalance ≤ 1.1e-24 m³; 1.33–1.38 s per step
  on 4 cores (the scalar REV: 1.35).
- `horizontal`: checkMesh OK (cyclics matched); box cells (eps, yarnID, fYarn, K) identical to job 3051's box; bath rows
  water, fabric dry, top air. Smoke test: see the predictions below (start phase).
- All three rebuilt from this folder after the move: byte-identical to the checked builds.

### Predictions (written before the runs, 2026-11-09)
Reference job 3068 (scalar K 1e-11, same mesh as the tensor cases): y-yarn front 0.985 / 1.185 / 1.526 / 1.947 / 2.288
/ 2.549 mm at 1 / 2 / 5 / 10 / 15 / 20 ms, fit 2–20 ms 14.44 mm/√s (2–10 ms 14.35, c 0.52 mm), closed end (2.99 mm) at 28
ms; crossing yarn 6 mean S 0.92 at 5 ms, yarn 7 0.21 / 0.58 at 5 / 10 ms; gap water 179 cell volumes at 1 ms, 81–98
after 2 ms; α ≤ 1.0017; free |U| ≤ 1.1 m/s from 2 ms; dt 1.25e-7 s; 3,440 s per simulated ms on 8 cores.

`tensorA` (anisotropy alone; the bath faces are all on the y-yarns, K_yy = Kpar: the bath feed per face unchanged):
- A1 stability: no stopGuard to 30 ms; α ≤ 1.02; free |U| ≤ 3 m/s at the writes from 2 ms; |imbalance| ≤ 1e-16 m³.
- A2 front: fit 2–20 ms between 14.8 and 16.6 mm/√s (+3 to +15 % over job 3068): the crossing yarns draw less (the
  y-yarn/crossing-yarn contact faces carry ×0.22 (z faces, Kperp on both sides) to ×0.36 (x and y faces, harmonic of
  Kpar and Kperp)), so the REV/1D ratio (0.80) moves towards 1. **Fails if below 14.0 mm/√s**: then the slower spreading
  across the y-yarns (Kperp in x and z) costs more than the weaker sink gains, and the sink hypothesis for 0.80 is wrong.
- A3 crossing yarns wet later: yarn 6 mean S at 5 ms ≤ 0.85 (job 3068 0.92), yarn 7 at 10 ms ≤ 0.50 (0.58).
- A4 gaps drained by 2 ms as in job 3068 (the drain runs through yarn faces at Kperp: gap water at 1 ms between 179 and
  1,500 cell volumes).
- A5 dt 2.5–3e-7 s at the Coats limit; 30 ms in 12–16 h on 8 cores.

`tensorB` (Gebart; K ×0.4245 along the yarn, ×0.418 across: nearly a uniform scaling of `tensorA`'s K):
- B1 stability as A1, to 60 ms.
- B2 **time scaling**: at fixed pc0 the porous part of `tensorB` at time t is `tensorA` at 0.4245·t (Darcy and gravity
  fluxes both ∝ K; the gaps, which do not scale, have drained by then): y-yarn front of (b) at t within 0.04 mm (2 rows)
  of (a) at 0.4245·t, for t ≤ 60 ms (against (a) to 25 ms); fit k_b = 0.652·k_a ± 3 %. A larger difference = the free
  cells or the coupling, which do not scale with K, matter.
- B3 front fit 2–40 ms 9.1–10.8 mm/√s (0.652 × 13.9–16.6); the closed end not reached by 60 ms (front ~2.8 mm).
- B4 dt 5.5–7e-7 s (Coats, then dSmax 1.3e-6 and the capillary waves 1.5e-6 close); 60 ms in 10–14 h on 8 cores.

### Results: `tensorA` (job 3107) and `tensorB` (job 3108), analysed 2026-11-10
Copies `~/PDM_results/REV_pipeline_tensorA`, `REV_pipeline_tensorB` (fetched 2026-11-10, includes repointed);
`tools/compareTensor.py <A> <B>` (per-write table, per-crossing-yarn S, B2, log statistics) and `tools/compare3068.py`.
Both on mini03, 8 cores, started 2026-11-09 10:40 next to `anisoA`, `anisoA_mu100` and another user's 20-core job (44 of 46 CPUs).
- **`tensorA`, 30 ms, no stopGuard, 70,580 s (19.6 h).** dt median 2.4–2.8e-7 s, at the Coats limit on every sampled step
  after 0.5 ms; α ≤ 1.0014 (sampled log), free |U| ≤ 1.3 m/s at the writes from 2 ms (3.0 / 2.9 m/s at 0.5 / 1 ms; job
  3068: 15 / 7), imbalance −1.9e-18 m³ once in the first 0.5 ms, constant after. **y-yarn front behind job 3068 from 2 ms**
  (+0.02 mm at 0.5–1 ms, −0.04 / −0.10 / −0.14 / −0.22 mm at 2 / 10 / 20 / 30 ms; 2.769 mm at 30 ms, closed end not reached);
  fit 13.47 / 12.97 / 12.81 mm/√s over 2–10 / 2–20 / 2–25 ms (job 3068 14.36 / 14.44 / 14.15), REV/1D 0.72 (0.80). Porous
  water 0.90 × job 3068 from 2 ms; split: y-yarns 0.90–0.94 ×, crossing yarns 0.87–0.89 × (5–30 ms). Crossing yarn 6 mean
  S 0.890 at 5 ms (0.920), yarn 7 0.092 / 0.450 at 5 / 10 ms (0.215 / 0.584). Gap water 296 at 1 ms (179), then 115–214
  cell volumes, slowly rising (job 3068 81–98); first fabric row 19 of 944 free cells water (17): the J cut-off as before.
  Lost through top/bottom 7.4 cell volumes by 30 ms (11).
- **`tensorB`, 60 ms, no stopGuard, 62,796 s (17.4 h).** dt median 5.4–6.5e-7 s at the Coats limit (not dSmax nor the
  capillary waves); free |U| ≤ 1.25 m/s at the writes from 2 ms; imbalance −8.6e-19 m³ once. α above 1.001 in three
  episodes (sampled log: 12 of 91 steps at 0–5 ms, 70 of 184 at 30–40 ms, 79 of 153 at 50–60 ms; max 1.0067 / 1.013 /
  1.017), never in porous cells at the writes: free cells at the lower flank of crossing yarn 6 (x 0.33–0.61, y 0.52–0.58,
  z 0.02–0.06 mm; near the job 3067/3068 pump site, but |U| ≤ 1.3 m/s). Front 1.386 / 1.967 / 2.569 mm at 10 / 30 / 60 ms,
  fit 8.50 / 8.20 / 8.24 mm/√s over 2–20 / 2–40 / 2–60 ms. Gap water 158 cell volumes at 20–30 ms, **184 → 508 from 39 to
  60 ms**, all within 0.5 mm of the bath plane (y 0.34–0.83 mm, z 0–0.14 mm: the yarn band), 260 cells α > 0.5 at 60 ms;
  first row 18 of 944 throughout (no refill from the bath).
  **What that gap water is (2026-11-10, after the user saw water films on yarn surfaces near the bath; face fluxes
  `alphaPhi0.wetting` across the yarn/gap faces, 45 and 60 ms):** 1,640 free box cells α > 0.05 at 60 ms (`tensorA` at 30 ms
  698, job 3068 279), 1,317 touching a yarn, half at y 0.43–0.53 mm (below crossing yarn 6), none above 0.9 mm. Two kinds:
  (1) thin partial layers on the yarn surfaces, two thirds of the cells at α 0.05–0.2: the yarns absorb them (gap p −34 to +20
  Pa, yarn pc 810–935 Pa at S 0.982–0.986; on 672 / 915 faces at 45 / 60 ms); at 20 µm such a layer is smeared water in
  transit, not a resolved film (H also holds θ 60° on wet yarn surfaces); (2) water-filled pockets (164 cells α > 0.9 at 60 ms)
  at gap p −750 to −850 Pa that **draw water out of the yarns** where the yarn pc is lower (674–767 Pa at S 0.987–0.990, yarn
  air p ~95 Pa: not trapped air) on 83 / 203 faces: the S_eq condition (yarn pc below the meniscus suction; 800 Pa ≈ 2σcosθ/w
  for w ≈ 90 µm, a narrow corner). Net over all wet gap cells the yarns still take water (−23 / −22 cell volumes per ms); in
  the band below yarn 6 the yarns give (+14 / +31 per ms, gross out 67 / 159, back in 53 / 128). The 18 open free bath faces
  feed the gaps 30 cell volumes per ms (15 % of the bath inflow; porous faces 164–183). `tensorA` at the same porous state
  (25.5 and 30 ms) has no such outflow (0–1 face): the gap side has 2.4 × more physical time in (b) (bath feed through the
  free faces ~1,800 against ~1,300 cell volumes). Hypothesis, not tested: the narrow pockets near the bath fill first once
  the yarn rows beside them pass S_eq, as expected for gaps behind the front. The free-cell α overshoot episodes (1.013–1.017)
  sit in the same band (x 0.33–0.61, y 0.52–0.58 mm).
- **B2, the time scaling, holds:** front of (b) at t against (a) at 0.4245·t (interpolated) within 0.028 mm for every write
  1–60 ms; arrival times of the front, 0.4245·t_b / t_a = 0.996–1.005 from y 1.3 mm (0.91–1.10 below, rows at 20 µm against
  writes 0.5 ms apart); fits of (b) over (a)'s windows ÷ 0.4245: k_b / k_a = 0.6552 / 0.6478 / 0.6501 (√0.4245 = 0.6515,
  within 0.6 %), same offset c within 0.007 mm; porous water ratio 1.046 / 1.010 / 1.002 / 0.997 at 1 / 5 / 20 / 60 ms;
  crossing yarns 6 and 7 S within 0.003 from 10 ms. **The porous part is a pure time rescaling of (a)**: at fixed pc0 and
  anisotropy ratio the gaps and the porous/free coupling do not change the yarn wicking; the gaps do not scale (gap water
  of (b) 2.5 × (a)'s at the scaled time at 60 ms).
- **Scoring.** A1 pass. **A2 fails** (12.97 < 14.0 mm/√s, −10 % instead of +3 to +15 %). A3: yarn 6 at 5 ms 0.890 > 0.85
  fails, yarn 7 at 10 ms 0.450 ≤ 0.50 passes. A4 pass (296 at 1 ms; the gaps then keep ~2 × job 3068's water). A5: dt
  pass (2.37e-7 at 10–20 ms, 5 % below the range), cost fails (19.6 h; 0.61 s per step against 0.425 for job 3068; the
  laptop smoke tests showed no per-step difference, so likely the node load, not checked). B1 pass (α 1.017 ≤ 1.02, in
  free cells). **B2 passes.** B3 fails as written (8.20 below 9.1–10.8 mm/√s, a consequence of A2: 0.652 × 12.97 = 8.45);
  closed end not reached, passes. B4: dt pass, cost fails (17.4 h; 0.63 s per step, as `tensorA`).
- **Lucas–Washburn check (2026-11-10, `compareTensor.npz` of the three copies; scratch script):** the uptake (water above the
  bath plane, yarns + gaps, per fabric cross-section 1.82 × 0.28 mm²) grows as √t with a constant coefficient over 2–30 ms:
  per window (2–5 / 5–10 / 10–15 / 15–20 / 20–25 / 25–30 ms) job 3068 2.38 / 2.32 / 2.37 / 2.36 / 2.37 / 2.37 mm/√s, `tensorA`
  2.19 / 2.02 / 2.13 / 2.12 / 2.12 / 2.13, `tensorB` 1.30–1.49 over 2–60 ms (rising from 40 ms with the gap water). The front
  (highest y-yarn cell at S > 0.1, from the bath plane) follows h² = k²(t + t0) within one cell row (rms 23 / 36 / 30 µm):
  k 15.0 / 13.6 / 9.0 mm/√s, t0 1.5 / 2.4 / 4.3 ms (the initial wet rows); a power law without the time origin gives exponents
  0.40–0.43 only because of that offset. Per-window front coefficients scatter (job 3068 12.6–15.0, `tensorA` 8.4–14.2): the
  front is one cell on 20 µm rows and jumps at the crossing yarns (0.67 mm period), so the front coefficient needs windows of
  ≥ 10 ms; the uptake coefficient is the robust one. Gravity is negligible at these heights (ρgh ≈ 25 Pa against kPa).
- **Reading.** A2's failure line: the crossing-yarn sink does not explain REV/1D 0.80 on its own. The crossing yarns do
  take less water with Kperp across (A3 partly, 0.87–0.89 ×), but the y-yarns hold less too (0.90–0.94 ×) and their front
  is slower although K_yy along them is unchanged and every bath face is a y-yarn face at Kpar. Candidates, not tested:
  (1) in job 3068 the crossing yarns (45 % of the porous cells, isotropic 1e-11) also carry water along y between y-yarn
  segments; in `tensorA` their K_yy is Kperp; (2) the crimp staircase: a y-yarn steps in z through z-faces at Kperp. Cheap
  test without a solver run: the saturated single-phase Darcy conductance along y of the porous cells (scipy, 78,489
  cells) for scalar K, `tensorA`'s K, and two variants (crossing yarns K_yy = Kpar; y-yarns K_zz = Kpar). The weave factor
  (REV front ÷ 1D front along the yarn axis) depends on the anisotropy: 0.80 isotropic, 0.72 at Kpar/Kperp 4.55.

`horizontal` (written before the smoke test; **the case is on hold**, see "Horizontal: smoke test failed" below):
- H1 stability: no stopGuard to 5 ms; α ≤ 1.02; free |U| ≤ 3 m/s at the writes from 0.5 ms (study 2d S9, closed yarns,
  the same direction: early peaks 8 m/s); |imbalance| ≤ 1e-16 m³; water out through `top` ≤ 10 cell volumes.
- H2 yarns: mean porous S ≥ 0.9 by 2 ms and ≥ 0.97 by 5 ms (D ≈ K·pc0/(μ·ε) ≈ 1e-4 m²/s: 150 µm in ~0.2 ms; fed through
  the crests and the gap water).
- H3 gaps: at 5 ms the free box cells ≥ 50 % water in every z layer up to mid-thickness (z ≤ 0.07 mm), connected to the
  bath; the layers above the yarn crests (z ≥ 0.18 mm) < 20 % (S9 with closed yarns: ≥ 91 % up to z 0.14 mm by 0.7 ms,
  top at 0.18 mm). **Fails if the free box cells above the first box layer hold < 20 % water at 5 ms**: the yarn suction
  would then empty even gaps fed by the bath over their whole area.
- H4 uptake (water above the bath surface) at 5 ms 120–200 g/m² (yarns full: 65 g/m²; all free box cells full: +152).

### Cross-check: `anisoA`, `anisoA_mu100` (anisoImpesFoam, set up 2026-11-09; a cross-check only, decided with the user)

The yarns of `tensorA` alone (plan item 5, yarn-only REV against the hybrid), stock anisoImpesFoam of porousMultiphaseFoam
(laptop: `30adb89`). `Allpre` builds `tensorA`'s mesh and fields, keeps the yarn cells (`topoSet` eps ≤ 0.99, `subsetMesh`),
and `tools/toAnisoImpes.py` writes `0/Sb` (`tensorA`'s initial saturation), `constant/K` (its tensor), the BCs. 78,489 cells
(= `tensorA`'s yarn cells), patches: `inlet` 330 faces (the bath: Sb 0.99, air pressure p = pc(0.99) = 675.7 Pa so the water is
at 0 Pa as in `tensorA`, no air through it), `outlet` 329 faces (the yarn ends at y 3.0 mm: air at 0 Pa, no water out),
`sideA`/`sideB` cyclic, `yarnSurface` 39,115 faces (`tensorA`'s yarn/gap faces) as `symmetry` (zero flux without gravity).
Differences from `tensorA` by construction: no gaps (no gap water, no venting of the yarns' air into the gaps: the air
leaves through the yarn ends, the crossing yarns through their contacts), **no gravity** (anisoImpesFoam's gravity-aware wall
BC fails on OpenFOAM 9; ρgL ≈ 26 Pa against pc0 5000 Pa, ~1 %), the outlet open to air (closed in `tensorA`), Coats dt from
the full face tensor (Kpar on every face: dt 1.26e-7 s, half of `tensorA`'s). `anisoA_mu100`: `anisoA` with μ_air 1.76e-7
(÷100): how much the venting route matters. `decomposePar -constant` (K lives in `constant/`).
Laptop checks: checkMesh OK; smoke test 50 µs on 4 cores (403 steps, 0.25 s per step): Sb in [0.002, 0.99], water +124 cell
volumes, y-yarn front 0.271 → 0.311 mm above the bath. 30 ms ≈ 238,000 steps: ~16 h on the laptop, so mini03 (4 cores each).
`anisoA_mu100` smoke test (50 µs, 4 cores): 918 steps, dt 5.3–6.0e-8 s (the freer air raises the capillary part of the
Coats number: ÷2.2 against `anisoA`), 0.235 s per step, Sb in [0.002, 0.99]; water +133 cell volumes (`anisoA` +124), the
same front row. 30 ms ≈ 545,000 steps: ~36 h on the laptop, ~15 h on 4 mini03 cores (estimate; within the 72 h limit).
**Solver:** porousMultiphaseFoam fork, branch `of9-port`, **`c6e6578`** (2026-11-09, user). anisoImpesFoam had not compiled since
`65ea0f9` (2026-09-22): its `SEqn.H` is a symlink to impesFoam's, which gained the opt-in fixedSb clamp, declared only in
impesFoam's `createFields.H` (mini03 build failed on it). `c6e6578` declares the three clamp variables in anisoImpesFoam's
`createFields.H`, constant and inactive. Regression (laptop, 2026-11-09): the `anisoA` 50 µs smoke test with the rebuilt binary
= with the 2026-09-16 binary (the one of check 4, kept as `anisoImpesFoam_0916`): same 403 steps and deltaT sequence, `Sb`, `p`,
`Ua`, `Ub`, `phi` byte-identical at both writes. mini03 had no anisoImpesFoam: built there from `c6e6578`.

Predictions (before the runs; `tensorA` = job 3107):
- X1: both reach 30 ms, Sb in [0.002, 0.99] (impesFoam gives NaN above Sbmax: a NaN is a failure).
- X2 front: `anisoA`'s y-yarn front fit (2–20 ms, free offset) within −3 to +6 % of `tensorA`'s (impesFoam ahead by 1.8 % in
  the 1D twins and 2.5 % in check 4; no gravity, up to +1 %; the missing gap water costs 1–2 rows early, mostly in the offset).
- X3 water: `anisoA`'s yarn water below `tensorA`'s by 2,000–3,500 cell volumes at 1–2 ms (`tensorA`'s yarns also take part
  of the initial gap column, 4,715 cell volumes, which `anisoA` does not have), the ratio rising to 0.95–1.08 by 10–20 ms
  (impesFoam holds 4–9 % more water in the twins).
- X4 venting: `anisoA_mu100` within +0 to +3 % of `anisoA` in front, +0 to +5 % in yarn water (1D: the air back-pressure
  cost ~2.5 % of the uptake); more than 5 %: the yarns' trapped or slowly vented air matters once the gaps are gone.
- **Result `anisoA` (job 3109, analysed 2026-11-10; copy `~/PDM_results/REV_pipeline_anisoA`; `tools/compareAniso.py`):**
  30 ms, 45,648 s on 4 cores (12.7 h; `tensorA` 19.6 h on 8: ~3 × fewer core-hours, not 10 ×), dt 1.25e-7 s (half of
  `tensorA`'s, full-tensor Coats as expected), Sb in [0.002, 0.99], no NaN: **X1 passes.** Front behind `tensorA` at every write
  (−0.06 / −0.06 / −0.12 / −0.04 / −0.10 / −0.14 mm at 1 / 2 / 5 / 10 / 20 / 30 ms); fits 13.33 / 12.51 / 12.68 mm/√s over 2–10 /
  2–20 / 2–25 ms (−1.0 / −3.5 / −1.0 %): **X2 fails as written** (2–20 ms −3.5 % against −3 to +6 %; the other windows inside),
  and the sign is the opposite of the 1D twins (impesFoam ahead there). Yarn water below `tensorA` by 788 / 998 cell volumes at
  1 / 2 ms (predicted 2,000–3,500) and by 1,311 / 1,695 at 10 / 30 ms, ratio 0.84 → 0.91 / 0.92 / 0.93 at 1 → 10 / 20 / 30 ms
  (predicted 0.95–1.08 by 10–20 ms): **X3 fails.** Row-mean S lower than `tensorA` from the second 0.2 mm above the bath at every
  time (10 ms: 0.907 / 0.879 / 0.801 against 0.960 / 0.932 / 0.836 at y 0.54 / 0.74 / 0.94 mm; 30 ms: 0.942 against 0.981 at
  0.54 mm); crossing yarns 6 and 7 wet later (yarn 6 S 0.884 against 0.943 at 10 ms). Candidates, not tested: (1) the air of
  the yarns has no lateral exit in `anisoA` (only the yarn ends at y 3.0 mm and the crossing-yarn contacts; in `tensorA` it
  leaves into the gaps through 39,115 yarn/gap faces), so near-saturated rows near the bath keep air; `anisoA_mu100` (X4)
  tests it; (2) the hybrid's yarns also take water from the gaps (the initial column, and the bath water entering through
  the few open free bath faces: 47–52 cell volumes per ms against 349–378 through the yarn faces at 26–30 ms, ~12 %).
  X4 waits for `anisoA_mu100` (job 3110).
- **Result `anisoA_mu100` (job 3110, analysed 2026-11-10; copy `~/PDM_results/REV_pipeline_anisoA_mu100`):** 30 ms, Sb in
  [0.002, 0.99]; dt 5.4e-8 s (÷2.3 against `anisoA`, the freer air raises the Coats capillary term), 81,329 s on 4 cores (22.6 h,
  90 core-hours; `anisoA` 51, `tensorA` 157). Against `anisoA`: front fits −0.1 / +1.4 / +0.7 % (2–10 / 2–20 / 2–25 ms), yarn
  water +4.8 / +6.9 / +8.7 / +9.9 / +7.5 / +5.5 / +4.8 % at 0.5 / 1 / 2 / 5 / 10 / 20 / 30 ms: **X4 passes for the front, fails
  for the water** (above +5 % from 1 to 20 ms). Against `tensorA`: yarn water 0.88 / 0.93 / 0.97 / 0.976 / 0.975 / 0.974 at 0.5 /
  2 / 5 / 10 / 20 / 30 ms, front fits −1.1 / −2.3 / −0.3 % (X2 passes), row-mean S near the bath now as `tensorA` (10 ms, y 0.54 /
  0.74 / 0.94 mm: 0.968 / 0.939 / 0.834 against 0.960 / 0.932 / 0.836; `anisoA` 0.907 / 0.879 / 0.801). **Reading:** `anisoA`'s
  deficit near the bath is air that cannot leave the yarns sideways; with the air nearly free the yarn-only model gives
  `tensorA`'s yarn water within 2.5 % from 5 ms and its front within 2.3 %. The early deficit (0.88–0.93 to 2 ms) is the initial
  gap column that `tensorA`'s yarns absorb. So in the hybrid the gaps act for the yarns mainly as an air vent (they hold little
  water at the bath, J); a yarn-only model needs a vent, and freeing the air in anisoImpesFoam costs 2.3 × the steps (not
  cheaper than the hybrid per core-hour: 90 against 157 for the same 30 ms, the hybrid also carrying the gaps).
- Reading: X2 and X3 hold = the REV front is set by the yarn network, and anisoImpesFoam (yarn-only, ~10× cheaper) can
  carry the weave and density variants. X2 fails with X4 small = the hybrid's gaps or bath change the front: not a
  substitute. X4 large = a yarn-only model needs a vent (a Richards solver with a tensor K, or a venting boundary).

### Effective conductance of the yarn network (`tools/conductance.py`, 2026-11-10)
Question: is the weave factor w a geometric property of the yarn network, so that a linear solve on the REV mesh (seconds)
could give it for any weave, density or anisotropy instead of a REV run? Saturated single-phase Darcy flow through the
yarn cells only (gaps dry, as in the fabric-scale Richards model), two-point fluxes with the harmonic mean of the normal K
components (as the solver), periodic in x and y with a mean pressure drop per period along y; K_eff per cross-section of the
fabric box, w_sat = K_eff/(φ_y·Kpar). K variants from the yarn axes: `scalar` (Kpar everywhere, job 3068), `tensor` (Kpar
along the yarn, Kperp across, `tensorA`), `tensor_crossKyy` (crossing yarns K_yy = Kpar: their conduit along y restored),
`tensor_yarnKzz` (y-yarns K_zz = Kpar: the crimp staircase without its penalty), `*_yonly` (crossing yarns impermeable).
Runs to compare with (h² fit and uptake coefficient, both measures agree within 1 %): w_run 0.70 (job 3068), 0.56 (`tensorA`),
ratio 0.80.
**Predictions (written before computing):**
- C1: `scalar` w_sat between 0.6 and 0.95 (the saturated network has no sink and no lagging crossing yarns, so ≥ w_run).
- C2: `tensor`/`scalar` between 0.75 and 0.90; within ±0.05 of 0.80 = the geometry alone explains the slower front of
  `tensorA`, and the conductance can stand in for REV runs for the anisotropy dependence of w.
- C3: the crossing yarns carry 20–40 % of the flux in `scalar`, under 10 % in `tensor`.
- C4: restoring the crossing yarns' K_yy recovers more of the `scalar` value than restoring the y-yarns' K_zz.
**Result (2026-11-10, job 3068's mesh = `tensorA`'s, 28 s for the six variants; solver checked first on synthetic cases:
uniform, rows in series, columns in parallel, a detached blob: exact):** yarn cells 78,489 (43,410 along y, 35,079 crossing),
φ_y 0.4632, one connected group spanning the period, the same flux through every plane to 1e-12.

| Variant | K_eff [m²] | w_sat | / `scalar` | flux share: along y / crossing / mixed faces |
|---|---|---|---|---|
| `scalar` | 2.74e-12 | 0.591 | 1 | 0.841 / 0.154 / 0.005 |
| `tensor` | 2.14e-12 | 0.461 | 0.780 | 0.921 / 0.075 / 0.004 |
| `tensor_crossKyy` | 2.25e-12 | 0.486 | 0.821 | 0.882 / 0.110 / 0.007 |
| `tensor_yarnKzz` | 2.47e-12 | 0.533 | 0.901 | 0.925 / 0.071 / 0.003 |
| `scalar_yonly` | 2.29e-12 | 0.493 | 0.834 | 1 / 0 / 0 |
| `tensor_yonly` | 1.93e-12 | 0.417 | 0.705 | 1 / 0 / 0 |

- **C1 fails:** w_sat 0.59 is below the runs' 0.70 (job 3068; the saturated network is 15–20 % less conductive than the wicking
  rate implies). Cause not known; candidates, not tested: the bath also feeds the yarn flanks through the gap water near the
  bath (8–12 % of the inflow in the runs), the unsaturated network is not the saturated one scaled by kr.
- **C2 passes:** `tensor`/`scalar` 0.780 against 0.81–0.82 from the runs (h² fit 0.816, offset fit 2–20 ms 0.807, uptake 0.807):
  the geometry of the saturated network reproduces the anisotropy effect within 0.04.
- **C3 half:** the crossing yarns carry 15 % of the flux in `scalar` (predicted 20–40 %), 7.5 % in `tensor` (under 10 %).
- **C4 fails:** restoring the y-yarns' K_zz recovers 55 % of the gap between `tensor` and `scalar`, the crossing yarns' K_yy 19 %.
  Without the crossing yarns the anisotropy still costs 15.5 % (`tensor_yonly`/`scalar_yonly` 0.845): most of the drop is inside
  the y-yarns, where the crimp makes the flow step in z through faces at Kperp. That penalty may partly be a representation
  effect of the axis-aligned K on the staircase (the real fibres follow the crimp, crimp angle ~11°); not quantified.
- **Reading:** the conductance reproduces ratios (the anisotropy effect), not the absolute w. Use: w of a new geometry =
  w_run of a reference × the ratio of the conductances; the twill run tests that across geometries.

### Weave test: twill 1/3 (`twillA`, set up 2026-11-10, not run yet)
Question (user, 2026-11-10): does the weave alone change the REV result noticeably? If not, w is close to one number for
these yarns and densities, and the upscaling strategy changes. `twillA` = `tensorA` with one change, the STL: twill 1/3 from
`geometry/funge.py` (same yarns, densities 22 / 15 per cm, v 0.4, r_f 0.5); the same construction of the mid-gap bath (the
`inspect_stl.py` box moved by half a weft spacing along y), K diagonal in the yarn axes (Kpar 1e-11, Kperp 2.2e-12), 20 ms,
compared with `tensorA` over the same windows.
- **First STL (generated by the user 2026-11-10 with the original twill block of `funge.py`): not periodic.** Built in a
  scratch copy: box z −0.083–0.231 mm (0.314 mm, PW 0.282: the cubic spline through the 1/3 pattern dips below the floats),
  91 × 133 × 16 box cells (dz 19.6 µm) + 3 + 3 padding layers = 266,266 cells, 79,298 porous, checkMesh OK, yarn volume
  0.623 mm³ (PW 0.633). Periodicity (`geometry/stl_periodicity.py`: STL vertices within 150 µm of an x or y plane of the box,
  moved by one period, distance to the STL surface): max 15.1 µm (weft 7), 11.9 (wefts 5, 9), 10.6–11.6 (warps 0, 2, 4),
  1.6–4.4 µm for warps 1, 3 and wefts 6, 8; 4.6 / 2.0 % of those vertices above 10 µm at the x / y planes. Plain weave, same
  check: max 0.7 µm (facet error).
- **Cause:** the twill node lists ran over −1 to 5 spacings (1.5 periods of the 4-spacing pattern) with repeat vectors of 5
  spacings, so the yarn ends shape the cubic spline inside the box. Centreline check (scipy cubic splines of the node
  heights against the infinite pattern, inside the box): 4–17 µm off, depending on the end condition.
- **Fix (2026-11-10, `geometry/funge.py`):** the twill block builds its nodes from the 1/3 pattern over −4 to 8 spacings (3
  whole periods), repeat vectors 13 spacings; the same check gives ≤ 0.33 µm (natural and not-a-knot ends), 0 (periodic
  ends). The block now tests the function argument `weave` like the other blocks. The basket (BW) block has the same
  1.5-period node lists (not changed). The defect (up to 0.75 cell where the yarn cells on both sides of the cyclic planes
  should line up) has an effect not quantified against an expected difference of a few %, hence the regeneration.
- **Regenerated STL (user, 2026-11-10, replaces the first one in `geometry/Textiles/`):** 10 closed bodies, yarns twice as long
  (only the part in the box is used). Periodic: max 0.55 µm at the x planes, 0.06 µm at the y planes (plain weave 0.69 / 0.27
  µm). Box (`inspect_stl.py` → `rev_domain_TW.json`; `rev_domain_TW_midbath.json` with job 3068's y shift): z −0.0804–0.2272
  mm (0.3075 mm; first STL 0.314, PW 0.282), the same z range inside the box as over the whole STL (the yarn ends do not set
  it). Mesh (`Allpre`, 33 s): 91 × 133 × (3 + 15 + 3) = 254,163 cells of 20.0 × 20.05 × 20.5 µm, 75,936 porous (0.624 mm³; PW
  78,489 cells, 0.633 mm³), 178,227 free, inlet 1,365 faces (322 porous, 1,043 free; PW 330 + 944), checkMesh OK; crossing
  yarn 5 outside the box as in job 3068.
- **Conductance (`tools/conductance.py`, 19 s):** φ_y 0.418 (PW 0.463); w_sat `scalar` 0.581 (0.591), `tensor` 0.498 (0.461):
  twill/plain 1.080 with the tensor K, 0.983 with the scalar K; `tensor`/`scalar` 0.857 (PW 0.780: longer floats, fewer z-steps
  at Kperp in the y-yarns, see C4); the crossing yarns carry 4.1 % of the flux (PW 7.5 %). The first STL gave the same w_sat
  within 0.001 (its defect sat at the planes only).

**Predictions (written 2026-11-10, before the run).** Reference `tensorA` (job 3107: same K, bath construction and initial
state; values at 1 / 5 / 10 / 20 ms: front 1.005 / 1.486 / 1.847 / 2.409 mm, fit 2–20 ms 12.97 mm/√s, h² fit k 13.6 mm/√s;
uptake per fabric width (water above the bath plane, yarns + gaps, ÷ 1.818 mm) per window 0.619 / 0.574 / 0.601 / 0.599
mm²/√s over 2–5 / 5–10 / 10–15 / 15–20 ms; crossing yarn 6 S 0.890 at 5 ms, yarn 7 0.450 at 10 ms, yarn 8 0.255 at 20 ms;
gap water 296 cell volumes at 1 ms, 115–214 after). Ratio method of the conductance section: w_twill = w_tensorA × 1.080,
front ×√1.080 = 1.039, uptake per width × 0.985 (yarn volume per fabric area) × 1.039 = 1.024.
- T1 stability: no stopGuard to 20 ms; α ≤ 1.02; free |U| ≤ 3 m/s at the writes from 2 ms; |imbalance| ≤ 1e-16 m³; lost
  through top/bottom ≤ 20 cell volumes (`tensorA` 7.4 by 30 ms).
- T2 front: fit 2–20 ms 13.2–13.8 mm/√s (ratio 1.02–1.06), h² fit k 13.9–14.4 mm/√s; front at 20 ms 2.43–2.52 mm; closed
  end (2.99 mm) not reached.
- T3 uptake per width: ratio to `tensorA` 1.00–1.05 in each window 5–10, 10–15, 15–20 ms.
- T4 crossing yarns: yarn 6 S at 5 ms 0.80–0.95, yarn 7 at 10 ms 0.35–0.60, yarn 8 at 20 ms 0.15–0.40.
- T5 gaps: drained by 2 ms (gap water at 1 ms 150–1,500 cell volumes, 50–500 after); first fabric row ≤ 50 of the 1,043
  free cells water (the J cut-off; `tensorA` 19 of 944).
- T6 dt 2.3–2.8e-7 s at the Coats limit (cells within 2 % of the plain mesh, same K); 20 ms in 10–15 h on 8 cores (254k
  cells, +5 %; `tensorA` 0.61 s per step under load, job 3068 0.425).
**Reading.** T2 and T3 inside their ranges: the saturated conductance carries the weave effect across geometries (so far
tested on the anisotropy only, C2), so w of another weave of these yarns comes from a linear solve in seconds and REV runs
serve as checks; and the weave changes w by ~8 % here (front +4 %, uptake +2 %), small against the scatter of repeated
strip tests (Parada 2018), so for these yarns and densities the weave is a second-order input. Front or uptake ratio
outside the ranges by more than their width: the weave also acts through what the saturated network leaves out
(crossing-yarn sinks, gap water, air venting), and w needs a REV run per weave.
- **Smoke test (laptop, scratch copy, 4 cores, 60 steps, after the predictions):** J, L and T active (precompile log); dt at
  the Coats limit from step 30, 2.71e-7 s (CFL 0.499; dSmax limit 1.28e-6 s, capillary waves 1.51e-6 s; `tensorA` 2.74e-7);
  α in [−4.9e-19, 1.0006]; imbalance −2.9e-21 m³; 1.54 s per step on 4 cores.

### Horizontal: resolved by a wet contact zone (2026-11-09, `../verification/study2f_horizontalAir/`)
The dry start below fails because a dry yarn cell touching bath water gets the Van Genuchten dry-end capillary pressure (2.5 MPa at
S 0.002) across one face; it tears the bath surface beside the crests in the first steps and the study 2c pump follows. With the yarn
cells of the bottom four fabric layers starting on a ramp (S 0.84 / 0.64 / 0.35 / 0.15; `Allpre`: `initFields.py --free-fill 1e-4
--sat-height 1e-4 --ramp 8e-5`, the same treatment as the bath of the vertical cases) the case runs to 0.5 ms **with the unchanged
solver** (study 2f R3b, laptop, 4 cores, 3,865 steps, 1.7 h; copy `~/PDM_results/study2f_R3b_ramp`): uptake 135.9 g/m² at 0.5 ms
(yarns ~55, gaps ~81), yarns S 0.92, gaps filling bottom-up (52 % of the fabric's free cells, the open surface layers dry), a
transient sag of the thin bath (refilled by 350 µs), the displaced air leaving through the top at the water's inflow rate (3–5 m/s
in the narrow mid-thickness passages). Adopted by the user the same day; `Allpre` reproduces R3b's initial fields byte for byte.
Predictions H1–H4 above were written for the dry start and are superseded by these for the cluster run (written 2026-11-09, before
it):
- J1: 5 ms without stopGuard on 16 cores; to 0.5 ms within 3 % of R3b (another decomposition).
- J2: yarn mean S ≥ 0.95 by 2 ms; gaps of layers 9–14 ≥ 90 % water by 2 ms; the open surface layers 15–18 below 20 % water at
  5 ms (no confinement above the yarn crests, as S9 with closed yarns); no water out through the top beyond 10 cell volumes.
- J3: uptake at 5 ms between 140 and 200 g/m² (everything full: 217).
- J4: fastest fabric free cell below 1 m/s from 1.5 ms (the venting falls with the uptake rate); bath air below 200 cell volumes
  from 0.4 ms on.
- Cost estimate: 1–2 h per simulated ms on 16 mini03 cores (laptop 4 cores: 3.4 h per ms), 5 ms in 5–10 h.

### Horizontal: smoke test failed (2026-11-09), case on hold (superseded, see above)

Laptop, 4 cores (scratch copy). **600-step test: stopGuard at step 350, t = 31 µs** (dt 8.8e-15 s), α ≤ 1.0001, budget closed.
dt rose from 3.6e-11 s (step 10, the dry crests taking bath water) to 1.4–2e-7 s at the Coats limit (steps 150–250), while a
velocity grew ~8 % per step (Co·Δx/dt ≈ 19 / 30 / 80 / 230 / 750 m/s at steps 240 / 250 / 262 / 270 / 278).
Rerun with `dsLocator` (from `verification/study2e_bathLayer/tools`) and a write every 20 steps: the runaway is one bath-surface
cell under a yarn crest, (1.389, 2.055, −0.081) mm, α 0.24 → 0.10, |U| 6 / 25 / 750 / 9e4 m/s at steps 160 / 240 / 276 / 300.
Fluxes across the bath surface (12,103 faces, 747 under crests): the dry yarns vent their air down into the bath through the
crest faces (18–41 cell volumes per µs from 1 µs), more air enters through the faces under the gaps (5–19 per µs), J at the bath
bottom passes no air: bath air 373 → 1,684 cell volumes by 31 µs, all 747 bath cells under the crests α < 0.5 by 5 µs, after which
the crests take ~no water (the bath feeds the gaps only, +18 → +83 per µs). A partly filled bath cell under a crest then runs away
(the study 2c pump). Model gap: nothing stops air from a porous cell entering a water-filled free cell (`../NOTES_solver.md`, open
issues).
Variant with the 747 crest cells at S 0.99 (`--sat-height 1.2e-4`, 369 cell volumes): 300 steps (18 µs) without stopGuard, dt back
to 1.2e-7 s, but a start transient (515 m/s in 5,060 fabric free cells at 0.01 µs) and 13–26 m/s for 100+ steps after; the crest
venting drops to 7–15 per µs, the air now enters through the faces under the gaps (19–125 per µs: water rising into the first
fabric layer swaps with its air across the flat bath surface); bath air 14 → 1,188 cell volumes by 18 µs, 565 of the 747 bath
cells under crests α < 0.5. **Not a fix.** Two air leaks into a bath that cannot vent: from dry yarns, and across the flat bath
surface where the fabric draws water through part of it. Options (each a study with predictions, decided with the user): a bath
that lets air out; a solver change (no air from a porous cell into a free cell with α > 0.5: the first leak only); the waterline
inside a submerged fabric layer (no open bath surface under the fabric). `job.slurm` stops at its first line until then.
**Would a solver rule "no air from a yarn into a mostly-water free cell" fix it? (analysis of the two runs above, 2026-11-09,
not run with the rule):** air flowing out of yarns into free cells, split by the free cell's α, against the air entering the
bath through its surface. Dry start: into wet cells (α > 0.5) 15–27 cell volumes per µs only in the first µs, which turns the
bath cells under the crests air-rich; after that the venting (50–110 per µs) goes into those now air-rich cells, and 38–47 per
µs enter the bath. The rule would act at the start, so the cells under the crests would stay water: it should stop this first
leak. Pre-wetted crests: into wet cells only 2–37 per µs after 1.6 µs, but 95–131 per µs into air-filled gap cells (the normal,
physical venting of the yarns), and 34–100 per µs of air still enter the bath through its flat surface under the gaps: the air
vented into the gaps goes down into the bath instead of up and out. The rule would not touch that second route. Hypothesis:
the rule is needed for a dry fabric on water but not sufficient; the flat bath surface under the open space under the fabric
also has to go (the submerged-fabric set-up, waterline inside the fabric), or the second route needs its own fix.

## Commands

Laptop, check a case before submitting (scratch copy of the whole folder, so the relative paths hold):
`cp -r REV_pipeline <scratch>/ && cd <scratch>/REV_pipeline/cases/<case> && PY=<repo>/.venv/bin/python ./Allpre`; smoke
test: `maxSteps` in `system/controlDict`, `N 4` in `caseSetup`, `LOG_DIR=<scratch>/logs ./run`.

Cluster (mini03), after commit, push and `git pull` (solver `4bb5d2e`, already there): check the load (`squeue`,
`sinfo -o "%n %C"`), then in each case folder `sbatch job.slurm` (`tensorA`, `tensorB`: 8 cores; `horizontal`: 16). The
job builds the case (`./Allpre`, ~20 s), checks the cell counts against the laptop build, runs, reconstructs. Restart
after a crash: `sbatch job_restart.slurm` (never `job.slurm` on a run in progress: its `Allpre` deletes the results; it
continues by itself if `processor0/` exists).

Fetch: `rsync -avz --exclude 'processor*' --exclude 'dynamicCode' msinegre@mini03.polito.it:PDM_repo_perso/REV_pipeline/cases/<case>/ ~/PDM_results/REV_pipeline_<case>/`,
then point the includes at this folder's tools (paraFoam and postProcess need them):
`sed -i 's#"\.\./\.\./\.\./tools/#"/home/martin_sng/PDM_repo_perso/REV_pipeline/tools/#' ~/PDM_results/REV_pipeline_<case>/system/controlDict`.
Analysis: `tools/compare3068.py <copy>` (tensor cases), `tools/check.py <copy>`, `tools/zLayers.py <copy>` (horizontal).

## Pipeline: the main script (planned, not written)

One input file per REV, one command. Steps and what exists for each:
1. STL from the weave inputs (weave, picks/cm D1 D2, yarn sizes, v, rf): `geometry/funge.py`, today a TexGen script
   with the inputs in its first lines, run in the TexGen GUI. Needs a TexGen Python callable from the pipeline (open
   point, see below).
2. REV box: `geometry/inspect_stl.py` (+ the half-spacing shift for a mid-gap bath).
3. Case folder from a reference (`cases/tensorA` for vertical wicking, `cases/horizontal` for the through-thickness
   set-up): copy, then the dictionaries filled from the inputs (yarn K or Gebart inputs, pc0, m, θ, end time, cores).
4. Mesh and fields: `tools/build_fields.py`, `tools/initFields.py` (what `Allpre` does).
5. Checks: checkMesh, cell counts, periodicity, a short smoke test.
6. Launch: `./run` on the laptop, or `job.slurm` written for the cluster (the submission itself stays a manual `sbatch`).

Open point for step 1: TexGen is installed on Windows (`C:\Program Files\TexGen`, bundle 3.13.1 with an embedded Python
3.9, no `python.exe`); WSL and the clusters cannot import it. Options: run `funge.py` in the GUI (manual step, STL
committed, as now); a Windows Python 3.9 with TexGen's `Python/libxtra` on its path, called from WSL; or TexGen built on
Linux (also usable on the clusters).
