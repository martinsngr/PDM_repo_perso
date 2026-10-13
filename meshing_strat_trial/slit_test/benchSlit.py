#!/usr/bin/env python3
"""
benchSlit.py  -  thick-wall slit bench (makeSlit.py --nw 8): gap meniscus, wall fronts, wall water, max |U|.

    ../../.venv/bin/python benchSlit.py CASE [CASE ...]
Gap meniscus h: gap-averaged alpha < 0.5 (as slitReport.py). Wall fronts: first x where alpha < 0.1 in the wall row
next to the gap (surface) and in the row against the closed back wall (back). Wall water: sum(eps*alpha) over the
porous cells, in cell volumes. Wall without gap (--w 0): fronts of row nw-1 (surface) and row 0 (back) of the lower wall.
"""
import sys

import numpy as np

from slitReport import info, readU, times
sys.path.insert(0, "../tools")
from initFields import read_internal  # noqa: E402

LX = 2e-3


def grid(c):
    d = dict(l.split(None, 1) for l in open(f"{c}/slit.info") if l.strip())
    dx = float(d.get("dx", 20e-6))
    return dx, round(LX / dx)


def front(row, lim):
    j = np.where(row < lim)[0]
    return x[j[0]] * 1e3 if len(j) else LX * 1e3


for c in sys.argv[1:]:
    walls, w, th, K, nw, nz = info(c)
    DX, NXC = grid(c)
    x = (np.arange(NXC) + 0.5) * DX
    print(f"== {c}: gap {w} cells, walls {nw} cells, dx {DX*1e6:g} um, K {K:g}, theta {th:g}")
    print(f"{'t[ms]':>6} {'gap h':>6} {'wSurf':>6} {'wBack':>6} {'wMean':>6} {'wallW':>7} {'max|U|':>7}")
    for t in times(c):
        a = read_internal(f"{c}/{t}/alpha.wetting", NXC * nz).reshape(nz, NXC)
        e = read_internal(f"{c}/{t}/eps", NXC * nz).reshape(nz, NXC)
        gap = a[nw:nw + w].mean(axis=0) if w else None
        h = front(gap, 0.5) if w else np.nan
        wall = np.concatenate([a[:nw], a[nw + w:]])
        surf = (a[nw - 1] + a[nw + w]) / 2
        back = (a[0] + a[-1]) / 2
        por = e < 0.99
        print(f"{float(t)*1e3:6.2f} {h:6.3f} {front(surf, 0.1):6.3f} {front(back, 0.1):6.3f} "
              f"{front(wall.mean(axis=0), 0.1):6.3f} {(e * a)[por].sum():7.2f} {readU(f'{c}/{t}/U'):7.2f}")
