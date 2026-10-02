# hybridPorousInterFoam: porous-face changes for capillary-driven flow

Working log of the changes made to `hybridPorousInterFoam` (repo Franjcf/hybridPorousInterFoam, branch `of9-port`,
`be54696`) so that it can compute capillary wicking in 2D/3D. Started 2026-10-01.

**Status: committed on `of9-port` (2026-10-01), pushed to `martinsngr/hybridporousinterfoamperso`.** Commits `b0c0f67` (A), `cf95c59` (B), `b93e429` (C),
`c0c1b4e` (B fix), `b995db5` (C fix); the state before them is tagged `of9-port-before-porous-fixes` (= `be54696`).
The installed `hybridPorousInterFoam` is built from `b995db5`; the previous binary is kept as
`$FOAM_USER_APPBIN/hybridPorousInterFoam_be54696`. A and C are always active; B only with `darcyFaceMaxDa`. The diagnosis behind it is in `../NOTES.md` (Findings → hybridPorousInterFoam in 3D).

## Why

With the yarn properties (K 1e-11, Van Genuchten pc0 5000 Pa, m 0.5, initially dry at S = 0.002), the original solver:

- diverges in 2D/3D within a few hundred steps: a transverse (across-width) error grows from round-off by ×1.25–1.5
  per step. The 1D case survives only because a 1-cell-wide column has no room for it;
- in 1D, gives a "staircase" saturation profile early on (cell pairs, some inverted: 0.293/0.305, 0.068/0.147 at 5e-6 s).

The solver's own tutorials never run this regime: capillarity in porous cells is either 1D or mild (pc0 100 Pa,
m 0.8 or Brooks–Corey) with the flow driven by something else. In spontaneous imbibition capillarity is the only
driver, so its discretisation is the whole flow.

## Changes (patches in `patches/`, one per commit)

All changes only act on faces between two porous cells (`Solidf = 1`). `Solidf` is binary in this solver: a face
between a porous and a free cell has `Solidf = 0` and is computed as before, so free-fluid regions and the
porous/free interface (Darcy–Brinkman–Stokes coupling) are unchanged.

### A. Relative flux from two-point face fluxes — `alphaEqn.H`
- **Before:** `phirPore = interpolate(Ur) & Sf`, with `Ur` from the cell-centred phase velocities `Uwetting`,
  `UnonWetting` (built with `fvc::grad`).
- **After:** the phase Darcy fluxes are computed on the faces with `snGrad` (same operators as `phiPc` in `pEqn.H`):
  `φ_w = M1f [ (−∂p/∂n + (1−α_f) ∂pc/∂n − pc_f ∂α/∂n)|S| ] + L1f g·S`, same for the air with `−α_f ∂pc/∂n`, and
  `phirPore = (φ_w/α_f − φ_a/(1−α_f))/ε_f`.
- **Why:** an averaged cell gradient is blind to odd-even patterns (for two cells alternating, the two cell
  gradients cancel on their common face), so capillary diffusion did not damp them. Same physical model, compact
  stencil.

### B. Opt-in Darcy total flux — `createPorousMediaFields.H`, `pEqn.H`
- **New keyword** in `constant/transportProperties`: `darcyFaceMaxDa <value>;`. Porous faces with Darcy number
  `K_f/Δx² < darcyFaceMaxDa` are "Darcy faces". **Without the keyword there are none and the solver behaves as
  before.**
- **In Darcy faces** the pressure equation uses the Darcy mobility `Mf` instead of `rAUf` and the explicit flux
  `φ_w + φ_a` (without the `−∂p/∂n` part) instead of the momentum `HbyA`, so `phi = φ_w + φ_a` exactly, as in
  impesFoam. Cells whose faces are all Darcy faces take `U = reconstruct(phi)`.
- **Why:** with A alone the transverse mode still grew: the cell velocity U of the momentum equation alternated along
  the column (0.08–0.30 m/s in neighbouring rows) and re-entered the face fluxes through `HbyA`.
- **Physical justification (where it is switched on):** Darcy relaxation time ρK/(με) 2e-5 s (water) / 1e-6 s
  (air) ≪ wicking time scale; Brinkman layer √K ≈ 3 µm < cell size (20 µm). Does **not** hold in mostly-open
  porous cells (large K): the Da criterion keeps the momentum formulation there.
