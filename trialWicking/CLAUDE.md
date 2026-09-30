Working notes, setup and findings for the wicking cases in this folder:

@NOTES.md

## Run scripts and solver logs

- **Never write a solver log directly inside this workspace.** The solvers flush their log after every line, and
  VSCode watches the workspace: a log written here slows the run (hybridPorousInterFoam 1D: +20 %; impesFoam 1D:
  73 s → 115–209 s for the same 0.1 s). Piping the output through a filter (`| awk`, `| dd`) costs as much.
- **Use `runTmpLog` from `runTools.sh`** in every `run` script: `. ../runTools.sh`, then
  `runTmpLog log.impesFoam impesFoam` (or `runTmpLog log1.impesFoam mpirun -np 4 ...`). It writes the log in
  `/tmp/<case>.XXXXXX/`, leaves a symlink with the usual name in the case folder during the run (`tail -f` and
  `grep "^Time ="` work as before), moves the log back at the end and returns the solver's exit status.
  Used by `1D_vertical_hybrid`, `1D_vertical_impes`, `1D_vertical_impes_inletRes` and `singleYarn_IMPES_vertical`.
  `singleYarn_IMPES_yarn` (reference case) still writes its log in place.
- **Long runs: `LOG_EVERY=N ./run`.** The log is ~0.4 kB (impesFoam) to ~0.9 kB (hybrid) per time step, i.e. GBs for
  millions of steps. With `LOG_EVERY=100` only the header, the first 10 steps and every 100th step are kept after the
  run, plus the last 400 lines in `<log>.tail`; the full log only exists in `/tmp` while the solver runs.
- **If a run is killed**, the symlink stays and the full log is still in `/tmp` (a reboot may clear it). For a manual
  restart, redirect the log outside the workspace yourself, e.g. `> /tmp/log2.impesFoam 2>&1`.
- Commands launched by hand for timing or tests follow the same rule: log to `/tmp` or the scratchpad.
