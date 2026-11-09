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
the plane). Analysis (2026-11-05, any mesh, cells matched by centre): `compare3068.py <run>` (per write against job 3068: front, porous
water, gap and padding water, first row, layer min α, |U|, budget; front fits; dt and |U| from the sampled log), `leakFaces.py
<run>` (where water leaves through top/bottom, padding and outer box layers).

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
The copy's `controlDict` includes `../../tools/dsLocator`, which `~/PDM_results/tools` (→ `meshing_strat_trial/tools`) does
not have: paraFoam and `foamListTimes` stop with "Cannot open include file". After each fetch, point that one include at
this study's `tools/` (done 2026-11-04):
`sed -i 's#"\.\./\.\./tools/dsLocator"#"/home/martin_sng/PDM_repo_perso/verification/study2e_bathLayer/tools/dsLocator"#' ~/PDM_results/study2e_B_full/system/controlDict`.
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

**`B_full`, job 3072** (mini03, 16 cores, 2026-11-03 17:35 to 2026-11-04 13:17; copy `~/PDM_results/study2e_B_full`; analysed
2026-11-04 against job 3068 on the same cells above the bath plane; scripts in the session scratchpad: a comparison of the
two runs above y0, a locator of the outflow faces of top/bottom, `connected.py` with cell centres written from
`blockMeshDict`). Reached 30 ms, no stopGuard; 69,994 s (2,330 s per simulated ms). dt 1.14–1.28e-7 s at the Coats limit,
below 5e-8 s only at the start (0.3 % of the sampled steps); α in [−2e-19, 1.0041] (job 3068: 1.0017), ≤ 1.0002 at 25–30
ms; budget closed (imbalance −1.6e-19 m³).

- **A leak through the open top/bottom faces carries 86 % of the inflow (P6 failed).** Lost through top/bottom 1,640 /
  3,550 / 76,800 / 283,700 cell volumes by 0.5 / 2 / 10 / 30 ms (job 3068: 11 by 30 ms), steady ~8e-8 m³/s from ~3 ms; inflow
  through the inlet 2.64e-9 m³ by 30 ms (job 3068: 1.62e-10). Where: the padding cells (the 3 free layers of 60 µm beside the
  fabric) are full of water (α 0.96–0.99) from the bath plane up to y 0.70–0.76 mm, along the whole x width (8,000–8,700
  cell volumes from 3 ms), and pour out through 1,800–2,200 of their open z faces; air enters through other top/bottom faces
  at ~1e-7 m³/s per side. **Cause: the layer also runs under the padding**, so the bath surface beside the fabric sits in
  cells whose z faces are open; water climbs the 60 µm padding along the fabric's outer face (a static meniscus on a
  vertical wall at θ 60° rises l_c·√(2(1 − sin θ)) ≈ 1.4 mm) and leaves through a boundary that holds no meniscus. A
  design error of this study: the design expected a free bath surface there.
- **Gaps (P1 passed).** First fabric row (y 0.343 mm): all 944 free cells water at every write (job 3068: 17). Gap water
  (free box cells above the plane) 5,000 / 5,900 / 9,200 / 11,200 cell volumes at 0.5 / 1 / 2 / 3 ms, 11,800–12,600 from 5
  to 30 ms (job 3068: 81–98). Water connected to the bath: top 0.544 / 0.805 / 0.825 / 0.865 mm at 1 / 3 / 10 / 30 ms, rows
  ≥ 20 % / ≥ 50 % water up to 0.484 / 0.444 mm (1 ms), 0.684 / 0.644 (3 ms), 0.744 / 0.704 (30 ms): the first gap and the
  slots around crossing yarn 6 fill and stay full; the top stops at the opening above yarn 6 (0.84 mm), as in S10 with
  closed yarns (0.892 mm). P2: top ≥ 0.40 mm by 1 ms, yes; below 0.84 mm to 30 ms, no (0.865 mm, just past the opening);
  rows ≥ 50 % up to at least 0.37 mm, yes.
- **No back-flow at the start (P3 failed):** net inflow through the inlet from the first write (+4.5e-11 m³ by 0.5 ms; job
  3068 −1.9e-11).
- **Yarns (P4 failed, larger than predicted).** y-yarn front 1.005 / 1.286 / 1.466 / 1.727 / 2.168 / 2.529 / 2.789 mm at 1 /
  2 / 3 / 5 / 10 / 15 / 20 ms (job 3068: 0.985 / 1.185 / 1.306 / 1.526 / 1.947 / 2.288 / 2.549); closed end at 22.5 ms (28);
  fit at every write 2–10 ms 15.65 mm/√s (job 3068 14.36, +9 %), 2–20 ms 15.28 (14.44, +6 %), i.e. 0.85–0.87 of the 1D 18.04
  (job 3068 0.80); water in the porous cells 1.34 / 1.36 / 1.26 / 1.23 / 1.20 / 1.17 × job 3068 at 1 / 2 / 5 / 10 / 15 / 30 ms.
  The padding water lies against the outer yarn faces from the bath plane to ~0.7 mm, so this gain mixes the feed from the
  gaps and from the padding: not separable from this run. First y-yarn row S 0.987–0.994 (job 3068 0.971–0.992), still
  below S_eq 0.995–0.998.
- **Stability (P5 passed).** Box free |U| at the writes ≤ 2.4 m/s (1.0–1.6 from 3 ms), padding 2.3–3.0 m/s; implied by the
  sampled log (all cells) ≤ 4.7 m/s after 1 ms, median 3.3–3.5 (job 3068: 0.76). The yarn 6 transient of job 3068 (15 m/s at
  its 0.5 ms write) comes earlier and shorter: 12–15 m/s at 0.20–0.35 ms in the free cell (1.189, 0.484, 0.081) mm, α
  0.25–0.42 (`dsLocator`), gone at the 0.5 ms write while the gap filled. This contradicts the P5 hypothesis (gap water
  beside yarn 6 makes the pump last longer): water-filled cells do not pump, the pump needs partly filled cells.
- **Bath layer (P6, rest):** layer min α 0.975–0.997 at the writes (stays water), no flux through `bathWall`; the air
  entering the layer through the plane was not measured.

**Reading.** P1 holds: J's face closure is what kept the REV gaps dry at the bath. With the bath inside the domain, the
first gap and the slots around yarn 6 stay full of water to 30 ms at the base pc, where the yarn S never reaches S_eq:
gaps fed by the bath hold water, unfed ones do not (estimates in `NOTES_cases.md`, gap vs yarn wicking). `B_full` is not a
usable reference otherwise: the padding leak carries 86 % of the inflow and wets the outer yarn faces, so the yarn gain
(+6–9 % front fit, +17–36 % yarn water) is not attributed. A corrected bath is needed before it serves as the scalar
reference for tensor K (decision with the user, options in `NOTES_cases.md`, START HERE).

## Option 1: bath under the fabric box only (decided with the user 2026-11-04)

