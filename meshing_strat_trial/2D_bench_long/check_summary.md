# 2D bench: expected-behaviour checks

| Check | Value | Pass | Criterion |
|---|---|---|---|
| reaches the end time | 20.00 ms (ok) | yes | 20 ms, no stopGuard |
| water budget | max imbalance/stored 2.6e-14 | yes | < 1e-10 |
| max |U| (all writes) | 1.85 m/s | yes | < 2 m/s (real-wall slit ~1) |
| stray water ahead of the meniscus | max 0 cells | yes | <= 5 cells |
| walls take water from the gap, 1 ms | meniscus 0.430 < 0.629 mm (impermeable, Bosanquet) | yes | below the impermeable rise |
| gap feeds the walls, 1 ms | wall front 0.750 > 0.601 mm (walls alone, 1D) | yes | ahead of the walls alone |
| walls take water from the gap, 20 ms | meniscus 1.970 < 5.643 mm (impermeable, Bosanquet) | yes | below the impermeable rise |
| gap feeds the walls, 20 ms | wall front 1.950 > 2.558 mm (walls alone, 1D) | **NO** | ahead of the walls alone |
| wall front uniform across the wall (from 0.5 ms) | max |surface - back| 50 um | **NO** | <= 2 cells (lateral imbibition faster than the front) |
| wall water increases | 41.1 -> 754.1 cell volumes | yes | monotone |

| t [ms] | gap meniscus [mm] | wall front surface / back / mean [mm] | wall water [cell vol.] | max \|U\| [m/s] |
|---|---|---|---|---|
| 0.25 | 0.110 | 0.190 / 0.190 / 0.190 | 41 | 0.00 |
| 0.50 | 0.110 | 0.190 / 0.190 / 0.190 | 41 | 0.00 |
| 1.00 | 0.430 | 0.750 / 0.750 / 0.750 | 220 | 1.09 |
| 1.50 | 0.430 | 0.750 / 0.750 / 0.750 | 220 | 1.09 |
| 20.00 | 1.970 | 1.950 / 1.950 / 1.950 | 754 | 1.58 |
