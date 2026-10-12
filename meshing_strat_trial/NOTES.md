# meshing_strat_trial — working notes

Fabric REV (several yarns + the gaps between them) with `hybridPorousInterFoam`: vertical wicking from a
saturated inlet, capillary drive only. Follows the 1D and single-yarn hybrid cases of `../trialWicking`
(see `../trialWicking/NOTES.md` for their setup, solver changes A/B/C and verification).
Last updated 2026-10-12 (session 1, after change E and the cleanup).

## Folder layout

| Path | What it is |
|---|---|
| `Textiles/PW-22-15-0.4-0.5.stl` | TexGen plain-weave model (cm), copy in `constant/triSurface/` (identical, md5 checked) |
| `inspect_stl.py` | STL checks + REV detection → `rev_domain.json` (`--zgap` adds free space above/below) |
| `build_fields.py` | Uniform hex mesh (`blockMeshDict`) + `eps`, `K`, `fYarn`, `yarnID` from the STL |
| `check_periodicity.py` | Compares opposite REV faces (is `cyclic` valid?) |
| `system/`, `constant/`, `0/` (top level) | Original meshing trial: mesh + tensor-K fields, `fractional` cut cells. Not a solver case (placeholder `system/`). Kept as is. |
| `tools/` | Shared by both cases: `runTools.sh`, `initFields.py`, coded BC `pOpenAir`, function objects `coatsTimeStep`, `liquidBalance` |
| `2D_bench/` | Small 2D test: porous slab between two free layers, wetted from its end |
| `REV_hybrid/` | The REV case (**in progress, not runnable yet**) |
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

### `2D_bench/`
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

### `REV_hybrid/` (incomplete)
Present: `system/{controlDict, fvSchemes, fvSolution}`, `constant/{transportProperties, g,
momentumTransport, dynamicMeshDict}`, `0.orig/{p, U, Uwetting, UnonWetting}` (same as the bench; cyclic patches via
`setConstraintTypes`). Missing: `Allpre` (build_fields `--k-mode scalar --cut-cells binary` → blockMesh →
checkMesh → cell centres → initFields), `run` (decompose, serial precompile of coded BC/FOs, mpirun),
`clean`, `caseSetup` (N), `decomposeParDict`, `job.slurm`, endTime.

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

## Next steps
1. ~~Fix 1 into the solver repo~~: done (change E, `c3a2e6e`, installed, pushed). To do: rebuild on
   mini01, consider reporting the bug upstream (Franjcf/hybridPorousInterFoam).
2. **Rerun all bench variants with the installed solver (E)** (`./Allpre`, then `variants/makeVariant.sh <v> steps`
   and `run`): the pre-E variant results with free cells only showed the bug.
3. **Diagnose the second failure** with the face-dump build (`../trialWicking/hybridSolverChanges/debug_faceDump/`,
   to rebuild on top of E; change `DBGON` and the face list in `dbgSetup.H` to dump at the steps where water first
   enters the free cells next to the inlet and where α first exceeds 1): pressure on yarn/gap faces vs −α·pc,
   flux on the free inlet faces, MULES boundedness.
4. Then design the yarn/gap face treatment (consistent capillary/pressure term on those faces), test on the bench.
5. **Open top/bottom with porous faces:** close them (walls) or pad with free cells for the REV.
6. Then complete `REV_hybrid` (scripts, `job.slurm`, `build_fields.py --k-mode scalar --cut-cells binary`),
   local smoke test, number of cores.
7. Later: tensor K (solver change), real K/pc/contact angle.

## Pitfalls met
- `foamDictionary -set` rewrites the whole file and **strips the comments**. Edit dictionaries with sed or by
  hand.
- With `timePrecision 6`, steps of ~1e-12 s get the same time name; use 12 for step-by-step writes.
- **A `clean` pattern `[0-9].*` (for time folders like `0.00025`) also deletes `0.orig`.** Happened once in the
  2026-10-12 cleanup (sources restored). `clean` now matches names made only of digits, `.`, `e`, `+`, `-`.
- **The repo-root `.gitignore` ignores `[1-9]*/` and `0.*/` (time folders):** it also caught `2D_bench` and
  `0.orig`. Exceptions `!2D*/` and `!0.orig/` added next to the existing `!1D*/`.
- If `postProcess -func writeCellCentres -time 0` runs without a `0/` folder, it writes C, Cx, Cy, Cz into
  `constant/`.
