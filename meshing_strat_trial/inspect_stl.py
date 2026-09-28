#!/usr/bin/env python3
"""
01_inspect_stl.py  -  sanity checks on the TexGen STL before building any fields.

Usage:
    python3 01_inspect_stl.py yarns.stl 1e-3          # 1e-3 = STL units -> metres (TexGen in mm)

Checks:
  * is each yarn a separate CLOSED (watertight) body?  -> inside/outside test only works if yes
  * yarn count, volume, bounding box, main direction (x or y) of each yarn
  * how much the yarns overlap each other (TexGen interpenetration at crossovers)
  * yarn volume fraction of the domain (compare with the real fabric!)

Requires: pip install numpy trimesh rtree      (optional, much faster: pip install embreex)
"""
import sys
import numpy as np
import trimesh

stl_file = sys.argv[1]
scale = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

mesh = trimesh.load(stl_file, force="mesh")
mesh.apply_scale(scale)
print(f"STL: {stl_file}   faces: {len(mesh.faces)}   whole mesh watertight: {mesh.is_watertight}")

bodies = mesh.split(only_watertight=False)
print(f"Number of separate bodies (should be the number of yarns): {len(bodies)}\n")

lo, hi = mesh.bounds
print(f"Bounding box [m]: min {lo}  max {hi}")
print(f"Size [mm]: {(hi - lo) * 1e3}\n")

print(" #  closed   volume[mm3]   main axis   extents x/y/z [mm]")
total_vol = 0.0
for i, b in enumerate(bodies):
    ext = b.extents
    axis = "xyz"[int(np.argmax(ext[:2]))]          # longest in-plane extent
    vol = b.volume if b.is_watertight else float("nan")
    total_vol += 0.0 if np.isnan(vol) else vol
    print(f"{i:2d}  {str(b.is_watertight):6s}  {vol * 1e9:11.4f}   along {axis}    "
          f"{ext[0]*1e3:.3f} / {ext[1]*1e3:.3f} / {ext[2]*1e3:.3f}")

open_bodies = [i for i, b in enumerate(bodies) if not b.is_watertight]
if open_bodies:
    print(f"\n!! Bodies {open_bodies} are NOT closed. The inside test will be wrong for them.")
    print("   Typical cause: yarns trimmed to the domain without capping the cut faces.")
    print("   Fix: export the UNtrimmed yarns from TexGen and let the blockMesh box do the cropping.")

# Monte Carlo estimate of yarn fraction and overlap inside the bounding box
N = 100_000
rng = np.random.default_rng(0)
pts = lo + (hi - lo) * rng.random((N, 3))
count = np.zeros(N, dtype=int)
for b in bodies:
    if b.is_watertight:
        count += b.contains(pts)
dom_vol = np.prod(hi - lo)
print(f"\nDomain (bounding box) volume: {dom_vol * 1e9:.4f} mm3")
print(f"Sum of yarn volumes:          {total_vol * 1e9:.4f} mm3")
print(f"Yarn volume fraction of domain (Monte Carlo): {np.mean(count >= 1):.3f}")
print(f"Volume where >= 2 yarns overlap:             {np.mean(count >= 2) * 100:.2f} % of domain")
print("\nIf the overlap is more than ~1 %, run TexGen's interference check/correction.")
print("If you exported untrimmed yarns, the bounding box is larger than your REV:")
print("the fractions above are then for the bounding box, not for the REV.")