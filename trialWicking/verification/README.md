# Verification: original vs modified hybridPorousInterFoam

The solver before and after the porous-face changes, on tutorials of the paper with an analytical solution
(Carrillo, Bourg & Soulaine 2020, JCP:X 8, 100073), Brooks-Corey closures:

| Folder | Tutorial | Paper | Tests |
|---|---|---|---|
| `BL_flow_BC` | Buckley-Leverett/flow_Driven_BrooksCorey, **inlet p fixedFluxPressure** | 4.1.1, Fig. 4B | kr, fixed-velocity inlet |
| `BL_grav_BC` | Buckley-Leverett/gravity_Driven_BrooksCorey | 4.1.2, Fig. 5B | kr, gravity |
| `eq_BC` | Gravity_Capillarity_Equilibrium/gravity_Capillarity_BrooksCorey | 4.1.3, Fig. 6 | pc terms (capillary + gravity at rest) |

Each case has two variants:

| Variant | Binary | What it is |
|---|---|---|
| `port` | `hybridPorousInterFoam_be54696` | OF9 port only, i.e. the v8 solver with the vocabulary changes (tag `of9-port-before-porous-fixes`) |
| `ABC` | `hybridPorousInterFoam` (`b995db5`) | changes A, B and C with `darcyFaceMaxDa 0.1`, as in the wicking cases |

The changes are described in `../hybridSolverChanges/README.md`. Both binaries link the same porous libraries
(`git diff be54696 b995db5 -- OpenFoamV8/libraries` is empty). The port itself (`0a408f5` -> `be54696`) only renames
OpenFOAM API calls (fvOptions -> fvModels/fvConstraints, the CorrectPhi signature, link flags); no physics term changes.

## Files

- `setupCases`: copies the committed tutorials (`git archive of9-port`) into `<case>/<variant>/`; the only change
  is `stopAt endTime` (the tutorials stop at once with `writeNow`), plus `darcyFaceMaxDa 0.1` for `ABC`, and for
  `BL_flow_BC` p `fixedFluxPressure` on the inlet instead of zeroGradient (the paper's dp/dx = 0): with Darcy faces
  the zeroGradient pair lets no water in; the original solver gives the same result with either BC.
- `<case>/<variant>/run`: runs the solver, log through `runTmpLog` (`../runTools.sh`).
  - `BL_flow_BC`: 120,000 s at dt 50 s, ~2 min each.
  - `BL_grav_BC`: 85,000 steps (dt 1 s), ~25 min each on the laptop. Stopped at t = 18,000 / 17,000 s and resumed
    (`startFrom latestTime`): the first part of each log is `log.hybridPorousInterFoam.part1.gz`.
  - `eq_BC`: endTime 30,000 s at dt 0.1 s (~300k steps), ~1.6 h each on the laptop; run with `LOG_EVERY=100`.
- `analyse.py` (`BL_flow_BC`, `BL_grav_BC`) and `analyseEquilibrium.py` (`eq_BC`): analytical solutions (closures written as in
  the solver library) and comparison. `../../.venv/bin/python <script>` writes the figure next to it and prints the
  error table.

- `inlet_eps1e-8/`: the `+ 0.001` → `+ 1e-8` inlet test (patch, log, fields, README).
- `bench_ddtCorr/` + `benchDdtCorr.py`: is change B needed? (5 × 172 × 3 bench: ddtCorr, inertia, pressure-solver
  tolerance; case, variant patch, logs, figures).

## Results

See `../NOTES.md` (Findings -> Verification).
