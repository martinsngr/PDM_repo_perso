# Maier et al. 2025 in 1D: the solver with their inputs

Question (user, 2026-11-20): with Maier et al.'s inputs (Textile Res. J. 95, 937; `NOTES_parametrization.md`), does the
solver reproduce their 1D wicking model, and how does it compare with their measured profiles? First case: f128 yarns with
PEG 400. Solver: the installed, frozen `4bb5d2e`. Nothing run with OpenFOAM yet.

## Files
- `richards1D.py`: their model written from the paper (1D Richards, Van Genuchten pc, Mualem kr, Gebart K, gravity,
  S(0) = 0.99, S(0.15 m) = 0.01, initial 0.01), finite volumes on the solver's cells, scipy `solve_ivp`. Two face fluxes:
  `--scheme maier` (their diffusion form, mean D and kr, LSODA as they did) and `--scheme ours` (the solver's form:
  pressure difference, kr of the upstream cell, change C; BDF). Options `--k4` (K × 4: the fibre diameter in Gebart's
  formula), `--bath` (S(0) = 1: water at 0 Pa, the N2c bath), `--nograv`, `--dx`, `--save`. Other cases: `f48_PEG`,
  `f256_PEG`, `f256_EG`.
- `f128_PEG/`: the OpenFOAM case (from `../waterOnlyReservoir/1D_waterOnly`): 300 cells of 0.5 mm over 0.15 m, gravity −y,
  ε 0.84, K 1.112e-10 m² (Gebart with the radius, c = 57), PEG μ 0.0948 Pa·s, ρ 1120 kg/m³, air μ 1.8e-5 Pa·s, ρ 1.2 kg/m³,
  `relativePermeabilityModel VanGenuchten` and `capillarityModel VanGenuchten` sharing `VanGenuchtenCoeffs` (pc0 1652.89 Pa,
  m 0.7767857), saturation limits 0 / 1. Inlet = their condition (user, 2026-11-20): J, α 0.99, air at 0 Pa (coded p), so
  water at −pc(0.99) = −627 Pa; open top (coded p, air at 0 Pa; `Uwetting` 0). Initial S 0.01. 3000 s, writes every 50 s,
  `startFrom latestTime`; `./run` builds the mesh once and continues an interrupted run; `./clean`. Functions included from
  `REV_pipeline/tools`: `coatsTimeStep`, `waterBudget`, `stopGuard`. Mesh checked (checkMesh OK).
- `f128_PEG_g0/`: the same case with g = 0 (`constant/g` only).
- `compare.py`: an OpenFOAM run against the replica and their figure (P1–P3, G1–G3).
- `readFronts.py`: their fronts (S 0.1, S 0.5) traced in the figure images by code (frame calibration, series colours,
  curve components; ±0.3 mm), with lettered 8× tiles to tell the measured curves (solid with markers) from the simulated
  ones (dotted / dashed). The images (extracted from the PDF with PyMuPDF) are in `~/PDM_results/maier1D_figures/`, the
  tiles and overlays in `~/PDM_results/maier1D_overlays/` (not in the repo: derived from the paper).
- `fitFigures.py`: the traced fronts (`FIG` their simulations, `EXP` their experiments, with the identification of each
  value) and the fits: `main`/`profile` (K and gravity factors against their simulations), `candidates` (possible
  misreadings), `gravityVariants` (their eq. 6 coded literally with variants of eq. 8), `experiments` (their measured fronts,
  correct gravity term).
- `meanSaturation.py`: the right panels (S_av/S_av(t_end)) by colour against the replica variants, local growth exponents;
  writes `meanSaturation_digitised.csv`.

## Status
- **`coatsTimeStep` takes the Van Genuchten (Mualem) kr (written by Claude at the user's choice, 2026-11-20,
  `REV_pipeline/tools/coatsTimeStep`):** reads `relativePermeabilityModel`; Brooks–Corey lines unchanged; Mualem branch
  kra = (1 − Se)^0.5·(1 − Se^(1/m))^(2m), krb = Se^0.5·(1 − (1 − Se^(1/m))^m)², m from `VanGenuchtenCoeffs` (as the library);
  fatal error for another kr model, a pc model other than Van Genuchten, kr end points ≠ 1. Checks (scratch runs, installed
  `4bb5d2e`):
  - derivatives: dkra/dSe, dkrb/dSe against central finite differences over Se 1e-4 … 1 − 1e-4: ≤ 8e-6 relative; equal to
    porousMultiphaseFoam's (`krVanGenuchten.C:141–147`); the hybrid library's dkrbdS (line 140, integer `1/2`) is 25–83 % low
    for Se ≤ 0.5;
  - Brooks–Corey regression: this case with `relativePermeabilityModel BrooksAndCorey` (n 3), old tool (git `HEAD`) against
    the new, 2000 steps to 17.3 s with the Coats limit binding (CFL 0.5): Coats line, deltaT and Time identical at every step,
    α, p, U, φ identical (17 digits);
  - Mualem branch: 60 steps written at every step, the Coats CFL recomputed in Python from the written α and φ (all three
    terms, boundary faces included): equal to the log to ≤ 1.8e-15 relative at every step.
- **Inlet α `fixedValue 0.99`, not the template's `inletOutlet` (found 2026-11-20):** with the column dry at S 0.01 the
  `inletOutlet` face starts with no flux, takes the cell value (kr ~ 1e-6 with Brooks–Corey, 4e-7 with Mualem) and water never
  enters (the first run wicked nothing in 2110 s; the template avoided it with its wet ramp). `fixedValue 0.99` is their
  Dirichlet S(0) = 0.99; with J the inlet flux stays water-only.
