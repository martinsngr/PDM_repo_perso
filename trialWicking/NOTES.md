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
- **Changes A (face relative flux), B (opt-in Darcy total flux, `darcyFaceMaxDa`) and C (upwinded kr) are logged with patches in `hybridSolverChanges/`** (committed on `of9-port` 2026-10-01: A `b0c0f67`, B `cf95c59`, C `b93e429`, B fix `c0c1b4e`, C fix `b995db5`; the installed solver is `b995db5`). Bench stable (5 ms, spread ≤ 4e-7); 1D uptake within 0.5 % of the original hybrid. A porous/free interface with a wet porous side diverges in the original solver too: next problem before the fabric case.
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
- **Gravity–capillarity equilibrium, Brooks–Corey (paper 4.1.3), running (`verification/eq_BC`)**: tutorial =
  paper's Fig. 6 setup (pc0 1000 Pa: Fig. 6C's analytical |dS/dy| at S = 1 is 19.5 1/m = Δρg/(β pc0); Table 2's
  p0 100 Pa would give 196). Reference from inputs only (`analyseEquilibrium.py`: Fig. 6C relation, and the static
  profile holding the initial 0.25 m of water). **Preliminary (t = 4,500–5,000 s of 30,000): with Darcy faces on,
  the column does not drain.** Port: bottom at 0.997 by 1,000 s, mean |S − static| 0.18 → 0.03. A+B+C: profile
  frozen near the initial step (S ≈ 0.51 in the lower half), mean error 0.20 throughout, although the cell phase
  velocities show counter-current drainage (Uwetting −2.3e-5, UnonWetting +2.5e-5 m/s). So the α face fluxes
  (change A, `phirPore`) do not carry counter-current gravity segregation with B on; cause not found yet. The
  "round-off Courant number" of A+B+C in this case (below) is this frozen state, not a clean equilibrium.
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
    feedback as part 2 above.
  - Capillary rise (4.2.2, porous walls): all three versions start cleanly (A+B+C to 5 ms); ~330k steps for 5 s,
    not run. With `darcyFaceMaxDa 0.1` the porous walls (K 1e-20) are Darcy faces; air/porous faces are untouched.

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
