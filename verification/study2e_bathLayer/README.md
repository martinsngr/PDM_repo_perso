# Study 2e — bath inside the mesh: do the gaps stay wet where they touch the bath? (2026-11-03)

**Why.** In job 3068 (`meshing_strat_trial/REV_midbath`: REV values, L, bath plane mid-gap at y 0.333 mm) the dry yarns
emptied the initial gap column within ~1 ms (4,715 → 179 cell volumes), partly back into the bath (net flow through the
bath plane −1.9e-11 m³ at 0.5 ms, i.e. ~2,400 cell volumes out). Then 927 of the 944 free faces of the bath plane stayed
closed to 30 ms: J (`waterOnlyPatches`) closes a free reservoir face while its cell is air-rich (α < 0.5), and nothing
else can refill that cell. The gaps then got no water from the bath. The 330 yarn faces carried 90–92 % of the inflow
and the 17 free cells that never drained the rest. Job 3051 (edge bath) behaves the same: 281 of 290 free faces closed.
A gap that touches a bath should not be dry at the bath level: the bath refills it. The user does not accept dry gaps
at the bath (2026-11-03). Two causes are possible: (a) J's face closure (the meniscus would have to sit on the boundary
face, which the model cannot hold); (b) the yarn–gap coupling empties the gaps even when they can always refill (at the
base pc the y-yarns stay below S_eq = 0.995–0.998, where their pc equals the gap suction 2σcosθ/w = 240–450 Pa).

**Design (decided with the user 2026-11-03: option B, the bath inside the mesh; run `B_full` only).** `B_full` = job
3068 with 5 rows (0.1 mm) of free cells added below the bath plane, full of water (the bath): 251,160 cells (job 3068:
242,060). The inlet (J, p `totalPressure` 0) is the bottom of that layer, the z faces of the layer are a closed patch
`bathWall`, and the layer also runs under the padding, so beside the fabric the bath has a free surface at y0 with air
above. Nothing is held fixed: the layer cells stay water only because the inlet below feeds them. Above the plane
everything is job 3068: cells, eps, K, fYarn, yarnID and initial α identical cell by cell (checked), REV values
unchanged (K 1e-11, VG 5000 / 0.5, θ 60°, G + H + F′ + I, J, L), 30 ms, writes every 0.5 ms. Reference: job 3068 itself
(copy `~/PDM_results/REV_midbath_run3068`). Differences from job 3068 apart from the layer: the yarn and gap faces of the
bath plane are internal faces (yarn faces: porous/free G faces, so air may leave a yarn into the bath, which J forbids
in job 3068); the bath water at the plane is at −1 Pa (hydrostatic over 0.1 mm) instead of 0; 16 cores instead of 8
(jobs 3051 / 3055, 16 / 8 cores: integrals unchanged, front 1.634 mm at 10 ms in both; local details such as the α
overshoot differed).

`R0_inlet` (job 3068 cut at y 1.496 mm) and `B_layer` (the same with the bath layer), 3 ms, 4 cores each: short variants
built and smoke-tested, **not submitted** (the user runs `B_full` only: the pair would only give an earlier answer).
Kept for diagnostics if `B_full` needs cheaper reruns.

**Files.** `makeCases.sh` writes the case folders from `REV_midbath` (changes listed at its top: `bathWall` in the
closed-wall entries of `0.orig/U` and `p`, `endTime`, `writeInterval`, `dsLocator`, N, path of `runTools.sh`;
`B_full` also gets `job_restart.slurm` and a requeue that continues from the last complete write). `buildCase.sh`
(called by each `Allpre`) builds the mesh and fields: `build_mesh.py` (REV_midbath's `build_fields.py` with the y range
changed), blockMesh, for the layer cases topoSet + createPatch (`bathWall`) and `bathLayer.py` (fields of a twin
without the layer, built beside the case). `tools` = the study 2c copies of the function objects (identical to
`meshing_strat_trial/tools`, plus `dsLocator`), so the run does not depend on the coming tensor K change of
`coatsTimeStep`. `log.initFields` of a layer case reports the fields before `bathLayer.py`; `log.bathLayer` has the
final counts (`B_full`: porous 78,489 as job 3068, free 172,671, layer 9,100 water cells, 4,715 free water cells above
the plane).

**Checks before submission (laptop scratch copies, installed `8a97d02`, 2026-11-03):** all three build in 15–40 s and
pass checkMesh (`bathWall` 910 faces). `B_full` above the plane = job 3068's 0/ cell by cell (eps, K, fYarn, yarnID, α:
max difference 0); `R0_inlet` = job 3068's first 58 rows. Smoke tests: `R0_inlet` and `B_layer` 40 steps on 4 cores,
`B_full` 20 steps on 8 cores: J and L active, dt at the Coats limit (1.23e-7 s), α in [−1e-19, 1.001], no flux through
`bathWall`; start-up imbalance 1.5e-17 m³ in `B_full` after 20 steps (job 3068: one-time −8.6e-18 m³ in the first
0.5 ms). First 10 time steps: `R0_inlet` = job 3068 to 4 digits, `B_layer` = `R0_inlet` to 6 digits.