- **Run done (12:56), results below.** Next options (user to decide): the same case with g = 0 (their curves are reading C);
  the 0.25 mm run (P4); the other three cases (`richards1D.py` has them).
- **Run (2026-11-20, laptop, `./run`):** launched 11:27; at 11:44 at 614 s simulated (0.62 s per wall-clock second, dt ~2.5 ms
  at the Coats limit), end expected ~12:50. The user closed the laptop for travel at 11:45 (lid: should keep running).
  **On return:** finished if `f128_PEG/3000/` exists and `log.hybridPorousInterFoam` is a file (not a symlink to /tmp), with
  `log.hybridPorousInterFoam.tail` next to it. Then `../../.venv/bin/python compare.py f128_PEG` (P1–P3). **If it stopped:**
  the full log is in `/tmp/f128_PEG.liHGTr/` (if /tmp survived); remove the last time folder if it lacks one of `alpha.wetting`,
  `p`, `U`, `phi`; `rm f128_PEG/log.hybridPorousInterFoam` (the dangling symlink); `cd f128_PEG && ./run` continues from the
  latest write (the mesh is kept).
- Reference curves: their Figs. 16–19, fronts traced by `readFronts.py` (2026-11-20 evening; the first readings by eye were
  off by 0.5–1.3 mm in many places, 2.3 mm at worst: "How reliable the readings are").

## Check of the replica (2026-11-20)
`richards1D.py f128_PEG --nograv` against the Richards similarity solution without gravity (Philip's method, as
`../analyseWicking1D.py`, scratch script): front (S 0.1) at 3000 s 81.8 against 82 mm, uptake 56.8 against 56.7 mm. Their
scheme converged at 0.5 mm (front at 3000 s 65.2 mm at 0.5 and 0.25 mm), as their grid study says.

## Replica results, f128 PEG (0.5 mm; front at S 0.1, uptake = liquid volume per cross-section)

| reading | 50 s | 100 s | 300 s | 600 s | 3000 s | uptake 3000 s |
|---|---|---|---|---|---|---|
| A as stated (K radius, gravity, S(0) 0.99), their scheme | 10.6 | 14.6 | 24.2 | 33.1 | 65.2 mm | 42.1 mm |
| A, our scheme (upwind kr) | 11.4 | 15.5 | 25.3 | 34.3 | 66.6 | 42.5 |
| A, our scheme, 0.25 mm | 10.9 | 15.0 | 24.7 | 33.7 | 65.9 | 42.3 |
| B: K × 4 (diameter in Gebart) | 20.1 | 27.6 | 44.7 | 59.7 | 106.6 | 63.8 |
| C: no gravity | 10.9 | 15.2 | 26.0 | 36.7 | 81.8 | 56.8 |
| D: bath inlet S(0) = 1 | 13.5 | 18.5 | 30.6 | 41.9 | 82.4 | 58.4 |

The digitised Fig. 17 (their simulated profiles) tells which reading their model is: A and C agree early and part at long
times (gravity), D is ahead from the start, B is twice as far.

**Fig. 17 read (2026-11-20):** the figures are raster JPEGs in the PDF (no vector data; f128 PEG = image xref 54, 994 × 478
px), extracted with PyMuPDF (scratch environment), axes calibrated on the frame and the tick marks (x 3.58 px/mm, S 398 px per
unit). Fronts first read by eye on 3× zoomed crops (±0.5 mm claimed), traced by `readFronts.py` since the evening (±0.3 mm);
the table gives the traced values (by eye: S 0.1 within 0.6 mm, S 0.5 up to 1 mm low at 100–600 s). Where both curves fall in
one traced component (closer than a line width) the value is the same for both.

| front | 50 s | 100 s | 300 s | 600 s | 3000 s |
|---|---|---|---|---|---|
| their simulation, S 0.1 | 11.67 | 16.20 | 27.51 | 38.29 | 81.99 mm |
| their simulation, S 0.5 | 9.92 | 14.63 | 25.28 | 35.5 | 74.52 |
| their experiment, S 0.1 | 11.67 | 17.39 | 30.79 | 42.75 | 86.19 |
| their experiment, S 0.5 | 9.92 | 14.63 | 26.86 | 38.55 | 74.52 |
| C, no gravity, our scheme, S 0.1 | 11.7 | 16.2 | 27.2 | 38.0 | 83.3 |
| C, no gravity, our scheme, S 0.5 | 10.2 | 14.2 | 24.3 | 34.2 | 75.9 |
| C, no gravity, their scheme, S 0.1 / 0.5 | 10.9 / 9.9 | 15.2 / 13.9 | 26.0 / 23.9 | 36.7 / 33.8 | 81.8 / 75.4 |
| D, bath inlet, gravity, S 0.1 / 0.5 | 13.5 / 12.6 | 18.5 / 17.4 | 30.6 / 28.7 | 41.9 / 39.1 | 82.4 / 75.1 |
| A, as stated (gravity), S 0.1 / 0.5 | 10.6 / 9.5 | 14.6 / 13.2 | 24.2 / 21.8 | 33.1 / 29.6 | 65.2 / 56.1 |

