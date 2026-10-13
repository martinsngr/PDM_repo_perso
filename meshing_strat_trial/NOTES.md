# meshing_strat_trial — working notes

Fabric REV (several yarns + the gaps between them) with `hybridPorousInterFoam`: vertical wicking from a
saturated inlet, capillary drive only. Follows the 1D and single-yarn hybrid cases of `../trialWicking`
(see `../trialWicking/NOTES.md` for their setup, solver changes A/B/C and verification).
Last updated 2026-10-13 (session 2: thick-wall slit bench, scratch changes H, F′, I). **Start next session at "Next steps".**

## Folder layout

| Path | What it is |
|---|---|
| `REV/` | **The REV, in one folder** (merged 2026-10-13 from `REV_hybrid/` and the meshing files that were at the top level): geometry `Textiles/PW-22-15-0.4-0.5.stl` + `features.csv` (TexGen script `funge.py`; copy in `constant/triSurface/`), `inspect_stl.py` (STL checks, REV box → `rev_domain.json`, `--zgap` adds free space), `build_fields.py` (uniform hex mesh `system/blockMeshDict` + `eps`, `K`, `fYarn`, `yarnID`; STL and `rev_domain.json` found next to the script), `check_periodicity.py`, ParaView state `meshing.pvsm`; solver dictionaries `system/`, `constant/`, `0.orig/`; `./Allpre` = geometry → mesh → fields → initial α. Solver run scripts not written yet. The original meshing trial outputs (tensor K, fractional cut cells, top-level `0/`, `system/`) were removed: regenerate with `build_fields.py <dir> --k-mode tensor --cut-cells fractional` (also in git history before 2026-10-13). |
| `tools/` | Shared by both cases: `runTools.sh`, `initFields.py`, coded BC `pOpenAir`, function objects `coatsTimeStep`, `liquidBalance` |
| `2D_bench/` | **The 2D bench (since 2026-10-13): thick-wall slit**, yarn wall 8 cells \| gap 8 \| yarn wall 8, H + F′ + I on; `check.py` = expected-behaviour checks |
| `2D_bench_strip/` | The first 2D bench (2026-10-12, was `2D_bench/`): porous strip between two open free layers, with `variants/` (debugging runs, referees R1–R3) and their results; template of `slit_test/makeSlit.py` |
| `slit_test/` | Slit capillary-rise tests (gap capillarity): `makeSlit.py` (defaults = validated setup; `--nw/--dx/--add` for the thick-wall bench), `slitReport.py`, `benchSlit.py` (thick-wall bench), `figures/`; `old_runs/` = superseded runs (see "Slit tests") |
| `.gitignore` | generated files of the cases (`0/`, variant runs, `liquidBalance.csv`); logs, polyMesh, time folders are in the repo-root `.gitignore` |

Case layout (both cases): source fields in `0.orig/`; `./Allpre` copies them to `0/` and writes the generated
fields there (eps, K, alpha.wetting), so `0/` is never edited by hand and not committed. The face-flux debug
tooling of the solver lives with the solver change log: `../trialWicking/hybridSolverChanges/debug_faceDump/`.

## Decisions (2026-10-12)

- **Properties are setup values, not calibrated.** Same as the single-yarn cases: K = 1e-11 m² (scalar),
  eps 0.5 in the yarns (VF_YARN 0.5), Brooks–Corey n 3, Van Genuchten pc0 5000 Pa, m 0.5, water/air.
  Real K (tensor), pc and contact angle come later.
- **Cut cells: `binary`** (f ≥ 0.5 → yarn, otherwise free fluid). A sharp yarn surface, the most robust
  option for a first run.
- **Gravity along x** (vertical wicking): g = (−9.81 0 0), inlet = x-min.
- **Contact angle: solver default** (`activatePorousContactAngle 0`; `theta0` 90° would apply when switched on).
- **BCs:** inlet = reservoir over the whole x-min face; outlet (x-max), top and bottom (z) open to air;
  y cyclic (symmetry of interest is in the fabric plane).
- **Mesh:** keep 20 µm (169k cells) for now. Number of cores: after local smoke tests show the case is stable.
- **Staged approach:** first the 2D bench (porous/free interface, cheap), then the REV.

## What was done

### `build_fields.py` (changed)
- **Porous/free classification aligned with the solver.** The solver treats a cell as porous when eps ≤ 0.99
  (`createPorousMediaFields.H`). Before, K followed `f ≥ 0.5` while eps was fractional: **13,974 cells were
  porous for the solver (so they got pc) but had K = 1 m²** (no drag, not Darcy faces), all on the yarn
  surfaces. Now every cell with eps ≤ `EPS_FREE` (0.99) gets the yarn K and every other cell gets `K_VOID`.
  This also changes the tensor output of the top-level trial if it is rebuilt.
- **New options** (command line or CONFIGURATION block):
  `python3 build_fields.py [caseDir] --k-mode scalar|tensor --k-scalar 1e-11 --cut-cells binary|fractional`.
  Scalar mode writes a `volScalarField` K (what `hybridPorousInterFoam` reads). Defaults are unchanged
  (tensor, fractional), so a plain run from the top level reproduces the original trial (with the fix above).
- STL and `rev_domain.json` are now found relative to the script folder, so it runs for any case folder.
- The summary prints the porous/free cell counts and the solid volume.
- **Not run yet** with the new options.

### Original REV fields (top-level `0/`, before the change)
91 × 133 × 14 cells (20 µm), 1.82 × 2.67 × 0.28 mm, 169,442 cells: 45 % free (eps 1), 37 % full yarn
(eps 0.5), 18 % cut cells. Free fraction per z layer 0.86 (bottom) → 0.15 (middle) → 0.91 (top): the
layers next to the z patches are mostly the open space beside the crimped fabric, not inter-yarn gaps.
Inlet/outlet faces are 25 % free.

### Solver facts that shaped the setup (code read, `of9-port` `b995db5`)
- **Free cells:** `Drag = average(Dragf)*Solid` → no drag in free cells, so K_VOID only matters on
  porous/free faces (via interpolated K). Phase velocities `Uwetting`/`UnonWetting` = `Solid*M*(...)` → **0
  in free cells**.
- **Consequence for the open patches:** the 1D outlet BC (`Uwetting` fixedValue 0) makes `correctUBc.H`
  impose (Uwetting + UnonWetting)·Sf on the whole patch, i.e. **it closes the free-fluid faces of the
  patch**. All open patches therefore use `Uwetting`/`UnonWetting` zeroGradient (flux from the pressure
  equation, no relative flux on the patch), `U` pressureInletOutletVelocity, α inletOutlet. Difference from
  the agreed "outlet as in 1D": water is no longer blocked at the outlet's porous faces (matters only once
  the front reaches x-max).
- **p is the mixture pressure** p_air − α·pc(α). Across an interior porous/free face (Solidf = 0, momentum
  equation, no pc term) the solver makes p continuous. On a dry yarn (α 0.002) α·pc ≈ 5 kPa, so the 1D rule
  "air at 0 Pa on the patch" (p = −α·pc) contradicts what happens at every interior yarn/gap face (p ≈ 0).
  Kept as a switch (`openPorousAirZero` in `transportProperties`, see `tools/pOpenAir`), to be tested on the
  bench. Note also α·pc(α) ~ pc0/α for VG m 0.5, so the dry value S_dry (0.002) sets this offset.
- **Coats time step in free cells is meaningless** (K = 1 m² would collapse dt): the function object now
  evaluates it on porous cells / porous faces only, and adds the capillary-wave limit of the free surface.
- **Darcy faces** (`darcyFaceMaxDa 0.1`): yarn faces K/dx² = 0.025 → Darcy; free and porous/free faces not.
- **Porous contact angle** (`porousInterfaceProperties.C`): off by default; when on, it corrects the
  interface normal at porous surfaces (`correctContactAngleDB`, angle `theta0`).

### `tools/` (new)
- `runTools.sh`: copy of `../trialWicking/runTools.sh` (solver log in /tmp, `LOG_EVERY`, `LOG_DIR`).
- `initFields.py` (numpy only): writes `0/alpha.wetting` from `0/eps` + `0/C`. Every cell dry at 0.002
  (porous and free, so no α jump at the yarn surface at t = 0). Porous cells within 0.2 mm of the inlet get the
  10-band ramp 0.99 → 0.002, as in 1D. Free cells near the inlet stay dry. Inlet inletOutlet with a per-face
  `inletValue`: 0.99 on porous faces, 1 on free faces (reservoir). Other open patches inletOutlet 0.002;
  constraint patches keep their type. Inlet normal and plane detected from the mesh. `--ramp 0`: no ramp
  (sharp start); `--s-dry`: dry value.
- `pOpenAir`: one coded p BC for all open patches. Free faces p = 0; porous faces −α·pc(α)
  (`openPorousAirZero 1`, default) or 0. Included in `0/p` with `#include "../../tools/pOpenAir"`.
- `coatsTimeStep`: from `singleYarn_vertical_hybrid`, plus porous-only Coats/dSmax and the capillary-wave
  limit dt < CapillaryMaxCo·√(ρ̄ dx³/(2πσ)) (1.5e-6 s here), skipped without free cells or with σ = 0
  (it divided by σ: SIGFPE, fixed 2026-10-12). Prints dtCoats, dtdS, dtCap.
- `stopGuard`: writes and ends the run after `maxSteps` steps or when dt < `minDeltaTStop` (controlDict; bench
  and REV: −1 and 1e-14). Avoids the 50,000-step / 50 MB logs of a collapsed dt.
- `liquidBalance`: same 4 columns as trialWicking + `porousLiquid_mL`, `freeLiquid_mL`, `meanSaturationPorous`.

### `2D_bench/` (thick-wall slit bench, 2026-10-13)
- Same case as `slit_test/makeSlit.py --walls porous --nw 8 --w 8 --K 1e-11 --theta 60` with the H/F′/I keywords
  (decided with the user: the bench should match the slit build), as a standalone case: 2.0 × 0.48 mm, 100 × 1 × 24
  cells (20 µm); yarn walls z < 0.16 and > 0.32 mm (eps 0.5, K 1e-11, ending 3 cells before the outlet), gap 8 cells;
  `inlet` reservoir (total pressure for free faces, `openFreeTotalPressure 1`), `outlet` open, `top`/`bottom` closed
  walls behind the yarn walls; contact angle on, 60°; `porousFreeDarcyFaces`, `porousContactAngleWallLike`,
  `porousFreeFluxForce`, `porousFreeNoSlip` on. Initial state: walls dry with the 0.2 mm ramp, gap air with a 0.1 mm
  water column (`initFields.py --closed-patch top --closed-patch bottom --free-fill 1e-4`, new options). 2 ms.
- `./Allpre` → `./run` (serial, ~3 min) → `../../.venv/bin/python check.py` (writes `check_summary.md`,
  `check.png`; exit 1 if a check fails).
