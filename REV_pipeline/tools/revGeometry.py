#!/usr/bin/env python3
"""revGeometry.py  -  geometry facts of a REV case from its fields (read-only).

    python3 ../tools/revGeometry.py <case> [--axis y]     (numpy, scipy; run after ./Allpre)

Reads 0/eps, 0/yarnID, 0/alpha.wetting (cells in OpenFOAM order: uniform blocks stacked in z, as
build_fields.py writes them; the cell counts come from system/blockMeshDict) and prints: porous faces
on each box face, porous/free face pairs across the periodic in-plane planes, the run direction of
each yarn, free cells inside the per-column envelope of the yarns, whether the free cells form a path
from the inlet face to the outlet face of the wicking axis (6-connected, periodic across), also without
the outer z layers, straight free rows along the wicking axis, and the widest path (distance to the
nearest yarn or z plane, in cells) that still crosses the REV. --axis: wicking direction (x or y,
default y); the other in-plane direction is periodic. Porous = eps <= 0.99 (hybridPorousInterFoam).
(2026-10-26, REV review before the case setup; results in ../../NOTES_cases.md, REV geometry.)"""
import re, sys
import numpy as np
from scipy import ndimage

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("case")
ap.add_argument("--axis", choices=("x", "y"), default="y", help="wicking direction (default y)")
args = ap.parse_args()
case = args.case
bm = open(f"{case}/system/blockMeshDict").read()
blocks = re.findall(r"hex\s*\([\d\s]+\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", bm)
assert all(b[:2] == blocks[0][:2] for b in blocks), "blocks must be stacked in z"
N = (int(blocks[0][0]), int(blocks[0][1]), sum(int(b[2]) for b in blocks))
dx = 20e-6                 # nominal cell size, for the yarn extents only
print(f"mesh {N[0]} x {N[1]} x {N[2]} ({len(blocks)} block(s)), wicking along {args.axis}")

def read(name):
    txt = open(f"{case}/0/{name}").read()
    body = txt.split("internalField", 1)[1]
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    vals = body.split("(", 1)[1].split(")", 1)[0].split()
    return np.array(vals[:n], float).reshape(N, order="F")

eps = read("eps"); yid = read("yarnID"); alpha = read("alpha.wetting")
P = eps <= 0.99          # porous
F = ~P
print(f"cells {P.size}: porous {P.sum()}, free {F.sum()}")

# ---- box faces (original frame)
for name, sl in [("x min", P[0]), ("x max", P[-1]), ("y min", P[:, 0]), ("y max", P[:, -1]),
                 ("z min (bottom)", P[:, :, 0]), ("z max (top)", P[:, :, -1])]:
    print(f"{name:15s}: {sl.size:6d} faces, porous {sl.sum():6d} ({sl.mean()*100:5.1f} %)")
for name, a0, a1 in (("x", P[0], P[-1]), ("y", P[:, 0], P[:, -1])):
    print(f"across the {name} planes (periodic image): porous/free face pairs {(a0 != a1).sum()} of {a0.size}")

# porous/free internal faces
pf = sum(((P[:-1] != P[1:]).sum(), (P[:, :-1] != P[:, 1:]).sum(), (P[:, :, :-1] != P[:, :, 1:]).sum()))
print(f"internal porous/free faces: {pf}")

# ---- yarns
print("\nyarn  cells  x-extent[mm]  y-extent[mm]  z-range[mm]  runs along")
for y in range(10):
    idx = np.argwhere((yid == y) & P)
    if len(idx) == 0:
        continue
    ext = (idx.max(0) - idx.min(0) + 1) * dx * 1e3
    along = "x" if ext[0] > ext[1] else "y"
    print(f"{y:4d} {len(idx):6d}  {ext[0]:10.3f}  {ext[1]:12.3f}  {idx[:,2].min()}-{idx[:,2].max()} (cells)   {along}")

# ---- from here on: axis 0 = wicking axis (inlet at index 0), axis 1 = periodic in-plane axis
if args.axis == "y":
    P, F, yid, alpha = (np.ascontiguousarray(f.transpose(1, 0, 2)) for f in (P, F, yid, alpha))
    N = (N[1], N[0], N[2])

