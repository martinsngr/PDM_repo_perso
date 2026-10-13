# trialWicking — working notes

Status and findings for the wicking cases. Last updated 2026-10-05.

## Cases

| Folder | What it is |
|---|---|
| `1D_vertical_impes/` | 1D equivalent of the yarn case: column length = yarn centreline unfolded along the crimp (3.446 mm for x 0.4–3.6 mm; straight 3.2 mm), section 0.55 mm (width) × 0.237 mm (mean thickness), both measured from slices of `yarn-c.stl`. 1×172×1 cells (20 µm), reservoir = bottom 0.2 mm cellZone held at Sb 0.99 via `fixedSb`, pc0 5000 Pa, K 1e-11, Coats CFL. Top is open to air (`outlet` p fixed 0, Ub fixed 0): with the old `darcyGradPressure` top the air could only leave counter-current back into the reservoir, which made the column fill much more slowly than the yarn (mean Sb 0.59 vs 0.91 at 0.06 s). The yarn vents air through `yarn_to_fluid` along its whole length. Open top: mean Sb 0.36 / 0.50 / 0.70 / 0.84 at 0.01 / 0.02 / 0.04 / 0.06 s (yarn 0.42 / 0.56 / 0.77 / 0.91), front at the top at ~0.035 s; 0.1 s runs in ~75 s. The real section is lens-shaped: its area (STL volume / unfolded length = 9.47e-8 m²) is 27 % smaller than the 1.30e-7 m² rectangle, so scale uptake volumes by 0.73 before comparing with the 3D case. (Before 2026-09-24: 1 m column, pc0 100 Pa, ~1 cm equilibrium rise.) |
| `1D_vertical_impes_inletRes/` | Copy of `1D_vertical_impes` with the reservoir as the inlet boundary instead of the clamped cellZone: Sb fixed 0.99 on `inlet` (infinite supply), no `fixedSb`/`topoSet`, outlet Sb zeroGradient. Initial Sb 0.002 with the 10 bottom cells ramped linearly 0.99 → 0.002 (`setFieldsDict`). Same start state and inlet as `1D_vertical_hybrid`, for a like-for-like comparison. 0.1 s in ~2 min; mean Sb 0.352 / 0.606 / 0.777 / 0.902 at 0.01 / 0.03 / 0.05 / 0.1 s (hybrid: 0.337 / 0.585 / 0.753 / 0.891). |
| `1D_vertical_hybrid/` | The same column in hybridPorousInterFoam (renamed from `BL_flowDriven_VanGenuchten_hybridPorousInterFoam` 2026-09-30). p is the mixture pressure p_air − α·pc(α); both ends compute it every step (`codedFixedValue`) so the air stays at 0 Pa as α at the face changes. Inlet α `inletOutlet` 0.99 (infinite reservoir, as the `Capillary_Rise` tutorial), outlet α zeroGradient (a fixed value draws water into the top cell and crashes), same ramp as above, adaptive dt from a coded function object applying impesFoam's Coats CFL 0.5 / dSmax 0.01 limits with a 1e-7 floor (the solver itself has no capillary dt limit), PIMPLE 1/2, `nAlphaSubCycles 1`, endTime 0.1 s (~9.5 min; mean α 0.891 at 0.1 s vs 0.902 for `1D_vertical_impes_inletRes`). `liquidBalance.csv` from a coded function object. Details in its `CLAUDE.md`. |
| `singleYarn_IMPES_yarn/` | Original 3D yarn case (`yarn-c.stl`): wetting from below in z through a `wetInlet` patch, fixed deltaT 1e-9. Kept as reference ("original set up" commit). Its mesh has 24 negative-volume cells (see below). |
| `singleYarn_IMPES_vertical/` | The 1D vertical test moved onto the yarn geometry. **Current working case.** |
| `singleYarn_vertical_impes_inletRes/` | `1D_vertical_impes_inletRes` on the yarn mesh of `singleYarn_IMPES_vertical` (same snappy pipeline, 15,188 cells). Reservoir = Sb 0.99 on the end face `left` (no `fixedSb`), dry at 0.002 with the 0.2 mm ramp from x = 0.4 mm. Air leaves through the top `right` only (p 0, Ub 0, Sb zeroGradient); the lateral surface `yarn_to_fluid` is **closed** (Ua, Ub 0, p `darcyGradPressure`) since 2026-10-01, to match the hybrid twin. With the open lateral wall: mean Sb 0.0716 at 0.2 ms; closed: 0.0659. fvSchemes, fvSolution and controlDict from the 1D case (upwind kr, harmonic K; the old yarn case had no `interpolationSchemes`, i.e. linear kr). Smoke test (0.2 ms, 4 cores): dt 5.1e-8, Coats CFL 0.50, Sb in [0.002, 0.95], 73 s → ~10 h for 0.1 s. **Run to 0.1 s on mini03 (job 2691, 2026-10-02): 3.8 h**, 1.79M steps, mean Sb 0.904 at 0.1 s (see Cost and scaling → Yarn runs to 0.1 s). |
| `singleYarn_vertical_hybrid/` | `1D_vertical_hybrid` on the same yarn mesh: `left` = 1D inlet, `right` = 1D outlet, lateral surface `yarn_to_fluid` closed (an open lateral wall is ill-posed in this solver). With the original solver it diverged within 10 steps; **with the porous-face changes (`hybridSolverChanges/`, `darcyFaceMaxDa 0.1`) it runs**: smoke test 0.2 ms, dt 5.1e-8 (as impesFoam), α in [0.002, 0.99], mean α 0.0584 vs 0.0659 for the impesFoam twin (early inlet gap, as in 1D). Estimated ~1.5–2 days for 0.1 s on 4 cores; **run to 0.1 s on mini03 (job 2692, 2026-10-02): 11.9 h**, 1.88M steps, mean α 0.899 at 0.1 s. p, p_air, p_water and `Uwetting` profiles in `wickingFront.ipynb`. |
| `verification/` | Paper tutorials, original solver (`be54696`) vs modified (`b995db5`, `darcyFaceMaxDa 0.1`) vs analytical solutions: flow-driven Buckley–Leverett (4.1.1, inlet p `fixedFluxPressure`), gravity-driven Buckley–Leverett (4.1.2), gravity–capillarity equilibrium (4.1.3), all Brooks–Corey. See Findings → Verification. |

## singleYarn_IMPES_vertical setup

- **Wicking direction:** along the yarn axis x (bottom = `left` at x-min, top = `right` at x-max). Gravity `(-9.81 0 0)`.
- **Reservoir:** cellZone `bottomReservoir`, x ∈ [xmin, xmin + `xRes`] with `xRes` = 0.2 mm (`caseSetup`), built by `system/topoSetDict.reservoir` after the yarn mesh is extracted; clamped at Sb = 0.99 every step by the `fixedSb` block in `transportProperties`.
- **Boundary conditions** (copied from the 1D inlet/outlet):

  | Patch | p | Ua | Ub | Sb |
  |---|---|---|---|---|
  | `left` (bottom) | fixed 0 | fixed 0 | zeroGradient | zeroGradient |
  | `right` (top) | darcyGradPressure | zeroGradient | fixed 0 | fixed 1e-3 |
  | `yarn_to_fluid` (lateral, open to air) | fixed 0 | zeroGradient | fixed 0 | zeroGradient |

  The `0/` files also carry `"(inlet|outlet)"` / `"(top|bottom)"` entries: `splitMeshRegions` reads the fields on the **full** mesh and fails without them.