- **First run (2026-10-13, installed `b525086`) — measured:** fields at 2 ms bit-identical to the slit run
  `slit_test/V_w8_t60_K1e-11` (same mesh, ε, K, initial α); all 10 checks pass: 2 ms reached, budget 5e-15, max |U|
  1.2 m/s, no stray water; gap meniscus 0.43 / 0.79 mm at 1 / 2 ms (impermeable walls, Bosanquet: 0.63 / 1.16); wall
  front 0.75 / 1.15 mm (walls alone, 1D similarity: 0.60 / 0.83), uniform across the wall within 1 cell; wall water
  41 → 369 cell volumes. **The walls lead the gap** (wall front 0.36 mm ahead of the meniscus at 2 ms): the walls
  draw water out of the gap (meniscus 32 % below the impermeable rise) and are fed sideways along the wetted gap.
  The meniscus first drops (0.11 → 0.09 mm, the column feeds the walls), then rises about linearly in t.

### `2D_bench_strip/` (first bench, 2026-10-12; was `2D_bench/`, renamed 2026-10-13)
- Kept with its variants and results; paths in the sections below that say `2D_bench/variants/` now are
  `2D_bench_strip/variants/`. `slit_test/makeSlit.py` uses its `system/`, `constant/`, `0.orig/` as template
  (unchanged, so slit results stay reproducible).
- 1.0 × 0.3 mm (x–z), 50 × 1 × 15 cells (20 µm, as the REV); `frontAndBack` empty. Porous slab z 0.06–0.22 mm
  (8 cells, eps 0.5, K 1e-11, `setFieldsDict`), free layers below (3 cells) and above (4 cells).
  Patches and BCs as the REV: `inlet`, `outlet`, `bottom`, `top` open. 750 cells (400 porous, 350 free); 742
  of 1435 internal faces are Darcy faces.
- `./Allpre` (copies `0.orig` to `0`, blockMesh, checkMesh, setFields, cell centres, `initFields.py`) → `./run`
  (serial) → `./clean` (results only; time folders matched by name, `0` and `0.orig` kept). Mesh OK. Initial and boundary α checked.
- `system/controlDict`: endTime 5 ms (1D estimate: front at 1 mm after ~3 ms), write every 0.25 ms, Coats
  settings as the single-yarn case, `stopGuard`. fvSchemes/fvSolution copied from `singleYarn_vertical_hybrid`.
- **`variants/`: test bench for the debugging** (see Findings).
  - `./makeVariant.sh <variant> steps [N]` runs N steps (default 10) with the fields written at every step;
    `./makeVariant.sh <variant> run [T]` runs to T (default 2e-4 s), writing every T/10.
    Each variant is a copy of the bench with ONE change, in `variants/<variant>_<mode>/`; open
    `<variant>_<mode>.foam` in ParaView. `variant.diff` shows the change actually applied (check it!).
    The list of variants is at the top of the script. `dynamicCode` is deleted after the run; big logs are gzipped.
  - `../../../.venv/bin/python analyseVariants.py steps|run` writes `variants/figures/<mode>_alpha.png`
    (α maps at t = 0, step 1 or first write, last write), `<mode>_p.png` (p maps, symlog), `<mode>_dt.png`
    (dt per step) and `<mode>_summary.md` (table).
  - `variants/tools` is a symlink to `../../tools`, so the `#include "../../tools/..."` still work one level deeper.

### `REV/` (was `REV_hybrid/`; merged with the meshing files 2026-10-13; solver run not set up yet)
Present: `system/{controlDict, fvSchemes, fvSolution}`, `constant/{transportProperties, g, momentumTransport,
dynamicMeshDict, triSurface/}`, `0.orig/{p, U, Uwetting, UnonWetting}` (cyclic sideA/sideB via `setConstraintTypes`),
the geometry and meshing scripts, `Allpre` and `clean`. **`./Allpre` (tested 2026-10-13, 20 s):** `build_fields.py .
--k-mode scalar --k-scalar 1e-11 --cut-cells binary` → blockMesh → checkMesh (169,442 cells, Mesh OK) → cell centres →
`initFields.py` (78,528 porous, 90,914 free; inlet 1,862 faces, 1,262 porous; 9,325 ramp cells). Missing: `run`
(decompose, serial precompile of coded BC/FOs, mpirun), `caseSetup` (N), `decomposeParDict`, `job.slurm`, endTime;
setup decisions listed at the top of `Allpre` (top/bottom, gap water column, H/F′/I keywords, contact angle).

## Findings

### Bench smoke test 1 (2026-10-12): fails at the first step
Setup as above, `openPorousAirZero 1`, contact angle off.
- Step 1 (dt 1.2e-8 s): the ramp cells on the **porous/free edges of the slab** (rows z = 3 and z = 10, x = 0–2)
  drop from α 0.94 / 0.84 / 0.74 to 0.002 in one step. Their water is pushed out. p in the free cells next
  to the slab reaches −0.5 to −1.5 MPa (p was 0 everywhere at t = 0); the porous cells of row z = 10 are at
  +1.6 to +13 kPa.
- Total water fraction oscillates (0.048 → 0.054 → 0.049) and the **dSmax limit drives dt to 1e-33 s**
  (Coats limit ~1e-8, capillary-wave limit 1.5e-6 are not the cause). 50,000 steps reach only 1.2e-8 s.
- This is the known open problem from `../trialWicking/NOTES.md`: "a porous/free interface with a wet porous
  side diverges in the original solver too".
- **Hypotheses (status after the variants below):**
  1. **Rejected** (σ = 0 and ca90 give identical results). Spurious surface tension at the yarn surface: a wet porous cell next to a dry free cell looks like a
     sharp water/air interface to the VOF part (α 0.94 → 0.002 over one face); σκ∇α acts on the porous/free
     faces (Solidf = 0), with nothing to balance it. The porous contact-angle correction (off by default) is
     meant to act there.
  2. Open (part of 3). Mobility mismatch: at dt ~1e-8 the free-cell face mobility rAUf ≈ dt/ρ (~4e-9) is ~100× below the air
     Darcy mobility K/μ_a (5.7e-7), so any volume the porous cells need through the side faces costs a huge
     pressure difference in the free cells.
  3. **Open, now the main hypothesis** (see the conclusions below). The mixture-pressure jump at the porous/free faces (α·pc not balanced there; see above), with
     `openPorousAirZero 1` adding a −α·pc offset on the porous boundary faces.
- (A first attempt at variants in the scratchpad did not apply its edits: `foamDictionary` has no `-case`.)

### Bench variants (2026-10-12, `2D_bench/variants/`)
**Run folders and figures deleted on 2026-10-12 (cleanup after change E): all made with the pre-E solver. The
numbers below are the record; two figures are kept as evidence of the bug in
`../trialWicking/hybridSolverChanges/debug_faceDump/solidfBug_bench_{alpha,p}.png`.**
**Pre-fix (installed solver `b995db5`). The variants with free cells are dominated by the Solidf bug found below:
they only locate the failure, they say nothing about σ, θ, pc or the p option. Still valid: `fullSlabClosed`
(control) and `fullSlab` (open porous lateral boundary unstable), which have no free cells.**
One change at a time from the bench (`base`). Measured (`steps_summary.md`, `run_summary.md`):

| Variant | Change | Result |
|---|---|---|
| `base` | — | dt collapses at step 5 (2e-16 s, t 1.2e-8 s). Step 1: the slab's edge rows (porous cells next to free cells) empty into the free rows (α 0.94 → 0.002; the free row gets ~α/2, volume conserved); p in the free cells ±1e15 Pa by step 5 |
| `ca90` | porous contact angle on, θ 90° | **identical to base** (same numbers to 3 digits) |
| `sigma0` | σ = 0 | **identical to base** |
| `airZero0` | `openPorousAirZero 0` | **identical to base** (step 1); p differs at the last step only |
| `closedTB` | top/bottom closed walls | fails at step 6 like base |
| `pcMild` | VG pc0 1000, m 0.8 | edge rows stay wet at step 1, then fails at step 6 (same pattern: edge row empties, p ±1e14) |
| `noRamp` | no ramp (dry slab, wet inlet face) | 23 steps, dt collapses at 4.1e-7 s; water enters only through the **free** part of the inlet, the slab stays dry; liquid +23 %, p ~1e12 in the free cells |
| `paperLike` | ca90 + pcMild + no ramp + dry value 0 | runs to 0.2 ms (162 steps, dt 1.4e-6 = capillary-wave limit) but **no water enters at all** (max α 0 at 0.2 ms): stable because nothing happens, not a success. Likely kr_w(0) = 0 on the upwinded inlet face (not checked) |
| `fullSlab` | all porous, top/bottom open | the front runs ahead along the open top/bottom faces, then α → 105, liquid +538 %: **the open lateral porous boundary is broken** (as the open `yarn_to_fluid` wall of the single-yarn case) |
| `fullSlabClosed` | all porous, top/bottom closed | **runs cleanly to 0.2 ms** (865 steps, dt at the Coats limit 2.4e-7): z-spread ≤ 1e-6 (1D as expected), front at S 0.1 grows as √t, 0.08 mm ahead of the 1D similarity solution at 0.2 ms (start-up/ramp offset, shrinking; not compared quantitatively with the 1D runs) |

**Conclusions (2026-10-12):**
- **Established:** the failure comes from the **porous/free interface with water on the porous side**. It is not
  the free-surface tension (σ = 0 identical), not the porous contact angle (identical), not the p BC of the open
  porous faces (identical at step 1), not the open top/bottom (closed: same failure). The bench and the tools are
  sound when there is no free cell (`fullSlabClosed`).
- **Established:** the size of the pc jumps controls how fast it fails (pcMild: step 6 instead of step 1), and a
  dry start only delays it (noRamp: as soon as water reaches porous/free faces).
- **Established, separate problem:** porous faces on an open (p-fixed) lateral boundary are unstable
  (`fullSlab`). The REV's top/bottom patches have porous faces (14 % / 9 % of the edge layers): they must be
  closed, or padded with free cells (`inspect_stl.py --zgap`), whatever the interface fix.
- **Superseded by the step-1 diagnosis below** (the first failure is the unclipped Solidf, not this; the idea may
  still explain the second failure). Former hypothesis: the flux on porous/free faces (Solidf = 0) comes from the momentum equation
  (rAUf, mixture p) while the neighbouring porous faces are Darcy faces with the capillary terms (pc, α·pc in
  the mixture p). On a porous/free face nothing balances the jump of the porous cell's mixture pressure
  (−α·pc + ...), so the pressure solve drives a large flux across it (0.8 m/s in step 1). This is the face type
  that change B left unchanged.
- **Boubaker et al.'s fix (isoAdvector) targets α advection and the CSF curvature:** with σ = 0 changing
  nothing here, it is unlikely to be enough for our case, where the problem is the flux itself (to be confirmed).