**Why.** The same rule as the bath layer itself: no meniscus on a boundary face. `B_full` kept the menisci of the gaps
inside the domain, but its bath beside the fabric reached the open top/bottom faces of the padding. The user asked first
whether J could instead let water back into drained gap cells (a one-way water face): possible, but the meniscus would
still sit on the boundary face, so the refill would be driven by the pressure of an air-filled cell (≈ 0) instead of the
meniscus suction, and forcing water into an empty gap through a boundary gave a spurious kick in the slit tests (6× too
fast, 23 m/s). Option 1 chosen.

**Design.** `B_full` built as before, then (last step of `buildCase.sh`, mode `box`) the 2,730 layer cells under the
padding removed with topoSet + subsetMesh (fields mapped; `U`, `p` and the phase velocities copied again from `0.orig`).
The exposed faces join `bathWall`: the floor of the padding at y0 (546 faces, the closed `inletPad` of job 3068) and the z
sides of the layer (910). The bath is 6,370 water cells under the box; the inlet keeps its 1,274 faces; `inletPad` has no
face left. Everything else as `B_full`. The outer meniscus of a real dip (the bath climbing the fabric's outer faces, ~1.4 mm
on a flat wall at θ 60°) is left out, as weighing tests usually subtract it. Cases: `Bbox_cut` (y 0.233–1.496 mm, 111,930
cells, 3 ms, 4 cores: the leak test) and `Bbox_full` (y 0.233–3.0 mm, 248,430 cells, 30 ms, 16 cores, requeued and
continued like `B_full`).

**Checks before submission (laptop scratch copies, installed `8a97d02`, 2026-11-04):** both build (`Bbox_full` ~40 s) and
pass checkMesh; patch faces as above (top/bottom 91 × 58 / 91 × 133 faces, all above y0). Fields above the plane identical
to job 3068's 0/ cell by cell (eps, K, fYarn, yarnID, α, matched by cell centre: max difference 0 on 105,560 / 242,060
cells); the layer is all water, under the box only. Smoke tests: `Bbox_cut` 40 steps on 4 cores, `Bbox_full` 20 steps on 8:
J and L active, dt at the Coats limit (1.24e-7 s), α in [−1.5e-19, 1.0006], no flux through `bathWall`, start-up imbalance
4.4e-17 / −2.9e-20 m³; first 10 time steps of `Bbox_cut` = `R0_inlet` and `B_layer`.

**Risk.** The box's outermost z layers are 94–97 % free (yarn crests only). The bath water fills them from below, and
nothing separates them from the padding (free/free faces), so water may still spread into the padding and reach the open
faces 3 cells further. `B_full` cannot tell how much of its padding water came from below and how much from the box:
hence the leak test first.

**Predictions (written before the runs, 2026-11-04).** References: `B_full` at 1 / 2 / 3 ms: lost through top/bottom 2,070 /
3,550 / 10,670 cell volumes, padding water 1,000 / 3,900 / 7,000, gap water 5,900 / 9,200 / 11,200, y-yarn front 1.005 /
1.286 / 1.466 mm, porous water 7,262 / 10,250 / 11,814 cell volumes; job 3068: front 0.985 / 1.185 / 1.306 mm, porous water
5,426 / 7,553 / 9,179, lost ~3 by 3 ms. The cut ends at 1.496 mm, which the front nears by 3 ms: yarns compared to 2 ms.

| | `Bbox_cut`, 3 ms |
|---|---|
| Q1 (leak, decides the next run) | Lost through top/bottom ≤ 100 cell volumes by 3 ms; padding water (padding cells above y0) ≤ 50 cell volumes at every write. Fails if ≥ 1,000 by 3 ms: the water then leaves through the box's outer layers, and the open faces near the bath need another treatment (with the user) |
| Q2 (gaps) | All 944 free cells of the first fabric row water from 1 ms; gap water at 1 / 2 ms between −30 % and +5 % of `B_full` (part of its edge-layer water came from the padding) |
| Q3 (yarns) | Front at 1 / 2 ms between job 3068 and `B_full` (0.985–1.005 / 1.185–1.286 mm); porous water at 2 ms between 1.0 and 1.36 × job 3068 |
| Q4 (stability, bath) | No stopGuard; dt 1.2–1.3e-7 s at the Coats limit after 0.5 ms; free max |U| at the writes ≤ 3 m/s after 1 ms; layer min α > 0.9; no flux through `bathWall` |

| | `Bbox_full`, 30 ms (submitted only if `Bbox_cut` passes Q1) |
|---|---|
| R1 | 30 ms without stopGuard; lost through top/bottom ≤ 200 cell volumes by 30 ms (job 3068: 11) |
| R2 | First fabric row 944/944 water at every write; gap water 8,000–12,600 cell volumes from 5 ms (`B_full` 11,800–12,600) |
| R3 | Front fit 2–20 ms between job 3068 and `B_full` (14.44–15.28 mm/√s); porous water at 10 / 30 ms between 1.00 and 1.23 / 1.17 × job 3068. The share of `B_full`'s gain that remains is the gap feed |

**Commands.** After commit, push and `git pull` on mini03: `cd verification/study2e_bathLayer/Bbox_cut && sbatch job.slurm`
(4 cores, ~2.5 h); then, if Q1 passes, `cd ../Bbox_full && sbatch job.slurm` (16 cores, ~18 h). Fetch as `B_full` into
`~/PDM_results/study2e_Bbox_cut` / `study2e_Bbox_full` (`--exclude 'processor*' --exclude 'dynamicCode'`), then point the
`dsLocator` include of the copy at this study's `tools/` (above).
**Submitted (2026-11-04):** `Bbox_full` directly, as job 3078 (16 cores, ~16:47), without waiting for `Bbox_cut` (user: its result would not change anything that evening); `Bbox_cut` (job 3077) cancelled after 4 min. Q1 (the leak) is read from `Bbox_full` itself at 3 ms; Q2–Q4 apply to `Bbox_full` at the same times.

### Results `Bbox_full`, job 3078

**Run** (mini03, 16 cores, 2026-11-04 16:46 to 2026-11-05 13:01; copy `~/PDM_results/study2e_Bbox_full`, its five
`controlDict` includes pointed at this study's `tools/` by absolute path; analysed 2026-11-05 with `compare3068.py` and
`leakFaces.py` (this folder), `../study2d_gapRise/connected.py` and one-off locators in the session scratchpad). Reached 30 ms,
no stopGuard, 71,939 s (2,400 s per simulated ms; `B_full` 2,330). dt 1.25e-7 s at the Coats limit (medians 1.14e-7 at 0.5–1
ms and 1.16e-7 at 25–30 ms; below 5e-8 s only in the first 0.5 ms); α in [−2.6e-19, 1.0074]; budget: one-time 4.4e-17 m³ at the
start (as the smoke test), constant after; no flux through `bathWall` (≤ 4e-36 m³). Above the plane the 242,060 cells match
job 3068's 0/ (eps, yarnID, α identical).