- **Properties:** K 1e-11 m², ε 0.5, Brooks–Corey n = 3, Van Genuchten pc0 5000 Pa, m 0.5, Sbmin/Sbmax 0/0.999 (Sbmax must stay above the 0.99 clamp value).
- **Mesh:** `CpD 12` cells per `w1` = 0.55 mm (yarn width), giving a 70×24×25 base mesh (46 µm); surface refinement `refLev 1` only (no interior refinement region); `nCellsBetweenLevels 1`. Result: 15,188 yarn cells, checkMesh OK, max non-orthogonality 42°, volume within 0.2 % of the STL.
- **Time control:** `adjustTimeStep yes`, `CFL Coats`, `maxCo 0.5`, `dSmax 0.01`, `minDeltaT 1e-12`, `endTime 0.1`, write every 0.01 s.

## Findings

### Geometry and mesh
- **The yarn is crimped.** It is a flat section about 0.55 mm wide (y) and 0.22–0.29 mm thick (z), and its centre oscillates in z with a period of about 1.8 mm. The bounding-box z extent (0.58 mm) is crimp amplitude plus thickness, not thickness.
- **The inside point was outside the yarn.** The bounding-box centre (z ≈ 0) lies outside the crimped yarn at mid-length, so snappy's `yarn` zone was really the air around it. The old `topoSetDict` hid this by redefining `yarn` with `surfaceToCell includeCut true`, which added a layer of cells and made the volume 11–25 % too large.
  - Fix: `zcat 0.000179` in `caseSetup`; `bounding.py` now takes the section centre from a slice at mid-length.
  - `topoSetDict` now keeps snappy's `yarn` zone and defines `fluid` as its complement.
- **`nx` formula:** `blockMeshDict` divided by `0.0316`, the yarn width `w1` of the fabric case (`PW-22-15-0.4-0.5`), which gave nx ≈ 1, so `(40 20 20)` had been hard-coded. It now uses `$w1` and `($nx $ny $nz)`. `dg` in `caseSetup` is not used anywhere.
- **`minVol 1e-13` in `snappyHexMeshDict`** is an absolute volume (m³) inherited from the metre-scale fabric case. With cells of about 1e-15 m³, it flagged about 750k faces and made snappy's quality control useless; it is now 1e-25.
- **`left`/`right` changed from `symmetry` to `patch`** in `blockMeshDict`, so they can take the end BCs.

Mesh comparison (after the inside-point fix):

| Settings | Yarn cells | Volume error | checkMesh |
|---|---|---|---|
| Original (40×20×20, refLev 0) | 2,840 | — | 24 negative-volume cells |
| CpD 12, refLev 1, nCBL 1 (**current**) | 15,188 | +0.2 % | OK |
| CpD 12, refLev 2, nCBL 1 | 68,296 | +0.3 % | OK |

### Time stepping (`impesFoam`)
- **Without `adjustTimeStep yes`, deltaT is never adapted.** This explains the fixed 1e-9 in the original yarn case.
- **Todd bug, upstream code:** `ToddNo.H:61` divides `maxCo` by `Tpc`, which is a time in seconds, so the capillary limit never applies. The same line is in upstream master (6a8ecc3) and dev; not yet reported or patched. A consistent form would be `maxCo*Todd_factor_pc/runTime.deltaTValue()`. **Use `CFL Coats`**, whose CFL is correctly dimensionless.
- **Any Sb above Sbmax crashes the solver.** Van Genuchten returns NaN and the run dies with SIGFPE.
- **The 0.1 s yarn run crashed near full saturation** (t = 0.0678 s, min Sb 0.908, max Sb oscillating 0.991–0.998, then above Sbmax). Two likely causes, not fixed yet:
  1. The Coats capillary term uses the mobility kra·krb/(μb·kra + μa·krb), which goes to 0 as kra → 0, but `phiPc` (`updateSbProperties.H:22`) uses the liquid mobility `Mbf` alone. With air supplied freely through the p = 0 side wall, the real explicit limit near Sb 0.99 (where dpc/dS → ∞) is much tighter than Coats says.
  2. On `yarn_to_fluid`, fixed p lets both phases cross the wall in `pEqn`, but `SEqn.H` forces `phib` = 0 there (Ub fixed). Once the yarn is wet, most of the wall flux is liquid for `pEqn`, which leaves unbalanced liquid sources in the wall cells.
  - Proposed fix: on patches with fixed `Ub`, use only the air mobility in `pEqn`. Alternatives: a stricter capillary CFL, Van Genuchten Sbmax > 1, or a clip (hides the mass error). The 1D case survived because Sb stayed ≤ 0.96, but the open-top 1D outlet has the same BC inconsistency.

Tests on the current mesh (4 cores, about 7 min each):

| Settings | Result |
|---|---|
| Todd, dSmax 0.001 | stable; dt swings between about 4e-7 and 1e-12; 1.85e-3 s simulated |
| Todd + `minDeltaT 1e-8` | blows up at t = 0 (Sb = 327) |
| Two stages: 1e-12 floor until 1.5e-4 s, then 1e-8 | Sb 1.0004 > Sbmax, SIGFPE |
| Todd, dSmax 0.01 | Sb 0.9994 > Sbmax, SIGFPE |
| **Coats, maxCo 0.5, dSmax 0.01** | **stable; dt steady at about 5e-8; Sb ≤ 0.99; 1.21e-3 s simulated** |

### Cost and scaling
- Explicit IMPES: the stable dt is about Δx_min²/D, with D ≈ K·pc0/(μ·ε) ≈ 1e-4 m²/s. Here the stable dt is about 1e-7 s on 23 µm surface cells.
- The number of steps is about (distance wicked / Δx_min)², independent of the physical size. Cost ∝ (L/d)³·CpD⁵: a few cm of yarn in full 3D would take months.
- pc0 does not change the number of steps; it scales the physical time (lower pc0 needs a longer `endTime`).
- The 1D case is cheap because Δx is 1 mm and the front stops after about 1 cm, after which dt grows freely.
- `singleYarn_IMPES_vertical` run: 0.02 s per step, about 2.2M steps to reach 0.1 s, about 12 h on 4 cores.
- A faster machine helps more than expected (1.7× for impesFoam, 3.7× for hybrid on mini03 vs the laptop, below).
  More cores don't help: 15k cells are already communication-bound.

#### Yarn runs to 0.1 s (mini03, 4 cores, 2026-10-02)

Both cases on the same 15,188-cell mesh, Coats CFL 0.5, `LOG_EVERY=100`. Wall times from the SLURM logs
(`Log_*.log`); steps counted from the kept log lines (every 100th step).

| Case | Job | Wall time | Steps | Cost per step | dt | Estimate from the laptop test |
|---|---|---|---|---|---|---|
| `singleYarn_vertical_impes_inletRes` | 2691 | 3.8 h (solver 13,701 s) | 1.79M | 7.6 ms | 5.4e-8 → 3.9e-8 (0.06 s) → 1.7e-7 (0.1 s) | 73 s per 0.2 ms → 10 h |
| `singleYarn_vertical_hybrid` | 2692 | 11.9 h (solver 42,786 s) | 1.88M | 22.7 ms | 5.2e-8 → 3.4e-8 (0.06 s) → 1.5e-7 (0.1 s) | 5.3 min per 0.2 ms → 44 h |

