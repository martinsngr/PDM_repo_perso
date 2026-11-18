# Experimental inputs: what the model needs (checklist, 2026-11-13)

What the REV and the 1D model need from the yarn and fabric tests, with the value used until now (setup values, not measured).
Context: `NOTES_cases.md` (Plan: fabric-scale 1D model; Next steps), `NOTES_solver.md` (open issue: kr/pc models outside the solver).

## Yarn (inputs of the porous continuum)
| Quantity | Feeds | Value until now |
|---|---|---|
| Fibre diameter, fibre volume fraction in the yarn V_f | ε = 1 − V_f; Gebart K (`build_fields.py`) | 15 µm, V_f 0.5 (ε 0.5) |
| K along and across the yarn (saturated), or V_f and fibre diameter for Gebart | K tensor (Kpar, Kperp) | Gebart hex 4.2e-12 / 9.2e-13 m²; scalar 1e-11 |
| Capillary pressure pc(S), whole range: dry end (bounded by the bundle's largest pores) and near saturation (S 0.9–1, decides when gaps hold water: gap suction 0.2–0.7 kPa) | pc model and coefficients | Van Genuchten pc0 5000 Pa, m 0.5 (bundle estimate ≈ 19 kPa·cosθ) |
| Relative permeability kr(S), or unsaturated K(S) (e.g. from wicking profiles with pc(S)) | kr model | Brooks–Corey n 3 |
| Highest water saturation reached by wicking (trapped air): weigh dry, wicked, fully saturated (vacuum) | S_max | 0.999 |
| Contact angle: on the fibre material (Young) and apparent on the yarn surface, dry and wet; a fully wetting reference liquid separates geometry from wetting | θ (change H, gap menisci); pc ∝ cosθ | 60° (REV), 40° / 85° tested |
| Test liquid at the test temperature: σ, μ, ρ | fluid properties | water 0.072 N/m, 1e-3 Pa·s |

Model limits to keep in mind when fitting: the solver offers pc Van Genuchten, Brooks–Corey, Linear and kr Brooks–Corey, Van
Genuchten; `tools/coatsTimeStep` assumes Brooks–Corey kr + Van Genuchten pc (another law needs it changed); a pc bounded at the dry end
is not in the library (both laws diverge as S → 0); water and air kr end points share one keyword.

## Fabric (REV geometry)
- Weave, ends and picks per cm, yarn width and thickness in the fabric, crimp, fabric thickness, areal mass (the `funge.py` / TexGen
  inputs; check the TexGen gaps against the real fabric, µCT if available: the gaps carry most of the through-thickness uptake).
- The same yarn in several weaves and densities (the planned comparison).

## Validation tests (not used for calibration)
- Vertical strip wicking: front height and uptake mass against time per fabric width, up to equilibrium (minutes to hours, gravity).
- Through-thickness absorption (fabric laid on water): uptake per area against time, from ms if possible, and at the end.
- Weighing at long times: total water against the capacities of the REV (plain weave: yarns full 65 g/m², everything full ~212 g/m²),
  which tells whether the gaps fill.