- **Leak: small to ~8 ms, then a body of water pours out through the bottom (R1 failed).** Lost through top/bottom 22 / 44 / 88
  / 468 / 2,095 / 7,797 / 31,388 / 59,426 cell volumes at 0.5 / 3 / 5 / 10 / 15 / 20 / 25 / 30 ms (bottom 55,636, top 3,790 at
  30 ms; `B_full` 283,700; job 3068 11). To ~15 ms: traces in outgoing air, within 0.1 mm of the plane on both sides (at 3 ms
  all of it through faces of cells at α < 0.05, at 10–15 ms 65–80 % from cells at α 0.05–0.5), as in job 3063. From ~17 ms the
  bottom padding fills (25–30 ms: 3,734 of its 4,095 cells between y0 and y0 + 0.3 mm at α > 0.5, whole x width; top padding
  ~100 cells) and pours out through the open bottom faces (30 ms: 57 % of the water out from cells at α > 0.95). From 23 ms
  5,000–6,000 cell volumes per ms leave, 80–96 % of the bath inflow (~6,200 per ms; job 3068 at 30 ms: ~400 per ms). The bottom
  outer box layer has 749 porous cells (yarn crests), the top one 411 (hypothesis for the asymmetry, not checked: the bottom face
  of the fabric wets more).
- **Outer box layers.** The two outermost box layers (z layers 3 and 16, 94–97 % free, nothing between them and the padding) held
  the bath surface at the plane: their 182 first-row cells stayed air to 7.5 ms, all flooded at 8 ms (the other 762 free cells of
  the first row water from 1 ms). Free water in these two layers 76 / 169 / 588 / 1,122 / 1,738 cell volumes at 1 / 5 / 10 / 20 /
  30 ms, at the bottom up to y0 + 0.6 mm by 25 ms. Bath inflow 1,400–1,500 cell volumes per ms at 3–7.5 ms, 2,000–3,100 at 8–9.5
  ms, 1,100–1,350 at 10.5–16.5 ms, then rising with the leak. Cause of the flood at 8 ms: not checked. This is the risk written
  before the run (water fills the outer layers from below and reaches the padding), delayed by 8 ms.
- **Gaps.** First fabric row 762 / 944 free cells water from 0.5–1 ms to 7.5 ms, 944 from 8 ms. Gap water (free box cells above the
  plane) 1,240 / 1,786 / 1,920 / 2,512 / 2,955 / 6,893 / 8,283 / 9,601 cell volumes at 0.5 / 1 / 2 / 3 / 5 / 10 / 20 / 30 ms
  (`B_full` 5,003 / 5,890 / 9,242 / 11,247 / 11,818 / 12,271 / 12,579 / 12,484; job 3068 373 / 179 / 96 / 83 / 84 / 81 / 91 / 98);
  inner layers 4–15 alone 1,710 / 2,785 / 6,305 / 7,862 at 1 / 5 / 10 / 30 ms (`B_full` 5,194 / 8,902 / 9,202 / 9,441): `B_full`'s
  early gap water came largely through its flooded padding and outer layers. Water connected to the bath: top 0.404 / 0.424 /
  0.464 / 0.524 / 0.805 / 0.865 mm at 1 / 3 / 5 / 7.5 / 10 / 30 ms; rows ≥ 20 % / ≥ 50 % up to 0.363 / 0.343 (1 ms), 0.404 / 0.383
  (5 ms), 0.544 / 0.504 (10 ms), 0.684 / 0.604 mm (25–30 ms) (`B_full` 0.744 / 0.704 at 30 ms). The first gap fills slowly to 7.5
  ms and mostly at 8–10 ms, with the outer layers; the slots around yarn 6 by 25 ms; the top stops at the opening above yarn 6
  (0.84 mm), as in `B_full` and S10.
- **Yarns.** y-yarn front 0.985 / 1.185 / 1.326 / 1.566 / 2.008 / 2.388 / 2.629 mm at 1 / 2 / 3 / 5 / 10 / 15 / 20 ms (job 3068 0.985
  / 1.185 / 1.306 / 1.526 / 1.947 / 2.288 / 2.549; `B_full` 1.005 / 1.286 / 1.466 / 1.727 / 2.168 / 2.529 / 2.789); closed end at
  25.5 ms (28; 22.5). Fits 15.05 / 15.32 / 15.34 mm/√s over 2–10 / 2–20 / 2–25 ms (job 3068 14.36 / 14.44 / 14.15; `B_full` 15.65 /
  15.28 / 15.24): +5 / +6 / +8 %, 0.83–0.85 of the 1D 18.04 (job 3068 0.80). From 2 ms the slope equals `B_full`'s; `B_full`'s lead
  is in the intercept (0.64 against 0.49 mm), built in its first 2 ms. Porous water (Σ ε·α) × job 3068: 1.017 / 1.047 / 1.065 /
  1.076 / 1.089 / 1.099 at 0.5 / 1 / 2–5 / 8 / 10 / 13–30 ms (`B_full` 1.34 at 1 ms, 1.17 at 30 ms): +6.5 % with the inner gaps
  wet and the outer layers dry, ~+10 % once these are wet; flat from 13 to 30 ms while the leak grows 40×.