- **The step count was predicted correctly:** 3,800 steps in the first 0.2 ms × 500 = 1.9M. dt stays at the
  Coats limit all the way (CFL max 0.4985 at the last step): it falls to ~3.5–4e-8 while the yarn fills, then rises
  from ~0.065 s, when the air kr (and with it the Coats capillary mobility) goes to 0 near saturation. The two
  roughly cancel (1–6 % fewer steps than the estimate).
- **The difference is the cost per step.** Laptop (Ryzen 7 5700U, WSL, 4 cores): 19 ms (impesFoam), 84 ms (hybrid).
  mini03: 7.6 and 22.7 ms. For impesFoam the first 0.2 ms also cost more than the rest (11.5 ms/step on mini03:
  start-up, more pressure iterations), so the short test overestimates by a further ~1.5×. The hybrid's 3.7× is not
  fully explained by the logs: it does more memory-bound work per step (PISO with 2 GAMG p solves, α equation,
  coded function objects), and the laptop time may include compiling the 4 coded libraries, which the cluster
  `run` does in a separate serial step.
- **For estimates:** extrapolate the step count from a short test, and use the per-step cost measured after the
  first few hundred steps on the target machine. The hybrid costs ~3× impesFoam per step on this mesh.

### hybridPorousInterFoam in 3D (2026-10-01, tests in the scratchpad)
- **The open lateral wall is ill-posed in this solver.** On a patch with `Uwetting` fixed and `U` not fixed, `correctUBc.H` replaces the face flux from the pressure equation by `(Uwetting_b + UnonWetting_b)·Sf`. With `UnonWetting` zeroGradient this is the cell's air velocity vector. That is fine on a face normal to the flow (1D outlet, yarn top), but on the crimped lateral surface the mostly axial air velocity is projected on tilted normals and the wall flux no longer follows the pressure: |U| ≈ 700 m/s in the wall cells at the ramp end after one step (p −5e6 Pa).
- **The solver is also unstable in 3D, whatever the walls.** A closed lateral wall (U, Uwetting, UnonWetting fixed 0, p `fixedFluxPressure`) still diverges at ~1.3e-7 s, and so does the 1D case itself meshed as 5×172×3 cells, with closed or `symmetry` side walls (3.5–3.9e-5 s; the 1-cell-wide original runs to 0.1 s). In the box the across-section spread of α grows from 3e-6 to 0.1 within 1e-5 s at the front, with transverse velocities ~1 m/s: a numerical transverse mode (water displacing air is viscously stable).
- Not caused by: dt (floor 2e-8, 1e-9 or none all diverge, earlier with smaller dt), non-orthogonal correction (`uncorrected` and `limited 0.333` the same), snappy refinement interfaces (uniform `refLev 0` mesh the same). A dry state of 0.05 instead of 0.002 (pc 22 kPa instead of 2.5 MPa) lasts 6× longer (2.2e-4 s) but still diverges.
- **Root cause, part 1 (established; became change A): odd-even decoupling of the relative flux.** `alphaEqn.H` builds `phirPore` by interpolating the cell velocities `Uwetting`/`UnonWetting` (from `fvc::grad`) to the faces: a wide stencil that cannot see a checkerboard. Between two cells across the width, the interpolated gradient is exactly 0, so capillary diffusion does not damp the mode, while the total flux (`phiPc`, compact `snGrad`) does see it. It also affects 1D: with the original solver the early 1D profile is a staircase of cell pairs, some inverted (0.293/0.305, 0.068/0.147 at 5e-6 s). An experimental copy computing the phase fluxes on faces with `snGrad` (scratchpad, not in the solver repo) gives a smooth monotone 1D profile, and the 5-cell-wide bench now runs to 0.2 ms instead of diverging (1D mean α at 0.2 ms: 0.0492 instead of 0.0542).
- **Part 2 (became change B):** with face fluxes, a transverse mode still grows (×1.5 per step, spread ~0.08). The α profile is smooth, but the cell total velocity U alternates along the column (0.08–0.30 m/s in neighbouring rows, though the face flux is uniform), and feeds back through `HbyA` (ddt/convection terms of the momentum equation). Removing inertia (`ddt(rho,U) steadyState`) makes both versions worse.
- **Part 2 fixed in a second experimental copy (`hybridPorousInterFoamDarcy`, scratchpad; committed later as change B, the numbers below are from the prototype): Darcy total flux in porous faces.** In `pEqn.H`, faces with `Solidf = 1` use the Darcy mobility `Mf` instead of `rAUf` and the face phase Darcy fluxes (capillary + gravity, the same terms as part 1) instead of `HbyA`; porous cells take U = reconstruct(phi). Faces with `Solidf = 0` (free fluid) are unchanged by construction. Justified for this yarn: Darcy relaxation time ρK/(με) 2e-5 s (water) / 1e-6 s (air) ≪ wicking time, and Brinkman layer √K ≈ 3 µm < one cell. Bench: spread stays at round-off (1e-9 for NX = 2, 8e-8 for NX = 5), identical mean α for NX = 1, 2, 5, about 5× fewer steps than part 1 alone.
- **Remaining difference to impesFoam (bench, 0.2 ms): mean α 0.0528 vs 0.0592.** The front part is the kr interpolation: impesFoam upwinds kr (`upwind phia/phib`), hybrid interpolates linearly; impesFoam with linear kr gives 0.0570 and the same leading edge as the hybrid. The rest sits next to the reservoir (first cell 0.896 vs 0.947), probably the inlet BC (hybrid `inletOutlet` lets 1 % air in, impesFoam water only); not checked yet.
- **2026-10-13: changes H (`1588863`), F′ (`3aded21`), I (`b525086`), opt-in (porous walls next to free fluid);
  no effect on the cases of this folder (no free cells). Details: `hybridSolverChanges/README.md`.**
- **2026-10-12: changes F (`febfcae`, mixed-cell velocity, always on) and G (`1b007d8`, opt-in
  `porousFreeDarcyFaces`, capillary jump at porous/free faces).** Cases in this folder (no free cells) are unaffected
  in α, p, φ; F changes only the written U of `singleYarn_vertical_hybrid` along its closed wall (U written by the
  older binaries there is not meaningful). Details: `hybridSolverChanges/README.md`, `../meshing_strat_trial/NOTES.md`.
- **2026-10-12: change E (`c3a2e6e`, bug fix): `Solidf` stays binary at every step.** Found in the fabric work
  (`../meshing_strat_trial/NOTES.md`): from step 1 porous/free faces had `Solidf = 0.5`. Bit-identical for all cases
  in this folder (no free cells); installed, A–C binary kept as `hybridPorousInterFoam_b995db5`. Details in
  `hybridSolverChanges/README.md` and the solver repo's `CHANGES_of9-port.md`.
