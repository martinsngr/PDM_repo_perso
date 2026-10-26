# waterOnlyReservoir — change J: a reservoir patch that exchanges water only (2026-10-26)

**Why.** The reservoir (inlet) of the wicking cases lets air through: on porous faces the α flux is α_b·φ_b (the
inflow at α_b 0.99 carries 1 % air: the 1D hybrid's ~2 % uptake deficit, `../../NOTES_solver.md`), outflow carries
air in proportion to α of the cell, and on free faces an air-filled cell next to the reservoir vents air through it.
Its two parts also disagree on the water pressure: porous faces air at 0 Pa with S 0.99, i.e. water at −pc(0.99) =
−676 Pa; free faces water at total pressure 0. In the 2D bench ~10 % of the gap inflow leaves again through the yarn
inlet faces (water short circuit). In the REV smoke test (2026-10-26, old inlet) the dry yarns drained the gap water
column within 0.1 ms, the free inlet cells turned to air, air flowed in through the open top/bottom and out through
the reservoir face (9e-8 m³/s at 0.1 ms), and α went negative (−0.025) in air-filled free inlet cells: dt collapsed
and stopGuard ended the run at 0.21 ms. A bath supplies water at its own pressure and lets no air through.

**Change J (solver, opt-in `waterOnlyPatches (<patches>);` in `constant/transportProperties`; scratch build
`hybridPorousInterFoamJ`, patch `solver/J_waterOnly.patch` on of9-port `f9d5e41`):**
- porous faces of those patches: air mobility 0 (`updateVariables.H`), so the pressure equation carries the water
  Darcy flux only;
- all their faces: α flux = total flux (`alphaEqn.H`);
- their free faces: closed (zero conductance and flux, reconstructed U consistent) while the cell next to them is
  air-rich (α < 0.5), open both ways while it holds water (`pEqn.H`).
**p BC** (`tools/pOpenAir`, patch `solver/pOpenAir_waterOnly.patch`): on those patches water at
`reservoirWaterPressure` (Pa, default 0): porous faces p = p_w + (1 − α)·pc, free faces p_w (total pressure on inflow).

## Runs and predictions (written before the runs)
Solver: scratch `hybridPorousInterFoamJ` (installed of9-port `0f6c6d4` + J); laptop, serial.

| Run | Case | Change | Prediction |
|---|---|---|---|
| `1D_regression` | `../wicking1D/ABC` inputs, 0.03 s | none (no keyword) | bit-identical to the stored `../wicking1D/ABC` (every write) |
| `1D_waterOnly` | same | `waterOnlyPatches (inlet)`; inlet p BC unchanged (air at 0 Pa with α_b 0.99 on the inflow face = water at −pc(0.99) = −675.8 Pa) | inlet air fraction +1.00 % → 0; first-cell S 0.938 → ~0.97; p_air first cell 1064 → ~500 Pa; front −1.6 % → ~−0.6 %, uptake −4.6 % → ~−2.3 % vs the similarity solution (impesFoam: −0.5 / −2.2 %) |
| `1D_bath0` | same | water-only, inlet water at 0 Pa (`0/p`: p = (1 − α)·pc) | another problem (inlet S → ~0.999 instead of 0.99): faster than the S_in 0.99 reference by a few %; no pass/fail vs it; dt and step count recorded |
| `bench_regression` | `../../meshing_strat_trial/2D_bench` inputs, 2 ms | none | bit-identical to the installed solver on the same case (scratchpad run `inst_serial` of 2026-10-26) |
| `bench_waterOnly` | same | `waterOnlyPatches (inlet)`, `reservoirWaterPressure 0` | no water out through the yarn inlet faces (short circuit gone); air through the inlet ~0; wall front at 2 ms ≥ 1.15 mm (walls fed at 0 Pa instead of −676 Pa); gap meniscus 0.75–0.85 mm; `check.py` passes |

Afterwards: the REV smoke test with the water-only inlet (scratch copy, 4 cores): should pass 0.21 ms (where the old
inlet failed), no air through the inlet, max |U| at the inlet below the old run's 2.3–2.8 m/s.

## Results (2026-10-26)

**Regressions: pass.** `1D_regression` = stored `../wicking1D/ABC` (α, p, U, φ at all 30 writes, 120 files);
`bench_regression` = installed solver (`inst_serial`, 440 files; the p files differ only by the BC source text that
OpenFOAM writes into them, the numbers are identical); water budget identical. The new `tools/pOpenAir` without the
keyword gives the same numbers.

**1D** (`waterOnly1D.py`, slopes vs √t for t ≥ 10 ms; reference: front 18.044, uptake 6.1048 mm/√s):

| Run | front (mm/√s) | vs ref | uptake (mm/√s) | vs ref | first-cell S | inlet air / total flux | p_air first cell (Pa) | steps |
|---|---|---|---|---|---|---|---|---|
| impesFoam (reference run) | 17.95 | −0.5 % | 5.970 | −2.2 % | 0.974 | — | 529 | |
| hybrid, current inlet (= `1D_regression`) | 17.76 | −1.6 % | 5.824 | −4.6 % | 0.938 | +1.00 % | 1064 | 48,921 |
| `1D_waterOnly` (water at −pc(0.99)) | 17.84 | −1.1 % | 5.900 | −3.4 % | 0.955 | 0.00 % | 783 | 48,922 |
| `1D_bath0` (water at 0 Pa) | 18.61 | +3.1 % | 6.383 | +4.6 % | 0.964 | 0.00 % | 1301 | 49,005 |

- Air entry removed (**pass**). Front and uptake improve in the predicted direction but by half the predicted amount
  (**partial**): the 1 % air entry explains ~1.2 % of the uptake deficit, not ~2 %; the hybrid stays ~1.2 % below
  impesFoam (first cell drier, 0.955 vs 0.974; air pressure higher, 783 vs 529 Pa): cause not isolated.
- `1D_bath0`: a different problem, as predicted (bath at the inlet level). The first cell does not saturate: the air
  near the inlet can no longer leave through it and its pressure rises to 1.3 kPa (pc of the first cell). Same cost.

**Bench** (`benchCompare.py`; `check.py` of `2D_bench` on each run; inlet flux by face type, m³/s, out > 0):

| Run, 2 ms | yarn faces water | yarn faces air | gap faces water | meniscus | wall front | wall water | max \|U\| | checks |
|---|---|---|---|---|---|---|---|---|
| `bench_regression` | +2.9e-10 (out) | +4.0e-12 | −2.5e-9 | 0.790 mm | 1.15 mm | 369 | 1.20 | all pass |
| `bench_waterOnly` | −1.8e-10 (in) | +2.2e-14 | −2.0e-9 | 0.790 mm | 1.17 mm | 373 | 1.20 | all pass |

- Short circuit gone (**pass**): the yarn walls take water through their own inlet faces at every write (before:
  water left through them from 0.5 ms on, ~10 % of the gap inflow). Residual air on the yarn faces ≤ 0.2 % of their
  water flux at 0.05 ms, 0.01 % at 2 ms (the α limiter trimming the boundary water flux, not investigated).
  Total inflow −2 % (the walls take more from the reservoir, less from the gap). Predictions met.
- **Hydrostatic reservoir** (`tools/pOpenAir`: p_w = reservoirWaterPressure + ρ_w g·(Cf − reservoirReferencePoint)):
  `bench_waterOnly_hydro` = `bench_waterOnly` (numbers identical: the inlet lies at the reference height).
- **Horizontal wicking** (`bench_horizontal`: gravity −z, across the slit, so the bath face is vertical; bath surface
  at the top of the inlet, `reservoirReferencePoint (0 0 0.00048)`): all checks pass; meniscus 0.810 mm at 2 ms
  (+2.5 %: gravity no longer opposes the rise, ρgh ≈ 8 Pa vs 450 Pa), wall front 1.17 mm, lower/upper wall asymmetry
  0.001 in α (hydrostatic difference across the slit ~2 Pa).
- **Installed build** (of9-port + J, `wmake` of the same sources): bench run bit-identical to the scratch build
  (`bench_waterOnly_hydro`, 440 files, water budget).