- **Circulation through the bath plane (water face fluxes `alphaPhi0.wetting` at the writes, cell volumes per ms).** The bath
  feeds the gaps through the outer layers, not straight up: the plane faces under the 182 outer first-row cells carry water up at
  1,280 / 1,470 / 1,410 / 1,580 / 1,780 / 1,100 at 1 / 3 / 5 / 7.5 / 8 / 10 ms (every face upward), and the outer layers pass
  1,400–1,510 of it sideways into the inner box free cells at 5–8 ms, while those 182 cells are the bath surface (mean α 0.39 /
  0.46 / 0.59 at 3 / 5 / 7.5 ms, |U| 0.26–0.29 m/s). The plane faces under the 762 inner first-row free cells carry water net down
  into the bath at 1, 5 and 7.5 ms (−400 / −420 / −200; 445–492 of the 762 faces downward), up from 8 ms (+960 at 8 ms, +4,600–4,900
  at 25–30 ms, the leak's supply). The yarn faces of the plane take 990 at 1 ms, 400 at 3 ms, ≤ 125 from 5 ms: the yarns are fed
  mostly from the gaps. The faces above the two air spots of the inlet row (below) carry water down (19–29 of 30 faces at 5–15 ms).
  A loop bath → outer layers → inner gaps → bath, at ~1,000 cell volumes per ms, through interface cells of a bath that should be
  at rest. Hypothesis, not tested: a parasitic surface-tension current at the bath surface under the outer layers (the corner of
  the free surface, the closed padding floor and the yarn crests), whose down branch also carries the air to the inlet row.
- **Air in the bath.** Layer min α 0.79 at 0.5 ms (158 cells of the top bath row, start transient; net back-flow into the bath
  −1.2e-11 m³ by 0.5 ms, as job 3068, `B_full` none), 0.94 at 1 ms. From 3 ms air collects in the inlet row (the bath bottom) at an x
  mirror pair of spots (x 0.67–0.69 / 1.11–1.13 mm, z 0.06–0.14 mm, below the gaps between y-yarns 1–2 and 2–3): min α 0.70 / 0.50 /
  0.39 / 0.28 / 0.34 at 3 / 5 / 15 / 25 / 30 ms, 17–21 inlet cells at α < 0.5 from 15 ms, whose faces J closes. Origin not checked.
  Hypothesis, not tested: J takes water only (α flux = total flux) through an outflow face, so a bath cell with local outflow keeps
  any air that reaches it until J closes it.
- **Velocity.** Box free |U| at the writes 13.2 / 5.1 m/s at 0.5 / 1 ms (the yarn 6 transient of job 3068, y 0.484 mm, log locator
  12 m/s at 0.31 ms and 8 m/s at 0.81 ms), ≤ 2.2 m/s at 1.5–14 ms, **6–9 m/s at the writes 15–19.5 ms** (log: median 7.3, max 11.9
  m/s at 15–20 ms), ≤ 3 m/s from 21 ms; job 3068 ≤ 0.78 m/s at 15–20 ms. It is the air pump of job 3067 and study 2c: free cell
  (0.609, 2.208, 0.020) mm, α 0.15, p 330–400 Pa, 2 faces on y-yarn 1 at S 0.22–0.45, its pure-air neighbour (0.629, 2.208, 0.020)
  6–9 m/s at −10 to −32 Pa; mirror sites at x 1.21 mm (yarn 3) and 0.91 mm (yarn 2), y 2.13–2.21 mm, around the top of crossing
  yarn 8 (mean S 0.30 → 0.53 over 14.5–20 ms) while the y-yarn front passes. The water in that cell appears at ~14.8 ms, 1.4 mm
  above any connected gap water: its source is not traced, face fluxes not computed. Job 3068, at the same rows and comparable
  yarn S, has no site.

| | Scoring (predictions above) |
|---|---|
| Q1 | Lost ≤ 100 cell volumes by 3 ms: yes (44); padding water ≤ 50 at every write to 3 ms: yes (3–15). Passed, but the leak returns after 8 ms (R1) |
| Q2 | 944/944 first-row cells water from 1 ms: no (762 to 7.5 ms: the outer layers); gap water −30 to +5 % of `B_full` at 1 / 2 ms: no (−70 / −79 %) |
| Q3 | Front at 1 / 2 ms between job 3068 and `B_full`: yes, at the job 3068 value (0.985 / 1.185 mm); porous water 1.0–1.36 × at 2 ms: yes (1.065) |
| Q4 | No stopGuard: yes; dt 1.2–1.3e-7 s after 0.5 ms: mostly (medians 1.14e-7 at 0.5–1 ms, 1.16e-7 at 25–30 ms); free \|U\| ≤ 3 m/s after 1 ms: no (6–9 m/s at 15–19.5 ms); layer min α > 0.9: no (0.28–0.70 from 3 ms, inlet row); no flux through `bathWall`: yes |
| R1 | 30 ms without stopGuard: yes; lost ≤ 200 cell volumes by 30 ms: no (59,426) |
| R2 | 944/944 at every write: no (from 8 ms); gap water 8,000–12,600 from 5 ms: no to 19.5 ms (2,955–7,993), yes from 20 ms (8,283–9,601) |
| R3 | Fit 2–20 ms within 14.44–15.28 mm/√s: no, at the `B_full` value (15.32); porous water 1.00–1.23 / 1.00–1.17 × at 10 / 30 ms: yes (1.089 / 1.098) |

**Reading.** Restricting the bath to the box delays the leak (8 ms instead of from the start) but does not remove it: the two
outermost box layers are open space next to the padding, and once they flood the bath water climbs the bottom face of the fabric
and pours through the open faces, the `B_full` mechanism. Any bath touching the fabric's outer free layers meets it: a dip's outer
meniscus (~1.4 mm high on a flat wall at θ 60°, ~l_c = 2.7 mm wide) does not fit in a 60 µm padding whose open boundary holds no
meniscus. With the inner gaps wet and the outer layers dry (to 7.5 ms) the yarns hold +6.5 % water and the front fit is +5 % (2–10
ms), REV/1D 0.83 against 0.80; but the gaps get that water through a circulation in the outer layers' bath surface cells, not
straight from the bath, so the gain is not clean either. The air pump at 15–20 ms appears at the base pc, where job 3068 was calm after 1.5 ms:
cause not known. To 7.5 ms (outer layers dry) the leak stays ≤ 1.4 % of the inflow; the bath set-up of the tensor K runs is still
open (decision with the user).

## Option 2: bath under the yarn band only (decided with the user 2026-11-05)

**Why.** `Bbox_full` (job 3078, above): the two outermost box layers held a bath surface beside the fabric, flooded at 5–8 ms
and fed the padding, which leaked 80–96 % of the inflow from 23 ms; the bath fed the gaps through a loop up those layers'
bath-surface cells. At the bath plane the 944 free cells of the first row are of two kinds: 307 in the yarn band (z layers
6–12, between the y-yarns: a yarn on each side in x) and 637 in the open space above and below the yarns (layers 3–5 and
13–16: a yarn on one side, the padding and open air on the other). In job 3068 (J at the plane) the open space drained first
(637 → 7 cells water by 0.5 ms), the band later (307 → 47 / 10 at 0.5 / 1 ms). The 2D bench (a slit with walls on both sides)
kept and raised its water at a J inlet. Hypothesis: a bath-fed gap keeps its water where it is confined; the open space beside
the yarns holds no meniscus and, fed by the bath, carries water to the open faces. Set aside in the discussion with the user:
no J with α 1 on the inlet (a drained free inlet cell then vents air, or α fixed at 1 refills it by the spurious kick of the
slit tests, 6×, 23 m/s); closing the lower part of top/bottom (the 60–120 µm free space beside the fabric becomes a slit of
300–600 Pa suction at a 90° wall, as strong as the gaps; a 120° wall is neutral but ±5° gives ±4.7 mm of Jurin height); α
held at 1 in the first band rows (needs code, does not conserve water, imposes the yarn S at the bath); the through-thickness
set-up (no boundary problem, but no in-plane front).

**Design.** As `Bbox`, then mode `band` of `buildCase.sh`: the bath cells kept only under the yarn band of the bath plane (z
between the lowest and highest yarn cell of the first fabric row: −0.0101 to 0.1309 mm, layers 6–12): 3,185 bath cells
(`Bbox` 6,370), inlet 637 faces. The open space beside the yarns and the padding stand on a closed floor at y0 (`bathWall`,
2,093 faces with the z sides of the bath) and start dry (the 3,103 cell volumes of initial water job 3068 had there are
removed); the band keeps job 3068's initial column (1,612 cell volumes). Everything else as `Bbox` (J at the bath bottom, L,
REV values, top/bottom open, outlet closed). `PAD_GRADED="10 1.3"` (`build_mesh.py --pad`): padding of 10 layers from 20 µm
growing ×1.3 (0.86 mm per side, outermost cell 214 µm, 1.7× the cells) instead of 3 × 20 µm; the first padding cell keeps
the box size, so the faces at the box surface stay uniform (G, H, I use 0.5 weights). Cases (`./makeCases.sh Bband_cut
BbandP_cut Bband_full`): `Bband_cut` (y 0.233–1.496 mm, 108,745 cells, 12 ms, 4 cores, writes every 0.25 ms), `BbandP_cut`
(the same with the graded padding, 182,637 cells), `Bband_full` (y 0.233–3.0 mm, 245,245 cells, 30 ms, 16 cores). All
requeued and continued after a crash.

