"""Shape of the growing transverse mode in the dump runs (original solver be54696).

    ../../.venv/bin/python modeShape.py r1_dump 5 172 3
    ../../.venv/bin/python modeShape.py r2_dump 10 344 6

Cell order of the single block: i + nx*(j + ny*k). For each written time: delta = alpha - row mean (row = all cells
at the same j). Prints the max |delta|, the row where it sits, the cross-section of delta (x across, z down) in that
row, the parity checks (does delta flip sign from one cell to the next in x, z, y) and the same for U (x and z).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solver_failures"))
from foamio import read_field, times  # noqa: E402


def parity(d, axis):
    """Fraction of neighbour pairs along axis with opposite signs, weighted by |product| (1 = pure odd-even)."""
    a = np.take(d, range(d.shape[axis] - 1), axis=axis)
    b = np.take(d, range(1, d.shape[axis]), axis=axis)
    w = np.abs(a * b)
    return float((w * (a * b < 0)).sum() / w.sum()) if w.sum() > 0 else float("nan")


case, nx, ny, nz = sys.argv[1], *map(int, sys.argv[2:5])
n = nx * ny * nz
for t in times(case):
    if float(t) == 0:
        continue
    a = read_field(os.path.join(case, t, "alpha.wetting"), n).reshape(nz, ny, nx)  # [k, j, i]
    U = read_field(os.path.join(case, t, "U"), n, vector=True).reshape(nz, ny, nx, 3)
    d = a - a.mean(axis=(0, 2), keepdims=True)
    k, j, i = np.unravel_index(np.abs(d).argmax(), d.shape)
    rows = np.abs(d).max(axis=(0, 2))
    active = np.where(rows > 0.1 * rows.max())[0]
    print(f"t {t}: max|delta| {np.abs(d).max():.3g} at row {j} (y {(j + 0.5) * 3.446 / ny:.3f} mm), "
          f"rows > 10% of max: {active.min()}-{active.max()}, row mean alpha {a[:, j, :].mean():.3f}")
    print(f"   parity x {parity(d, 2):.2f}  z {parity(d, 0):.2f}  y {parity(d[:, active.min():active.max() + 1], 1):.2f}"
          f"   | Ux parity x {parity(U[..., 0], 2):.2f}, max|Ux| {np.abs(U[..., 0]).max():.3g}, "
          f"max|Uz| {np.abs(U[..., 2]).max():.3g}, max|Uy| {np.abs(U[..., 1]).max():.3g}")
    if t == times(case)[-1] or len(sys.argv) > 5:
        print("   delta in row", j, "(rows: z = k, columns: x = i):")
        for kk in range(nz):
            print("    ", " ".join(f"{v:+.1e}" for v in d[kk, j]))
        print("   delta along y, cell (i, k) =", (i, k), ":",
              " ".join(f"{v:+.1e}" for v in d[k, max(0, j - 6):j + 7, i]))
