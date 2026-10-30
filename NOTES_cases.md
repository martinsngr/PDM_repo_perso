# Wicking cases — 1D, single yarn, fabric REV

Setups, results and open work of the cases in `trialWicking/` (1D column and single yarn, impesFoam and
hybridPorousInterFoam) and `meshing_strat_trial/` (fabric REV, 2D bench, slit tests). Last updated 2026-10-30.
Companion file: `NOTES_solver.md` (solver changes A–I, model, verification, open solver issues).
(Before 2026-10-13: `trialWicking/NOTES.md` and `meshing_strat_trial/NOTES.md`; day-by-day record in git history.)
**Start a new session at "Next steps".**

## Folder map

| Path | What it is |
|---|---|
| `trialWicking/1D_vertical_impes/` | 1D column (yarn centreline unfolded, 3.446 mm, 172 cells of 20 µm), reservoir = bottom 0.2 mm cellZone clamped at Sb 0.99 (`fixedSb`), open top. impesFoam |
| `trialWicking/1D_vertical_impes_inletRes/` | Same, reservoir as the inlet boundary (Sb fixed 0.99), dry 0.002 with a 0.2 mm ramp: twin of the hybrid case. 0.1 s in ~2 min |
| `trialWicking/1D_vertical_hybrid/` | The same column in hybridPorousInterFoam (`darcyFaceMaxDa 0.1`), coded inlet/outlet p (air at 0 Pa), Coats dt from a coded function object. 0.1 s in ~8 min. Case description in its `README.md` |
| `trialWicking/singleYarn_IMPES_yarn/` | Original 3D yarn case (`yarn-c.stl`), reference only (24 negative-volume cells) |
| `trialWicking/singleYarn_IMPES_vertical/` | 1D vertical setup on the yarn geometry, open lateral wall (crashed near saturation, see below) |
| `trialWicking/singleYarn_vertical_impes_inletRes/` | Yarn twin of `1D_vertical_impes_inletRes` (15,188 cells, lateral wall closed). 0.1 s: mini03 3.8 h |
| `trialWicking/singleYarn_vertical_hybrid/` | Yarn twin of `1D_vertical_hybrid` (lateral wall closed). 0.1 s: mini03 11.9 h |
| `trialWicking/wickingFront.ipynb` | Front analysis of the 1D cases (front at S = 0.1 vs √t, profiles, p_air/p_water) |
| `meshing_strat_trial/REV/` | **The REV in one folder:** TexGen geometry (`Textiles/`, `funge.py`), `inspect_stl.py` (REV box → `rev_domain.json`, `--zgap`), `build_fields.py` (mesh + eps, K, fYarn, yarnID), `check_periodicity.py`, `meshing.pvsm`, solver dictionaries, `Allpre` (geometry → mesh → fields → initial α). Run scripts not written yet |
| `meshing_strat_trial/REV_lowpc/` | Copy of `REV/` with VG pc0 1000 Pa, m 0.4 and θ0 40° (2026-10-27); with change L, 10 ms, 4 cores since 2026-10-30 |
| `meshing_strat_trial/REV_gapflow/` | Copy of `REV_lowpc` with K 2e-11, VG pc0 500 Pa, m 0.4, θ0 40°, `darcyFaceMaxDa` 0.2, L, 150 ms, 8 cores (2026-10-30): can the solver show gap water rising behind the yarn saturation? Not physical values |
| `meshing_strat_trial/2D_bench/` | **The 2D bench:** thick-wall slit (yarn wall 8 cells \| gap 8 \| yarn wall 8), G + H + F′ + I on; `Allpre`, `run`, `check.py` |
| `meshing_strat_trial/2D_bench_strip/` | First 2D bench (strip between open free layers), archive: `variants/` (debugging runs, referees R1–R3, `makeVariant.sh`, `ADD=` option) and figures; template of `slit_test/makeSlit.py` |
| `meshing_strat_trial/slit_test/` | Slit capillary-rise tests: `makeSlit.py` (`--walls real/porous`, `--nw`, `--w`, `--K`, `--theta`, `--dx`, `--add`), `slitReport.py`, `benchSlit.py`, `interFoamSlit.sh`, `figures/`, `old_runs/`. Run folders: `S0_*` real walls, `P_*` current porous-wall set, `IF_*` stock interFoam; `B_/H_/HF_/I_/J_/N_/R_/V_` intermediate |
| `verification/` (repo root) | All verification: paper tutorials, 1D similarity solution, ddtCorr bench, inlet test (moved from `trialWicking/verification/` 2026-10-13; results in `NOTES_solver.md`), and **`PLAN.md`: the planned studies 1–3** |
| `meshing_strat_trial/tools/` | `runTools.sh`, `initFields.py`, `pOpenAir` (coded open-patch p BC of the 2D bench and slit cases; `REV/` and `REV_lowpc/` use `totalPressure` since 2026-10-27), function objects `coatsTimeStep`, `liquidBalance`, `waterBudget`, `stopGuard` |

## Common setup and rules

- **Properties (setup values, not calibrated):** K 1e-11 m² scalar, ε 0.5, Brooks–Corey n 3, Van Genuchten pc0 5000 Pa
  m 0.5, water/air (μ 1e-3 / 1.76e-5 Pa·s), σ 0.072. pc0 5000 Pa is consistent with K 1e-11 by Leverett scaling (4–8 kPa).
  The wicking rate constrains K·pc0, the equilibrium height (pc0/ρg ≈ 0.5 m) constrains pc0: fitting both needs
  experimental-length samples. Real K (tensor), pc and contact angle (polyester) come later.
- **Gravity along the wicking direction** (−x), reservoir at x-min (REV: −y, reservoir at y-min).
- **Case layout (meshing_strat_trial):** source fields in `0.orig/`, `./Allpre` writes `0/` (eps, K by setFields or
  build_fields, `alpha.wetting` by `initFields.py`); `0/` is never edited by hand and not committed; `./clean` keeps
  `0`, `0.orig` and the mesh.
- **Solver logs never in the workspace** (`runTmpLog` in `runTools.sh`; `LOG_EVERY=100` for long runs; on a cluster
  `LOG_DIR=$PWD/logs`). Hand-run tests log to /tmp or the scratchpad.
- **Cluster mini01: `sbatch job.slurm` only**, never `./run` there (OF9 at /opt/OpenFOAM-9; check free CPUs with
  `squeue`; job checks `N` in `caseSetup` = `--ntasks`). Parallel hybrid runs compile the coded BCs/function objects
  first in serial (`hybridPorousInterFoam -postProcess -time 0`; inside `mpirun` they abort with `MPI_ERR_TRUNCATE`).
  impesFoam on mini01: `./Allwmake` stops at `groundwater2DFoam`; `wmake` the five libraries, then `solvers/impesFoam`.
- **Python:** repo `.venv` (numpy, trimesh, matplotlib, ipykernel).

## 1D and single-yarn cases (`trialWicking/`)

### Geometry and mesh of the yarn
- The yarn is crimped: flat section ~0.55 mm wide, 0.22–0.29 mm thick, centre oscillating in z with ~1.8 mm period.
  Unfolded centreline 3.446 mm for x 0.4–3.6 mm; real section lens-shaped, 27 % smaller than the 0.55 × 0.237 mm
  rectangle (scale 1D uptake volumes by 0.73 before comparing with 3D).
- Fixes to the snappy pipeline: inside point taken from a mid-length slice (`zcat 0.000179`, `bounding.py`; the
  bounding-box centre was outside the crimped yarn); `topoSetDict` keeps snappy's `yarn` zone; `blockMeshDict` uses
  `$w1`; `minVol` 1e-25 (an absolute volume inherited from the metre-scale fabric case flagged 750k faces);
  `left`/`right` patches instead of symmetry.
- Current mesh: `CpD 12`, `refLev 1`: 15,188 cells, volume +0.2 %, checkMesh OK, max non-orthogonality 42°
  (refLev 2: 68,296 cells, +0.3 %).

