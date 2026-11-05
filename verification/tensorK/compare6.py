#!/usr/bin/env python3
"""Check 6, prediction 3: serial against parallel 2D bench runs (after `../parallel_H/compare.py`).

    python3 compare6.py            (in verification/tensorK, after the C6 runs)

For the pairs (C6_scalar_serial, C6_scalar_split) = control and (C6_aniso_serial, C6_aniso_split) = test, at every
common write: max |alpha_split - alpha_serial|, gap meniscus (alpha 0.5, linear between cells) on the rows next to
the lower (k 8) and upper (k 15) wall and at mid-gap (k 11/12), wall front (alpha 0.1, linear) on the wall rows next to
the gap (k 7, 16), lower/upper mirror asymmetry max |alpha(k) - alpha(23 - k)|, max |U|. The bench mesh: 100 x 24
cells (x fastest), 20 um; walls k 0-7 and 16-23 end 3 cells before the outlet.
Pass (README.md): test max |dalpha| <= 3 x control, meniscus and fronts within 1 um of serial, asymmetry <= 3 x control.
"""
import os
import re
import sys

import numpy as np

NX, NZ, DX = 100, 24, 20e-6


def times(case):
    return sorted((d for d in os.listdir(case) if re.fullmatch(r"[0-9.eE+-]+", d) and float(d) > 0), key=float)


def read(case, t, name, vec=False):
    body = open(os.path.join(case, t, name)).read().split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        v = np.array(m.group(1).strip("()").split(), float)
        return np.tile(v, (NZ, NX, 1)) if vec else np.full((NZ, NX), v[0])
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if vec:
        return np.array([v.split() for v in re.findall(r"\(([^()]+)\)", data)[:n]], float).reshape(NZ, NX, 3)
    return np.array(data.split(")", 1)[0].split()[:n], float).reshape(NZ, NX)


def crossing(row, level, nmax=NX):
    """x [mm] where row drops below level (first crossing from the inlet), linear between cell centres"""
    idx = np.where(row[:nmax] < level)[0]
    if len(idx) == 0:
        return np.nan
    i = idx[0]
    if i == 0:
        return 0.0
    return ((i - 0.5) + (row[i - 1] - level) / (row[i - 1] - row[i])) * DX * 1e3


def measures(a, U):
    return {"men_low": crossing(a[8], 0.5), "men_up": crossing(a[15], 0.5),
            "men_mid": 0.5 * (crossing(a[11], 0.5) + crossing(a[12], 0.5)),
            "wall_low": crossing(a[7], 0.1, NX - 3), "wall_up": crossing(a[16], 0.1, NX - 3),
            "asym": np.abs(a - a[::-1]).max(), "Umax": np.linalg.norm(U, axis=2).max()}


def pair(serial, split):
    common = [t for t in times(serial) if os.path.isdir(os.path.join(split, t))]
    rows = []
    for t in common:
        a0, a1 = read(serial, t, "alpha.wetting"), read(split, t, "alpha.wetting")
        m0 = measures(a0, read(serial, t, "U", vec=True))
        m1 = measures(a1, read(split, t, "U", vec=True))
        rows.append((t, np.abs(a1 - a0).max(), m0, m1))
    return rows


res = {}
for name, (s, p) in {"control (scalar)": ("C6_scalar_serial", "C6_scalar_split"),
                     "test (tensor)": ("C6_aniso_serial", "C6_aniso_split")}.items():
    rows = pair(s, p)
    res[name] = rows
    print(f"== {name}: {p} vs {s}, {len(rows)} common writes")
    print(f"   {'t [ms]':>7} {'max|da|':>9} {'men low':>15} {'men up':>15} {'men mid':>15} "
          f"{'wall low':>15} {'wall up':>15} {'asym ser/par':>19} {'max|U|':>6}   (mm: serial / split)")
    for t, d, m0, m1 in rows:
        if abs(float(t) * 1e4 - round(float(t) * 1e4)) > 1e-6 or round(float(t) * 1e4) % 5:   # print every 0.5 ms
            continue
        f = lambda k: f"{m0[k]:7.4f}/{m1[k]:7.4f}"
        print(f"   {float(t) * 1e3:7.3f} {d:9.2e} {f('men_low'):>15} {f('men_up'):>15} {f('men_mid'):>15} "
              f"{f('wall_low'):>15} {f('wall_up'):>15} {m0['asym']:9.2e}/{m1['asym']:9.2e} {m0['Umax']:6.3f}")

ctl, tst = res["control (scalar)"], res["test (tensor)"]
dctl, dtst = max(r[1] for r in ctl), max(r[1] for r in tst)
keys = ("men_low", "men_up", "men_mid", "wall_low", "wall_up")
dmeas = max(abs(r[3][k] - r[2][k]) for r in tst for k in keys if np.isfinite(r[2][k]) and np.isfinite(r[3][k]))
actl = max(r[3]["asym"] for r in ctl)
atst = max(r[3]["asym"] for r in tst)
ok = dtst <= 3 * dctl and dmeas <= 1e-3 and atst <= 3 * actl
print(f"\n   max |dalpha| split vs serial: test {dtst:.2e}, control {dctl:.2e} (ratio {dtst / dctl:.2f}, limit 3)")
print(f"   meniscus and wall fronts, test split vs serial: largest difference {dmeas * 1e3:.4f} um (limit 1 um)")
print(f"   mirror asymmetry of the split runs: test {atst:.2e}, control {actl:.2e} (ratio {atst / actl:.2f}, limit 3)")
print(f"   {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
