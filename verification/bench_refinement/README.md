# Mesh refinement of the porous strip bench, original solver (2026-10-15)

**Question:** the original solver (`be54696`, OF9 port, none of A–I) diverges on the all-porous strip
(`../bench_ddtCorr`, 5 × 172 × 3 cells, step 351 = 3.5e-5 s). Is this an under-resolution effect that goes away on a
finer mesh, or does it persist on finer meshes?

**Case:** `case/` = copy of `../bench_ddtCorr/case` (column 0.55 × 3.446 × 0.237 mm, all porous, K 1e-11, ε 0.5,
VG pc0 5000 Pa m 0.5, BC n 3, dry 0.002 with the 0.2 mm ramp, reservoir inlet, symmetry sides, fixed dt, end 2e-4 s).
`transverseSpread` prints per step the max over rows of (max − min α across the row).
`./makeRun.sh <name> <r> <dt>` splits each cell r times in each direction (cells 110/r × 20/r × 79/r µm), same initial
function (20 µm ramp boxes), same solver.

**Solver:** `hybridPorousInterFoam_be54696` (the binary of `log.i_original`; it links today's shared libraries, H
inactive without its keyword). Check: run r1 must reproduce `../bench_ddtCorr/log.i_original` (divergence at step 351).

## Runs

| Run | r | cells | dt (s) | why |
|---|---|---|---|---|
| r1_dt1e-7 | 1 | 2,580 | 1e-7 | reproduces `log.i_original` |
| r2_dt1e-7 | 2 | 20,640 | 1e-7 | mesh refined, same dt |
| r2_dt2.5e-8 | 2 | 20,640 | 2.5e-8 | mesh and dt refined together (dt/Δx² constant, explicit capillary diffusion) |
| r4_… | 4 | 165,120 | decided after r2 | only if r2 is not conclusive |

## Predictions (written before the runs)

- The A mechanism (`fvc::grad` cell gradients interpolated to faces cannot see an odd-even pattern) is a property of
  the scheme on any mesh, not of resolution. **Prediction: the mode appears on every mesh**, as a cell-to-cell
  (grid-scale) pattern, and the run diverges on r2 too. Growth per unit time equal or faster on the finer mesh (a
  grid-scale mode has a shorter wavelength on a finer mesh).