### impesFoam findings
- Without `adjustTimeStep yes` deltaT is never adapted (the original case's fixed 1e-9).
- **Todd capillary limit bug (upstream):** `ToddNo.H:61` divides `maxCo` by `Tpc` (a time), so the limit never applies.
  **Use `CFL Coats`** (maxCo 0.5, dSmax 0.01), no `minDeltaT` floors. Not reported upstream yet.
- Any Sb above Sbmax crashes (VG returns NaN). `singleYarn_IMPES_vertical` (open lateral wall) crashed at 0.068 s near
  saturation; likely the Coats mobility vs the liquid-only `phiPc`, and the open wall (fixed p lets both phases cross in
  `pEqn`, `SEqn` forces phib = 0). The closed-wall twins run to 0.1 s.

### Results
- **1D:** impesFoam (inletRes) mean Sb 0.352 / 0.606 / 0.777 / 0.902 at 0.01 / 0.03 / 0.05 / 0.1 s; hybrid 0.335 / 0.583 /
  0.751 / 0.891. Front (S 0.1): k = 18.35 (impesFoam), 18.03 mm/√s (hybrid; 1D similarity 18.04). Verification against
  the similarity solution and the inlet/air-pressure split: `NOTES_solver.md`.
- **Single yarn, 0.1 s on mini03 (4 cores, 2026-10-02):** impesFoam 3.8 h, 1.79M steps, mean Sb 0.904; hybrid 11.9 h,
  1.88M steps, mean α 0.899. dt at the Coats limit throughout (5e-8 → 3.5e-8 while filling → 1.5e-7 near saturation).
  p, p_air, p_water, `Uwetting` profiles in `wickingFront.ipynb` (U near the wall from pre-F binaries is not meaningful).

### Cost and scaling
- Explicit IMPES: dt ≈ Δx_min²/D with D ≈ K·pc0/(μ·ε) ≈ 1e-4 m²/s; number of steps ≈ (wicked distance/Δx_min)², independent
  of the physical size; cost ∝ (L/d)³·CpD⁵ (cm of yarn in 3D would take months). pc0 rescales the physical time only.
- Per step on 15k cells: laptop 19 ms (impesFoam) / 84 ms (hybrid), mini03 7.6 / 22.7 ms; more cores don't help.
  Estimate runs from a short test's step count × the per-step cost after a few hundred steps on the target machine.

### Running (yarn cases)
- `nohup ./run > run.out 2>&1 &`; progress `grep "^Time =" log*.impesFoam | tail -1`.
- **If a run dies, do not rerun `./run`** (it deletes meshes and results): set `startFrom latestTime`, relaunch the
  solver by hand with the log outside the workspace, then `reconstructPar` and `postProcess -func sampleDict`.
- Laptop: lid close → do nothing, sleep → never while plugged in (WSL2 may stop without an open window).

## Fabric REV (`meshing_strat_trial/`)

### REV geometry
- TexGen plain weave `PW-22-15-0.4-0.5.stl` (cm → ×0.01). REV 1.82 × 2.67 × 0.28 mm, 91 × 133 × 14 cells of 20 µm =
  169,442 cells. `build_fields.py --k-mode scalar --k-scalar 1e-11 --cut-cells binary` (f ≥ 0.5 → yarn; every cell with
  eps ≤ 0.99 gets the yarn K, others K_VOID = 1 m²): 78,528 porous, 90,914 free; inlet 1,862 faces (1,262 porous).
  Free fraction per z layer 0.86 (bottom) → 0.15 (middle) → 0.91 (top) counting every cell touched by a yarn as yarn;
  with the binary cut the solver sees (f ≥ 0.5): 0.94 → 0.21 → 0.97. The edge layers are mostly open space beside the
  crimped fabric.
- **Yarns:** thickness median 6 cells (120 µm), max 7–8; width ~15 cells (300 µm); yarns 0/4 and 5/9 are halves cut by
  the periodic boundaries. A yarn flank facing an in-plane gap is ~8 cells deep, a face facing a crimp pocket ~3.
- **Gaps** (narrowest free run between yarns along x, y or z, per free cell): median 15 cells (300 µm), p25 9, p10 6, p5 4;
  ≤ 4 cells 6 %, ≤ 8 cells 20 %. Narrow throats at mid-thickness where warp and weft cross; near the surfaces medians
  18–58 cells. 82 % of the free cells inside the fabric envelope, 1 % enclosed. TexGen model, not the real fabric.
- **Boundaries and connectivity** (binary mesh, measured 2026-10-26 with `tools/revGeometry.py --axis x|y`): yarns 0–4
  run along y over 2.66 mm (0 and 4 are halves at the x-periodic planes, one yarn across them), yarns 5–9 along x over
  1.82 mm (5 and 9 halves at the y planes). Each periodic plane cuts a crossing yarn along its centreline: porous faces
  x planes 1,262 of 1,862 (68 %), y planes 984 of 1,274 (77 %); bottom 747 and top 417 of 12,103 (6.2 / 3.4 %, yarn
  crests); **no porous/free face pair across the x or the y planes** (first and last layers identical); 38,242
  internal porous/free faces. The free cells form one network (all but 4 cells) joining the opposite faces in x and in
  y, still connected without the outer 4 z layers. Straight full-length free rows exist only in the outer layers (along
  x: 396 of 1,862 rows, z layers 0–2 and 10–13; along y: 204 of 1,274, z layers 0–2 and 11–13). Widest path crossing
  the REV: cells ≥ 3 cells from the nearest yarn cell and from the top/bottom planes along x, only ≥ 2 along y (the
  in-plane gaps between the y-yarns are narrower). **The gaps form a continuous but tortuous network** (over and
  under the crossing yarns), not isolated pockets.
- **Faces that a yarn-aligned tensor K would change** (REV mesh with `--zpad 3`, `0/yarnID`, measured 2026-10-27): of
  the 984 porous inlet faces 665 belong to the half crossing yarn 5 (an x-yarn: K_yy = Kperp), 319 to the y-yarns
  0–4 (K_yy = Kpar); 4,457 porous/porous warp/weft contact faces (yarns 0–4 against 5–9): 3,221 z-faces (Kperp on
  both sides), 860 x-faces and 376 y-faces (Kpar on one side, Kperp on the other).

### Gap vs yarn wicking (estimates)
Viscous Washburn h²/t = σw cosθ/(3μ) for a slit: w 160 µm θ 60° → 44 mm/√s, w 300 µm θ 75° → 43, θ 85° → 25; yarn
(K 1e-11, pc0 5000) 18 mm/√s. **A straight continuous gap out-runs the yarn unless θ ≳ 87°**, but stops at
h_eq = 2σcosθ/(ρgw) ≈ 13 mm (300 µm, θ 75°) while the yarn holds ~0.5 m. In a plain weave the gaps are interrupted by
crossing yarns (checked 2026-10-26, REV geometry above: the free space is continuous along x but tortuous, straight
channels only in the outer layers; whether the menisci pass the widenings behind each crossing is open). In the 2D bench the
yarn walls lead even with a straight gap (they draw water out of it).

### 2D bench (`2D_bench/`, since 2026-10-13)
- Thick-wall slit, 2.0 × 0.48 mm, 100 × 1 × 24 cells: yarn walls z < 0.16 and > 0.32 mm (eps 0.5, K 1e-11, ending 3 cells
  before the outlet: porous faces on an open patch are unstable), gap 8 cells (160 µm, ~20th percentile of the REV gaps;
  15 cells would be the median). Inlet reservoir (free faces at total pressure 0, `openFreeTotalPressure 1`; porous
  faces air at 0 Pa, `openPorousAirZero 1`), outlet open, top/bottom closed walls. θ 60°, G + H + F′ + I on. Initial:
  walls dry 0.002 with the 0.2 mm ramp, gap pure air with a 0.1 mm (5-cell) water column. 2 ms, serial ~3 min.
- Same case as `slit_test/makeSlit.py --walls porous --nw 8 --w 8 --K 1e-11 --theta 60` + the H/F′/I keywords:
  bit-identical results. ε, K and wall extent in `system/setFieldsDict`; widths in cells also in `check.py` (`NW`, `W`).
- **Result (2026-10-13, `b525086`), all 10 checks pass:** budget 5e-15, max |U| 1.2 m/s, no stray water; gap meniscus
  0.43 / 0.79 mm at 1 / 2 ms (impermeable walls 0.63 / 1.16); wall front 0.75 / 1.15 mm (walls alone, 1D: 0.60 / 0.83),
  uniform across the wall. **The walls lead the gap** (0.36 mm at 2 ms): they draw water out of the gap and are fed
  sideways along it. The meniscus first drops (0.11 → 0.09 mm) while the column feeds the walls.
- Known bias: θ fixed at 60° also on the wet wall surface ahead of the meniscus (physically ~0°): the gap rise is biased low.
- **20 ms run (`2D_bench_long/`, 2026-10-15, `b525086`):** stable (α bounded, budget 2.6e-14, max |U| 1.85 m/s); fronts
  reach the slit end at ~5–6 ms; afterwards a non-physical steady through-flow (~0.05 m/s in the gap, 10 % of the early
  wicking rate) leaves through the open outlet, with ±1 m/s churning in the outlet cells. Open outlets are not valid
  once water reaches them (details in its README).
- **θ 120° (`2D_bench_t120/`, run 2026-10-14):** stopped by stopGuard at 1.71 ms (dt 1e-14, min α −0.26). Not analysed.

### Slit tests (`slit_test/`, 2026-10-12/13)
- **Setup:** 2 mm vertical slit, 20 µm, reservoir at x = 0, open at x = 2 mm; `S0` real walls with
  `constantAlphaContactAngle`; porous walls `--nw` cells, closed behind, ending 3 cells before the outlet. Reference:
  Bosanquet rise ρ d(hḣ)/dt = 2σcosθ/w − 12μhḣ/w² − ρgh from the 0.1 mm start.
- **Inlet:** a static p = 0 inlet gives the entering water velocity without the dynamic-pressure cost (~60 % too fast
  at 2 ms); free inlet faces at total pressure 0 (`openFreeTotalPressure 1`, p = −½ρ|U|²) = reservoir at rest.
  Porous inlet faces (1D, single yarn, yarn part of the bench) keep static p: Darcy faces (B) and impesFoam carry no
  ½ρU², and it is small anyway (estimate, not run: pore velocity at 1 ms ~0.2 m/s → ~20 Pa vs pc ~kPa; comparable only
  for t < ~10 µs, inside the initial ramp). In the gap ½ρU² (50–500 Pa) competes with 2σcosθ/w = 450 Pa.
- **Initial water column needed:** with α `inletOutlet` an empty gap sees α = 0 on the inlet and never rises (stock
  interFoam the same); α fixed 1 on the inlet with an empty gap gives a spurious kick (6× too fast, 23 m/s); a 1-cell
  column drains back; 5 cells (0.1 mm) correct. The previous student's case had initial water in its `0/alpha.water`.
- **Previous student's setup** (interFoam, body-fitted free volume, impermeable yarns, θ 40–80°): p_rgh fixed 0 at inlet
  and atmosphere (static: early rise rates likely overestimated), g = 0, α inlet `inletOutlet` 1. Not a direct reference
  (smooth walls vs our staircased porous yarns). Compare with `--static-inlet`, g = 0 and her water depth if needed.
- **Results:** `NOTES_solver.md` (real walls vs Bosanquet 2–11 %; porous walls with G + H + F′ + I = real walls within 2 %;
  permeable walls; 10 µm). Meniscus depth resolved only 1–2 cells (θ 70–80° menisci are < 1 cell deep anyway).

### 2D_bench_strip (archive of the 2026-10-12 debugging)
Strip (8 porous cells) between open free layers of 3 and 4 cells, 1.0 × 0.3 mm. It located the Solidf bug (E) and the
missing capillary jump (F, G), see `NOTES_solver.md`. Lasting lessons: **porous faces on an open lateral boundary are
unstable** (all-porous strip with open top/bottom: α → 105); the closed all-porous strip reproduces 1D; **free cells must
start as pure air**; 3–4-cell gaps are not representative; with reservoir water entering the gaps the strip collapsed at
0.57 ms (unresolved meniscus, contact angle off, before H/F′/I). Variants: `variants/makeVariant.sh` (list at its top),
referees `R1staticWet`, `R2waterGap`, `R3closedRamp(Slab)`, figures `variants/figures/`; face-flux debug build and the
Solidf-bug figures in `debug_faceDump/`.

### REV case status (`REV/`, set up 2026-10-26)
**Setup (decided with the user 2026-10-26):** wicking along **y** (along yarns 0–4 over 2.67 mm = 2 weave repeats,
yarns 5–9 crossing), gravity −y, reservoir at y = 0, x cyclic. Mesh `build_fields.py --wick-axis y --zpad 3`: the
REV box (91 × 133 × 14, cells identical to the unpadded mesh) + 3 free layers (60 µm) below and above = 91 × 133 × 20
= 242,060 cells (78,528 porous). Patches:
- `inlet` (y = 0, box part): the bath, water-only (J). Since 2026-10-27 standard BCs (`verification/standardOpenBC`):
  p `totalPressure` 0 (bath at rest at 0 Pa), α inletOutlet 1 on all faces (`initFields.py --porous-in 1`: the yarn
  faces are saturated by the bath, so p = 0 there is the water pressure). Before (job 3051, smoke tests): coded
  `pOpenAir` (gap faces total pressure 0, yarn faces water at 0 Pa, p = (1 − α)·pc) with α 0.99 on the yarn faces;
- `inletPad` (y = 0, padding part) and `outlet` (y = L): closed walls (U noSlip, p fixedFluxPressure, α zeroGradient;
  phase velocities zeroGradient on every patch, output only). The outlet plane cuts the half crossing yarn 9 along its centreline (77 % porous faces): open,
  it would carry porous faces on an open boundary (unstable) and the open-outlet artefact once water arrives
  (`2D_bench_long`); with top/bottom open, air does not need it;
- `bottom`/`top`: faces of the padding, open to air (p `totalPressure` 0 since 2026-10-27, before `pOpenAir`: same
  numbers; α inletOutlet 0); `sideA`/`sideB`: cyclic in x.

Initial state as `2D_bench` (`initFields.py --closed-patch outlet --closed-patch inletPad --free-fill 1e-4`): yarns
0.002 with the 0.2 mm ramp (holds the same water as a saturated 0.1 mm column), free box cells within 0.1 mm of the
inlet full of water (1,645 cells), padding dry. `constant/transportProperties` = `2D_bench` (G + H + F′ + I, θ 60°);
`system/controlDict` = `2D_bench` (Coats dt, stopGuard, liquidBalance, waterBudget) with endTime 10 ms and writes every
0.5 ms (46 MB each). Scripts: `./Allpre` (20 s), `./run` (serial precompile, decomposePar scotch, mpirun with N from
`caseSetup`, reconstructPar), `check.py` (per-write checks). Checked: box fields identical to the unpadded mesh; x and
y planes exactly periodic (`check_periodicity.py`); padding dry, ramp along y. `job.slurm` (2026-10-26): 10 ms on mini03, 16 cores, saturated rows (`Allpre`: `--sat-height 1e-4`); the mesh
and 0/ are built by the job itself (`./Allpre`; mini03 repo `.venv`: numpy scipy trimesh==5.1.0 rtree embreex; without
embreex the mesh build takes > 1 h instead of 7 s; the job checks the cell counts 78,528 / 163,532); `run` stops if the
solver ignores `waterOnlyPatches`.
- **Cluster run (mini03, job 3051, started 2026-10-26 ~15:25, 16 cores, solver `c3dbf48` built there, 10 ms):** cost
  ~1,900 s per simulated ms (1.89 ms after 3,590 s; laptop 4 cores: 11,600 s/ms) → end ~20:30–21:00. Clean to 1.9 ms (no
  stop). **α overshoot in episodes:** max α per 0.2 ms window 1.001, 1.007, 1.016, 1.022, 1.023 (0.8–1.0 ms), then 1.007,
  1.009, 1.013, 1.016, 1.003 (1.8–2.0 ms): builds up ~0.6–0.8 ms then collapses, bounded; > 1.01 on 282 steps by
  1.9 ms. The laptop's 4-core run of the same case peaked at 1.0017 to 0.5 ms → possibly decomposition-sensitive.
  Results: `meshing_strat_trial/REV/` on mini03 (reconstructPar at the end; solver log in `logs/REV.*/`).
- **Job 3051 analysed (2026-10-27, copy in `~/PDM_results/REV_run3051`, `check.py` over the 20 writes):** reached
  10 ms, no stopGuard, 20,440 s on 16 cores (~85k steps, dt 1.0e-8 to 1.3e-7 s; in the 850 sampled log steps dt
  is set by the Coats limit on 792 (1.25e-7 s), by dSmax on 58; dSmax limit mostly 3.7–6.6e-7 s, capillary-wave
  limit 1.5e-6 s). Budget closed (imbalance 1.5e-20 m³,
  1e-10 of the water); water lost through top/bottom 10.2 cell volumes; padding dry; α min −2e-20.
  - **Yarn front (y-yarns, α > 0.1):** 0.27 → 0.69 / 1.13 / 1.63 mm at 1 / 4 / 10 ms; fit (t ≥ 2 ms)
    front = 13.9 mm/√s · √t + 0.24 mm, exponent of (front − 0.27 mm) vs t 0.52: diffusive. 1D reference 18 mm/√s
    (hypotheses for the lower rate, not tested: water drawn into crossing yarns and gaps, crimped path). Profile
    diffuse: S 0.98 at the inlet, 0.72 at 0.9 mm, 0.1 at 1.6 mm (10 ms). Mean porous S 0.096 → 0.411.
  - **Crossing yarns** wet as the y-yarn front reaches them: yarn 6 (y 0.50–0.84 mm) from ~1 ms, yarn 7 (1.16–1.50)
    from ~5.5 ms.
  - **Gaps: capillary valve confirmed.** Gap water never passes y 0.18–0.19 mm, i.e. the first row above the half
    crossing yarn 5 (y 0–0.16 mm); at 10 ms row y 0.16–0.18 holds 37 water cells, the next row 1 of 943 free cells.
    Gap water drains 1,645 → 268 cell volumes by 1 ms, then refills slowly to 383, piling up in rows y 0.10–0.18 mm.
  - **α overshoot grows:** in the sampled log steps (every 100th) max α > 1.001 on 11–37 % of steps per ms to 4 ms,
    68–86 % at 4–7 ms, 99–100 % after 7 ms; peaks 1.014 (0–1 ms), 1.020 (3–4), **1.051 (8–9 ms)**. At the writes the
    cells above 1.0005 (≤ 9) are almost all porous, inside the half yarn 5 at the inlet (y 0–0.16 mm, mostly not on
    the porous/free interface), saturated region. **Not decomposition-related:** scotch decomposition regenerated
    locally (`decomposePar -cellDist`, processor sizes and shared faces identical to the job's); 13 % of cells touch a
    processor face, overshoot cells hit one at about that rate. Next to the reservoir only once (y 0–0.02 mm, 5.5 ms).
  - **Velocity spikes** at single writes: 7.3 m/s at 1 ms (4 air-side interface cells near yarns 2/5, y 0.10–0.16 mm,
    all on processor faces), 3.0 / 5.1 / 3.3 m/s at 6.5 / 7 / 8 ms (air-side porous/free interface cells near yarn 5,
    not on processor faces). Water-cell |U| 0.6–0.9 m/s throughout.
- **Job 3055 (mini03, REV unchanged, 8 cores, endTime 50 ms, started 2026-10-27; overwrote the 3051 results on mini03):**
  4,390 s per simulated ms (3051 on 16 cores: 2,040), dt 1.26e-7 s at the Coats limit as in 3051, ~8,700 steps/ms.
  Live full log at 5.65 ms: max α per ms 1.046 / 1.042 / **1.092** / 1.022 / 1.086 / 1.056 (0–5 ms), above 1.001 on
  33,538 of 49,109 steps (68 %). 3051 (16 cores, full live log) stayed ≤ 1.023 to 2 ms: **the overshoot amplitude
  depends on the decomposition** (or on run-to-run differences), although at the 3051 writes the overshoot cells were
  not on processor faces. Episodic, back to ~1.005 between peaks; not monotonic over 0–5 ms.
  **mini03 crashed 2026-10-28 ~15:04** (rebooted ~15:37): the solver log stopped at t = 11.066 ms (last write 11.0 ms;
  NUL bytes in the log), no solver process left but squeue still showed 3055 running (also the other users' 3048 and
  3053, dead since the reboot, holding 36 CPUs). 3055 cancelled; **job 3058 = restart from 11.0 ms** with
  `REV/job_restart.slurm` (no `Allpre`/`clean`/`decomposePar`, same 8-core decomposition; a last write with missing,
  cut or NUL-containing files goes to `processor*/<t>.incomplete`; NUL check added after `800cb20`, the version on
  mini03 may lack it). Running at 11.083 ms the same afternoon. Full log of 3055 unfiltered in `logs/REV.eW8Mmo/`
  (89 MB, `grep -a`), restart log in `logs/REV.S65Z44/`. `waterBudget.csv`: the restart adds a second 0.011 row; inflows restart from 0 there, imbalance offset −3.4e-16 m³ (2e-6 of the water) from then on.
  **Never resubmit `job.slurm` to continue a run** (`Allpre` → `clean` deletes `processor*/`).
  **3055 + 3058 to 30.5 ms (copy `~/PDM_results/REV_run3055_3058`, 15 writes reconstructed locally, 2026-10-29):**
  0–10 ms = 3051 (y-yarn front 1.634 mm at 10 ms in both, mean porous S 0.410 vs 0.411, gap water 394 vs 383
  cells): the 2026-10-27 BC change has no integral effect to 10 ms. Restart continuous (front 1.714 → 1.754 mm,
  S 0.429 → 0.439 from 11 to 11.5 ms). y-yarn front at the closed end (2.657 mm) between 25 and 30 ms (fit of 3051:
  ~31 ms); mean porous S 0.70 and min porous α 0.15 at 30.5 ms. Budget closed after the restart (offset 1.78e-15 m³,
  7.9e-6 of the water, constant 11.5–30.5 ms); padding dry; ~12 cell volumes lost through top/bottom. Max α per ms
  1.02–1.09 to 11 ms, 1.014–1.046 at 11–20 ms, 1.004–1.010 after 20 ms; free Courant ≤ 0.06. dt < 5e-8 s on 1.8 % of
  the steps to 11 ms, 0.4 % after (location not checked). **Gaps:** valve held to ~12 ms; from 15 ms 2–4 free cells
  hold water at y 1.23–1.43 mm on both flanks of yarn 2 (x 0.77 and 1.05 mm, z 0.04 mm, next to crossing yarn 7);
  the fastest free cells (3.5 / 4.8 m/s at 15 / 20 ms, 1.3 m/s at 30.5 ms) are partly filled cells there with 2–3
  porous neighbours: the REV_lowpc pattern, weaker, appearing once the yarns are near saturation.
- **`REV_lowpc/` (2026-10-27): REV with Van Genuchten pc0 1000 Pa, m 0.4** (sharper pc drop with S; only change in
  `constant/transportProperties`, job name `REVlowpc`; that file also has theta0 40°, REV 60°, committed with it in
  `dbb7b0a`, noted 2026-10-27). VG pc/pc0 at the dry start S 0.002: 1.1e4 (m 0.5: 500). Same standard open-patch BCs
  as `REV/` since 2026-10-27 evening (files identical to `REV/` except pc0, m, θ, job name; scratch copy built by
  `./Allpre` and run 20 steps: J active, α in [−7e-20, 1.00001]); the smoke test below used the old BCs.
  **Smoke test, 0.2 ms** (scratch copy, 4 cores, writes every 0.05 ms): no stopGuard, 600 steps, dt 3.7–4.0e-7 s
  (REV ~1.2e-7), 850 s = ~4,250 s per ms (REV laptop 11,600); budget closed to 3e-24 m³; max α 1.00008 (≤ 1.001 on
  every step); max |U| 1.3–1.9 m/s (water cells up to 1.5 m/s at 0.1 ms; REV 0.7–1.0). Yarn front 0.27 → 0.37 mm,
  mean porous S 0.096 → 0.103, gap water 1,645 → 626 cell volumes (gap water front 0.15 mm). **Water flows back out
  through the reservoir face:** net inflow −5.8e-12 m³ (≈ 725 cell volumes) by 0.2 ms, slowing (−1.5 / −2.8 / −1.2 /
  −0.4e-12 m³ per 0.05 ms); the yarns took ≈ 290 cell volumes, so most of the drained gap column went back to the
  reservoir (REV saturated-rows smoke: −2.4e-12 m³ at 0.2 ms, inflow again by 0.5 ms). Water in the padding near the
  inlet: 232 cells α > 0.05 at 0.05 ms, 16 at 0.2 ms; lost through top/bottom 0.8 cell volumes. Cause not checked.
  **Job 3059 (mini03, 8 cores, 50 ms planned, 2026-10-28 16:04–20:17): diverged at 6.553 ms** (stopGuard, dt
  1.3e-24; SLURM `COMPLETED`, reconstructed; copy in `~/PDM_results/REV_lowpc_run3059`). Measured (sampled log,
  `.tail`, `check.py`): dt 2–4e-7 s at the Coats limit, max α ≤ 1.003, free Courant ≤ 0.36 up to 6.548 ms; then in
  ~20 steps dt ×0.65 per step at a free Courant pinned at ~1.17 (a velocity growing ~1.5× per step, ~30 → ~10^3 →
  ~10^6 m/s), Coats and dSmax limits falling with it (porous cells involved), α stays in [0, 1.003]; the last two
  p solves diverge (continuity errors 63, 5e39). The final write is garbage everywhere (largest in the saturated
  yarn 0 at the inlet row, p −3e72: end stage, not the origin); the onset lies between the 6.5 ms write and 6.548 ms.
  **Before the onset, against job 3051 (REV, same mesh and BCs):** max |U| free cells 7–16 m/s from 0.5 ms, rising
  (3051: 0.8, rare spikes 3–7), porous 3–11 m/s (3051: ~0.2); water-filled free cells 0.5–2.0 m/s (0.75); cells
  |U| > 1 m/s: 318 at 1 ms, 579 at 6.5 ms. **Most fast cells are air** (seen by the user in ParaView, counted
  2026-10-29): of the free cells above 1 m/s, α ≤ 0.01 for 225 of 300 at 1 ms and 372 of 514 at 6.5 ms, about half
  without a yarn neighbour, the others next to partly wet yarn (mean α of the yarn neighbours 0.51 / 0.39). Only the
  fastest few are partly filled cells (α 0.03–0.35, 2–3 yarn faces; 8 of 18 above 5 m/s at 1 ms, 14 of 43 at 6.5
  ms), y 0.27–0.63 mm around crossing yarns 5/6, mirror pairs across x = 0.91 mm. In the truncated REV (study 2c, T0,
  0.5 ms) 34 of the 38 fast air cells lie within 3 cells of the one pumping corner pair: the air stream that feeds
  it (`verification/study2c_nearSaturation/README.md`). In 3059 itself the fast air cells lie within 3 / 6 cells of a
  partly filled free cell with ≥ 2 yarn faces for 142 / 225 of 225 (1 ms), 114 / 176 of 193 (3.5 ms), 278 / 359 of
  372 (6.5 ms); the rest (13–17 cells, 1.0–1.2 m/s, no yarn neighbour) sit in the bottom padding layer next to the
  inlet (z −0.12 mm, y 0.01–0.11 mm), where the gap water spread into the padding (θ 40°): a second, mild group, not
  checked further. Gap water grows 1,645 → 2,611 cell volumes and passes
  the 3051 valve (top 0.25 mm; 3051: drained to ~300, top 0.17 mm); ~530 padding cells wet (3051: 0); lost through
  top/bottom 411 cell volumes by 6.5 ms (3051: 10 by 10 ms); budget closed (imbalance 1.6e-19 m³). y-yarn front
  0.51 / 0.79 / 0.97 mm at 1 / 4 / 6.5 ms (3051: 0.69 / 1.13 / 1.35), mean porous S 0.204 at 6.5 ms (3051: 0.335).
  VG with these inputs: pc lower than REV only above S ≈ 0.04 (S 0.5: 2.5 vs 8.7 kPa; S 0.9: 0.5 vs 2.4 kPa) and
  higher at the dry end (S 0.002: 11 vs 2.5 MPa). Three changes at once (pc0, m, θ 60 → 40°): the cause of the fast
  interface currents cannot be attributed from this run. Not checked: the origin cell of the divergence (needs
  writes between 6.5 and 6.553 ms).
  **Diagnosis (2026-10-29, laptop scratch runs, solver `be1a3ab`, 8 cores):**
  - Restart of 3059 from the 6.5 ms write (6-digit fields): no divergence to 7.2 ms (3,224 steps), dt dips in
    episodes every ~0.12 ms (6.508, 6.639, 6.748, 6.875, 7.000, 7.126 ms; dt down to 1–2e-8 s, all recovered). The
    6.553 ms collapse was one such episode that did not recover; the restart took another path.
  - Locator function object (largest porous |dα/dt| and largest free |U| per step): both episodes of 7.0–7.2 ms sit
    at the flank of yarn 2 (yarn cells x 0.769 mm, y 0.23–0.33, z 0.02–0.08 mm): the surface cells drain from α 0.94
    to 0.76–0.80 in ~4 µs (|dα/dt| up to 9.6e5 1/s), refill between episodes; the free cells beside them (x 0.749 mm)
    α 0.06–0.22 at 20–30 m/s; pure-air free cells up to 59 m/s elsewhere. In the writes the gap
    beside that flank holds a diffuse band of α 0.05–0.6 (4 cells wide, ~8 tall, from y 0.19 mm, growing from 1 ms);
    in 3051 the same cells are air (α ≤ 0.02) and the yarn flank is wetter (α 0.94–0.98 vs 0.83–0.97).
  - Exchange across the 39,406 internal porous/free faces (alphaPhi0): 3059 net yarn → gap +1.1 to +1.8e-9 m³/s
    (outflow faces: yarn S median 0.96–0.97), gross out 2.0–2.6e-8 and in −1.9 to −2.5e-8 m³/s; 3051 net mostly
    gap → yarn, gross ~0.5e-8.
  - One-change variants to 0.5 ms (0.5 ms write; baseline = REV with the current BCs, job 3055):
    REV 0 free cells with |U| > 1 m/s, max 0.77 m/s, gap water 289 cells (3051, old BCs: 0, 0.76, 293);
    `REV_t40` (θ 40° only) 7 cells, max 2.5 m/s (locator: 4–17 m/s spikes per 0.05 ms), gap water 1,004, valve
    holds (0.17 mm); `lowpc_t60` (pc0 1000, m 0.4 only) 56 cells, max 8.5 m/s (rising from 1.4 at 0.1–0.2 ms), gap
    water 395, valve holds; 3059 (both) 155 cells, max 7.9 m/s, gap water 1,228. **The low pc is the main trigger of
    the fast currents; θ 40° keeps more water in the gaps and adds to them.**
  - VG (pc = pc0·(Se^(−1/m) − 1)^(1−m), Se = S/0.999, solver `pcVanGenuchten.H`): the gap meniscus suction
    2σcosθ/w (0.37–0.69 kPa at θ 40°, 300–160 µm) equals the yarn pc at S ≈ 0.84–0.92 here, at S ≈ 0.99–0.997 in
    REV. Fibre-bundle estimate pc ≈ (4/d_f)·V_f/(1 − V_f)·σcosθ (Ahn, Seferis & Berg 1991; d_f 15 µm, V_f 0.5)
    ≈ 19 kPa·cosθ, i.e. 20–40× the gap suction at any θ: REV pc0 5000 Pa is the physical order, REV_lowpc is weaker
    than a fibre bundle at moderate S.
  - Hypothesis (not tested): the porous/free coupling (G pc jump driven by the free-cell pressure of a smeared VOF
    interface, kr on yarn/gap faces from the gap cell α, H on a wet surface) is unstable where a nearly saturated
    yarn (pc ≈ meniscus suction) faces a partly filled gap cell. Scripts and runs: laptop scratchpad (disposable).
- **Tensor K, planned (decided with the user 2026-10-27; solver change not written, plan in `NOTES_solver.md`,
  "Planned: diagonal tensor K"):** yarn-aligned diagonal K (`build_fields.py --k-mode tensor`, `ORIENTATION "axis"`),
  harmonic face values. Gebart with the script's inputs (Vf 0.5, fibre radius 7.5 µm, both to measure; hex): Kpar
  4.2e-12, Kperp 9.2e-13 m², ratio 4.6 (quad: 3.9e-12 / 7.3e-13), both below the current 1e-11. Two studies, one
  change each, pc0 kept at 5000 Pa (Leverett pc0 ∝ √(ε/K) has no single K for a tensor; following it with Kpar would
  give pc0 ×1.5 and a front ×0.81 instead of ×0.65): **(a) anisotropy alone**, Kpar 1e-11, Kperp 1e-11/4.6 = 2.2e-12
  (needs `--k-par`/`--k-perp` in `build_fields.py`); **(b) Gebart magnitudes**. Reference: job 3051 (scalar 1e-11);
  its results stay valid as the isotropic case (the scalar path of the solver stays as it is).
  **Estimates for (b), not run:**
  - yarn front ∝ √K at fixed pc0: ×0.65 (1D 18.0 → 11.7 mm/√s; REV 13.9 → ~9 mm/√s); the same front 2.4× later (~1.1
    mm at 10 ms instead of 1.63, where job 3051 was at ~4 ms);
  - reservoir feed: 665 of the 984 porous inlet faces are in yarn 5 (K_yy = Kperp, ×0.09 of now), 319 in the y-yarns
    (Kpar); the α overshoot of job 3051 sits in yarn 5 at the inlet: effect on it not predictable;
  - warp/weft transfer: 3,221 of the 4,457 contact faces are z-faces with Kperp on both sides (×0.09): yarns 6 and 7
    wet later and draw relatively less water. If the crossing-yarn sink explains REV 13.9 vs 1D 18 mm/√s (hypothesis),
    the REV/1D ratio moves towards 1 (also in (a): a test of that hypothesis);
  - across a yarn's thickness (120 µm): D ≈ K·pc0/(μ·ε) gives ~1.6 ms instead of ~0.14 ms, so the saturation is no
    longer uniform across a yarn during the run (add a thickness profile to `check.py`);
  - gaps: drained by the yarns through porous/free faces at ~2·Knn: slower drain (job 3051: 1,645 → 268 cell volumes
    by 1 ms); the capillary valve at y ≈ 0.18 mm is set by geometry and θ, not by K: expected to hold;
  - dt: the Coats face-K sum of a y-yarn cell 2Kpar + 4Kperp = 0.2× now → Coats dt ×5, then the dSmax limit
    (3.7–6.6e-7 s in job 3051) and capillary waves (1.5e-6 s) take over: dt ×3–5, ~400–650 s per simulated ms on 16
    cores (job 3051: 1,900); with 2.4× the time for the same front, ~1.2–2× cheaper per front distance.
  **Estimates for (a):** y-yarn along-axis rate unchanged; inlet faces of yarn 5, z-contacts and the gap drain through
  x/z yarn faces ×0.22; Coats sum 2·1e-11 + 4·2.2e-12 = 0.48× now → dt ~×2.
- **Cost (laptop, 2026-10-26):** s per step serial 2.18, 4 cores 1.35, 8 cores 1.55 (memory bound; `caseSetup` N 4);
  dt at the Coats limit ~1.2e-7 s after 50 steps.
- **Smoke test, old inlet** (scratch copy, 4 cores, 2026-10-26): **failed at 0.21 ms** (stopGuard, dt 1e-14 s). The dry
  yarns drained the 0.1 mm gap column within 0.1 ms (free water 1,645 → 250 cell volumes; 112 of 290 free inlet cells
  air), air entered through the open top/bottom and left through the reservoir face (9e-8 m³/s), α went to −0.025 in
  air-filled free inlet cells and the Coats limit collapsed dt. Cause: the reservoir inlet let air through →
  **water-only reservoir (solver change J, `be1a3ab`)**, `waterOnlyPatches (inlet); reservoirWaterPressure 0;
  reservoirReferencePoint (0 0 0);` in `constant/transportProperties` since 2026-10-26.
- **Smoke test, water-only inlet** (scratch copy, 4 cores, J, 0.5 ms): past 0.22 ms; at 0.2 ms α in [−6e-20, 1], max
  |U| 0.98 m/s (old 2.85), water cells 0.44 m/s (old 1.73), yarn front (y-yarns, α > 0.1) 0.37 mm, mean porous S 0.105,
  gap water 320 cell volumes (old 142; the column still drains into the yarns, slower), water lost through the open
  top/bottom 1.1 cell volumes (from the initial column spreading into the padding), budget closed to 1e-13. Air
  leaves through top/bottom, none through the inlet. **Reached 0.5 ms** (6,250 s on 4 cores, ~4,000 steps, dt
  1.1–1.3e-7 s): yarn front (y-yarns) 0.17 → 0.51 mm, mean porous S 0.058 → 0.127, gap water 1,645 → 244 cell volumes
  (gap water top 0.15 mm: the gaps barely rise, the yarns drain them), water lost through top/bottom 1.7 cell volumes,
  budget closed to 7e-14, max |U| 0.7–1.0 m/s until 0.45 ms. **Warning signs:** α overshoots above 1 on 132 steps from
  0.26 ms (peak 1.009, back to 1 between episodes; one yarn cell at 1.0004 at 0.5 ms) and at 0.5 ms a local spike of
  4.5 m/s in two gap cells at an interface (y 0.17 mm, next to the x-periodic plane). Needs a longer run (≥ 1 ms) to
  tell whether it grows.
- **Smoke test, saturated rows** (2026-10-26, same as above + `initFields.py --sat-height 1e-4`: yarns at 0.99 over the
  first 0.1 mm, ramp above, gaps full over the same 0.1 mm): reached 0.5 ms (5,790 s, 4 cores), no stopGuard, budget
  closed to 6e-14, max |U| 0.7–1.2 m/s at the writes (brief 1.9–2.2 m/s at 0.25 / 0.4 ms in a gap cell near the
  inlet), no 4.5 m/s spike at 0.5 ms. Yarn front 0.55 mm at 0.5 ms (previous run 0.51), mean porous S 0.136 (0.127),
  gap water 296 cell volumes (244), gap water front 0.15 mm (same: the gaps still do not rise), water lost through
  top/bottom 1.2 cell volumes (1.7). α > 1 on 363 steps (from step 1; peak 1.0017, ≤ 1.0000 at the writes); net water
  out through the inlet early (−2.4e-12 m³ at 0.2 ms, trapped air in the saturated rows), back to inflow by 0.5 ms.
- Before 2026-10-26 the dictionaries were older than `2D_bench` (no H/F′/I keywords, `activatePorousContactAngle 0`, no
  `openFreeTotalPressure`, `timePrecision 6`, no `waterBudget`) and wicking was planned along x.
- Parallel: E, G, F′, I consistent on processor porous/free faces; H fixed there by `0f6c6d4` (`NOTES_solver.md`;
  `verification/parallel_H/`). No porous/free faces on the cyclic planes.

## Reference: Boubaker et al. 2026 (Compos. Part A 206, 109781)
Same solver on a plain-weave E-glass µCT geometry (tows porous, inter-tow space free; K_VOID = 1 m² comes from there).
They replaced MULES by isoAdvector after an unstable porous/free interface; contact angle 90° assigned at the interface;
mild pc (VG pc0 1000 Pa, m 0.8 "for stability": α·pc ~10 Pa vs our ~5 kPa); flow pressure-driven (ΔP 50 kPa), no pure
spontaneous wicking; mould walls top/bottom, cyclic sides; 131 × 101 × 53 µm cells, 4–6 days on 32 cores; tensor K per
tow (diagonal Gebart; data availability statement: data on request, nothing about the solver, checked 2026-10-27). They see artificially fast flow in the free layer near the upper
surface (race-tracking, as our open edge layers could). Post-processing to reuse: x_f² vs t,
K_unsat = (x_f²/t)·μ(1 − Vf)/(2 P_in).

## Literature: solvers for capillary-driven wicking (web search 2026-10-12, mostly abstracts)
No demonstrated solver for **spontaneous** wicking in a dual-scale medium (porous yarns with pc(S) + free gaps) found.
- Micro-continuum DBS two-phase (Soulaine 2018; Carrillo, Bourg & Soulaine 2020; Boubaker et al. 2026): stress
  continuity + contact angle, no capillary jump; their imbibition cases are forced or have K ~1e-20 walls.
- Stokes–Darcy level set, Saint-Étienne (Abouorm, Moulin, Bruchon, Drapier; Cataldi et al. 2023–2026; Pucci, Liotier,
  Drapier 2015 experiments): capillarity as a pressure jump at a sharp front, single fluid.
- Two-phase porous / free-flow coupling theory (Mosthaf et al. 2011, WRR, DuMux): gas pressure continuous at the
  interface = our G condition; sharp-interface domain coupling, gas-only free flow.
- Grey multiphase LBM (Zalzale et al. 2016, PRE 94 053301): capillarity consistent across the interface by construction.
- Pore-scale / pore network for yarns (Empa/ETH: Carmeliet, Fischer; Du et al. 2025): yarn wicking shows filling bursts.
- Single-scale Richards (porousMultiphaseFoam / impesFoam, Horgue; Maier et al. 2025; Masoodi & Pillai); LCM dual-scale
  sink models (Pillai).

## Next steps
**2026-10-30 — START HERE.** L committed in the solver repo (`8a97d02`, docs `97f3b35`), installed on the laptop.
- **REV_lowpc = L validation (decided with the user):** only changes from job 3059: `porousFreeAirKrPorous on` in
  `constant/transportProperties`, `endTime` 10 ms, `caseSetup` N 4 and `job.slurm` `--ntasks=4` (next to the new case on
  mini03), `job.slurm` `--no-requeue`; `run` stops if the binary ignores the keyword; `job_restart.slurm` added (= `REV/`).
  Its submission overwrites the 3059 results on mini03 (local copy `~/PDM_results/REV_lowpc_run3059`).
- **Screening (user: can the solver carry gap water rising significantly? the yarn may lead):** `verification/study2d_gapRise/`,
  cut REV, K 1e-12: S1 VG 5000 / 0.5 θ 40°, S2 θ 30°, S3 VG 1000 / 0.4, S4 θ 20°, S5 column to 0.33 mm; S6 set C with wet yarns. To 1 ms: stable, gap
  top 0.19–0.21 mm, K 1e-12 does not help (results in its README).
- **Measured (`satGap.py`):** in job 3059 the gap top stays between the heights where the y-yarns reach S_eq (yarn pc = gap suction 2σcosθ/w) for w 300 and
  160 µm, at every write to 6.5 ms; the 1D similarity predicts that contour within 0.012 mm; base pc: S_eq never reached, gap top 0.19 mm.
- **Hypothesis (user, not tested):** the gap fills up to the next crossing yarn, a second gap rise starts once the yarns around it are saturated.
- **`REV_gapflow` (decided with the user 2026-10-30): the test of that hypothesis on the full REV.** Set C: K 2e-11 (`Allpre`), VG 500 / 0.4, θ 40°, L,
  `darcyFaceMaxDa` 0.2 (same 39,406 porous/free Darcy faces), 150 ms on 8 cores (weekend run, ~53 h, a write every ms), `job.slurm` continues from the last
  complete write if requeued after a crash. Same K·pc0 as REV_lowpc (yarn front 8.55 mm/√s), lower S_eq.
  **Prediction:** gap top ≈ 0.16 mm + 3.2 mm/√s·√t (S_eq 0.73, w 200 µm): y 0.5 mm at ~11 ms, y 0.84 mm at ~45 ms, y 1.16 mm at ~96 ms or earlier (yarn front
  at the closed end at ~78 ms, the yarns then fill faster). Scratch copy: built by `Allpre`, 15 steps,
  L active, α in [−6e-20, 1]. Check `satGap.py <run> 500 0.4 40` on the writes, water lost through top/bottom (discuss thicker padding above ~10 %).
  **Aim (user):** if the solver can show the phenomenon with tuned values, its absence with real yarn values is a result of the model, not a solver limit
  (still to confirm by experiment). Real yarn pc (estimate 19 kPa·cosθ) ≫ gap suction (0.4–0.7 kPa): S_eq ≥ 0.99, gaps fill only near full yarn saturation.
- **Job 3058 (REV, restart of 3055): stopped by the user 2026-10-30 16:26** (arbitrary values, stability question answered),
  last write 43.5 ms; `processor*/` on mini03, not reconstructed (local copy to 30.5 ms only). **mini03 rebooted again ~11:50
  that day** (uptime 4:36 at 16:26, second crash in 3 days); 3058 and 3060 both started again ~12:24, so SLURM requeues jobs
  after a reboot: harmless for `job_restart.slurm`, but a requeued `job.slurm` reruns `Allpre` and deletes the run, hence
  `--no-requeue` in `REV_lowpc/job.slurm` (restart by hand with `job_restart.slurm`).

**2026-10-29 (end of day): REV_lowpc failure explained, fix K2 chosen and tested.**
- **Mechanism** (`verification/study2c_nearSaturation/README.md`, `NOTES_solver.md` Study 2c): a free cell in a
  concave staircase corner of a yarn surface (3–5 yarn faces; ~4,300 such cells in the REV) collects water when the
  yarn pc is low; surface tension raises its pressure, its Darcy faces let air out into the yarn with the gap cell's
  air mobility (C upwinds kr by each phase's flux), F′ amplifies: an air pump (corner cell 517 Pa, 3–5 m/s), dt-dip
  episodes, and in job 3059 the blow-up at 6.553 ms. Not reproducible on the flat 2D bench (9 configurations);
  reproduced exactly on a truncated REV (first 0.7 mm, 64k cells, ~20 min per 0.5 ms on 4 cores, `makeREVcut.sh`).
- **Fix chosen by the user: K2** (on porous/free Darcy faces the air kr from the porous cell; water kr unchanged;
  scratch binary `hybridPorousInterFoam_K2`, keyword `porousFreeKrAirPorous on`, patch
  `verification/study2c_nearSaturation/solver/K2_porousFreeKrAirPorous.patch`). Passed: cut REV θ 60° (pump no longer
  grows, 1 ms) and **θ 40° = the job 3059 configuration (T12: steady 1.3–1.6 m/s to 2 ms, no step above 5 m/s, gap
  water within 3 % of the unfixed T11 = 3059)**; regressions: 1D bit-identical, slit K 1e-20 U/p/φ bit-identical,
  2D bench identical numbers (all 10 checks); keyword off: bit-identical to `be1a3ab`. Alternative kept in reserve:
  G2b (VOF capillary pressure in free interface cells: removes the pressure build-up, but stiff exchange episodes).
- **Decisions pending (user):** (1) commit K2 in the solver repo: proposed change letter **L** (K clashes with the
  permeability), keyword `porousFreeAirKrPorous` (default off), `CHANGES_of9-port.md` entry with the study's evidence,
  rebuild the installed binary (back up the current one first), push; (2) commit this repo (study folder, notes).
- **Then:** mini03 pull + `wmake` the solver; validation jobs (sbatch): REV_lowpc (θ 40°, as 3059) with K2 past
  6.5 ms (≥ 10 ms); base REV with K2 past 15 ms (the weaker corner pattern of job 3058 from 15 ms, at y 1.2–1.5 mm next
  to yarn 2 / crossing yarn 7) vs job 3058.
- **Still running on mini03:** job 3058 (REV, base pc, restart of 3055 from 11 ms, endTime 50 ms; healthy to 30.5 ms:
  copy `~/PDM_results/REV_run3055_3058`). Fetch and check at the end (`check.py`, the corner pattern after 15 ms).
- **Local files:** results copies in `~/PDM_results/` (REV_run3051, REV_lowpc_run3059, REV_run3055_3058 to 30.5 ms,
  study2c_logs; `tools` symlink for paraFoam); scratch binaries `hybridPorousInterFoam_K1/_K2/_G2/_G2b` in
  `$FOAM_USER_APPBIN` (diagnostic; sources were in the session scratchpad, the patches are in the study's `solver/`;
  delete K1/G2 once K2 is committed).
- **Physics points discussed 2026-10-29 (not tested):** pc0 5000 Pa (m 0.5) is the physical order for the yarn
  (fibre-bundle estimate ≈ 19 kPa·cosθ for d_f 15 µm, V_f 0.5, i.e. 20–40× the gap meniscus suction at any θ);
  REV_lowpc (pc0 1000, m 0.4) is a stress test, not a physical case. With realistic pc the gaps fill behind the yarn
  front (yarns near saturation), in well-connected gaps, and past crossings when θ allows. Characterisation (user's
  next step): the upward–horizontal–downward wicking test (Simile & Beckham) gives fabric-level K–S–pc, i.e. yarns +
  gaps together: use it as validation of the REV, and a yarn-only test (or bundle) for the yarn inputs; θ needs a
  fully wetting reference liquid; H needs the apparent angle on the yarn surface: Young angle (Wilhelmy) on a dry
  surface, Cassie wet-surface angle (≈ 48–54° for θ_Y 70–80°, φ_s 0.5) on a wet one: bracket both in Study 3.

**Earlier entries:**
**State 2026-10-13:** solver `b525086` installed and pushed (mini01: pull, rebuild library and solver); `2D_bench` is the
thick-wall slit with all checks passing; `REV/` prepared up to `Allpre`; 1D and single yarn unchanged with the new solver.
**2026-10-27: job 3051 analysed (REV case status above): runs to 10 ms, valve confirmed, α overshoot grows to 1.05 inside the saturated half yarn 5, not decomposition-related. Next: why porous α > 1 in saturated cells (reservoir-fed yarn 5, J?); decide before longer runs.** **2026-10-27 (later): diagonal tensor K with harmonic faces decided, written down only
(`NOTES_solver.md` "Planned: diagonal tensor K"; REV studies (a)/(b) and estimates in REV case status).**
**2026-10-27 (evening): REV open patches on standard OpenFOAM BCs** (agreed with the user: adapt the setup after
the tests; α 1 = the announced default, kept after `REV_B0`; `verification/standardOpenBC/README.md`): p `totalPressure` 0 on inlet/top/bottom instead of the coded `pOpenAir`, α 1
on all inlet faces (`initFields.py --porous-in 1`), `Uwetting`/`UnonWetting` zeroGradient, the four `pOpenAir`
keywords removed from `transportProperties` (not committed). Measured: top/bottom and phase velocities bit-identical
(bench 2 ms; REV 0.05 ms, 4 cores); inlet: no integral change (REV 0.1 ms: fronts identical, porous S within 1e-4,
water within 0.06 %; bench 2 ms: meniscus and wall front identical; 1D uptake −0.24 %), but the yarn-face inflow of the
inlet moves (REV −16 → −2 % over 0.1 ms, bench −12 % at 2 ms): the yarn faces sit almost in equilibrium with the bath
(net drive 7–30 Pa), so the discrete product term (α_b − α_c)(pc_b − pc_c) of the boundary flux shows (α_b 0.99 with
the standard BC: no closer). Not tested: effect on the α > 1 overshoot inside yarn 5 at the inlet (from ~0.3 ms): watch
it in the next long run (mini03, needs commit, push, pull). Job 3051 used the old BCs; `REV_lowpc/` aligned the
same evening (20-step start checked). Both jobs set to 8 cores (`caseSetup` N 8, `--ntasks=8`) and endTime 50 ms
(5× job 3051; estimate 30–55 h for REV, ~3× less for REV_lowpc; walltime 72 h kept; ~100 writes of ~46 MB each).
Committed and pulled on mini03 (`f2f31f6`); submitted 2026-10-27 evening: **job 3055 (REV) and 3056 (REV_lowpc)**,
pending (node full: 44 of 48 cores taken by other users' jobs, limits 6 d, 15 d and unlimited).
**2026-10-28: mini03 crashed (~15:04) during job 3055 at 11.07 ms; restarted from 11.0 ms as job 3058
(`REV/job_restart.slurm`, running). 3056 (never started) cancelled and resubmitted unchanged as 3059 (REV_lowpc,
fresh start, `job.slurm`); both running on 8 cores the same afternoon.** **2026-10-29: 3059 diverged at 6.553 ms** (fast interface currents at
partly wet yarn surfaces from 0.5 ms, gap water past the valve, water out through top/bottom; REV_lowpc entry). **Diagnosed 2026-10-29: low pc is the main trigger (one-change
variants), θ 40° adds; same pattern, weaker, in the REV run from 15 ms; 3058 healthy to 30.5 ms. Next: isolate the
coupling term on a small case (near-saturated porous wall next to a partly filled gap).**
Previous plan: analyse the 10 ms REV run on mini03 (job 3051): `check.py` table over all writes
(yarn front, gap water, gap rise, |U|, budget, losses); locate the α > 1 cells at the writes near the overshoot peaks
(0.5, 1.0, 1.5 ms: next to the reservoir → boundary water flux of J; next to processor boundaries → decomposition);
short 4- vs 16-core comparison on mini03 if it looks decomposition-related; check the capillary-valve hypothesis (gap
water front stuck at ~0.15 mm = top of the half crossing yarn on the inlet plane). Decide then on longer/production
runs. Git: both repos pushed (thesis `ac70ec3`, solver `c3dbf48`); laptop scratch runs in /tmp are disposable.
**2026-10-26:** review before the REV setup; H found wrong on processor boundaries (fix tested on the bench, not
committed); REV geometry facts measured (above); REV decisions put to the user (open). `verification/PLAN.md` still not run.
1. **Verification: `verification/PLAN.md`, start there** (agreed 2026-10-13, nothing run yet): Study 1 equilibrium
   oscillation (EQ0m-dt first), 2a ablation of G/H/F′/I on the 15-cell slit, 2b face checks (bench, R2), 3 sensitivity
   (θ, K, pc0). Still to schedule after them: static meniscus at 4/8/15 cells (Δp vs 2σcosθ/w), kr variant on yarn/gap
   faces, `porous_Boundary` tutorial original vs E.
2. **REV:** take the decisions above, write `run`/`job.slurm`, local smoke test, then mini01. Before: the H processor fix
   (decision pending); the 3D check of H/F′/I (edges, corners) comes with the REV smoke test.
3. Bench extensions: 15-cell gap (REV median), gaps interrupted by porous crossings (yarn first, then gap: needs an empty
   gap to fill from a wet wall, probably a saturation-dependent θ), θ 75°, 5 ms runs.
4. Later: tensor K (diagonal, harmonic faces: decided 2026-10-27, plan and checks in `NOTES_solver.md`, REV studies
   (a)/(b) in REV case status; not started), real K/pc/θ for polyester; report the impesFoam Todd bug upstream; a swept yarn mesh
   (~100 µm axial cells) for cm-long samples comparable with experiments.
5. Tidy: move the intermediate slit runs (`B_/H_/HF_/I_/J_/N_/R_/V_`) to `slit_test/old_runs/` (proposed, not done);
   delete the obsolete scratch build `hybridPorousInterFoamH`.

## Pitfalls met
- **Check the standard OpenFOAM BCs before coding one** (lesson of 2026-10-27, `verification/standardOpenBC`): the
  REV's coded `pOpenAir` re-implemented `totalPressure` on its free faces (bit-identical), and its yarn-face branch
  existed only because the inlet kept α 0.99 (an impesFoam NaN workaround; the hybrid clips Se): with α 1 at the bath
  `totalPressure` is exact. It grew by accretion and was copied from the 2D bench without review. List the standard
  candidates and the choices of the other fields that make one exact; re-check coded pieces inherited by a new case.
- `foamDictionary -set` rewrites the whole file and strips the comments: edit dictionaries by hand or with sed.
- `timePrecision 6` gives equal time names for ~1e-12 s steps: use 12 for step-by-step writes.
- A `clean` pattern `[0-9].*` also deletes `0.orig`: `clean` matches names made only of digits, `.`, `e`, `+`, `-`.
- The repo-root `.gitignore` ignores time folders (`[1-9]*/`, `0.*/`): exceptions `!1D*/`, `!2D*/`, `!0.orig/`.
- Re-reading a file after editing it in memory dropped a BC (`makeSlit.py --fill`): check the written `0/` fields of a
  generated case, not only the script.
- `postProcess -func writeCellCentres -time 0` without a `0/` folder writes C, Cx, Cy, Cz into `constant/`.
- Never edit a script while background runs read it (two runs died on a half-read `makeVariant.sh`): run from a frozen copy.
- Compiling coded BCs/function objects inside `mpirun` aborts (`MPI_ERR_TRUNCATE`): precompile serially.
- A sed replacement containing the delimiter character (`#`) silently fails: use Python or another delimiter.
- Case copies outside the repo (`~/PDM_results/<case>`): `system/controlDict` includes `../../tools/<functionObject>`,
  so `paraFoam`/`foamListTimes` stop with "Cannot open include file" unless `../../tools` exists: symlink
  `~/PDM_results/tools` → `meshing_strat_trial/tools` (made 2026-10-29, serves every copy at that depth).
