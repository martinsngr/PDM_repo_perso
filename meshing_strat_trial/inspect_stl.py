#!/usr/bin/env python3
"""
inspect_stl.py  -  sanity checks on the TexGen STL + REV detection, before building any fields.

Usage:
    python3 inspect_stl.py yarns.stl 1e-2              # 1e-2 = STL units -> metres (TexGen in cm)
    python3 inspect_stl.py yarns.stl 1e-2 --zgap 0.5   # + 0.5 x fabric thickness of free space above and below

Checks:
  * is each yarn a separate CLOSED (watertight) body?  -> inside/outside test only works if yes
  * yarn count, volume, bounding box, main direction (x or y) of each yarn
  * REV: TexGen exports the boundary yarn at BOTH ends of the repeat, so the periodic REV spans
    from the first to the last yarn centreline in x and in y; in z it spans the fabric (+ optional gap)
  * how much the yarns overlap each other (TexGen interpenetration at crossovers)
  * yarn volume fraction of the REV (compare with the real fabric!)

Writes the REV to rev_domain.json, which build_fields.py reads.
"""
import argparse
import json

import numpy as np
import trimesh

parser = argparse.ArgumentParser(description="Sanity checks on a TexGen STL and REV detection")
parser.add_argument("stl_file")
parser.add_argument("scale", nargs="?", type=float, default=1.0, help="STL units -> metres")
parser.add_argument("--zgap", type=float, default=0.0,
                    help="free space added above and below the fabric, as a fraction of its thickness")
parser.add_argument("--out", default="rev_domain.json", help="file the REV is written to")
args = parser.parse_args()

mesh = trimesh.load(args.stl_file, force="mesh")
mesh.apply_scale(args.scale)
print(f"STL: {args.stl_file}   faces: {len(mesh.faces)}   whole mesh watertight: {mesh.is_watertight}")

bodies = mesh.split(only_watertight=False)
print(f"Number of separate bodies (should be the number of yarns): {len(bodies)}\n")

lo, hi = mesh.bounds
print(f"Bounding box [m]: min {lo}  max {hi}")
print(f"Size [mm]: {(hi - lo) * 1e3}\n")

print(" #  closed   volume[mm3]   main axis   extents x/y/z [mm]")
axes = []                                          # main in-plane axis of each yarn: 0 = x, 1 = y
for i, b in enumerate(bodies):
    ext = b.extents
    axes.append(int(np.argmax(ext[:2])))           # longest in-plane extent
    vol = b.volume if b.is_watertight else float("nan")
    print(f"{i:2d}  {str(b.is_watertight):6s}  {vol * 1e9:11.4f}   along {'xy'[axes[-1]]}    "
          f"{ext[0]*1e3:.3f} / {ext[1]*1e3:.3f} / {ext[2]*1e3:.3f}")

open_bodies = [i for i, b in enumerate(bodies) if not b.is_watertight]
if open_bodies:
    print(f"\n!! Bodies {open_bodies} are NOT closed. The inside test will be wrong for them.")
    print("   Typical cause: yarns trimmed to the domain without capping the cut faces.")
    print("   Fix: export the UNtrimmed yarns from TexGen and let the blockMesh box do the cropping.")

# REV: yarns running along y are spaced in x (and vice versa). The centreline position across a
# yarn is the middle of its bounding box in that direction (crimp is in z, so it does not affect it).
rev_lo, rev_hi = lo.copy(), hi.copy()
print("\nREV detection:")
for across in (0, 1):
    along = 1 - across
    c = np.sort([b.bounds[:, across].mean() for b, a in zip(bodies, axes) if a == along])
    if len(c) < 2:
        print(f"  {'xy'[across]}: fewer than 2 yarns along {'xy'[along]} -> keeping the STL bounding box")
        continue
    gaps = np.diff(c)
    s = np.median(gaps)
    n_sp = int(round((c[-1] - c[0]) / s))
    rev_lo[across], rev_hi[across] = c[0], c[-1]
    print(f"  {'xy'[across]}: {len(c)} yarns along {'xy'[along]}, spacing {s * 1e3:.4f} mm "
          f"({1e-2 / s:.2f} yarns/cm) -> REV = {n_sp} spacings = {(c[-1] - c[0]) * 1e3:.4f} mm")
    if np.max(np.abs(gaps - s)) > 1e-3 * s:
        print(f"  !! yarn spacing is not uniform ({gaps * 1e3} mm) -> check the REV by hand")
    if n_sp % 2:
        print("  !! odd number of spacings -> not periodic for a plain weave (repeat = 2 yarns)")

thickness = hi[2] - lo[2]
rev_lo[2] = lo[2] - args.zgap * thickness
rev_hi[2] = hi[2] + args.zgap * thickness
print(f"  z: fabric thickness {thickness * 1e3:.4f} mm, gap of {args.zgap} x thickness on each side")
print(f"REV [m]: min {rev_lo}  max {rev_hi}")
print(f"REV size [mm]: {(rev_hi - rev_lo) * 1e3}")

with open(args.out, "w") as fh:
    json.dump({"stl_file": args.stl_file, "stl_scale": args.scale, "zgap": args.zgap,
               "min_m": rev_lo.tolist(), "max_m": rev_hi.tolist()}, fh, indent=2)
print(f"-> written to {args.out}")

# Monte Carlo estimate of yarn fraction and overlap inside the REV
N = 100_000
rng = np.random.default_rng(0)
pts = rev_lo + (rev_hi - rev_lo) * rng.random((N, 3))
count = np.zeros(N, dtype=int)
for b in bodies:
    if b.is_watertight:
        count += b.contains(pts)
print(f"\nREV volume: {np.prod(rev_hi - rev_lo) * 1e9:.4f} mm3")
print(f"Yarn volume fraction of REV (Monte Carlo): {np.mean(count >= 1):.3f}")
print(f"Volume where >= 2 yarns overlap:           {np.mean(count >= 2) * 100:.2f} % of REV")
print("\nIf the overlap is more than ~1 %, run TexGen's interference check/correction.")
