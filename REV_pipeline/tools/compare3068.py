#!/usr/bin/env python3
"""compare3068.py  -  a bath-layer run of study 2e against job 3068 (REV_midbath), on the cells above the bath plane.
    .venv/bin/python -I compare3068.py <run> [<ref = ~/PDM_results/REV_midbath_run3068>]
Works on any mesh (subsetMesh of Bbox_*): cells are matched by their centre (0/C; written with
`postProcess -func writeCellCentres -time 0` if missing). Bath plane y0 = lowest cell face of the reference.
Fabric box = z between the padding layers (z vertices of system/blockMeshDict). Per write of the run:
  - y-yarn front (yarnID 0-4, alpha > 0.1), porous water (sum of eps*alpha over the porous cells, cell volumes) and its
    ratio to the reference at the same time
  - gap water (free box cells above y0, sum of alpha) and padding water (free padding cells above y0)
  - first fabric row: free box cells of the row just above y0 at alpha > 0.5 (of all free cells of that row)
  - yarn band of the bath plane (z of the yarn cells of the first fabric row): its first-row free cells at alpha > 0.5,
    its gap water, and the water in the open space beside the yarns (free box cells above y0 outside the band)
  - layer (cells below y0): min alpha
  - max |U| of free box cells, padding cells (above y0) and porous cells
  - waterBudget.csv: lost through top/bottom in cell volumes, inlet inflow, flux through bathWall, imbalance
Then the front fits front = k sqrt(t) + c over 2-10 / 2-20 / 2-25 ms for both runs and the time the closed end is
reached, and dt / max |U| statistics of the sampled log (coatsTimeStep, dsLocator lines)."""
import csv
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # analyseCut.py (field, rlist) in this folder
from analyseCut import field, rlist  # noqa: E402

DX = 20e-6
V = DX ** 3


def writes(run):
    return sorted((x for x in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0"
                   and os.path.isfile(os.path.join(run, x, "alpha.wetting"))), key=float)


