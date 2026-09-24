# trialWicking — working notes

Status and findings for the wicking cases. Last updated 2026-09-23.

## Cases

| Folder | What it is |
|---|---|
| `./` (1D) | 1D equivalent of the yarn case: column length = yarn centreline unfolded along the crimp (3.446 mm for x 0.4–3.6 mm; straight 3.2 mm), section 0.55 mm (width) × 0.237 mm (mean thickness), both measured from slices of `yarn-c.stl`. 1×172×1 cells (20 µm), reservoir = bottom 0.2 mm cellZone held at Sb 0.99 via `fixedSb`, pc0 5000 Pa, K 1e-11, Coats CFL. Top is open to air (`outlet` p fixed 0, Ub fixed 0): with the old `darcyGradPressure` top the air could only leave counter-current back into the reservoir, which made the column fill much more slowly than the yarn (mean Sb 0.59 vs 0.91 at 0.06 s). The yarn vents air through `yarn_to_fluid` along its whole length. Open top: mean Sb 0.36 / 0.50 / 0.70 / 0.84 at 0.01 / 0.02 / 0.04 / 0.06 s (yarn 0.42 / 0.56 / 0.77 / 0.91), front at the top at ~0.035 s; 0.1 s runs in ~75 s. The real section is lens-shaped: its area (STL volume / unfolded length = 9.47e-8 m²) is 27 % smaller than the 1.30e-7 m² rectangle, so scale uptake volumes by 0.73 before comparing with the 3D case. (Before 2026-09-24: 1 m column, pc0 100 Pa, ~1 cm equilibrium rise.) |
| `singleYarn_IMPES_yarn/` | Original 3D yarn case (`yarn-c.stl`): wetting from below in z through a `wetInlet` patch, fixed deltaT 1e-9. Kept as reference ("original set up" commit). Its mesh has 24 negative-volume cells (see below). |
| `singleYarn_IMPES_vertical/` | The 1D vertical test moved onto the yarn geometry. **Current working case.** |

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
- Current run: 0.02 s per step, about 2.2M steps to reach 0.1 s, about 12 h on 4 cores.
- A faster PC gives 1.5–2× at most. More cores don't help: 15k cells are already communication-bound.

### Physics
- pc0 = 5000 Pa is consistent with K = 1e-11 by Leverett scaling (about 4–8 kPa); the 1D value of 100 Pa corresponds to millimetre pores and is not realistic for a yarn.
- The wicking rate constrains K·pc0; the equilibrium height (pc0/ρg, about 0.5 m here) constrains pc0. A 3.2 mm segment only shows the rate, so fitting K and pc0 needs experimental-length samples.

## Running

```bash
cd singleYarn_IMPES_vertical
nohup ./run > run.out 2>&1 &
grep "^Time =" log1.impesFoam | tail -1     # progress
```

- **If the run dies, do NOT rerun `./run`:** it deletes meshes, processor folders and results. Instead, set `startFrom latestTime` in `system/controlDict`, relaunch with `nohup mpirun -np 4 impesFoam -parallel -noFunctionObjects > log2.impesFoam 2>&1 &`, then run `reconstructPar` and `postProcess -func sampleDict`.
- **Laptop:** set "lid close → Do nothing" and "sleep → Never" while plugged in. WSL2 may also shut down when no WSL window is open.
- **Outputs:** `liquidBalance.csv` (uptake over time) and `postProcessing/sampleDict/<t>/alongYarn_Sb.xy` (Sb(x) profiles).

## Next steps

1. Analyse the 0.1 s run: front position over time, uptake, Sb(x) profiles.
2. Cheap speed-ups: `maxCo 0.9` (about 1.8×); benchmark 1, 2 and 4 cores; `DIC` or `GAMG` instead of `diagonal` PCG for p; check whether the maximum Coats CFL sits in the tiny snapped cells.
3. **Main lever:** replace the snappy mesh with a mesh that follows the yarn (a Python generator writing a swept `blockMeshDict` from STL slices, about 100 µm axial cells), or a 1D model over the centreline length. This enables cm-long samples to compare with experiments.
4. Report the Todd bug upstream (phorgue/porousMultiphaseFoam) or patch the fork, and commit the fork's local changes (`setDeltaT.H`, `updateLiquidContent.H`, `Make/files`).
5. Fabric scale: `hybridPorousInterFoam` on a Cartesian unit cell with the yarns as a porosity field. The yarn mesh does not carry over, but the calibrated K/kr/pc do; check that its kr and pc models match.
