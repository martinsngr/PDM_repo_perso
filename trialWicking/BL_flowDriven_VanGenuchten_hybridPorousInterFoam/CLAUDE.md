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
- The only change from the tutorial is `system/controlDict`: `stopAt writeNow; //endTime;` → `stopAt endTime;`.
  The tutorial as shipped stops after one step.
- The mesh is already in `constant/polyMesh` (2000×1×1 cells, 4 m long). `./run` does not call blockMesh or setFields.
- Fields: `0/alpha.wetting, U, Uwetting, UnonWetting, p, eps, K`. Relative permeability and capillarity models
  and their coefficients are in `constant/transportProperties` (`activateCapillarity 0` here).
- Reference run of the unmodified case: it reached t = 130000 s (~80 s wall time) and the front ended at x ≈ 3.88 m.
  Ahead of the front, alpha.wetting fell below its initial 0.002 (to 3e-5 at the outlet). This undershoot
  has not been explained yet.

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
