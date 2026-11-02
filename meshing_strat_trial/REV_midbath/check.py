#!/usr/bin/env python3
"""check.py  -  run checks of the REV (wicking along y), from the reconstructed fields of every write time.

    python3 check.py [case]          (numpy; run after ./run, or after reconstructPar of a partial run)

Mesh: uniform blocks stacked in z (build_fields.py --zpad), cell counts from system/blockMeshDict; the box (fabric)
layers are the z layers between the padding (zpad read from the yarn-free bottom/top layers). Per write time:
  - alpha bounds in porous (yarn) and free cells
  - max |U| in free cells (gaps, padding), in water-filled free cells (alpha > 0.5) and in porous cells, with the
    position of the free maximum
  - yarn fronts: highest y of porous cells with alpha > 0.1, for the yarns along y (yarnID 0-4) and the
    crossing yarns (5-9); mean saturation of the porous cells
  - gaps: highest y of free box cells with alpha > 0.5 (water column / menisci), water volume in free box cells
  - padding: number of cells with alpha > 0.05 (water outside the fabric box)
  - water budget (waterBudget.csv, same write times): water lost through the open top/bottom faces, imbalance / water
Porous = eps <= 0.99 (hybridPorousInterFoam)."""
import csv
import os
import re
import sys

import numpy as np

case = sys.argv[1] if len(sys.argv) > 1 else "."
bm = open(os.path.join(case, "system/blockMeshDict")).read()
blocks = re.findall(r"hex\s*\([\d\s]+\)\s*\((\d+)\s+(\d+)\s+(\d+)\)", bm)
N = (int(blocks[0][0]), int(blocks[0][1]), sum(int(b[2]) for b in blocks))
NC = int(np.prod(N))


def read(path, vec=False):
    txt = open(path).read()
    body = txt.split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        v = np.array(m.group(1).strip("()").split(), float)
        a = np.tile(v, (NC, 1)) if vec else np.full(NC, v[0])
    else:
        n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
        data = body.split("(", 1)[1]
        if vec:
            a = np.array(re.findall(r"\(([^()]+)\)", data)[:n])
            a = np.array([s.split() for s in a], float)
        else:
            a = np.array(data.split(")", 1)[0].split()[:n], float)
    return a.reshape(N + ((3,) if vec else ()), order="F") if not vec else \
        a.reshape(N[2], N[1], N[0], 3).transpose(2, 1, 0, 3)


eps = read(os.path.join(case, "0/eps"))
yid = read(os.path.join(case, "0/yarnID"))
P = eps <= 0.99
F = ~P
nzb = [int(b[2]) for b in blocks]
zpad = nzb[0] if len(nzb) == 3 else 0
box = np.zeros(N, bool)
box[:, :, zpad:N[2] - zpad] = True
pad = ~box
# cell centres of the uniform grid (vertices from blockMeshDict)
v = np.array([[float(x) for x in l.split()] for l in
              re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", bm.split("vertices", 1)[1].split(");", 1)[0])])
lo, hi = v.min(axis=0), v.max(axis=0)
d = (hi - lo) / np.array(N)
yc = lo[1] + (np.arange(N[1]) + 0.5) * d[1]
Y = np.broadcast_to(yc[None, :, None], N)
along = P & (yid >= 0) & (yid <= 4)
cross = P & (yid >= 5)
V = np.prod(d)

times = sorted((t for t in os.listdir(case) if re.fullmatch(r"[0-9.e+-]+", t) and t != "0"
                and os.path.isfile(os.path.join(case, t, "alpha.wetting"))), key=float)
print(f"mesh {N[0]} x {N[1]} x {N[2]}, padding {zpad} layers, porous {P.sum():,}, free box {(F & box).sum():,}, "
      f"padding {pad.sum():,}")
hdr = ("t [ms]", "a por min/max", "a free min/max", "|U| free", "at y,z [mm]", "|U| water", "|U| por",
       "front y-yarns", "front x-yarns", "S por", "gap water y", "gap water [cells]", "pad cells", "lost top+bottom [cells]")
wb = os.path.join(case, "waterBudget.csv")
budget = {r["time"]: r for r in csv.DictReader(open(wb))} if os.path.isfile(wb) else {}
print(" | ".join(hdr))


def front(mask, a):
    m = mask & (a > 0.1)
    return Y[m].max() * 1e3 if m.any() else float("nan")


for t in ["0"] + times:
    a = read(os.path.join(case, t, "alpha.wetting"))
    if t == "0":
        Um = np.zeros(N)
    else:
        U = read(os.path.join(case, t, "U"), vec=True)
        Um = np.linalg.norm(U, axis=3)
    iF = np.unravel_index(np.argmax(np.where(F, Um, -1)), N)
    gw = F & box & (a > 0.5)
    water = F & (a > 0.5)
    r = budget.get(t)
    lost = (-(float(r["in_top"]) + float(r["in_bottom"])) / V) if r and "in_top" in r else float("nan")
    print(f"{float(t)*1e3:7.3f} | {a[P].min():.3g}/{a[P].max():.4f} | {a[F].min():.2g}/{a[F].max():.4f} | "
          f"{Um[F].max():6.3f} | {yc[iF[1]]*1e3:.2f},{(lo[2] + (iF[2] + 0.5) * d[2])*1e3:.3f} | "
          f"{(Um[water].max() if water.any() else 0):6.3f} | "
          f"{Um[P].max():6.3f} | {front(along, a):6.3f} | {front(cross, a):6.3f} | {a[P].mean():.4f} | "
          f"{(Y[gw].max()*1e3 if gw.any() else float('nan')):6.3f} | {(a[F & box]).sum():9.1f} | "
          f"{int((pad & (a > 0.05)).sum())} | {lost:.3g}")

if os.path.isfile(wb):
    rows = list(csv.DictReader(open(wb)))
    if rows:
        r = rows[-1]
        w = float(r["water_m3"])
        print(f"\nwater budget at t = {r['time']}: water {w:.4e} m3, inflow {float(r['in_total']):.4e} m3, "
              f"imbalance {float(r['imbalance']):.3e} m3 ({float(r['imbalance'])/w:.2e} of the water); "
              f"max |imbalance| over the writes {max(abs(float(x['imbalance'])) for x in rows):.3e} m3")
