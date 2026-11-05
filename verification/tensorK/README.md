# tensorK — checks of the diagonal tensor permeability (solver change T)

**Why.** The yarns are anisotropic: water moves more easily along the fibres (Kpar) than across them (Kperp). Change T
lets `0/K` be a `volTensorField`, diagonal in the mesh axes, aligned with each yarn (`build_fields.py --k-mode tensor`).
The design, the decisions and the six checks are in `../../NOTES_solver.md` ("Planned: diagonal tensor K"); the REV
studies that need it in `../../NOTES_cases.md` (REV case status, "Tensor K, planned").

**What change T does** (the user wrote it, steps 0–7, 2026-11-02 to 11-05):
- solver (`solver/T_steps0-5.patch`, on of9-port `97f3b35` = code of `8a97d02`): K read as scalar or tensor;
  with a tensor, k0f = n·K·n on each face (n = the mesh axis of the face), harmonic mean where the two cells differ
  (`tensorKFaces.H`); G's porous/free block leaves k0f to it; fatal errors if K is not diagonal, a face is not
  along an axis or a porous face is not a Darcy face; the cell phase velocities `Uwetting`/`UnonWetting` =
  Solid·(kr/μ)·(K·F): output only, except on a patch where `Uwetting` is fixed, where `correctUBc.H` sets the
  flux to (`Uwetting`_b + `UnonWetting`_b)·Sf with the computed air velocity of the boundary cell (1D cases: the
  outlet; check 3). k0 = K_xx where K cancels (M1/M, L/M).
- `../../meshing_strat_trial/tools/coatsTimeStep` (`solver/coatsTimeStep_T6.patch`): gravity part of the Coats
  number with ĝ·K·ĝ of the cell; the capillary part already sums the solver's k0f.
- `../../meshing_strat_trial/REV/build_fields.py` (`solver/build_fields_T7.patch`): `--k-par`/`--k-perp` instead of
  Gebart (checked on scratch REV builds, `../../NOTES_solver.md`).

**Solver version of this study (one version, PLAN.md rule):** `hybridPorousInterFoam_T` built 2026-11-05 from the
working tree = `97f3b35` + `solver/T_steps0-5.patch` (sha1 of the patch `34904eb4…`; `Make/files` names the binary
`_T`; md5 `ceb6faf0…`, built 10:12); reference `hybridPorousInterFoam` installed = `8a97d02` (md5 `5e2349b8…`). `coatsTimeStep` = `HEAD` + `solver/coatsTimeStep_T6.patch`
(file sha1 `5b81431e…`).

## Files
- `makeCases.sh`: builds the run folders (not tracked) from their sources, each with a `run` script naming its
  binary; logs through `runTmpLog` (in /tmp during the run, moved into the folder at the end).
- `runAll.sh`: runs them side by side, then the comparisons; `./runAll.sh --compare` for the comparisons only.
- `compare.py`: two runs, every file of every common write byte by byte (largest difference printed when one
  differs) and the "Coats CFL Number"/"deltaT =" line of every step (17 digits).
- `toTensorK.py`: scalar `0/K` → `volTensorField` K·I, same text on the diagonal.
- `tools` → `../../meshing_strat_trial/tools` (function objects and `pOpenAir` of the bench).

## Checks 1 and 2: runs and predictions (written 2026-11-05, before the runs)