Reading (Claude, 2026-11-20, by-eye numbers; superseded by the fit below): **their f128 curves are reproduced by reading C,
without gravity** (within ~0.5 mm at S 0.5 and S 0.1 with the upwinded flux, 1–2 mm low at S 0.1 with the mean flux; with the
traced readings C with the upwinded flux is within 0.3 mm at S 0.1 to 600 s and 1.3 mm at 3000 s, −0.3 to +1.4 mm at S 0.5),
not by their stated model with gravity (A: 65 against 82 mm at 3000 s). Early times (gravity negligible) fix K·pc0: K with the radius (B, the diameter, gives 20 mm at 50 s
against 11.7). D (bath inlet) reaches 82 mm at 3000 s too, but is 2–4 mm ahead early, and their profiles start at S 0.98–0.99.
Porosity 0.856 for f128 (their REV-size study) with gravity does not fit either (12.7 / 73.1 mm at 50 / 3000 s, S 0.1).

**How reliable the readings are (2026-11-20):** text and tables read from the PDF and checked on the rendered pages (eq. 8 is
printed without the ∂ in the numerator; eq. 4 is printed ∇(p_w + ρg·e_z), literally the gradient of a constant vector; ρ given
in m³/kg: typos, the intended equations are clear). Figures: raster JPEGs, axes calibrated on the tick marks (±1 px = ±0.3 mm,
±0.003 in S), fronts first read by eye on zoomed crops (±0.5 mm claimed where a curve is clear, ±1–2 mm where dashed and solid
curves of the same colour overlap). **Revised the same evening (asked by the user, comparing the mean-saturation panels):**
the fronts are now traced by `readFronts.py` (pixels classified by series colour, curve components in ±8 rows around the
level, a line fitted per component and taken at the level; ±0.3 mm), the measured and simulated curve of each component told
apart on lettered 8× tiles (`~/PDM_results/maier1D_overlays/fronts/`). The by-eye readings were off by 0.5–1.3 mm in many
places and by 2.3 mm at worst (f48 3000 s S 0.5: 65 against 67.3 mm; f256 PEG 300 s S 0.5: 24.5 against 23.2 mm, where the
simulated and measured curves cross; f48 100 s S 0.1: the value read as their simulation was the measured curve); the f48
readings of their simulation were low throughout (0.3–2.3 mm). Every fit and table below uses the traced values; the fits
were rerun (2026-11-20 evening), the conclusions hold with changed numbers. Check: overlays of their figures with the read
points and the replica profiles (gravity and no gravity)
drawn in the figure's pixel coordinates, `~/PDM_results/maier1D_overlays/overlay_<case>.png` (not in the repo: derived from
the paper's figures); the read points sit on their dashed curves in all four. The overlays also compare whole profiles, not only
fronts: f128's 3000 s curve lies on the no-gravity profile along its whole length; f256 EG's 600 s curve has the rounded shape
of the gravity profile; f256 PEG's 3000 s curve lies between the two; f48's early curves are slower than both.

**Audit of my reading of the paper (2026-11-20, asked by the user: could a misread parameter explain the figures?).**
- *Fitting:* the paper never says the model was fitted to the wicking curves; it says the opposite (abstract: "parameterized
  using only the porosity and filament diameter … in conjunction with the material properties of the imbibing fluid";
  introduction and conclusion the same). The only fit is Van Genuchten to the pore-morphology points (Table 4).
- *Values and units, checked on the rendered pages:* Table 1 (d 18.6 / 11.7 / 8.5 µm, φ 0.86 / 0.84 / 0.86), Table 2 (η 0.0948 /
  0.01661 kg/(m·s), ρ 1120 / 1140 kg/m³; σ and θ enter only through α), Table 3 (Δx 5e-4 m, S(0) 0.99, S(0.15) 0.01, initial
  0.01), Table 4 (α in 1/Pa → pc0 = 1/α, n → m = 1 − 1/n), eqs. 4–11: all as in `richards1D.py`. The one interpretation is the
  radius in Gebart's formula (their R_f is called a diameter): the diameter doubles the early fronts (RMS 15–30 mm).
- *Their pc curves against Table 4* (`~/PDM_results/maier1D_overlays/overlay_pc_<case>.png`, Table 4 pc(S) drawn on their
  Figs. 21, 22, 11): f128 exactly on their fitted line (Fig. 22; Fig. 15 also gives α ≈ 0.0006 at 25 fibres); f48 ~10 % below
  their line; f256 PEG ~20 % above it (their Fig. 11 line corresponds to pc0 ≈ 2,050 Pa against 2,457 Pa from Table 4).
- *Their tables against each other:* d of f256: 180 dtex / 256 filaments at ρ_PES 1380 gives 8.05 µm, not 8.5 (f48, f128
  reproduce); porosities from their footnote formula with Table 1's diameters: 0.852 / 0.844 / 0.836 against 0.86 / 0.84 / 0.86;
  their REV-size study uses φ 0.856 for f128. Inconsistencies of 10–30 % in K or pc, case by case.
- *Each possible misreading against the four figures, full gravity* (`fitFigures.candidates()`, traced readings, RMS mm, f128 /
  f256 PEG / f256 EG / f48): as read 8.4 / 2.7 / 1.9 / 8.0; diameter in Gebart 15.1 / 25.7 / 29.5 / 14.3; c2 = 53 7.5 / 2.1 /
  2.2 / 7.7; footnote porosities 7.7 / 7.8 / 6.5 / 8.7; f128 φ 0.856 5.4; f256 d 8.05 µm 5.7 / 4.3; EG ρ 1113 1.8; inlet S 1
  2.7 / 8.4 / 11.1 / 6.1; our face flux 7.9 / 2.6 / 2.4 / 7.8. None reaches the reading precision (≲ 0.5 mm) for the four
  figures.
