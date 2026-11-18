#!/usr/bin/env python3
"""horizUptake.py <run> [--layers] [time ...]  -  through-thickness runs (cases/horizontal, horizB_*): per write the water
taken up above the bath surface (g/m2 of fabric, split yarns / gaps), the yarn mean saturation, the gap fill, the bath state
(air in the bath rows, bath cells under the yarn crests still water), the water out through the top, max alpha and the
fastest free fabric cell; then the time step and its limits from the solver log. --layers adds, every 1 ms and at the last
write, the free-cell water fraction (alpha > 0.5, as zLayers.py) and the yarn mean S of each fabric z layer.

Mesh: the three-block blockMeshDict of build_fields.py --wick-axis z --zpad N (bath rows | fabric box | air rows, cells
numbered block by block, x fastest, then y, then z), so 0/C is not needed (Allpre deletes it). Uptake = water above the bath
surface (fabric box + air rows) minus its value at t = 0 (removes the initial contact ramp, ~4.2 g/m2), as in study 2f.
Yarn cells: eps <= 0.99. Checked against study 2f R3b (~/PDM_results/study2f_R3b_ramp)."""
import csv
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # analyseCut.py (field) in this folder
from analyseCut import field  # noqa: E402

RHO = 1000.0
args = [a for a in sys.argv[1:] if not a.startswith("--")]
LAYERS = "--layers" in sys.argv
run = args[0]
times = args[1:] or sorted((x for x in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0"
                            and os.path.isfile(os.path.join(run, x, "alpha.wetting"))), key=float)

# --- mesh from blockMeshDict: blocks (nx ny nz) and the z levels of the vertices
bm = open(os.path.join(run, "system", "blockMeshDict")).read()
verts = np.array(re.findall(r"\(\s*([-0-9.e+]+)\s+([-0-9.e+]+)\s+([-0-9.e+]+)\s*\)",
                            bm.split("vertices", 1)[1].split(");", 1)[0]), float)
blocks = [tuple(map(int, b)) for b in re.findall(r"hex\s*\([^)]*\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", bm)]
assert len(blocks) == 3 and len({b[:2] for b in blocks}) == 1, f"expected 3 stacked blocks, got {blocks}"
nx, ny = blocks[0][:2]
nb, nf, na = (b[2] for b in blocks)                  # bath rows, fabric box layers, air rows
zl = np.unique(np.round(verts[:, 2], 12))
assert len(zl) == 4, zl
Lx, Ly = np.ptp(verts[:, 0]), np.ptp(verts[:, 1])
A = Lx * Ly
vol = np.concatenate([np.full(nx * ny * n, Lx / nx * Ly / ny * (zl[k + 1] - zl[k]) / n) for k, n in enumerate((nb, nf, na))])
n = len(vol)
iz = np.repeat(np.arange(nb + nf + na), nx * ny)     # z layer of each cell, 0 = bottom bath row
vbox = vol[nb * nx * ny]                             # one fabric cell [m3]

eps = field(os.path.join(run, "0", "eps"), n)
P = eps <= 0.99                                      # yarn cells
F = ~P
box = (iz >= nb) & (iz < nb + nf)
above = iz >= nb                                     # above the bath surface
bath = iz < nb
crest = P & (iz == nb)                               # yarn cells of the first fabric layer (the crests on the bath)
crestBath = np.where(crest)[0] - nx * ny             # the bath cells right under them
gpm2 = RHO * 1e3 / A                                 # kg/m3 * g/kg / m2: g/m2 per m3 of water

def water(a, mask):
    return float(np.sum(a[mask] * eps[mask] * vol[mask]))

# initial water, capacities
a0 = field(os.path.join(run, "0", "alpha.wetting"), n)
W0 = {k: water(a0, m) for k, m in (("above", above), ("yarn", P & box), ("gap", F & box))}
print(f"{run}: {n:,} cells ({nx} x {ny} x {nb}+{nf}+{na}), fabric box: yarn cells {np.sum(P & box):,}, free {np.sum(F & box):,}; "
      f"crest cells on the bath {crest.sum()}")
print(f"capacity [g/m2]: yarns {water(np.ones(n), P & box) * gpm2:.1f}, free box cells {water(np.ones(n), F & box) * gpm2:.1f}; "
      f"initial water above the bath surface {W0['above'] * gpm2:.2f} (yarns {W0['yarn'] * gpm2:.2f})")

# water out through the top (waterBudget.csv, cumulative m3, negative = out)
budget = {}
bpath = os.path.join(run, "waterBudget.csv")
if os.path.isfile(bpath):
    for r in csv.DictReader(open(bpath)):
        budget[float(r["time"])] = r

