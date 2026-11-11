# Study 2g: the mid-gap REV bath without change J (2026-11-10)

**Question (user, 2026-11-10).** Every REV run since 2026-10-26 has change J (`waterOnlyPatches (inlet)`) on its bath.
J closes a free bath face while its cell is air-rich (α < 0.5) and never reopens it while the cell stays so: in job 3068
927 of the 944 free bath faces closed within 1 ms and the gaps at the bath stayed dry (study 2e: the closure is the cause,
`B_full`). The inlet α is 1 (`inletOutlet` 1 on every face) with saturated yarn rows at the bath: can air still vent
through it without J, and do the gaps at the bath keep their water if the faces stay open?

**What J does, and what goes without it** (solver `4bb5d2e`: `createPorousMediaFields.H:141`, `updateVariables.H:62`,
`alphaEqn.H:290`, `pEqn.H:71`):
1. yarn faces of the bath: no air mobility (the pressure equation carries the water Darcy flux only). Without it the
   air mobility of the face stays; with α_b 1 on inflow (and the first yarn rows at S 0.99) it is small;
2. α flux = total flux on every face of the bath (all of it booked as water). Without it the α flux is α_b·φ_b: with
   `inletOutlet` α_b = 1 on inflow but **α_b = the cell's α on outflow, so an air-filled gap cell next to the bath
   pushes its air out through the face** (the venting route of the 2026-10-26 failure); with `fixedValue` 1 every
   outflow is booked as water, also from a cell that has none (α < 0 unless the outflow stops);
3. free faces closed while the cell is air-rich. Without it they stay open both ways: a drained cell can take bath
   water back on inflow (α_b 1), but an interface lying on a boundary face has no curvature (no suction draws the bath
   in; slit tests: an empty gap above an `inletOutlet` inlet never rises).
The only REV run without J (2026-10-26, before J existed) failed at 0.21 ms, but with a different inlet: edge bath on
the half crossing yarn 5, coded `pOpenAir` (yarn faces water at −676 Pa), α 0.99 on the yarn faces, dry yarns at the
bath (no saturated rows), no L (`../waterOnlyReservoir/README.md`).

## Cases (`makeCases.sh`, from `../study2e_bathLayer/R0_inlet`)
Job 3068 (`meshing_strat_trial/REV_midbath`: scalar K 1e-11, VG 5000 / 0.5, θ 60°, G + H + F′ + I, L, mid-gap bath
plane y0 = 0.333 mm, saturated rows, 0.1 mm gap column) cut at y 1.496 mm (58 fabric rows, 105,560 cells; inlet 330
porous + 944 free faces), 3 ms, 4 cores, a write every 0.1 ms. Scalar K so that job 3068 is a second reference; J's
role does not depend on K.

| Case | Inlet | One change against |
|---|---|---|
| `R0_J` | J on, α `inletOutlet` 1 | none (= `R0_inlet`; job 3068 cut) |
| `N1_noJ` | J off, α `inletOutlet` 1 | `R0_J`: `waterOnlyPatches` removed |
| `N2_noJfix` | J off, α `fixedValue` 1 | `N1_noJ`: α fixed at 1 on every inlet face |

Built 2026-11-10 on the laptop (installed `4bb5d2e`): checkMesh OK; mesh, eps, K and initial α byte-identical in the three
cases, N2's inlet entry `fixedValue 1`. `run` of N1/N2 stops if the binary reports J active.

## Predictions (written 2026-11-10, before any run of these cases)
Reference values, job 3068 (full length; the cut changes nothing near the bath before ~3 ms): first fabric row 54 / 17 of
944 free cells water (α > 0.5) at 0.5 / 1 ms and 17 to 30 ms; yarn band of that row (z layers 6–12) 47 / 10 of 307; gap water
4,715 → 373 / 179 / 96 / 83 cell volumes at 0.5 / 1 / 2 / 3 ms; y-yarn front 0.865 / 0.985 / 1.185 / 1.306 mm; free |U|
15 / 7 / 1.6 m/s at 0.5 / 1 / 1.5 ms; inlet net outflow in the first 0.5 ms (the column falling back: −1.9e-11 m³), inflow
after.
- **R0_J:** = job 3068 within 1 row in the front and 10 % in the gap water and the first-row counts to 3 ms.
- **N1_noJ, stability:** 3 ms without stopGuard; α ≥ −1e-3 at every write; dt at the Coats limit after 0.5 ms; free |U| ≤ 3 m/s
  at the writes from 1.5 ms. (The 2026-10-26 failure needed dry yarns and α 0.99 at the bath.)
