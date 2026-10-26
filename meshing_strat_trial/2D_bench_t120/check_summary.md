# 2D bench: expected-behaviour checks

| Check | Value | Pass | Criterion |
|---|---|---|---|
| reaches the end time | 2.00 ms (ok) | yes | 2 ms, no stopGuard |
| water budget | max imbalance/stored 5.2e-15 | yes | < 1e-10 |
| max |U| (all writes) | 1.20 m/s | yes | < 2 m/s (real-wall slit ~1) |
| stray water ahead of the meniscus | max 0 cells | yes | <= 5 cells |
| walls take water from the gap, 1 ms | meniscus 0.430 < 0.629 mm (impermeable, Bosanquet) | yes | below the impermeable rise |
| gap feeds the walls, 1 ms | wall front 0.750 > 0.601 mm (walls alone, 1D) | yes | ahead of the walls alone |
| walls take water from the gap, 2 ms | meniscus 0.790 < 1.159 mm (impermeable, Bosanquet) | yes | below the impermeable rise |
| gap feeds the walls, 2 ms | wall front 1.150 > 0.829 mm (walls alone, 1D) | yes | ahead of the walls alone |
| wall front uniform across the wall (from 0.5 ms) | max |surface - back| 20 um | yes | <= 2 cells (lateral imbibition faster than the front) |
| wall water increases | 41.1 -> 369.0 cell volumes | yes | monotone |

| t [ms] | gap meniscus [mm] | wall front surface / back / mean [mm] | wall water [cell vol.] | max \|U\| [m/s] |
|---|---|---|---|---|
| 0.25 | 0.110 | 0.390 / 0.390 / 0.390 | 99 | 1.09 |
| 0.50 | 0.210 | 0.530 / 0.510 / 0.530 | 140 | 1.15 |
| 1.00 | 0.430 | 0.750 / 0.750 / 0.750 | 220 | 1.09 |
| 1.50 | 0.610 | 0.950 / 0.950 / 0.950 | 297 | 1.03 |
| 2.00 | 0.790 | 1.150 / 1.150 / 1.150 | 369 | 0.98 |
