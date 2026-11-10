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

## Analysis (after the runs)
`../study2e_bathLayer/compare3068.py <case>` (per write against job 3068: front, porous and gap water, first row and band,
budget); inlet fluxes per face type (water and air, porous and free faces, φ and `alphaPhi0.wetting` on the inlet patch):
script to write with the results.

## Commands
Build on the cluster: commit, push, `git pull` on mini03, then in each case folder `sbatch job.slurm` (4 cores each, ~3–4 h
estimated from `B_full`'s 2,330 s per simulated ms on 16 cores for 2.3 × the cells). Fetch:
`rsync -avz --exclude 'processor*' --exclude 'dynamicCode' msinegre@mini03.polito.it:PDM_repo_perso/verification/study2g_noJ/<case>/ ~/PDM_results/study2g_<case>/`,
then point the includes at the study 2e tools:
`sed -i 's#"\.\./\.\./\.\./study2e_bathLayer/tools/#"/home/martin_sng/PDM_repo_perso/verification/study2e_bathLayer/tools/#' ~/PDM_results/study2g_<case>/system/controlDict`.