- *Why no misreading can do it:* the gravity effect is set only by ρg against pc; φ, K, η and d scale the time. For f128 both
  are confirmed inside the paper (ρ in Table 2; pc from Table 4 equal to their own Fig. 22), and its published curve still needs
  gravity at ≤ ~40 % of ρg (fit below). So the difference is between what the paper states and what their runs computed (code
  or unreported inputs), not in the reading. Hypothesis about the cause: not possible from the paper.

**A candidate for the missing factor: their eq. 8 as printed (`fitFigures.gravityVariants()`, 2026-11-20, asked by the
user).** Eq. 8 is printed K* = ρgK/η · k_rel(S)/∂S, without the ∂ on k_rel. Their eq. 6 coded literally (non-conservative
gravity term, central differences, LSODA) with K* = ρgK·G(S)/η; best RMS (mm) with K adjusted per case (K factor in brackets);
paper's inputs otherwise, full gravity (traced readings; by-eye values before the revision: 0.4 / 0.6 / 0.7 / 1.3 mm for the
printed form):

| G(S) | f128 | f256 PEG | f256 EG | f48 |
|---|---|---|---|---|
| ∂k_rel/∂S (correct) | 3.4 (1.70) | 1.9 (1.13) | 1.9 (1.01) | 7.1 (1.40) |
| **k_rel (eq. 8 as printed)** | **0.4 (1.12)** | **0.2 (0.88)** | **0.3 (0.79)** | **1.4 (0.63)** |
| only the derivative of S^0.5 | 0.6 (1.09) | 0.2 (0.87) | 0.3 (0.78) | 1.7 (0.59) |
| exponent 1/m instead of 1/m − 1/2 | 2.5 (1.57) | 1.5 (1.08) | 1.5 (0.97) | 5.0 (1.20) |
| none (g = 0) | 1.0 (1.02) | 0.4 (0.84) | 0.5 (0.75) | 2.6 (0.52) |

With the paper's K unchanged (× 1; the same run, `gravityVariants()`, first column of its output, recorded 2026-11-24): correct
form 8.4 / 2.7 / 1.9 / 8.0 mm, eq. 8 as printed 2.2 / 2.4 / 4.9 / 9.3 mm, g = 0 1.1 / 3.6 / 6.3 / 15.0 mm (f128 / f256 PEG /
f256 EG / f48). So no form reproduces the figures with the tables' K: the printed form needs K × 0.79–1.12 (f48 0.63). What
separates the forms is that a per-case K rescues the printed one (0.2–0.4 mm) and not the correct one (1.9–7.1 mm): K moves the
whole time scale, the gravity form the slowing of the front.

Why the printed form is physically wrong, whatever their code does (2026-11-20): the printed term (ρgK/η)·k_rel·∂S/∂z is
∂/∂z[(ρgK/η)·F(S)] with F(S) = ∫₀^S k_rel ds, i.e. a gravity flux with F in place of k_rel; at rest it gives a pressure rise
dpc/dz = ρg·F/k_rel instead of ρg (hydrostatics, Jurin): F/k_rel = 0.02 / 0.12 / 0.20 at S 0.1 / 0.5 / 0.99 for f128, the
liquid at rest would stand with S 0.1 at 3.2 m above the bath instead of 23 cm. The derivative follows from their own eq. 4 by
the chain rule (∇·(ρgK·k_rel/η e_z) = (ρgK/η)(∂k_rel/∂S)∂S/∂z), as in the standard 1D form ∂θ/∂t = ∂/∂z[K(θ)(∂h/∂z + 1)]
(gravity term ∂K(θ)/∂z; Richards 1931, their ref. 39) and in Parada et al.'s textile model (∂K/∂w).
With k_rel instead of its derivative the gravity term is 4–7× too weak (k_rel/(∂k_rel/∂S) = 0.15–0.23 at S 0.1–0.99), which acts
on the fronts like gravity × ~0.3. It reproduces f128, f256 PEG and f256 EG within the reading precision with no gravity factor
at all (0.2–0.4 mm), whole profiles on their curves (`~/PDM_results/maier1D_overlays/overlay_eq8printed_<case>.png`), and f48
only to 1.4 mm (its intermediate times run ~1 mm behind), where one common gravity factor 0.35 gives 0.48 mm (fit below). The slip is invisible to a units check (k_rel and its derivative are both
dimensionless). Reading (Claude): the most likely single cause of their published curves is that the code computed eq. 8 as it
is printed; a hypothesis (their code is not public), supported by (1) the printed equation lacks exactly this ∂, (2) it fits
their figures without any gravity factor, (3) the correct term fails for every K. Not explained by it: the per-case K factors
(1.12 / 0.88 / 0.79 / 0.63); f256 EG's 0.79 equals their Fig. 11 pc over Table 4's EG pc (2,050 / 2,597), f48's 0.63 has no
candidate; and f48 itself (1.4 mm against 0.48 with a uniform factor 0.35). With the correct gravity term their model and inputs
miss their experiments by −21 / −9 / −3 / +12 mm at the last time (S 0.1, their face flux; S 0.5: −18 / −10 / −4 / −1 mm), so the
published model–experiment agreement rests partly on this (section "Their measured fronts with the correct gravity term").

**Fit of the replica to all four figures (`fitFigures.py`, 2026-11-20; supersedes the per-figure readings below).** Two
factors per case on the paper's inputs: fD on K (at fixed pc) and fg on gravity; RMS over the fronts at S 0.1 and S 0.5 at
their five times, their scheme (mean flux, LSODA, banded Jacobian). Best RMS (mm) over fD at each fg (`profile()`, traced
readings, rerun 2026-11-20 evening):

