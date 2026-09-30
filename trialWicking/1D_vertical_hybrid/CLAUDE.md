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
This folder (renamed from `BL_flowDriven_VanGenuchten_hybridPorousInterFoam` on 2026-09-30) is the
hybridPorousInterFoam version of the 1D vertical capillary wicking case. Its impesFoam twin with the same
reservoir, ramp and properties is `../1D_vertical_impes_inletRes`. The original tutorial state is in git history
and in the solver's `tutorials/Darcy_Flow_Cases/Buckley-Leverett/flow_Driven_VanGenuchten`.

- **Mesh:** `system/blockMeshDict`: 0.55 × 3.446 × 0.237 mm, 1×172×1 cells (20 µm), axis y, patches `inlet`
  (bottom) / `outlet` (top) / `frontAndBack` (empty).
- **Properties** (as impesFoam): water (ν 1e-6, ρ 1000) / air (ν 1.76e-5, ρ 1), eps 0.5, K 1e-11, Brooks–Corey kr
  n = 3, Van Genuchten pc0 5000 Pa, m 0.5, Smin/Smax 0/0.999, g (0 -9.81 0). The whole column is porous (eps < 0.99).
- **Reservoir:** infinite, through the inlet boundary (as in the `Capillary_Rise` tutorial): alpha `inletOutlet`
  0.99, U `pressureInletOutletVelocity`. No clamped cellZone.
- **Initial state:** dry at 0.002, with the 10 bottom cells ramped linearly from 0.99 to 0.002 (`setFieldsDict`,
  applied by `./run` to a copy of `0/alpha.wetting.orig`). A sharp 0.99 → 0.002 jump at the inlet face crashes
  the run within microseconds: the discrete pc term cannot balance the jump in the mixture pressure.
- **BCs:**

  | Patch | alpha.wetting | p (mixture) | U | Uwetting | UnonWetting |
  |---|---|---|---|---|---|
  | `inlet` | inletOutlet 0.99 | computed (−669) | pressureInletOutletVelocity | zeroGradient | zeroGradient |
  | `outlet` | zeroGradient | computed (−4995 → −3908) | zeroGradient | fixed 0 | zeroGradient |

- **`p` is the mixture pressure** α·p_w + (1−α)·p_nw = p_nw − α·pc(α) (from `updateDarcyVelocities.H` and `PcCoeff`).
  Air at 0 Pa at both ends gives p = −α·pc(α). Both patches are `codedFixedValue` and compute this every step from the
  face alpha and the Van Genuchten parameters in `transportProperties` (same formula and Se clipping as the solver's
  model). A fixed outlet value (−4995 Pa, exact only while the top is dry) put the air at the top 1.2 kPa below 0 by
  0.055 s and gave 2.3 % more uptake; with the computed BC it stays within 3 Pa of 0.
- **Outlet alpha must be zeroGradient.** A fixed alpha, even equal to the column value, lets the capillary flux
  draw water in through the outlet face: it piles up in the top cell and crashes the run at ~0.035 s.
- **Phase fluxes at the ends:** on a patch where Uwetting or UnonWetting is fixedValue, `alphaEqn.H` rebuilds the
  relative flux from the two boundary velocities, and `correctUBc.H` (Uwetting fixed, U not) overwrites the total flux
  with Uwetting + UnonWetting; otherwise the relative flux on the patch is zero. Outlet: Uwetting fixed 0, so only
  air leaves. Inlet: neither fixed, so the face carries the total inward flux at alpha 0.99 (1 % air, 99 % water);
  no air escapes into the reservoir. impesFoam's inlet is water only (Ua fixed 0).
- **Time step and loops:** `setDeltaT.H` only limits the Courant numbers of the total flux, not the explicit
  capillary diffusion, so `maxDeltaT 3e-7` is set by hand. PIMPLE 1 outer / 2 pressure correctors,
  `nAlphaSubCycles 1`: about 7× faster than 2/3/4, same front, uptake within 5 %. `nCorrectors 1` crashes.
- **End time 0.1 s**, as the impesFoam cases (~18 min). Older setups (inlet alpha 1, fixed outlet p) crashed at
  ~0.058 s; this one runs to 0.1 s.
- **Output:** `liquidBalance.csv` (coded function object in `controlDict`, same format as the impesFoam fork)
  and `postProcessing/sampleDict/<t>/acrossFlow_alpha.wetting.csv` alpha profiles (same `sampleDict` as the impesFoam twin).
- **Tested (scratchpad copy, 2026-09-30):** this setup ran to 0.1 s in 18 min, alpha within [0.002, 0.99].
  Mean alpha 0.586 / 0.677 / 0.754 / 0.815 / 0.857 / 0.877 / 0.891 at 0.03 / 0.04 / 0.05 / 0.06 / 0.07 / 0.08 / 0.1 s;
  `../1D_vertical_impes` (clamped reservoir) gives 0.614 / 0.705 / 0.782 / 0.841 / 0.878 / 0.893 / 0.906. Water
  collects at the top once the front arrives (top cell 0.975 at 0.1 s), as in impesFoam, since both block water
  at the outlet.

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
