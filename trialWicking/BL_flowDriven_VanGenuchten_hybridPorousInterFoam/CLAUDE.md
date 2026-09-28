# Context: hybridPorousInterFoam trial (OpenFOAM 9)

## Goal
Replicate the user's earlier impesFoam wicking setup (parent folder `trialWicking/`) using
**hybridPorousInterFoam** instead. This folder started as a clean copy of the solver's tutorial
`Darcy_Flow_Cases/Buckley-Leverett/flow_Driven_VanGenuchten`. This is master-thesis work.

## Solver
- Source: `~/OpenFOAM/martin_sng-9/run/hybridPorousInterFoam/OpenFoamV8` (repo Franjcf/hybridPorousInterFoam),
  branch **`of9-port`** (9 commits on top of `master`, d98e12e..be54696). Built and installed in
  `$FOAM_USER_APPBIN`, with its 3 libraries in `$FOAM_USER_LIBBIN`.
- The port only renamed API calls, mirroring OF9 `interFoam`: fvOptions → fvModels/fvConstraints,
  the new `CorrectPhi` signature + `pressureReference`, and link flags. Physics and numerics were left unchanged.
- Correctness is **not validated**. The user checks results against Carrillo et al. 2020 themselves.
  Never claim results are correct just because the case runs.
- `hybridPorousPimpleFoam` (the single-phase solver) is **not** ported and doesn't build on OF9.
- Don't edit the solver source from here. Solver changes belong in that repo, on `of9-port`, one justified commit each.

## This case
Since 2026-09-28, this folder is no longer the tutorial. It is the hybridPorousInterFoam version of
`../1D_vertical_impes` (vertical capillary wicking, impesFoam). The tutorial state is in git history and in the
solver's `tutorials/Darcy_Flow_Cases/Buckley-Leverett/flow_Driven_VanGenuchten`.

- **Mesh:** `system/blockMeshDict`, the same as the 1D impesFoam case: 0.55 × 3.446 × 0.237 mm, 1×172×1 cells (20 µm),
  axis y, patches `inlet` (bottom) / `outlet` (top) / `frontAndBack` (empty). `./run` calls blockMesh.
- **Properties** (as impesFoam): water (ν 1e-6, ρ 1000) / air (ν 1.76e-5, ρ 1), eps 0.5, K 1e-11, Brooks–Corey kr
  n = 3, Van Genuchten pc0 5000 Pa, m 0.5, Smin/Smax 0/0.999, g (0 -9.81 0). The whole column is porous (eps < 0.99).
- **No reservoir:** alpha.wetting is fixed at 0.99 on `inlet` (impesFoam clamped a 0.2 mm cellZone at Sb 0.99).
- **BCs** (same meaning as impesFoam):

  | Patch | alpha.wetting | p (mixture) | U | Uwetting | UnonWetting |
  |---|---|---|---|---|---|
  | `inlet` | fixed 0.99 | fixed −669 | zeroGradient | zeroGradient | fixed 0 |
  | `outlet` | fixed 0.001 | fixed −4995 | zeroGradient | fixed 0 | zeroGradient |

- **`p` is the mixture pressure** α·p_w + (1−α)·p_nw = p_nw − α·pc(α) (from `updateDarcyVelocities.H` and `PcCoeff`).
  impesFoam fixed the air pressure at 0 at both ends, so here p = −α·pc(α): −669 Pa at α 0.99, −4995 Pa at α 0.001–0.002.
  These values must be recomputed if pc0, m, alpha.wettingmaxpc or the imposed alpha values change.
- **Time step:** `setDeltaT.H` only limits the Courant numbers of the total flux, not the explicit capillary diffusion
  in `alphaEqn.H`. `maxDeltaT 5e-7` is the stable impesFoam dt on the same mesh, which is an assumption, not a derived limit.
  `endTime 0.1`, write every 0.01 s, `nAlphaSubCycles 4` (unchanged from the tutorial).
- **Differences from impesFoam that remain:** a single-momentum (VOF-like) formulation instead of IMPES, Se clamped to
  [1e-4, 1−1e-4] in the kr/pc models (so no NaN above Smax), and outlet phase fluxes enforced through `correctUBc.H`
  (phi on `outlet` is overwritten with the Darcy air velocity of the adjacent cell).
- **Not run yet** (the shell was unavailable when the case was written).
- Reference run of the unmodified tutorial: it reached t = 130000 s (~80 s wall time) and the front ended at x ≈ 3.88 m.
  Ahead of the front, alpha.wetting fell below its initial 0.002 (to 3e-5 at the outlet). This undershoot
  has not been explained yet. The tutorial file had `activateCapillarity 1`, not 0 as noted before.

## OpenFOAM 9 notes
- Source terms and constraints go in `constant/fvModels` / `system/fvConstraints`. There is no `fvOptions`.
- `pMin`/`pMax` in `fvSolution` PIMPLE are a fatal error in OF9 (they belong in fvConstraints `limitPressure`).
- `singleGraph` doesn't exist in OF9. Use `postProcess -func "graphCell(start=(...), end=(...), fields=(alpha.wetting))"`
  or `graphUniform`.

## How to work with this user
- Keep changes minimal, justified and traceable, and list every change to case dictionaries.
- Ask before browsing folders outside this case folder, including the parent `trialWicking/` impesFoam setup:
  ask for paths or permission first.
- This folder is inside the git repo `PDM_repo_perso` (pushed to GitHub). Don't commit unless asked, and keep
  results/logs out of commits.
