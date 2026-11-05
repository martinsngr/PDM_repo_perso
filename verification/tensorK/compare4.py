#!/usr/bin/env python3
"""Check 4: the 2D spreading box (README.md).

    python3 compare4.py            (in verification/tensorK, after C4_tensor, C4_stretched, C4_aniso_impes)

(a) C4_tensor vs C4_stretched: alpha cell by cell at every common write (same cell order), number of steps and the
    deltaT of every step (relative difference). Pass: max |dalpha| <= 1e-8, same step count, dt within 1e-8.
(b) C4_tensor vs C4_aniso_impes (Sb): front (0.1, linear between cell centres) along the left edge (y_f, cells of
    the first column) and along the bottom edge (x_f, cells of the first row), aspect y_f/x_f, mean saturation.
    Pass from 2 ms: y_f and x_f within 3 %, aspect within 2 %; aspect at the last write in [1.75, 2.0] for both.
"""
import os
import re
import sys

import numpy as np


def times(case):
    return sorted((d for d in os.listdir(case) if re.fullmatch(r"[0-9.eE+-]+", d) and float(d) > 0), key=float)


def read(case, t, name):
    body = open(os.path.join(case, t, name)).read().split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        raise SystemExit(f"{case}/{t}/{name}: uniform field")
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if "(" in data.split("\n)", 1)[0]:                      # vector list
        return np.array([v.split() for v in re.findall(r"\(([^()]+)\)", data)[:n]], float)
    return np.array(data.split(")", 1)[0].split()[:n], float)


def dts(case, log):
    p = os.path.join(case, log)
    return np.array([float(l.split("=")[1]) for l in open(p, errors="replace") if l.startswith("deltaT =")])


def front(coord, val, level=0.1):
    """first position along coord (sorted) where val drops below level, linear between cell centres"""
    o = np.argsort(coord)
    c, v = coord[o], val[o]
    idx = np.where(v < level)[0]
    if len(idx) == 0:
        return np.nan
    i = idx[0]
    if i == 0:
        return c[0]
    return c[i - 1] + (v[i - 1] - level) / (v[i - 1] - v[i]) * (c[i] - c[i - 1])


ok = True
# ---- (a)
T, S = "C4_tensor", "C4_stretched"
common = [t for t in times(T) if t in times(S)]
dmax = max(np.abs(read(T, t, "alpha.wetting") - read(S, t, "alpha.wetting")).max() for t in common)
dt_t, dt_s = dts(T, "log.hybridPorousInterFoam_T"), dts(S, "log.hybridPorousInterFoam_T")
n = min(len(dt_t), len(dt_s))
ddt = np.max(np.abs(dt_t[:n] - dt_s[:n]) / dt_t[:n]) if n else np.nan
oka = dmax <= 1e-8 and len(dt_t) == len(dt_s) and ddt <= 1e-8
ok &= oka
print(f"== (a) {S} vs {T}: {len(common)} common writes")
print(f"   max |dalpha| {dmax:.2e}; steps {len(dt_t)} / {len(dt_s)}; deltaT max relative difference {ddt:.2e}")
print(f"   {'PASS' if oka else 'FAIL'} (<= 1e-8, same steps, dt <= 1e-8)")

# ---- (b)
I = "C4_aniso_impes"
C = read(T, "0", "C")
x, y = C[:, 0] * 1e3, C[:, 1] * 1e3                         # mm
col, row = np.isclose(x, x.min()), np.isclose(y, y.min())
common = [t for t in times(T) if t in times(I)]
print(f"\n== (b) {I} (Sb) vs {T} (alpha): {len(common)} common writes; fronts at 0.1 [mm]")
print(f"   {'t [ms]':>7} {'y_f T / I':>17} {'diff':>7} {'x_f T / I':>17} {'diff':>7} {'aspect T / I':>15} {'diff':>7} "
      f"{'mean sat. T / I':>17}")
okb, last = True, None
for t in common:
    a, s = read(T, t, "alpha.wetting"), read(I, t, "Sb")
    yt, yi = front(y[col], a[col]), front(y[col], s[col])
    xt, xi = front(x[row], a[row]), front(x[row], s[row])
    at, ai = yt / xt, yi / xi
    dy, dx, da = yi / yt - 1, xi / xt - 1, ai / at - 1
    if float(t) >= 2e-3 - 1e-9:
        okb &= abs(dy) <= 0.03 and abs(dx) <= 0.03 and abs(da) <= 0.02
    last = (at, ai)
    print(f"   {float(t) * 1e3:7.2f} {yt:8.4f}/{yi:8.4f} {dy:+7.2%} {xt:8.4f}/{xi:8.4f} {dx:+7.2%} "
          f"{at:7.4f}/{ai:7.4f} {da:+7.2%} {a.mean():8.5f}/{s.mean():8.5f}")
okb &= last is not None and all(1.75 <= v <= 2.0 for v in last)
ok &= okb
print(f"   aspect at the last write: {last[0]:.4f} / {last[1]:.4f} (prediction 1.75-2.0, -> sqrt(4) = 2)")
print(f"   {'PASS' if okb else 'FAIL'} (from 2 ms: fronts within 3 %, aspect within 2 %)")
sys.exit(0 if ok else 1)