- Smaller dt alone (r2, dt 2.5e-8) does not remove it (`e_A_c0_dthalf` with A: halving dt did not help).
- **Decision:** diverges on r2 at both dt → not an under-resolution effect (pass for the hypothesis "scheme defect,
  fixed by A + B"). Survives to 2e-4 s with spread ≤ 1e-6 on r2 → resolution-dependent, the A/B evidence must be
  re-examined. Grows but saturates without diverging → inconclusive, run r4.

## Results (2026-10-15, laptop, serial, `hybridPorousInterFoam_be54696`)

| Run | steps | spread > 1e-3 at | spread > 1 at | end |
|---|---|---|---|---|
| r1_dt1e-7 | 352 | 6.5e-6 s | 3.48e-5 s | diverged (spread 1e55), **identical to `log.i_original`** |
| r2_dt1e-7 | 127 | 4.8e-6 s | 1.23e-5 s | diverged (spread 4e67) |
| r2_dt2.5e-8 | 386 | 4.4e-6 s | 9.6e-6 s | diverged (spread 2e51) |

- **Pass (prediction confirmed):** the original diverges on the refined mesh at both dt, and earlier in physical time
  (3.5e-5 → 1.2e-5 → 9.6e-6 s). Refinement makes it worse, so it is not an under-resolution effect. r4 not needed.
- Smaller dt on r2 (÷4) does not delay it in physical time.
- Not checked: the spatial pattern of the mode on r2 (cell-to-cell vs longer wavelength), i.e. whether the faster
  growth is the shorter grid-scale wavelength. Only one solver version (original); A and A+B+C not rerun on r2.
- Logs: `<run>/log.<run>` (git-ignored).

## Why it diverges (2026-10-15, follow-up)

### 1. Mode shape in the solver (`modeShape.py`, dump runs `r1_dump`, `r2_dump`, `r1_zoom` every 2 steps to 8.2e-6 s)
- **The 1D profile breaks first, within 2–6 steps, before any transverse growth.** Row means (20 µm rows) at 0.6 µs:
  the ramp turns into equal pairs (0.743/0.644 → 0.716/0.715, 0.545/0.447 → 0.495/0.495) and the front inverts: row 8
  0.150 → 0.117, row 9 0.051 → 0.150 (row 9 > row 8, non-monotone). The front is then frozen for ~6 µs (rows 8/9
  stay 0.117/0.150, row 10 creeps 0.002 → 0.011).
- Transverse spread 1e-5 (step 2–20; the seed is not round-off, likely the GAMG relTol 0.1 solve), flat or slowly
  decaying up to 6.2 µs, then ×450 in 4 steps (6.4–6.6 µs) when row 10 (the dry cell ahead of the frozen front) starts
  filling: rows 9–10 go 0.150/0.011 → 0.040/0.123. From then on the pattern alternates cell to cell in z (parity 0.8–0.97)
  and along y, max |U| ~1 m/s, divergence at 3.5e-5 s.

### 2. Darcy-limit model of the original transport (`darcyModel.py`, Python, no momentum equation)
Same step order and stencils as be54696 (cell-gradient phase velocities → `phirPore`, upwinded α fluxes, explicit α),
total flux from a Darcy pressure equation (rAUf = Mf). Seed 1e-10 random on α. 5 × 172 × 3, run to 1e-5 s.

| Variant | dt 1e-7 | dt 1e-8 |
|---|---|---|
| A (face Darcy fluxes, `snGrad`, b0c0f67) | stable, spread 6e-10 → 5e-10, smooth front | stable, same |
| original (cell `fvc::grad`, `interpolate(Ur)`) | front inverts at step 1 (rows 8/9 0.150/0.051 → 0.000/1.000), bounds clipped from step 1 | step 1: 0.150/0.051 → 0.051/0.157, clipped from step 3 |
| wideFaceAlpha (diagnostic: cell gradients, divided by the face α as in A) | as original | as original |

- **The original transport discretisation alone is unstable at the wicking front**, independent of dt (10× smaller dt
  still fails within 3 steps) and without any momentum contribution. A, same model otherwise, is stable. The per-cell
  division by α (`Uwetting/alpha1` before interpolation) is not the cause (wideFaceAlpha fails the same way).
- First step of the model = first steps of the solver: same direction (row 8 empties into row 9, row 9 above row 8).
  The solver is slower (350 steps instead of 1–3): its total flux comes from the momentum equation with inertia
  ρ/(ε dt) ≈ 1e10 ≫ drag μ/K ~1e6–1e8 at dt 1e-7, so φ follows the capillary forcing over ~ρK/(με) = 2e-5 s (water)
  instead of instantly. Not tested: the model with the inertial rAU.

### 3. Mechanism (stencil reading, consistent with 1–2; not a formal stability proof)
In the original the water velocity of cell j is M1(α_j)·(…∇pc…) with ∇pc_j = (pc_{j+1} − pc_{j−1})/2Δ, and the
flux on face j|j+1 is the average of the velocities of cells j and j+1. At the front (cell 9 wet, cell 10 dry):
- face 8|9 carries half of cell 9's velocity, driven by pc_10 − pc_8 (pc ≈ pc0/Se: 2.5 MPa dry vs 30–100 kPa): the dry
  cell 10 sucks water out of cell 8, across cell 9;
- face 9|10 carries half of cell 9's velocity plus half of cell 10's, which is ~0 (kr ∝ Se³ at Se 0.002);
→ water leaves 8 and piles up in 9 instead of entering 10: inverted, frozen front. The scheme is not monotone (a cell's
update depends on the cell two away with the wrong locality), and pc(S) ~ 1/Se near dry makes the error large at
once. The odd and even cells are coupled only through the cell-gradient average (zero damping of a cell-to-cell pattern,
uniform-state analysis), so nothing removes the pairs. With A each face flux uses its own two cells (snGrad) and the
face mobility: monotone and stable.
- **Open:** why the transverse pattern takes over at 6.4 µs (the trigger is visible: the frozen front releasing into
  row 10; the amplification across the strip is not isolated). Not done: an eigenvalue analysis of the linearised step
  around the front profile; the Darcy model with the inertial rAU (to reproduce the 350-step delay).

## Does the B failure come from the momentum path? (2026-10-15, model extended)

`darcyModel.py` 6th argument = total-flux path: `darcy` (Darcy limit, rAUf = Mf ≈ A+B without C), `mom` (pEqn.H:
rAU = 1/(ρ/(ε dt) + Drag), HbyA from the old U, OF9 ddtCorr with the flux-normalised coefficient, U reconstructed
from the fluxes), `mom0` (no ddtCorr), `steady` (no inertia, rAU = 1/Drag); extras `+V` implicit viscous Laplacian,
`+C` upwind convection with rhoPhi from the α step, `+T` dev2(T(grad U)), `+L` linearUpwind correction; `NCORR=2`
two pressure correctors with H rebuilt from the corrected U; `SEEDRAMP=1` seed only in the 0.2 mm ramp; `NX=1 NZ=1` 1D.
Not in the model: MULES limiter (clip instead), correctUBc, constrainHbyA / inlet U BC, iterative GAMG solve.

All with A, dt 1e-7, 5 × 172 × 3 unless noted:

| Flux path | Seed | Transverse spread | 1D profile | End |
|---|---|---|---|---|
| darcy | 1e-10 all / 1e-5 ramp | decays | monotone | stable to 6e-5 s, front 0.230 mm |
| mom, mom0 (dt 1e-7, 5e-8, 2.5e-8; also 1D) | 1e-10 all | flat until the collapse | non-monotone from 1.2–1.9 µs | **1D collapse at 3.5–3.8e-5 s, same physical time at every dt** |
| mom+C | 1e-10 all | flat | non-monotone from 2.6 µs | stable to 6e-5 s, front 0.210 mm |
| steady | 1e-10 all | flat | monotone | stable |
| steady+C, steady+V+C | either | — | non-monotone at 0.6 µs | collapse at step 7 (solver steadyState: crash at 73–139 steps) |
| mom+V+C (+T, +L, NCORR=2) | 1e-5 ramp | **decays 4e-5 → 1.2e-5** | non-monotone from 2.6–3 µs | stable to 6e-5 s, front 0.210 mm |
| solver A only (`../bench_ddtCorr/log.ii_A_c1`) | (solver) | **grows 2.7e-5 → 8e-3 → 0.14 at steps 20 / 100 / 200**, rows 6–8 | — | runs to 2e-4 s, spread saturates 0.05–0.14 |

- **Not reproduced: the transverse growth that motivated B.** With every momentum-path term I could copy, the model
  damps a front perturbation that grows ×300 in 80 steps in the solver. So the B failure needs an ingredient that is
  not in the model (candidates: MULES limiter, correctUBc, the boundary HbyA/U treatment, the iterative p solve; the
  10-07 tight-tolerance runs make the last one unlikely). **Its mechanism is still unknown.**
- A growth seen with a 1e-10 seed everywhere (`mom+V`, `steady+V`) sat at the front but saturated near 1e-6 and
  disappeared with the seed confined to the ramp; a 1e-5 seed everywhere blew up at the outlet (row 171, dry cells:
  δα 1e-5 at α 0.002 is δpc ≈ 12 kPa; the model's outlet is simplified). Neither is the solver's mode.
- What the model does show about the momentum path (with A): the total flux lags the capillary forcing and the 1D
  profile becomes non-monotone within ~2 µs at any dt; without convection it collapses at ~3.6e-5 s physical time;
  removing inertia with convection kept collapses in a few steps (as in the solver). Time scale: in partly saturated
  cells the mixture momentum combines the water density with the (larger) air mobility: ρ_mix·M_mix/ε ≈ 1e-4 s at
  α 0.3 (estimate), longer than the run. With the Darcy-limit flux (as B) none of this appears.

**Is B the only way to stabilise?** Not established either way. Evidence for B: the 10-07 solver runs (ddtCorr,
inertia, tolerance, dt: none helped, B did) and the model (Darcy-limit flux: monotone and stable; momentum path:
non-monotone profile, collapse without convection). Alternatives were not tested in the solver. To test next, in the
real solver (installed `b525086` with `darcyFaceMaxDa` removed = A + C + E–I without B, on this bench): MULES settings
(`MULESCorr yes`, `nLimiterIter`), and dropping the viscous/convective terms in porous cells; in the model: a MULES limiter.