**Checks (laptop scratch builds, installed `4bb5d2e`, whose scalar path is bit-identical to `8a97d02`, 2026-11-05).** All
three build in 30–60 s and pass checkMesh (non-orthogonality 0); patch faces inlet 637, `bathWall` 2,093 (`BbandP_cut`
3,367), top/bottom 5,278 (cut) / 12,103 (full), `inletPad` 0. On the cells at job 3068's cell centres (all 105,560 / 242,060
above the plane; `BbandP_cut` 84,448: the box and the first padding layer): eps, yarnID, fYarn, K identical; α identical on
the yarns and the band, 0 in the open space beside the yarns; the bath all water and all under the band. Smoke tests (30
steps, serial): J and L active, dt at the Coats limit (1.23e-7 s), α in [−4e-19, 1.0006], no flux through `bathWall`,
imbalance ≤ 7e-23 m³; 1.07 / 1.75 / 2.4 s per step (`Bband_cut` / `BbandP_cut` / `Bband_full`).

**References for the band** (free cells above y0 in z layers 6–12; open space = free box cells above y0 outside the band):

| | Band first row water (of 307) | Band gap water at 1 / 3 / 10 ms [cell volumes] | Open space water at 1 / 10 ms |
|---|---|---|---|
| Job 3068 (J at the plane) | 47 / 10 at 0.5 / 1 ms, then 10 | 145 / 52 / 49 | 34 / 33 |
| `Bbox_full` | 307 at every write | 970 / 1,328 / 3,234 | 816 / 3,659 |

**Predictions (written before the runs, 2026-11-05).** The cut ends at 1.496 mm, which the front reaches at ~4.5 ms: yarns
compared to 3 ms only.

| | `Bband_cut` and `BbandP_cut`, 12 ms |
|---|---|
| S1 (the question) | Band first row ≥ 276 of 307 cells water at every write from 0.5 ms; band gap water ≥ 500 cell volumes from 1 ms |
| S2 (leak) | Open space beside the yarns ≤ 300 cell volumes of water at every write; padding water ≤ 20; lost through top/bottom ≤ 50 cell volumes by 12 ms (`Bbox_full` 468 by 10 ms) |
| S3 (feed) | The plane faces under the band's free cells carry water net up at every write from 0.5 ms (`Bbox_full`: its inner faces net down at 1, 5 and 7.5 ms) |
| S4 (yarns) | Front at 1 / 2 / 3 ms between job 3068 and `Bbox_full` (0.985 / 1.185 / 1.306–1.326 mm); porous water at 2–3 ms 1.00–1.065 × job 3068 |
| S5 (stability) | No stopGuard; dt 1.1–1.3e-7 s at the Coats limit after 0.5 ms; free \|U\| at the writes ≤ 3 m/s from 1.5 ms (the yarn 6 transient before, up to 15 m/s in job 3068, accepted); bath min α > 0.9; no flux through `bathWall`; \|imbalance\| ≤ 1e-16 m³ |
| S6 (padding) | `BbandP_cut` against `Bband_cut`: lost through top/bottom not larger; band water, open-space water, front and porous water within 3 % |

**Reading.** S1 and S2 pass in `Bband_cut`: `Bband_full` with the 3-layer padding. S2 fails in `Bband_cut` and passes in
`BbandP_cut`: the padding matters, a full run with the graded padding (spec to add in `makeCases.sh`). S2 fails in both: water
reaches the open space from inside the fabric; rethink before a full run. S1 fails (the band drains although fed): the
confinement hypothesis is wrong; look at the yarn–gap coupling.

| | `Bband_full`, 30 ms (after the cut cases) |
|---|---|
| R1 | No stopGuard; lost through top/bottom ≤ 200 cell volumes by 30 ms |
| R2 | S1 and S2 (open space ≤ 300 cell volumes) at every write |
| R3 | Front fit 2–20 ms between job 3068 and `Bbox_full` (14.44–15.32 mm/√s); porous water at 10 / 30 ms 1.00–1.10 × job 3068 |
| R4 | Free \|U\| ≤ 3 m/s at the writes from 1.5 ms, single-write spikes ≤ 10 m/s; the current of `Bbox_full` at 15–20 ms near crossing yarn 8 (6–9 m/s): recorded, no prediction |

**Solver.** The `Bband` runs use of9-port `4bb5d2e` (change T) on mini03, pulled and built before their submission (decided with
the user 2026-11-05), so that this scalar reference and the coming tensor K runs share one binary. Its scalar-K path is
bit-identical to `8a97d02`, the build of `B_full` and `Bbox_full` (`verification/tensorK`, checks 1 and 2): the comparisons
with those runs are not affected. Previous mini03 binary kept as `hybridPorousInterFoam_8a97d02`. Confirmed 2026-11-05: repo
at `11d060b` (the docs commit on `4bb5d2e`), binary rebuilt 15:28, job 3090 started 15:32, job 3091 after it.

**Commands.** After commit, push and `git pull` on mini03 (both repos; solver rebuilt, above), check the free cores and memory
(`sinfo -o "%n %C"`, `squeue`, `scontrol show node mini03 | grep -E "RealMemory|AllocMem"`, `free -g`; the cut cases ask 6G
and use ~1 GB on 4 ranks, measured on the laptop), then
`cd verification/study2e_bathLayer/Bband_cut && sbatch job.slurm` and the same in `BbandP_cut` (4 cores each). Estimates from
job 3068 (8 cores, ~30k cells per core, 3,440 s per simulated ms): `Bband_cut` ~11 h, `BbandP_cut` ~18 h (~46k cells per core),
`Bband_full` ~20 h on 16 cores (as `Bbox_full`). Fetch into `~/PDM_results/study2e_<case>` with
`rsync -avz --exclude 'processor*' --exclude 'dynamicCode' msinegre@mini03.polito.it:PDM_repo_perso/verification/study2e_bathLayer/<case>/ ~/PDM_results/study2e_<case>/`,
then point all five function-object includes at this study's `tools/`:
`sed -i 's#"\.\./\.\./tools/#"/home/martin_sng/PDM_repo_perso/verification/study2e_bathLayer/tools/#' ~/PDM_results/study2e_<case>/system/controlDict`.
Analysis: `compare3068.py` (band columns: band first row, band gap water, open space), `leakFaces.py`,
`../study2d_gapRise/connected.py`.

### Results `Bband_cut`, job 3090

