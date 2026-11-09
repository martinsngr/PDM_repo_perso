# Study 2f: air at the yarn surface in the horizontal set-up (scratch solver changes)

Started 2026-11-09 by Claude while the user was away (user's brief: explore solver changes on scratch copies that make
`REV_pipeline/cases/horizontal` work **without** putting part of the fabric under the bath line; minor set-up changes
allowed; nothing to the solver repo; up to 8 laptop cores). Success as agreed: the full-REV horizontal case stable for
≥ 0.5 ms (no stopGuard, no air piling up in the bath, gaps fed from below, fabric free |U| ≤ 3 m/s after the start), plus
keyword-off regressions bit-identical and the 2D bench unchanged. **Rule (user): physics first. Every change states the
physical condition it represents; no limiter, clip or damper whose only purpose is to make the run survive. A change that
only suppresses a symptom is rejected and recorded as such.**

## Background
`REV_pipeline/README.md`, "Horizontal: smoke test failed": the dry fabric lying on 5 bath rows (J at the bath bottom, x and
y cyclic, g −z, θ 40°, REV values) stops at 31 µs. Flux analysis: (1) the dry yarn crests vent their air down into the bath
water through the 747 crest faces (yarn/gap Darcy faces carry air with the yarn's air mobility into a water-filled free cell:
nothing stands for the bubble entry pressure), the bath cells under the crests turn to air, then a partly filled one runs away
(study 2c pump); (2) with pre-wetted crests the yarns vent normally into the air-filled gaps, and part of that air goes down
into the bath through its flat surface (34–100 cell volumes per µs).

## Set-up of the runs
Scratch copies (session scratchpad, `study2f/`): the horizontal case as built by `REV_pipeline/cases/horizontal/Allpre`
(290,472 cells), 4 cores, writes every 20 steps, `dsLocator` (study 2e tools) for the per-step fastest cell, `maxSteps` as
stated per run. Solver: scratch copies of of9-port `11d060b` (= installed `4bb5d2e` code) built under other names
(`hybridPorousInterFoam_M`, `_M1`, ...); the installed binary and the solver repo are not touched. Patches in `solver/`.

## R0: the scratch build is the installed solver
`hybridPorousInterFoam_M` (unchanged sources) on the failing case, 300 steps: α, p, U, φ byte-identical to the installed
binary's run at all 15 writes, deltaT identical at every step. **Pass.** Every difference below comes from the change tested.

## M1: air through the yarn surface only where the free side is air (`porousFreeAirFraction`)
**Physical statement.** Air passes between the pore space of a yarn and a free cell only through the part of the free cell
that is air. A yarn's air does not enter the water of a gap or bath cell (that takes the bubble entry pressure 2σ/r_pore,
~30 kPa for 5 µm pores, against kPa pressure differences here), and a water-filled free cell has no air to give.
**In the model:** the air relative permeability of a porous/free Darcy face (`kr2f`, after L) is multiplied by 1 − α of the
face's free cell, the VOF air fraction of that cell, on internal and processor faces (`solver/M1_porousFreeAirFraction.patch`,
`updateVariables.H` after change L; keyword in `createPorousMediaFields.H`, off by default). No threshold: a face next to an air
gap keeps the yarn's air mobility (L's), a face next to a full water cell carries water only. The water side is unchanged.
**Predictions (written before R1, 2026-11-09)**, the failing case with `porousFreeAirFraction on`, 300 steps (then continued if
it survives):
- P1 the air flux from yarns into free cells at α > 0.5 drops to ≤ 3 cell volumes per µs at every write (dry start: 15–27 per µs
  in the first µs, the start of the cascade);
- P2 the bath cells under the crests stay water (≥ 700 of 747 at α > 0.5 at 30 µs; dry start: 0);
- P3 the crests keep taking water from the bath (water up through the crest faces ≥ 10 per µs at 30 µs; dry start: ~0 from 8 µs);
- P4 no runaway by step 300: fastest free cell ≤ 5 m/s from step 100 (dry start: 6 m/s at step 160 growing to 9e4);
- P5 the second route is not touched: air still enters the bath through its flat surface under the gaps, 10–60 per µs, bath air
  300–1,500 cell volumes at 30 µs. If so, M1 is necessary but not sufficient (expected).