- **Changes A (face relative flux), B (opt-in Darcy total flux, `darcyFaceMaxDa`) and C (upwinded kr) are logged with patches in `hybridSolverChanges/`** (committed on `of9-port` 2026-10-01: A `b0c0f67`, B `cf95c59`, C `b93e429`, B fix `c0c1b4e`, C fix `b995db5`; installed until 2026-10-12, now E `c3a2e6e`). Bench stable (5 ms, spread ≤ 4e-7); 1D uptake within 0.5 % of the original hybrid. A porous/free interface with a wet porous side diverges in the original solver too: next problem before the fabric case.
- Test bench: the 1D hybrid case widened to NX cells (symmetry sides, empty front/back) with a coded function object printing the across-width spread of α and p per step. NX = 1 stays exactly 0; NX = 2 and 5 grow from round-off.
- Parallel: compiling the coded BCs / function objects inside `mpirun` aborts with `MPI_ERR_TRUNCATE`; the `run` script compiles them first with a serial `hybridPorousInterFoam -postProcess -time 0`.
- On the yarn mesh the Coats limit is ~5e-8 s, below the 1D floor `minDeltaTCoats 1e-7`; the yarn case uses 2e-8.

### Verification against the paper (2026-10-05, `verification/`)
- **The OF9 port is physics-neutral:** `0a408f5` (upstream v8) → `be54696` only renames OpenFOAM API calls
  (fvOptions → fvModels/fvConstraints, `CorrectPhi` signature + `pressureReference`, link flags); the porous libraries
  are unchanged and are the same for `be54696` and `b995db5`. v8 itself was not rebuilt (OpenFOAM 8 not installed).