def load(run):
    if not os.path.isfile(f"{run}/0/C"):
        subprocess.run(["postProcess", "-func", "writeCellCentres", "-time", "0"], cwd=run,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    C, _ = rlist(f"{run}/0/C", vec=True)
    n = len(C)
    eps = field(f"{run}/0/eps", n)
    P = eps <= 0.99
    yid = field(f"{run}/0/yarnID", n)
    v = open(f"{run}/system/blockMeshDict").read().split("vertices", 1)[1].split(");", 1)[0]
    zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", v)})
    box = (C[:, 2] > zv[1]) & (C[:, 2] < zv[2])
    key = np.round(C / 1e-6).astype(np.int64)
    nbox = int(re.findall(r"hex \(4 5 6 7 8 9 10 11\) \(\d+ \d+ (\d+)\)", open(f"{run}/system/blockMeshDict").read())[0])
    return dict(run=run, C=C, n=n, eps=eps, P=P, F=~P, yid=yid, box=box, key=key, times=writes(run),
                dz=(zv[2] - zv[1]) / nbox)


def budget(run):
    p = os.path.join(run, "waterBudget.csv")
    if not os.path.isfile(p):
        return {}
    out = {}
    for r in csv.DictReader(open(p)):
        out[r["time"]] = r  # a restart repeats a time: keep the last row
    return out


def stats(d, t, sel=None):
    a = field(f"{d['run']}/{t}/alpha.wetting", d["n"])
    U = field(f"{d['run']}/{t}/U", d["n"], vec=True)
    Um = np.linalg.norm(U, axis=1)
    C, P, F, box = d["C"], d["P"], d["F"], d["box"]
    above = C[:, 1] > d["y0"]
    if sel is not None:
        above &= sel
    yy = P & (d["yid"] >= 0) & (d["yid"] <= 4) & (a > 0.1)
    row = F & box & (np.abs(C[:, 1] - d["yrow"]) < DX / 4)
    r = dict(
        front=C[yy, 1].max() * 1e3 if yy.any() else np.nan,
        porw=(d["eps"] * a)[P].sum(),
        S=a[P].mean(),
        gap=a[F & box & above].sum(),
        pad=a[F & ~box & above].sum(),
        row1=(row & (a > 0.5)).sum(), nrow1=row.sum(),
        brow1=(row & d["band"] & (a > 0.5)).sum(), nbrow1=(row & d["band"]).sum(),
        bgap=a[F & box & above & d["band"]].sum(), open_=a[F & box & above & ~d["band"]].sum(),
        layer=a[~above & (C[:, 1] < d["y0"])].min() if (C[:, 1] < d["y0"]).any() else np.nan,
        Ubox=Um[F & box & above].max(), Upad=Um[F & ~box & above].max() if (F & ~box & above).any() else 0,
        Upor=Um[P].max(), amax=a.max(), amin=a.min(),
    )
    return r


def logstats(run):
    path = os.path.join(run, "log.hybridPorousInterFoam")
    if not os.path.isfile(path):
        return
    t, dt, um = [], [], []
    cur = None
    for line in open(path, errors="replace"):
        if line.startswith("Time = "):
            cur = float(line.split()[2])
        elif line.startswith("deltaT = ") and cur is not None:
            t.append(cur)
            dt.append(float(line.split()[2]))
        elif " uLoc " in line:
            w = line.split()
            w = w[w.index("uLoc") + 1:]
            um.append((float(w[0]), float(w[2])))
    t, dt = np.array(t), np.array(dt)
    um = np.array(um) if um else np.zeros((0, 2))
    txt = open(path, errors="replace").read()
    tail = open(path + ".tail", errors="replace").read() if os.path.isfile(path + ".tail") else ""
    stop = [l for l in (txt + tail).splitlines() if l.startswith("stopGuard: ")]
    end = "\nEnd" in tail
    print(f"\nsampled log {os.path.basename(run)}: {t.size} steps, last t {t.max()*1e3 if t.size else 0:.3f} ms; "
          f"stopGuard: {stop[-1] if stop else 'none'}; 'End' in .tail: {end}")
    for lo, hi in [(0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30.1)]:
        m = (t * 1e3 >= lo) & (t * 1e3 < hi)
        mu = (um[:, 0] * 1e3 >= lo) & (um[:, 0] * 1e3 < hi) if um.size else np.zeros(0, bool)
        if m.any():
            print(f"  {lo:4.1f}-{hi:4.1f} ms: dt median {np.median(dt[m]):.3g} min {dt[m].min():.3g} "
                  f"(< 5e-8: {(dt[m] < 5e-8).mean()*100:.1f} %)"
                  + (f" | uLoc max |U| median {np.median(um[mu,1]):.2f} max {um[mu,1].max():.2f} m/s" if mu.any() else ""))


def fit(ts, fr, lo, hi):
    m = (ts >= lo) & (ts <= hi + 1e-9) & np.isfinite(fr)
    if m.sum() < 3:
        return np.nan, np.nan
    k, c = np.polyfit(np.sqrt(ts[m] * 1e-3), fr[m], 1)
    return k, c


def main():
    run = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/PDM_results/REV_midbath_run3068")
    R, D = load(ref), load(run)
    y0 = R["C"][:, 1].min() - DX / 2
    for d in (R, D):
        d["y0"] = y0
        d["yrow"] = y0 + DX / 2
    # check: same cells above y0
    kr = {tuple(k) for k in R["key"]}
    kd = {tuple(k) for k, y in zip(D["key"], D["C"][:, 1]) if y > y0}
    print(f"run {run}: {D['n']:,} cells ({(D['C'][:,1] < y0).sum():,} below y0 = {y0*1e3:.4f} mm), porous {D['P'].sum():,}; "
          f"ref {R['n']:,} cells; cells above y0 matched: {len(kr & kd):,} of {len(kr):,} / {len(kd):,}")
    eps_r = field(f"{ref}/0/eps", R["n"])
    eps_d = field(f"{run}/0/eps", D["n"])
    idx = {tuple(k): i for i, k in enumerate(D["key"])}
    mi = np.array([idx.get(tuple(k), -1) for k in R["key"]])   # -1: no cell there (graded padding, cut domain)
    ok = mi >= 0
    mi = mi[ok]
    a0r = field(f"{ref}/0/alpha.wetting", R["n"])[ok]
    a0d = field(f"{run}/0/alpha.wetting", D["n"])
    print(f"  0/ on the {ok.sum():,} cells at job 3068 cell centres, max |difference|: eps {np.abs(eps_r[ok] - eps_d[mi]).max():.3g}, "
          f"yarnID {np.abs(R['yid'][ok] - D['yid'][mi]).max():.3g}, alpha {np.abs(a0r - a0d[mi]).max():.3g} "
          "(band cases: alpha 0 by design in the open space beside the yarns)")

    B, BR = budget(run), budget(ref)
    rtimes = set(R["times"])
    print("\n t[ms] | front y-yarns (ref) | porous water [cells] (x ref) | gap water (ref) | pad water | row1 water | "
          "layer min a | |U| box / pad / por | a min/max | lost t+b [cells] (ref) | inlet in [m3] | bathWall | imbalance"
          " || band row1 water | band gap water (ref) | open space beside the yarns (ref)")
    # yarn band of the bath plane (band cases: the bath lies only under it): z of the yarn cells of the first fabric row
    for d in (R, D):
        r1 = d["P"] & (np.abs(d["C"][:, 1] - d["yrow"]) < DX / 4)
        zlo, zhi = d["C"][r1, 2].min() - d["dz"] / 2, d["C"][r1, 2].max() + d["dz"] / 2
        d["band"] = (d["C"][:, 2] > zlo) & (d["C"][:, 2] < zhi)
    print(f"  yarn band of the bath plane: z {zlo*1e3:.4f} to {zhi*1e3:.4f} mm")
    rows = []
    for t in ["0"] + D["times"]:
        s = stats(D, t) if t != "0" else None
        if s is None:
            continue
        sr = stats(R, t) if t in rtimes else None
        b, br = B.get(t), BR.get(t)
        lost = -(float(b["in_top"]) + float(b["in_bottom"])) / V if b else np.nan
        lostr = -(float(br["in_top"]) + float(br["in_bottom"])) / V if br else np.nan
        rows.append((float(t) * 1e3, s["front"], sr["front"] if sr else np.nan))
        print(f"{float(t)*1e3:6.2f} | {s['front']:.3f} ({sr['front'] if sr else np.nan:.3f}) | "
              f"{s['porw']:8.0f} ({s['porw']/sr['porw'] if sr else np.nan:.3f}) | {s['gap']:7.0f} ({sr['gap'] if sr else np.nan:5.0f}) | "
              f"{s['pad']:6.0f} | {s['row1']}/{s['nrow1']} | {s['layer']:.3f} | "
              f"{s['Ubox']:.2f} / {s['Upad']:.2f} / {s['Upor']:.2f} | {s['amin']:.2g}/{s['amax']:.4f} | "
              f"{lost:8.1f} ({lostr:.1f}) | {float(b['in_inlet']) if b else np.nan:.3e} | "
              f"{float(b['in_bathWall']) if b else np.nan:.2g} | {float(b['imbalance']) if b else np.nan:.2g}"
              f" || {s['brow1']}/{s['nbrow1']} | {s['bgap']:6.0f} ({sr['bgap'] if sr else np.nan:5.0f}) | "
              f"{s['open_']:6.0f} ({sr['open_'] if sr else np.nan:5.0f})")
    rows = np.array(rows)
    print("\nfront fit k [mm/sqrt(s)], c [mm]:  run | ref")
    for lo, hi in [(2, 10), (2, 20), (2, 25)]:
        k, c = fit(rows[:, 0], rows[:, 1], lo, hi)
        kr_, cr = fit(rows[:, 0], rows[:, 2], lo, hi)
        print(f"  {lo}-{hi} ms: {k:.2f}, {c:.3f} | {kr_:.2f}, {cr:.3f}  (ratio {k/kr_:.3f}; / 1D 18.04: {k/18.04:.3f})")
    ymax = D["C"][:, 1].max() * 1e3
    for name, col in (("run", 1), ("ref", 2)):
        m = rows[:, col] >= ymax - 1e-3
        print(f"  closed end ({ymax:.3f} mm) reached by {name} at {rows[m,0].min() if m.any() else np.nan:.1f} ms")
    logstats(run)


if __name__ == "__main__":
    main()
