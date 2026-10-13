# Wicking cases — 1D, single yarn, fabric REV

Setups, results and open work of the cases in `trialWicking/` (1D column and single yarn, impesFoam and
hybridPorousInterFoam) and `meshing_strat_trial/` (fabric REV, 2D bench, slit tests). Last updated 2026-10-13.
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
| `meshing_strat_trial/2D_bench/` | **The 2D bench:** thick-wall slit (yarn wall 8 cells \| gap 8 \| yarn wall 8), G + H + F′ + I on; `Allpre`, `run`, `check.py` |
| `meshing_strat_trial/2D_bench_strip/` | First 2D bench (strip between open free layers), archive: `variants/` (debugging runs, referees R1–R3, `makeVariant.sh`, `ADD=` option) and figures; template of `slit_test/makeSlit.py` |
| `meshing_strat_trial/slit_test/` | Slit capillary-rise tests: `makeSlit.py` (`--walls real/porous`, `--nw`, `--w`, `--K`, `--theta`, `--dx`, `--add`), `slitReport.py`, `benchSlit.py`, `interFoamSlit.sh`, `figures/`, `old_runs/`. Run folders: `S0_*` real walls, `P_*` current porous-wall set, `IF_*` stock interFoam; `B_/H_/HF_/I_/J_/N_/R_/V_` intermediate |
| `verification/` (repo root) | All verification: paper tutorials, 1D similarity solution, ddtCorr bench, inlet test (moved from `trialWicking/verification/` 2026-10-13; results in `NOTES_solver.md`), and **`PLAN.md`: the planned studies 1–3** |
| `meshing_strat_trial/tools/` | `runTools.sh`, `initFields.py`, `pOpenAir` (open-patch p BC), function objects `coatsTimeStep`, `liquidBalance`, `waterBudget`, `stopGuard` |

## Common setup and rules

- **Properties (setup values, not calibrated):** K 1e-11 m² scalar, ε 0.5, Brooks–Corey n 3, Van Genuchten pc0 5000 Pa
  m 0.5, water/air (μ 1e-3 / 1.76e-5 Pa·s), σ 0.072. pc0 5000 Pa is consistent with K 1e-11 by Leverett scaling (4–8 kPa).
  The wicking rate constrains K·pc0, the equilibrium height (pc0/ρg ≈ 0.5 m) constrains pc0: fitting both needs
  experimental-length samples. Real K (tensor), pc and contact angle (polyester) come later.
- **Gravity along the wicking direction** (−x), reservoir at x-min.
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
  Free fraction per z layer 0.86 (bottom) → 0.15 (middle) → 0.91 (top): the edge layers are mostly open space beside the
  crimped fabric.
- **Yarns:** thickness median 6 cells (120 µm), max 7–8; width ~15 cells (300 µm); yarns 0/4 and 5/9 are halves cut by
  the periodic boundaries. A yarn flank facing an in-plane gap is ~8 cells deep, a face facing a crimp pocket ~3.
- **Gaps** (narrowest free run between yarns along x, y or z, per free cell): median 15 cells (300 µm), p25 9, p10 6, p5 4;
  ≤ 4 cells 6 %, ≤ 8 cells 20 %. Narrow throats at mid-thickness where warp and weft cross; near the surfaces medians
  18–58 cells. 82 % of the free cells inside the fabric envelope, 1 % enclosed. TexGen model, not the real fabric.

### Gap vs yarn wicking (estimates)
Viscous Washburn h²/t = σw cosθ/(3μ) for a slit: w 160 µm θ 60° → 44 mm/√s, w 300 µm θ 75° → 43, θ 85° → 25; yarn
(K 1e-11, pc0 5000) 18 mm/√s. **A straight continuous gap out-runs the yarn unless θ ≳ 87°**, but stops at
h_eq = 2σcosθ/(ρgw) ≈ 13 mm (300 µm, θ 75°) while the yarn holds ~0.5 m. In a plain weave the gaps are interrupted by
crossing yarns (hypothesis, not checked from `fYarn`: mostly no continuous channels → yarns lead). In the 2D bench the
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