- **N1_noJ, venting:** air leaves through the free bath faces (air flux φ − αφ out of the domain through the inlet > 0) at
  every write from 0.5 ms, while the first-row cells drain.
- **N1_noJ, gaps at the bath:** more first-row water than `R0_J` but most of the drained cells do not refill (no suction
  through a boundary face): first-row water cells at 1, 2, 3 ms between 17 and 300 of 944, band cells between 10 and 150 of
  307. **Above 300 (most of the first row water) = J's closure alone kept the gaps dry**, and an open bath face is enough.
- **N1_noJ, yarns:** y-yarn front within 1 row of `R0_J` to 1 ms, at most +2 rows at 3 ms (the gaps near the bath feed the
  yarn flanks only if they stay wet).
- **N2_noJfix:** fails before 1 ms (stopGuard, or α < −0.01 in a free bath cell): the outflow of the falling column continues
  once the first-row cells empty and is booked as water. If it runs to 3 ms with α ≥ −1e-3, compare its first row with N1.

## Smoke tests, 0.1 ms (laptop, 2026-11-10, after the predictions; copies `~/PDM_results/study2g_smoke_<case>`)
The three cases in parallel on 4 cores each, writes every 20 µs: 785–786 steps each, 1,578 s (2.0 s per step with the three
together), no stopGuard, dt 1.29e-7 s mean after step 100 (identical in the three), α in [−3e-16, 1.0019], budgets closed
(imbalance −4.3e-21 m³ in all three). `inletFluxes.py` (cell volumes per ms, + = into the domain):

| t [µs] | water out, free faces R0_J / N1 / N2 | air through free faces R0_J / N1 / N2 | first-row free cells α > 0.5 (of 944) |
|---|---|---|---|
| 20 | −675 / −675 / −663 | −33 / −33 / −33 | 944 / 944 / 944 |
| 60 | −20,788 / −19,958 / −19,846 | −72 / **−936** / −52 | 944 / 944 / 944 |
| 80 | −20,515 / −24,389 / −21,428 | −28 / **−6,335** / +46 | 762 / 844 / 814 |
| 100 | −17,692 / −21,651 / −10,524 | −5 / **−11,115** / +44 | 580 / 598 / 788 |

- In all three the initial 0.1 mm gap column falls back into the bath through the free faces (~20,000 cell volumes per ms
  from 60 µs; job 3068 also lost water through the inlet in its first 0.5 ms), the yarn faces too (−500 to −1,600 per ms).
- The air through the free faces of `R0_J` (≤ 72 per ms, 0.3 % of the water flux, where J allows none) is the noise floor of
  this measure (φ and αφ written at different stages of the step).
- **`N1_noJ` vents air into the bath from 60 µs**, 11,000 cell volumes per ms at 100 µs (half of its free-face outflow): air
  comes in through the open top/bottom faces and leaves through the bath, the signature of the 2026-10-26 failure, here with
  α ≥ 0 and the time step unaffected so far. The venting prediction holds, ten times earlier than written (0.5 ms).
- **`N2_noJfix` has no venting** (air within the noise, +44 to +46) and keeps more of the first row: 788 cells water at 100 µs
  against 580 (`R0_J`) and 598 (`N1_noJ`), first-row min α 0.26 (`R0_J` 0.08, `N1_noJ` 0); no negative α yet, its outflow
  halves (−10,500 against −21,700 per ms). Its predicted failure (an outflow booked as water from an emptied cell) would come
  once a first-row cell drains to α 0 with an outflow: not reached at 100 µs.
- Cost: 0.1 ms in 26 min on the laptop with the three together; 2–3 ms needs the cluster.

## Runs
Decided with the user after the smoke tests (2026-11-10): `R0_J` and `N2_noJfix` to 3 ms on mini03, **jobs 3111 (`R0_J`) and
3112 (`N2_noJfix`)**, 4 cores each, submitted 2026-11-10 next to another user's 20-core job, both ended 12:49 / 12:52 the same day;
`N1_noJ` not run (its venting is shown by the smoke test and is not a physical bath).