**Run** (mini03, 4 cores, solver `4bb5d2e`, 2026-11-05 15:32 to 2026-11-06 01:14; copy `~/PDM_results/study2e_Bband_cut`;
analysed 2026-11-06 with `compare3068.py` and two one-off scripts in the session scratchpad: bath cells against the gap cells
above them, plane face fluxes). Reached 12 ms, no stopGuard, ~2,900 s per simulated ms. dt 1.15–1.43e-7 s at the Coats limit
after 0.5 ms; budget closed (imbalance ≤ 8e-20 m³). The cut's closed end (1.486 mm) is reached at 4.5 ms (job 3068: 5.0 ms):
yarn comparisons to 3 ms only.

- **No leak:** lost through top/bottom 3.9 cell volumes by 12 ms (`Bbox_full` 468 by 10 ms; job 3068 ~3); padding water ≤ 2;
  open space beside the yarns 3–46 cell volumes (`Bbox_full` 816 / 3,659 at 1 / 10 ms). No flux through `bathWall`.
- **The band gaps do not stay wet.** The initial band column collapsed within 0.25 ms: through the plane faces under the band
  gaps 800 cell volumes per ms of water and 2,400 of air went down into the bath (air from the open space beside the yarns),
  while the yarn faces of the plane took 2,400 per ms up; net back-flow through the inlet −5.9e-12 m³ by 0.25 ms (job 3068
  −1.9e-11 at 0.5 ms). Band first row (307 free cells) water 20 / 206 / 98 / 71 / 98 / 113 at 0.25 / 0.5 / 1 / 3 / 6 / 12 ms;
  band gap water 152 / 345 / 290 / 296 / 334 / 437 / 498 cell volumes at 0.25 / 0.5 / 1 / 2 / 3 / 10 / 12 ms (job 3068 at 1 /
  3 / 10 ms: 145 / 52 / 49; `Bbox_full` 970 / 1,328 / 3,234). **From 0.5 ms every bath cell under the band gaps is water, and
  194–236 of the 307 first-row gap cells above them are air: the menisci sit on the bath plane faces.** Water reaches the band
  gaps from below (the plane faces under them carry water net up at every write from 0.5 ms: +1,234 / +311 / +180 / +151 cell
  volumes per ms at 0.5 / 1 / 5 / 10 ms, down parts ≤ 155: the `Bbox` loop is gone), and goes on into the yarn flanks. The
  first-row band yarns sit at S 0.96–0.99 (VG pc 0.7–1.4 kPa), above the gap suction 2σcosθ/w = 240–450 Pa.
  Hypothesis, not tested: the yarn flanks drain the gap cells down to the plane; a flat interface lying on a face (water-filled
  bath cell below, air-filled gap cell above) is no interface cell, so neither the VOF curvature nor H's contact angle acts on
  it, and the bath cannot push it back up (the slit tests' "empty gap above the inlet never rises", here with the bath inside the
  mesh). The "band" also includes mostly open layers: at the first row z layers 6 / 7 / 11 / 12 are 87 / 51 / 42 / 59 % free
  (yarn lens tips), layers 8–10 31–35 %; water stays in 4–21 of 28–32 first-row cells even in layers 8–10.
- **Yarns:** front 0.965 / 1.165 / 1.286 mm at 1 / 2 / 3 ms, one row (0.02 mm) behind job 3068; porous water 0.91 / 0.94 /
  0.97 / 0.99 × job 3068 at 0.5 / 1 / 2 / 3–8 ms: job 3068's yarns also absorbed the 3,103 cell volumes of initial water that
  the band case removes from the open space (a design difference, not a coupling effect).
- **Air in the bath:** 26–80 cell volumes from 0.5 ms, mostly interface cells of the top bath row, and 4–17 cells of the inlet
  row (since the 0.25 ms collapse, 185 cell volumes of air reached rows 2–4), where J holds α at its 0.5 closure threshold
  (bath min α 0.500) and α overshoots to 1.047 at 4.5 ms (1.002 at 10 ms) in free inlet-row cells.
- **Velocity:** box free max 15.5 / 14.5 / 9.7 / 6.8 / 4.2 / 2.95 m/s at 0.25–1.5 ms (job 3068: 15.0 at 0.5, 7.0 at 1, 1.6 at 1.5
  ms), ≤ 2.6 m/s from 1.75 ms; sampled log ≤ 3.2 m/s from 2 ms.

| | Scoring |
|---|---|
| S1 | No: band first row 70–206 of 307 from 0.5 ms; band gap water 290–498 cell volumes from 1 ms (≥ 500 predicted), 2–9× job 3068 |
| S2 | Yes: open space ≤ 46, padding ≤ 2, lost 3.9 cell volumes by 12 ms |
| S3 | Yes: net up at every write from 0.5 ms |
| S4 | No: front one row behind job 3068 at 1 / 2 / 3 ms, porous water 0.94–0.99 × (the removed initial water) |
| S5 | Partly: no stopGuard, dt at the Coats limit, \|U\| ≤ 3 m/s from 1.5 ms, no flux through `bathWall`, imbalance ≤ 8e-20 m³; bath min α 0.5, not > 0.9 (air at the inlet row) |
| S6 | Mostly yes (`BbandP_cut`, job 3091, ended 2026-11-06 10:00, ~18 h on 4 cores; copy `~/PDM_results/study2e_BbandP_cut`): front and porous water within 0.1 % of `Bband_cut` at every write, open space 48 against 46, band gap water within 1–3 % to 8 ms and up to +7 % at 9–12 ms (532 against 498); lost through top/bottom 0.01 cell volume by 12 ms against 3.9: the traces of water carried out by air leave only through open faces close to the fabric (supports the job 3063 hypothesis); the graded padding changes nothing near the fabric |

**Reading.** The band bath removes the leak and the loop: the open space beside the yarns gets no bath water and stays nearly
dry, the padding stays dry. It does not keep the gaps at the bath wet: the reading table's last case (S1 fails although fed),
so confinement in x does not hold the gap water; the yarn flanks drain the gaps to the plane, where the menisci stop on the
plane faces.

## Option 3: the bath under everything with a wide padding (decided with the user 2026-11-06)

**Why.** `Bband_cut`: no leak, but with the open space beside the yarns dry the band's gap column collapsed and the menisci
stopped on the bath plane. In `B_full` and `Bbox_full`, where water reached the open space beside the yarns too, the gaps at the
bath stayed wet. In a real dip the bath surrounds the fabric (outer meniscus up the fabric faces, ~1.4 mm on a flat wall at
θ 60°, capillary length 2.7 mm); `B_full` leaked only because its padding is 60 µm: the outer meniscus reached the open faces. A
wide padding lets the outer meniscus form inside the domain, the bath surface being nearly flat where it meets the open faces.
`Bbox` with a wide padding was set aside: it keeps the 20 µm bath strip against a closed floor where the loop formed. Making
top/bottom cyclic (a row of strips, air out at the far end) was set aside by the user: it changes the whole set-up.

