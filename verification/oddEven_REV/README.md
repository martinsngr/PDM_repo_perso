# Odd-even check of the REV outputs (post-processing only, 2026-11-18)

**Question (user's reviewer, with the solver freeze of 2026-11-18):** A + B + C oscillates cell to cell in the
gravity–capillarity equilibrium (counter-current flow at zero total flux; roughness 0.29 → 0.89; suspected cause C, never
isolated; Study 1 of `verification/PLAN.md` never run). The production set-ups avoid that case, but the flow is locally
counter-current where water enters a yarn and air leaves through its surface. Agreed on 2026-10-13: fix it, or show that it
does not occur in the wicking runs. This is the second option, on the REV outputs already in `~/PDM_results/`: no run, no
solver change. Earlier evidence (`../scanOddEven.py`, `../oddEvenScan.png`): the 1D and single-yarn wicking fields have the
level of their impesFoam twins; no free cells there.

## Method (`scanREV.py`)

Mesh read from `constant/polyMesh` (cell centres from the face points, one neighbour per direction ±x, ±y, ±z from the
internal faces; cyclic and boundary faces not used). Porous cells: `eps` < 0.999. Yarn axis of a porous cell: the longer
in-plane extent (x or y) of its yarn (`0/yarnID`); z is always across. At every write:
1. **Zig-zag in S** (porous cells, porous neighbours only): four consecutive cells along an axis whose three differences
   alternate in sign (up-down-up or down-up-down), each larger than 1e-3 in S. This is the odd-even signature (a 1D
   oscillation makes every interior quadruple a zig-zag); a front, a crossing contact or a drained surface give at most one
   sign change over four cells. Counted per direction, along / across the cell's yarn, as a share of the porous cells.
2. **Strict local extrema** of S among the porous face neighbours, by more than 1e-3 (`../scanOddEven.py` restricted to the
   yarns).
3. **Phase fluxes on yarn/gap faces** (internal faces between a porous and a free cell): water `alphaPhi0.wetting` and air
   `phi − alphaPhi0.wetting`, signed positive into the yarn. Along the yarn surface (three consecutive porous cells along a
   direction parallel to the face, each with a yarn/gap face on the same side), a triplet alternates if the middle flux has
   the opposite sign of both neighbours, all three above 1 % of the 99th percentile of |q| on yarn/gap faces at that write.
   Reported as a share of the triplets above that threshold, water and air separately; also the share of counter-current
   faces (water in, air out).

Controls: `../eq_BC/port` (original, no oscillation) and `../eq_BC/ABC` (A + B + C, the oscillation): the metric must flag
ABC and not port, otherwise it is not used. Second solver on the same yarns: `anisoA` (anisoImpesFoam, `tensorA`'s yarns
without gaps). **Correction after the scan:** I first called `anisoA` a reference without C; its `fvSchemes` upwind kr by each
phase's flux (`kra upwind phia`, `krb upwind phib`), C's principle, so it is not one (another solver with the same kr rule,
explicit S, no momentum path). `locate.py` (added after the scan, after R2 failed): where the alternating flux triplets sit, and
the gross and net water exchange through them.

Cases (copies in `~/PDM_results/`): job 3068 (scalar K, J bath), `study2g_N2_full` and `study2g_N2c_full` (scalar K, N2 /
N2c bath; N2c = the bath of the vertical template), `tensorA`, `tensorB` (tensor K, J bath), `twillA` (twill, tensor K),
`horizB_t40`, `horizB_t85` (horizontal, Gebart tensor K, θ 40 / 85°), `anisoA`. Every write.

## Predictions (written before the scan)

- C1: `eq_BC/ABC` zig-zags along y on ≥ 10 % of its cells at the late writes, `eq_BC/port` on < 1 %.
- R1: every REV run, every write: zig-zag quadruples ≤ 0.1 % of the porous cells, along and across, with no growth over the
  run; strict extrema within ×3 of `anisoA` at the same times for `tensorA`.
- R2: alternating flux triplets on yarn/gap faces ≤ 1 % of the triplets above the threshold, water and air, every write.
- Reading: C1 fails → the metric does not catch the known oscillation, no conclusion. R1 and R2 pass → one sentence in the
  thesis (the oscillation of the equilibrium case does not appear in the wicking runs, with the numbers). Either fails →
  locate the sites (where, which faces, growing or not) and put it in the limitations.

## Results (2026-11-18, every write; `results/<case>.csv`, one row per write)

| Case | writes | zig-zags in S, max (% porous) | largest step | strict extrema, max | water: alternating triplets, max share | air: same | over time |
|---|---|---|---|---|---|---|---|
| eq_BC port (control) | 120 | 72 (4.8 %) | 0.054 | 144 | — | — | 72 → 25–34 |
| eq_BC A + B + C (control) | 120 | 766 (51 %) | 0.889 | 771 | — | — | 664 → 700–766 |
| 3068 (scalar, J) | 60 | 71 (0.09 %) | 0.006 | 47 | 6.1 % (44 of 722) | 1.7 % | 71 at 0.5 ms, then 1–10 |
| N2_full (scalar, N2) | 60 | 293 (0.37 %) | 0.022 | 414 | 16.6 % (283 of 1,708) | 1.7 % | 54 → ~230 from 8 ms, flat |
| N2c_full (scalar, N2c) | 60 | 224 (0.29 %) | 0.021 | 372 | 17.2 % (283 of 1,645) | 1.5 % | 66 → ~200 from 15 ms, flat |
| tensorA (J) | 60 | 104 (0.13 %) | 0.028 | 74 | 4.9 % (36 of 734) | 1.0 % | 55 → 29 |
| tensorB (J, 60 ms) | 120 | 107 (0.14 %) | 0.022 | 140 | 5.1 % (33 of 645) | 1.2 % | 18–88, no trend |
| twillA (J, 20 ms) | 40 | 68 (0.09 %) | 0.030 | 48 | 5.2 % (37 of 717) | 1.1 % | 68 → 20 |
| horizB_t40 (10 ms) | 50 | 1,203 (1.5 %) | 0.030 | 3,131 | 5.6 % (912 of 16,417) | 1.7 % | 544 → ~1,000 from 5 ms, flat |
| horizB_t85 (10 ms) | 50 | 1,858 (2.4 %) | 0.038 | 1,514 | 4.4 % (643 of 14,651) | 2.0 % | 600–980, no trend |
| anisoA (anisoImpesFoam) | 60 | 2,574 (3.3 %) | 0.019 | 80 | — | — | 792 → ~2,400 from 15 ms, flat |

**Saturation.** The oscillation of the equilibrium case is not there. ABC zig-zags on half of its cells with steps up to 0.89
in S. The REV runs zig-zag on 0.09–0.37 % (vertical) and 1.5–2.4 % (horizontal) of the yarn cells, with steps ≤ 0.04, and
reach a plateau or decay. That is at or below the level of the original solver in the equilibrium case (port 1.7–4.8 %, steps
≤ 0.054) and of anisoImpesFoam on the same yarns (3.3 %, ≤ 0.019). In N2/N2c the count rises when the waterline gaps fill
(8–15 ms); the largest steps sit there (S 0.94–0.97, along y, within 0.05 mm of the bath plane).

**Fluxes on yarn/gap faces (`locate.py`, N2c 30 ms, N2 15 ms, 3068 and tensorA 15.5 ms, horizB 10 ms).** Where nearly saturated
yarn (S 0.95–1.0) faces water-filled gap cells (α 0.9–1), the water exchange changes sign from one face to the next. That is
the waterline gaps in N2/N2c (within 0.3 mm of the plane) and every water-filled gap of the horizontal case. The alternating
faces have the magnitudes of the other active faces (median 0.07–0.25 of the 99th percentile). They chain into 4-face
zig-zags 69–138 times per write (N2, N2c, horizontal) and carry 15–16 % (N2, N2c), 4 % (horizontal) and 2–10 % (J runs) of
the gross exchange. Their net flows out of the yarns: −8 % of the net yarn uptake in N2c (−3.2e-10 against 4.2e-9 m³/s),
−7 % in N2, −46 % in horizB_t40 and −2 % in horizB_t85 at 10 ms, when the yarns are near saturation and the net uptake is
small. In the J runs the gaps are dry, the faces few and the fluxes tiny (p99 4e-14 m³/s in 3068). Measured on the way: the
gross exchange is 9× (N2c) to 220× (horizB_t40) the net. Water enters and leaves the saturated yarns at different places;
most of that is not face-to-face alternation (not looked at further).

**Scoring.**
- C1: ABC 51 % passes. Port < 1 % fails (1.7–4.8 %, steps ≤ 0.054): low-level roughness exists without the oscillation. The
  controls still separate by ×10–25 in count and ×20–40 in step size.
- R1 (≤ 0.1 % at every write, no growth): passes for 3068 and twillA. Fails for tensorA/B (0.13–0.14 %), N2/N2c
  (0.29–0.37 %) and the horizontal pair (1.5–2.4 %). No growth past a plateau anywhere. tensorA's extrema are within ×3 of
  anisoA (74 against 80), but anisoA is not a reference without C (correction above).
- R2 (≤ 1 % alternating triplets): fails for water in every run (4.4–17 %); air 1.0–2.0 %.

**Reading (for the thesis).** No odd-even oscillation of the yarn saturation like the equilibrium case's: one sentence, with
the numbers above. **Limitation:** at the surface of nearly saturated yarns facing water-filled gaps, the water exchange
alternates in sign from face to face on 4–17 % of the active surface triplets, bounded in time. Its net is opposite to the
uptake and reaches −46 % of the net yarn uptake once that uptake is small (horizontal case near saturation). Its effect on the
uptake curves is not separated, and whether C causes it is not known (no run without C; not to be run, solver frozen).
