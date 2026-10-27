# standardOpenBC — standard OpenFOAM BCs on the open patches instead of `tools/pOpenAir` (2026-10-27)

**Why.** The open patches of the REV (reservoir `inlet`, `top`/`bottom` open to air) use the coded p BC
`tools/pOpenAir` (VG pc recomputed in the BC, switches `openPorousAirZero` and `openFreeTotalPressure`, hydrostatic
reservoir pressure from `reservoirWaterPressure`/`reservoirReferencePoint`), and `Uwetting`/`UnonWetting` have
patch-by-patch BCs with long comments. The physics is simple: a fabric open to air, fed by a bath at rest, everything
outside at atmospheric pressure (0 Pa), flow driven by capillarity only (gravity opposes it). Question: do the
standard OpenFOAM BCs give the same result?

**What `pOpenAir` does in the REV** (code read 2026-10-27, solver `be1a3ab`):
- `top`/`bottom`: all 2 × 12,103 faces are free (padding cells, eps 1; their α inletValue is 0 on every face, a yarn
  face would carry S_dry 0.002), so only the free-face branch runs: p = 0 on outflow, −½ρ|U|² on inflow
  (`openFreeTotalPressure 1`). OpenFOAM's `totalPressure` with p0 0 gives p0 − ρ·½(1 − pos0(φ))|U|²
  (`dynamicPressureFvPatchScalarField`, p in Pa): the same numbers (the factor ½ is exact in floating point).
- `inlet`, 290 gap faces: water at ρ_w g·(Cf − reservoirReferencePoint) + reservoirWaterPressure = 0 exactly (inlet
  plane y = 0, reference point (0 0 0), g along −y), total pressure on inflow: same as `totalPressure`.
- `inlet`, 984 yarn faces: p = (1 − α_b)·pc(α_b), i.e. water at 0 Pa in the mixture pressure p = p_air − α·pc:
  6.76 Pa on inflow (α_b = 0.99, pc 676 Pa), (1 − α_c)·pc(α_c) on outflow. `totalPressure` gives −½ρ|U|² / 0, i.e.
  water at −6.8 Pa − ½ρ|U|² instead of 0. With α_b = 1 on these faces the static part is exact ((1 − α_b)·pc = 0);
  what is left is −½ρ|U|² on inflow (Darcy velocity of the yarn inlet faces ~0.01–0.1 m/s from job 3051's uptake:
  ≤ 5 Pa, vs capillary pressures of 1–50 kPa in the yarns).
- Not used in the REV: `openPorousAirZero` (porous faces of a non-reservoir open patch: none), the hydrostatic term
  (zero), `reservoirWaterPressure`, `reservoirReferencePoint` (read by `pOpenAir` only; the solver reads
  `waterOnlyPatches` only: `grep` of the solver sources).

**Phase velocities.** `Uwetting`/`UnonWetting` are recomputed from p and α every step (`updateDarcyVelocities.H`).
Their BCs enter only (1) `correctUBc.H`: on a patch where U is not fixedValue and Uwetting is fixedValue, the face
flux is replaced by (Uwetting + UnonWetting)·Sf (on an open patch this closes the free faces); (2) `alphaEqn.H:150`:
the boundary relative flux from their values if fixedValue (0 on the walls, the same as without). On the walls U is
`noSlip` (a fixedValue), so (1) never acts; zeroGradient on every patch gives the same solution. `Ur` is only written.

**Proposed set** (the usual interFoam "atmosphere" set): p `totalPressure` p0 0 on `inlet`, `top`, `bottom`
(`fixedFluxPressure` on the walls, unchanged); U unchanged (`pressureInletOutletVelocity` / `noSlip`); `Uwetting`,
`UnonWetting` zeroGradient on every patch; α inlet `inletOutlet` with inletValue uniform 1 (bath-saturated yarn faces
instead of 0.99; kr and pc clip Se to ≤ 1 − 1e-4, so α_b = 1 gives pc 70.7 Pa and kr_w 0.9997, as α_b = Smax 0.999
would); `transportProperties` without the four `pOpenAir` keywords. J (`waterOnlyPatches`) stays: it is the solver
part of the reservoir, not a BC.

