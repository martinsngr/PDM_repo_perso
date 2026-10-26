# parallel_H — changes H, F′, I on processor boundaries (2026-10-26)

**Question:** are the porous/free-face changes correct when a yarn surface (porous/free faces) lies on a processor
boundary? Untested so far (`../../NOTES_solver.md`, open issues) and needed before the REV runs in parallel.
**Answer:** H is not (gap rise +14 % at 2 ms, spurious velocity ×2). A one-line fix restores the serial result.
F′, I, G and E behave consistently there. **Fix committed as of9-port `0f6c6d4` and installed (2026-10-26):** the
installed build reproduces `parfix` and `serial` bit-identically (every file of every write, water budget).

## Code reading (before the runs)
- `OpenFoamV8/libraries/porousInterfaceProperties/porousInterfaceProperties.C`, `calculateK()`, with H on: the
  porous cells of `alpha1Smoothed` get the area mean of α of their free neighbours, cell by cell. The processor patch
  values of `alpha1Smoothed` still hold the neighbour cell values from before that loop (the porous neighbour's
  saturation). `fvc::grad(alpha1Smoothed, "nHat")` (Gauss linear) uses them on processor faces, so a free cell next to
  a porous cell across a processor boundary sees the yarn saturation as an α jump: point (1) of H is undone on those
  faces. Cyclic patches read the neighbour values from the internal field and are not affected (the REV y-cyclic
  patches carry no porous/free faces anyway: `../../meshing_strat_trial/tools/revGeometry.py`).
- G (`porousFace`, harmonic `k0f` on coupled faces, `pc *= Solid` multiplies the boundary values too), E
  (`binarySolidf.H`), F′ (`pEqn.H`) and I (`UEqn.H`) use face indicators set on every patch and standard
  interpolations: no cell-by-cell change without a boundary update.
- Candidate fix (`solver/H_processor_fix.patch`): `alpha1Smoothed.correctBoundaryConditions();` after the loop. In
  serial nothing changes (the non-coupled patches of this temporary field are `calculated`, which `evaluate` leaves
  as they are; cyclic patch values are not used by the interpolation).

## Predictions (stated before the runs)
- Serial: lower/upper mirror asymmetry at round-off. **Measured 1e-4 to 2e-4** (solver-tolerance level, not
  round-off).
- Parallel, split on the lower yarn surface, installed solver: asymmetry far above that, mostly at the meniscus next
  to the lower wall. **Measured: asymmetry up to 0.39, but the whole meniscus rises faster** (lower, upper and mid-gap
  rows alike), not only next to the lower wall.
- Same with the fix: serial/parallel noise level; serial with the fix bit-identical. **Both confirmed.**

## Setup
Case: copy of `../../meshing_strat_trial/2D_bench` (`0/`, `constant/`, `system/` of 2026-10-13: thick-wall slit,
yarn walls 8 | gap 8 | yarn walls 8 cells of 20 µm, K 1e-11, θ 60°, G + H + F′ + I, 0.1 mm water column), 2 ms.
Solver: installed `hybridPorousInterFoam` = `b525086` (A–I). Laptop, 2026-10-26. Two processors, `method manual`
(`decomposeParDict`, `makeDecomposition.py` writes `constant/cellDecomposition`).

| Run | Processors | Processor boundary | `libporousInterfaceProperties` |
|---|---|---|---|
| `serial` | 1 | — | installed |
| `par` | 2 | lower yarn surface, between z-cells 7 and 8 (100 faces, porous/free over the wall length) | installed |
| `parfix` | 2 | same | scratch build with the patch (same name, first in `LD_LIBRARY_PATH`) |
| `parmid` | 2 | mid-gap, between z-cells 11 and 12 (free/free faces only): control for the ordinary parallel difference | installed |
| `serialfix` | 1 | — | scratch build with the patch |

`runs/<case>/`: inputs, the writes at 0.05, 0.1, 0.5, 1, 1.5, 2 ms (reconstructed), `waterBudget.csv`,
`liquidBalance.csv`, log filtered as `runTools.sh` with `LOG_EVERY=100` plus `.tail`. Runs done in the session
scratchpad (logs outside the workspace), then copied here. Comparison: `compare.py` → `compare_output.txt`;
`bitcheck.sh serial serialfix` (every file of every write).