- **Fix (4th patch):** on non-coupled boundary faces `deltaCoeffs` is 1/(half a cell), so Da was 4× too large
  and on a 10 µm mesh the inlet/outlet fell out of the Darcy set (Da 0.4) while all internal faces were in it; the
  pressure equation then mixed `Mf` (~1e-8) and the dt-dependent `rAUf` (~5e-12): GAMG stalled, run diverged.
  Boundary Da now uses the cell size.

### C. Upwinded kr in porous faces — `createPorousMediaFields.H`, `alphaEqn.H`, `updateVariables.H`
- **Before:** `kr1f`, `kr2f` linearly interpolated.
- **After:** in porous faces, each phase's kr is taken from the upstream cell of that phase's Darcy flux from the
  last `alphaEqn` (`phiWettingUp`, `phiNonWettingUp`), as impesFoam (`kra upwind phia`, `krb upwind phib`).
- **Why:** linear interpolation halves the water mobility of the face between a wet and a dry cell and slows the
  front (bench, 0.2 ms: leading edge 0.134/0.076 → 0.184/0.130; impesFoam 0.208/0.146).
- **Fix (5th patch):** the momentum drag of a porous cell is the average of 1/Mf over its faces, so the upwinded
  kr also changed the momentum equation of porous cells next to free fluid. `Dragf` now uses the linearly
  interpolated mobility, as before C; upwinding only enters the Darcy fluxes.

## Tests (scratchpad bench: the 1D hybrid case widened to NX cells, symmetry sides, empty front/back)

"Spread" = maximum difference of α across the width; it should stay at round-off.

| Solver | NX = 1 | NX = 2 | NX = 5 | Notes |
|---|---|---|---|---|
| original | runs | spread 0.09 | diverges 0.12 ms | needs `minDeltaTCoats` floor in 1D |
| A | runs | spread 0.08 | spread 0.08–0.2 | smooth 1D profile |
| A+B+C, `darcyFaceMaxDa 0.1` | runs | 1e-9 | 7e-8 | same mean α for NX = 1, 2, 5; ~5× fewer steps; no dt floor needed in 1D |

Comparison with impesFoam (1D, mean α at 0.2 ms, very early, inlet-dominated):

| Cells | hybrid A+B+C | impesFoam | difference |
|---|---|---|---|
| 172 | 0.05394 | 0.05919 | −8.9 % |
| 344 | 0.05309 | 0.05737 | −7.4 % |

The front matches once kr is upwinded; the gap sits in the first cells next to the reservoir (inlet BC and the
discretisation of the inlet face: impesFoam uses dpc/dS at the face saturation, about 2× the secant slope between
0.99 and the first cell). It shrinks with refinement but not to zero.

Longer runs (A+B+C, `darcyFaceMaxDa 0.1`):
- 5-cell bench to 5 ms (8,762 steps): spread never above 4e-7.
- 1D `1D_vertical_hybrid` to 0.1 s (only the keyword added; run before the C fix, which does not act with B on in
  a purely porous case), mean α:

  | t [s] | impesFoam (`inletRes`) | hybrid original | hybrid A+B+C | vs original | vs impes |
  |---|---|---|---|---|---|
  | 0.01 | 0.3521 | 0.3374 | 0.3351 | −0.69 % | −4.8 % |
  | 0.03 | 0.6058 | 0.5853 | 0.5825 | −0.48 % | −3.8 % |
  | 0.05 | 0.7768 | 0.7533 | 0.7508 | −0.33 % | −3.3 % |
  | 0.07 | 0.8746 | 0.8566 | 0.8553 | −0.15 % | −2.2 % |
  | 0.10 | 0.9015 | 0.8908 | 0.8913 | +0.06 % | −1.1 % |

  The changes move the 1D uptake by less than 0.7 %; the gap to impesFoam was already there (inlet treatment)
  and shrinks with time. 497 s instead of 758 s (no dt floor active, 3 % fewer steps).

Rerun of `../1D_vertical_hybrid` with the installed solver (2026-10-01, `darcyFaceMaxDa 0.1`, no dt floor;
old results in `../1D_vertical_hybrid/results_oldsolver/`, compared in `../wickingFront.ipynb`): mean α 0.8913 at
0.1 s (old 0.8908, impesFoam 0.9015). Front at S = 0.1, Lucas–Washburn k: impesFoam 18.35, new 18.03 (−1.7 %),
old 18.23 mm/√s. The old profiles show the staircase and a spurious foot (S ≈ 0.02–0.07) running ahead of the front,
which reached the top before impesFoam (0.0317 vs 0.0333 s) and made h/√t jump (18.05 → 18.32 → 18.19); the new
profiles are smooth like impesFoam's and h/√t decreases smoothly (18.26 → 17.95), as impesFoam's (18.68 → 18.24).