### Step-1 flux diagnosis (2026-10-12, debug build, now in `../trialWicking/hybridSolverChanges/debug_faceDump/`)
Scratch copy of the solver (`b995db5`) printing every flux term of `alphaEqn.H`/`pEqn.H` on selected faces
during steps 1–2 of `base` (`debug_faceDump.patch` + `dbgSetup.H`, log `base_step1_faceDump.log.gz`, all in
`../trialWicking/hybridSolverChanges/debug_faceDump/`). Faces: yarn/gap faces of the top edge row (YG), yarn/yarn faces below
(YY), x-faces along the edge row (X). **Measured, step 1:**
- `phi` before the α equation is 0 (the α equation runs first, with the previous step's flux) and the pressure
  correction on YG faces is ~1e-12 m³/s: **the pressure equation is not what empties the edge cells.**
- **`Solidf` = 0.5 on the yarn/gap faces, not 0.** `createPorousMediaFields.H` clips Solidf < 1 to 0, but
  `updateDarcyVelocities.H` (called at the start of every α equation) recomputes `Solidf = fvc::interpolate(Solid)`
  **without the clipping**. Upstream code (Carrillo, commit `98e48b9` "added dynamic mesh capability"), untouched
  by our A/B/C; invisible in the 1D / single-yarn cases (no free cells).
- On those half-porous faces the porous phase fluxes use (i) the face permeability interpolated between the yarn
  (1e-11) and K_VOID (1 m²), i.e. 0.5 m², a mobility ~1e10× too large, and (ii) the Van Genuchten pc of the
  **free** cell (α 0.002 → 2.5 MPa), meaningless in a gap. Result: `phirPore` 1.6e4 on YG faces (1e-26 on YY
  faces), α flux 3.1e-7 m³/s = the whole water of the edge cell in one step (3.7e-15 m³); MULES empties the
  cell. Step 2: p in the gap cells −6e8 Pa, then the collapse. This explains why σ, the contact angle and the
  boundary p option had no effect.

### Fix 1 tested: Solidf clipping restored in `updateDarcyVelocities.H` (scratch build, internal faces only; became change E)
Same bench variants with the fixed binary (`SOLVER=... TAG=clip ./makeVariant.sh`; run folders and figures deleted
in the 2026-10-12 cleanup, numbers kept here):
- **First failure gone:** 10 clean steps, edge cells stay wet, the ramp starts to advance.
- **Second failure, later:** base 464 steps / 1.8e-5 s, ca90 3.9e-6 s, pcMild 7.5e-5 s, noRamp 3.3e-5 s,
  closedTB 7.8e-5 s, then dt < 1e-14. In all of them **water accumulates in the free cells next to the inlet**
  (blobs in the gaps at x < 0.05 mm), liquid +62 % to +3,500 %, **α > 1** (up to 1.12) and |p| ~1e18 Pa at the end.
  A faint α haze also spreads through the whole slab ahead of the front in base (not understood).
- **Hypothesis (not tested):** the second failure is the mixture-pressure inconsistency at yarn/gap faces. A free
  cell next to a wet yarn takes the yarn's mixture pressure (−α·pc, kPa below 0), so reservoir water at p = 0 on the
  free inlet faces is sucked into the gap, where it should not rise (θ 90°, gravity −x). The yarn/gap faces carry
  the momentum (rAUf) flux without any capillary term (Solidf = 0 now): nothing represents the capillary pressure
  jump at the yarn surface. Also to check: α > 1 means MULES boundedness is lost somewhere (eps-weighted
  explicitSolve with mixed eps across the yarn/gap faces?).
- **No change without free cells (verified 2026-10-12):** fix-only build (installed source `b995db5` + the clipping,
  nothing else) vs the installed solver, **bit-identical**: `1D_vertical_hybrid` to 0.1 s (copies in the scratchpad,
  228 field files at 21 write times, `liquidBalance.csv`, 145,652 steps both, final mean α 0.89127, 714 vs 717 s)
  and `fullSlabClosed` to 0.2 ms (43 field files, `liquidBalance.csv`, 865 steps both).
  Expected: without porous/free faces Solidf is already exactly 0 or 1. The single-yarn case (yarn mesh only, no
  free cells) is covered by the same argument, not rerun.
- **Committed as change E (2026-10-12), installed:** `of9-port` `c3a2e6e` (code) + `d1c688a` (solver-repo change
  log `CHANGES_of9-port.md`), pushed 2026-10-12. Final version = the scratch fix extended to **boundary faces**:
  coupled patches (processor, cyclic) are averaged by `interpolate` too, so a processor boundary on porous/free faces
  kept Solidf = 0.5. Test (scratch `parTest`, bench on 2 processors, manual decomposition with the processor
  boundary exactly on the top porous/free faces, 10 steps): internal-only clipping → the porous cells on the
  processor boundary empty as before, dt collapses after 5 steps; with E → same steps as serial, α within 3e-6,
  p within 0.1 %. The REV is cyclic in y and will run in parallel: this part matters for it.
  New file `binarySolidf.H` included after both `interpolate(Solid)` calls. Installed binary verified
  bit-identical to the tested build (bench serial and parallel) and to `b995db5` on the 1D case (0.1 s).
  Binaries: `hybridPorousInterFoam` = E, `hybridPorousInterFoam_b995db5` = A–C, `_be54696` = port only.
  Patch `../trialWicking/hybridSolverChanges/patches/0006-*.patch`, README there updated.
  **Cluster (mini01): rebuild there after pulling** (`cd OpenFoamV8/solvers/hybridPorousInterFoam && wmake`).
- Rebuilding the scratch binaries (the scratchpad is temporary): copy
  `~/OpenFOAM/martin_sng-9/run/hybridPorousInterFoam/OpenFoamV8/solvers/hybridPorousInterFoam` somewhere, apply
  the patch(es) with `patch -p0` from inside it (paths in the patch headers are absolute: edit them or use
  `patch <file> <patch>`), set `EXE` in `Make/files` to a new name and the `../../libraries` paths in
  `Make/options` to absolute paths, then `wmake`. The debug build only works on the bench mesh (750 cells).

### Bench variants with change E (2026-10-12, `2D_bench/variants/*_steps`, `*_run`, `figures/`)
Same 10 variants, installed solver E. Measured (`figures/steps_summary.md`, `run_summary.md`; in run mode the
column "edge-cell … step 1" is the first write, 2e-5 s):

| Variant | 10 steps | Run to 0.2 ms: end | Liquid change at end | Note |
|---|---|---|---|---|
| `base` | clean (edge 0.94 → 0.94, p ≤ 2.4 kPa) | collapse 1.8e-5 s (464 steps) | +62 % | |
| `ca90` | clean | **collapse 3.9e-6 s** (earliest) | −27 % | Boubaker's contact angle makes it worse here |
| `sigma0` | clean | collapse 1.6e-5 s | +13 % | σ nearly irrelevant |
| `pcMild` | clean | collapse 7.5e-5 s | +182 % | |
| `noRamp` | clean, but +15 % liquid in 10 steps (gaps at the inlet) | collapse 3.3e-5 s | +3550 % | |
| `airZero0` | clean | **collapse 1.8e-4 s** (longest, 1052 steps) | +608 % | the top/bottom free layers flood along x to 0.35 mm, the yarn barely fills |
| `closedTB` | clean | collapse 7.8e-5 s | +136 % | |
| `paperLike` | no water enters | 0.2 ms, still no water | 0 | not a success |
| `fullSlab` | α 1.1 at step 10 | collapse 4.2e-8 s | +538 % | unchanged by E (no free cells): open porous lateral boundary |
| `fullSlabClosed` | clean | **0.2 ms, clean** | | identical to the pre-E run |

**Second failure: mechanism (measured on the inlet faces and the first cells, `base` after 10 steps = 0.3 µs,
`airZero0` and `pcMild` at 2e-5 s):**
- Inlet faces of the yarn (k = 3–10): flux **outward** (+2.1e-10 m³/s per face), α_b 0.93: the yarn drains back
  into the reservoir. Gap inlet faces next to the yarn (k = 1–2, 11–12): flux **inward** (−4 to −8e-10), α_b = 1:
  reservoir water is drawn into the gap beside the yarn. Outer gap faces: air out. A circulation reservoir → gap →
  yarn (through the yarn/gap faces) → reservoir.
- (1) **Mixture-pressure suction of the gap:** p in the yarn near the inlet is −α·pc ≈ −1.2 to −1.8 kPa; across the
  yarn/gap faces (Solidf = 0, momentum flux, no capillary term) p is continuous, so the gap cells sit below the
  reservoir's 0 Pa and suck water in. Physically a 60 µm gap with θ = 90° cannot hold water at −1.8 kPa (no
  meniscus supports it); nothing on the yarn/gap faces represents the capillary barrier at the yarn surface.
- (2) **Positive feedback at the yarn inlet faces:** once the flux there turns outward, `inletOutlet` gives α_b =
  cell value (0.93 instead of 0.99), `pOpenAir` gives p_b = −α_b·pc(α_b) ≈ −1.8 kPa, below the cell p, which keeps
  the outflow going. Never happened in 1D (inflow throughout). `airZero0` (p_b = 0 on porous faces) removes part
  of (2) and lasts 10× longer.
- Then water piles up in the free cells, α > 1, p ~1e18 Pa, dt collapse. **Status: (1) and (2) measured; that they
  are the cause of the collapse is the working explanation, not yet proven by a fix.**

**Tests of the mechanism (2026-10-12, variants `gapInletAir`, `yarnInletFixed`, `plic`, run to 0.2 ms):**

| Variant | Change | Collapse | vs base (1.8e-5 s) | Liquid |
|---|---|---|---|---|
| `gapInletAir` | free (gap) faces of the inlet supply air (α_b 0.002), no reservoir water into the gaps | 6.9e-6 s | **earlier** | −24 % |
| `yarnInletFixed` | yarn faces of the inlet as patch `inletYarn`, α fixedValue 0.99 (p from `pOpenAir`) | 8.6e-6 s | **earlier** | +82 % |
| `plic` | `div(phi,alpha) Gauss PLIC interfaceCompression vanLeer 1` (geometric VoF on free faces; was `Gauss upwind`, which **still had interface compression**: see the correction under "Slit tests") | 2.0e-5 s | same | +17 % |

- **(1) and (2) are not the trigger: rejected as the cause.** Without any reservoir water in the gaps
  (`gapInletAir`) the run fails earlier. In all three, the largest |p| at the collapse sits in the **gap cell next to
  the yarn's edge row in the first columns** (k = 11 or 2, x = 0–2), water leaks from the yarn's edge row into the gap
  beside it, and the yarn also drains backwards through its inlet (first column 0.94 → 0.4–0.6, also with α fixed at
  0.99 on the yarn inlet faces). **The failure starts at the interior yarn/gap faces next to the wet zone**, i.e. the
  configuration the REV has everywhere: no boundary condition can fix it.
