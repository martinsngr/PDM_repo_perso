#!/usr/bin/env python3
"""compareTensor.py  -  the tensor K runs (a) `tensorA` and (b) `tensorB` against job 3068 (scalar K, same mesh, BCs and
initial state), and the time scaling of (b) against (a) (README, predictions A1-A5, B1-B4).
    .venv/bin/python -I compareTensor.py <tensorA copy> <tensorB copy> [<ref = ~/PDM_results/REV_midbath_run3068>]
The three meshes are identical (checked on the cell centres 0/C, written with `postProcess -func writeCellCentres
-time 0` if missing). Per write of each run (cached in <run>/compareTensor.npz, recomputed when the writes change):
  - y-yarn front: highest cell centre of the porous cells of yarns 0-4 (along y) with alpha > 0.1 [mm]
  - porous water: sum of eps*alpha over the porous cells [cell volumes]; mean S of the porous cells and of each
    crossing yarn 5-9 (mean alpha of its porous cells)
  - gap water: sum of alpha over the free box cells [cell volumes] (box = between the padding layers)
  - max |U| of the free cells and of the porous cells, alpha min / max
  - waterBudget.csv: water lost through top + bottom [cell volumes], imbalance [m3]
Then: front fits front = k sqrt(t) + c, the time the closed end is reached, the arrival time of the front at each row
(linear between writes) and the B2 test: (b) at t against (a) at S*t, S = Kpar_b/Kpar_a = 0.4245 ((a) interpolated
linearly between its writes), fits of (b) over the windows of (a) divided by S. Last, statistics of the sampled log per
time bin: dt, the limit that sets it (Coats line: dtCoats, dtdS, dtCap), the max |U| implied by the Courant number
(Co*dx/dt, all cells), the wall time per simulated ms."""
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
S = 4.245e-12 / 1e-11          # Kpar of (b) / Kpar of (a); Kperp: 9.20e-13 / 2.2e-12 = 0.418
YARNS = (5, 6, 7, 8, 9)
KEYS = ["front", "porw", "S", "gap", "Ufree", "Upor", "amin", "amax"] + [f"S{k}" for k in YARNS]


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
    return dict(run=run, C=C, n=n, eps=eps, P=P, F=~P, yid=yid, box=box, times=writes(run))


def stats(d, t):
    a = field(f"{d['run']}/{t}/alpha.wetting", d["n"])
    U = field(f"{d['run']}/{t}/U", d["n"], vec=True) if t != "0" else np.zeros((d["n"], 3))
    Um = np.linalg.norm(U, axis=1)
    C, P, F = d["C"], d["P"], d["F"]
    yy = P & (d["yid"] >= 0) & (d["yid"] <= 4) & (a > 0.1)
    r = dict(front=C[yy, 1].max() * 1e3 if yy.any() else np.nan, porw=(d["eps"] * a)[P].sum(), S=a[P].mean(),
             gap=a[F & d["box"]].sum(), Ufree=Um[F].max(), Upor=Um[P].max(), amin=a.min(), amax=a.max())
    for k in YARNS:
        r[f"S{k}"] = a[P & (d["yid"] == k)].mean()
    return r


def series(d):
    """per-write stats of a run, cached in <run>/compareTensor.npz"""
    cache = os.path.join(d["run"], "compareTensor.npz")
    times = ["0"] + d["times"]
    if os.path.isfile(cache):
        z = np.load(cache, allow_pickle=False)
        if list(z["times"]) == times and all(k in z for k in KEYS):
            return {k: z[k] for k in KEYS} | dict(t=np.array([float(x) for x in times]) * 1e3, times=times)
    rows = []
    for t in times:
        rows.append(stats(d, t))
        print(f"  {os.path.basename(d['run'])} {t}", end="\r", file=sys.stderr)
    out = {k: np.array([r[k] for r in rows]) for k in KEYS}
    np.savez(cache, times=np.array(times), **out)
    return out | dict(t=np.array([float(x) for x in times]) * 1e3, times=times)


def budget(run):
    p = os.path.join(run, "waterBudget.csv")
    out = {}
    if os.path.isfile(p):
        for r in csv.DictReader(open(p)):
            out[r["time"]] = r   # a restart repeats a time: keep the last row
    return out


def fit(ts, fr, lo, hi):
    m = (ts >= lo - 1e-9) & (ts <= hi + 1e-9) & np.isfinite(fr)
    if m.sum() < 3:
        return np.nan, np.nan
    k, c = np.polyfit(np.sqrt(ts[m] * 1e-3), fr[m], 1)
    return k, c