| fg | 0 | 0.1 | 0.2 | 0.3 | 0.35 | 0.4 | 0.5 | 0.75 | 1 (paper) |
|---|---|---|---|---|---|---|---|---|---|
| f128 PEG | 1.04 | 0.73 | 0.41 | 0.26 | 0.35 | 0.51 | 0.90 | 2.03 | 3.52 (K at the 1.6 bound) |
| f256 PEG | 0.43 | 0.27 | 0.17 | 0.26 | 0.35 | 0.45 | 0.66 | 1.23 | 1.86 |
| f256 EG | 0.55 | 0.38 | 0.28 | 0.32 | 0.38 | 0.46 | 0.67 | 1.24 | 1.91 |
| f48 PEG | 2.57 | 1.98 | 1.34 | 0.68 | 0.48 | 0.58 | 1.38 | 4.10 | 7.10 |

With the paper's inputs (fD 1, fg 1): 8.4 / 2.7 / 1.9 / 8.0 mm. **One common gravity factor 0.35 fits all four figures within
the reading precision** (RMS 0.35 / 0.35 / 0.38 / 0.48 mm; by-eye readings: 0.53 / 0.77 / 0.71 / 0.42) with K × 1.21 / 0.92 /
0.83 / 0.73 (f128 / f256 PEG / f256 EG / f48; by eye 1.20 / 0.94 / 0.82 / 0.70); the profiles then lie on their curves along
their whole length, not only at the fronts (`~/PDM_results/maier1D_overlays/overlay_fit_<case>.png`, by-eye factors). f48
(weakest pc, strongest gravity effect) pins the factor: 0.3–0.4; the finer yarns allow 0.1–0.4; full gravity misfits f128 and
f48 for any K, no gravity misfits f48. Reading (Claude): their code solves the same
equations, but their runs have gravity ~1/3 as strong relative to capillarity as the paper's inputs give, in every case, plus
case-by-case K·pc factors of 0.7–1.2. A common factor points to one systematic difference in their code or inputs, not to
per-case tuning. Equivalent and not separable from the figures: pc ~2.9× the tables' with K ~2.9× lower (same curves). Which
it is: only the authors can say. The earlier readings "f128 = no gravity" and "f256 EG = gravity" were each one end of this
picture (f128 allows fg 0.1–0.45; f256 EG's 600 s match with full gravity was two differences cancelling).

**The other three figures do not follow that pattern** (earlier reading, superseded by the fit above; figure values traced,
replica with our face flux; front at S 0.1 / S 0.5 in mm):

| case, time | their simulation | A (gravity) | C (no gravity) | their experiment |
|---|---|---|---|---|
| f256 PEG, 600 s | 35.55 / 32.84 | 36.8 / 32.5 | 39.5 / 35.6 | 37.32 / 32.84 |
| f256 PEG, 3000 s | 77.5 / 71.22 | 74.1 / 64.6 | 86.7 / 79.0 | 82.07 / 73.86 |
| f256 EG, 120 s | 37.14 / 34.31 | 40.2 / 35.5 | 43.3 / 39.1 | 39.65 / 34.31 |
| f256 EG, 600 s | 80.38 / 73.91 | 80.6 / 70.0 | 95.0 / 86.7 | 82.36 / 73.91 |
| f48 PEG, 50 s | 11.54 / 10.61 | 14.0 / 11.9 | 15.1 / 13.2 | 10.69 / 9.60 |
| f48 PEG, 3000 s | 75.3 / 67.32 | 63.4 / 46.2 | 108.5 / 99.1 | 50.27 / 46.72 |

f256 EG fits the model with gravity at 600 s (but runs ~8 % slower than our inputs at 120 s); f256 PEG lies between A and C;
f48 differs already at 50 s, where gravity does not act (their K·pc0 ~0.6 × ours there). **So their published curves cannot
be reproduced from the paper's tables with one model: per-case inputs (porosity, K, pc, time origin) must differ from the
tables in ways the paper does not give.** The no-gravity match of f128 may be a coincidence of such differences; it does not
show that they left gravity out. Their gravity term (eq. 6–8: K*(S)·∂S/∂z with K* = ρgK/η·∂kr/∂S; the printed eq. 8 lacks the
∂ in the numerator) follows from their eq. 4 with the right sign (it slows the rise); coded literally (non-conservative,
central differences, LSODA; scratch test 2026-11-20) it gives the flux-form results within 0.1 mm for f128 (65.2 / 56.1 mm at
3000 s): the way they lump gravity does not explain the f128 figure. **What would (scratch test, f128, gravity on, our face
flux):** the early fronts fix only the product K·pc0 (capillary diffusion), the late front the ratio ρgh/pc (gravity against
capillarity, 0.9 kPa at 80 mm against pc 1.6–3 kPa here). Same K·pc0 with pc0 × 2 / 3 / 4 / 6 (K ÷ the same): early fronts
unchanged (50 s 11.6–11.7 / 10.0–10.1 mm), 3000 s 74.3 / 77.1 / 78.6 / 80.2 mm (S 0.1) against their 82 mm. Their f128 curve
needs gravity ~6× weaker relative to capillarity than the tables give (pc0 ~10 kPa with K ~1.9e-11 m², or ρg ÷ 6): not a
K computed differently (K alone moves the early fronts, which already match). Simplest single-input explanation (hypothesis,
not verifiable from the paper): gravity much weaker or absent in that one run (e.g. a slip in ρ or g); a misprinted α or K
alone would move the early fronts too. No sign of intent: the other runs show other, unrelated deviations (f48 early). Against their experiments the model with gravity and the tables' inputs is
short for the finer yarns and long for f48 (−21 / −9 / −3 / +12 mm for f128 / f256 PEG / f256 EG / f48 at the last time, S 0.1,
their face flux, traced readings; by eye −19 / −7 / +2 / +14 mm with our face flux). The authors' data and inputs would settle
it (data on request).

**Mean saturation, the right panels of Figs. 16–19 (`meanSaturation.py`, 2026-11-20 evening, asked by the user).** S_av/S_av(t_end)
read by colour (their simulation blue, the mean of their experiments green; each curve on its own pixel columns), against the
replica's uptake/uptake(t_end): A = correct gravity term, paper's inputs; eq. 8 as printed, gravity × 0.35 and g = 0, each with
the K factor of its fit to their simulated fronts. Overlays: `~/PDM_results/maier1D_overlays/overlay_Sav_<case>.png`. RMS
against their simulation | their experiment:

| case | A | eq. 8 as printed | gravity × 0.35 | g = 0 | their simulation vs their experiment |
|---|---|---|---|---|---|
| f48 PEG | 0.094 \| 0.030 | 0.028 \| 0.119 | 0.006 \| 0.097 | 0.052 \| 0.142 | 0.091 |
| f128 PEG | 0.039 \| 0.067 | 0.007 \| 0.022 | 0.003 \| 0.031 | 0.019 \| 0.018 | 0.028 |
| f256 PEG | 0.029 \| 0.075 | 0.004 \| 0.043 | 0.003 \| 0.049 | 0.011 \| 0.037 | 0.047 |
| f256 EG | 0.030 \| 0.066 | 0.006 \| 0.035 | 0.003 \| 0.039 | 0.012 \| 0.031 | 0.037 |

Local growth exponent b = d ln S_av/d ln t over t_end/16–t_end/4 | t_end/4–t_end/2 | t_end/2–t3 (√t: 0.5; t3 = 0.93–0.98 t_end,
where both traces still show):

| case | their experiment | their simulation | A | eq. 8 as printed | gravity × 0.35 | g = 0 |
|---|---|---|---|---|---|---|
| f48 PEG | 0.49 / 0.31 / 0.20 | 0.45 / 0.42 / 0.39 | 0.36 / 0.28 / 0.22 | 0.47 / 0.46 / 0.45 | 0.45 / 0.43 / 0.40 | 0.50 / 0.50 / 0.50 |
| f128 PEG | 0.61 / 0.53 / 0.49 | 0.48 / 0.47 / 0.46 | 0.44 / 0.41 / 0.38 | 0.49 / 0.48 / 0.47 | 0.48 / 0.46 / 0.45 | 0.50 / 0.50 / 0.50 |
| f256 PEG | 0.70 / 0.59 / 0.53 | 0.49 / 0.48 / 0.47 | 0.46 / 0.44 / 0.41 | 0.49 / 0.49 / 0.48 | 0.48 / 0.48 / 0.47 | 0.50 / 0.50 / 0.50 |
| f256 EG | 0.69 / 0.56 / 0.50 | 0.49 / 0.48 / 0.47 | 0.46 / 0.43 / 0.41 | 0.49 / 0.49 / 0.48 | 0.48 / 0.48 / 0.47 | 0.50 / 0.50 / 0.50 |

- *Their simulations:* gravity × 0.35 reproduces the four simulated curves (0.003–0.006, about a line width) with no new fitting,
  eq. 8 as printed three of them (f48: 0.028), the correct term none (0.029–0.094). The right panels come from the same runs as
  the left ones, so this checks the readings on another quantity and another reading method; it is not independent evidence. Same
  answer as the fronts: gravity ~1/3 in their runs, f48 against the printed form.
- *Their experiments:* in f128, f256 PEG and f256 EG the measured S_av grows faster than √t at the start (b 0.61–0.70), which no
  Richards solution does (b ≤ 0.5; gravity only lowers it). Two reasons visible in their figures: the measured profiles begin at
  ~3.5 mm (the first 1.5 mm square) where the model's begin at 0, so the early S_av counts a shorter wet length; and they fill in
  behind the front (f128 first square S 0.84 at 50 s, 0.92 at 3000 s; the model holds 0.99 at the inlet from the start). f128:
  measured S_av ×4.0 from 50 to 300 s while the measured fronts grow ×2.6–2.7. **So the measured right panels do not measure gravity
  for these three; their agreement with the simulated S_av tests neither gravity term.** f48's measured S_av bends strongly (b
  0.49 → 0.20): the correct term with the paper's inputs follows its shape (RMS 0.030; b 0.28 / 0.22 in the later windows against
  0.31 / 0.20), their simulation does not (0.091), as the authors note for f48.