## Results (jobs 3111 and 3112, analysed 2026-11-10; copies `~/PDM_results/study2g_R0_J`, `study2g_N2_noJfix`)
Tools: `../../REV_pipeline/tools/compare3068.py <copy>` (the study 2e copy needs a `bathWall` patch), `inletFluxes.py`,
`../study2d_gapRise/connected.py`, `../study2e_bathLayer/leakFaces.py` (it puts the bath plane 0.1 mm too high for these
cases: its y bins are shifted), `../study2c_nearSaturation/cellFaces.py`; gross bath fluxes and first-row cells per z layer: `bathRegions.py`
(2026-11-10); pictures of the bath region (inlet patch coloured by U_y, slice x = 0.709 mm with U arrows): `viewBath.py` (pvbatch, ParaView's
built-in reader: paraFoam's default reader shows ~0 for the inlet patch values of `pressureInletOutletVelocity`). Both reached 3 ms, no stopGuard, 8,294 / 8,466 s on 4 cores, dt 1.25e-7 s at the Coats limit
from 1 ms, budgets closed (imbalance −2.8e-20 / −5.0e-21 m³).
- **`R0_J` = job 3068:** front identical at every common write (0.865 / 0.985 / 1.085 / 1.185 / 1.226 / 1.306 mm at 0.5 / 1 /
  1.5 / 2 / 2.5 / 3 ms), porous water 0.990–0.996 ×, gap water 369 / 178 / 115 / 94 / 81 cell volumes at 0.5 / 1 / 1.5 / 2 / 3 ms
  (373 / 179 / 117 / 96 / 83), first row 17 of 944 from 1 ms (17), lost through top/bottom 3.1 (3.0).
- **`N2_noJfix`, stability:** α in [−5e-20, 1.0001] at every write; the first-row free cells never empty (min α 0.15–0.31);
  free |U| ≤ 2.6 m/s at the writes from 1.5 ms (`R0_J` ≤ 1.2), 7–10 m/s at 0.3–1 ms (`R0_J` up to 14.7).
- **`N2_noJfix`, gaps at the bath stay wet:** 762 of the 944 first-row free cells water at every write from 0.2 ms, all 307 of
  the yarn band; the 182 others are exactly the first-row cells of the two outermost box layers (z layers 3 and 16, next to the
  padding, mean α 0.23 → 0.37). Gap water 1,604–1,780 cell volumes at 0.4–1.1 ms, 2,100 at 2 ms, 2,715 at 3 ms (`R0_J` 81): band
  1,405, open space beside the yarns 1,310 (50 / 31). Connected water 1,376 → 2,333 cells from 1 to 3 ms, top 0.383 → 0.464 mm
  (plane 0.333 mm); rows ≥ 50 % water only the first two (≤ 0.363 mm), ≥ 20 % up to 0.404 mm at 3 ms.
- **`N2_noJfix`, yarns:** porous water 1.027 / 1.046 / 1.055 / 1.059 × job 3068 at 1 / 1.5 / 2 / 3 ms, front = `R0_J` to 2.4 ms and
  one row (0.02 mm) ahead at 2.5–3 ms, mean yarn S 0.534 against 0.501 at 3 ms. Extra porous water over `R0_J` 185 / 341 / 455 /
  526 / 586 cell volumes at 1 / 1.5 / 2 / 2.5 / 3 ms, still growing at 2.5–3 ms at ~8 % of `R0_J`'s uptake rate over that window
  (a rate effect, or an offset still building up: not decidable at 3 ms). The yarn faces of the bath carry 124 cell
  volumes per ms at 3 ms (`R0_J` 1,304): the yarns near the bath are fed through the wet gaps.
- **`N2_noJfix`, where the bath water enters** (inflow 4.55e-11 m³ by 3 ms, `R0_J` 1.92e-11; 2,200–2,500 cell volumes per ms
  through the free faces from 0.4 ms; gross per region from 1 ms): band 340–420 in and 290–370 out per ms (150 outflow faces,
  cells at α 0.71–0.90 min, 0.84–0.90 median: water circulating through the bath, net about zero); open space 2,100–2,700 in,
  330–490 out (cells at α ≥ 0.52); **of that, the 182 air-rich first-row cells of the outermost layers take 960 (1 ms) → 1,590
  (3 ms) per ms, inflow only** (face velocity up to 0.24 m/s): two thirds of the bath inflow at 3 ms.
- **What drives it** (`cellFaces.py`, 3 ms, cell x 0.709, y 0.343, z 0.201 mm, layer 16): α 0.40, p 195 Pa; air enters from the
  padding cell beside it (z+, p −6 Pa) at 0.57 m/s, **against the pressure difference**, water from the bath at 0.24 m/s; both
  leave upward (0.64 m/s, 76 % air) and towards layer 15 (0.18 m/s, half water); the cell above (y 0.363 mm, α 0.20) passes 0.80
  m/s upward, 86 % air. An air stream from the padding through the outer layers near the bath: the study 2c pump signature at
  an interface lying on bath faces, and the `Bbox_full` loop (water in under the outer layers' bath-surface cells, sideways into
  the inner gaps).
- **Leak:** lost through top/bottom 8 / 14 / 26 cell volumes at 1 / 2 / 3 ms (`R0_J` 2.7 / 2.9 / 3.1), 5 / 9 / 20 per ms: doubling
  every ms, under 1 % of the inflow at 3 ms; all as traces in outgoing air (owner cells α < 0.05) within ~0.13 mm of the bath
  plane; padding ≤ 12 cell volumes, no padding or outer-layer free cell at α > 0.5. Air through top/bottom: out 1.1e-7, in 9.5e-8
  m³/s at 3 ms (the displaced air, 1.9e-8 m³/s, plus a recirculation 5 × larger).
- **Scoring.** `R0_J`: passes. `N2_noJfix`: the predicted failure did not come (3 ms, α ≥ −5e-20, the first-row cells never
  empty): fails as written. Its first row (762 of 944) is above the 300 of the `N1_noJ` reading: **J's face closure alone kept the
  gaps at the bath dry; open faces with α fixed at 1 keep them wet**, without venting and without a bath layer in the mesh.
  `N1_noJ` not run.
- **Reading.** The α `fixedValue` 1 bath works where the bath faces lie under water-filled gap cells, but under the two outermost
  box layers (open space next to the padding, no yarn near the bath) the bath-surface cells stay air-rich and carry a parasitic
  circulation fed by air from the padding: two thirds of the inflow at 3 ms and the source of a leak that doubles every ms. Not
  settled: how much of the yarns' +6 % and of the gap water comes from that circulation rather than from the band gaps (the band
  also circulates ~300 cell volumes per ms in and out through the bath); whether the circulation stays bounded after 3 ms
  (`Bbox_full`'s loop flooded the outer layers at 8 ms). Option, not decided: N2 with the bath faces of the two outermost box
  layers closed (walls as `inletPad`), 10 ms on this cut.
- **Per z layer at 3 ms** (`bathRegions.py`, measured 2026-11-11; cell volumes per ms through the free bath faces): layers 3 / 16
  in 762 / 815, nothing out, first-row cells air-rich; layers 4 / 15 in 397 / 444, nothing out, first-row cells water; layers 5 / 14
  in 33 / 25, out −186 / −193 (69–71 faces); the band (6–12) 338 in, −370 out. The circulation spans the open space beside the
  yarns (in through layers 3–4 and 15–16, back down through 5 and 14), not only the two outermost layers.

## Full-length runs (2026-11-11): `N2_full`, `N2c_full`
Asked by the user: a longer N2 run on the full REV for mini03 (16 cores free), possibly with the bath faces of the outermost box
layers closed (the option above). Both built by `makeCases.sh` (NA 133: y 0.333–3.0 mm, the domain of job 3068; 30 ms, a write
every 0.5 ms, 72 h, LOG_EVERY 100, 16G, continued after a node crash by `job_restart.slurm`: the run settings of study 2e's
`Bbox_full`, whose `job.slurm` and `job_restart.slurm` they copy; 8 cores each, so that the two run side by side on the 16
free cores).
- **`N2_full`** = `N2_noJfix` at full length = job 3068 with J off and α `fixedValue` 1 on the bath (one change against job 3068,
  the scalar reference of the tensor runs).
- **`N2c_full`** = `N2_full` with the bath faces under z layers 3 and 16 closed (`closeZ 3,16` in `makeCases.sh`): `Allpre` moves
  those 182 inlet faces (all free) to a patch `bathWall` (closed: noSlip, fixedFluxPressure, α zeroGradient, the closed entries of
  `0.orig`), then rebuilds `0/alpha.wetting` with the narrowed inlet, so the initial 0.1 mm water column is not set in those two
  layers (no bath under them; `initFields.py` fills only across the inlet's extent). The open space of those layers then stands on
  a closed floor, as the padding does (`inletPad`). Inlet 330 porous + 762 free faces.

**Checks (laptop, 2026-11-11, installed `4bb5d2e`, builds in a scratch copy of the repo tree):** `makeCases.sh` regenerates
`R0_J`, `N1_noJ`, `N2_noJfix` byte-identical. `N2_full`: mesh (points, faces, owner, neighbour, boundary) and 0/ eps, K, fYarn,
yarnID, Uwetting, UnonWetting byte-identical to job 3068's (`~/PDM_results/REV_midbath_run3068`); `0/alpha.wetting` differs only by
the inlet entry (`fixedValue` 1), `0/U` and `0/p` only by the closed-wall regex naming `bathWall` (no such patch there).
`N2c_full`: checkMesh OK; `bathWall` 182 faces, all under free cells of layers 3 and 16; eps, K, fYarn, yarnID, points and
neighbour identical to `N2_full`; α differs in 910 cells exactly (the initial column of layers 3 and 16: 5 rows × 91 × 2, α 1 → 0,
free water 4,715 → 3,805 cell volumes). Smoke tests, 40 steps on 4 cores (stopGuard `maxSteps`, scratch copies only): both J off
(no `waterOnlyPatches` line), L active, dt 1.23e-7 s at the Coats limit (job 3068: 1.22e-7), α in [−2.5e-19, 1.0014], imbalance
≤ 1e-23 m³, flux through `bathWall` 6e-41 m³.

**Predictions (written 2026-11-11, before the runs).** References: job 3068 (J): y-yarn front 0.865 / 0.985 / 1.185 / 1.526 / 1.947 /
2.288 / 2.549 / 2.749 mm at 0.5 / 1 / 2 / 5 / 10 / 15 / 20 / 25 ms, closed end at 28 ms, fit 2–20 ms 14.44 mm/√s; gap water 81–98 cell
volumes from 2 ms; lost through top/bottom 11 by 30 ms. `N2_noJfix` (cut, 3 ms): above. `Bbox_full` (bath layer under the whole
box, outer layers included): the outer layers held their bath surface to 7.5 ms and flooded at 8 ms; lost 44 / 468 / 7,797 / 59,426
cell volumes at 3 / 10 / 20 / 30 ms; porous water 1.065 × job 3068 at 2–5 ms, 1.099 from 13 ms; fit 15.32 mm/√s; closed end 25.5 ms.
- **Both:** 30 ms without stopGuard; α ≥ −1e-3 at every write; dt 1.2–1.3e-7 s at the Coats limit.
- **`N2_full`:** to 3 ms = `N2_noJfix` (front within one row, porous water within 1 %, 762 of 944 first-row cells water). The
  outer layers flood as in `Bbox_full`: lost through top/bottom ≥ 1,000 cell volumes by 20 ms, padding water > 100 cell volumes
  from 10–15 ms. Porous water 1.06–1.12 × job 3068 from 3 ms, fit 2–20 ms 14.5–15.5 mm/√s, closed end at 25–28 ms.
- **`N2c_full`, at the bath:** ≥ 700 of the 762 first-row cells above the inlet water at every write from 0.5 ms (all 307 of the
  band). Then one of two outcomes, decided by 3 ms:
  - (a) **the circulation moves one layer in** (expected: layers 4 and 15 are open space too, inflow-only in the cut, and once
    layers 3 and 16 are dry on a closed floor they border air as layers 3 and 16 bordered the padding): ≥ 50 of the 182 first-row
    cells of layers 4 and 15 at α < 0.5 at 3 ms, layers 4 + 15 ≥ 50 % of the bath inflow, lost through top/bottom growing as in
    `N2_noJfix` (≥ 15 cell volumes by 3 ms);
  - (b) **it stops**: layers 4 and 15 first-row cells water at every write, inflow per layer within 2 × the band's mean, lost
    through top/bottom ≤ 10 cell volumes by 3 ms and ≤ 300 by 30 ms.
- **`N2c_full`, yarns:** porous water 1.03–1.08 × job 3068 from 3 ms (between job 3068 and `N2_noJfix`'s 1.059: less gap feed
  beside the closed layers), fit 2–20 ms 14.4–15.2 mm/√s, closed end at 26–28 ms.
- **Reading.** (b) with ≤ 300 cell volumes lost by 30 ms: `N2c` is a bath set-up with wet gaps at the waterline and no leak, a
  candidate for the next REV runs; against job 3068 it measures what the bath-fed gaps add to the yarns. (a): closing layers 3 and
  16 only moves the loop one layer in, and closing more is no way out (user, 2026-11-11): the bath under the band only was
  `Bband_cut` (study 2e, job 3090), where the band gaps drained to the plane and never refilled to 12 ms. J did not do it there: it
  sat at the bottom of the 5-row bath layer, and the plane faces under the band were internal faces, open both ways. With the
  open space beside the band dry, its air went down through the plane into the bath with the collapsing column (2,400 cell volumes
  per ms to 0.25 ms), then the menisci sat on the plane faces although the bath pushed water up into the band at every write. The
  N2 boundary passes no air (outflow booked as water), so `Bband_cut` does not strictly settle an N2 band bath, but the dry open
  space beside the band would be back: in every run where the band stayed wet (`B_full`, `Bbox_full`, `BfullP_cut`, `N2_noJfix`)
  the open space beside it held bath-fed water, and in job 3068 (J at the plane) the open space drained first (637 → 7 first-row
  cells by 0.5 ms), the band after it. `N2c_full` keeps bath-fed open space on both sides of the band (layers 4–5 and 13–15; two
  layers below the band only). In case (a) it is `N2_full` with the loop one layer in, and the question left is the one `N2_full`
  answers with one change against job 3068: does the loop stay bounded, or flood the outer layers and then the padding as in
  `Bbox_full` (8 ms, padding from ~17 ms)? Hence `N2_full` is the cleaner long run; `N2c_full` adds information only through (b).
  Both side by side on 8 cores each (~29 h) answer both questions at once.
- **Runs (decided with the user 2026-11-11): both, side by side on mini03, 8 cores each.** The smoke tests above ran on 4
  cores; the 8-core decomposition was not rerun locally (job 3068 ran this mesh on 8 cores; `N2c_full` only adds the
  `bathWall` patch). Job numbers: to add at the submission.

## Commands
Build on the cluster: commit, push, `git pull` on mini03, then in each case folder `sbatch job.slurm` (4 cores each, ~3–4 h
estimated from `B_full`'s 2,330 s per simulated ms on 16 cores for 2.3 × the cells). Fetch:
`rsync -avz --exclude 'processor*' --exclude 'dynamicCode' msinegre@mini03.polito.it:PDM_repo_perso/verification/study2g_noJ/<case>/ ~/PDM_results/study2g_<case>/`,
then point the includes at the study 2e tools:
`sed -i 's#"\.\./\.\./\.\./study2e_bathLayer/tools/#"/home/martin_sng/PDM_repo_perso/verification/study2e_bathLayer/tools/#' ~/PDM_results/study2g_<case>/system/controlDict`.

Full-length runs (`N2_full`, `N2c_full`): commit, push, `git pull` on mini03, then `sbatch job.slurm` in each of the two case
folders (8 cores each; ~29 h at job 3068's 3,440 s per simulated ms on 8 cores, up to ~42 h on a loaded node: the tensor runs
cost 45 % more per step; ~60 writes of ~50 MB per case, twice with `processor*/`; 16G each, as job 3068). A resubmitted
`job.slurm` on a run in progress continues it (`job_restart.slurm`); `./clean` first for a fresh start.
Early check (outcome (a) or (b) of `N2c_full` by 3 ms, ~3 h into the run; `N2_full` against `N2_noJfix` at the same writes): on mini03 `tail -3 waterBudget.csv` (`in_top`,
`in_bottom`: cumulative m³, negative = out; one box cell 8.07e-15 m³); per layer: fetch the case with its processor folders
(the rsync above without `--exclude 'processor*'`), then on the laptop `reconstructPar -time 0.0005:0.003`,
`postProcess -func writeCellCentres -time 0` and `.venv/bin/python -I bathRegions.py <copy> 0.001 0.002 0.003` (its "outermost
layers" are those of the inlet's free faces: 4 and 15 in `N2c_full`). Compare with job 3068: `../../REV_pipeline/tools/compare3068.py <copy> ~/PDM_results/REV_midbath_run3068`.