def arrival(ts, fr, y):
    """first time the front reaches y [mm] (linear between writes; nan if never)"""
    i = np.nonzero(fr >= y - 1e-6)[0]
    if not i.size:
        return np.nan
    i = i[0]
    if i == 0:
        return ts[0]
    return ts[i - 1] + (ts[i] - ts[i - 1]) * (y - fr[i - 1]) / (fr[i] - fr[i - 1])


def logstats(run, bins):
    path = os.path.join(run, "log.hybridPorousInterFoam")
    name = os.path.basename(run.rstrip("/"))
    if not os.path.isfile(path):
        print(f"\n{name}: no log.hybridPorousInterFoam")
        return
    rec, cur, coats, co, ex = [], None, None, None, None
    for line in open(path, errors="replace"):
        if line.startswith("Time = "):
            cur, coats, co = float(line.split()[2]), None, None
        elif line.startswith("ExecutionTime = ") and cur is not None:
            ex = float(line.split()[2])
        elif line.startswith("Coats CFL Number max:"):
            w = line.split()
            coats = [float(w[w.index(k) + 2]) for k in ("dtCoats", "dtdS", "dtCap", "maxDeltaT")]
        elif line.startswith("Courant Number mean:"):
            co = float(line.split()[-1])
        elif line.startswith("deltaT = ") and cur is not None and coats is not None:
            rec.append((cur, float(line.split()[2]), *coats, co if co is not None else np.nan, ex))
    tail = open(path + ".tail", errors="replace").read() if os.path.isfile(path + ".tail") else ""
    txt = open(path, errors="replace").read()
    stop = [l for l in (txt + tail).splitlines() if l.startswith("stopGuard: ")]
    print(f"\nsampled log {name}: {len(rec)} steps, last t {rec[-1][0]*1e3 if rec else 0:.3f} ms; "
          f"stopGuard: {stop[-1] if stop else 'none'}; 'End' in .tail: {'End' in tail.split()}")
    if not rec:
        return
    r = np.array(rec)
    t, dt, dC, dS, dCap, dMax, Co, ex = r.T
    lim = np.argmin(np.c_[dC, dS, dCap], axis=1)
    atmax = np.abs(dt / dMax - 1) < 0.01
    U = Co * DX / dt
    for lo, hi in bins:
        m = (t * 1e3 >= lo) & (t * 1e3 < hi)
        if not m.any():
            continue
        i0, i1 = np.nonzero(m)[0][[0, -1]]
        cost = (ex[i1] - ex[i0]) / ((t[i1] - t[i0]) * 1e3) if t[i1] > t[i0] else np.nan
        print(f"  {lo:4.1f}-{hi:5.1f} ms: dt median {np.median(dt[m]):.3g} min {dt[m].min():.3g} | limit Coats/dS/cap "
              f"{(lim[m]==0).mean()*100:3.0f}/{(lim[m]==1).mean()*100:3.0f}/{(lim[m]==2).mean()*100:3.0f} %, "
              f"dt at that limit {atmax[m].mean()*100:3.0f} % | max |U| implied median {np.nanmedian(U[m]):.2f} "
              f"max {np.nanmax(U[m]):.2f} m/s | {cost:,.0f} s per ms")
    print(f"  wall time {ex[-1]:,.0f} s (last sampled step)")


def table(name, s, B):
    print(f"\n{name}\n t[ms] | front | porous water | S por | S yarn 5 / 6 / 7 / 8 / 9 | gap water | |U| free / por | "
          "a min / max | lost t+b [cells] | imbalance [m3]")
    for i, t in enumerate(s["times"]):
        b = B.get(t)
        lost = -(float(b["in_top"]) + float(b["in_bottom"])) / V if b else np.nan
        imb = float(b["imbalance"]) if b else np.nan
        print(f"{s['t'][i]:6.2f} | {s['front'][i]:.3f} | {s['porw'][i]:8.0f} | {s['S'][i]:.4f} | "
              + " / ".join(f"{s[f'S{k}'][i]:.3f}" for k in YARNS)
              + f" | {s['gap'][i]:6.0f} | {s['Ufree'][i]:5.2f} / {s['Upor'][i]:5.2f} | "
              f"{s['amin'][i]:.2g} / {s['amax'][i]:.4f} | {lost:7.1f} | {imb:.2g}")