# ---- column envelope: free cells between the lowest and highest yarn cell of their (x, y) column
#      (not the "fabric envelope" of NOTES_cases.md, which counts free cells inside the fabric thickness)
anyP = P.any(axis=2)
kmin = np.where(anyP, np.argmax(P, axis=2), N[2])
kmax = np.where(anyP, N[2] - 1 - np.argmax(P[:, :, ::-1], axis=2), -1)
K3 = np.arange(N[2])[None, None, :]
env = (K3 >= kmin[:, :, None]) & (K3 <= kmax[:, :, None])
print(f"\ncolumns without any porous cell: {(~anyP).sum()} of {anyP.size}")
print(f"free cells between yarn cells of their column: {(F & env).sum()}, others (holes through the fabric, space above/below the yarns): {(F & ~env).sum()}")
print("free fraction per z layer:", np.round(F.mean(axis=(0, 1)), 2))
print("fraction per z layer of free cells between yarn cells of their column:", np.round((F & env).mean(axis=(0, 1)), 2))

# ---- connectivity along the wicking axis (6-connectivity, periodic across it)
def percolates(mask):
    """components of mask touching the inlet and outlet faces (axis 0), periodic along axis 1 (labels merged)."""
    lab, n = ndimage.label(mask)
    # merge labels across the periodic planes of axis 1
    parent = np.arange(n + 1)
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    a, b = lab[:, 0, :], lab[:, -1, :]
    for u, v in zip(a[(a > 0) & (b > 0)], b[(a > 0) & (b > 0)]):
        ru, rv = find(u), find(v)
        if ru != rv: parent[ru] = rv
    roots = np.array([find(i) for i in range(n + 1)])
    L = roots[lab]; L[~mask] = 0
    s_in = set(np.unique(L[0][L[0] > 0])); s_out = set(np.unique(L[-1][L[-1] > 0]))
    both = s_in & s_out
    vol = sum((L == r).sum() for r in both)
    return len(both), vol, L, both

nb, vol, L, both = percolates(F)
print(f"\nall free cells: {nb} component(s) connect inlet and outlet ({vol} cells)")
nb2, vol2, L2, both2 = percolates(F & env)
print(f"free cells between yarn cells of their column only: {nb2} component(s) connect inlet and outlet ({vol2} cells)")
for kk in range(1, 5):
    core = np.zeros_like(F); core[:, :, kk:N[2]-kk] = True
    nb3, vol3, *_ = percolates(F & core)
    print(f"free cells without the outer {kk} z layer(s) top and bottom: {nb3} percolating component(s)")

# enclosed free regions (not connected to any non-cyclic boundary)
lab, n = ndimage.label(F)
touch = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
encl = sum((lab == r).sum() for r in range(1, n + 1) if r not in touch)
print(f"free cells in regions touching no open boundary (periodic wrap ignored): {encl}")

# straight free rows along the wicking axis
rows = F.all(axis=0)
print(f"\nstraight free rows along {args.axis} (whole length): {rows.sum()} of {rows.size}; per z layer: {rows.sum(axis=0)}")
rows_env = (F & env).all(axis=0)
print(f"straight rows of free cells between yarn cells of their column: {rows_env.sum()}")

# bottleneck: largest w such that free cells with local half-width >= w percolate along the wicking axis
# distance from each free cell centre to the nearest yarn cell centre (in cells); the top/bottom planes count as
# walls (padded with porous cells), axis 1 is periodic (wrapped), the wicking axis is open
W = 20
Fz = np.pad(F, ((0, 0), (0, 0), (1, 1)), constant_values=False)
dt = ndimage.distance_transform_edt(np.pad(Fz, ((0, 0), (W, W), (0, 0)), mode="wrap"))[:, W:-W, 1:-1]
for thr in (1, 1.5, 2, 2.5, 3, 4, 5):
    m = F & (dt >= thr)
    nbw, *_ = percolates(m)
    m2 = F & env & (dt >= thr)
    nbw2, *_ = percolates(m2)
    print(f"free cells with distance to the nearest yarn or z plane >= {thr} cells: percolating {nbw} (all free) / {nbw2} (column envelope)")

# initial state
print(f"\nalpha: porous min/max {alpha[P].min():.4g}/{alpha[P].max():.4g}, free min/max {alpha[F].min()}/{alpha[F].max()}")