Regression: `_M1` with the keyword off on R0's case, byte-identical to R0.

## Runs (2026-11-09)
- **R0off (`_M1`, keyword off, R0's case): byte-identical to R0** (deltaT at all 41 steps run, α, p, U, φ of the writes at steps
  20 and 40 on all four processors); stopped at step 41 to free the cores (keyword-off regression on the REV: pass).
- **R0 analysed with `analyse.py`** (the failing reference): air out of yarns into water-filled free cells 15–27 cell volumes
  per µs in the first µs, then into the now air-rich bath cells under the crests (52–110 per µs); air down into the bath through
  the crest faces 18–41 per µs and through the faces under gaps 5–25 per µs; **all of the latter from free cells connected to
  the open top through air** (none trapped): not an air pocket pushed down by trapped air. Its size (~750 cell volumes over
  12,103 surface faces in 30 µs, ~1.2 µm of mean surface drop, ~0.01 Pa) is compatible with a slight sag of the bath surface
  while the fabric draws water; the concentration of air under the crests is the problem, not the mean.
- **Start transient (R0 and R1 alike):** in the first ~20 steps bath-surface cells next to the crests drop to α ≈ 0.5 with free
  velocities up to 31–43 m/s: the dry crest cells (S 0.002, Van Genuchten pc 2.5 MPa) touch bath water across one face. The
  vertical cases never show it (the yarns at the bath start wet, with the 0.2 mm ramp).
- **2D bench, M1 on (`porousFreeAirFraction on`): unchanged.** All 10 checks pass; meniscus and wall front identical at 1 and
  2 ms (0.430 / 0.790 mm, 0.750 / 1.150 mm), meniscus +1 row at 0.25 / 0.5 / 1.5 ms, wall water 366 against 369 cell volumes
  at 2 ms (−0.8 %), max |U| 1.16 against 1.20 m/s. **M1 keyword off on the bench: byte-identical** (160 files over 40 writes,
  deltaT at all 8,490 steps).
- **R1 (M1 on, dry start): fails as R0, ~25 steps later.** Fastest free cell 4.3 / 5.2 / 8.3 / 18.4 m/s at steps 100 / 150 /
  200 / 250, 654 m/s at 300, in a bath-surface cell next to a crest at α 0.16–0.27 (R0: 9.7 m/s at 200, 40 at 250). Bath cells
  under the crests still water: 747 / 225 / 44 / 0 at 0 / 1.1 / 2.6 / 5 µs (R0: 747 / 225 / 91 / 0). P1 fails as measured
  (air into water-filled cells 15–20 per µs in the first 0.3 µs, but see below), P2 fails, P3 fails, P4 fails (runaway), P5 holds
  (air through the faces under the gaps 5–21 per µs, all from air connected to the open top). **Reading:** the first leak is
  not what seeds the runaway. In the first steps a dry crest cell (S 0.002, Van Genuchten pc 2.5 MPa) drives a water Darcy flux
  `phiWetting` of order m/s across its face with a bath cell (harmonic K, pc jump of 2.5 MPa over one cell): the bath next to
  the crests is emptied faster than it refills, the flat bath surface beside them is pulled down and air enters from above
  (the start transient, 31–43 m/s); M1 cannot act on that air (it comes through the bath surface, not out of the yarn). The
  φ − αφ air diagnostic mixes time levels in such fast transients (αφ = `phiWetting` of the α step, φ of the following pressure
  step), which explains P1's nonzero values. M1 stays physically right and harmless (bench, bit-identity) but is not sufficient.
