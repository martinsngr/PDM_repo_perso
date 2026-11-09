# Wicking cases — 1D, single yarn, fabric REV

Setups, results and open work of the cases in `trialWicking/` (1D column and single yarn, impesFoam and
hybridPorousInterFoam) and `meshing_strat_trial/` (fabric REV, 2D bench, slit tests). Last updated 2026-11-09.
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
| `meshing_strat_trial/REV_lowpc/` | Copy of `REV/` with VG pc0 1000 Pa, m 0.4 and θ0 40° (2026-10-27); with change L, 4 cores since 2026-10-30: job 3063 reached 10 ms, its continuation job 3067 30 ms (REV case status) |
| `meshing_strat_trial/REV_gapflow/` | Copy of `REV_lowpc` with K 2e-11, VG pc0 500 Pa, m 0.4, θ0 40°, `darcyFaceMaxDa` 0.2, L, 150 ms, 8 cores, **bath plane at y 0.333 mm, mid-gap** (2026-10-30): can the solver show gap water rising behind the yarn saturation? Not physical values. Job 3065 diverged at 1.386 ms; not fixed, not rerun (decision of the user, 2026-11-02) |
| `meshing_strat_trial/REV_midbath/` | `REV` values (K 1e-11, VG pc0 5000 Pa, m 0.5, θ0 60°) with L and the bath plane of `REV_gapflow` (y 0.333 mm, mid-gap), 30 ms, 8 cores (2026-11-02): L past 15 ms at the base pc, bath plane effect, scalar reference for tensor K. Job 3068 reached 30 ms, calm after 1.5 ms (REV case status) |
| `meshing_strat_trial/2D_bench/` | **The 2D bench:** thick-wall slit (yarn wall 8 cells \| gap 8 \| yarn wall 8), G + H + F′ + I on; `Allpre`, `run`, `check.py` |
| `meshing_strat_trial/2D_bench_strip/` | First 2D bench (strip between open free layers), archive: `variants/` (debugging runs, referees R1–R3, `makeVariant.sh`, `ADD=` option) and figures; template of `slit_test/makeSlit.py` |
| `meshing_strat_trial/slit_test/` | Slit capillary-rise tests: `makeSlit.py` (`--walls real/porous`, `--nw`, `--w`, `--K`, `--theta`, `--dx`, `--add`), `slitReport.py`, `benchSlit.py`, `interFoamSlit.sh`, `figures/`, `old_runs/`. Run folders: `S0_*` real walls, `P_*` current porous-wall set, `IF_*` stock interFoam; `B_/H_/HF_/I_/J_/N_/R_/V_` intermediate |
| `verification/` (repo root) | All verification: paper tutorials, 1D similarity solution, ddtCorr bench, inlet test (moved from `trialWicking/verification/` 2026-10-13; results in `NOTES_solver.md`), and **`PLAN.md`: the planned studies 1–3** |
| `meshing_strat_trial/tools/` | `runTools.sh`, `initFields.py`, `pOpenAir` (coded open-patch p BC of the 2D bench and slit cases; `REV/` and `REV_lowpc/` use `totalPressure` since 2026-10-27), function objects `coatsTimeStep`, `liquidBalance`, `waterBudget`, `stopGuard` |
| `REV_pipeline/` (repo root) | **The REV runs from 2026-11-09 on, self-contained:** `geometry/` (`funge.py`, the STL, the REV boxes), `tools/` (copies of every script and function object the cases use; `build_fields.py` with `--stl`/`--domain` and `--wick-axis z`), `cases/` (`tensorA`, `tensorB`, `horizontal`). Target: one main script from the REV inputs to the launched run (its `README.md`) |

## Common setup and rules