**Their measured fronts with the correct gravity term (`fitFigures.experiments()`, 2026-11-20 evening).** The fronts are not
affected by the window start nor (much) by the filling-in, so they are the cleaner test. Same two factors as for their
simulations; with the correct term fg reads as pc × 1/fg and K × fD·fg (same curves). Best RMS (mm) over fD, all five times |
without the first two (their measured early rise is slower than any model, dynamic contact angle in their discussion):

| case | fg 0.2 (pc × 5) | 0.35 (× 2.9) | 0.5 (× 2) | 0.75 (× 1.33) | 1 (Table 4) | 1.5 (× 0.67) | 2 (× 0.5) |
|---|---|---|---|---|---|---|---|
| f128 PEG | 1.93 \| 2.43 | 1.46 \| 1.74 | **1.12 \| 1.01** | 1.49 \| **0.88** | 2.75 \| 2.56 | 6.17 \| 6.94 | 9.79 \| 11.59 |
| f256 PEG | **0.90 \| 0.91** | 0.94 \| 0.99 | 1.09 \| 1.21 | 1.54 \| 1.80 | 2.16 \| 2.54 | 3.69 \| 4.40 | 5.54 \| 6.67 |
| f256 EG | 1.09 \| 1.09 | **1.01** \| 0.83 | 1.03 \| **0.71** | 1.34 \| 1.00 | 1.88 \| 1.68 | 3.33 \| 3.51 | 5.13 \| 5.76 |
| f48 PEG | 5.78 \| 7.01 | 5.23 \| 6.39 | 4.61 \| 5.71 | 3.56 \| 4.51 | **2.89 \| 3.71** | 4.62 \| 5.65 | 7.40 \| 8.98 |