Tutorial regression (`darcyFaceMaxDa` absent, 0.02 s):
- `Free_Flow_Cases/Capillary_Rise/standard_Boundary` (pure free flow): `alpha.wetting`, `U`, `p` **bit-identical**
  to the original solver (895 steps). Free-fluid faces are unaffected.
- `Free_Flow_Cases/Capillary_Rise/porous_Boundary` (free rise between porous walls, K 1e-20, not required, kept
  for the interface work): **not identical.** A alone: free water +0.40 %, meniscus a few cells higher near the
  left wall; A+C (with the C fix): +0.11 %; porous α differs by ~1e-3. The original solver gives identical results
  with a 10× tighter p tolerance, so this is a real effect, not run-to-run noise. Interface faces are untouched
  (`Solidf = 0`), so it comes through the porous solution next to the interface; mechanism not identified yet.

Yarn case (`../singleYarn_vertical_hybrid`, closed lateral wall, scratch copy with `darcyFaceMaxDa 0.1` and
`minDeltaTCoats 0`, 4 cores, 0.2 ms): **runs** (original solver: diverged within 10 steps). dt at the Coats limit
(~5.1e-8, CFL 0.50, same as impesFoam on this mesh), α in [0.002, 0.99], mean α 0.034 / 0.048 / 0.058 at
0 / 0.1 / 0.2 ms. All 42,581 internal faces are Darcy faces; 1,628 of 12,938 boundary faces are not (thin snapped
wall cells, Da from the centre-to-face distance; zero flux there since the wall is closed). 5.3 min for 0.2 ms,
i.e. ~1.9M steps and roughly 1.5–2 days for 0.1 s on 4 cores.

Other checks: `darcyFaceMaxDa` absent → no Darcy faces, results as A alone; all faces Darcy → identical to the
ungated prototype; the 4 patches apply cleanly on `of9-port` `be54696` (`git am --directory=OpenFoamV8/solvers`).

## Open items
- Porous_Boundary tutorial difference (see Tests): understand before the fabric/gap work.
- Inlet difference (D): only partly explained.
- **Porous/free interface with a wet porous side fails in the original solver too (2026-10-01).** 2D test:
  porous strip (ε 0.5, K 1e-11) | band of split cells (ε 0.75, K 5e-11, Da 0.125) | free air gap (ε 1), 20 µm
  cells, water entering the porous part from below with the usual 0.2 mm ramp. The original solver, A+C and A+B+C
  all diverge within ~11 steps (1.2e-9 s); it starts in the split cells next to the gap, at the wet end of the
  ramp (x 0.23 mm, y 0.15–0.23 mm). Not caused by A/B/C (those faces have `Solidf = 0`). Suspected: the
  mixture pressure in porous cells is p_air − α·pc(α), in free cells it is p, and nothing on an interface face
  (`Solidf = 0`) accounts for the jump α·pc (which with m = 0.5 stays ≈ pc0 even when dry). **Next problem to
  understand before the fabric case.** The Da switching itself (3,430 of 6,688 faces Darcy) could not be checked yet. Cells with some Darcy and some non-Darcy
  faces keep the momentum U, and the U correction in `pEqn.H` then divides Darcy-face fluxes by `rAUf`: to check.
- `createPorousMediaFields.H` interpolates kr2 with the `"kr1"` scheme name (pre-existing, harmless with the
  default linear scheme; not changed).
- Model limit for the fabric: pc0 is a single value; split cells and gaps need a pc0 field (e.g. Leverett,
  pc0 ∝ √(ε/K)).

## Using it / tracking
- Cases opt in with `darcyFaceMaxDa 0.1;` in `constant/transportProperties` (A and C are always on).
- See the changes: `git log of9-port-before-porous-fixes..of9-port` and `git diff of9-port-before-porous-fixes of9-port`
  in the solver repo; the same commits are exported in `patches/` (paths relative to `OpenFoamV8/solvers`).
- Go back to the old solver: run `$FOAM_USER_APPBIN/hybridPorousInterFoam_be54696`, or rebuild from the tag
  (`git checkout of9-port-before-porous-fixes`, `wmake`).
- Checked: the installed binary gives bit-identical results to the tested experimental build (1D, 0.2 ms).