def main():
    runA, runB = sys.argv[1], sys.argv[2]
    ref = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/PDM_results/REV_midbath_run3068")
    R, A, Bd = load(ref), load(runA), load(runB)
    for d in (A, Bd):
        same = d["n"] == R["n"] and np.array_equal(d["C"], R["C"]) and np.array_equal(d["yid"], R["yid"])
        print(f"{d['run']}: {d['n']:,} cells, porous {d['P'].sum():,}, writes {len(d['times'])} "
              f"(last {float(d['times'][-1])*1e3 if d['times'] else 0:.1f} ms); mesh and yarnID = job 3068: {same}")
        if not same:
            sys.exit("meshes differ: this script assumes the job 3068 mesh")
    sR, sA, sB = series(R), series(A), series(Bd)
    ymax = R["C"][:, 1].max() * 1e3
    for name, s, run in (("job 3068 (scalar K 1e-11)", sR, ref), ("tensorA (Kpar 1e-11, Kperp 2.2e-12)", sA, runA),
                         ("tensorB (Kpar 4.245e-12, Kperp 9.20e-13)", sB, runB)):
        table(name, s, budget(run))

    # same-time comparison against job 3068
    print("\nagainst job 3068 at the same time: front difference [mm] | porous water ratio | yarn 6 / 7 S (ref)")
    for name, s in (("tensorA", sA), ("tensorB", sB)):
        print(f" {name}")
        for t in (0.5, 1, 2, 3, 5, 10, 15, 20, 25, 30):
            i, j = np.nonzero(np.isclose(s["t"], t))[0], np.nonzero(np.isclose(sR["t"], t))[0]
            if i.size and j.size:
                i, j = i[0], j[0]
                print(f"  {t:5.1f} ms: {s['front'][i] - sR['front'][j]:+.3f} | {s['porw'][i] / sR['porw'][j]:.3f} | "
                      f"{s['S6'][i]:.3f} / {s['S7'][i]:.3f} ({sR['S6'][j]:.3f} / {sR['S7'][j]:.3f})")

    print("\nfront fit k [mm/sqrt(s)], c [mm] (/ 1D 18.04)")
    for name, s, wins in (("job 3068", sR, [(2, 10), (2, 20), (2, 25)]), ("tensorA", sA, [(2, 10), (2, 20), (2, 25)]),
                          ("tensorB", sB, [(2, 10), (2, 20), (2, 40), (2, 60)])):
        for lo, hi in wins:
            k, c = fit(s["t"], s["front"], lo, hi)
            print(f"  {name:8s} {lo}-{hi} ms: k {k:.2f}, c {c:.3f} ({k/18.04:.3f})")
        m = s["front"] >= ymax - 1e-3
        print(f"  {name:8s} closed end ({ymax:.3f} mm) reached at {s['t'][m].min() if m.any() else np.nan:.1f} ms")

    # B2: (b) at t against (a) at S*t
    print(f"\nB2: tensorB at t against tensorA at {S}*t (tensorA interpolated linearly between its writes)")
    print(" t_b [ms] | S*t_b | front b | front a(S t) | diff [mm] | porous water b / a(S t) | S6 b / a | S7 b / a | gap b / a")
    for i, t in enumerate(sB["t"]):
        ta = S * t
        if t == 0 or ta > sA["t"][-1] + 1e-9:
            continue
        ip = lambda k: np.interp(ta, sA["t"], sA[k])
        if t in (1, 2, 3, 4, 5) or t % 5 == 0:
            print(f" {t:7.1f} | {ta:6.3f} | {sB['front'][i]:.3f} | {ip('front'):.3f} | {sB['front'][i] - ip('front'):+.3f} | "
                  f"{sB['porw'][i] / ip('porw'):.4f} | {sB['S6'][i]:.3f} / {ip('S6'):.3f} | "
                  f"{sB['S7'][i]:.3f} / {ip('S7'):.3f} | {sB['gap'][i]:.0f} / {ip('gap'):.0f}")
    print(" arrival time of the front at y [mm]: t_a, t_b, S*t_b / t_a")
    for y in np.arange(0.7, ymax, 0.2):
        ta, tb = arrival(sA["t"], sA["front"], y), arrival(sB["t"], sB["front"], y)
        print(f"  y {y:.2f}: {ta:6.2f} ms, {tb:6.2f} ms, {S * tb / ta:.3f}")
    print(f" fits of (b) over the windows of (a) / S (exact scaling: k_b / k_a = sqrt(S) = {np.sqrt(S):.4f}, same c)")
    for lo, hi in [(2, 10), (2, 20), (2, 25)]:
        ka, ca = fit(sA["t"], sA["front"], lo, hi)
        kb, cb = fit(sB["t"], sB["front"], lo / S, hi / S)
        print(f"  a {lo}-{hi} ms: {ka:.2f}, {ca:.3f} | b {lo/S:.1f}-{hi/S:.1f} ms: {kb:.2f}, {cb:.3f} | "
              f"k_b / k_a {kb/ka:.4f} ({(kb/ka/np.sqrt(S) - 1)*100:+.1f} %)")

    bins = [(0, 0.5), (0.5, 1), (1, 2), (2, 5), (5, 10), (10, 20), (20, 30.1), (30.1, 40), (40, 50), (50, 60.1)]
    for run in (ref, runA, runB):
        logstats(run, bins)


if __name__ == "__main__":
    main()
