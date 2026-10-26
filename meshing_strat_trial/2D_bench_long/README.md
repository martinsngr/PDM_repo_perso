# 2D_bench_long — the 2D bench to 20 ms (2026-10-15)

Copy of `../2D_bench` (thick-wall slit, yarn walls 8 cells, gap 8 cells, θ 60°, G + H + F′ + I), solver
`hybridPorousInterFoam` = `b525086`. Only changes: `endTime 0.02` (was 0.002), `writeInterval 1e-3` (was 5e-5).
Run: `LOG_EVERY=100 ./run`. Question: does the current solver stay stable over 10× the tested time (runs > 5 ms were
never tested)?

## Predictions (before the run)
- √t extrapolation of the 2 ms results: wall front 1.15 mm at 2 ms → reaches the end of the walls (1.94 mm) at ~6 ms;
  gap meniscus 0.79 mm at 2 ms → ~1.4 mm at 6 ms, ~2.5 mm at 20 ms if it kept rising (it cannot: the slit is 2 mm),
  so the gap water should reach the open outlet around 12–15 ms.
- Stable while the fronts are inside the slit (as at 2 ms). Risks, in order: (1) water reaching the open outlet
  (free cells: total-pressure/inletOutlet BCs never tested with water leaving), (2) wet wall ends next to the free
  outlet cells, (3) long-time drift of the water budget.
- Pass: reaches 20 ms, α in [0, 1] (within MULES tolerance), max |U| ≲ 1–2 m/s, water budget closed (as `check.py`).
  Crash or dt collapse = fail, recorded with time, last dt, last max |U| and where.

## Results (2026-10-15, laptop serial, 7.5 min; log `log.hybridPorousInterFoam` every 100th step + `.tail`)

**Stability: pass.** Reaches 20 ms (`End`), α in [0, 1] (min −3e-19), water budget closed (max imbalance/stored
2.6e-14), max |U| 1.85 m/s over the writes, Courant max ≤ 0.14, no stray water. `check.py` (T_END set to 2e-2 in
this copy) fails two checks by construction: wall front vs the 1D walls-alone reference (2.56 mm, outside the 2 mm
domain) and front uniformity (uses 0.5/1.5 ms, not written here).

| t (ms) | water (m³) | inflow / outflow (m³/ms) | gap α at x 95–99 | gap Ux x 0 / 50 / 99 (m/s) | wall α mean |
|---|---|---|---|---|---|
| 2 | 5.44e-12 | 2.4e-12 / 0 | | | |
| 4 | 9.45e-12 | 1.9e-12 / 0 | 0 | 0.63 / 0.56 / 0.48 (air) | 0.81 |
| 5 | 1.12e-11 | 1.7e-12 / 2e-17 | ~0 | 0.57 / 0.50 / 0.40 | 0.93 |
| 6 | 1.22e-11 | 1.4e-12 / 3.6e-13 | ~1 | 0.44 / 0.36 / 0.38 | 0.94 |
| 10 | 1.21e-11 | 2.8e-13 / 3.2e-13 | 0.99 → 0.28 | 0.13 / 0.06 / 0.16 | 0.96 |
| 20 | 1.22e-11 | 1.55e-13 / 1.52e-13 | 0.92 → 0.16 | 0.08 / 0.05 / 0.05 | 0.97 |

- Fronts reach the end of the slit at ~5–6 ms (faster than the √t extrapolation: ~6 ms walls, 12–15 ms gap).
- **After that, not physical:** a steady through-flow (~1.5e-13 m³/ms ≈ 10 % of the early wicking rate, mean gap
  velocity ~0.05 m/s, not decaying from 11 to 20 ms) leaves through the open outlet. The gap pressure rises upward
  (−5 / 97 / 186 Pa at x 0 / 50 / 90) and drops ~200 Pa in the last cells: water flows against the pressure rise and
  gravity (20 Pa over 2 mm). Outlet column (x 97–99, free cells over the full height: the walls end 3 cells before
  it): α 0–0.26 with Ux alternating ±1 m/s cell to cell (air in, water out). A real slit (h_eq ≈ 13 mm) would pin the
  meniscus at the open end and stop. Driving term not isolated (hypothesis: surface tension of the smeared interface
  at the open boundary).
- **Consequence:** the coupled solver is stable to 20 ms; the open-outlet treatment is not valid once water reaches
  it. Benches and the REV must end before water arrives at an open outlet, or close / extend the outlet (REV decision
  "outlet" in `NOTES_cases.md`).
