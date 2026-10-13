# Inlet relative-flux test: `+ 0.001` → `+ 1e-8` (2026-10-07)

Tests the explanation of the 0.24 % water deficit in `../BL_grav_BC` (both solvers store 99.76 % of the injected
water). In `alphaEqn.H`, on patches where `Uwetting`/`UnonWetting` are fixedValue, the boundary relative flux divides
by (eps*alpha_b + 0.001); the water inflow is then u[alpha + (1 - alpha) eps*alpha/(eps*alpha + 0.001)] = 0.9977 u.

- Solver: `b995db5` (installed `hybridPorousInterFoam`) with only those two lines changed (`variant_eps1e-8.patch`),
  built in the scratchpad as `hybridPorousInterFoam_eps1e-8`; `of9-port` and the installed binaries untouched.
- Case: `../BL_grav_BC/ABC` (tutorial setup + `darcyFaceMaxDa 0.1`), endTime 21,000 s.
- Kept: `log.hybridPorousInterFoam.gz`, and `21000/alpha.wetting`, `21000/phi` (the fields used below).

| at 21,000 s | `+ 0.001` (`../BL_grav_BC/ABC`) | `+ 1e-8` |
|---|---|---|
| water stored / injected | 0.99741 | 0.99973 |
| plateau saturation (exact 0.4668) | 0.4663 | 0.4667 |
| front (exact 0.9036 m) | −0.12 % | +0.05 % |

90 % of the deficit removed; the remaining 0.03 % is not explained. Not applied to `of9-port` (pending decision).