- **Physical reading of the seed:** 2.5 MPa is the Van Genuchten curve diverging at S → 0, not the suction of a fibre bundle,
  which its pore size bounds to tens of kPa (fibre-bundle estimate ≈ 19 kPa·cosθ, `NOTES_cases.md`). The vertical cases never
  meet it: their yarns touch the bath through a wet ramp (`initFields.py`: "a sharp S_IN → S_DRY jump at the inlet crashes the
  solver within microseconds").

## R2, R2b: a wet contact zone, as the vertical cases at their bath (predictions written before the runs, 2026-11-09)
Set-up change (allowed by the user: minor, the waterline stays at the fabric's underside): the yarn cells of the bottom four
fabric layers start on a ramp, S 0.84 / 0.64 / 0.35 / 0.15 in z layers 5 / 6 / 7 / 8 (`initFields.py --free-fill 1e-4
--sat-height 1e-4 --ramp 8e-5`), the rest of the yarns at 0.002, gaps air, bath as before. Physical statement: the first
instants of contact between dry fibres and water (pore-scale wetting, microseconds) are not resolved; the model starts after
them, with the yarn wetted near the contact, as at the bath of every vertical case (there over 0.3 mm). R2 = ramp + M1; R2b =
ramp without M1 (isolates M1's role). Built: 14,540 yarn cells on the ramp (747 / 2,789 / 4,667 / 6,337 in layers 5–8); initial
yarn water 2,564 cell volumes against 79 for the dry start: +2,485, **6.3 % of the yarn capacity (≈ 4 g/m²)**, the price of this
start, to subtract from the uptake.
- Q1 (both) no start transient: fastest free cell ≤ 3 m/s from step 20 (R0, R1: 31–43 m/s at step ~20).
- Q2 (R2) bath cells under the crests stay water: ≥ 700 of 747 at α > 0.5 at every write to 300 steps; bath air within +100
  cell volumes of its start value (R1: +1,300).
- Q3 (R2) no runaway: fastest free cell ≤ 3 m/s from step 50 to 300.
- Q4 (R2) the bath feeds the gaps: water up through the faces under the gaps > 0 at every write, free box water increasing.
- Q5 (R2b) without M1, once bath water rises around the wetted yarn bottoms the yarns vent air into it: bath air grows faster
  than in R2; worse than R2 on Q2/Q3. If R2b = R2, M1 is not needed with a wet contact zone.
- **R2 (contact ramp + M1) and R2b (contact ramp only), 300 steps (38.6 / 34.8 µs): calm.** Fastest free cell 0.33–0.39 m/s at
  step 25 (R0/R1: 31–43), ≤ 2.07 m/s throughout and decaying to 1.8, in first-layer cells beside the crests slowly filling (α 0.01
  → 0.16: bath water rising into the open space under the fabric); dt 1.1–1.5e-7 s at the Coats limit. Bath cells under the
  crests: 747 of 747 water at every write in both. Water up through the crests 25–38 (R2) / 16–33 (R2b) per µs. Air from yarns
  into water-filled cells: R2 0–1.3 per µs; R2b 34 → 0 per µs over the first 14 µs (the wetted crests vent into the bath until
  they fill), then the two converge (bath air 854 / 899 cell volumes at 35 µs). Q1 pass, Q2 crest part pass, Q3 pass, Q4 pass;
  Q2 bath-air part fails (R2 +917, predicted ≤ +100); Q5: M1 helps only in the first ~14 µs once the contact zone is wet.
  **The contact ramp removed the failure; M1 is a small, physical correction on top.**
- **The remaining bath air (R2) is the bath level dropping, not a phase swap.** Water budget at 38.6 µs: fabric +3,161 cell
  volumes, inlet +2,238, bath −923 (imbalance −3e-20 m³); the deficit, ~26 per µs from 12 µs on, is replaced by air from above
  (the "second route"), as a sag of the bath surface under the open space (4,260 top-row cells at α 0.72–0.9, none within 2 cells
  of a crest; bath rows 0–2 untouched). Physical reading (estimate, not proven): the bath is a 0.1 mm layer fed at fixed pressure
  from below; its only refill drive is hydrostatic, ρgΔh ≈ 0.01 Pa per µm of surface drop, against the inertia of the layer
  (ρh du/dt) to reach the fabric's uptake rate, ~1.4e-4 m/s per unit area; the flat surface between the crests, at the air
  pressure, cannot pass the fabric's suction down to the inlet. With the measured deficit the inflow should catch up within
  ~0.1–0.3 ms after a total sag of a few µm (≈ 0.3 cell). In a real dip the same sag is spread over a bath far larger than the
  fabric (negligible); in the periodic REV the bath area equals the fabric's. M2 (M1 + G2b, built as `hybridPorousInterFoam_M2`)
  is not needed: no pump appeared.

## R3: the long run, contact ramp + M1, to 0.5 ms (predictions written before the run, 2026-11-09)
R2's case and binary, `maxSteps` off, endTime 0.5 ms, writes every 50 µs, 4 cores alone (~2–3 h, estimate).
- S1 stability: no stopGuard to 0.5 ms; fastest free cell ≤ 3 m/s at every write and in the per-step locator after 50 µs;
  dt 1–1.6e-7 s at the Coats limit.
- S2 bath: the bath air levels off: its growth rate falls below 5 cell volumes per µs by 0.3 ms and the total stays ≤ 3,000 cell
  volumes (mean sag ≤ 0.25 cell); bath cells under the crests stay water (≥ 700 of 747) at every write. Fails if the bath air
  keeps growing at ≥ 20 per µs to 0.5 ms (the bath would drain: then the fixed-pressure layer is not a usable bath).
- S3 gaps fed: free box water grows at every write; water up through the faces under the gaps > 0.
- S4 yarns: mean porous S rises at every write; uptake (water above the bath) by 0.5 ms between 20 and 60 g/m² (yarns full 65,
  all full 217; 1D estimate for 0.28 mm through-thickness at 18 mm/√s: the yarns cross it in ~0.25 ms, then fill sideways).

## V: does M1 change the vertical REV? (predictions written before the runs, 2026-11-09)
`R0_inlet` of study 2e (job 3068 cut at 58 rows, 105,560 cells, mid-gap bath with J, REV values, θ 60°, L), built in the
scratchpad by `../study2e_bathLayer/buildCase.sh . 0 58`, 0.2 ms (the phase in which the gap column at the bath drains into the
yarns), writes every 50 µs, 4 cores: `V_M1on` (`_M1`, keyword on) and `V_M1off` (`_M`, unchanged build). Expected small: at the
bath the gap water sits next to yarn rows at S 0.99 (air mobility ~0 anyway), above the column the gap cells are air (weight 1).
M1 can act only where the top of the gap column meets ramp yarn cells (S 0.94 → 0.05).
- V1 y-yarn front within one row (20 µm) at every write; porous water within 2 %.
- V2 gap water within 15 % at every write; fastest free cell within 30 % (no new current).
A larger difference would mean M1 changes the vertical results already obtained: it would then need its own decision before
being used anywhere.
**Result V (2026-11-09):** `V_M1on` against `V_M1off` at 0.05 / 0.10 / 0.15 / 0.20 ms: y-yarn front identical at every write
(0.311 / 0.351 / 0.391 / 0.411 mm above the bath); yarn water ratio 0.9993 / 0.9990 / 0.9990 / 0.9991; gap water ratio 1.001 /
1.002 / 1.004 / 1.005 (the column drains 4,183 → 1,341 cell volumes in both); fastest free cell 1.97 / 2.19 / 1.98 / 1.72 against
1.97 / 2.20 / 1.98 / 1.74 m/s. **V1 and V2 pass: M1 does not change the vertical REV** (in the phase in which the gap water at
the bath meets the yarns).

### Result R3 (2026-11-09): the horizontal case runs to 0.5 ms
3,778 steps, 7,779 s on 4 cores, no stopGuard, dt 1.2e-7 s at the Coats limit (1.2e-8 at the first step), imbalance ≤ 7e-20 m³.
| t [µs] | uptake above the bath [g/m²] (yarns / gaps) | yarn mean S | fabric free cells water | bath air [cell vol] | fastest free cell [m/s] |
|---|---|---|---|---|---|
| 50 | 7.3 (4.9 / 2.4) | 0.14 | 2 % | 1,196 | 2.06 |
| 100 | 17.4 (11.8 / 5.6) | 0.25 | 4 % | 2,196 | 2.78 |
| 150 | 28.7 (19.0 / 9.8) | 0.36 | 7 % | 2,405 | 3.75 |
| 200 | 42.6 (26.7 / 15.9) | 0.47 | 11 % | 2,384 | 3.34 |
| 250 | 58.1 (34.5 / 23.6) | 0.59 | 16 % | 1,882 | 2.79 |
| 300 | 74.3 (42.2 / 32.1) | 0.71 | 21 % | 575 | 4.90 |
| 350 | 92.6 (48.3 / 44.3) | 0.81 | 29 % | 25 | 5.06 |
| 400 | 110.7 (52.3 / 58.3) | 0.87 | 39 % | 27 | 5.01 |
| 450 | 125.4 (54.4 / 71.0) | 0.90 | 47 % | 32 | 3.73 |
| 500 | 136.8 (54.9 / 81.9) | 0.91 | 54 % | 39 | 2.82 |
(Uptake: water above the bath surface minus the initial contact ramp; yarns full 65 g/m², all free fabric cells full 152.)
- At 0.5 ms: yarns S 0.90–0.91 in every layer; gaps full in layers 5–8, 68–90 % water in 9–13, 10 % in 14, dry in 15–18 (the open
  surface region above the yarn crests, as S9 with closed yarns); no water in the air layers above, 0.7 cell volume out through
  the top. Bath cells under the crests water at every write (747 of 747).
- The bath sag of R2 was transient: bath air peaked at 2,405 cell volumes at 150 µs (mean 0.2 cell), the inflow then caught up
  and the bath refilled (air leaving upward through the surface, 21–24 per µs at 250–300 µs), 25–39 from 350 µs.
- The fast air (3.7–5.6 m/s, up to 3,124 fabric free cells above 3 m/s at 350 µs, ~20,000 above 1 m/s) is the air displaced by the
  uptake: pure air cells without yarn faces, through-flow (in = out per cell), no net horizontal flow (mean Ux, Uy 0, horizontal
  air fluxes ~1e-12 m³/s), a net upward mean of 0.22–0.65 m/s, and the air leaving through the top equals the water entering
  through the bath at every write (ratio 0.999–1.000; 0.93 / 1.47 / 1.85 / 1.85 / 1.62 / 0.96e-6 m³/s at 100 / 200 / 300 / 350 /
  400 / 500 µs = 0.19–0.38 m/s per unit fabric area), squeezed through the narrowest layers at mid-thickness (21–27 % free, partly
  water). It falls with the uptake rate.
- Scoring: S1 partly (no stopGuard, dt at the Coats limit; fastest free cell above 3 m/s at 150–200 and 300–450 µs, see above:
  physical venting, not a current); S2 pass (peak 2,405 ≤ 3,000, back to ~30; crest cells water); S3 pass (gap water grows at every
  write, filling bottom-up); S4 fails high (136.8 g/m², predicted 20–60: the gaps fill along with the yarns, 82 g/m², which the
  prediction left out; the yarn part, 54.9, is inside it).
- Against the success criterion agreed with the user: ≥ 0.5 ms, no stopGuard: yes; no air piling up in the bath: yes (transient,
  refilled); gaps fed from below: yes; fabric free |U| ≤ 3 m/s after the start: **no as written** (3.7–5.6 m/s, explained above as
  the displaced air; the criterion came from the vertical runs, where the uptake per unit area is far smaller); keyword-off
  regressions bit-identical: yes (REV, bench); 2D bench unchanged: yes.

## R3b: the contact ramp alone, unchanged solver, to 0.5 ms (predictions written before the run, 2026-11-09)
R3's case with the unchanged build (`hybridPorousInterFoam_M`, no M1). Question: is M1 needed at all once the contact zone starts
wet (R2b: calm to 35 µs, M1 acting only in the first 14 µs)?
- T1 reaches 0.5 ms without stopGuard.
- T2 bath cells under the crests stay water (≥ 700 of 747 at every write); bath air peaks ≤ 3,000 and returns below 200 by 0.5 ms.
- T3 uptake within 5 % of R3 at every write from 100 µs.
- T4 the same venting humps (fastest free cell 3–6 m/s at 150–450 µs, no runaway).
If T1–T3 hold, the horizontal case needs no solver change: the contact ramp alone (a set-up choice) is enough, and M1 is an
optional physical refinement.

### Result R3b (2026-11-09): the contact ramp alone is enough
Unchanged solver (`_M` = installed), 3,865 steps, no stopGuard, imbalance −2.8e-20 m³, 1.0 cell volume out through the top.
Against R3 (ramp + M1) at 50 / 100 / 200 / 300 / 400 / 500 µs: uptake 6.9 / 16.9 / 42.0 / 73.5 / 109.8 / 135.9 g/m² (ratio 0.944 /
0.968 / 0.987 / 0.990 / 0.992 / 0.993); yarn mean S within 0.012; fabric free cells water within 0.004; bath air peak 2,358
(R3 2,405) at 150 µs, then 595 / 82 / 87 / 100 / 122 at 300–500 µs (R3 575 / 25 / 27 / 32 / 39); bath cells under the crests 747 of
747 at every write; fastest fabric free cell 2.08 / 2.81 / 3.27 / 4.77 / 5.08 / 2.80 m/s (R3 within 3 %). T1 pass, T2 pass (peak
≤ 3,000, 122 at 0.5 ms), T3 pass (3.2 % at 100 µs, ≤ 1.3 % from 150 µs), T4 pass.

## Conclusions (2026-11-09)
1. **The horizontal case (dry fabric on a bath at rest, waterline at the fabric's underside) runs without any solver change**
   once the yarn cells in contact with the bath start wet: a ramp over the bottom four fabric layers (S 0.84 / 0.64 / 0.35 / 0.15,
   `initFields.py --free-fill 1e-4 --sat-height 1e-4 --ramp 8e-5`), +6.3 % of the yarn capacity (≈ 4 g/m²) at the start. It is the
   same treatment as the bath of every vertical case, and stands for the unresolved first instants of contact.
2. **Why the dry start fails:** a dry yarn cell (S 0.002) in direct contact with bath water gets the Van Genuchten dry-end
   capillary pressure (2.5 MPa, the curve's divergence, far above the suction a fibre bundle's pores allow, ~tens of kPa); across
   one cell this drives a water flux of order m/s out of the bath next to the crests, tears the flat bath surface there, lets air
   in from above, and a partly filled bath cell beside a crest becomes the study 2c pump. The same applies to any first contact
   between dry yarn and free water (a droplet on a dry fabric, gaps meeting dry yarn): a measured yarn pc curve with a bounded
   dry end, or a wet contact zone, is needed there.
3. **M1** (`porousFreeAirFraction`, air mobility of yarn/gap faces × the free cell's air fraction): physically right (no air out of
   a yarn into water), byte-identical when off, bench and vertical cut REV unchanged when on, but neither sufficient (R1) nor
   necessary (R3b) for this case; its only effect here is less yarn air left in the bath (39 against 122 cell volumes at 0.5 ms).
   An optional refinement, not proposed for the solver now. M2 (M1 + G2b) built, not needed.
4. **What the 0.5 ms runs show:** uptake 136–137 g/m² at 0.5 ms (yarns ~55, gaps ~82), yarns S 0.91 uniform through the
   thickness, gaps filling bottom-up (52–54 % of the fabric's free cells water, the open surface layers dry), a transient sag of the
   thin fixed-pressure bath (refilled by 350 µs), air leaving through the top at the rate water enters (0.19–0.38 m/s per unit
   area), squeezed through the narrow mid-thickness passages at 3–5 m/s. The ≤ 3 m/s velocity criterion fails as written for that
   physical reason.
5. **Not tested:** the length of the contact ramp (2 or 6 layers instead of 4), times beyond 0.5 ms (the end state of the gaps),
   the tensor K, the 15 µm mesh; no comparison with a measurement (through-thickness absorption, MMT).

**Kept results:** R3b (contact ramp, unchanged solver, 0.5 ms) in `~/PDM_results/study2f_R3b_ramp` (578 MB: 10 writes, mesh, full
solver log with the `dsLocator` lines, `waterBudget.csv`; its function-object includes point to `REV_pipeline/tools` and
`study2e_bathLayer/tools`, so paraFoam opens it; `study2f_R3b_ramp.foam`). The other runs (R0, R1, R2, R2b, R3, V, benches)
stayed in the session scratchpad and are gone with it; their numbers are above. Scratch binaries `_M/_M1/_M2` deleted
(2026-11-09, user). Adopted: the contact ramp in `REV_pipeline/cases/horizontal` (user, 2026-11-09). R0 (dry start, failing, 300 steps) kept too in
`~/PDM_results/study2f_R0_dry` (841 MB, 15 writes 0.01–30.8 µs), for the failure figure F1 of `NOTES_figures.md`.