**Design (`BfullP_cut`, `./makeCases.sh BfullP_cut`).** `B_full` (5 bath rows under the fabric and the padding, `bathWall` only
at the far z ends of the bath layer) on the cut (y 0.233–1.496 mm), with:
- graded padding `PAD_GRADED="12 1.5"`: 12 layers per side from 20 µm growing ×1.5, 5.19 mm per side, outermost cell 1.74 mm
  (cells stay 20 µm in x and y; the bath surface is flat and horizontal where the cells are long); estimated bath surface at
  the open faces ~0.2 mm above the plane (exponential decay from 1.4 mm over 2.7 mm, not computed);
- the whole bath bottom fed: `inletPad` (the padding part, 2,184 faces) open like the inlet (U, p) and in `waterOnlyPatches`
  (J), so the bath under the padding is fed from below as a deep bath, not sideways through the 0.1 mm layer;
- inlet total pressure p0 = ρ g Δy = 1000 × 9.81 × 0.10026 mm = 0.9836 Pa (makeCases column `p0in`): the solver solves the full
  pressure, gravity as a body force in the face fluxes (`pEqn.H:31`, no `p_rgh`), so the water is at 0 Pa at the bath plane, at
  rest against the air at 0 Pa of the open faces. With 0 Pa at the inlet (all runs so far) the water at the plane is at −1 Pa:
  negligible against the capillary pressures in the gaps, but the only force on a wide flat bath surface, which would sink to
  the inlet;
- 217,854 cells, 12 cores, 12 ms, writes every 0.25 ms; everything else as `B_full` (REV values, J, L, outlet closed, x cyclic).

**Checks (laptop scratch build, installed `4bb5d2e`, 2026-11-06).** checkMesh OK (non-orthogonality 0); patches inlet 1,274,
`inletPad` 2,184, `bathWall` 910, top/bottom 5,278, outlet 3,458. On the 84,448 cells at job 3068's cell centres (the box and
the first padding layer) eps, yarnID and α identical; the bath (17,290 cells) all water; padding above the plane dry. Smoke test
(30 steps, serial): J active on inlet and `inletPad`, L active, dt at the Coats limit (1.24e-7 s), α in [−1.7e-19, 1.00004],
imbalance 1.5e-24 m³; 2.3 s per step, 0.74 GB. After 30 steps (2.7 µs) the far bath and the air are still accelerating (|U| 1e-4
and 1e-3 m/s, far bath top row at 2.2 Pa): the static balance cannot be read from the smoke test, hence F1 below.

**Predictions (written before the run, 2026-11-06).** References: `B_full` (same bath, 60 µm padding) lost 1,644 / 3,550 /
76,800 cell volumes through top/bottom by 0.5 / 2 / 10 ms, band first row 307/307, front 1.005 / 1.286 / 1.466 mm at 1 / 2 / 3
ms; `Bbox_full` band gap water 970 / 1,023 / 1,328 / 3,234 at 1 / 2 / 3 / 10 ms; `Bband_cut` 290 / 296 / 334 / 437; job 3068
front 0.985 / 1.185 / 1.306 mm. The cut's closed end is 1.26 mm above the plane: the outer meniscus may reach it.

| | `BfullP_cut`, 12 ms |
|---|---|
| F1 (leak, far bath) | Lost through top/bottom ≤ 50 cell volumes by 12 ms; the far bath surface (more than 3 mm from the box) stays at the bath plane within one row at every write; net inflow through `inletPad` ≥ 0 from 1 ms (the far bath does not drain out). Fails if ≥ 1,000 cell volumes are lost by 12 ms |
| F2 (gaps) | Band first row ≥ 276 of 307 cells water at every write from 0.5 ms; band gap water ≥ 900 cell volumes from 1 ms |
| F3 (outer meniscus) | Water climbs the fabric's outer faces: the top of the padding water against the box at 12 ms between 0.3 mm above the plane and the cut end (1.26 mm), still rising (not at equilibrium by 12 ms); no prediction of its volume |
| F4 (loop) | The plane faces under the band gaps carry water net up at every write from 0.5 ms |
| F5 (yarns) | Front at 1 / 2 / 3 ms between job 3068 and `B_full`; porous water at 2–3 ms 1.00–1.36 × job 3068 |
| F6 (stability) | No stopGuard; dt 1.1–1.4e-7 s at the Coats limit after 0.5 ms; box free \|U\| at the writes ≤ 3 m/s from 1.5 ms; no J closure at the bath bottom (bottom row min α > 0.9); \|imbalance\| ≤ 1e-16 m³ |

**Reading.** F1 and F2 pass: this is the REV bath (full length next, then the tensor runs; ~1.9× the cells of `Bbox_full`). F1
fails at the far edge: the open faces cannot meet a bath surface even where it is flat; then close the far-edge faces up to a
few rows above the plane (5 mm from the fabric a wall forms no capillary slit with it). F2 fails with the bath around the fabric:
the yarns' suction empties the gaps at the bath whatever the bath (the `Bband_cut` result stands).

