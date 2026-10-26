# Slit: free surface and porous-wall coupling (consolidated 2026-10-15)

Evidence for the free-surface part of the solver and for the porous-wall treatment G + H + F′ + I, regenerated from
the existing runs (no new runs). Before this folder the numbers were quoted in `NOTES_solver.md` from terminal output
and the saved slit figures (`meshing_strat_trial/slit_test/figures/`, 2026-10-12) predated H, F′ and I.

```
../../.venv/bin/python slitVerification.py      # writes summary.md and slit_verification.png
```

## Case
Vertical slit 2 mm long, cells of 20 µm (one run at 10 µm), reservoir inlet at x = 0 (free faces at total pressure 0),
open outlet at x = 2 mm, gravity along −x, initial water column 0.1 mm in the gap, 2 ms. Built by
`meshing_strat_trial/slit_test/makeSlit.py` (parameters in each run's `slit.info`).
- **S0_\*** real walls (`constantAlphaContactAngle`, noSlip), gap 4/8/15 cells, θ 40/60/80°.
- **P_\*** porous walls 8 cells thick (16 at 10 µm), closed behind, ending 3 cells (30 µm at 10 µm: 6) before the
  outlet, with `porousFreeDarcyFaces on`, `activatePorousContactAngle 1`, `porousContactAngleWallLike 1`,
  `porousFreeFluxForce 1`, `porousFreeNoSlip 1`, `darcyFaceMaxDa 0.1` (0.5 at 10 µm). Walls ε 0.5, K 1e-20
  (impermeable), 1e-14 or 1e-11, yarn pc/kr (VG pc0 5000, m 0.5; BC n 3), dry 0.002.
- **IF_fill_total** stock OpenFOAM 9 `interFoam` on the S0 slit (gap 8, θ 60°), `slit_test/interFoamSlit.sh`.
- Reference: Bosanquet slit rise ρ d(hḣ)/dt = 2σcosθ/w − 12μhḣ/w² − ρgh from the 0.1 mm column (`slitReport.analytic`).

## Solver versions
| Runs | Binary | Date | Note |
|---|---|---|---|
| S0_\* | installed `hybridPorousInterFoam` of 2026-10-12 | 10-12 | real walls, no porous cells: A–I do not act |
| P_\* | scratch `hybridPorousInterFoamH` (H + F′ + I) | 10-13 | **bit-identical to the installed `b525086`**: `slit_test/V_w8_t60_K1e-20` and `V_w8_t60_K1e-11` (installed binary) = the P twins in α, U, p at 2 ms (`cmp`, rechecked 2026-10-15) |
| IF_fill_total | OpenFOAM 9 `interFoam` | 10-12 | stock solver |

## Results (`summary.md`, `slit_verification.png`)
| Check | Result | Verdict |
|---|---|---|
| Real walls vs Bosanquet (5 configurations, 1 and 2 ms) | +2.1 to +10.4 %, always fast, largest for the 4-cell gap | reported (no criterion; mesh/meniscus resolution and the simplified analytical model) |
| Stock interFoam vs our solver, real walls | max \|Δh\| 0.001 mm (0.5–2 ms) | **pass** (≤ 0.01 mm) |
| Porous walls K 1e-20 vs real walls | +0.0 to +1.4 % (1 and 2 ms) | **pass** (≤ 2 %) |
| Max \|U\| | S0 0.51–1.18 m/s, P 0.50–2.17 m/s (θ 40°: 2.17) | reported |
| Permeable walls, gap 8 θ 60° | h(2 ms) 1.252 / 1.214 / 0.782 mm for K 1e-20 / 1e-14 / 1e-11 | **pass** (monotone in K) |
| 20 µm vs 10 µm (K 1e-11) | 20 µm faster: meniscus +7.5 → +3.7 %, wall front +9.3 → +5.0 % (0.5 → 2 ms) | reported (two meshes: trend only) |

## What this does and does not show
- Shows: the free-surface part reproduces stock interFoam and is 2–10 % fast vs the analytical rise; impermeable porous
  walls with G + H + F′ + I behave like real walls (within 1.4 %); permeable walls slow the gap rise in the right order;
  the coupled result changes by ~4–9 % from 20 to 10 µm.
- Does not show: that the amount of water the walls take from the gap, or the interface pressure jump, is right (no
  reference); the effect of θ fixed on wet wall surfaces (biases the rise low); 3D, staircased or curved yarn surfaces.
- The 4-cell gap is the least accurate (+10 % vs Bosanquet with real walls already): gaps of ≤ 4 cells (6 % of the REV
  free cells) are under-resolved.