## Results (2 ms; all write times in `compare_output.txt`)

| Run | gap meniscus at lower wall / upper wall / mid-gap (mm) | wall front lower / upper (mm) | max \|α − α_serial\| | mirror asymmetry max \|α(k) − α(23−k)\| | max \|U\| (m/s) | steps |
|---|---|---|---|---|---|---|
| `serial` | 0.7902 / 0.7902 / 0.7783 | 1.14 / 1.14 | — | 1.9e-4 | 0.98 | 8490 |
| `par` | 0.9001 / 0.8973 / 0.8891 | 1.22 / 1.20 | 1.0 | 0.35 | 2.09 | 8561 |
| `parfix` | 0.7902 / 0.7902 / 0.7783 | 1.14 / 1.14 | 8.9e-4 | 6.5e-4 | 0.98 | 8490 |
| `parmid` | 0.7901 / 0.7902 / 0.7782 | 1.14 / 1.14 | 1.3e-3 | 1.1e-3 | 0.98 | 8490 |
| `serialfix` | bit-identical to `serial` (440 files, `waterBudget.csv`) | | 0 | | | 8490 |

- `par` departs from `serial` from the first write (meniscus at the lower wall 0.0935 vs 0.0875 mm at 0.05 ms) and
  stays 12–15 % ahead; max |U| 1.3–2.3 m/s vs 1.0–1.2 m/s over the writes.
- Over all writes: `parfix` within 8.9e-4 of `serial`, `parmid` within 1.3e-3, i.e. the fix brings the yarn-surface
  split to the ordinary serial/parallel difference.
- Water budget: `serial`, `parmid` imbalance ~1e-27 m³. `par` and `parfix`: −2.57e-17 m³, identical in both and
  constant from the first write on, i.e. a one-time loss at the start of ~3e-3 cell volumes (4e-6 of the water at
  2 ms). Not from H (same with the fix); cause not looked into.

## Conclusions
- **Installed solver: fail.** A yarn surface on a processor boundary makes the gap rise 14 % faster at 2 ms and
  doubles the spurious velocity. A scotch decomposition of the REV cuts many yarn surfaces.
- **Fix: pass** (parallel = serial within the ordinary parallel difference; serial bit-identical). Committed as
  `0f6c6d4` (docs `f9d5e41`); pre-fix library kept in `$FOAM_USER_LIBBIN/backup_b525086/`.
- F′, I, G, E on processor porous/free faces: consistent in this planar 2D case. Not tested: 3D processor faces at
  edges and corners of staircased yarn surfaces, cyclic porous/free faces (none in the REV).

## Rerun
From a copy outside the workspace, with `meshing_strat_trial/tools` copied next to the case folders (the
dictionaries include `../../tools/...`):
```bash
mkdir -p /tmp/pH && cp -r runs/par /tmp/pH/par && cp -r ../../meshing_strat_trial/tools /tmp/pH/tools
cd /tmp/pH/par
rm -rf 0.0* 5e-05 liquidBalance.csv waterBudget.csv log.*    # keep 0/, constant/, system/
hybridPorousInterFoam -postProcess -time 0 > log.precompile 2>&1   # compiles the coded objects; ends with an
rm -f liquidBalance.csv waterBudget.csv                             # abort from waterBudget (harmless)
decomposePar > log.decomposePar 2>&1
mpirun -np 2 hybridPorousInterFoam -parallel > log.hybridPorousInterFoam 2>&1 && reconstructPar > log.reconstructPar 2>&1
```
Scratch library with the fix: copy `OpenFoamV8/libraries/porousInterfaceProperties` (`Make/`, `.C`, `.H`), apply
`solver/H_processor_fix.patch`, set `LIB = <dir>/libporousInterfaceProperties` in `Make/files`, `wmake libso`, then
run with `LD_LIBRARY_PATH=<dir>:$LD_LIBRARY_PATH mpirun -np 2 -x LD_LIBRARY_PATH hybridPorousInterFoam -parallel`
(`ldd $(which hybridPorousInterFoam) | grep porousInterface` shows which copy is loaded).