**Expected differences, yarn inlet faces only:** water pressure 0 → −½ρ|U|² on inflow; face kr_w 0.973 → 0.9997;
pc_b 676 → 70.7 Pa. In the solver's boundary flux (mixture-pressure form, `alphaEqn.H` phiWetting) the water flux of
a boundary face is −M1f·δ·|Sf|·[Δp_w + (α_b − α_c)(pc_b − pc_c)] + gravity, with Δp_w = p_w,b − p_w,c: the exact
two-point water flux plus a product term, which changes with α_b. Inflow faces: with α_b = 1 the upwind α flux equals
J's α flux (no boundary correction left for MULES).

## Runs and predictions (written before the runs)
Solver: installed `hybridPorousInterFoam` (of9-port `be1a3ab`), laptop. Bench and 1D serial (folders here, built by
`makeCases.sh`); REV on 4 cores in a scratch copy (results below, not kept).

| Run | From | Change | Prediction |
|---|---|---|---|
| `bench_ref` | `../waterOnlyReservoir/bench_waterOnly` | none | bit-identical to the stored run (all fields, all writes; waterBudget.csv) |
| `bench_A` | `bench_ref` | `outlet` p (free faces only) → `totalPressure`; `Uwetting`/`UnonWetting` zeroGradient everywhere | bit-identical to `bench_ref` (α, p values, U, φ, alphaPhi0; `Uwetting`, `UnonWetting`, `Ur` differ only in their written wall boundary values) |
| `bench_B` | `bench_A` | `inlet` p → `totalPressure`, α inlet uniform 1, no `pOpenAir` keywords | gap meniscus within 0.005 mm at 1 and 2 ms; wall front within 0.02 mm (1 cell); wall water within 1 %; yarn-face water inflow within 5 %, gap faces within 2 %; air through the yarn faces ≤ the reference's; `check.py` passes; max \|U\| within 0.1 m/s |
| `bench_B0` | `bench_A` | `inlet` p → `totalPressure`, α inlet unchanged (0.99 / 1) | same bounds as `bench_B` |
| `1D_ref` | `../waterOnlyReservoir/1D_bath0` | none | bit-identical to the stored run |
| `1D_B` | `1D_ref` | `inlet` p → `totalPressure`, α inlet uniform 1 (the porous outlet face keeps its coded air-at-0 BC: no counterpart in the REV) | front and uptake slopes within 0.5 % (uptake probably lower: at the first cell's state, S 0.964, the product term goes from −18 to −46 Pa), first-cell S within 0.01, steps within 1 % |
| `1D_B0` | `1D_ref` | `inlet` p → `totalPressure`, α inlet 0.99 | front and uptake within 0.3 % (bath water at −6.8 Pa) |
| `REV_ref` | `meshing_strat_trial/REV` | none (`./Allpre`, N 4, to 0.1 ms, writes every 0.025 ms) | reference |
| `REV_A` | `REV_ref` | `top`/`bottom` → `totalPressure`; `Uwetting`/`UnonWetting` zeroGradient; to 0.05 ms | bit-identical to `REV_ref` at 0.025 and 0.05 ms (exceptions as `bench_A`) |
| `REV_B` | `REV_ref` | the proposed set (the files later copied to the case), to 0.1 ms | at every write: y-yarn front within 0.02 mm, mean porous S within 0.001, free box water within 2 %, water in the domain within 0.5 %; max porous α ≤ 1.001 in both runs; budget closed (≤ 1e-13 m³); no stopGuard |

Added after the bench results (`bench_B`: yarn-face inflow −10 / −12 % at 1 / 2 ms, see Results), before any REV
result was looked at:

| Run | From | Change | Prediction |
|---|---|---|---|
| `REV_B0` | `REV_B` | α as `REV_ref` (yarn inlet faces 0.99), to 0.1 ms | integral bounds as `REV_B`. Yarn-face inflow of the inlet: `REV_B0` within 3 % of `REV_ref`, `REV_B` within 5 % (the first yarn cells start saturated at 0.99, so the product term stays below ~20 Pa, against −30 to −66 Pa at α_c 0.95 in the bench) |

## Results (2026-10-27)

**Bench: the parts claimed identical are bit-identical (pass).** `bench_ref` = stored `bench_waterOnly` (482 files
over the 40 writes, waterBudget.csv, liquidBalance.csv: the installed solver is the tested J build). `bench_A` =
`bench_ref` in every compared value, except the written wall (top/bottom) values of `Uwetting`, `UnonWetting`, `Ur`,
as predicted: `totalPressure` on the outlet (free faces) gives the same p as `pOpenAir`, bit for bit, and the
phase-velocity BCs do not enter the solution.

**Bench B and B0** (`compare.py bench`; inlet flux in m³/s per 20 µm depth, in < 0):

| Run | meniscus 1 / 2 ms (mm) | wall front 1 / 2 ms (mm) | wall water 2 ms | yarn faces water 1 / 2 ms | gap faces water 1 / 2 ms | total in 2 ms | max \|U\| | checks |
|---|---|---|---|---|---|---|---|---|
| `bench_ref` | 0.430 / 0.790 | 0.750 / 1.170 | 372.7 | −2.368e-10 / −1.792e-10 | −2.223e-9 / −1.996e-9 | −2.175e-9 | 1.20 | all pass |
| `bench_B` (α_b 1) | 0.430 / 0.790 | 0.750 / 1.170 | 372.4 (−0.08 %) | −2.134e-10 / −1.573e-10 (−10 / −12 %) | −2.250e-9 / −2.021e-9 (+1.2 / +1.3 %) | −2.178e-9 (+0.1 %) | 1.19 | all pass |
| `bench_B0` (α_b 0.99) | 0.430 / 0.790 | 0.750 / 1.170 | 372.6 (−0.03 %) | −2.302e-10 / −1.727e-10 (−2.8 / −3.6 %) | −2.231e-9 / −2.003e-9 (+0.4 / +0.4 %) | −2.176e-9 (+0.04 %) | 1.20 | all pass |

- Meniscus, wall front, wall water, total uptake, budget (≤ 8e-15), `check.py`: as predicted, unchanged.
- **Yarn-face inflow of `bench_B`: −10 / −12 % at 1 / 2 ms, outside the predicted 5 % (prediction not met);**
  `bench_B0` −3 % (met). The walls take the difference from the gap (gap faces +1.2 %): the split of the inflow
  between yarn and gap faces moves by ~1 % of the total inflow.
- Why: the first wall cells at the inlet are not saturated (α_c 0.95–0.96, pc_c ~1.5 kPa) and are almost in
  equilibrium with the bath (p_w,c −58 to −114 Pa): the net drive across the half cell of the yarn faces,
  Δp_w + (α_b − α_c)(pc_b − pc_c), is only ~25–30 Pa. The product term is −29 to −39 Pa in `bench_ref` (α_b 0.99)
  and −66 to −80 Pa in `bench_B` (α_b 1): the yarn-face inflow follows (B0: bath water −6.8 Pa, product term as the
  reference, −3 %). The product term is a discretisation error of the mixture-pressure boundary flux (the
  reference carries one of the same size), so neither run is the exact yarn-face inflow; it is a local effect
  (8 % of the inflow enters through the yarn faces here), invisible in the wall water and the fronts.
- "Air" through the yarn faces (phi − alphaPhi0 on those faces): 2.4e-12 → 2e-14 m³/s in all runs, 0.02–0.2 % of
  their water flux, slightly higher in `bench_B` at 1–2 ms (prediction "≤ the reference" not met at 1–2 ms). Its
  size matches the change of the face flux over one time step (alphaPhi0 is computed with the flux of the start of
  the step, phi written at its end; hypothesis, not checked).

**1D** (`compare.py 1D`; slopes vs √t for t ≥ 10 ms; reference values of the similarity solution: front 18.044,
uptake 6.1048 mm/√s, S_in 0.99; the bath at 0 Pa is another problem, as in `../waterOnlyReservoir`):

| Run | front (mm/√s) | vs `1D_ref` | uptake (mm/√s) | vs `1D_ref` | uptake at 30 ms | first-cell S (10–30 ms) | p_air first cell 25 ms | steps |
|---|---|---|---|---|---|---|---|---|
| `1D_ref` (= stored `1D_bath0`, bit-identical, 361 files) | 18.610 | | 6.3828 | | | 0.9636 | 1301 Pa | 49,005 |
| `1D_B` (α_b 1) | 18.583 | −0.15 % | 6.3674 | −0.24 % | −0.36 % | 0.9633 | 1278 Pa | 48,999 |
| `1D_B0` (α_b 0.99) | 18.604 | −0.04 % | 6.3787 | −0.06 % | −0.09 % | 0.9635 | 1295 Pa | 49,004 |

Predictions met: `1D_B` within 0.5 % and lower in uptake (first cell at S 0.964, product term larger with α_b 1),
first-cell S within 0.0003, steps within 0.02 %; `1D_B0` within 0.1 %.

**REV** (scratch copies, 4 cores, `compare.py identical` / `compare.py rev`; 799 steps to 0.1 ms, ~1,100–1,430 s):
- `REV_A` = `REV_ref` at 0.025 and 0.05 ms in every compared value (α, p, U, φ, alphaPhi0 of all cells and patches;
  waterBudget.csv and liquidBalance.csv rows), except the written wall (outlet, inletPad) values of `Uwetting`,
  `UnonWetting`, `Ur`: as predicted, in 3D and in parallel.
- `REV_B` vs `REV_ref`, every write (0.025 / 0.05 / 0.075 / 0.1 ms):

| Quantity | `REV_ref` | `REV_B` | prediction |
|---|---|---|---|
| y-yarn front (mm) | 0.311 / 0.331 / 0.351 / 0.371 | identical | met |
| mean porous S | 0.1002 / 0.1035 / 0.1064 / 0.1089 | 0.1002 / 0.1035 / 0.1063 / 0.1089 | met |
| free box water (cells) | 1450.3 / 1227.6 / 979.6 / 786.8 | 1449.7 / 1226.5 / 977.9 / 784.6 (≤ −0.3 %) | met |
| water in the domain (m³) | 4.36227 / 4.28740 / 4.17023 / 4.09335 e-11 | −0.02 / −0.03 / −0.05 / −0.06 % | met |
| max porous α | 0.9975 / 0.9970 / 0.9958 / 0.9941 | 0.9975 / 0.9970 / 0.9958 / 0.9934 | met |
| budget imbalance | ≤ 3.1e-24 m³ | ≤ 3.3e-24 m³ | met |
| yarn faces water (m³/s, in < 0) | −2.977e-9 / −2.790e-9 / −4.168e-9 / −5.993e-9 | −2.491e-9 / −2.382e-9 / −3.761e-9 / −5.887e-9 (−16 / −15 / −10 / −1.8 %) | 5 %: not met at the first three writes |
| gap faces water (m³/s, out > 0) | +1.861e-8 / +4.801e-8 / +3.849e-8 / +2.544e-8 | −2.9 / −0.2 / −0.1 / −0.2 % | (none) |
| inlet net inflow, cumulative (m³) | +1.06e-13 / −6.42e-13 / −1.81e-12 / −2.58e-12 | +0.98e-13 / −6.56e-13 / −1.83e-12 / −2.60e-12 | (none) |

- In both runs water leaves through the gap faces of the inlet (the 0.1 mm gap column drains back into the bath,
  1,645 → 785 cell volumes by 0.1 ms) while the yarn faces take water in: the net exchange is outflow (as in the
  2026-10-26 saturated-rows smoke test). Not caused by the BC change (gap faces have the same p formula).
- Why the yarn faces differ: the first yarn cells stay at α 0.990 (air trapped in the saturated rows at ~670 Pa =
  pc(0.99) holds them; J lets no air out through the bath), p_w,c −7 to −16 Pa: the net drive across their half
  cell is only 7–16 Pa (mean over the 984 faces). With α_b 0.99 = α_c the product term is ~0 in `REV_ref`; with
  α_b 1 it is −5.8 to −6.6 Pa in `REV_B` (the first cells answer with a lower p_w,c, −12.9 instead of −7.6 Pa).
  The difference fades as the drive grows (−1.8 % at 0.1 ms). Same mechanism as in the bench.
- Not covered by 0.1 ms: the α > 1 overshoot of job 3051 (inside the half yarn 5 at the inlet, from ~0.3 ms in the
  smoke tests): no porous α above 0.9975 here in either run.
- `REV_B0` (standard p, α_b 0.99) vs `REV_ref`: front, porous S, gap water (784.4 at 0.1 ms) as `REV_B`; water in
  the domain −0.02 / −0.04 / −0.05 / −0.07 % (`REV_B` −0.02 / −0.03 / −0.05 / −0.06 %); max porous α 0.9975 →
  0.9945; budget 3.3e-24 m³. Yarn-face inflow −2.447e-9 / −2.359e-9 / −3.832e-9 / −5.719e-9 m³/s, i.e. −18 / −15 /
  −8 / −5 % (`REV_B` −16 / −15 / −10 / −2 %): prediction "within 3 %" not met. With α_b 0.99, p = 0 puts the bath
  water at −6.8 Pa on the yarn faces, the size of the net drive there (7–16 Pa).

**Conclusion.** The coded `pOpenAir` is not needed in the REV. `top`/`bottom` and the phase velocities: standard
BCs give bit-identical results (bench, REV). Inlet: `totalPressure` with α 1 on all faces changes no integral
quantity (REV 0.1 ms: fronts identical, porous S within 1e-4, water within 0.06 %; bench 2 ms: meniscus, wall front
identical, wall water −0.08 %; 1D: uptake −0.24 %). The yarn-face inflow of the inlet moves by up to 16 % early
(bench −12 % at 2 ms, REV −2 % at 0.1 ms): the yarn faces sit almost in equilibrium with the bath (net drive 7–30
Pa), so a few Pa of boundary discretisation (the product term with α_b 1, or the −6.8 Pa of α_b 0.99) shows; the
old BC carries a product term of the same size where the first cells are below 0.99 (bench). α_b 0.99 with the
standard BC is not closer to the old results than α_b 1 → **chosen: α 1 on the whole inlet + `totalPressure`**
(bath-saturated yarn faces, p = water pressure there). Not tested here: the effect on the α > 1 overshoot inside
yarn 5 at the inlet (job 3051, from ~0.3 ms): to watch in the next long run.

**Applied to `meshing_strat_trial/REV/`** (2026-10-27, after `REV_B0`; not committed): `0.orig/p` (totalPressure on
inlet/top/bottom), `0.orig/Uwetting`, `0.orig/UnonWetting` (zeroGradient everywhere), `0.orig/U` (comment only),
`constant/transportProperties` (`openPorousAirZero`, `openFreeTotalPressure`, `reservoirWaterPressure`,
`reservoirReferencePoint` removed, J comment), `Allpre` (`--porous-in 1`, BC comment), `run` (comment);
`meshing_strat_trial/tools/initFields.py`: option `--porous-in` (default S_IN: other cases unchanged, checked value by
value on the REV) and `uniform` for single-valued boundary lists. `./Allpre` of the case regenerates `0/` and the
mesh byte-identical to the tested `REV_B` (`0/U`: comment). Same files in `meshing_strat_trial/REV_lowpc/` (its own
pc0 1000 Pa, m 0.4, θ0 40° kept; not run beyond a 20-step start of a scratch copy). `tools/pOpenAir` stays for the
bench and slit cases.