**Commands.** After commit, push and `git pull` on mini03: `cd verification/study2e_bathLayer/BfullP_cut && sbatch job.slurm`
(12 cores, 8G; estimate 7–8 h from `Bband_cut`'s ~2,900 s per simulated ms at 27k cells per core, here 18k). Fetch and point the
includes as for the other cases (end of option 2).

### Results `BfullP_cut`, job 1600

**Run** (mini01, 12 cores, solver `4bb5d2e`, 2026-11-06 10:43 to 2026-11-07 00:34, 13.9 h; copy `~/PDM_results/study2e_BfullP_cut`,
fetched and analysed 2026-11-09 with `compare3068.py`, `leakFaces.py`, `../study2d_gapRise/connected.py` and one-off scripts in the
session scratchpad: water level per padding layer from 20 µm × Σα per column, plane face fluxes, band gaps against the padding water,
pressures in the far bath). Reached 12 ms, no stopGuard. ~2,200 s per simulated ms to 4 ms (as mini03), then ~4,300 s per ms
although dt grew to 4.8–6.1e-7 s (yarns saturated, Coats limit relaxed): the second p solve of a step took 0 GAMG iterations to 3 ms
and 220–540 on average from 4–5 ms (max 748), once the far bath had drained (below). Budget: one-time 4.6e-17 m³ in the first
0.25 ms, constant after. Note: the cut end is 1.163 mm above the bath plane (y0 0.333 mm, last row 1.486 mm); the 1.26 mm of F3 is the
height above the inlet.

- **The fabric floods.** Band first row 307/307 at every write; band gap water 3,140 / 3,505 / 3,949 / 10,440 cell volumes at 1 / 2 /
  3 / 7.25 ms (`Bbox_full` 970 / 1,023 / 1,328; `Bband_cut` 290 / 296 / 334); all box free cells (gaps and open space beside the yarns,
  ~37,000) water by 7.25 ms, porous water constant from ~6 ms (17,600 cell volumes, yarn mean S 0.97). Band gaps ≥ 50 % water up to
  0.23 / 0.45 / 0.49 / 0.63 / 0.83 / 1.15 mm above the plane at 1 / 2 / 3 / 4 / 5 / 6 ms, the padding layer next to the box 0.15 / 0.39
  / 0.51 / 0.59 / 0.77 / 0.97 mm: **the gaps rise with the outer water body, 0–0.18 mm ahead of it**; the y-yarn front ahead of both
  (0.67 mm at 1 ms) until the closed end. Whether the gaps lift the outer water or the outer meniscus lifts the gaps: not separable here.
- **The outer meniscus overshoots to the lid.** Water level next to the box (padding layer 1) 0.09 / 0.41 / 0.61 / 0.85 mm above the
  plane at 0.5 / 2 / 4 / 5.25 ms, at the closed outlet (top row) from 7.25 ms over padding layers 1–7 (~0.6 mm out from the box), a
  plateau rather than a decaying meniscus; from ~10 ms it drains back (outflow through `inletPad` under layers 1–8 at 12 ms). Bath
  feed through `inletPad`: 798,800 cell volumes in by 7.25 ms (6.4e-9 m³, ~0.34 mm over the padding area), 378,600 left at 12 ms;
  through `inlet` 44,270 by 8.5 ms, 14,050 at 12 ms. From ~8 ms the full fabric is a conduit: at 10 / 12 ms the plane faces under the
  band gaps carry −1,000 / −5,600 cell volumes per ms of water down, the open space −2,700 / −16,700, while the box water stays at
  ~72,700: padding water enters the fabric sideways and leaves through the bath.
- **The far bath drains and J locks it.** Under the rising meniscus the bath runs at −8 to −42 Pa; the air just above the far bath
  (layers 8–12) is at −0.1 to +0.8 Pa at 0.25–1 ms, mostly positive and falling towards the open faces (displaced air leaving there),
  −5 to +7 Pa at 3 ms (+18 Pa 0.5 mm above the plane next to the box); the bottom bath row of the far layers at 0.90–0.93 Pa at
  0.25 ms against 0.886 Pa hydrostatic for a surface at the plane. The far bath (0.1 mm deep, ~1 Pa hydrostatic margin) flows out
  through `inletPad` (−400 to −700 cell volumes per ms under layers 10–12 from 0.5 ms): under the
  outermost layer (12, 1.745 mm wide) the bath is at −0.087 mm by 4 ms and all its 455 bath cells are air from then on, `inletPad`
  faces there closed (inflow 0, J); layers 10–11 the same by 10–12 ms. Bottom bath row min α 0.49 at 4 ms, 0 from 5.25 ms.
- **Leak and air currents.** Lost through top/bottom 9 / 77 / 879 / 1,597 / 3,491 / 4,633 cell volumes at 3.75 / 5 / 6 / 7 / 10 / 12
  ms (`B_full` 76,800 by 10 ms). At 3.75–4 ms 99.6 % of it leaves within 0.1 mm of the plane through faces of air cells (α < 0.05):
  traces in the outgoing air next to the drained far bath; from 5 ms at all heights up to 1.5 mm, with air crossing each far patch at
  2–4e-6 m³/s in and out (recirculation). Padding air 15–30 m/s from 4.75 ms, in the far layers 10–12 over the drained bath (0.4–0.9
  m/s there to 2 ms); air ρ 1, so ½ρU² ≈ 100–450 Pa against the 1 Pa of the bath layer. Box free |U| ≤ 1.4 m/s from 1.5 ms except
  2.2 / 2.0 / 2.7 m/s at 3.5 / 4.75 / 5 ms.
- **Yarns:** front 1.005 / 1.306 / 1.486 mm at 1 / 2 / 3 ms (job 3068 0.985 / 1.185 / 1.306; `B_full` 1.005 / 1.286 / 1.466), closed
  end at 2.75 ms (job 3068 5.0 ms); porous water 1.39 / 1.41 / 1.35 × job 3068 at 1 / 2 / 3 ms. No front fit (2 points before the end).

| | Scoring |
|---|---|
| F1 | No: lost 4,633 cell volumes by 12 ms (fail ≥ 1,000), from 3.75 ms; the far bath does not stay at the plane (empty under the outermost layer by 4 ms, J-closed); net inflow through `inletPad` negative from 7.25 ms |
| F2 | Yes: band first row 307/307 at every write; band gap water ≥ 3,140 from 1 ms |
| F3 | Partly: the padding water against the box reaches the cut end (1.163 mm) at 7.25 ms and spreads ~0.6 mm out under the closed outlet; not rising at 12 ms (draining back from ~10 ms) |
| F4 | No from 10 ms: net up at every write from 0.5 to 7.5 ms (940–3,300 per ms), net down at 10 and 12 ms (the fabric drains into the bath, not a loop) |
| F5 | No, by a little: front = `B_full` at 1 ms, one row ahead of it at 2 and 3 ms; porous water 1.41 / 1.35 × job 3068 at 2 / 3 ms (1.00–1.36 predicted) |
| F6 | Partly: no stopGuard, box free \|U\| ≤ 3 m/s from 1.5 ms, \|imbalance\| 4.6e-17 m³, dt 1.25e-7 s at the Coats limit to 5 ms (then 4.8–6.1e-7, yarns saturated); bottom bath row min α 0 from 5.25 ms (J closure at the far bath) |

**Reading.** F2 passes: with water around the fabric the gaps at the bath stay wet (third run after `B_full` and `Bbox_full`), and here
the gaps fill the whole cut by 6–7 ms. F1 fails, but not as the reading table expected (open faces meeting a flat bath surface): the
far bath does not stay flat. Hypothesis, not tested: the air displaced by the rising outer water leaves through the far open faces at
small pressures (−5 to +18 Pa), which empties the 0.1 mm far bath (1 Pa of hydrostatic margin) through `inletPad`; J then keeps those
faces closed, air circulates through the open faces over the empty bath (15–30 m/s, stiff p solve) and carries water out. Two
features of the domain make the outer water dynamics dominate: the cut (1.163 mm) is shorter than the static outer meniscus at θ 60°
(~1.4 mm; up to l_c√2 ≈ 3.8 mm on a fully wetting face), so the meniscus reaches the closed outlet over the padding and spreads under
it; and the outer water body (≈ 0.9 million cell volumes at 7.25 ms against ~55,000 in the fabric) rises and falls with inertia.
"Closing the far faces up to a few rows above the plane" (the fallback above) would not remove the drained bath, the lid or the
slosh. Next decision with the user (`NOTES_cases.md`, Next steps).

**Study closed (decided with the user 2026-11-09).** The tensor K runs use the job 3068 set-up with job 3068 as the scalar reference.
Fully wet gaps at the bath (`B_full`) move the y-yarn front by a constant ~0.24 mm from 15 ms (an offset, not a rate), and every bath
that kept the gaps wet leaked or sloshed on this domain. Dry gaps at the waterline stay a known limitation of the set-up (front
offset ≤ 0.24 mm; uptake underestimated at long times); the gaps come back with the horizontal set-up.
