Working notes, setup and findings for this folder (fabric REV with hybridPorousInterFoam):

@NOTES.md

## Rules for this folder

- **Work from this folder.** It is self-contained: tools in `tools/`, cases `2D_bench/` (thick-wall slit bench),
  `2D_bench_strip/` (first bench, variants), `slit_test/` and `REV/` (the REV in one folder: geometry,
  meshing, fields and solver case).
  `../trialWicking/` holds the 1D / single-yarn cases and is the reference (read it when needed; don't add new
  work there).
- **Solver:** `hybridPorousInterFoam`, OpenFOAM 9, source `~/OpenFOAM/martin_sng-9/run/hybridPorousInterFoam/OpenFoamV8`,
  branch `of9-port` (installed `b525086`: changes A–I; H, F′, I opt-in, see `../trialWicking/hybridSolverChanges/` and NOTES.md). Don't edit
  the solver from here; solver changes go to that repo, one justified commit each. Correctness is not validated:
  never claim results are right because a case runs.
- **Solver logs never in the workspace:** use `runTmpLog` from `tools/runTools.sh` (log in /tmp, symlink in the
  case). Long runs: `LOG_EVERY=100`. Tests by hand: log to /tmp or the scratchpad.
- **Cluster: sbatch only** (mini01, OF9 at /opt/OpenFOAM-9); never run cases directly there.
- **Python:** `../.venv/bin/python` (numpy, trimesh). `REV/build_fields.py` needs trimesh; `tools/initFields.py`
  needs numpy only.
- Keep changes minimal, justified and traceable; list every change to case dictionaries; update NOTES.md
  (measured vs hypothesis kept apart). Don't commit unless asked; keep results and logs out of commits.
- Don't edit dictionaries with `foamDictionary -set`: it strips the comments.