- Measured: f128 is fitted to ~1 mm with pc × 1.3–2 (K × 0.7–1.3, K·pc × 1.45–1.7), f256 EG to 0.7–1.0 mm with pc × 2–2.9
  (K × 0.3–0.45), f256 PEG to 0.9 mm with pc × 2.9–5 (flat: K·pc × 1.0 is set, the split is not); Table 4's pc gives 1.7–2.8
  mm (f128: S 0.5 front at 3000 s ~69–70 against 74.5 mm). f48 is fitted by no pc scale (2.9 mm at best, at Table 4's pc): its
  measured front stays sharp while it slows (S 0.1 and S 0.5 3.6 mm apart at 3000 s; the model with the paper's inputs 16 mm; near
  equilibrium a Richards profile with this flat pc(S) spreads S 0.5–0.1 over ~60 mm). Residuals ~1 mm (2–3× the reading
  precision): the model does not follow the measured profiles' shape and slow start exactly.
- Reading (Claude, hypothesis): with the correct gravity term, the finer yarns' measured fronts need gravity weaker relative to
  capillarity than Table 4's pc gives, i.e. an effective pc ~1.3–2× (f128) to ~2–5× (f256) Table 4's; their runs' slip (× 0.35,
  the same as pc × 2.9) acts in that direction, at or beyond its upper end, and moves f48 (which needs Table 4's pc or less)
  the wrong way, the case the authors flagged. **So the published agreement of f128 and f256 rests on two differences that
  partly cancel: the gravity term, and a pc (or another input) too low for those yarns.** "pc scale" is an effective number: it
  also stands for anything else that holds the measured liquid higher (the shape of pc(S), Gebart's K for a random bundle, the
  filling-in); the fronts cannot tell which. For the pore-morphology route this means their experiments do not validate the
  computed pc as published.

## Result of `f128_PEG` (run 2026-11-20 11:27–12:56 on the laptop, installed `4bb5d2e`; `compare.py f128_PEG`)
Reached 3000 s, no stopGuard, ~1.07 million steps, 5,282 s; dt 2.5–2.8 ms at the Coats limit (3.6 ms at the end).

| t | front S 0.1 run / replica (ours) | front S 0.5 | uptake (mm) | first-cell S |
|---|---|---|---|---|
| 50 s | 11.78 / 11.43 (+3.1 %) | 9.89 / 9.79 (+1.0 %) | 7.60 / 7.47 (+1.7 %) | 0.9883 / 0.9886 |
| 100 s | 15.94 / 15.55 (+2.5 %) | 13.59 / 13.48 (+0.9 %) | 10.38 / 10.25 (+1.3 %) | 0.9888 / 0.9890 |
| 300 s | 25.73 / 25.35 (+1.5 %) | 22.29 / 22.18 (+0.5 %) | 16.90 / 16.77 (+0.8 %) | 0.9892 / 0.9894 |
| 600 s | 34.73 / 34.32 (+1.2 %) | 30.11 / 30.01 (+0.4 %) | 22.77 / 22.64 (+0.6 %) | 0.9894 / 0.9895 |
| 3000 s | 66.97 / 66.56 (+0.6 %) | 56.55 / 56.48 (+0.1 %) | 42.60 / 42.49 (+0.3 %) | 0.9896 / 0.9897 |

- **P1** (≤ 2 %): passes for the uptake (≤ 1.7 %) and the S 0.5 front (≤ 1.0 %) at every time; fails for the S 0.1 front at 50
  and 100 s (+3.1 / +2.5 %: 0.35 / 0.39 mm, under one 0.5 mm cell, in the foot of the profile), within 2 % from 300 s. The run
  is ahead of the replica at every time, by less and less (+1.7 → +0.3 % in uptake): the solver's explicit step at the Coats
  limit against BDF, or the start next to the inlet (not separated). The air, which can only slow the run, does not show.
- **P2:** passes (first-cell S 0.9883–0.9896, 0.0007 below the predicted range at 50 s, as the replica; α in [0.01, 0.9896];
  budget imbalance 2.8e-20 m³, 2.5e-12 of the water; no stopGuard).
- **P3:** fails as written: 1.07 million steps against ~0.76 million, 88 min against ~45 min. My estimate counted two faces
  per cell; the first cell's inlet face is at half a cell (its Coats sum is 1.5×), which sets dt ~2.6 ms instead of 3.9 ms;
  the laptop also ran ~40 % slower per step from ~11:40 (other runs, then the lid closed).
- **Against their figure:** the run has gravity, as their stated equations: front 67 mm at 3000 s (S 0.1) against 82 mm in
  their simulated curve and 86 mm in their experiment, as reading A. Their curves are reading C (no gravity, above).

## Result of `f128_PEG_g0` (run 2026-11-20 15:26–17:24 on the laptop; `compare.py f128_PEG_g0 --nograv`)
3000 s, no stopGuard, ~1.09 million steps, 7,042 s (the laptop also ran the figure fits), dt 2.8 ms at the end.

| t | front S 0.1 run / replica C (ours) | front S 0.5 | uptake (mm) | run − their figure (S 0.1 / 0.5), traced |
|---|---|---|---|---|
| 50 s | 12.15 / 11.73 (+3.6 %, 0.42 mm) | 10.29 / 10.16 (+1.2 %) | 7.90 / 7.76 (+1.8 %) | +0.5 / +0.4 mm |
| 100 s | 16.61 / 16.19 (+2.7 %, 0.42 mm) | 14.35 / 14.22 (+0.9 %) | 10.97 / 10.82 (+1.4 %) | +0.4 / −0.3 |
| 300 s | 27.67 / 27.23 (+1.6 %) | 24.47 / 24.32 (+0.6 %) | 18.61 / 18.45 (+0.9 %) | +0.2 / −0.8 |
| 600 s | 38.49 / 38.01 (+1.3 %) | 34.36 / 34.22 (+0.4 %) | 26.08 / 25.91 (+0.7 %) | +0.2 / −1.1 |
| 3000 s | 83.84 / 83.33 (+0.6 %) | 76.08 / 75.91 (+0.2 %) | 57.52 / 57.33 (+0.3 %) | +1.8 / +1.6 |

- **G1 passes:** uptake ≤ 1.8 %, S 0.5 front ≤ 1.2 %, S 0.1 front within one cell (≤ 0.42 mm); ahead of the replica by less and
  less, as `f128_PEG`.
- **G2 passes at 50–300 s (≤ 0.8 mm), fails at 600 s at S 0.5 (−1.1 mm) and at 3000 s (+1.8 / +1.6 mm)** (scored first
  against the by-eye readings: passed to 600 s): the run follows the replica with our face flux (upwinded kr: 83.3 / 75.9 mm),
  which runs 1.5 mm ahead of the one with their mean face flux (81.8 / 75.4 mm) at 0.5 mm cells; the 0.25 mm run (P4) would show
  whether that gap closes. Their curve is not reading C anyway (gravity × ~0.35 in their runs, fit above).
- **G3:** α in [0.01, 0.9898], budget imbalance 3.2e-13 of the water, no stopGuard, steps as predicted; 117 min against 70–90
  (laptop shared).
- Both runs (gravity on and off) reproduce the corresponding replica within 1.8 % in uptake: the solver's pure-porous path is
  verified with the Van Genuchten / Mualem laws, long times, with and without gravity. Their published f128 curve is not a
  verification target (study above): G2 only says the g = 0 run sits where their curve is.

## `f128_PEG_g0`: the same case with g = 0 (decided with the user 2026-11-20, to match their published curves)
Only `constant/g` differs from `f128_PEG` (0/, transportProperties, mesh, system identical). Predictions, written before the run:
- G1: against the replica C with our face flux (`richards1D.py --nograv --scheme ours`): uptake and S 0.5 front within 2 %
  at every profile time, S 0.1 front within one cell (0.5 mm), the run ahead early as `f128_PEG` (+0.3–1.7 % in uptake).
  Replica C, ours: S 0.1 front 11.7 / 16.2 / 27.2 / 38.0 / 83.3 mm, S 0.5 10.2 / 14.2 / 24.3 / 34.2 / 75.9 mm, uptake 7.76 /
  10.82 / 18.45 / 25.91 / 57.33 mm at 50 / 100 / 300 / 600 / 3000 s.
- G2: against their simulated curves read from Fig. 17 (S 0.1: 11.7 / 16 / 27.5 / 38.5 / 82; S 0.5: 10 / 14 / 24.5 / 34.5 /
  74.5 mm): within 1 mm at every time and level (reading ±0.5 mm, replica within 0.5 mm of it, run ~0.4 mm ahead early).
- G3: as P2 (α bounded, budget closed, no stopGuard); dt set by the inlet cell as in `f128_PEG` (~2.6 ms, gravity only
  enters the Coats gravity term, ~1e-5 of the rest), ~1.1 million steps, 70–90 min on the laptop.
Reading: G1 = the solver reproduces a Richards solution with their inputs in pure porous media, gravity off (with
`f128_PEG`, gravity on, against the replica, the gravity path too); G2 = it also reproduces their published f128 curves. G2
is not evidence that their model had no gravity (the other figures disagree, above).

## Predictions for `f128_PEG` (written 2026-11-20, before any OpenFOAM run)
- P1: front (S 0.1) and uptake within 2 % of "A, our scheme" at every profile time (11.4 / 15.5 / 25.3 / 34.3 / 66.6 mm;
  uptake 7.47 / 10.25 / 16.77 / 22.64 / 42.49 mm at 50 / 100 / 300 / 600 / 3000 s). Reasons: same space discretisation; the
  air costs ~2.5 % of the uptake for water in 1D, PEG is 90× more viscous relative to air (5,300 against 57), so far less here;
  explicit against implicit time stepping is a small effect at the Coats limit.
- P2: first-cell S 0.989–0.990; α in [0, 1]; budget closed (imbalance ≤ 1e-6 of the water); no stopGuard.
- P3: about 0.76 million steps to 3000 s (Coats estimate, `NOTES_parametrization.md`), ~45 min on the laptop.
- P4 (0.25 mm run, if made): front at 3000 s within 1 mm of the 0.5 mm run (replica 65.9 against 66.6 mm).
Fail: beyond 2 % → look at the start (dry cell 0.01 next to the 0.99 inlet), the air (rerun with μ_air ÷ 100) and the dt.
