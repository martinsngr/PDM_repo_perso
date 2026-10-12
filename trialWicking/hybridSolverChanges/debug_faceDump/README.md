# Face-flux dump (debug build of hybridPorousInterFoam)

Tooling used on 2026-10-12 to find the bug fixed by change E (`Solidf` = 0.5 on porous/free faces; see
`../README.md`, change E, and `../../../meshing_strat_trial/NOTES.md`, "Step-1 flux diagnosis").

- `debug_faceDump.patch` + `dbgSetup.H`: prints, during the first 2 time steps, every flux term of `alphaEqn.H`,
  `UEqn.H` and `pEqn.H` (phi, phase Darcy fluxes, relative flux, alpha flux, rAUf, HbyA flux, phiG, phiPc,
  PcCoeff, Darcy flux, pressure-equation flux) on a few chosen faces, and alpha, p, pc, eps, Drag, rho in the
  neighbouring cells. Lines start with `DBGF` (faces) / `DBGC` (cells).
  **Bench mesh only:** `dbgSetup.H` hard-codes the 2D bench grid (50 x 1 x 15 cells, slab k = 3..10) and stops
  on any other mesh. Edit the face/cell lists there for another case or time.
- `base_step1_faceDump.log.gz`: the dump of the `base` bench with the pre-E solver (`b995db5`).
- `solidfBug_bench_alpha.png`, `solidfBug_bench_p.png`: alpha and p of the pre-E bench variants after 1 and 5 steps
  (the yarn edge rows empty into the gap in step 1; p ~1e15 Pa by step 5).

Rebuild (never in the solver repo itself): copy `OpenFoamV8/solvers/hybridPorousInterFoam` to a scratch folder,
apply the patch from inside it (`patch -p0 < debug_faceDump.patch` after adjusting the absolute paths in the patch
headers, or `patch <file> <patch>` per file), copy `dbgSetup.H` next to it, set `EXE` in `Make/files` to a new name
and the `../../libraries` paths in `Make/options` to absolute paths, then `wmake`. The patch was made against
`b995db5`; on later commits (E: `updateDarcyVelocities.H` and `createPorousMediaFields.H` changed, not the dumped
files) it should still apply.