**Commands.** After commit, push and `git pull` on mini03 (the repo `.venv` and solver `8a97d02` are there already):
`cd verification/study2e_bathLayer/B_full && sbatch job.slurm` (builds the case with `./Allpre`, then
`LOG_DIR=logs LOG_EVERY=100 ./run`; estimate ~18 h: job 3051, 242k cells on 16 cores, 2,040 s per simulated ms). Fetch:
`rsync -avz --exclude 'processor*' --exclude 'dynamicCode' msinegre@mini03.polito.it:PDM_repo_perso/verification/study2e_bathLayer/B_full/ ~/PDM_results/study2e_B_full/`.
Analysis: `meshing_strat_trial/REV_midbath/check.py`, `../study2d_gapRise/connected.py` and `satGap.py` (the first 5
rows are the layer: the inlet row of these scripts is the layer bottom), face fluxes of the bath plane from `phi` /
`alphaPhi0.wetting`.

## Predictions (written before the run, 2026-11-03)

Reference job 3068 at 0.5 / 1 / 2 / 3 / 10 / 30 ms: y-yarn front 0.865 / 0.985 / 1.185 / 1.306 / 1.947 mm, closed end
(2.990 mm) at 28 ms, fit 2–10 ms 14.35 mm/√s (2–25 ms 14.15); gap water 373 / 179 / 96 / 83 / 81 / 98 cell volumes;
free cells of the first fabric row at α > 0.5: 54 / 17 / 17 / 17 / 17 / 17 of 944; net flow through the bath plane
−1.93e-11 / −1.04e-11 / +6.1e-12 / +1.92e-11 / +7.29e-11 / +1.62e-10 m³; free max |U| at the writes 15.0 / 7.0 / 0.98 /
0.98 m/s, ≤ 0.9 m/s from 4.5 ms; lost through top/bottom 11 cell volumes by 30 ms.

| | Prediction |
|---|---|
| P1 (the question) | From 1 ms on, ≥ 50 % of the 944 free cells of the first fabric row (y 0.343 mm) at α > 0.5 at every write (job 3068: 2 %) |
| P2 (how high) | Water connected to the bath reaches y ≥ 0.40 mm by 1 ms and stays below the opening above crossing yarn 6 (0.84 mm) to 30 ms; rows ≥ 50 % water up to at least 0.37 mm (2 fabric rows) at every write from 1 ms. Basis: at S_eq 0.995–0.998 any yarn flank drains a meniscus away from the bath, so the gaps stay wet only where the bath supply beats the flank drain. Upper bound S10 (closed yarns, same plane: top 0.81 mm by 0.6 ms, 0.892 at 3 ms) |
| P3 (early transient) | As job 3068 to ~1 ms: net flow through the plane negative (part of the gap column back to the bath), then positive; net inflow at 3, 10 and 30 ms ≥ job 3068 |
| P4 (yarns) | Front fit 2–25 ms between 0 and +5 % of job 3068 (14.15 mm/√s); closed end reached 0–2 ms earlier (job 3068: 28 ms); water in the porous cells at 10 and 30 ms between 1.00 and 1.10 × job 3068 (2D bench: walls fed by a gap that rises along the whole slit run 25–40 % ahead; here the gap water stays near the bath) |
| P5 (stability) | 30 ms without stopGuard; dt at the Coats limit, 1.1–1.3e-7 s after 0.5 ms; free max |U| at the writes ≤ 3 m/s after 1.5 ms, single-write spikes up to 10 m/s accepted. If gap water stays beside crossing yarn 6 (y 0.50 mm) while yarn 6 is at S 0.2–0.5 (0.3–1.5 ms in job 3068), pump sites (> 5 m/s, 1 yarn face, α 0.2–0.4) form there and last longer than in job 3068: hypothesis from jobs 3067 / 3068; calm with gap water beside yarn 6 at that S would contradict it |
| P6 (bath layer) | Layer cells stay water (min α in the layer > 0.9 at every write); air entering the layer through the plane ≤ 1 % of the water crossing it; no flux through `bathWall`; water lost through top/bottom ≤ 50 cell volumes by 30 ms (job 3068: 11) |

**Reading.** P1 holds: J's face closure is what dried the REV gaps at the bath; the bath layer (or an immersed fabric,
option B2) becomes the REV setup, to decide with the user before the tensor K runs (`B_full` is then the scalar
reference). P1 fails (first row drained as in job 3068): the gaps empty even when the bath can always refill them, so
the cause is the yarn–gap coupling or the physics at these values (S_eq ≥ 0.995); compare with the 2D bench, whose
straight 160 µm slit kept its meniscus with J, before changing the bath again.

## Results

Not run yet.