### Slit tests (`slit_test/`, 2026-10-12/13)
- **Setup:** 2 mm vertical slit, 20 µm, reservoir at x = 0, open at x = 2 mm; `S0` real walls with
  `constantAlphaContactAngle`; porous walls `--nw` cells, closed behind, ending 3 cells before the outlet. Reference:
  Bosanquet rise ρ d(hḣ)/dt = 2σcosθ/w − 12μhḣ/w² − ρgh from the 0.1 mm start.
- **Inlet:** a static p = 0 inlet gives the entering water velocity without the dynamic-pressure cost (~60 % too fast
  at 2 ms); free inlet faces at total pressure 0 (`openFreeTotalPressure 1`, p = −½ρ|U|²) = reservoir at rest.
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

### REV case status (`REV/`)
`./Allpre` works (20 s, Mesh OK). Missing: `run` (decompose, serial precompile, mpirun), `caseSetup` (N),
`decomposeParDict`, `job.slurm`, endTime. Decisions to take (listed at the top of `Allpre`):
- top/bottom: open porous faces are unstable → closed walls or free-cell padding (`inspect_stl.py --zgap`);
- outlet: yarns end before it, or porous outlet faces closed;
- inlet: total pressure for free faces; water column in the gaps at the inlet (`initFields.py --free-fill`);
- keywords G + H + F′ + I, `activatePorousContactAngle 1`, θ (as `2D_bench`);
- y cyclic (checked by `check_periodicity.py`), parallel: E handles coupled faces; H/F′/I not yet tested on coupled faces.

## Reference: Boubaker et al. 2026 (Compos. Part A 206, 109781)
Same solver on a plain-weave E-glass µCT geometry (tows porous, inter-tow space free; K_VOID = 1 m² comes from there).
They replaced MULES by isoAdvector after an unstable porous/free interface; contact angle 90° assigned at the interface;
mild pc (VG pc0 1000 Pa, m 0.8 "for stability": α·pc ~10 Pa vs our ~5 kPa); flow pressure-driven (ΔP 50 kPa), no pure
spontaneous wicking; mould walls top/bottom, cyclic sides; 131 × 101 × 53 µm cells, 4–6 days on 32 cores; tensor K per
tow (diagonal Gebart; solver and data on request). They see artificially fast flow in the free layer near the upper
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
**State 2026-10-13:** solver `b525086` installed and pushed (mini01: pull, rebuild library and solver); `2D_bench` is the
thick-wall slit with all checks passing; `REV/` prepared up to `Allpre`; 1D and single yarn unchanged with the new solver.
1. **Verification: `verification/PLAN.md`, start there** (agreed 2026-10-13, nothing run yet): Study 1 equilibrium
   oscillation (EQ0m-dt first), 2a ablation of G/H/F′/I on the 15-cell slit, 2b face checks (bench, R2), 3 sensitivity
   (θ, K, pc0). Still to schedule after them: static meniscus at 4/8/15 cells (Δp vs 2σcosθ/w), kr variant on yarn/gap
   faces, `porous_Boundary` tutorial original vs E.
2. **REV:** take the decisions above, write `run`/`job.slurm`, local smoke test, then mini01. Before: parallel/cyclic and a
   small 3D check of H/F′/I.
3. Bench extensions: 15-cell gap (REV median), gaps interrupted by porous crossings (yarn first, then gap: needs an empty
   gap to fill from a wet wall, probably a saturation-dependent θ), θ 75°, 5 ms runs.
4. Later: tensor K (solver change), real K/pc/θ for polyester; report the impesFoam Todd bug upstream; a swept yarn mesh
   (~100 µm axial cells) for cm-long samples comparable with experiments.
5. Tidy: move the intermediate slit runs (`B_/H_/HF_/I_/J_/N_/R_/V_`) to `slit_test/old_runs/` (proposed, not done);
   delete the obsolete scratch build `hybridPorousInterFoamH`.

## Pitfalls met
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