| Run | Case | Binary | Compared with | Prediction |
|---|---|---|---|---|
| `C1_1D_T` | inputs of `../wicking1D/ABC` (1D column, no free cells, its own Coats copy), 0.03 s, writes every 1 ms, 6 digits | `_T` | the stored `../wicking1D/ABC` (b995db5) | every file of the 30 writes identical (as change J's `1D_regression`) |
| `C1_bench_inst`, `C1_bench_T` | `2D_bench` (G + H + F′ + I, θ 60°, g along −x), 2 ms, writes every 0.5 ms, 17 digits, serial | installed / `_T` | each other | Coats and deltaT lines of every step and all files of the 4 writes identical |
| `C2_bench_tensor` | `C1_bench_T` with `0/K` → K·I | `_T` | `C1_bench_T` | α, p, U, φ, `alphaPhi0` and the Coats/deltaT lines identical; `K` differs (tensor file); `Uwetting`, `UnonWetting`, `Ur` equal or different in the last digits only (product order (kr/μ)·(K·F) against (K·kr/μ)·F; output only); the log shows the tensor line ("Tensor K: normal component on the faces …"), no guard stops the run |
| `C2_S1_scalar`, `C2_S1_tensor` | cut REV of study 2d (S1: K 1e-12, VG 5000/0.5, θ 40°, L; 91 × 35 × 20 cells, x cyclic, g along −y), 0.5 ms, writes every 0.25 ms, 17 digits, 4 cores | `_T` | each other | as `C2_bench_tensor` (adds processor and cyclic patches, porous/free faces in 3D) |

Reading: check 1 failing = change T moved the scalar path (find out before anything else). Check 2 failing on α,
p, U, φ or dt = the tensor path does not reduce to the scalar one for K0·I: `tensorKFaces.H` (k0f), the skipped G
block or `coatsTimeStep` (Kg) is the place to look; differences in `Uwetting`/`UnonWetting`/`Ur` alone are expected.

## Check 3: 1D column along x, y and z (decided with the user 2026-11-05; predictions written before the runs)

Does each face take the K component of its own direction, and the Coats gravity term the component along g? And does
the front scale as √K? Base: the 1D column of `../wicking1D/ABC` (172 cells of 20 µm along y, one cell across,
empty sides, no free cells; = `_T` in check 1). For every C3 run: its own coded Coats function object (reads K as a
scalar) replaced by `tools/coatsTimeStep` (for an all-porous column the same faces, k0f and limits: no free cells,
so no capillary-wave limit); K along the column Ka = 2.5e-12 (time scale factor exactly 4 against ABC's 1e-11), across
Kt = 1e-11; 0.12 s, writes every 4 ms (30), 17 digits, serial, `_T`. The x and z columns are the y mesh after
`blockMesh` and `setFields`, rotated by `transformPoints "rotate=((0 1 0) (1 0 0))"` (or `(0 0 1)`): an exact
rotation (matrix of 0 and ±1), same cell and face order; g rotated with it. The inlet p BC (coded) uses α and pc
only, not positions.

| Run | Column | `0/K` | g |
|---|---|---|---|
| `C3_y_scalar` | y | scalar 2.5e-12 | (0 −9.81 0) |
| `C3_y_tensor` | y | diag(1e-11, 2.5e-12, 1e-11) | (0 −9.81 0) |
| `C3_x_tensor` | x | diag(2.5e-12, 1e-11, 1e-11) | (−9.81 0 0) |
| `C3_z_tensor` | z | diag(1e-11, 1e-11, 2.5e-12) | (0 0 −9.81) |

Predictions:
1. `C3_y_tensor` = `C3_y_scalar`: α, p, φ, `alphaPhi0` and the Coats/deltaT line of every step identical; phase
   velocities equal to rounding (as check 2). k0 = K_xx = 1e-11 ≠ Ka there, but in this column every face is a Darcy
   face and k0 only enters where K cancels: bit-identical expected, at worst round-off differences.
2. `C3_x_tensor` and `C3_z_tensor` = `C3_y_tensor`: α, p, φ, `alphaPhi0` and the Coats/deltaT lines identical
   (bit-identical expected: the rotation is exact and every face of the column is along one axis); the vectors (U,
   phase velocities) and K hold the same numbers in other components. Failing: `axisNormal` or ĝ·K·ĝ takes the wrong
   component in that direction.
3. √K scaling: at fixed pc0 every term of the problem (capillary, gravity, air flow) and every dt limit (Coats, dSmax)
   scales with K, only the first steps do not (fixed start dt). `C3_y_scalar` at 4t against ABC at t (30 writes,
   `compareScaling.py`): front (α = 0.1, linear between cells) within one cell (20 µm), mean α within 0.5 %, i.e. a
   front of 18.04·√0.25 ≈ 9.0 mm/√s (about −1.6 % as ABC against the similarity solution).
Not covered: across the column there are no faces (1D), so the transverse components cannot act here (checks 4–6).

## Check 5: two layers in series (decided with the user 2026-11-05; predictions written before the runs)

Does the face between two different K carry the exact series resistance (harmonic mean), with gravity in the flux?
Base: the 1D column of `../wicking1D/ABC` (172 cells, Δx = 3.446 mm/172 = 20.035 µm, along y, cross-section 0.55 ×
0.237 mm), made a saturated pressure-driven column: α = 1 everywhere and on the inflow (Se clipped to 0.9999: kr_w
= 0.9999³, kr_a = 1e-12), `activateCapillarity 0`, p fixed 1000 Pa at the inlet (y = 0) and 0 at the outlet (y = L),
`Uwetting` zeroGradient on the outlet (fixed (0 0 0) in ABC would close the outlet to water through `correctUBc.H`),
gravity (0 −9.81 0) kept, p solver tolerance 1e-12 (ABC 1e-6), tools/coatsTimeStep, 1 ms (~60 steps, dt growing from
1e-8 s), one write, 17 digits, `_T`. K along y: 1e-11 in cells 0–85 (y < 1.723 mm), 2.5e-12 in cells 86–171; one face
on the jump.

Exact steady flux (Darcy, two phases, uniform α): φ = A·λ_t·(Δp − ρ_eff·g·L)/R with R = Σ_cells Δx/K = L1/K1 + L2/K2
= 8.615e8 m⁻¹, λ_t = kr_w/μ_w + kr_a/μ_a, ρ_eff = (ρ_w kr_w/μ_w + ρ_a kr_a/μ_a)/λ_t: φ = 1.4615e-10 m³/s. The two-point
flux with harmonic face K is exact (each face = its two half cells in series, boundary faces one half cell); with the
linear face K at the jump, (K1 + K2)/2, the jump face loses Δx/2·(1/K1 + 1/K2) − Δx/((K1 + K2)/2) = 1.80e6 m⁻¹ of
resistance: flux +0.210 %.

| Run | `0/K` | Prediction |
|---|---|---|
| `C5_tensor` | diag(1e-11, K_y, 1e-11), K_y per layer | φ uniform along the column (spread ≤ 1e-8 relative) and = the exact series value within 1e-8; p at the cell centres = the exact piecewise-linear profile within 1e-5 Pa; α stays 1 |
| `C5_scalar` | scalar K_y per layer (the scalar path interpolates linearly between porous cells) | φ = the linear-face value, +0.210 % against the exact one, within 1e-8; p = the discrete profile with that face |

`compareSeries.py` computes both references from the inputs and compares. Failing `C5_tensor`: the harmonic face of
`tensorKFaces.H` (or its use in Mf, Lf) is not the series resistance.

## Check 6: 2D bench with anisotropic walls, serial and parallel (decided with the user 2026-11-05; predictions written before the runs)

Does a yarn-like anisotropy act where it should (the exchange across the yarn surface), and does the tensor path give
the same result when the porous/free faces lie on a processor boundary? Base: `../../meshing_strat_trial/2D_bench`
(slit along x, g along −x; walls z-cells 0–7 and 16–23, gap 8–15, 20 µm; G + H + F′ + I, θ 60°; 2 ms), writes every
0.05 ms as the bench (its `check.py` needs them), 17 digits, `_T`. Walls: scalar 1e-11 (as the bench) or the tensor
diag(Kpar 1e-11 along the slit, 2.2e-12, Kperp 2.2e-12 across) = REV study (a); free cells 1·I. Parallel runs: 2
processors, `method manual`, processor boundary between z-cells 7 and 8, i.e. on the lower wall surface (100
porous/free faces, as `../parallel_H` `par`), `makeDecomposition.py` of `../parallel_H`.

| Run | Walls | Processors |
|---|---|---|
| `C6_scalar_serial` | scalar 1e-11 | 1 |
| `C6_scalar_split` | scalar 1e-11 | 2, boundary on the lower wall surface |
| `C6_aniso_serial` | diag(1e-11, 2.2e-12, 2.2e-12) | 1 |
| `C6_aniso_split` | same | 2, same boundary |

References (bench, `../../NOTES_cases.md`): scalar walls gap meniscus 0.43 / 0.79 mm at 1 / 2 ms, wall front 0.75 /
1.15 mm; impermeable walls (Bosanquet) 0.63 / 1.16 mm; walls alone (1D) 0.60 / 0.83 mm.

Predictions:
1. `C6_scalar_serial`: the bench numbers above; `check.py` 10 of 10.
2. `C6_aniso_serial`: the gap–wall faces carry 2·Kperp/(1 + Kperp) ≈ 2·Kperp instead of 2·1e-11 (×0.22) and the
   imbibition across the wall thickness is 4.5× slower, while the walls conduct along the slit as before. So the walls
   take less water from the gap: meniscus at 2 ms between the scalar walls and the impermeable ones, 0.79 < h < 1.16
   mm; the walls are fed less sideways: wall-averaged front at 2 ms between the walls alone and the scalar walls,
   0.83 < x_f < 1.15 mm (less sure than the meniscus: a higher meniscus feeds the walls higher up). `check.py`: 9 of
   10 pass; "wall front uniform across the wall" (≤ 2 cells) may fail by design, since it assumes the sideways
   imbibition is faster than the front (not a solver error; reported, not a pass criterion). Budget closed, max
   |U| < 2 m/s, no stray water.
3. Parallel: `C6_aniso_split` against `C6_aniso_serial` differs as little as the scalar control `C6_scalar_split`
   against `C6_scalar_serial` (ordinary parallel difference, `../parallel_H`: max |Δα| 9e-4): max |Δα| over the writes
   ≤ 3× the control, meniscus and wall fronts within 1 µm, lower/upper mirror asymmetry ≤ 3× the control. Failing:
   the coupled branch of `tensorKFaces.H` (processor faces where the two sides differ) or the guards/sums on
   processor patches.
`compare6.py` measures 3 (and the numbers of 1–2); `check.py` runs in each folder.

**Added after the first results (2026-11-05), before running them:** `C6_scalar_mid`, `C6_aniso_mid` = the split runs
with the processor boundary in the middle of the gap (between z-cells 11 and 12: free/free faces only, as
`../parallel_H` `parmid`). Question: does the larger serial/parallel difference of `C6_aniso_split` (max |Δα| 6.1e-3,
a transient at 0.65 ms in the first three columns next to the inlet, in both walls) come from the processor faces on
the wall surface? Prediction: no; `C6_aniso_mid` shows a transient of the same order (1e-3 to 1e-2) at the inlet
columns around 0.6–0.7 ms and differs elsewhere by ≤ ~2e-3, i.e. ordinary parallel round-off, amplified at the inlet
wall cells (yarn inlet faces near equilibrium with the bath, `../../NOTES_solver.md` open issues). If instead the mid
split stays at the control level (≤ 1.1e-3, no inlet transient), the wall-surface processor faces of the tensor path
are the cause.

## Check 4: 2D anisotropic spreading (decided with the user 2026-11-05; predictions written before the runs)

Case: 2D box 40 × 80 cells of 20 µm (0.8 × 1.6 mm, one cell thick, empty), all porous, the yarn inputs of the 1D
twins (ε 0.5, Brooks–Corey n 3, VG 5000 Pa / 0.5, μ 1e-3 / 1.76e-5), **no gravity**, K = diag(Kxx 2.5e-12, Kyy 1e-11).
Water enters through the bottom edge at x < 0.1 mm (`inlet`, 5 faces, at the left corner); air leaves through the top
edge (`outlet`); the left edge (a symmetry line: half of a 0.2 mm source), the right edge and the rest of the bottom
are closed (`walls`). Initial: 0.002, with the 1D ramp drawn around the inlet segment: α = max(0.002, 0.99 − 4.94·r
[mm]), r = distance of the cell centre to the segment (the 1D ramp at r = y). 10 ms, writes every 0.5 ms, 17 digits.
Boundaries as the 1D twins (the REV's own bath and outlet questions stay open, `../../NOTES_cases.md`): hybrid as
`../wicking1D/ABC` (inlet: coded p, α inletOutlet 0.99; outlet: coded p, `Uwetting` fixed 0, water cannot leave),
walls U noSlip, p fixedFluxPressure, the rest zeroGradient, its Coats copy replaced by `tools/coatsTimeStep`;
anisoImpesFoam as `../../trialWicking/1D_vertical_impes_inletRes` (inlet Sb 0.99, p 0, air velocity 0; outlet p 0,
water velocity 0), CFL Coats, maxCo 0.5, dSmax 0.01. Its walls were first set as in its tutorials (Ua = Ub = 0, p
`darcyGradPressureAniso`); three start-up failures, fixed before any result: (i) `fvSchemes` interpolates K `harmonic`,
which OpenFOAM defines for scalars only → `linear` (K is uniform: same faces); (iii) `interpolationSchemes` has
`default none` in the 1D template, while the tensor Laplacian interpolates grad(p) for its cross term (zero here) →
`default linear`, as the anisoImpesFoam tutorials; (ii) `darcyGradPressureAniso` looks `g`
up in the Time registry (`db().time().lookupObject`, `darcyGradPressureAniso.C:127`) while anisoImpesFoam registers it
on the mesh (`anisoImpesFoam.C:65`): fatal on OpenFOAM 9 at the first pressure solve (a porousMultiphaseFoam OF9-port
issue; its tutorials would stop the same way). The walls are therefore `symmetry` patches in this run: with g = 0
they carry no flux in its formulation (zero normal gradient of p and Sb, diagonal K, so pressure, gravity and capillary
boundary fluxes all vanish). The hybrid keeps its walls (zero flux too).

| Run | Solver | Mesh | K |
|---|---|---|---|
| `C4_tensor` | `_T` | 20 × 20 µm cells (box 0.8 × 1.6 mm, inlet x < 0.1 mm) | diag(2.5e-12, 1e-11, 1e-11) |
| `C4_stretched` | `_T` | stretched ×2 along x: 40 × 20 µm cells (box 1.6 × 1.6 mm, inlet x < 0.2 mm), same cell order and initial values per cell | scalar 1e-11 |
| `C4_aniso_impes` | anisoImpesFoam | as `C4_tensor` | diag(2.5e-12, 1e-11, 1e-11) in `constant/K` |

Predictions:
1. (a) `C4_stretched` = `C4_tensor` cell by cell: a diagonal K on (Δx, Δy) is the isotropic K on (Δx·√(K/Kxx), Δy):
   transmissibility per volume Kxx/Δx² = K/Δx'², the Darcy-face test, the Coats terms (capillary sum, flux sum; no
   gravity) and dSmax are all per unit volume; the coded inlet/outlet BCs use α and pc only, the outlet's fixed
   `Uwetting` closes it to water in both. α equal to 1e-8 at all 20 writes, same number of steps, dt equal to 1e-8
   relative; not bit-identical (the geometry numbers differ). Failing: one of the per-direction pieces of the tensor
   path (`axisNormal`, k0f, ĝ·K·ĝ is 0 here) differs from the scalar path in 2D.
2. (b) `C4_aniso_impes` against `C4_tensor`: fronts (α or Sb = 0.1, linear between cells) along the left edge (y_f)
   and along the bottom edge (x_f) within 3 % from 2 ms on (1D twins: ~2 % apart, air back-pressure and the 1 % air of
   the hybrid inlet); aspect ratio y_f/x_f within 2 % of the hybrid's, rising towards √(Kyy/Kxx) = 2, between 1.75
   and 2.0 at 10 ms in both (the 0.2 mm source keeps it below 2: at most 1 + 0.2 mm/y_f elongation in the stretched
   frame).
`compare4.py` measures both.

**Results (2026-11-05): (a) passes; (b) holds within its tolerances up to 9 ms, its 10 ms aspect criterion could not
be evaluated (my box was too narrow).**
- (a) `C4_stretched` = `C4_tensor`: max |Δα| 1.5e-11 over the 20 writes, 52,396 steps in both, every deltaT identical
  (relative difference 0). A diagonal K is handled exactly as the isotropic K on the stretched mesh, with both face
  directions carrying different K in the same run.
- (b) anisoImpesFoam (40,686 steps) against the hybrid tensor run:

| t [ms] | y_f hybrid / aniso [mm] | diff | x_f hybrid / aniso [mm] | diff | aspect hybrid / aniso | diff | mean saturation hybrid / aniso |
|---|---|---|---|---|---|---|---|
| 1 | 0.586 / 0.600 | +2.3 % | 0.368 / 0.369 | +0.2 % | 1.593 / 1.626 | +2.1 % | 0.058 / 0.063 |
| 2 | 0.761 / 0.779 | +2.3 % | 0.442 / 0.444 | +0.5 % | 1.721 / 1.753 | +1.8 % | 0.087 / 0.095 |
| 4 | 0.998 / 1.020 | +2.2 % | 0.552 / 0.556 | +0.7 % | 1.808 / 1.835 | +1.5 % | 0.139 / 0.149 |
| 6 | 1.175 / 1.199 | +2.0 % | 0.638 / 0.642 | +0.6 % | 1.843 / 1.869 | +1.4 % | 0.186 / 0.198 |
| 8 | 1.322 / 1.347 | +1.9 % | 0.710 / 0.715 | +0.6 % | 1.861 / 1.885 | +1.3 % | 0.230 / 0.244 |
| 9 | 1.387 / 1.414 | +1.9 % | 0.756 / 0.760 | +0.5 % | 1.835 / 1.860 | +1.3 % | 0.251 / 0.266 |
| 10 | 1.447 / 1.483 | +2.5 % | out of the box | | | | 0.272 / 0.287 |

  From 2 ms the fronts agree within 2.5 % (y) and 0.7 % (x), the aspect within 1.8 %: inside the predicted 3 % / 2 %.
  anisoImpesFoam is ahead along y and holds 5–9 % more water, as the 1D twins (front +1.8 %, mean saturation +4–5 %:
  the hybrid's 1 % air at the inlet and the air back-pressure). The aspect rises 1.59 → 1.86 to 8 ms in both codes
  (inside the predicted 1.75–2.0, towards 2; in the stretched frame the front is 7.5 % longer along the source than
  across, under the 15 % bound of the 0.2 mm source), then drops as the x front feels the closed right wall (x_f 0.756
  mm at 9 ms) and leaves the box at ~9.2 ms: from 9.5 ms the whole bottom row is above 0.1 in both codes, x_f and the
  aspect are undefined and `compare4.py` reports FAIL. The prediction "aspect at 10 ms in [1.75, 2.0]" fails as
  written for that reason: the estimate of x_f was ~0.5 mm at 8 ms, the runs gave 0.71 mm; a box of ≥ 1.2 mm along x
  would have kept the front inside.

## Results

**Checks 1 and 2 (2026-11-05, laptop, `./runAll.sh`, all six runs side by side, ~10 min): all predictions hold.**

| Comparison | Writes | Files | Time steps (Coats + deltaT lines) | Verdict |
|---|---|---|---|---|
| `C1_1D_T` vs stored `../wicking1D/ABC` | 30 (1–30 ms) | 360 identical | identical at the 500 steps of the stored log (filtered with `LOG_EVERY`; the new run has 48,921 steps) | pass |
| `C1_bench_inst` vs `C1_bench_T` | 4 (0.5–2 ms) | 48 identical | identical at all 8,447 steps | pass |
| `C1_bench_T` vs `C2_bench_tensor` | 4 | α, p, U, φ, `alphaPhi0`, eps, Solid, `uniform/time`: 32 identical; `K` scalar vs tensor; `Uwetting`, `UnonWetting` relative ≤ 4.4e-16, `Ur` ≤ 4.8e-14 (absolute ≤ 2.8e-14 m/s) | identical at all 8,447 steps | pass |
| `C2_S1_scalar` vs `C2_S1_tensor` (4 cores, x cyclic) | 2 (0.25, 0.5 ms) | 16 identical (same list); `Uwetting`, `UnonWetting` ≤ 4.4e-16, `Ur` ≤ 2.5e-13 (absolute ≤ 1.4e-14 m/s) | identical at all 435 steps | pass |

- Check 1: change T does not move the scalar path, over 0.03 s of 1D wicking (no free cells) and 2 ms of the bench.
- Check 2: a tensor K0·I reduces exactly to the scalar K0, in serial and on 4 cores with cyclic and processor
  patches, porous/free faces in 2D and 3D, gravity along x (bench) and y (cut REV): k0f from `tensorKFaces.H` (the
  harmonic on the porous/free faces included), G's block skipped and the tensor branch of `coatsTimeStep` (ĝ·K·ĝ)
  give the same numbers as the scalar code. The guards ran and passed (cut REV: "Tensor K: normal component on the
  faces …" after the Darcy face count; same Darcy face counts as scalar, 67,731 internal and 2,633 boundary faces in
  serial). The phase velocities differ only by rounding (product order), `Ur` a little more because it subtracts two
  nearly equal terms; they are output only.
- Not covered by checks 1–2: any K that is not a multiple of I, i.e. the anisotropic physics (checks 3–6).
- `compare.py` first compared the log line by line and failed against the filtered stored log; it now matches the
  steps by their `Time =` line.

**Check 3 (2026-11-05, four runs side by side, ~3 min each, 48,929 steps each): predictions 2 and 3 hold; prediction 1
holds to round-off only, cause found.**

| Comparison | Result | Verdict |
|---|---|---|
| `C3_y_scalar` vs `C3_y_tensor` (prediction 1) | not bit-identical. First difference: the outlet boundary value of φ at 20 ms, in the last digit (…273e-09 / …271e-09), internal field identical; then φ at 13 of 30 writes, α, p, U from 92 ms; largest relative differences at 120 ms: α 2.6e-13, p 1.1e-13, φ 9.8e-12; Coats line different in the 17th digit at 12,250 of 48,929 steps from 89.4 ms (deltaT identical at the first one) | fails as written (bit-identity), holds within its "at worst round-off" clause |
| `C3_x_tensor`, `C3_z_tensor` vs `C3_y_tensor` (prediction 2) | 210 files identical at the 30 writes (α, p, φ, `alphaPhi0`, eps, Solid, `uniform/time`); Coats and deltaT identical at all 48,929 steps; U, `Uwetting`, `UnonWetting`, `Ur` bit-identical to the y column's vectors rotated (checked at 4, 60, 120 ms) | pass |
| `C3_y_scalar` at 4t vs `../wicking1D/ABC` at t (prediction 3, `compareScaling.py`) | front within 0.002 µm at all 30 writes, mean α within 3.6e-6 (relative), largest cell difference 3.9e-6; front fit for t ≥ 2 ms (front = k√t + c): 8.850 against 17.700 mm/√s, ratio 0.5000 | pass |

- **Why prediction 1 is not bit-identical:** the 1D case fixes `Uwetting` on the outlet (no water out). There
  `correctUBc.H` sets the outlet flux to (`Uwetting`_b + `UnonWetting`_b)·Sf, and `UnonWetting`_b (zeroGradient) is the
  computed air velocity of the last cell: (kr/μ)·(K·F) in the tensor branch of step 5, (K·kr/μ)·F in the scalar one,
  equal in exact arithmetic but rounded differently. The prediction assumed every flux of the column comes from k0f
  and missed this patch. Checks 2 have no fixed phase velocity, hence their bit identity.
- Prediction 2 shows that `axisNormal` takes the right component for faces along x, y and z, and that the Coats
  gravity term takes ĝ·K·ĝ along each axis.
- Prediction 3: the column with K/4 at 4t reproduces K at t to 1e-6, so the tensor path keeps the exact √K scaling
  of the front at fixed pc0. The fit form above gives 17.70 mm/√s for ABC (the 18.03 of `../../NOTES_cases.md` comes
  from another fit); 8.85 is −1.9 % from 18.04·0.5, the same relative deviation as ABC in this form, not the "about
  −1.6 %" written in the prediction (that number came from the other fit).

**Check 5 (2026-11-05, 56 steps each, dt 1e-8 → 8.5e-5 s, compared at 1 ms): both predictions hold.**

| Run | Flux against its expected reference | Spread along the column | Cell-centre p against its profile | Against the other reference | α |
|---|---|---|---|---|---|
| `C5_tensor` (harmonic expected) | 1.461470749835e-10 m³/s, −7.9e-12 relative | 5.8e-11 | ≤ 4.1e-9 Pa | flux −0.209 %, p up to 1.6 Pa off | 1 ± 1e-12 |
| `C5_scalar` (linear expected) | 1.464536057862e-10 m³/s, −8.7e-12 relative | 6.3e-11 | ≤ 4.5e-9 Pa | flux +0.210 %, p up to 1.6 Pa off | 1 ± 1.1e-12 |

- The tensor path carries the exact series resistance across the jump, with the gravity term (Lf uses the same face
  K): flux and pressure equal the analytical solution to the solver tolerance.
- The scalar path interpolates K linearly between two porous cells and is off by one face's worth: +0.21 % in flux
  for one jump of ratio 4 in 172 cells (the error grows with the contrast and with the number of jump faces). It
  is left as it is (the scalar path stays bit-identical to `8a97d02`); in the scalar REV runs K is uniform inside
  the yarns, so no porous/porous face has a jump there (porous/free faces have had the harmonic since G).

**Check 6 (2026-11-05, six runs, 2 ms each): the anisotropy acts at the wall surface as expected and the tensor path
in parallel reproduces every measured quantity of the serial run; two predictions failed as written (2b, 3 max |Δα|),
and so did the prediction of the added diagnostic.**

| Run | `check.py` | Gap meniscus 1 / 2 ms (gap-averaged) | Wall front 2 ms surface / back / mean | Wall water 2 ms | max \|U\| |
|---|---|---|---|---|---|
| `C6_scalar_serial` | 10 / 10 | 0.430 / 0.790 mm | 1.150 / 1.150 / 1.150 mm | 369.0 cell vol. | 1.20 m/s |
| `C6_aniso_serial` | 9 / 10 (uniform front: 60 µm > 40 µm) | 0.510 / 0.930 mm | 1.190 / 1.150 / 1.170 mm | 365.7 cell vol. | 1.25 m/s |
| `C6_scalar_split` | 9 / 10 (budget 4.7e-6, see below) | as serial | as serial | as serial | 1.20 m/s |
| `C6_aniso_split` | 8 / 10 (budget 9.7e-7; uniform front) | as serial | as serial | as serial | 1.25 m/s |

- Prediction 1 (scalar serial = bench numbers, 10 / 10): holds.
- Prediction 2 (tensor walls, serial): the meniscus rises higher, 0.930 mm at 2 ms, inside the predicted (0.79, 1.16):
  the walls draw less water from the gap (the gap–wall faces carry ×0.22). The wall-averaged front, 1.170 mm, is NOT
  inside the predicted (0.83, 1.15): the surface rows lead (1.190 mm) because the higher meniscus wets the wall surface
  higher up and the walls still conduct along the slit at Kpar; the back rows stay at the scalar value (1.150 mm). The
  front is no longer uniform across the wall (60 µm, `check.py`'s ≤ 40 µm fails, anticipated). Budget 4.9e-15, no
  stray water, max |U| 1.25 m/s.
- Prediction 3 (split on the lower wall surface): meniscus and wall fronts within 0.021 µm of serial, lower/upper
  mirror asymmetry 2.0× the control (≤ 3): hold. max |Δα| 6.1e-3 = 5.5× the control (1.1e-3): fails as written.
  Away from the three inlet columns the tensor pair differs by 2.0e-3 (control 9.8e-4).
- Diagnostic (mid-gap splits, prediction above): fails as written. The large difference is a transient at the inlet
  columns, from 2e-5 to 6e-3 between 0.60 and 0.65 ms, decaying to 1e-4 by 0.9 ms. It appears only when the processor
  boundary lies on the wall surface (meeting the inlet at the corner): the scalar control has the same jump, 1e-3 at
  0.60 ms; both mid-gap splits stay ≤ 3e-4 at the inlet, and differ elsewhere by 2.1e-3 (tensor) and 2.5e-3 (scalar),
  ordinary parallel differences of this flow. The wall-surface splits also lose water once at the start (imbalance from
  the first write, constant after: scalar −2.6e-17 m³ ≈ 3e-3 cell volumes, as `../parallel_H`; tensor −5.7e-18 m³);
  the mid-gap splits do not (3e-27 m³). Reading: a pre-existing local inconsistency where a processor boundary on a
  porous/free surface meets the inlet (scalar path too), whose effect on the inlet wall cells the anisotropic walls
  amplify (×5); not an error of the tensor faces (check 2 has them bit-identical to scalar on processor faces). Cause
  of that corner inconsistency not looked for (open issue in `../../NOTES_solver.md`).
