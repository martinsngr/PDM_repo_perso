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
| `geometry/inspect_stl.py` | REV box of an STL → `rev_domain.json` (in metres) |
| `geometry/rev_domain.json` | REV box of `inspect_stl.py`: x 0–1.818, y 0–2.667, z −0.0705–0.2115 mm (exactly periodic in x and y) |
| `geometry/rev_domain_midbath.json` | the same box moved by half a crossing-yarn spacing along y (y 0.333–3.0 mm): bath plane mid-gap, job 3068 |
| `geometry/check_periodicity.py` | checks that the x and y planes of a built REV are periodic |
| `tools/build_fields.py` | mesh (`system/blockMeshDict`) + eps, K, fYarn, yarnID from the STL and a REV box |
| `tools/initFields.py` | initial `alpha.wetting` (bath water, dry yarns, ramps) and its boundary field |
| `tools/runTools.sh` | `runTmpLog`: solver log outside the workspace, `LOG_EVERY` filtering |
| `tools/coatsTimeStep`, `liquidBalance`, `stopGuard`, `waterBudget` | function objects included by every `system/controlDict` |
| `tools/check.py` | per-write checks of a REV run along y (fronts, gaps, |U|, budget) |
| `tools/compare3068.py` (+ `analyseCut.py`) | a run against job 3068 on the cells above the bath plane |
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
| `horizontal` | the previous student's set-up with our model: the fabric lying flat on a bath at rest, water rising through the thickness (z); x and y cyclic; 5 water rows (0.1 mm) under the fabric box fed from the bottom face (J, totalPressure 0.988 Pa = ρg·5Δz: water at 0 Pa at the bath surface), 5 air rows above it, top open; gravity −z; θ 40° (her value); gaps air, yarns 0.002 except a **wet contact zone** (yarn cells of the bottom four fabric layers on a ramp S 0.84 / 0.64 / 0.35 / 0.15, +6.3 % of the yarn capacity, adopted 2026-11-09 after study 2f) | new (her case: interFoam, impermeable body-fitted yarns, θ 40°, symmetry sides, g 0, inflow fixed at 1e-4 m/s; ours: bath at rest) | 16, 5 ms, every 0.1 ms |

The horizontal case is the REV box of `inspect_stl.py` (91 × 133 × 14 cells, its cells identical to job 3051's box)
with 5 + 5 free layers: 290,472 cells, 78,528 porous; `inlet` and `top` 12,103 faces each, all free (the bath touches
the yarn crests: 747 of the 12,103 faces of the first box layer are porous). The bath surface has no edge (x, y cyclic):
none of the outer-bath problems of study 2e.

**Runs:** `tensorA` job 3107 and `tensorB` job 3108 on mini03 (8 cores each, submitted 2026-11-09); `anisoA` job 3109 and
`anisoA_mu100` job 3110 (4 cores each, submitted the same day, ~30 min later); `horizontal` ready since 2026-11-09 (wet contact
zone, hold lifted), not submitted.

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
- Reading: X2 and X3 hold = the REV front is set by the yarn network, and anisoImpesFoam (yarn-only, ~10× cheaper) can
  carry the weave and density variants. X2 fails with X4 small = the hybrid's gaps or bath change the front: not a
  substitute. X4 large = a yarn-only model needs a vent (a Richards solver with a tensor K, or a venting boundary).

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