- **Gravity-driven Buckley–Leverett, Brooks–Corey (paper 4.1.2)**, `be54696` (port) vs `b995db5` + `darcyFaceMaxDa 0.1`
  (A+B+C, the wicking setup). **Same setup as the paper**: the shipped tutorial injects water only at 1e-5 m/s
  (`0/Uwetting` fixedValue (1e-5 0 0), `0/UnonWetting` 0 on `leftWall`, applied to the inlet flux by `correctUBc.H`;
  U, p and α are zeroGradient there), g 9.81 along the flow, K 1e-11, ε 0.5, Brooks–Corey n 3, 2000 cells.
  - **Darcy faces:** off in `port` (`be54696` does not read `darcyFaceMaxDa`), on in `ABC` (log: "1999 of 1999
    internal faces, 2 of 2 boundary faces").
  - **Comparison: error norms against a reference built from the inputs only** (`verification/analyse.py`, closures
    as in the library): u = 1e-5 m/s, plateau S_P from F_w(S_P) = 1e-5 → 0.4668 (paper eq. 54, which drops the
    f_w·u term: 0.467), shock speed u/(ε(S_P − S0)). At 21,000 / 42,000 / 63,000 / 85,000 s: plateau 0.4663 for both
    (−0.1 %); front −0.11 to −0.16 % (4–5 mm behind at 3.66 m, ~2 cells); mean |S − exact| over the cells 4e-4 →
    1.1e-3, the same for both. The lag is a water-balance deficit, identical in both solvers: the column holds
    99.76 % of the injected water (F_w(0.4663) = 0.997e-5), i.e. the original inlet treatment, not the changes.
    **Cause demonstrated (rerun, 2026-10-07, `verification/inlet_eps1e-8/`):** the boundary relative flux in `alphaEqn.H:157/159` divides by
    (ε α_b + 0.001); the water inflow is then u[α + (1 − α) εα/(εα + 0.001)] = 0.9977 u. Same solver with + 1e-8
    (scratch build, only those two lines changed), 21,000 s: stored/injected 0.99741 → 0.99973, plateau 0.4663 →
    0.4667 (exact 0.4668), front −0.12 % → +0.05 %. The remaining 0.03 % is not explained (start-up transient?).
    **Second inlet inconsistency, also in both solvers:** `correctUBc.H` writes 1.000e-5 on the inlet face after
    the pressure solve, but every interior face carries 1.082e-5 (both solvers): the pressure solve saw the
    gravity flux of both phases there, not the injection. The inlet cell creates 8.2e-7 m/s of volume per step
    (the air gravity flux λ_a ρ_a g ≈ 8.4e-7), which is exactly the logged continuity error (2.06e-7 per step,
    cumulative 0.083 at 85,000 s). The extra volume leaves as air; water flux barely depends on the total velocity
    here (f_w ≈ 0), so the water results survive. This agreement depends on that property of the setup: do not
    generalise it to inlets imposed through Uwetting with U zeroGradient.
    Port vs A+B+C: mean |ΔS| 1.2e-4, max 0.08 in the front cell. Total velocity, uniform in 1D: 17–19 % spread
    between cells with the port, < 0.1 % with A+B+C. ~25 min per run.
  - **Meshes:** one (the paper's 2000 cells). No refinement study (decided 2026-10-07): the check is "same setup as
    the paper, same or better agreement".
- **Gravity–capillarity equilibrium, Brooks–Corey (paper 4.1.3), `verification/eq_BC`, 30,000 s (2026-10-07).**
  Tutorial = the paper's Fig. 6 setup (pc0 1000 Pa: Fig. 6C's analytical |dS/dy| at S = 1 is 19.5 1/m = Δρg/(β pc0);
  Table 2's p0 100 Pa would give 196). 1 m, 1500 cells, lower half at S 0.5. Reference from the inputs only
  (`analyseEquilibrium.py`: Fig. 6C relation and the static profile holding the initial 0.25 m of water). Wall time
  1.7 h (original) / 2.2 h (modified). Figures `gravityCapillarityEquilibrium_BC.png` (last write) and
  `gravityCapillarityEquilibrium_BC_evolution.png` (profiles at 250 → 30,000 s, water volumes vs log t).
  - **Original (`be54696`): approaches the static profile, not fully converged at 30,000 s.** Water in the bottom
    0.2 m 0.100 → 0.145 (1,000 s) → 0.187 (5,000 s) → 0.190 at 30,000 s (static 0.188); lower half 0.2425, still
    falling (static 0.2375). Mean |S − exact| 0.0005 (y < 0.15 m), 0.0034 (0.3–0.5 m), 0.0099 (y > 0.5 m), but 0.034
    in the transition band 0.17–0.3 m, which still changes by 1.6e-2 per 250 s. Fig. 6C gradient: median error 8 % for
    S 0.05–0.2 (upper zone), 31–82 % for S 0.2–0.9 (the transition band). Water volume conserved to 3e-8.
  - **Modified (`b995db5`, `darcyFaceMaxDa 0.1`): fails — a cell-to-cell oscillation along the 1-cell-wide column.**
    Roughness max |S_i − (S_{i−1} + S_{i+1})/2| in the lower half: 0.29 at 250 s, 0.34 at 5,000 s, 0.74 at 7,500 s,
    0.89 from 10,000 s (original: 0.01–0.07, from the kink at the edge of the saturated zone). The bottom 0.2 m holds
    0.1004 m of water (unchanged) up to 5,000 s, then 0.101 (10,000 s), 0.115 (20,000 s), 0.131 (30,000 s); mean
    |S − exact| 0.16, Fig. 6C gradient error 150 % to > 1000 %. The earlier reading "frozen" (from t ≤ 5,000 s) was the
    first stage of this odd-even mode, not a stalled state. Water volume conserved to 4e-9. Cause not found; it
    concerns counter-current flow at zero total flux (A, B or C not isolated yet: step 4 of the 2026-10-07 plan).
- **Gravity-driven Buckley–Leverett with the paper's inlet, `verification/BL_grav_BC_FFP` (2026-10-07).** Tutorial with
  `U` fixedValue (1e-5 0 0) + `p` fixedFluxPressure on the inlet (Uwetting/UnonWetting unchanged; fixedFluxPressure
  takes its flux from the U boundary value, so U must be fixed). Predicted: interior flux 1.000e-5, plateau/front change
  < ~0.03 %. **Measured: passes.** Interior flux 1.0000e-5 at every write in both solvers (tutorial inlet: 1.0823e-5),
  continuity error per step ~1e-12 (tutorial inlet: 2.1e-7); plateau 0.4665 (was 0.4663; exact 0.4668); front
  −0.16 % (original) / −0.15 % (modified) at 85,000 s (was −0.13 / −0.12 %); mean |S − exact| 1.1e-3; water stored /
  injected 99.76 % (unchanged: the `+ 0.001` inlet term, not fixed). Port vs modified: mean |ΔS| 1.0e-4.
- Found in the other tutorials before they were dropped (not kept):
  - **B and a fixed-velocity inlet (2026-10-07: diagnosis revised and fix tested).** Flow-driven Buckley–Leverett
    (4.1.1, `U fixedValue 1e-5`, p zeroGradient) with `darcyFaceMaxDa 0.1`: no water enters. `pEqn.H:65` replaces
    `phiHbyA` by the explicit Darcy flux on Darcy boundary faces too, and U_b·S_f only existed in `phiHbyA`;
    `correctUBc.H` takes its "U fixedValue → do nothing" branch, so nothing restores it. Root cause: a fixed U with
    zeroGradient p asks Darcy's law for an inflow with no pressure gradient; the original solver hides this because
    its boundary flux comes from the momentum equation. B exposes it rather than creating it.
    **Fix, no code change: p `fixedFluxPressure` on fixed-U inlets** (`constrainPressure`, `pEqn.H:68`, already gets
    `rAUfD`, so it sets the gradient giving exactly U_b·S_f on a Darcy face). **Kept as `verification/BL_flow_BC`**
    (120,000 s, 2000 cells; only change from the tutorial is that BC; `analyse.py`, reference from the inputs:
    u = 1e-5, S_in = S_max, Welge rarefaction + shock): inlet and interior flux 1.0000e-5 in both solvers; front vs
    analytical (u = 1e-5, S_in = S_max) −0.12 % original, −0.07 % A+B+C; mean |S − exact| 0.0018 / 0.0016; water
    stored/injected 99.986 / 99.984 %; cumulative continuity error −6e-5; S halfway to the front 0.9488 / 0.9487
    (exact 0.9487); front +0.10 / +0.21 % at 30,000 s. Port vs A+B+C: mean |ΔS| 5.7e-4, max 0.19 in the front cell. The original solver gives the same result
    with zeroGradient or fixedFluxPressure, so the BC change does not alter the problem (it deviates from the paper's
    stated ∂p/∂x = 0 at the inlet: say so if used in the thesis). Preferred over excluding fixed-U boundary faces from
    `DarcyFace`, which would mix `rAUf` and `Mf` in the inlet cells (`createPorousMediaFields.H:137–138`).
    The wicking cases fix p at both ends: not affected. Not yet tested: capillary-driven inflow through a Darcy
    boundary face on its own (the yarn reservoir inlet).
  - Flow-driven Buckley–Leverett, port and A+C: front within 0.06–0.3 % of the analytical one.
  - **A+C without B: spurious currents at equilibrium.** Gravity–capillarity equilibrium (4.1.3, Brooks–Corey): cell
    Courant number ~20× the port's, `maxCo 0.01` limits dt to ~4e-3 s (port and A+B+C: 0.1 s). Same cell-velocity
    feedback as part 2 above. (The A+B+C run's small Courant number in this case is not a clean equilibrium: see the
    oscillation above.)
  - Capillary rise (4.2.2, porous walls): all three versions start cleanly (A+B+C to 5 ms); ~330k steps for 5 s,
    not run. With `darcyFaceMaxDa 0.1` the porous walls (K 1e-20) are Darcy faces; air/porous faces are untouched.

- **1D wicking column vs the similarity solution (2026-10-07, `verification/wicking1D/`, `analyseWicking1D.py`,
  `wicking1D.png`).** Reference from the inputs only: with uniform air pressure and no gravity, co-current
  spontaneous imbibition is ε∂S/∂t = ∂x(D ∂S/∂x), D = K kr_w/μ_w |dpc/dS| (BC n 3, VG pc0 5000 Pa m 0.5, K 1e-11,
  ε 0.5), S(0) = 0.99, S(∞) = 0.002; η(S) = x/√t from Philip's iterative integral method (validated on constant D
  against erfc: 1.7e-9). **Prediction: front (S = 0.1) x_f = 18.04 mm/√s·√t, uptake I = 6.105 mm/√s·√t** (front at
  the top at 0.0365 s). Runs: copies of `1D_vertical_impes_inletRes` (impesFoam), `1D_vertical_hybrid` (modified)
  and the same without `darcyFaceMaxDa` + `minDeltaTCoats 1e-7` (original), writes every 1 ms to 0.03 s
  (0.5–4 min each). Slopes vs √t fitted for t ≥ 0.01 s (the 0.2 mm start-up ramp offsets the absolute values):

  | Solver | front slope (mm/√s) | vs 18.04 | uptake slope (mm/√s) | vs 6.105 | inlet cell S (exact 0.99) | max S > 0.2 mm ahead of front, 30 ms |
  |---|---|---|---|---|---|---|
  | impesFoam | 17.95 | −0.5 % | 5.97 | −2.2 % | 0.968–0.976 | 0.015 |
  | hybrid original `be54696` | 17.91 | −0.8 % | 5.84 | −4.4 % | 0.933–0.940 | 0.071 (spurious foot) |
  | hybrid modified `b995db5` | 17.76 | −1.6 % | 5.82 | −4.6 % | 0.932–0.939 | 0.021 |

  **Status: front passes** (all three within 1.6 % of a prediction made from the inputs alone; previously fitted k
  18.35 / 18.03 mm/√s agreed with it). **Uptake: 2–5 % low, explained but not separated:** (a) the inlet cell sits
  below the imposed 0.99 (0.97 impesFoam, 0.94 both hybrids: an inlet treatment of the original hybrid, the same with
  and without the changes), and (b) the reference neglects the air pressure, which varies by ~1.1 kPa along the
  column (≈2 % of the ~50 kPa capillary drive; not decaying between 5 and 25 ms), gravity ρg x_f ≤ 28 Pa. The
  modified solver removes the original's foot ahead of the front (0.071 → 0.021). One mesh (20 µm).
  **Follow-up checks (2026-10-08, no new runs):**
  - **Inlet BCs.** impesFoam: Sb fixedValue 0.99, p fixedValue 0 (Ua fixed 0: water only). Hybrid: alpha.wetting
    inletOutlet 0.99; p (mixture) coded as −α_b pc(α_b), i.e. air pressure 0 and water pressure −pc(α_b),
    consistent with α_b; Uwetting/UnonWetting zeroGradient (relative flux 0 on the face, so 1 % of the inflow is air).
    **The inlet face is at 0.99 in all three runs at every write** (inward face flux), so "the solver reaches a lower
    S_in at the face" is ruled out: a reference recomputed with the face value is the reference above.
  - **Reference self-check:** ε∫η dS = ε∫(S − S0) dη = 6.1048 mm/√s; η ends at 19.50 mm/√s.
  - **Where the uptake deficit sits** (ε∫(S_exact − S_run) dx at 30 ms): inlet zone x < 0.2 mm 1.9 / 4.8 / 4.9 µm
    (impesFoam / original / modified), profile body 19.5 / 53.3 / 50.6 µm, front ±0.3 mm −4.3 / −5.3 / +1.7 µm; total
    17 / 52 / 57 µm of 1057 µm (1.6 / 4.9 / 5.4 %). The body of the profile is uniformly low, as for a lower
    effective inlet saturation. (The 6–10 % "uptake since t = 0" deficits at 30 ms are mostly the start-up offset: the
    runs start with 50 µm of water in the ramp; use the √t slopes.)
  - **Effective inlet saturation:** the first cell centre is 0.974 (impesFoam) / 0.938 (both hybrids) where the exact
    profile gives 0.989. A reference with S_in = first-cell value overcorrects: runs then 3–8 % faster (front) and
    5–15 % more uptake. The run uptake slopes match S_in ≈ 0.984 (impesFoam) / 0.976 (hybrids) by interpolation: the
    uptake is very sensitive to S near 1, where D(S) peaks (ΔS_in = −0.01 → about −2 % uptake). So the deficit sits in
    the inlet half-cell (face 0.99 → cell 0.94–0.97), i.e. in the discretisation of the inlet flux, plus the
    neglected air pressure. **Status: numerical (inlet half-cell) + reference (air pressure), not separated; needs a
    1D mesh study** (Δx/2, Δx/4).
  - **Front resolution:** Δx = 20.0 µm, 172 cells; front at 64–67 cells (5 ms) to 155–158 cells (30 ms); width
    S 0.3 → 0.02 = 15–33 cells for impesFoam and the modified hybrid (exact 11–28 cells), 26–39 cells for the original.
  - **Phase pressures and inlet-face fluxes** (`verification/wicking1DPressures.py`, `wicking1D_pressures.png`, existing
    output). impesFoam `p` is the air pressure (`phia = phi − phib = −Ma∇p`, `phib = −Mb∇(p − pc)`); hybrid
    p_g = p + α pc. Air pressure is raised through the whole wet zone and decays smoothly to 0 at the outlet: maximum
    1.06–1.14 kPa in the first cell of both hybrids, 0.61–0.81 kPa at 0.05–0.15 mm in impesFoam (its face is held at
    p_g = 0); 160 Pa (5 ms) / 20 Pa (25 ms) at the front. **Hybrid inlet face: 1.00 % of the inflow is air, inward**
    (both hybrids, 5 and 25 ms; α_face 0.99, relative flux 0 on that face). Inlet water flux vs the exact uptake rate
    S/(2√t): hybrids 4.09e-2 / 1.84e-2 m/s at 5 / 25 ms (−5.3 / −4.5 %), impesFoam 4.23e-2 / 1.90e-2 (−2.1 / −1.8 %),
    matching the uptake-slope deficits. impesFoam's face water flux uses the point pc′(0.99) (−38,050 Pa): with the
    true water-pressure jump across the half cell (secant) it would point outward (−0.19 / −0.10 m/s): its first-cell
    state is set by that face formula. impesFoam air flux on the inlet face: −0.08 to −0.12 % (outward).
  - **Runs 2026-10-08 (`verification/wicking1D/{impes_muA100,ABC_muA100,ABC_waterInlet}`, `wicking1DVariants.py`),
    predictions written before the runs, both confirmed:**

    | Run | front slope | vs 18.04 | uptake slope | vs 6.105 | first-cell S (exact 0.989) | inlet air / total | p_air first cell, 25 ms |
    |---|---|---|---|---|---|---|---|
    | impesFoam | 17.95 | −0.5 % | 5.970 | −2.2 % | 0.974 | — | 529 Pa |
    | impesFoam, μ_air/100 | 18.01 | −0.2 % | 6.086 | −0.3 % | 0.989 | — | 3 Pa |
    | hybrid modified | 17.76 | −1.6 % | 5.824 | −4.6 % | 0.938 | +1.00 % (in) | 1064 Pa |
    | hybrid modified, μ_air/100 | 18.04 | −0.0 % | 6.087 | −0.3 % | 0.984 | +0.99 % (in) | 173 Pa |
    | hybrid modified, inlet `UnonWetting` fixedValue 0 | 17.89 | −0.8 % | 5.943 | −2.6 % | 0.969 | −0.43 % (out) | 489 Pa |

    (1) **μ_air/100** (prediction: first cell → ~0.99, uptake within ~1 %): both solvers within 0.3 % (uptake) and
    0.2 % (front) of the reference. **Status: the base-run gap is the reference's uniform-air-pressure (Richards)
    assumption, i.e. the physical air back-pressure, not numerics; both solvers verified against the similarity
    solution on the 20 µm mesh with that effect switched off.** (2) **Water-only inlet** (prediction: the hybrid moves
    to impesFoam): uptake −4.6 → −2.6 % (impesFoam −2.2 %), first cell 0.938 → 0.969; air now leaves through the inlet
    (0.43 % of the flux, outward; impesFoam 0.1 %). **Split of the hybrid's −4.6 % uptake:** ~2 % from the 1 % air
    injected by its inlet BC, ~2.5 % physical air back-pressure (in impesFoam too), ≤ 0.3 % numerics on this mesh
    (not established: one mesh only, errors could cancel). Wall time 73 s (impesFoam μ/100), 283 s (water inlet),
    513 s (hybrid μ/100).
  - **Run 2 checked (code + output, 2026-10-08): `UnonWetting` fixedValue 0 does not make the inlet water-only.**
    Solver: modified `b995db5`, `darcyFaceMaxDa 0.1` (log: Darcy faces 171/171 internal, 2/2 boundary). The total face
    flux φ comes from the pressure equation (B's Darcy flux with both mobilities); nothing in `pEqn.H` reads
    `UnonWetting`, and `correctUBc.H` imposes (Uwetting + UnonWetting)·Sf only when `Uwetting` is fixedValue. The
    fixed `UnonWetting` only enters the boundary relative flux in `alphaEqn.H`: water flux on the face =
    α_b φ + α_b(1 − α_b) ε Uw_cell/(ε α_b + 0.001), with `Uwetting` zeroGradient (first-cell water velocity). This
    reproduces the run's face water flux to 3e-5 of the total (1.88068e-2 vs 1.88071e-2 m/s at 25 ms). The cell
    water velocity exceeds the face total flux, so water > φ and air leaves: 0.58 % (5 ms), 0.43 % (25 ms) outward.
    The `+ 0.001` term is active there but changes the water flux by 3e-5 of the total (× (1 − α_b) = 0.01). So run 2
    swaps "1 % air in" for "~0.5 % air out"; a truly water-only reservoir inlet is not yet available as a BC
    (candidate, untested: `Uwetting` fixedValue as well, so that `correctUBc.H` sets φ; that needs the inflow
    velocity, which is unknown for spontaneous imbibition).
  - **Code read, inlet α_b = 1 instead of 0.99 (2026-10-09, no runs).** Hybrid (original and modified): the face α
    flux is α_b φ + flux(−flux(−phirPore, α2 ε), α) (`alphaEqn.H:254`, α2 = 1 − α, l. 220/322), so with α_b = 1 the
    relative term is multiplied by α2_b = 0 and **the face carries water only in the α equation, exactly, whatever
    `phirPore`, `UnonWetting` or the `+ 0.001` term** (l. 147–159). The pressure equation agrees: C's
    `upwind(...).interpolate(kr)` returns the patch value on a boundary face, kr_a(α_b = 1) = 1e-12 (Se clipped to
    1 − 1e-4, `krBrooksAndCorey.H:123–124`), M2f/M1f = 5.7e-11 (4.3e-5 at 0.99). The hybrid libraries clip Se
    (`pcVanGenuchten.H:106–107`), so α_b = 1 is finite: pc_b = 70.7 Pa (not 0), dpc/dS = −3.5e5 Pa; the coded inlet p
    gives a face water pressure of −70.7 Pa (−676 Pa at 0.99). MULES bounds α to [0, 1], so α_b = 1 is allowed
    (`alpha.wettingmax 0.999` is a closure range, not a bound). **Consequence: the reference changes too**: with the
    same clipped closures, S_in = 1 gives front 19.27 and uptake 6.933 mm/√s (+6.8 %, +13.6 % vs 0.99), and the
    numbers depend on the 1e-4 clip, since pc′ diverges at Se = 1. impesFoam cannot take Sb_b = 1 with Sbmax 0.999:
    its libraries do not clip Se (`pcVanGenuchten.H:88–89`, `krBrooksAndCorey.C:135–137`), so Se = 1.001 gives
    pc = pc0·(negative)^0.5 = NaN (SIGFPE) and kr_a < 0; it needs Sbmax > 1 in both coefficient dicts (Sbmax = 1
    exactly makes dpc/dS infinite on the face).
    Still open (not run): 1D mesh study at the real air viscosity (Δx/2, where impesFoam's inlet flux depends on its
    point-pc′ face formula); C alone (be54696 + patches 0003, 0005) for the tail.
  - **Tail ahead of the front** (water > 0.2 mm ahead): original 2.0 → 5.8 µm from 5 to 25 ms (grows), impesFoam and
    modified ≤ 0.5 µm. Consistent with the hypothesis that linear kr lets water leak into dry cells and upwinded kr
    (change C) blocks it; C alone not tested (needs a be54696 + C build).
- **The equilibrium oscillation does not appear in the wicking runs (2026-10-07, `verification/scanOddEven.py`,
  `oddEvenScan.png`).** Scan of every write for cells that are strict local extrema of S (above or below all face
  neighbours) by > 1e-3. Positive control `eq_BC`: modified 750 extrema (median, of 1500 cells), amplitude 0.90;
  original 62 (median), up to 0.10 near the kink of the profile. Wicking runs, 0.005–0.1 s: `1D_vertical_hybrid` 1
  extremum (impesFoam twin 2), max amplitude 0.016 (0.024); `singleYarn_vertical_hybrid` at most 12 of 15,188 cells
  (0.08 %), amplitude ≤ 6.4e-3, the same level as the impesFoam twin (11, 5.9e-3). **Thesis sentence:** the odd-even
  mode is observed in counter-current flow at zero total flux (paper 4.1.3) and is absent from our co-current wicking
  runs, checked by a local-extremum scan of every saturation field against the impesFoam twins. It would need
  rechecking for configurations that trap air (counter-current flow), e.g. the fabric case. The original-solver 1D run
  (`results_oldsolver/`) keeps only profiles and is not in the scan.

### Is change B needed, or is ddtCorr the cause? (2026-10-07, `verification/bench_ddtCorr/`)
- **Hypothesis tested:** the transverse instability without B comes from the ddtCorr term of `phiHbyA`
  (`pEqn.H`: `fvc::interpolate(rho*rAU())*fvc::ddtCorr(U, phi, Uf)`), which carries cell-velocity noise into the
  face fluxes and grows as dt shrinks. **Status: fails (rejected).**
- **OF9 has no `ddtPhiCoeff` keyword** (that is the openfoam.com line). The coefficient is hard-coded in
  `ddtScheme<Type>::fvcDdtPhiCoeff` (`src/finiteVolume/finiteVolume/ddtSchemes/ddtScheme/ddtScheme.C:152`, "flux
  normalised": 1 − min(|φ_corr|/|φ|, 1), 0 on non-coupled boundaries) and used by `EulerDdtScheme.C:460–483`.
  So the test variant multiplies the whole term by `ddtCorrCoeff` read from `PIMPLE` (default 1): scratch build of
  `b0c0f67` (original + A, linear kr, no B) + `bench_ddtCorr/variant_A_ddtCorrCoeff.patch`.
- **Bench:** the 1D column (0.55 × 3.446 × 0.237 mm) as 5 × 172 × 3 cells, symmetry on the 4 lateral faces, inlet ramp
  uniform across the width, fixed dt 1e-7 (the original's 1D floor, below the ~3.4e-7 Coats limit), 2e-4 s; a coded
  function object prints per step the max over rows of (max − min α across the row). Case in
  `bench_ddtCorr/case/`, logs `bench_ddtCorr/log.*.gz`, table and figure `benchDdtCorr.py`.

  | Run | steps | end | spread at step 2 | time spread > 1e-2 | growth/step (1e-5..1e-2) | rate (1/s) | max transverse abs(U) | pass (≤ 1e-6 to 2e-4 s) |
  |---|---|---|---|---|---|---|---|---|
  | (i) original `be54696` | 351 | crash 3.51e-5 s | 4.9e-5 | 6.7e-6 s | 1.083 | 8.0e5 | 1.4e80 | FAIL |
  | (ii) original + A, ddtCorr × 1 | 2000 | 2e-4 s | 2.9e-5 | 9.4e-6 s | 1.064 | 6.2e5 | 1.8 m/s | FAIL (spread 0.05–0.2) |
  | (iii) original + A, ddtCorr × 0 | 2000 | 2e-4 s | 2.9e-5 | 7.2e-6 s | 1.075 | 7.2e5 | 0.93 m/s | FAIL |
  | (iv) original + A, ddtCorr × 0.1 | 2000 | 2e-4 s | 2.9e-5 | 7.5e-6 s | 1.083 | 8.0e5 | 0.98 m/s | FAIL |
  | (v) modified `b995db5`, `darcyFaceMaxDa 0.1` | 2000 | 2e-4 s | 2.5e-10 | never | — | — | 1.3e-6 m/s | PASS (max 1.3e-7) |
  | (e) = (iii) with dt 5e-8 | 4000 | 2e-4 s | 9.0e-6 | 4.9e-6 s | 1.438 | 7.3e6 | 6.3 m/s | FAIL |

- **Results (measured):** the ddtCorr coefficient (1, 0.1, 0) changes neither the growth (6–8e5 1/s) nor the time to
  reach 1e-2 (7–9 µs); without ddtCorr it is slightly faster, not slower. Halving dt with ddtCorr off still makes the
  growth ~10× faster per unit time (7.3e6 vs 7.2e5 1/s), so the dt sensitivity is not carried by ddtCorr. The original
  reproduces the old divergence (crash at 3.51e-5 s; records: 3.5–3.9e-5 s). With A, no B, the runs do not crash within
  2e-4 s but saturate at a transverse spread of 0.05–0.2 (not acceptable). Only B keeps the spread ≤ 1.3e-7.
- **The step-2 jump is the loose pressure solve.** The spread is ~1e-15 after step 1 and jumps in step 2 to 3e-5
  (5e-5 original, 9e-6 at dt 5e-8; 2.5e-10 with B). With p solved to tolerance 1e-12, relTol 0 (T2a GAMG, T2b PCG+DIC;
  default is GAMG 1e-6 / relTol 0.1) the step-2 value drops to 2.4e-9. **But the mode still grows** (1.09e6 1/s,
  1e-2 reached at 1.14e-5 s instead of 9.4e-6 s) and saturates at 0.14–0.16: the loose solve only provides a large
  seed; the instability is in the formulation without B, not in the solver tolerance. Status: established.
- **Inertia hypothesis: rejected.** The idea was that the porous-cell momentum equation is inertia-dominated at these dt
  (ρ/Δt 1e10 vs drag 1e8 for water, 1e7 vs 1.8e6 for air at Δt 1e-7) and lags the Darcy limit, so removing inertia
  should help. Test on original + A: T1a `ddt(rho,U) steadyState` crashes at 1.37e-5 s (137 steps), T1b the same with
  ddtCorr × 0 crashes at 7.1e-6 s (71 steps; growth 2.98/step); with inertia (ii) runs to 2e-4 s. Removing inertia
  makes it much worse, as the old record said. "Removing inertia" back then meant the ddt term only
  (`ddt(rho,U) steadyState`, record above); convection (`div(rhoPhiByEps,U)`) was kept, as here. A side hypothesis
  (the old test was flawed because ddtCorr keeps its own `ddt(U)` Euler scheme and grows by ρ/(Δt·drag) when rAU
  becomes 1/drag) is also rejected: T1b removes ddtCorr too and crashes even earlier.
- **Conclusion: B is needed.** Neither ddtCorr, nor inertia, nor the pressure-solver tolerance is the cause; without B
  the transverse mode grows from any seed at ~6e5–1e6 1/s (×1.06–1.12 per step at Δt 1e-7) and saturates at 0.05–0.2
  or diverges. The mechanism beyond "the momentum-equation flux in porous faces feeds it, the Darcy flux does not" is
  not established; per 2026-10-07 decision, no further digging. Logs: `bench_ddtCorr/log.T1*`, `log.T2*`; figure
  `bench_ddtCorr/bench_inertia_psolver_spread.png`.

### Physics
- pc0 = 5000 Pa is consistent with K = 1e-11 by Leverett scaling (about 4–8 kPa); the 1D value of 100 Pa corresponds to millimetre pores and is not realistic for a yarn.
- The wicking rate constrains K·pc0; the equilibrium height (pc0/ρg, about 0.5 m here) constrains pc0. A 3.2 mm segment only shows the rate, so fitting K and pc0 needs experimental-length samples.

## Running

```bash
cd singleYarn_IMPES_vertical
nohup ./run > run.out 2>&1 &
grep "^Time =" log1.impesFoam | tail -1     # progress
```

- **Solver logs are written in `/tmp`, not in the case folder** (`runTmpLog` in `runTools.sh`; see `CLAUDE.md`): `log1.impesFoam` is a symlink during the run and the real file afterwards. For a long run use `LOG_EVERY=100 nohup ./run > run.out 2>&1 &`, which keeps only every 100th step plus the last 400 lines (`log1.impesFoam.tail`).
- **If the run dies, do NOT rerun `./run`:** it deletes meshes, processor folders and results. Instead, set `startFrom latestTime` in `system/controlDict`, relaunch with `nohup mpirun -np 4 impesFoam -parallel -noFunctionObjects > /tmp/log2.impesFoam 2>&1 &` (log outside the workspace), then run `reconstructPar` and `postProcess -func sampleDict`.
- **Cluster (mini01, SLURM):** each yarn case has a `job.slurm` (4 tasks, 10 GB, `global` partition; 24 h impesFoam,
  72 h hybrid). Submit from the case folder with `sbatch job.slurm` (decided 2026-10-02: the jobs then run in parallel
  with the others) after checking with `squeue -o "%.10i %.12u %.15j %.2t %.10M %.5C %R"` that the running jobs leave
  CPUs free (48 in all; the partition oversubscribes, so a full machine slows everyone down). `../slurmSubmit.sh` is
  the mini01 guide's procedure (section 5: wait behind every active job). Never `./run` or `bash job.slurm` there. The job
  checks that `N` in `caseSetup` equals `--ntasks`, and runs `LOG_DIR=logs LOG_EVERY=100 ./run`. Both solvers must be
  built on mini01 from the `of9-port` branches (OpenFOAM 9, `/opt/OpenFOAM-9`); set `--mail-user` before submitting.
  `./Allwmake` stops at `groundwater2DFoam` (does not compile on OF9) before reaching `impesFoam`: run `./Allwclean`,
  `wmake` the five `libraries/*` in `Allwmake` order, then `wmake solvers/impesFoam`. impesFoam built this way on
  mini03, 2026-10-02.
- **Laptop:** set "lid close → Do nothing" and "sleep → Never" while plugged in. WSL2 may also shut down when no WSL window is open.
- **Front analysis:** `wickingFront.ipynb` (also shows `1D_vertical_hybrid` with the old solver, `results_oldsolver/`) loads the 1D cases' `postProcessing/sampleDict` profiles and `liquidBalance.csv`, takes the front as the height where S = 0.1 and compares it with Lucas–Washburn (h = k√t, k fitted). Kernel: the repo's `.venv` (`matplotlib` and `ipykernel` added to `requirements.txt`). Current runs: k = 18.35 mm/√s (impesFoam), 18.03 (hybrid, new solver; 18.23 with the old one, whose profiles had a staircase and a spurious foot ahead of the front), h/√t constant within 2 %.
- **Outputs:** `liquidBalance.csv` (uptake over time) and `postProcessing/sampleDict/<t>/alongYarn_Sb.xy` (Sb(x) profiles).

## Next steps

1. Analyse the 0.1 s run: front position over time, uptake, Sb(x) profiles.
2. Cheap speed-ups: `maxCo 0.9` (about 1.8×); benchmark 1, 2 and 4 cores; `DIC` or `GAMG` instead of `diagonal` PCG for p; check whether the maximum Coats CFL sits in the tiny snapped cells.
3. **Main lever:** replace the snappy mesh with a mesh that follows the yarn (a Python generator writing a swept `blockMeshDict` from STL slices, about 100 µm axial cells), or a 1D model over the centreline length. This enables cm-long samples to compare with experiments.
4. Report the Todd bug upstream (phorgue/porousMultiphaseFoam) or patch the fork, and commit the fork's local changes (`setDeltaT.H`, `updateLiquidContent.H`, `Make/files`).
5. Fabric scale: `hybridPorousInterFoam` on a Cartesian unit cell with the yarns as a porosity field. The yarn mesh does not carry over, but the calibrated K/kr/pc do; check that its kr and pc models match.
