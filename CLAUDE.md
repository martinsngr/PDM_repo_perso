Master-thesis repo: capillary wicking in a woven fabric with OpenFOAM 9 (impesFoam, hybridPorousInterFoam).
Working notes, loaded for the whole repo:

@NOTES_cases.md
@NOTES_solver.md

## Layout
- `meshing_strat_trial/`: current work, fabric REV. Self-contained: `2D_bench/` (thick-wall slit bench),
  `REV/` (geometry, mesh, fields and solver case in one folder), `slit_test/`, `2D_bench_strip/` (first bench,
  archive), `tools/` (shared scripts, function objects, `runTools.sh`).
- `trialWicking/`: 1D column and single-yarn cases. Reference work: read it when needed, don't add new work there.
- `verification/`: all verification evidence (paper tutorials, 1D similarity, benches) and `PLAN.md` (planned
  studies, their rules: predictions before runs, one recorded solver version per study, stop after each study).
- `NOTES_cases.md` (cases) and `NOTES_solver.md` (solver): update them after each piece of work, measured results
  kept apart from hypotheses.

## Solver
- `hybridPorousInterFoam`, OpenFOAM 9, source `~/OpenFOAM/martin_sng-9/run/hybridPorousInterFoam/OpenFoamV8`, branch
  `of9-port` (installed `8a97d02`: changes A–L + H fix, see `NOTES_solver.md`). Don't edit the solver from this repo: solver
  changes go to that repo, one justified commit each, with `CHANGES_of9-port.md` updated.
- Correctness is not validated: never claim results are right because a case runs.
- `hybridPorousPimpleFoam` is not ported and does not build on OF9.

## Running cases
- **Never write a solver log inside the workspace** (the solvers flush every line and VS Code watches the workspace:
  +20 % for the hybrid 1D, 73 s → 115–209 s for impesFoam 1D; piping through a filter costs as much). Use `runTmpLog`
  from `trialWicking/runTools.sh` or `meshing_strat_trial/tools/runTools.sh` in every `run` script: the log goes to
  `/tmp/<case>.XXXXXX/`, a symlink with the usual name stays in the case during the run, the log is moved back at the end.
  Long runs: `LOG_EVERY=100` (header, first 10 steps, every 100th step, last 400 lines in `<log>.tail`). On a cluster:
  `LOG_DIR=$PWD/logs`. If a run is killed the full log is still in `/tmp`. Hand-run tests log to /tmp or the scratchpad.
- **Cluster (mini01, OF9 at /opt/OpenFOAM-9): `sbatch job.slurm` only**, never `./run` or a solver directly there.
- **Python:** `.venv/bin/python` at the repo root (numpy, trimesh, matplotlib). `meshing_strat_trial/REV/build_fields.py`
  needs trimesh, `meshing_strat_trial/tools/initFields.py` numpy only.

## Editing and git
- Keep changes minimal, justified and traceable; list every change to case dictionaries.
- Don't edit dictionaries with `foamDictionary -set` (it strips the comments): edit by hand or with sed/Python.
- The repo is pushed to GitHub. Don't commit unless asked; keep results and logs out of commits (the root `.gitignore`,
  the only one of the repo).

## OpenFOAM 9 notes
- Source terms and constraints go in `constant/fvModels` / `system/fvConstraints`; there is no `fvOptions`.
- `pMin`/`pMax` in `fvSolution` PIMPLE are a fatal error (they belong in fvConstraints `limitPressure`).
- `singleGraph` doesn't exist: use `postProcess -func "graphCell(start=(...), end=(...), fields=(alpha.wetting))"`
  or `graphUniform`.