def budgetAt(t):
    if not budget:
        return None
    k = min(budget, key=lambda x: abs(x - t))
    return budget[k] if abs(k - t) < 1e-9 + 1e-6 * t else None

print("\n t[ms] | uptake g/m2 (yarns / gaps) | yarn S | gap fill vol / cells>0.5 | bath air [cells] | crest bath water"
      " | out top [cells] | imbalance m3 | max alpha | fastest free fabric |U| m/s")
layerRows = []
for t in times:
    a = field(os.path.join(run, t, "alpha.wetting"), n)
    U = field(os.path.join(run, t, "U"), n, vec=True)
    up = (water(a, above) - W0["above"]) * gpm2
    uy = (water(a, P & box) - W0["yarn"]) * gpm2
    ug = (water(a, F & box) - W0["gap"]) * gpm2
    S = a[P & box].mean()
    gvol = a[F & box].mean()
    gcells = np.mean(a[F & box] > 0.5)
    bair = np.sum((1 - a[bath]) * vol[bath]) / vbox
    cb = np.sum(a[crestBath] > 0.5)
    um = np.linalg.norm(U[F & box], axis=1).max()
    b = budgetAt(float(t))
    top = f"{-float(b['in_top']) / vbox:8.2f}" if b else "     n/a"
    imb = f"{float(b['imbalance']):9.2e}" if b else "      n/a"
    print(f" {float(t) * 1e3:5.2f} | {up:6.1f} ({uy:5.1f} / {ug:5.1f}) | {S:.3f} | {gvol:.3f} / {gcells:.3f} | {bair:8.1f} | "
          f"{cb:4d} of {crest.sum()} | {top} | {imb} | {a.max():.5f} | {um:5.2f}")
    if LAYERS:
        layerRows.append((float(t), [np.mean(a[F & (iz == k)] > 0.5) if np.any(F & (iz == k)) else np.nan
                                     for k in range(nb, nb + nf)],
                          [a[P & (iz == k)].mean() if np.any(P & (iz == k)) else np.nan for k in range(nb, nb + nf)]))

if LAYERS and layerRows:
    keep = [r for i, r in enumerate(layerRows)
            if i == len(layerRows) - 1 or abs(r[0] * 1e3 - round(r[0] * 1e3)) < 1e-6]
    hdr = " ".join(f"{k:5d}" for k in range(nb, nb + nf))
    print(f"\nfree-cell water fraction (alpha > 0.5) per fabric z layer, bottom to top (layers {nb}-{nb + nf - 1}):")
    print(f" t[ms] | {hdr}")
    for t, fw, _ in keep:
        print(f" {t * 1e3:5.2f} | " + " ".join(f"{x:5.2f}" for x in fw))
    print("yarn mean S per fabric z layer:")
    print(f" t[ms] | {hdr}")
    for t, _, sy in keep:
        print(f" {t * 1e3:5.2f} | " + " ".join(f"{x:5.2f}" for x in sy))

# --- time step and its limits from the solver log (every LOG_EVERY-th step + the .tail)
rows, t, dt, last = [], None, None, ""
for name in ("log.hybridPorousInterFoam", "log.hybridPorousInterFoam.tail"):
    path = os.path.join(run, name)
    if not os.path.isfile(path):
        continue
    co = None
    for line in open(path, errors="replace"):
        if line.startswith("Courant Number"):
            co = float(line.split()[-1])
        elif line.startswith("deltaT = "):
            dt = float(line.split()[2])
        elif line.startswith("Time = "):
            t = float(line.split()[2])
            if dt is not None and co is not None:
                rows.append((t, dt, co * vbox ** (1 / 3) / dt))
        elif line.startswith("stopGuard"):
            print(line.strip())
        elif line.startswith("ExecutionTime"):
            last = line.strip()
if rows:
    r = np.array(sorted(set(rows)))
    print(f"\nlog: {len(r)} sampled steps to t = {r[-1, 0] * 1e3:.3f} ms; {last}")
    print(" window [ms] | dt median / min [s] | fastest cell (log Courant, all cells) median / max [m/s]")
    edges = np.arange(0, r[-1, 0] + 1e-3, 1e-3)
    for lo in edges:
        m = (r[:, 0] >= lo) & (r[:, 0] < lo + 1e-3)
        if m.any():
            print(f" {lo * 1e3:4.0f}-{lo * 1e3 + 1:<4.0f} | {np.median(r[m, 1]):.2e} / {r[m, 1].min():.2e} | "
                  f"{np.median(r[m, 2]):5.2f} / {r[m, 2].max():5.2f}")