- **Properties (setup values, not calibrated):** K 1e-11 m² scalar, ε 0.5, Brooks–Corey n 3, Van Genuchten pc0 5000 Pa
  m 0.5, water/air (μ 1e-3 / 1.76e-5 Pa·s), σ 0.072. pc0 5000 Pa is consistent with K 1e-11 by Leverett scaling (4–8 kPa).
  The wicking rate constrains K·pc0, the equilibrium height (pc0/ρg ≈ 0.5 m) constrains pc0: fitting both needs
  experimental-length samples. Real K (tensor), pc and contact angle (polyester) come later. A change of the kr or pc
  model (not only its coefficients) also needs `tools/coatsTimeStep` changed: `NOTES_solver.md`, open issues.
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
- **anisoImpesFoam on OpenFOAM 9 (found 2026-11-05, `verification/tensorK` check 4):** its wall BC `darcyGradPressureAniso`
  looks `g` up in the Time registry (`db().time().lookupObject`, `darcyGradPressureAniso.C:127`) while the solver registers
  `g` on the mesh (`anisoImpesFoam.C:65`): fatal at the first pressure solve (OF9-port issue of porousMultiphaseFoam; its
  tutorials stop the same way, not run). Without gravity, `symmetry` patches serve as zero-flux walls. A tensor K also needs
  `K linear` (no harmonic interpolation for tensors) and `interpolationSchemes { default linear; }` (tensor Laplacian).
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
**Yarn pc against the gap suction (computed 2026-11-03, solver VG, Se = S/0.999):** pc(S 0.95) = 0.30–0.33·pc0 for m 0.3–0.5
(0.38 at m 0.6), i.e. 1,626 Pa at the REV values, against a gap suction 2σcosθ/w of 240 / 450 Pa (w 300 / 160 µm, θ 60°)
and at most 480 / 900 Pa (θ 0°). Equal at S 0.95 needs pc0 ≈ 740–1,480 Pa (w 300 µm, θ 60–0°) or 1,380–2,770 Pa (160 µm)
at m 0.5 (m 0.4: +8 %); no θ and no m does it at pc0 5000 (that needs gaps narrower than 44 µm at θ 60°, 89 µm at θ 0°).
REV_lowpc (pc0 1000, m 0.4, θ 40°) sits in that range (S_eq 0.93 / 0.84). The fibre-bundle estimate (~19 kPa·cosθ, REV
case status) puts real yarns above pc0 5000, so with real values the yarns win against any open gap until S ≥ 0.99.
**Lowering Smax does not help the gaps (derived 2026-11-04, not run):** the solver's pc and kr take Se = S/Smax (clipped to
[1e-4, 1 − 1e-4]: pc floor 71 Pa at pc0 5000, m 0.5), so with the same Smax in both, the yarn equation in Se is the
present one with ε·Smax: same Se profiles, time ×Smax, front ×1/√Smax, uptake ×√Smax (Smax 0.95: +2.6 % / −2.5 %). The
gap condition (yarn pc ≤ 2σcosθ/w) is a condition on Se (≥ 0.996–0.999 at the REV values) and does not move. Put
otherwise: a lower Smaxpc lowers pc at a fixed S, but S is not fixed; the gap feels the yarn water pressure, which near the
bath is set by the flow the yarn carries (≈ −qμy/K, kr ≈ 1), not by the pc curve, and the yarn settles at a lower S for
the same pressure (3068's bottom row, S 0.97–0.99 at 0.7–1.2 kPa, would sit near S 0.92–0.94 at Smax 0.95). Only the
start changes: rows initialised at S 0.99 would begin at the 71 Pa floor instead of 676 Pa. Smax < 1 is
trapped air (to measure by weighing a wicked yarn), relevant to the uptake, not to the gaps; set in pc
(`alpha.wettingmaxpc`) alone it leaves the air mobile above Smax and lowers the water kr (inconsistent).
**Where an unfed gap can hold water (1D estimate, 2026-11-04, not run):** near the bath kr ≈ 1 and the yarn suction is
pc ≈ (qμ/K + ρg)·y (q inflow Darcy flux, 1D: 6.1 mm/√s ÷ 2√t), so a meniscus beside the yarn survives up to
y ≈ 2σcosθ/w ÷ (qμ/K + ρg): 0.025 / 0.14 / 0.8 / 2.3 mm at 1 ms / 30 ms / 1 s / 10 s for w 300 µm, θ 60° (×1.9 at 160 µm),
i.e. 4–8 % of the yarn front, growing as √t; the gap's own Jurin height (24–46 mm) only once q < ρgK/μ ≈ 1e-4 m/s
(~15 min, yarn front near its equilibrium ~0.5 m). A gap fed by the bath is not bound by this: it can rise while feeding
the yarn flanks (2D bench, base values: meniscus 0.79 mm at 2 ms); study 2e (`B_full`) tests that in the REV. **Not
understood:** in job 3068 the first y-yarn row stayed at S 0.97–0.99 (pc 0.7–1.2 kPa) to 30 ms, while this estimate gives
~7 rows below 240 Pa by 30 ms (REV flux per yarn section ~1.5× the 1D one); candidate: the porous boundary faces of the
bath (Open issues, `NOTES_solver.md`), internal faces in `B_full`.

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
- **Job 3063 (REV_lowpc + L, mini03, 4 cores, solver `8a97d02`, 2026-10-30 16:36 to 2026-10-31 00:47; copy
  `~/PDM_results/REV_lowpc_run3063_3067` since 2026-11-03, with job 3067 to 30 ms; analysed 2026-11-02): reached 10 ms, past the 6.553 ms where job 3059 diverged, no
  stopGuard.** 29,216 s (2,920 s per simulated ms), ~25,800 steps, dt 3.9e-7 s at the Coats limit, no dips after the start in
  the log (every 100th step; 3059: 2.2e-7 s, dips from 5 ms). Budget closed (imbalance 8.8e-22 m³, 9e-12 of the water). α in [−2.5e-20,
  1.0060]; porous α above 1.001 from 2.5 ms, peak 1.006 at ~7 ms, 1.003 at the end (3059 ≤ 1.003).
  - **Same integrals as 3059:** y-yarn front 0.511 / 0.792 / 0.972 mm at 1 / 4 / 6.5 ms (3059: 0.51 / 0.79 / 0.97), mean
    porous S 0.205 at 6.5 ms (0.204), gap water 2,600 cell volumes (2,611), lost through top/bottom 428 (411). At 10 ms:
    front 1.133 mm, S 0.244, crossing yarn 6 mean S 0.44, yarn 7 0.01. Fit t ≥ 2 ms: front = 9.52 mm/√s·√t + 0.19 mm.
    The cut REV T12 matches the full REV at 2 ms (front 0.632 mm in both, gap top 0.231 mm in both, gap water 1,848
    against 1,851).
  - **Gaps:** gap water 2,863 cell volumes at 10 ms, top 0.291 mm; water connected to the bath 2,265 cells, top 0.271
    mm, rows ≥ 20 % connected water up to 0.19 mm: the valve holds. Gap top against the heights where the y-yarns reach
    S_eq (w 300 / 160 µm): 0.211 (0.130 / 0.231), 0.251 (0.231 / 0.311), 0.271 (0.271 / 0.351), 0.291 (0.291 / 0.371) mm
    at 1 / 4 / 6.5 / 10 ms: still between the two, at the lower edge from 6.5 ms.
  - **Water leaving through the open top/bottom:** 731 cell volumes by 10 ms (5.9e-12 m³, 9 % of what entered through the inlet, 64 %
    of it through the bottom), steady ~40 per 0.5 ms from 3 ms; 628 padding cells α > 0.05. Thicker padding not tried.
    Where it leaves (fields at the 10 ms write, 7.2e-10 m³/s, same as the rate in `waterBudget.csv`): 93 % within 0.1 mm of
    the bath, 99.9 % below y 0.3 mm, nothing near the front; 89 % through cells with α < 0.05, none with α > 0.5, on ~830
    faces: traces of water in outgoing air (0.6 % of the outgoing flux), not a body of water reaching the patch. Padding
    holds only 104 cell volumes. Air crosses top/bottom at ±1.2e-7 m³/s, ~30× the air the rising water displaces, mostly
    below y 0.2 mm. REV (job 3055, θ 60°, pc0 5000) at 10 ms: water out 1.7e-12 m³/s (430× less), air ±2e-8 m³/s, padding
    dry. Hypothesis, not tested: air recirculating through the open faces next to the thin 60 µm padding carries the water
    out. Closing top and bottom is not an option: outlet and `inletPad` are closed and the inlet is water-only, so the air
    would have no exit. **Decision pending (user): leave as it is for the tensor K runs (pc0 5000).**
  - **The 3059 currents are gone to 8 ms:** free |U| 1.2–2.5 m/s at the writes (3059: 7–16), cells above 1 m/s 67 / 70
    at 1 / 6.5 ms (318 / 579), porous |U| ≤ 0.37 m/s except 0.91 at 5 ms (3–11).
  - **A local fast current appears from 8.2 ms.** Maximum |U| implied by the log (free Courant·Δx/dt, every 100th step):
    ~2 m/s from 1 to 8.2 ms except one peak of 7.1 m/s at 5.0 ms; bursts of 11–12 m/s from 8.23 ms, steady 7–10 m/s from
    9.3 ms to the end. Writes 9 / 9.5 / 10 ms: free max 10.6 / 7.0 / 7.2 m/s, always the same free cell (x 0.35, y 0.49,
    z 0.10 mm, 1 yarn face, α 0.34 / 0.22 / 0.26, p 1,570 / 919 / 1,152 Pa), right below the yarn 6 cell (0.35, 0.51, 0.10)
    (S 0.45–0.48), the only porous cell above 2 m/s (6.3 / 3.6 / 3.9 m/s). Same spot as the two fastest cells at the 5 ms
    write (x 0.33–0.35, 2.5 m/s). Corner cell (0.37, 0.51, 0.10), 3 yarn faces, 3.5–7.1 m/s. Only 1–3 free cells above
    5 m/s, no effect on dt, α or budget. After 10 ms, the flow direction and whether it is the air pump of study 2c:
    job 3067 below.
  - **Job 3067, continuation to 30 ms (user, started 2026-11-02; `job_restart.slurm` on mini03, same 4-core decomposition,
    ~16 h; `endTime` 0.03 set on mini03 only, the repo keeps 0.01): does the local current stay local?**
    Predictions before the run: reaches 30 ms without stopGuard; the current stays in a few cells, ≤ 20 m/s, more sites
    possible around crossing yarn 7 (y 1.16–1.50 mm) once it wets; y-yarn front ~1.84 mm (fit above); gap top 0.46–0.52 mm
    (S_eq heights extrapolated in √t from 1 and 10 ms); ~2,300 cell volumes lost through top/bottom (40 per 0.5 ms).
    Fails if stopGuard stops it or free |U| stays above 50 m/s (job 3065's level before it diverged). The restart reads
    6-digit fields and takes another path (restart of 3059, 2026-10-29): a current that vanishes right after the restart
    says nothing about stability. `waterBudget.csv` gets a second 0.01 row, inflows restart from 0 there.
    **Result (analysed 2026-11-03, copy `~/PDM_results/REV_lowpc_run3063_3067`, 0–30 ms; log every 100th step from 10 ms;
    scripts: `check.py`, study 2d `connected.py` / `satGap.py`, study 2c `cellFaces.py`, per-ms log statistics and a
    fast-cell locator in the session scratchpad):** reached 30 ms, no stopGuard. 53,630 s (2,680 s per simulated ms),
    ~59,000 steps. dt at the Coats limit on every sampled step, no dips: 3.8–3.9e-7 s to 17 ms, 3.6e-7 at 17–22 ms,
    2.9e-7 at 22.5–28 ms (when the yarn 7 sites below appear; cause not checked), 3.3e-7 at 29–30 ms. α min −1.5e-6 in the
    first steps after the restart (6-digit fields), −1e-19 at the writes; porous α above 1.001 on every sampled step, max
    per ms 1.0036–1.0044 at 10–14 ms, 1.0015–1.0024 after; free α ≤ 1.0006. Budget: restart offset −1.21e-15 m³ (7.8e-6
    of the water), constant from 10.5 to 30 ms.
    - **Yarn 6 site fades:** 7.2 m/s at the 10 ms write; 23 m/s at the first sampled step after the restart (restart
      transient), 7 m/s at 11.7 ms; at the writes the same cell 2.7–6.8 m/s to 13.5 ms, ≤ 2.4 m/s from 14 ms, while yarn 6
      wets (mean S 0.44 → 0.58 at 15 ms). It fades over 4 ms and the same kind of site forms again later, so not a
      restart effect alone.
    - **New sites around crossing yarn 7 from ~22.7 ms, sustained:** maximum |U| implied by the log (all cells) 10.9 m/s at
      22.7 ms, 22.4 at 23.9 ms, 16–19 per ms after, median of the sampled steps 13–19 m/s from 23 ms. Writes 24 / 25 / 27.5
      / 30 ms: free max 10.9 / 13.0 / 13.0 / 16.7 m/s, 22 / 21 / 37 / 34 free cells above 5 m/s in 6 / 6 / ≥ 8 / ≥ 8 sites
      of 1–8 cells (listing capped at 8):
      the row below yarn 7 (y 1.153 mm, from 23 ms), inside its y range at z 0 and 0.14 mm (y 1.333 mm, from 27.5 ms), the
      row above it (y 1.514 mm, the fastest at 28–30 ms); x mirror pairs across x 0.91 mm. The fastest cell of each site:
      free, 1 yarn face (one site 2), α 0.20–0.37, p 700–1,170 Pa, yarn neighbour S 0.21–0.41, except one pure-air cell
      without yarn face (y 1.173 mm, 5.0–5.7 m/s); porous max |U| 8–11 m/s (next to them).
      Yarn 7 mean S 0.17 → 0.28 from 22.5 to 30 ms.
    - **It is the air pump of study 2c** (face fluxes at 27.5 ms, `cellFaces.py`): cell (1.469, 1.153, 0.020) mm, α 0.25,
      p 995 Pa: air enters through its free y− face at 13.2 m/s from a cell at −74 Pa (against the pressure difference)
      and leaves through its one yarn face (y+, yarn S 0.27) at 15.1 m/s; water through that face 0.17 m/s, into the yarn.
      Cell (0.729, 1.333, 0.000) mm: air in through z− at 10.2 m/s, out through the yarn face above at 12.9 m/s. In study
      2c the pump cells had 3–5 yarn faces next to nearly saturated yarn; here 1 yarn face next to yarn at S 0.2–0.4.
      Hypothesis, not tested: L takes the air kr from the porous cell, which is large at S 0.2–0.4, so L does not limit
      this leak.
    - **Integrals:** y-yarn front 1.133 / 1.273 / 1.454 / 1.634 / 1.774 mm at 10 / 15 / 20 / 25 / 30 ms; fit 10–30 ms
      front = 9.39 mm/√s·√t + 0.14 mm (2–10 ms: 9.52). Mean porous S 0.244 → 0.392; crossing yarn 6 mean S 0.44 → 0.75,
      yarn 7 0.01 → 0.28.
    - **Gaps:** gap water 2,863 → 3,828 cell volumes; connected to the bath 2,265 → 2,781 cells, top 0.271 → 0.311 mm,
      rows ≥ 20 % connected water up to 0.19 → 0.21 mm: the valve holds. Gap top (any free box cell α > 0.5) 0.291 → 0.311
      mm to 20 ms, 0.511–0.551 mm from 20.5 ms by isolated pockets (3–10 cells; 122 isolated cells at 30 ms, in the y range
      of yarn 6; not looked at further). S_eq heights (w 300 / 160 µm) 0.291 / 0.371 mm at 10 ms, 0.371 / 0.511 at 30 ms:
      the connected water stays below the 300 µm height.
    - **Lost through top/bottom:** 2,310 cell volumes from 10 to 30 ms (~3,040 in total, 65 % through the bottom), 47 per
      0.5 ms at 10.5 ms, 66 at 22.5 ms, 57 at 26.5 ms; padding cells α > 0.05: 628 → 730–790.
    - **Scoring:** 30 ms without stopGuard: yes. Current stays in a few cells, ≤ 20 m/s: no (the yarn 6 site faded, but 6
      to ≥ 8 sites with 21–37 cells above 5 m/s formed around yarn 7, predicted as possible; sampled max 22.4 m/s, 13–19 m/s
      sustained from 23 ms). Front ~1.84 mm: 1.774 mm (−0.07 mm, −4 %). Gap top 0.46–0.52 mm: no (0.551 mm by isolated
      pockets, connected water 0.311 mm). Lost ~2,300 cell volumes: ~3,040 (+30 %). Failure criteria (stopGuard, free |U|
      staying above 50 m/s): not met. **Stable to 30 ms at pc0 1000 with L, but the air pump is not removed: it moves with
      the wetting of the crossing yarns (yarn 6 at 8–13 ms, yarn 7 from 23 ms) and reaches 10–17 m/s at the writes.**
      Not known: whether it keeps growing after 30 ms (yarn 8 still dry, mean S 0.02).
- **Job 3065 (`REV_gapflow`, mini03, 8 cores, `8a97d02`, 2026-10-31 00:47 to 01:32; copy
  `~/PDM_results/REV_gapflow_run3065`, quick diagnostic 2026-11-02): diverged at 1.386 ms** (stopGuard, dt 4e-28 s;
  2,622 s, ~5,400 steps; 0.49 s per step as estimated). **Not fixed, not rerun (user, 2026-11-02): the setup is not
  physical, and S10 already shows free water moving around closed yarns.** Measured:
  - Maximum |U| implied by the log: 7–10 m/s at 0–0.3 ms, 18–25 at 0.3–0.7, 32–38 at 0.7–1.2, 45–51 after 1.2 ms: the
    current of S11 (17–32 m/s at 0.7–0.93 ms), on the full REV and still growing. dt 2.2–3.2e-7 s to 1.34 ms, 6e-8 s
    at 1.386 ms; in the last ~20 steps dt ×0.83 per step at a free Courant pinned at 0.82–1.04, then the p solves
    diverge (continuity errors 2,719, then 8.5e48), α stays in [0, 1]: the same collapse sequence as job 3059 (there ×0.65
    per step). The 1.386 ms write is garbage (|U| ~1e81 m/s): the origin cell cannot be located from it.
  - Write at 1 ms, the last usable one: 502 free cells above 5 m/s (413 air, 89 partly filled, none water), 95 above 10
    m/s, max 41 m/s; only 161 touch a yarn, 31 have ≥ 3 yarn faces; porous |U| up to 17 m/s (88 cells above 2 m/s). Most
    (332 of 502) at y 0.63–0.93 mm, around crossing yarn 6 up to the y-yarn front (row-mean porous S 0.38 → 0.08); the
    fastest partly filled ones at y 0.76–0.84 mm, 1 yarn face, α 0.05–0.19, p 263–985 Pa, S of the yarn neighbour 0.09–0.29.
  - Water at 1 ms: gap water 4,715 → 1,435 cell volumes, top 0.424 → 0.544 mm (between the S_eq heights 0.484 and
    0.564 mm); connected to the bath 999 cells, rows ≥ 20 % up to 0.343 mm; y-yarn front 0.604 → 0.905 mm, mean porous S
    0.056 → 0.112; net inlet flow −8.6e-12 m³ (~1,080 cell volumes back to the bath), inflow again by 1.386 ms; lost
    through top/bottom 12 cell volumes. Imbalance 1.05e-16 m³ at 1 ms, 2e-6 of the water, 1e5 × job 3063 (not looked at).
  - **Not answered:** the cause. Too short for the question it was built for: the second gap was not reached, so the
    user's second-gap hypothesis stays untested with wicking yarns. Runs side by side: S10 closed yarns, mid-gap ≤ 3.9
    m/s; S6 set C wet yarns, edge bath 5.9 m/s; S11 and 3065 set C dry yarns, mid-gap 32–51 m/s; pc0 1000 with a mid-gap
    bath not run, so K, pc0, `darcyFaceMaxDa` and the bath plane cannot be separated.
- **`REV_midbath/`, job 3068 (mini03, 8 cores, started 2026-11-02; decided with the user the same day): the REV values with L and the bath in the middle of a gap, instead of a closed-yarn full REV** (S10 already covers closed yarns up to y 1.5 mm: its top stops at
  0.892 mm from 2.3 ms, and by 3 ms 19 % of the inlet flow leaves through the open faces, so a longer closed-yarn run would mostly measure that leak; closed yarns cannot feed the far side of a crossing). **Questions:** (1) L past 15 ms at
  the base pc, never run; (2) REV/1D front ratio with this bath plane (edge bath 13.9/18 = 0.78; plan item 3); (3) does this bath plane alone trigger the currents of S11 and job 3065; (4) scalar reference for
  tensor K (job 3051 has the edge bath and no L). **Changes from `REV`:** `rev_domain.json` (y 0.333–3.0 mm; porous 78,489, free 163,571, inlet 330 porous + 944 free faces), `porousFreeAirKrPorous on`, the L check in `run`,
  `endTime` 30 ms, job names, restart logic in `job.slurm` (as `REV_gapflow`). Scratch copy (installed `8a97d02`, 4 cores, 1e-5 s, 90 steps): counts and checkMesh OK, J and L active, all 39,115 porous/free faces are Darcy
  faces, dt 1.22e-7 s at the Coats limit, α in [−1e-19, 1.002], budget closed to 5e-24 m³, 4,715 free cells of water at the start.
  **Predictions before the run (estimates):**
  - Stability: 30 ms without stopGuard; dt 1.2–1.3e-7 s at the Coats limit; free |U| ≤ 3 m/s at the writes after 1 ms (job 3058, no L: 3.5 / 4.8 m/s at 15 / 20 ms), single-write spikes up to 10 m/s accepted (job 3051: 7.3); no sustained current above 5 m/s in the slots around yarn 6 (S11: 17–32 m/s).
  - α: max per ms ≤ 1.02 (job 3055: 1.02–1.09 to 11 ms, in the half yarn 5 at the inlet, not in this domain).
  - y-yarn front: fit t ≥ 2 ms 12–16 mm/√s (edge bath 13.9, 1D 18). Closed end (y 3.0 mm) at 25–35 ms, so it may not be reached by 30 ms (job 3058: 25–30 ms).
  - Gaps: ≤ 1,500 cell volumes at 1 ms (edge bath drains to 16 %, here 770), ~1,300 at 10 ms within a factor 2 (edge bath 394, × 944/290 free inlet faces); water connected to the bath below y 0.55 mm to 15 ms, rows ≥ 20 % below y 0.45 mm.
  - Lost through top/bottom ≤ 100 cell volumes by 30 ms (REV 12).
  **Reading:** calm = this bath plane alone does not trigger the currents of job 3065, which then come from K and pc0 (`darcyFaceMaxDa` 0.2 not separated). S11-type current = the bath plane matters, to settle before tensor K uses it. Fit within ±10 % of 13.9 mm/√s = the REV/1D ratio barely depends on the inlet plane; otherwise it is a setup dependence that the weave factor has to carry.
  **Result (analysed 2026-11-03, copy `~/PDM_results/REV_midbath_run3068`, same scripts as job 3067): reached 30 ms, calm after 1.5 ms.**
  - Run: no stopGuard, 103,320 s on 8 cores (3,440 s per simulated ms; job 3055 4,390), ~243,000 steps. dt 1.25e-7 s at the Coats limit (1.14–1.2e-7 at 11–16 ms), below 5e-8 s only in the
    first ms (0.3 % of the sampled steps). α in [−1.1e-17, 1.0017]: above 1.001 only in the first ms (2.4 % of the sampled steps), ≤ 1 after; porous max 0.9959 at the writes. No overshoot:
    the one of jobs 3051/3055 sat in the half yarn 5 at the inlet, which this domain does not contain. Budget: one-time −8.6e-18 m³ (1e-3 cell volume, 4e-8 of the water) in the first
    0.5 ms, constant after.
  - Velocity: free max 15.0 / 7.0 / 1.6 m/s at the 0.5 / 1 / 1.5 ms writes, ≤ 1.1 m/s from 2 ms, 0.75–0.89 m/s from 4.5 ms (mostly in the bath row, y 0.34 mm), no free cell above 1 m/s at 29.5
    and 30 ms; implied by the log (all cells): 15 m/s at 0.5 ms, 5 m/s at 1 ms, ≤ 1.4 m/s from 2 ms. The 0.5 ms transient: 47 free cells above 3 m/s, mostly in an x mirror pair of sites
    in the row below crossing yarn 6 (y 0.484 mm, z 0.08 mm), fastest 15 m/s, 1 yarn face, α 0.36, p 1.9 kPa, yarn S 0.46: the signature of the job 3067 pump sites; gone by 1.5 ms,
    while the gap column drained.
  - Front: y-yarn front 0.604 mm (initial) → 0.865 / 0.985 / 1.185 / 1.526 / 1.947 / 2.288 / 2.549 / 2.749 mm at 0.5 / 1 / 2 / 5 / 10 / 15 / 20 / 25 ms, the closed end (last row,
    2.990 mm) at 28 ms. Fit 2–10 ms front = 14.35 mm/√s·√t + 0.52 mm (2–20 ms 14.44, 2–25 ms 14.15): +3 % against the edge bath (job 3051, 2–10 ms, 13.9), 0.80 of the 1D 18.04. Mean
    porous S 0.056 → 0.404 (10 ms) → 0.684 (30 ms); crossing yarn 6 mean S 0.92 at 5 ms, 0.98 from 25 ms; yarn 7 0.21 / 0.58 / 0.87 at 5 / 10 / 30 ms; yarn 8 0.63 at 30 ms; min
    porous α rises from 24 ms (0.175 at 30 ms).
  - **Gaps: drained, then cut off from the bath by J.** Gap water 4,715 → 373 / 179 / 96 cell volumes at 0.5 / 1 / 2 ms, 81–98 to 30 ms; water connected to the bath 17 cells from 1 ms
    (bath row only, top 0.343 mm), no row ≥ 20 % water; 9–18 isolated cells up to 0.72–0.80 mm. The dry yarns drained the initial column through the free inlet cells: 54 / 17 of the
    944 free inlet cells at α > 0.5 at 0.5 / 1 ms, 17 to 30 ms (mean α of those cells 0.024–0.025 from 5 ms). J closes a free reservoir face while its cell is air-rich (α < 0.5), so
    927 of the 944 faces stay closed and the gaps get no water from the bath (open issue in `NOTES_solver.md`: a drained free reservoir face does not refill). Job 3051 (edge bath)
    the same: 9 of 290 free inlet cells water from 0.5 to 10 ms. The yarns are fed through the 330 porous inlet faces (inlet-row S 0.97–0.99): 90–92 % of the bath inflow at every write
    (`phi`/`alphaPhi0.wetting` on the inlet patch: 1.6e-8 m³/s at 1 ms, 3.2e-9 at 30 ms), the 17 free cells that never drained the other 8–10 %, the 927 closed faces nothing. At the base pc S_eq is 0.995–0.998
    (w 300 / 160 µm, θ 60°) and the y-yarn row-mean S is below it from the first row at every write, so the gaps next to the yarns would drain anyway; whether a refilling free face
    changes the gap water or the yarn feed: not tested.
  - Lost through top/bottom 11 cell volumes by 30 ms (2.5 by 0.5 ms, from the initial column); padding dry (no cell α > 0.05).
  - **Scoring:** 30 ms without stopGuard: yes. dt 1.2–1.3e-7 s at the Coats limit: yes (1.14–1.26e-7). Free |U| ≤ 3 m/s at the writes after 1 ms: yes from 1.5 ms (7.0 m/s at the 1 ms
    write, within the accepted single-write spikes). No sustained current above 5 m/s around yarn 6: yes (transient to 1 ms). α ≤ 1.02 per ms: yes (1.0017). Front fit 12–16 mm/√s:
    yes (14.35). Closed end at 25–35 ms: yes (28 ms). Gaps ≤ 1,500 cell volumes at 1 ms: yes (179); ~1,300 at 10 ms within a factor 2: no (81, 16× less: the J cut-off above);
    connected water below 0.55 mm and rows ≥ 20 % below 0.45 mm to 15 ms: yes (trivially). Lost ≤ 100 cell volumes: yes (11).
  - **Answers:** (1) L past 15 ms at the base pc: calm to 30 ms, no corner pattern (job 3058, edge bath, no L: 3.5 / 4.8 m/s at 15 / 20 ms next to yarn 7), but the bath plane differs and
    the gaps hold almost no water here: not attributed to L. (2) Front: 14.35 against 13.9 mm/√s (+3 %, within ±10 %): the REV/1D ratio barely depends on the inlet plane (0.78–0.80),
    with the gaps cut off from the bath in both runs. (3) This bath plane alone does not trigger the currents of S11 and job 3065: only a 1 ms transient at the same place below
    yarn 6 while the gap column drains; those currents then come from set C (K 2e-11, VG 500 / 0.4, θ 40°, `darcyFaceMaxDa` 0.2; not separated). Hypothesis, not tested: the pump
    sites need partly filled free cells next to a crossing yarn at S 0.2–0.5; at the base pc the gaps drain within 1.5 ms and the sites die, with set C or pc0 1000 the gaps keep water
    and the sites persist (job 3067). (4) Scalar reference for tensor K: this run (scalar 1e-11, mid-gap bath, L, 30 ms).
- **Study 2e, `B_full` (job 3072, `verification/study2e_bathLayer/`, mini03 16 cores, 2026-11-03/04, analysed 2026-11-04; copy
  `~/PDM_results/study2e_B_full`): job 3068 with 5 rows of bath water below the plane.** Reached 30 ms, no stopGuard, 2,330 s per
  simulated ms, dt at the Coats limit, α ≤ 1.0041, budget closed. **The gaps at the bath stay wet:** all 944 free cells of the
  first fabric row water at every write (job 3068: 17), gap water ~12,000 cell volumes from 5 ms (81–98), the first gap and the
  slots around crossing yarn 6 full (rows ≥ 50 % water up to 0.70 mm), connected top 0.865 mm at 30 ms (the opening above yarn
  6, as S10): J's face closure was the cause of the dry gaps. **But the run leaks:** the layer also runs under the padding, the
  padding fills with water up to y ~0.7 mm along the fabric's outer faces and pours out through the open top/bottom faces,
  ~8e-8 m³/s from 3 ms, 283,700 cell volumes by 30 ms = 86 % of the inflow (design error of the study). y-yarn front fit
  15.65 / 15.28 mm/√s (2–10 / 2–20 ms; job 3068 14.36 / 14.44), closed end at 22.5 ms (28), yarn water 1.17–1.36 × job 3068: the
  gap feed and the padding feed are not separable. The yarn 6 pump transient: 12–15 m/s at 0.20–0.35 ms in a partly filled
  cell, gone once the gap filled (water-filled cells do not pump). Scoring P1–P6 and details in the study README.
- **Study 2e, `Bbox_full` (job 3078, mini03 16 cores, 2026-11-04 16:46 to 2026-11-05 13:01, analysed 2026-11-05; copy
  `~/PDM_results/study2e_Bbox_full`, its five includes pointed at the study's `tools/`): the bath under the fabric box only
  (option 1).** Reached 30 ms, no stopGuard, 2,400 s per simulated ms, dt 1.25e-7 s at the Coats limit, α ≤ 1.0074, budget closed
  (one-time 4.4e-17 m³ at the start). **The leak returns from 8 ms (R1 failed):** lost through top/bottom 44 / 468 / 7,797 /
  59,426 cell volumes at 3 / 10 / 20 / 30 ms (job 3068: 11 by 30 ms). To ~15 ms traces in outgoing air within 0.1 mm of the
  plane (as job 3063). The two outermost box layers (z layers 3 and 16: 94–97 % free, no yarn cell below y 0.58 mm, nothing
  between them and the padding) held the bath surface to 7.5 ms (their 182 first-row cells air), flooded at 8 ms; from ~17 ms
  the bottom padding fills up to y0 + 0.3 mm over the whole width and pours out through the open bottom faces, 80–96 % of the
  inflow from 23 ms. **The gaps are fed through a loop** (face fluxes `alphaPhi0.wetting`): water rises through the plane faces
  under the outer layers' bath-surface cells (α 0.4–0.6, ~0.27 m/s, 1,300–1,800 cell volumes per ms), goes sideways into the
  inner gaps and partly back down into the bath through the inner plane faces (net down at 1, 5 and 7.5 ms). Hypothesis, not
  tested: a parasitic surface-tension current at the bath surface under the outer layers; its down branch matches the air that
  collects at an x mirror pair of spots in the inlet row (min α 0.28–0.50 from 5 ms; J closes 17–21 inlet faces from 15 ms).
  Gaps: inner first row (layers 4–15) water from 1 ms, the outer 182 cells from 8 ms; gap water 1,786 / 6,893 / 9,601 cell
  volumes at 1 / 10 / 30 ms (`B_full` 5,890 / 12,271 / 12,484; job 3068 179 / 81 / 98); connected top 0.865 mm at 30 ms. Yarns:
  front = job 3068 to 2 ms, fit 15.05 / 15.32 mm/√s (2–10 / 2–20 ms; job 3068 14.36 / 14.44), closed end 25.5 ms (28); porous
  water 1.065 × job 3068 at 2–5 ms, 1.099 from 13 ms: not attributable (the gaps are fed by the loop). **A fast current at the
  base pc, 15–20 ms** (6–9 m/s at the writes, 11.9 m/s in the log; job 3068 ≤ 0.8 m/s then): the air-pump pattern (free cell α
  0.15, p 330–400 Pa, 2 faces on y-yarn 1 at S 0.22–0.45, its pure-air neighbour fast), x mirror sites at y 2.13–2.21 mm around
  crossing yarn 8 while the front passes; cause not known. Scoring (Q1 passed at 3 ms; Q2, Q4, R1, R2 failed; Q3 at job 3068's
  value; R3 front at `B_full`'s value) and details in the study README; scripts `compare3068.py`, `leakFaces.py` there.
- **Study 2e option 2: the bath under the yarn band only (decided with the user 2026-11-05, after a step back over all the bath
  findings; design, checks and predictions S1–S6 / R1–R4 in the study README).** At the bath plane the 944 free first-row cells
  are 307 in the yarn band (z layers 6–12, between the y-yarns: confined in x) and 637 in the open space above and below the
  yarns (layers 3–5 and 13–16: one yarn side, the padding and open air on the other). In job 3068 the open space drained first
  (637 → 7 cells water by 0.5 ms), the band later (307 → 47 / 10 at 0.5 / 1 ms); the 2D bench (walls on both sides) kept its
  water at a J inlet. Hypothesis: a bath-fed gap keeps its water where it is confined; the open space beside the yarns holds no
  meniscus and, fed by the bath, carries water to the open faces. Mode `band` of `buildCase.sh`: the 5 bath rows only under the
  band (3,185 cells, inlet 637 faces); the open space and the padding on a closed floor at y0 and dry at the start (job 3068's
  3,103 cell volumes of initial water there removed); the band keeps its column (1,612 cell volumes); everything else as
  `Bbox`. Graded padding option (`PAD_GRADED`, `build_mesh.py --pad`: 10 layers from 20 µm growing ×1.3, 0.86 mm per side, 1.7×
  the cells; first padding cell 20 µm, so the box surface keeps uniform faces). Set aside in the discussion: no J with α 1 on the
  inlet (a drained free inlet cell vents air, or α fixed at 1 refills it with the slit kick, 6×, 23 m/s); closing the lower part
  of top/bottom (the 60–120 µm space beside the fabric becomes a slit of 300–600 Pa at a 90° wall, as strong as the gaps; a 120°
  wall is neutral only on a knife edge, ±5° = ±4.7 mm of Jurin height); α held at 1 in the first band rows (code, not
  conservative); the through-thickness set-up (no boundary problem but no in-plane front; useful later for the coupling and the
  equilibrium uptake). Checks (laptop): the three cases pass checkMesh; above the plane the fields equal job 3068's except the
  dry open space; smoke tests 30 steps (J, L, Coats dt 1.23e-7 s, α ≤ 1.0006, imbalance ≤ 7e-23 m³), `BbandP_cut` 10 steps on 4
  ranks; `Bbox_full` rebuilt with the changed script byte-identical to job 3078's mesh and 0/; ~1 GB per 4-rank job (6G
  requested: mini03 was memory-bound, a comsol job pending on 50G). **Submitted on mini03 the evening of 2026-11-05: job 3090
  `Bband_cut` (108,745 cells, 12 ms, 4 cores, estimate ~11 h) and job 3091 `BbandP_cut` (graded padding, 182,637 cells, 12 ms,
  4 cores, ~18 h), both running.** Solver: `4bb5d2e` (T), so that the scalar reference and the tensor runs share one binary
  (scalar path bit-identical to `8a97d02`): pulled and built on mini03 by the user before the submission (confirmed: repo at
  `11d060b`, the docs commit on `4bb5d2e`; binary rebuilt 15:28, previous one kept as `hybridPorousInterFoam_8a97d02` 15:26;
  job 3090 started 15:32, job 3091 later). Job 3090
  (started 15:32) built the case on mini03 exactly as on the laptop (band z −1.007e-05 to 1.309e-04 m, 3,103 cell volumes
  removed, 1,612 kept, 3,185 bath cells, 108,745 cells, same patch faces). `Bband_full` (245,245 cells, 30 ms, 16 cores) built and smoke-tested, waits for the cut results.
  **`Bband_cut` result (job 3090, ended 2026-11-06 01:14, analysed the same day; copy `~/PDM_results/study2e_Bband_cut`; scoring in the
  study README): no leak, but the band gaps do not stay wet.** Lost through top/bottom 3.9 cell volumes by 12 ms, open space beside
  the yarns ≤ 46, padding dry, no loop (the plane faces under the band gaps carry water net up at every write from 0.5 ms). The
  initial band column collapsed within 0.25 ms (water and air from the open space went down into the bath, net back-flow through the
  inlet); from 0.5 ms every bath cell under the band gaps is water while 194–236 of the 307 first-row gap cells above are air: **the
  menisci sit on the bath plane faces**; band gap water 290–498 cell volumes from 1 ms (job 3068 ~50, `Bbox_full` 970–3,234). First-row
  band yarns at S 0.96–0.99 (pc 0.7–1.4 kPa) against a gap suction of 240–450 Pa. Hypothesis, not tested: the yarn flanks drain the gaps
  down to the plane, and a flat interface lying on a face (no interface cell) feels neither curvature nor H, so the bath cannot push it
  back up (the slit tests' empty gap above an inlet). The band's outer layers are mostly open (first row: layers 6 / 7 / 11 / 12 87 /
  51 / 42 / 59 % free); even layers 8–10 keep only 4–21 of 28–32 first-row cells wet. Yarns one row behind job 3068 to 3 ms, porous
  water 0.94–0.99 × (job 3068's yarns also took the initial water the band case removes from the open space). Air in the inlet row
  (J holds those cells at α 0.5; α overshoot to 1.047 there at 4.5 ms). `BbandP_cut` (job 3091, graded padding) = `Bband_cut` (Next
  steps, 2026-11-06).
- **Study 2e option 3, `BfullP_cut` (job 1600, mini01 12 cores, `4bb5d2e`, 2026-11-06 10:43 to 2026-11-07 00:34; copy
  `~/PDM_results/study2e_BfullP_cut`, analysed 2026-11-09; scoring F1–F6 and details in the study README): the bath under everything
  with the wide graded padding (12 layers ×1.5, 5.19 mm per side), `inletPad` open and water-only, inlet p0 0.9836 Pa. Reached 12 ms,
  no stopGuard, budget closed (one-time 4.6e-17 m³). **The gaps at the bath stay wet (F2 passes) and the whole cut floods:** band first
  row 307/307 at every write, band gap water 3,140 at 1 ms (`Bbox_full` 970, `Bband_cut` 290), all box free cells water by 7.25 ms,
  yarns full from ~6 ms; the band gaps rise with the outer water body (≥ 50 % water up to 0.23 / 0.45 / 0.83 / 1.15 mm above the plane
  at 1 / 2 / 5 / 6 ms, padding next to the box 0.15 / 0.39 / 0.77 / 0.97 mm): not separable which lifts which. y-yarn front 1.005 /
  1.306 mm at 1 / 2 ms, closed end at 2.75 ms (job 3068: 5.0 ms), porous water 1.35–1.41 × job 3068 at 1–3 ms. **But the outer bath is
  not controlled (F1 fails):** the outer meniscus climbs to the closed outlet (cut 1.163 mm above the plane, static meniscus ~1.4 mm at
  θ 60°) by 7.25 ms and spreads ~0.6 mm out under it (0.9 million cell volumes in the padding against ~55,000 in the fabric), then
  drains back from ~10 ms, through the fabric into the bath (plane faces net down at 10–12 ms; F4 fails from 10 ms); the far bath
  (0.1 mm deep, ~1 Pa hydrostatic margin) flows out through `inletPad` from 0.5 ms and is empty under the outermost padding layer by
  4 ms (layers 10–11 by 10–12 ms), and J keeps those faces closed; air then recirculates through the far open faces at 15–30 m/s,
  water leaves as traces in that air: 4,633 cell volumes by 12 ms (fail ≥ 1,000), and the p solve takes 220–540 GAMG iterations per
  step from 4–5 ms (0 before), ~4,300 s per simulated ms (2,200 before). Hypothesis, not tested: small air pressures over the far bath
  (−5 to +18 Pa, from the air the rising water displaces) empty it.
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
**Plan to the first yarn characterization (~2026-11-20; agreed with the user 2026-10-30), in this order:** (1) read REV_lowpc + L and `REV_gapflow` (done 2026-11-02); (2) tensor K, solver change and the 6 checks
(`NOTES_solver.md`, start Monday 2026-11-02); (3) weave factor (REV front ÷ 1D yarn front, 0.78 so far): vary K, wick along x, shift the inlet plane, other weaves and densities (STLs from the user,
`funge.py`); (4) mesh check, same REV at 15 µm; (5) yarn-only REV against the hybrid; (6) 1D model with gravity, script from measured geometry to a REV case; (7) freeze the solver version before
the data, for a blind first prediction. Left out unless the gaps turn out to matter: G2b, 10 µm, gap tuning, `verification/PLAN.md` Studies 1, 2a, 2b. Cores: about 8–10 usable on mini03 (cap 46), the user
expects more in the coming days and can also use mini01. Test planned: vertical wicking, front and uptake vs time, same yarn in different weaves and densities, then other yarns.

**2026-11-09 (later): `REV_pipeline/` set up (decided with the user).** New self-contained folder at the repo root (layout, tool
provenance, checks, predictions in its `README.md`); the user's target is one main script from the REV inputs (weave → STL → case
from a reference → mesh → fields → set-up → launch), not written yet (open point: TexGen's Python is only inside the Windows GUI).
Three cases built and checked on the laptop: **`tensorA`** (job 3068 with K diag, Kpar 1e-11, Kperp 2.2e-12: study (a)) and
**`tensorB`** (Gebart Kpar 4.245e-12, Kperp 9.20e-13: study (b), 60 ms), both on job 3068's mesh, fields and BCs (byte-identical
except K), to run side by side on mini03 (8 cores each; user); **`horizontal`**: the previous student's set-up with our model
(fabric lying flat on a bath at rest, water rising through the thickness, x and y cyclic, gravity −z, θ 40° her value; user's
choices: bath at rest, g −z, θ 40°), 16 cores, 5 ms. Smoke tests: tensor cases dt 2.74e-7 / 6.41e-7 s at the Coats limit (×2.2 /
×5.1 job 3068), tensor K read and guarded; horizontal: stiff start (dSmax-limited dt while the dry yarn crests take up bath water).
**Horizontal smoke test failed (600 steps, 4 cores): stopGuard at step 350, t = 31 µs** (dt 8.8e-15 s; α ≤ 1.0001, budget closed).
Diagnosis (rerun with `dsLocator` and writes every 20 steps, face fluxes across the bath surface): **the dry yarn crests vent their
air down into the bath water** through the 747 crest contact faces (porous/free G faces, air mobility of the dry yarn, nothing
against air entering a water-filled free cell), 18–41 cell volumes per µs from 1 µs, and 5–19 per µs more through the faces under the
gaps; the bath cannot vent it (J at its bottom passes no air): bath air 373 → 1,684 cell volumes by 31 µs, all 747 bath cells under
the crests α < 0.5 by 5 µs, the crests' water uptake then ~0 from 8 µs (the bath feeds only the gaps, +18 → +83 per µs). A partly filled
bath cell under a crest (α 0.24 → 0.10) runs away: 6 m/s at step 160, 25 at 240, 750 at 276, 9e4 at 300 (study 2c pump pattern), then
dt collapses. The vertical cases avoid it by construction (the yarns touch the bath only through J boundary faces, saturated rows at the
bath). Hypothesis, not tested: the same leak (dry yarn next to water-filled free cells) behind the currents of study 2d S5/S11 and job
3065. Test with the 747 crest cells at S 0.99 (369 cell volumes): 300 steps (18 µs) without stopGuard, but not a fix: the crest venting
drops (7–15 per µs) while air now enters through the faces under the gaps (19–125 per µs: water rising into the first fabric layer
swaps with its air across the flat bath surface); bath air 1,188 cell volumes by 18 µs, 565 of 747 bath cells under crests α < 0.5,
13–26 m/s for 100+ steps. **Horizontal case on hold** (`REV_pipeline/README.md`; its `job.slurm` stops at its first line): two air
leaks into a bath that cannot vent; options (a bath that lets air out, a solver change for the first leak, the waterline inside a
submerged fabric layer) to study later with predictions.
**anisoImpesFoam: only as a cross-check (user, 2026-11-09)**: a yarn-only REV (`tensorA`'s yarns, gaps removed) against `tensorA`
(plan item 5), g = 0 (its gravity-aware wall BC fails on OF9; symmetry walls are exact without gravity), far end open to air, μ_air
×1 and ÷100 (air venting route), bath water at 0 Pa as `tensorA`. Not built yet.

**2026-11-09: `BfullP_cut` (job 1600) fetched from mini01 and analysed** (REV case status, study 2e option 3; README scoring): gaps at the
bath wet and the cut flooded by 7 ms (F2 passes), but the outer bath is not controlled (F1 fails: far bath emptied through `inletPad`
and J-closed, outer meniscus up to the closed outlet and back, air recirculating at 15–30 m/s through the far open faces, 4,633 cell
volumes lost). Four bath set-ups now show that wet gaps at the bath need water beside the fabric, and every version of that so far
leaks or sloshes on this domain; the 1.163 mm cut is shorter than the outer meniscus. **Decided with the user 2026-11-09: the bath
line (study 2e) is closed; the tensor K runs use the job 3068 set-up (mid-gap bath, J) with job 3068 as the scalar reference.**
Reasons: the yarns lead in every run; fully wet gaps at the bath (`B_full`) shift the y-yarn front by a constant 0.24 mm (0.02 / 0.10 /
0.16 / 0.20 / 0.22 / 0.24 / 0.24 mm at 1 / 2 / 3 / 5 / 10 / 15 / 20 ms; both fronts advance 0.26 mm from 15 to 20 ms), an offset, not
a rate; every bath that kept the gaps wet also leaked or sloshed; a fabric continued below the waterline with walls beside it is
`Bbox` / job 3068 with a deeper wet layer (study 2d S5's deeper column retracted), water around it is `BfullP_cut`. Known
limitation of the set-up: dry gaps at the waterline (J closes the drained free bath faces; a VOF meniscus cannot sit on a boundary
face), front offset ≤ 0.24 mm, but the uptake is underestimated if a test weighs at long times (gaps near the bath can fill once the
yarn flux drops, Jurin 24–46 mm). The gaps will matter for the horizontal set-up (user). Fit fronts with a free offset (front = k√t + c).

**2026-11-06:** `Bband_cut` (job 3090) analysed: no leak, but the band gaps' menisci sit on the bath plane (REV case status, study 2e
option 2); S1 failed, S2/S3 passed. `BbandP_cut` (job 3091, ended 10:00, copy `~/PDM_results/study2e_BbandP_cut`): = `Bband_cut` within 0.1 % (front, yarn water) and 1–7 % (band gap water), lost through top/bottom 0.01 against 3.9 cell volumes: the graded padding changes nothing near the fabric, and the traces of water carried out by air need open faces close to the fabric (job 3063 hypothesis supported).
**Decided with the user 2026-11-06: option 3, the bath under everything (as `B_full`) with a wide graded padding** (12 layers ×1.5,
5.19 mm per side), the whole bath bottom fed (`inletPad` open and water-only), inlet total pressure 0.9836 Pa (water at 0 Pa at
the bath plane: the solver solves the full p, gravity as a body force, `pEqn.H:31`). Reason: the gaps at the bath stayed wet only
where the bath also reached the open space beside the yarns (`B_full`, `Bbox_full`), as in a real dip; `B_full` leaked only because
its padding is 60 µm. `BfullP_cut` (217,854 cells, 12 ms, 12 cores) built, checked and smoke-tested; design, checks and predictions
F1–F6 in the study README. **Running on mini01 (mini03 full): job 1600, 12 cores, started 2026-11-06 10:43** (mini01 brought up
to date the same morning: solver pulled from `c3dbf48` to `11d060b` and rebuilt, thesis repo pulled from `f2f31f6`; confirmed: solver repo
at `11d060b`, binary rebuilt 10:40 (1,785,848 bytes, as mini03's `4bb5d2e` build; previous one kept as
`hybridPorousInterFoam_old`, 1,747,520 bytes, the size of the `be1a3ab` build), job log `B: 217,854
cells, 5 layer rows (17,290 cells, water)` as on the laptop; mini01 repo `.venv` OK, trimesh
5.1.0 with embreex; partition `global`, cap 46). Measured: 1 ms in 2,253 s of solver time (as mini03), end expected ~18:00–18:30 the same day. Set aside: `Bbox` + wide padding (keeps the loop corner),
top/bottom cyclic (user: changes the whole set-up), the band bath with yarns continued below the plane (would likely end as
`Bband_cut`). If the bath line needs it later, the REV can be lengthened (y planes periodic; cost ~L³).

**2026-11-05, evening.** (1) **Check jobs 3090 (`Bband_cut`) and 3091 (`BbandP_cut`) on mini03** (REV case status,
study 2e option 2; both run the T build, `4bb5d2e`, confirmed 2026-11-05): fetch into
`~/PDM_results/study2e_Bband_cut` / `study2e_BbandP_cut` and point the five includes at the study's `tools/` (commands at the end
of the study README), run `compare3068.py` (band columns), `leakFaces.py`, `../study2d_gapRise/connected.py`, score S1–S6.
(2) **Decide with the user** from the README's reading table: `Bband_full` (3-layer padding) if S1 and S2 pass in `Bband_cut`; a
full run with the graded padding (spec to add in `makeCases.sh`) if only `BbandP_cut` passes S2; rethink if both leak or the
band drains although fed. (3) Then the REV tensor K runs (a), (b), which waited for the bath set-up; the chosen full band run is
their scalar reference. Open from `Bbox_full`: the loop at the bath surface (hypothesis: parasitic current), the 15–20 ms
current near crossing yarn 8 at the base pc. The study 2e files were committed by the user for the submission; these notes
edits came after (not committed).

**2026-11-05 (tensor K session).** Change T written (steps 0–7, by the user, guided) and checked in `verification/tensorK/`: checks 1, 2, 3, 5 pass, 6 done (two
predictions failed as written, causes found), 4 done (exact against the stretched-mesh twin; anisoImpesFoam within 2.5 %); next the `CHANGES_of9-port.md` entry and the commits (both repos, by the user); state and results in `NOTES_solver.md`, "Planned:
diagonal tensor K". **Still partly open, noted with the user (2026-11-05): the boundary set-up of the REV.** (1) The bath: J closes a drained free reservoir face and
the gaps lose the bath (jobs 3051, 3068); the bath inside the mesh (study 2e) keeps them wet but `B_full` leaked through the padding; `Bbox_full` (job 3078) tests
the bath under the fabric box only. (2) The closed outlet: the outlet plane cuts the half crossing yarn 9; closed, nothing leaves there; open, it would put porous
faces on an open boundary (unstable) and give the open-outlet through-flow once water arrives (`2D_bench_long`). The verification cases of change T keep the
boundaries of their templates (1D twins: old bath inlet, outlet open to air only through the fixed `Uwetting`; bench: its open outlet): they settle neither point.
**Order decided with the user (2026-11-05): the REV tensor runs (study (a), then (b)) wait for the result of `Bbox_full` (job 3078), which decides the bath set-up
they use.** Change T committed by the user (solver `4bb5d2e`, docs `11d060b`; thesis repo `7593c42`) and installed on the laptop (byte-identical to the
tested `_T`; previous binary `hybridPorousInterFoam_8a97d02`). Both repos pushed (user, 2026-11-05). mini03 (pull of both repos, `wmake` of the solver)
after the `Bbox_full` check (user); none of its jobs uses `meshing_strat_trial/tools/` (`Bbox_full` includes the study 2c copy).

**2026-11-03, end of day.** (1) **Tensor K, step 5 next** (the user writes it, guided; state of the solver working tree and the remaining steps in `NOTES_solver.md`, "Planned: diagonal tensor K", "State 2026-11-03"). (2) **mini03: jobs 3067 and 3068 ended and were scored on 2026-11-03** (REV case status; copies `~/PDM_results/REV_lowpc_run3063_3067`, the 3063 copy renamed, 0–30 ms, and `REV_midbath_run3068`; fetched with `rsync -avz`, about 3× less to transfer). 3067 (pc0 1000, L): stable to 30 ms, but the study 2c air pump moves with the wetting of crossing yarn 7 (10–17 m/s at the writes from 24 ms, 22 m/s peak; face fluxes checked). 3068 (base values, L, mid-gap bath): calm after 1.5 ms, front 14.35 mm/√s (edge bath 13.9), closed end at 28 ms; gaps drained by 1 ms and cut off from the bath by J (927 of 944 free inlet faces stay closed; 3051: 281 of 290). **To discuss with the user:** whether J's closure of drained free inlet faces needs a change before the tensor K runs (it decides the gap water in both bath planes). No job on mini03 uses `tools/` any more (Pitfalls). (3) **Study 2e: `B_full` (job 3072) ended 2026-11-04 13:17, analysed the same day** (REV case status, study README; copy `~/PDM_results/study2e_B_full`): with the bath inside the mesh the gaps at the bath stay wet (first row 944/944 water, ~12,000 cell volumes of gap water, first gap and the slots around yarn 6 full), so J's face closure kept them dry; but the layer under the padding makes the padding fill and pour through the open top/bottom faces (86 % of the inflow), so `B_full` is not a usable reference and its yarn gain is not attributed. **Chosen with the user 2026-11-04: option 1, bath under the fabric box only** (padding floor closed at the plane as `inletPad` in job 3068, no outer meniscus; a one-way J face was discussed and set aside: the meniscus would stay on the boundary face). Built as mode `box` of `buildCase.sh` (layer cells under the padding removed by subsetMesh): `Bbox_cut` (1.5 mm, 3 ms, 4 cores: the leak test) and `Bbox_full` (30 ms, 16 cores); fields above the plane identical to job 3068, smoke tests passed, predictions in the study README. **`Bbox_full` running on mini03: job 3078 (16 cores, started 2026-11-04 ~16:47; at `B_full`'s 2,330 s per simulated ms the end is ~12:15 on 2026-11-05).** Submitted directly, without waiting for the leak test (user: nobody would act on its result in the evening); `Bbox_cut` (job 3077) cancelled after 4 min, its partial files stay in `Bbox_cut/` on mini03. Then: fetch into `~/PDM_results/study2e_Bbox_full`, point the `dsLocator` include at the study's `tools/` (study README), score R1–R3 and the leak (Q1 at 3 ms from its own `waterBudget.csv`: ≤ 100 cell volumes; `B_full` 10,670). Short variants `R0_inlet` / `B_layer` (3 ms, cut at 1.5 mm) built and smoke-tested, not submitted. Still open: why the first y-yarn row stays below S_eq (B_full 0.987–0.994, 3068 0.971–0.992; gap-vs-yarn estimates above). The notes changes since commit `8b86db9` are not committed (job numbers, Courant pitfall, harmonic weights, the 3067/3068 scoring).

**2026-11-02.** Running on mini03: job 3067, REV_lowpc continued from 10 to 30 ms (~16 h, REV case status; check it against the predictions written there). Also job 3068, `REV_midbath` (8 cores, started 2026-11-02, ~37 h, same section, predictions written); copies in `~/PDM_results/REV_lowpc_run3063` and `REV_gapflow_run3065`, results in REV case status. Job 3063 passes the L validation (10 ms, no stopGuard), with a local fast current from 8.2 ms. Job 3065 diverged at 1.386 ms: not fixed, not rerun (decision of the user); why S11 and 3065 run at 17–51 m/s stays unanswered. **Next: tensor K, item (2) of the plan: the user writes the code, guided step by step (2026-11-02; corrections to the plan in `NOTES_solver.md`, "Review against `8a97d02`").** Not run: base REV with L past 15 ms (the corner pattern of job 3058).
L committed in the solver repo (`8a97d02`, docs `97f3b35`), installed on the laptop.
- **Final goal (user, 2026-10-30):** correlate the REV with cm-scale tests and use it as a prediction tool. First check (`verification/upscaling_REV/`): in job 3055/3058 the row-mean
  yarn S collapses on y/√t within 2–8 % for S 0.1–0.7 over 2–20 ms (S ≥ 0.8 not converged); front 14.0, uptake 2.43 mm/√s. Setup values, under 2 weave repeats. Missing: measured
  yarn inputs, a 1D model with gravity, a cm test not used for calibration. Weighing a wicked strip would show whether the gaps fill (TexGen geometry: 65 g/m² yarns full, up to 215 g/m² all full).
- **REV_lowpc = L validation (decided with the user):** only changes from job 3059: `porousFreeAirKrPorous on` in
  `constant/transportProperties`, `endTime` 10 ms, `caseSetup` N 4 and `job.slurm` `--ntasks=4` (next to the new case on
  mini03), `job.slurm` `--no-requeue`; `run` stops if the binary ignores the keyword; `job_restart.slurm` added (= `REV/`).
  Its submission overwrites the 3059 results on mini03 (local copy `~/PDM_results/REV_lowpc_run3059`). Result: job 3063, REV case status.
- **Screening (user: can the solver carry gap water rising significantly? the yarn may lead):** `verification/study2d_gapRise/`,
  cut REV, K 1e-12: S1 VG 5000 / 0.5 θ 40°, S2 θ 30°, S3 VG 1000 / 0.4, S4 θ 20°, S5 column to 0.33 mm; S6 set C with wet yarns. S1–S5 at 3 ms: stable, gap top 0.23–0.29 mm, no row above y 0.19 mm ≥ 20 % water, K 1e-12 does not help (results in its README).
- **Measured (`satGap.py`):** in job 3059 the gap top stays between the heights where the y-yarns reach S_eq (yarn pc = gap suction 2σcosθ/w) for w 300 and
  160 µm, at every write to 6.5 ms; the 1D similarity predicts that contour within 0.012 mm; base pc: S_eq never reached, gap top 0.19 mm.
- **Hypothesis (user, not tested):** the gap fills up to the next crossing yarn, a second gap rise starts once the yarns around it are saturated.
- **`REV_gapflow` (decided with the user 2026-10-30): the test of that hypothesis on the full REV; job 3065 diverged at 1.386 ms, before testing it (REV case status).** Set C: K 2e-11 (`Allpre`), VG 500 / 0.4, θ 40°, L,
  `darcyFaceMaxDa` 0.2 (same 39,406 porous/free Darcy faces), 150 ms on 8 cores (weekend run, ~53 h, a write every ms), `job.slurm` continues from the last
  complete write if requeued after a crash. Same K·pc0 as REV_lowpc (yarn front 8.55 mm/√s), lower S_eq. Pended from 2026-10-30 ~17:15 until job 3063 ended (2026-10-31 00:47):
  partition `global` has `MaxCPUsPerNode=46` (not 48), 40 were in use.
  **Bath plane moved to y 0.333 mm, mid-gap (decided with the user 2026-10-30, `rev_domain.json`, porous 78,489, free 163,571; S8 against S10 in study 2d: the half-yarn bath blocks the water even with closed yarns).**
  **Estimate if the yarn saturation limits the gap water:** y = 0.43 mm + 3.2 mm/√s·√t (S_eq 0.73, w 200 µm): y 0.5 mm in ~1 ms, y 0.84 mm at ~16 ms, y 1.16 mm at ~51 ms, yarn front at the closed end at ~78 ms. Measured to 1 ms only: gap top 0.544 mm; the later heights were not reached. Scratch copy before the shift: built by `Allpre`, 15 steps,
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
- **`Courant Number` in the log covers all cells, free and porous** (stock `CourantNo.H`: 0.5·Σ|φ|/V·dt, no cell filter; checked 2026-11-02): the "free Courant" of these notes is that number. Co·Δx/dt gives the fastest cell anywhere, not where it is; at the writes analysed so far (jobs 3059, 3063, 3065) the fastest cell was a free one.
- **Don't pull a change of `tools/` onto a cluster while runs use it** (risk, not tested): `system/controlDict` includes `tools/<functionObject>` with `runTimeModifiable yes`, and a coded function object that recompiles inside
  `mpirun` aborts (`MPI_ERR_TRUNCATE`). The tensor K change touches `tools/coatsTimeStep`: on mini03 only once jobs 3067 and `REV_midbath` have ended (both ended 2026-11-03).
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