- These BCs were diagnostic only (not a real strip test: real gaps touch the reservoir and can wick with θ < 90°).
  `yarnInletFixed` (Dirichlet α at the yarn end, as impesFoam's 1D Sb 0.99) remains a reasonable production inlet.
- **PLIC/MPLIC (OF9 geometric VoF, closest to Boubaker's isoAdvector) does not help:** it changes how α is carried on
  free faces for a given flux, while the flux on the yarn/gap faces is the problem; and on those faces the yarn
  cell's α is a pore saturation, not a sharp-interface fraction.

### Second failure: root cause analysis (2026-10-12, after the inlet tests)
Evidence gathered before any new solver test (logs and written fields of `base`, `airZero0`, `fullSlabClosed`):
1. **Log, `base` vs `fullSlabClosed`:** max Courant 0.002 → 0.55–0.87 (vs ≤ 0.004), dt set by dSmax from step 3 and
   shrinking (vs Coats, steady 2.3e-7), p initial residual 1e-2 (vs 1e-4), α-weighted water volume −37 % before the
   collapse (the yarn loses water; the "+62 %" of the summary is the collapse itself).
2. **`base` has an outlet-end air jet** (porous edge cell (3,49): face-flux velocity 24 m/s, cell U 96 m/s; the
   yarn interior at +0.5 kPa vs −α·pc ≈ −5 kPa on the outlet porous faces). Absent in `airZero0` (0.03 m/s).
3. **Cell U vs face fluxes** (own `reconstruct(phi)`, `/tmp` script, uniform grid): in the mixed edge cells (porous
   cells with one yarn/gap face, `DarcyCell` = 0, momentum U) U drifts from the fluxes by ~2–4 m/s per step from step 1
   (39–72 m/s at step 10), interior Darcy cells match to rounding, free cells follow slowly. The drift also exists
   in Uz (normal to the yarn/gap faces) and the real z flux across the yarn edge grows (airZero0 0.026 → 0.57 m/s,
   base 0.49 → 8.3 m/s in 10 steps). Open item of `hybridSolverChanges/README.md` ("mixed cells keep the momentum U,
   pEqn divides Darcy-face fluxes by rAUf") confirmed as a real inconsistency.
4. **Causality test, scratch build `DarcyCell = Solid`** (every porous cell U = reconstruct(phi); TAG `adc`): the
   drift disappears and both `base` and `airZero0` **run to 0.2 ms** (1058 / 558 steps) — **but the yarn drains
   instead of wicking**: mean yarn saturation 0.101 → 0.048 (base) / 0.068 (airZero0), vs 0.101 → 0.197 in
   `fullSlabClosed`; max α 0.45 in airZero0 (inlet cells started at 0.94); flux in the yarn inlet column −0.2 to
   −0.27 m/s (towards the reservoir) vs +0.32 m/s in fullSlabClosed. In base the real yarn-edge z flux grows as before
   over the first 10 steps (outlet jet still present). **Not a fix: stable, wrong physics.**
5. **Pressures (airZero0 + adc vs fullSlabClosed, 20 µs, ramp zone):** yarn mixture p pinned to the gap's ≈ 0 (0 to
   +0.3 kPa) instead of −α·pc (−0.9 to −4.5 kPa); hence **yarn air pressure p + α·pc = 4.1–5.1 kPa while the gap air
   next to it is ≈ 0** (fullSlabClosed: 0.4–1.3 kPa, the physical back-pressure). The yarn's water is pushed out.

**Conclusion (established for the bench): the root cause is the interface condition at yarn/gap faces.** p is the
mixture pressure p_air − α·pc in porous cells; on yarn/gap faces (Solidf = 0) the solver makes p continuous, with no
capillary term, so the yarn air pressure exceeds the gap air pressure by α·pc (kPa with VG pc0 5000, m 0.5; ≈ 5 kPa
even in the dry yarn, set by α·pc at the dry value). Consequences: the yarn drains instead of wicking; boundary
conditions that are physically right ("air at 0 Pa" on open porous faces) contradict the interior; large pressure
imbalances at the yarn edge make the mixed-cell U drift (a numerical consequence, real inconsistency of its own) and
the run collapse. Boubaker et al. do not see it: their α·pc is ~10 Pa vs a 50 kPa drive.
**Physical condition at a yarn/gap face:** gap holds air → air pressure continuous → p_gap − p_yarn = α_y·pc_y; gap
holds water → water pressure continuous → p_gap − p_yarn = −(1 − α_y)·pc_y; both = (α_y − α_g)·pc_y, i.e. a capillary
term of the solver's own form (−pc·∇α) with pc taken **from the porous side only**. The original code had a
half-active version of it (unclipped Solidf 0.5) with the free cell's meaningless pc mixed in: E removed the garbage,
the correct term is missing.
**Upstream history of `Solidf` on porous/free faces (checked 2026-10-12, `git log -S`):** `0a12b0b` (2019-10-17, first
commit) used `Solidf = interpolate(Solid)` unclipped, i.e. 0.5 on porous/free faces (capillary and porous terms
half-active there, with the free cell's pc); `cd088db` (2019-10-28, "fixed some instabilities") added the clipping to
0/1, i.e. **no porous capillary term on porous/free faces by design**; `98e48b9` (2020-09-11, dynamic mesh) recomputes
`Solidf` every step without the clipping, so **since then upstream runs with 0.5 again from the first step** (most
likely by accident). E restores the authors' `cd088db` intent, but it **changes the behaviour of current upstream
code** (results obtained with upstream code after 2020-09, possibly including published ones, used the half term).
**Role of pc (discussed 2026-10-12):** the missing jump α·pc scales with pc like the wicking drive itself, so in pure
capillary wicking the error is of the order of the drive for any pc curve (`pcMild` also fails); a mild curve only
shrinks it. m = 0.5 adds a dry-yarn overpressure α·pc → pc0 (≈ 5 kPa) as α → 0 (m = 0.8: → 0, ≈ 9 Pa at 0.002).
Boubaker et al. are pressure-driven (50 kPa), so it is negligible for them. A pressure-driven bench was judged not
useful for the wicking goal (not run).
**Options (not decided):** (i) add that interface term on yarn/gap faces (pc of the porous cell, in UEqn/pEqn and the
α relative flux there; solver change, prototype on the bench); (ii) model the gaps as a high-K porous medium with
their own small pc0 (all faces porous, Darcy-like everywhere; needs a pc0 field: solver change); (iii) the paper's
regime (mild pc) only hides it. Also keep `DarcyCell = Solid` (or fix the U correction of mixed cells) as a separate,
smaller consistency fix, to test with (i).

**Compared with Boubaker et al. 2026 (none of the problems is documented there):**
- Their flow is pressure-driven (ΔP 50 kPa) with a mild pc (pc0 1000, m 0.8: α·pc ~ tens of Pa), so the
  mixture-pressure suction is negligible next to the drive, and channels filling first is physical for them. In
  pure capillary wicking with our pc it is the whole drive.
- Their contact-angle setting (θ 90° on) shortens our runs (ca90: 3.9 µs vs 18 µs).
- Their Fig. 1b (ragged interface along the porous surface with the original solver) may partly be the Solidf bug
  (upstream since `98e48b9`, they changed only the α advection). Hypothesis only.
- Their mould walls at top/bottom avoid our open-porous-boundary problem (`fullSlab`); not discussed.
- Their sharp start (α 0, α = 1 on the inlet) admits no water here (`paperLike`); with a pressure drive it would.

### Option (ii) implemented as changes F and G (2026-10-12; **committed `febfcae` (F), `1b007d8` (G), docs `8b35cc4`; installed**)
Scratch build `hybridPorousInterFoamFG` (installed source E + F + G; source in the session scratchpad, to be committed).
- **F (always on; acts only where Darcy faces exist): U correction of mixed cells.** `pEqn.H`: the face driving force
  of `U = HbyA + rAU·reconstruct(...)` uses the mobility of each face's own flux: momentum faces (phiG + phiPc)/rAUf,
  Darcy faces phiDarcyExplicit/Mf, and snGrad(p)|Sf| on all (was pEqn.flux()/rAUf, Mf/rAUf times too large on Darcy
  faces: the drift of B's mixed cells). Unchanged on momentum faces.
- **G (opt-in `porousFreeDarcyFaces on;` in transportProperties): porous/free faces as two-phase Darcy faces.**
  New indicator `porousFace` (`porousFace.H`) = 1 on faces with at least one porous side (= Solidf without G);
  harmonic K on porous/free faces (≈ 2 K of the porous cell instead of (K + K_VOID)/2); pc = dpc/dS = 0 in free cells
  (`updateVariables.H`), so the phase fluxes on those faces follow the differences of the phase pressures (air
  pressure continuous next to a dry free cell, water pressure next to a wet one: the capillary jump at the porous
  surface, Mosthaf-type condition); Darcy-face selection, phase fluxes, kr upwinding use `porousFace`; **on porous/free
  faces the α flux is the water Darcy flux `phiWetting` itself** (the drift form α_up·φ + relative flux, kept inside
  the porous medium, gives the wrong phase split across the α and ε jumps: it pushed water out of the yarn at ~1.3× an
  incoming air flux, measured location and sign in R3); start-up mobilities/pc recomputed once if porous/free faces
  exist. Coats function object (`tools/coatsTimeStep`) now uses the solver's `porousFace` and `k0f` when registered.
- **Referee tests** (`variants/makeVariant.sh R1…R3`, `refereeCheck.py [tag]`; all patches closed, no reservoir),
  0.2 ms:

  | Test | Installed E | F + G | Correct |
  |---|---|---|---|
  | R1 static wet yarn (α 0.5) + air gaps: yarn water (of 100) | 99.999 | 99.9999 | 100 |
  | R2 dry yarn + water-filled gap: water taken by the yarn (cell volumes) | 0.04 | 37.8 | > 0 (counter-current, air must leave upward) |
  | R3 closed ramp: yarn water lost to the gaps | −42 % | −0.04 % | 0 |
  | R3 yarn α(x) vs no-gap reference R3closedRampSlab | ≤ 0.25 | ≤ 0.0065 (20 µs), ≤ 0.0005 from 0.1 ms | 0 |
  | R3 max velocity | 25 m/s | 0.14 m/s (20 µs) → 0.03 | ~0 |

  (A first G version without the `phiWetting` α flux leaked: R1 −0.05 % per 0.2 ms linear, R3 −8.3 %.)
- **Wicking bench `base` (open boundaries, reservoir) with F + G: runs to 0.2 ms and wicks** (was a collapse at
  18 µs). Yarn mean saturation 0.10 → 0.312, front 0.415 mm vs no-gap reference 0.197 / 0.334 mm. Split:
  `gapInletAir` + G (no reservoir water into the gaps): 0.209 / 0.343 mm, gaps stay dry → **with air gaps the yarn
  wicks like the reference, +6 % (lateral air escape, physical)**; the rest of `base`'s speed-up is **reservoir water
  climbing the gaps beside the wet yarn** (gaps full to x ≈ 0.2 mm at 0.2 ms, 74 cell volumes) and imbibed sideways.
  Wet-wall capillary rise in inter-yarn gaps is real (wet yarn surface ≈ perfectly wetting; 2σ/w ≈ 2.4 kPa for 60 µm),
  but here it rests on an unresolved 3-cell meniscus with the contact-angle model off: **modelling question, open.**
- **Regressions:** `fullSlabClosed` with F (G off) and with F + G on: bit-identical to the installed solver (40/40);
  `1D_vertical_hybrid` 0.1 s with F + G on: bit-identical (228/228, liquid balance; G finds 0 porous/free faces). A
  first G version recomputed the start-up mobilities unconditionally and was not bit-identical (6th digit): fixed.
- **Not yet checked:** single-yarn 3D case (F changes the mixed cells along its closed lateral wall: must be rerun and
  compared, not assumed identical); upstream tutorials with porous/free faces (G off: only F acts); porous/free faces
  that are not Darcy faces (Da ≥ darcyFaceMaxDa: G then uses the momentum path there; no warning yet); non-uniform
  meshes (the face form of the phase pressures is exact for 0.5/0.5 interpolation weights only).

## Reference: Boubaker et al. 2026 (Compos. Part A 206, 109781)
Same solver, same kind of problem: a plain-weave E-glass µCT geometry with tows as porous media and the inter-tow
space as free fluid. `build_fields.py`'s K_VOID = 1 m² comes from this paper. What matters for us:
- **Their original solver was unstable at the porous/free interface** (Fig. 1b: injection into a free channel
  over a porous half-disc, K 1e-13; MULES gives a ragged, broken interface along the porous surface). **They
  replaced MULES by isoAdvector** (geometric VOF) and report stable runs; no change to the p–U coupling or CSF.
  Their trigger was the viscosity ratio (resin 0.2 Pa·s / air, ~1e4; ours 57), but the failure sits at the same
  place as our bench failure.
- **Contact angle 90° at the free/porous interface, explicitly assigned** ("neutral wetting"), i.e. the porous
  contact-angle model switched on with θ = 90°. Our "default" is the model **off**: not the same thing.
- **Much milder capillary pressure:** VG pc0 = 1000 Pa, **m = 0.8**, chosen "to maintain numerical stability".
  With their values, pc(0.01) = 3.2 kPa, pc(0.002) = 4.7 kPa (α·pc 9 Pa), and pc at the 1e-4 clip = 10 kPa.
  Ours (pc0 5000, m 0.5): pc(0.002) = 2.5 MPa, α·pc = 5 kPa. At the dry state, the pc and α·pc jumps we put next
  to the free cells are ~500× theirs.
- **Initial state:** α = 0 everywhere, α = 1 on the inlet face only, no ramp; p atmospheric, U 0.
- **Flow is pressure-driven** (ΔP 50 kPa, or an imposed inlet velocity); capillarity only modifies it. Pure
  spontaneous wicking (our case) is not shown.
- **BCs:** inlet p fixed + `pressureInletVelocity`, α = 1; outlet p fixed, U and α zeroGradient; upper/lower
  faces = mould walls (noSlip, α zeroGradient); lateral faces cyclic.
- **Mesh and cost:** 150 × 150 × 50 hex cells of 131 × 101 × 53 µm (ours 20 µm); MaxCo 0.5, MaxAlphaCo 0.5;
  4–6 days on 32 cores to full saturation.
- **Tensor K** per tow (diagonal Gebart, warp and weft): their solver version reads a tensor K. Data and
  code "on request": worth asking them for the modified solver (isoAdvector + tensor K).
- They observe **artificially fast flow in the free layer near the upper surface** (geometry overestimates the
  inter-tow space there). Our open air layers above and below the fabric (86–91 % free in the edge z layers)
  could do the same (race-tracking along the surfaces).
- Post-processing for later: x_f from the end points of the interface in the mid-plane, x_f² vs t fit,
  K_unsat = (x_f²/t)·μ(1 − Vf)/(2 P_in) (their eq. 6).

### Pre-commit checks of F/G (2026-10-12; all passed, then committed — patches 0007/0008 in `../trialWicking/hybridSolverChanges/patches/`)
- **1b done:** Darcy-cell rule ignores non-coupled boundary faces with fixed U (their flux uses U_b, ddtCorr 0
  there). Single-yarn 3D, 225 steps: alpha/p/phi still bit-identical to E, max written U 2.3e4 (E) → 1.5e3 (F) →
  **18.9 m/s** (p99 4 m/s). Bench base/fullSlabClosed/R3 with G: bit-identical to before 1b (no cell changes status).
- **#7 done:** warning when porous/free faces are not Darcy faces (tested with darcyFaceMaxDa 0.04: "100 of 100 …");
  info line otherwise. Coupled faces are now counted once (each side 1/2).
- **#2 done:** processor boundary on the porous/free faces (R3, 2 procs, manual cut, p tol 1e-12): serial vs
  parallel max |Δα| 1e-5–2e-5, cut row 1e-6, yarn water identical to 4 decimals. Cyclic (bench top/bottom cyclic,
  `cycA` interfaces internal vs `cycB` interfaces on the cyclic patch, same system shifted by 3 cells): max |Δα|
  3.9e-5 at 0.2 ms (tight tol), same order as the all-internal control `cycA` vs `cycC` (shift 1, 2.4e-5); at default
  tol the difference concentrated at the cyclic interface row (1.7e-4) = tolerance effect. **No systematic error.**
- **#3 long runs (5 ms):** with gaps initialised at alpha 0.002 (old initFields): R1 conserved (4 ppm) but **gap air
  currents grew** to 0.085 m/s (σ = 0: none; g = 0: still; E: 1.4e-4 flat) → surface tension on small alpha variations
  in a "dry" gap at 0.002 (full-strength normals); **gapInletAir collapsed at 2.58 ms** (gap air 3→10 m/s at the inlet
  corner, then a Courant burst, alpha → 122 at the outlet column when the front arrived). **Fix (setup, not solver):
  free cells initialised as pure air (alpha 0) and air entering open free faces at 0** (`initFields.py --free-dry`,
  default 0; porous dry value unchanged). With it: R1 5 ms yarn −0.0004 %, gap U ≤ 1.7e-3 (bounded); R3 5 ms yarn
  water +0.0000 %, profile vs no-gap reference ≤ 4.2e-5, gap U decaying; **gapInletAir runs to 5 ms**, front reaches the
  outlet at ~2.5 ms and passes, alpha ≤ 0.972, gaps dry, yarn front +2–5 % / saturation +5–12 % vs the no-gap
  reference (lateral air escape). E's R1 lost 0.036 % yarn water in 5 ms (pre-G leak).
- **Open (documented, not blocking):** in gapInletAir the gap air near the inlet corner moves at **3.7 → 9 m/s**
  (rows alternating in p and U: −7/+14/−40 Pa), a jet from the gap inlet faces along the open bottom boundary; with
  top/bottom closed it drops to ~2 m/s, bounded; the yarn saturation is identical either way (4 digits). Not explained
  (air Darcy outflow from the yarn there is mm/s); likely a free-cell mode near the gap inlet. Base + G (reservoir water
  in the gaps): still the gap-water rise (modelling question).
- Lesson: never edit a script while background runs read it (two long runs died on a half-read makeVariant.sh); runs
  now use a frozen copy.

### Bench validation of the installed solver (2026-10-12, `2D_bench/variants/`, `benchReport.py`, `figures/`)
One consistent run set: installed of9-port `1b007d8`, bench defaults (`porousFreeDarcyFaces on`, free cells pure air,
`tools/waterBudget` function object), 5 ms, writes every 0.1 ms (`WRITE=1e-4 ./makeVariant.sh <v> run 5e-3`). Earlier
runs moved to `variants/old_variants/` (README there). Summary in `figures/summary.md`, figures
`bench_alpha_maps.png`, `bench_front_sqrt_t.png`, `bench_profiles.png`, `bench_water_budget.png`,
`bench_pressure_jump.png`, `bench_referees.png`. **Results:**
- **Pass:** yarn alone (reference) and yarn + air gaps reach 5 ms; front slopes 17.49 (reference) and 17.88 mm/√s
  (air gaps) vs 18.04 for the 1D similarity solution (fit 0.5–2 ms; air gaps slightly faster: lateral air escape);
  water budget (waterBudget.csv) stored = entered to ~1e-15 relative in all bench cases; R1 at rest (−0.0005 % in
  5 ms, gap velocity ≤ 2e-3 m/s); R2 dry yarn imbibes from the wet gap (0.40 → 47 cell volumes); R3 profile within
  6e-4 of the no-gap reference (4e-5 at 5 ms), yarn water conserved (≤ 1e-4 %).
- **Consistent, not quantified:** air pressure across the yarn surface (yarn edge cell p + α·pc vs gap cell p): median
  0.02 → 17 Pa, max 450–870 Pa near the reservoir (first columns), vs α·pc 3.4–5 kPa without G. The cell-centre
  difference contains the Darcy drop of the escaping air over half a yarn cell, large where the yarn is nearly
  saturated (kr_air ~1e-4): physical air back-pressure near the reservoir. A quantitative check would compare it with
  the air flux through each face.
- **Fail: `base` (reservoir water also entering the gaps) collapses at 0.57 ms** (34,229 steps): Courant 0.5–1.35 in
  the steps before, fast free-surface flow of the water climbing the gaps, then dt collapse. The gap-water question
  is therefore also a solver-robustness question for that configuration (unresolved 3–4-cell meniscus, contact angle
  off). To be handled with the gap-capillarity work (S1–S3).

### F/G open questions (2026-10-12, checklist)
(Status update: 1b, #2, #3, #7 done — see "Pre-commit checks of F/G" above.)
Verification missing: [x] 1 single-yarn 3D case with F — **done locally, 225 steps (1e-5 s), serial, scratch copy:
alpha, p, phi, dt sequence and liquid balance bit-identical to E; only the written cell U differs** in 1113 wall cells
(non-Darcy wall faces, U fixed 0 → no flux, so U of these mixed cells never feeds back; full run on the mini optional).
Side finding: E's written U there is spurious, max 2.3e4 m/s (B's drift); F lowers it to 1.5e3 m/s, still unphysical.
U-based post-processing of the yarn hybrid runs is invalid near the wall (wickingFront.ipynb uses p, p_air, p_water,
Uwetting: unaffected). [ ] 1b DarcyCell = cells whose internal and coupled faces are all Darcy faces (ignore wall
boundaries) → U = reconstruct(phi) there too — before commit; [ ] 2 porous/free faces on processor and cyclic patches (G's coupled harmonic-K path never run; REV is cyclic and
parallel) — before commit; [ ] 3 longer runs (R1/R3 conservation; bench until the front reaches the outlet, 3–5 ms) —
before commit; [ ] 4 3D geometry (edges/corners with several porous/free faces, staircased surfaces; small 3D bench) —
before REV; [ ] 5 mesh dependence (10 µm) — before REV; [ ] 6 upstream tutorials with G on (fracture imbibition) — nice.
Implementation gaps: [ ] 7 porous/free faces that are not Darcy faces under G (momentum path, inconsistent; warn/count or
force Darcy) — before commit; [ ] 8 porous contact-angle model with G (never run together) — S1/S2; [ ] 9
momentumPredictor path not adapted for G — document; [ ] 10 exact phase-pressure differences only for 0.5/0.5 weights
(uniform meshes) — document; [ ] 11 harmonic K set at start-up only (no dynamic meshes, as B) — document.
Modelling assumptions: 12 pc = 0 in free cells (gap capillarity only from VOF + contact angle: S1); 13 gap-water rise in
`base` + G physical or unresolved meniscus (S1/S2); 14 kr of free cells from their VOF α when flow goes gap → yarn
(partial mobilities in smeared cells); 15 one contact angle for dry polyester (~70–80°) and wet yarn (~0°); 16 open
porous boundaries still unstable (REV top/bottom: walls or padding).
Process: F always on (changes B cases with mixed cells → item 1); G opt-in; separate commits with patches and docs.

## Gap-water question and REV gap widths (2026-10-12)
**Context (user):** the fibre will most likely be polyester (wet/dry contact angle not known); a previous student modelled
capillary rise **between impermeable yarns** with contact angles 40–80°; **the goal of this work is to add the wicking
inside the yarns.** So the gaps must keep resolved capillarity (VOF + contact angle) and the yarns get G.
**Physics:** gap rise depends on the gap's own capillarity, 2σcosθ/w: wetting walls → a slit wicks (early on it can
even lead the yarn: slit K = w²/12 ≈ 3e-10 m² for 60 µm vs yarn 1e-11); θ ≥ 90° → no rise; a wet yarn surface is
nearly perfectly wetting. Dry polyester ≈ 70–80° (typical literature range, not checked for this fibre): at θ 75°, a
300 µm gap gives ≈ 125 Pa vs several kPa in the yarns → yarns should lead. The `base` + G gap water (θ 90°, model off,
3-cell gap) is most likely the unresolved meniscus not resisting (hypothesis, not tested).
**REV gap widths** (original 0/fYarn, yarn = f ≥ 0.5, 20 µm grid; narrowest free run bounded by yarn at both ends along
x, y (periodic) or z, per free cell; slightly overestimates oblique gaps): 82 % of the free cells are inside the fabric
envelope; narrowest width median **15 cells (300 µm)**, p25 9, p10 6, p5 4 cells; ≤ 4 cells: 6 %, ≤ 8 cells: 20 %. The
narrow throats (≤ 4 cells: 16–22 % of the free cells of z layers 5–8) sit at mid-thickness, where warp and weft cross;
near the surfaces medians 18–58 cells. Only 1 % of the free space is enclosed between yarns above and below
(single-layer weave: openings and crimp pockets connected to the surfaces). **At 20 µm the meniscus should be
resolvable in most gaps (≥ 8 cells for ~80 % of the gap volume); the crossing throats will be poorly resolved.** The
bench's 3–4-cell gaps were not representative (pessimistic).
**REV yarn dimensions (measured 2026-10-13, same fields, f ≥ 0.5, per yarnID; scratch script):** thickness (z run per
column) median **6 cells (120 µm)**, max 7–8; width (chord across the yarn axis) median **~15 cells (300 µm)**; yarns
0/4 and 5/9 are the halves cut by the periodic boundaries. So a yarn flank facing an in-plane gap is ~7–8 cells deep
(half width), a yarn face facing a crimp pocket ~3 cells (half thickness).
**Gap vs yarn wicking rate (estimate, 2026-10-13, viscous Washburn, μ 1e-3, σ 0.072):** slit h²/t = σw cosθ/(3μ):
w 160 µm θ 60 → 44 mm/√s; w 300 µm θ 75 → 43; θ 85 → 25; θ 88 → 16; yarn (bench K/pc, 1D similarity) 18 mm/√s.
Equivalent: K·pc of the slit (w²/12 · 2σcosθ/w = σw cosθ/6) ≈ 1e-6 vs yarn 1e-11 · 5000 = 5e-8. **A straight
continuous gap out-runs the yarn unless θ ≳ 87°**; it stops at h_eq = 2σcosθ/(ρgw) ≈ 13 mm (300 µm, θ 75) while the
yarn's pc (kPa) holds ~0.5 m. Measured in our slit runs: gap 1.25 mm at 2 ms (S0) vs yarn ~0.8 mm. Whether the fabric's
gaps form continuous channels along the wicking direction (plain weave: openings separated by crossing yarns) is
not checked (hypothesis: they mostly do not, so yarns lead in the fabric).
**The student's results are not a direct reference:** interFoam on a body-fitted mesh of the free volume only (yarn
surfaces = smooth walls, contact angle as wall BC), vs here a Cartesian grid with porous, staircased yarns and the
solver's porous contact-angle model. The continuity question is whether the porous-wall representation reproduces wall
contact-angle physics.
**Proposed next (not started):** slit benchmarks at 20 µm, gravity on, contact-angle model on, gaps 4 / 8 / 15 cells:
S1 porous walls in the impermeable limit (K 1e-20, θ 40/60/80°) vs the analytical slit rise, optionally vs an interFoam
slit with real walls and a contact-angle BC (the student's approach on the simplest geometry); S2 permeable walls
(K 1e-11, G on; contact-angle model + G never tested together); S3 S2 with wall K → 1e-20 must converge to S1.
Not covered by an axis-aligned slit: staircased yarn surfaces in the REV can pin/slow contact lines (effective angle ≠
imposed); a slit tilted relative to the grid would quantify it if needed.

## Slit tests (2026-10-12, `slit_test/`)
2D vertical slit (gravity −x), 2 mm, 20 µm cells, reservoir at x = 0 (free inlet faces: water at static p = 0, U
`pressureInletOutletVelocity`), open to air at x = 2 mm. `S0`: real walls, `constantAlphaContactAngle` (the
student's / interFoam approach). `S1`: 4 porous wall cells (eps 0.5, K 1e-20), porous contact-angle model on, G on,
closed walls behind. `S2`/`S3`: wall K 1e-11 / 1e-14 / 1e-17. `--fill`: initial water column in the gap (0.1 mm).
Folder renamed from `slit_bench` (user request). Reference: Bosanquet slit rise, ρ d(hḣ)/dt = 2σcosθ/w − 12μhḣ/w² − ρgh.
- **Script bug (found and fixed 2026-10-12):** with `--fill`, `makeSlit.py` re-read `0/alpha.wetting` after adding the
  wall BC, so **all `--fill` cases (the D_* diagnostics) ran with top/bottom open to air** (S0: no wall, no contact
  angle → flat meniscus, p = 0; S1: open porous lateral boundary, known unstable). Those diagnostics were invalid and
  are deleted, including the conclusions drawn from them (S1 spurious 8.8 m/s / 66 m/s, "no rise with any α scheme",
  "contact-angle model off → 0.125 mm", "G off → 0.34 mm"). The 2 ms series without fill (S0_*, S1_*, S2, S3 in
  `figures/summary.md`) had the right BCs.
- **Correction:** `alphaScheme.H` wraps any non-compression `div(phi,alpha)` scheme into `Gauss interfaceCompression
  <scheme> cAlpha`, so the bench's `Gauss upwind` **does** compress the interface (earlier notes said "no compression").
- **S0 with fill (gap 8 cells, θ 60°), rerun with the fix — measured:** curved meniscus (water at the walls), rise
  0.40 / 0.88 / 1.38 / 1.86 mm at 0.5 / 1 / 1.5 / 2 ms vs Bosanquet 0.34 / 0.63 / 0.91 / 1.16 (from the same 0.1 mm
  start); max |U| 1.4 m/s. Pressure jump across the meniscus ≈ 340–410 Pa (2σcosθ/w = 450). x-momentum balance from
  the written fields (column, 1.5 ms) closes within 0.5 % with water's viscosity (ρ∂u/∂t + pressure + gravity +
  viscous; 8-cell finite-volume Poiseuille only +3 % flow). **The gap to Bosanquet is the inlet BC:** a static p = 0
  inlet gives the entering water its velocity without the dynamic-pressure cost (no ρḣ² term). The model without that
  term and a 410 Pa drive gives 0.43 / 0.94 / 1.46 / 1.93 mm (sim within ~5 %); with a Bernoulli entry (½ρḣ²) 1.36 mm
  at 2 ms. **Conclusion: VOF + wall contact angle reproduces slit rise at 8 cells; the reservoir BC is not a reservoir
  at rest.** For the REV (gaps touching the inlet) the free inlet faces should use a total-pressure condition (p0 = 0)
  — proposed, not done.
- **S0 without fill (2 ms series): no rise at any width/angle**: the meniscus does not form from a gap that starts
  empty at the inlet face (hypothesis: the contact-angle BC needs an interface inside the domain). Start slit/REV gaps
  with a short water column, or check the corner cells (not investigated).
- **S1 with fill (porous walls K 1e-20), rerun:** 0.40 / 1.04 / ~1.7 mm at 0.5 / 1 / 1.5 ms, 2 mm (outlet) at 1.8 ms:
  lags S0 early (0.126 vs 0.165 mm at 0.2 ms), then ~10–20 % ahead of S0; interface inside the gap ragged; **max |U|
  14 → 42 m/s** (S0: 1.4). Wall water constant (41.12 → 41.16 cell volumes). **The porous-wall contact-angle model gives
  roughly the right rise but large spurious currents.** Without fill (2 ms series) S1 rose 4–5× faster than S0/analytic
  (1.46–1.78 mm at 0.5 ms for θ 40–60°): start-up from the inlet face is wrong with porous walls (not investigated).
- **S2 (K 1e-11, yarn-like walls) stopped at 0.36 ms, S3 K 1e-14 at 0.95 ms (no fill, dt collapse); S3 K 1e-17 ran.**
  Not rerun with fill yet.
- Tutorial check (scratch copy of `Capillary_Rise/standard_Boundary`, 1 mm gap, 20 cells, θ 45°): curved meniscus,
  slow rise (8.03 → 8.23 mm in 20 ms; rate not assessed). Used only to see that wall contact angle acts in this build.
- **Total-pressure inlet (`tools/pOpenAir`, `openFreeTotalPressure 1`, new, default 0 → bench unchanged; control
  run bit-identical):** free inflow faces get p = −½ρ|U|² (reservoir at rest). **S0 then matches Bosanquet: 0.34 /
  0.66 / 0.96 / 1.25 mm at 0.5 / 1 / 1.5 / 2 ms vs 0.34 / 0.63 / 0.91 / 1.16** (between the ρḣ² and ½ρḣ² entry models),
  max |U| ≤ 0.94 m/s. **Wall capillarity of the free-surface model: validated at 8 cells.**
- **S1 + total-pressure inlet:** 1.21 mm at 2 ms (S0 1.25), wall water constant, water budget 1e-14; **max |U| 15–38 m/s**
  (S0 < 1): the porous contact-angle model gives the right rise with large spurious currents.
- **S2 (K 1e-11 walls, G on) + total-pressure inlet:** walls to the outlet → **collapse at 0.45 ms at the outlet**
  (dry porous wall faces on the open outlet, p ±1e8: the `fullSlab` open-porous-boundary instability, not the gap).
  `makeSlit.py --wall-end 3` (walls stop 3 cells before the outlet) → **runs to 2 ms**: gap meniscus 1.17 mm (S0 1.25),
  wall front (α 0.1) 0.28 / 0.52 / 0.98 / 1.40 mm at 0.1 / 0.5 / 1.3 / 2 ms, ahead of the gap meniscus and **~1.7× the
  yarn-alone 1D similarity front** (18.04 mm/√s → 0.81 mm at 2 ms): the gap feeds the walls sideways (hypothesis:
  physical dual-scale effect, slit K = w²/12 ≈ 2e-9 vs 1e-11; no no-gap reference run yet). Max |U| 2–3.6 m/s (below S1),
  water budget 4e-15. Near-wall gap cells drier than the gap centre (the wall drains them; at 0.4 ms α 0.15–0.5 vs 1).
- **Full series with the validated setup (2026-10-12; `makeSlit.py` defaults now: fill 0.1 mm, total-pressure inlet,
  `--wall-end 3`; `slitReport.py` → `figures/slit_{widths,angles,permeability}.png`, `summary.md`; old runs and figures
  in `old_runs/`).** h at 2 ms sim / Bosanquet [mm]:
  - **S0 (real walls): within 2–11 %, all widths and angles** (w4 1.32/1.19, w8 1.25/1.16, w15 0.99/0.94; θ40 1.54/1.43,
    θ80 0.72/0.69), max |U| 0.5–1.2 m/s. Slightly faster than Bosanquet everywhere (entry/developing-profile effects).
  - **S1 (porous walls K 1e-20, porous contact-angle model): right at w8/θ60, wrong at the extremes**: w4 1.94/1.19 (+60 %),
    θ40 1.79/1.43 (+25 %), θ80 0.45/0.69 (−35 %, stalls), w15 0.89/0.94; **max |U| 30–60 m/s** in all. The porous
    contact-angle model over-/under-drives the rise depending on width and angle and makes large spurious currents.
  - **Wall permeability (w8, θ60):** gap meniscus 1.26 (1e-20), 1.39 (1e-17), **1.52 (1e-14)**, 1.17 (1e-11): the
    intermediate permeabilities rise *faster* than impermeable walls, which is not physical (a permeable wall can only take
    water from the gap) → unexplained, open. Wall front: 1e-20/1e-17 stay at the initial ramp (0.19 mm); 1e-11 1.43 mm,
    linear in t (fed sideways by the gap, ~1.8× the 1D yarn-alone front); **1e-14 1.25 mm in steps** — lateral imbibition
    across 4 cells looks too fast for K 1e-14 (sorptivity estimate with pc ~5 kPa: ~30 ms for 80 µm; the VG pc → ∞ at the
    dry state may dominate). Suspect; to check. Max |U|: 1e-11 2–4 m/s, 1e-14 3–6, 1e-17 4–13, 1e-20 up to 60.
- **Meniscus shape barely resolved (checked 2026-10-12; visible in ParaView at later times — t = 0 is the flat fill):** circular-arc depth
  (w/2)(1 − sinθ)/cosθ vs measured (α = 0.5 at the wall − at the centre, 2 ms): w8 θ40 37/23 µm (1.1 cells), w8 θ60 21/13
  (0.7), w15 θ60 40/30 (1.5), w8 θ80 7/4 (0.2). The interface is smeared over ~3 cells and the curvature spans only 1–2 cells.
  The rise is right because the contact-angle BC sets the interface normal at the wall (the capillary force),
  not because the shape is resolved. REV: with θ 70–80° (dry polyester) the real meniscus is < 1 cell deep anyway; it
  matters for strongly wetting (wet yarn) surfaces.
- **Why an initial water column (user question, tested 2026-10-12; runs in `old_runs/T_*`, `makeSlit.py --inlet-alpha`):**
  α `inletOutlet` is zeroGradient while the flux is 0 (`pos0(0) = 1`), so an empty gap sees α = 0 on the inlet at t = 0:
  no interface, no capillary force, nothing starts (S0 without fill). Alternatives, gap 8 θ 60, total-pressure inlet:
  (1) **fixed α = 1 inlet, empty gap → spurious start-up kick**: 0.71 mm at 0.1 ms (analytic 0.07), 23 m/s, inlet cells
  at −15 kPa (physical suction 450 Pa); 6× too fast at 0.4 ms. S1 the same way: +50 % at 2 ms, 54 m/s.
  (2) **1-cell column (20 µm), inletOutlet → the water drains back into the reservoir in < 0.1 ms**, empty gap, later
  dt collapse. (3) 0.1 mm (5 cells): correct. **Rule: the VOF interface must start inside the domain, several cells
  from the inlet face** (gap analogue of the yarn's 0.2 mm wetted ramp; physically the immersion depth of a strip test).
  REV: start the gaps with a short water column at the inlet (≥ 5 cells; minimum not searched).
- **Stock interFoam reference (`slit_test/interFoamSlit.sh`, runs `IF_*`, 2026-10-12):** same slit mesh (gap 8, θ 60,
  real walls), inlet α `inletOutlet` inletValue 1 / value 1 (**the previous student's inlet BC**), damBreak schemes.
  Empty gap, static (`prghPressure`) or total (`prghTotalPressure`) inlet: **no rise at all** (max |U| 0.002 m/s).
  0.1 mm column + total pressure: 0.28 / 0.78 / 1.25 mm at 0.4 / 1.2 / 2 ms = **hybridPorousInterFoam S0 to 0.01 mm**
  (max |U| 0.94 both). So (1) the free-fluid part of our solver reproduces interFoam; (2) that inlet BC alone cannot start
  a rise, in interFoam either: her case must have had water inside the domain at t = 0 (reservoir region in the mesh or
  a setFields layer; **confirmed by the user: the initial water is in her 0/alpha.water**).
  **Her full setup (user, 2026-10-12; "case study without gravity"):** p_rgh inlet and atmosphere fixedValue 0, walls
  fixedFluxPressure; U inlet/atmosphere pressureInletOutletVelocity, walls noSlip; α inlet inletOutlet 1. So an open
  water supply through the inlet (as ours), but **static p = 0 at the inlet** (no ½ρv² entry cost: our static-inlet slit
  was ~60 % faster at 2 ms than the reservoir at rest; ½ρv² ≈ 500 Pa at 1 m/s vs 2σcosθ/w ≈ 240 Pa for 300 µm at 60°, so
  her early rise rates are likely overestimated) and **g = 0** (no equilibrium height). For a direct comparison use her
  conditions: `--static-inlet`, g = 0, her initial water depth.
- **Consequence for the REV:** porous faces on the outlet patch must not see the open BC (yarns crossing x-max): close the
  porous outlet faces (the 1D cases used Uwetting 0 there) or end the yarns before the outlet.
- **Open:** S1 spurious currents (porous contact angle); start-up from an empty gap (S0 no rise, S1 too fast);
  no-gap reference for S2's wall front; mesh dependence (16 cells across); widths 4/15, θ 40/80; S3 K 1e-14/1e-17
  with the new settings; meniscus at a wet porous wall (effective θ ≈ 0?); then the `base` bench with the total-pressure
  inlet.

## Thick-wall slit bench and changes H, F′, I (2026-10-13, `slit_test/`; **committed `1588863` (H), `3aded21` (F′), `b525086` (I), docs `1a79db9`; installed**)
**New bench (decided with the user, replaces `2D_bench` `base`):** the slit with porous walls of 8 cells (half a REV yarn
width) instead of 4, gap 8 or 15 cells: `makeSlit.py --walls porous --nw 8 --w 8 [--K ..] [--theta ..]`; new options
`--nw`, `--dx` (cell size; widths and `--wall-end` stay in cells), `--add KEY=VALUE` (adds a transportProperties
keyword). Analysis `benchSlit.py CASE...`: gap meniscus (gap-averaged α 0.5), wall front (α 0.1) in the wall row next to
the gap ("surface") and at the closed back ("back"), wall water (Σ ε·α, cell volumes), max |U|. References: S0 (real
walls, validated vs Bosanquet), the same walls without gap (`--w 0`), the 1D similarity solution.
**With the installed solver (`1b007d8`) — measured, 2 ms, θ 60, `B_nw8_*`:** all runs reach 2 ms, budget closes
(~1e-26 m³); wall alone (w 0) front 0.87 mm (1D similarity ~0.8 + ramp). But: K 1e-20 walls max |U| 24–68 m/s and water
droplets thrown ahead of the meniscus (50–100 wet gap cells beyond it, some leave through the outlet); K 1e-17 rises
**faster** than K 1e-20 (1.43 vs 1.27 mm, unphysical); K 1e-14: only the wall's surface row wets, **ahead** of the gap
meniscus; K 1e-11: |U| 3–5 m/s, film of α 0.1–0.4 along the walls ahead of the meniscus.
**Causes found (code read + tests), and scratch fixes** (build `hybridPorousInterFoamH`, libraries `...H`, source in
the session scratchpad `hpifH/`, copied from `8b35cc4`; **not committed, not installed as default**):
- **H — porous contact angle as a wall** (`porousInterfaceProperties.C`, opt-in `porousContactAngleWallLike 1`).
  `correctContactAngleDB` (1) computes the interface normal from α including the porous cells, where α is a saturation:
  water in the gap next to a dry wall looks like an interface parallel to the wall along the whole wetted wall, a wet
  wall next to a dry gap cell looks like a film; (2) imposes θ on a band of faces 2–3 cells deep on both sides of the
  porous surface (smoothed grad Solid), i.e. most of a 4–8-cell gap (explains gap 4 worst, extreme angles worst). H:
  porous cells take the mean α of their free neighbours for the normal (zero gradient into the wall), the normal on
  porous/free faces is the free cell's gradient, θ is applied on porous/free faces only (wall normal = face normal,
  formula of `correctContactAngle`). Level 2 (ghost α from the contact-angle gradient, as `constantAlphaContactAngle`)
  tested: no measurable change, not kept. Alone, H fixed K 1e-11 (|U| 1.4, no film) but not K 1e-20 (14–49 m/s).
- **F′ — flux-consistent velocity of free cells next to porous/free Darcy faces** (`pEqn.H`, opt-in
  `porousFreeFluxForce 1`). Change F uses the Darcy driving force phiDarcyExplicit/Mf − ∇p (= φ/Mf) on Darcy faces in the
  U reconstruction; on a nearly impermeable porous/free face Mf → 0 and that force is arbitrary: the near-wall gap
  cells had a wall-normal velocity larger than the tangential one (0.87 vs 0.52 m/s at 0.1 ms, K 1e-20). F′ uses
  (φ − HbyA_f·S)/rAUf on porous/free Darcy faces (the reconstructed U carries the face flux, ≈ 0 for an impermeable
  wall). With H + F′: max |U| 0.8–1.1 m/s in all cases (S0 0.75–0.94), no droplets, ordering in K physical.
- **I — no-slip at the porous surface** (`UEqn.H`, opt-in `porousFreeNoSlip 1`). The viscous term couples the gap cell
  to the porous cell centre (distance dx) with μ interpolated between the gap and the (dry → air) porous cell: about a
  quarter of a wall's shear next to water. Measured: near-wall/mean velocity 0.78 (H+F′) vs 0.41 for real walls; the
  rise was 12–28 % too fast. I adds a face Laplacian on porous/free Darcy faces raising the coefficient to 2·μ_free
  (shear μ_free·(U_P − U_porous)/(dx/2); Beavers–Joseph slip ~√K neglected, Da < darcyFaceMaxDa), **bounded below by
  0** (never reduces the interpolated coupling): the unbounded version (2·μ_air next to a wet wall) gave air currents of
  10–60 m/s along wet walls ahead of the meniscus — not understood, open.
**Results H + F′ + I, 2 ms (`P_*`; gap meniscus sim / real walls S0 / Bosanquet, mm):** K 1e-20 walls: w8 θ60
1.27 / 1.25 / 1.16; w15 1.01 / 0.99 / 0.94; w4 1.33 / 1.32 / 1.19; w8 θ40 1.57 / 1.54 / 1.43; w8 θ80 0.73 / 0.72 / 0.69
→ **porous walls = real walls within 2 %** (old porous model S1: −35 to +60 %); max |U| 0.45–1.2 m/s (S0 0.5–1.2). Wall K
(w8): gap 1.27 (1e-20) > 1.23 (1e-14) > 0.79 (1e-11), monotone. K 1e-14: only the surface row wets, behind the meniscus
(plausible: lateral sorptivity ~0.57 mm/√s ≈ 1 cell in the time the gap is wet). K 1e-11 w8: wall front 1.15 mm vs 0.87
alone (gap feeds the wall sideways, front uniform across the 8 cells), gap 0.79; w15: 1.09 / 0.71. No droplets, budget
~1e-26 in all. **Regression:** keywords off → bit-identical to the installed solver (α, p, φ, U, dt; B_nw8_w8_K1e-11).
Intermediate runs (`B_`, `H_`, `HF_`, `I_`, `J_`, `N_`) kept for the record; `P_` = current.
**Mesh (measured):** `P_dx10_w16_t60_K1e-11` (10 µm, gap/walls 16 cells = same 160 µm, `--wall-end 6`, darcyFaceMaxDa
0.5 because K/dx² = 0.1 at 10 µm; √K ≈ 3 µm < dx) vs `P_w8_t60_K1e-11` (20 µm), 2 ms: gap 0.755 vs 0.79 mm (−4 %), wall
front 1.10 vs 1.15 (−4 %), wall water −3 %, max |U| 1.0 both, budget 1e-25. 0.1–0.4 ms: wall water within 2–3 %.
**20 µm overestimates by ~4 %.** Run time 2 ms: 20 µm ~3 min, 10 µm ~60 min (serial).
**`2D_bench` with H + F′ + I on (`variants/*_run_HFI`, `ADD=` option of `makeVariant.sh`, 1 ms, scratch build):**
`gapInletAir` (yarn + air gaps): yarn front 648 µm, saturation 0.4126 vs 0.4129 installed (same to 3–4 digits); **max
gap |U| 0.10 m/s vs 8.6 m/s**: the unexplained gap air jet near the inlet corner (see "Pre-commit checks of F/G", open)
was the same F flaw that F′ fixes. `R3closedRamp`: identical yarn (front 406 µm, saturation 0.1008), gap |U| 0.012.
**Not checked yet:** non-uniform meshes (H and I assume 0.5 weights); parallel/cyclic porous/free faces with H/F′/I;
3D (edges/corners, staircase); air next to wet walls (I bounded, see above); single-yarn case with the keywords on
(no free cells: H/I do nothing, F′ only acts on porous/free faces; expected identical, not run); longer runs (5 ms).
**Committed (2026-10-13, user decision: stay opt-in):** H without the level-2 code (class layout unchanged, so the
backup binaries sharing the library are unaffected); patches `../trialWicking/hybridSolverChanges/patches/0009–0011`
(relative to `OpenFoamV8`). Installed `hybridPorousInterFoam` = `b525086`, previous kept as
`hybridPorousInterFoam_1b007d8`. **Checked:** installed binary vs scratch build, keywords on, `V_w8_t60_K1e-11` and
`V_w8_t60_K1e-20` vs `P_*`: α, p, φ, U at 2 ms bit-identical; keywords off `V_off_w8_K1e-11` vs `B_nw8_w8_K1e-11`
(`1b007d8`): bit-identical. Scratch build `hybridPorousInterFoamH` (+ libraries `...H`) still in `$FOAM_USER_APPBIN` /
`$FOAM_USER_LIBBIN`: obsolete, can be deleted. Keywords to use: `--add porousContactAngleWallLike=1 --add
porousFreeFluxForce=1 --add porousFreeNoSlip=1` (makeSlit.py), `ADD="porousContactAngleWallLike 1;porousFreeFluxForce
1;porousFreeNoSlip 1"` (makeVariant.sh); H needs `activatePorousContactAngle 1` (makeSlit sets it for porous walls).

## Literature: solvers for capillary-driven wicking (search 2026-10-12, web; mostly abstracts, not exhaustive)
Question: has anyone built a solver for **spontaneous** capillary wicking in a dual-scale medium (porous yarns with
saturation-dependent pc + free gaps)? **No such demonstrated solver found.** Closest families:
- **Micro-continuum DBS two-phase** (Soulaine 2018; Carrillo, Bourg & Soulaine 2020 = hybridPorousInterFoam;
  Boubaker et al. 2026): porous/free coupling = continuity of stresses + contact angle, no capillary jump. Their
  imbibition cases are forced (repo tutorial `Fracture/fracture_Imbibition`: fracture inlet U = 1 m/s, θ 45°, matrix K
  1e-13, Brooks-Corey pc0 100 Pa) or have nearly impermeable walls (K 1e-20).
- **Stokes–Darcy with level set, Saint-Étienne** (Abouorm, Moulin, Bruchon, Drapier; Cataldi et al. 2023–2026 on 3D
  interlocks "with capillary effects"; Pucci, Liotier, Drapier 2015 wicking experiments): capillarity as a **pressure
  jump at the moving front** (sharp front, natural condition of the Darcy problem), RTM injection. Closest geometry; a
  sharp-front single-fluid approach, not a saturation (two-phase) model.
- **Two-phase porous medium / free flow coupling theory** (Mosthaf et al. 2011, WRR, DuMux): at the interface "the
  gas phase at the free-flow side has to balance the sum of the water pressure and the capillary pressure", i.e. gas
  pressure continuous = **the condition our diagnosis says is missing** (p_gap − p_yarn = α·pc). Sharp-interface domain
  coupling, gas-only free flow (evaporation), not a single-domain VOF.
- **Grey (partial bounce-back) multiphase lattice Boltzmann** (Zalzale, Ramaioli, Scrivener, McDonald 2016, PRE 94
  053301): free-energy multiphase + effective media, wetting potential at free/grey interfaces, validated on wicking and
  sorption in multiscale systems. Closest in spirit (capillarity consistent across the interface by construction), but LBM.
- **Pore-scale / pore-network for yarns** (Empa/ETH, Carmeliet, Fischer: X-ray + pore network for yarns and interlaces;
  Du et al. 2025 CFD of twisted yarns): resolved or network level, not a fabric REV continuum. Yarn wicking shows
  pore-filling bursts and deviates from Washburn.
- **Single-scale Darcy/Richards wicking** (porousMultiphaseFoam / impesFoam, Horgue; Maier et al. 2025 thin fibrous
  media with Van Genuchten; Masoodi & Pillai paper wicking): no free gaps.
- **LCM dual-scale sink-term models** (Pillai and others): macro scale, sink tuned on unit cells, forced injection.
**Consequence:** an interface term of the Mosthaf type inside the micro-continuum formulation (option (i) above) has a
theoretical basis but no published implementation found in a DBS/VOF solver; the grey-LBM and Saint-Étienne approaches
are the references to cite/compare. Full texts not checked (paywalls/anti-bot); Carrillo 2020 section 5.2 read only
through its tutorial files.

## Next steps
**State (2026-10-13):** the thick-wall slit bench works with H + F′ + I (see "Thick-wall slit bench"): porous walls =
real walls within 2 % (K 1e-20), yarn-like walls (K 1e-11) stable, ~1 m/s, no droplets, water budget ~1e-26, mesh
error ~4 % at 20 µm. **Committed and installed (`b525086`, opt-in keywords); solver repo not pushed yet (push from VS
Code); mini01: pull, `wmake libso` in `libraries/porousInterfaceProperties`, `wmake` in the solver.**
1. ~~Bench dictionaries~~ done: `2D_bench/` is the thick-wall slit bench with the keywords (all checks pass).
   REV: add the keywords, `activatePorousContactAngle 1`, θ, `openFreeTotalPressure 1`, gap water column at the inlet.
2. Air next to wet porous walls with the unbounded I (10–60 m/s): understand (I is bounded for now).
3. Bench extensions: gaps interrupted by porous "crossings" (wall-first, then gap: needs an empty gap to start filling
   from a wet wall, and probably a saturation-dependent contact angle); θ 75 (dry polyester); 5 ms runs.
4. Parallel/cyclic and 3D checks of H/F′/I (REV is cyclic and parallel), then the REV (items below).

**Previous state (2026-10-12, end of session):**
**State (2026-10-12, end of session):** installed solver = of9-port `1b007d8` (A–G, docs `8b35cc4`, pushed); bench
and REV `transportProperties` have `porousFreeDarcyFaces on;`; `tools/initFields.py` starts free cells as pure air.
mini01: rebuild after pulling (`git pull`, `wmake` in `OpenFoamV8/solvers/hybridPorousInterFoam`). Older solver states:
`git worktree add /tmp/hpif_<commit> <commit>`, new `EXE` in `Make/files`, `wmake`.
**Uncommitted work of this session (user commits):** `slit_test/` (new), `tools/pOpenAir` (`openFreeTotalPressure`,
default 0), `2D_bench/constant/transportProperties` (`openFreeTotalPressure 0;`), `tools/waterBudget`, bench scripts and
figures, this file, `.gitignore` entries; solver patches 0007/0008 in `../trialWicking/hybridSolverChanges/patches/`.
1. **Gap capillarity (`slit_test/`, see "Slit tests" → "Full series"):** S0 (real walls) validated vs Bosanquet. Open, in
   this order:
   a. **K 1e-14 / 1e-17 walls make the gap rise faster than impermeable walls** (unphysical) and the K 1e-14 wall front
      looks too fast: find why (cleanest symptom; look at the near-wall gap cells, the α flux on the porous/free faces,
      pc at the dry state).
   b. **Porous contact-angle model (S1):** ±25–60 % at gap 4 / θ 40 / θ 80, spurious |U| 30–60 m/s. Read
      `porousInterfaceProperties.C` (`correctContactAngleDB`) and compare with `constantAlphaContactAngle`.
   c. No-gap reference for S2's wall front; mesh dependence (16 cells across); wet porous wall effective angle.
   d. `2D_bench` `base` with `openFreeTotalPressure 1` (and porous faces kept off the open outlet).
   e. REV: total-pressure inlet; porous faces on the outlet closed or yarns ending before it.
2. Open G items (`F/G open questions` checklist): small 3D bench (edges/corners, staircase), 10 µm mesh, contact-angle
   model + G, gap air jets near a free inlet next to open boundaries (numerical, unexplained).
3. REV: top/bottom closed walls or air padding (open porous boundary unstable), complete `REV/` (was `REV_hybrid`; scripts,
   `job.slurm`, `build_fields.py --k-mode scalar --cut-cells binary`, initFields with pure-air gaps), local smoke
   test, then mini01.
4. Later: tensor K (solver change), real K/pc/contact angle (polyester).

## Pitfalls met
- `foamDictionary -set` rewrites the whole file and **strips the comments**. Edit dictionaries with sed or by
  hand.
- With `timePrecision 6`, steps of ~1e-12 s get the same time name; use 12 for step-by-step writes.
- **A `clean` pattern `[0-9].*` (for time folders like `0.00025`) also deletes `0.orig`.** Happened once in the
  2026-10-12 cleanup (sources restored). `clean` now matches names made only of digits, `.`, `e`, `+`, `-`.
- **The repo-root `.gitignore` ignores `[1-9]*/` and `0.*/` (time folders):** it also caught `2D_bench` and
  `0.orig`. Exceptions `!2D*/` and `!0.orig/` added next to the existing `!1D*/`.
- **Re-reading a file after editing it in memory** (`makeSlit.py`, `--fill`) silently dropped the wall BC: check the
  written `0/` fields of a generated case (`grep -A3 top 0/alpha.wetting`), not only the script.
- If `postProcess -func writeCellCentres -time 0` runs without a `0/` folder, it writes C, Cx, Cy, Cz into
  `constant/`.
