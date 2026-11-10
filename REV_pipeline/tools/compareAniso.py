#!/usr/bin/env python3
"""compareAniso.py  -  the yarn-only anisoImpesFoam runs (`anisoA`, `anisoA_mu100`) against `tensorA` (README, X1-X4).
    .venv/bin/python -I compareAniso.py <tensorA copy> <anisoA copy> [<anisoA_mu100 copy>]
The aniso mesh is tensorA's mesh after subsetMesh of the yarn cells (eps <= 0.99), which keeps them in their original
order: cell i of the aniso case = the i-th porous cell of tensorA (checked on eps, yarnID, fYarn). Per write common to the
runs: y-yarn front (yarns 0-4, S > 0.1, highest cell centre [mm]), yarn water (sum eps*S, cell volumes), mean S of each
crossing yarn 6-9, S bounds (NaN check), and cell by cell the mean |S_aniso - alpha_tensorA|. Then front fits
front = k sqrt(t) + c, row-mean S profiles along y at a few times, and the sampled log statistics of the aniso runs
(dt, Coats CFL, wall time per simulated ms)."""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyseCut import field, rlist  # noqa: E402

YARNS = (6, 7, 8, 9)


def writes(run, name):
    return sorted((x for x in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0"
                   and os.path.isfile(os.path.join(run, x, name))), key=float)


def fit(ts, fr, lo, hi):
    m = (ts >= lo - 1e-9) & (ts <= hi + 1e-9) & np.isfinite(fr)
    if m.sum() < 3:
        return np.nan, np.nan
    return np.polyfit(np.sqrt(ts[m] * 1e-3), fr[m], 1)


def logstats(run):
    path = os.path.join(run, "log.anisoImpesFoam")
    rec, cur, ex, smin, smax = [], None, np.nan, np.nan, np.nan
    for line in open(path, errors="replace"):
        if line.startswith("Time = "):
            cur = float(line.split()[2])
        elif line.startswith("Saturation b:"):
            w = line.replace("=", " ").split()
            smin, smax = float(w[w.index("Min(Sb)") + 1]), float(w[w.index("Max(Sb)") + 1])
        elif line.startswith("ExecutionTime = "):
            ex = float(line.split()[2])
        elif line.startswith("deltaT = ") and cur is not None:
            rec.append((cur, float(line.split()[2]), ex, smin, smax))
    r = np.array(rec)
    t, dt, ex, s0, s1 = r.T
    tail = open(path + ".tail", errors="replace").read() if os.path.isfile(path + ".tail") else ""
    print(f"\nsampled log {os.path.basename(run.rstrip('/'))}: {len(r)} steps, last t {t[-1]*1e3:.3f} ms, wall {ex[-1]:,.0f} s; "
          f"'End' in .tail: {'End' in tail.split()}; Sb over the sampled steps [{np.nanmin(s0):.4g}, {np.nanmax(s1):.4g}]")
    for lo, hi in [(0, 0.5), (0.5, 2), (2, 5), (5, 10), (10, 20), (20, 30.1)]:
        m = (t * 1e3 >= lo) & (t * 1e3 < hi)
        if m.sum() > 1:
            i0, i1 = np.nonzero(m)[0][[0, -1]]
            print(f"  {lo:4.1f}-{hi:4.1f} ms: dt median {np.median(dt[m]):.3g} min {dt[m].min():.3g} | "
                  f"{(ex[i1] - ex[i0]) / ((t[i1] - t[i0]) * 1e3):,.0f} s per ms")


def main():
    tA = sys.argv[1]
    runs = sys.argv[2:]
    C, _ = rlist(f"{tA}/0/C", vec=True)
    n = len(C)
    eps = field(f"{tA}/0/eps", n)
    P = eps <= 0.99
    idx = np.nonzero(P)[0]
    Cp, epsP = C[idx], eps[idx]
    yidP = field(f"{tA}/0/yarnID", n)[idx]
    fyP = field(f"{tA}/0/fYarn", n)[idx]
    m = len(idx)
    for r in runs:
        ok = all(np.array_equal(field(f"{r}/0/{k}", m), v) for k, v in (("eps", epsP), ("yarnID", yidP), ("fYarn", fyP)))
        print(f"{r}: {m:,} cells; eps, yarnID, fYarn = tensorA's porous cells in order: {ok}")
        if not ok:
            sys.exit("cell order differs")
    common = sorted(set(writes(tA, "alpha.wetting")).intersection(*[writes(r, "Sb") for r in runs]), key=float)
    t = np.array([0.0] + [float(x) * 1e3 for x in common])
    yy = (yidP >= 0) & (yidP <= 4)
    rows = np.round((Cp[:, 1] - Cp[:, 1].min()) / 20e-6).astype(int)
    yrow = Cp[:, 1].min() * 1e3 + np.arange(rows.max() + 1) * 0.02

    def stats(S):
        w = yy & (S > 0.1)
        d = dict(front=Cp[w, 1].max() * 1e3 if w.any() else np.nan, water=(epsP * S).sum(),
                 smin=np.nanmin(S), smax=np.nanmax(S), nan=int(np.isnan(S).sum()))
        for k in YARNS:
            d[f"S{k}"] = S[yidP == k].mean()
        return d

    names = ["tensorA"] + [os.path.basename(r.rstrip("/")) for r in runs]
    res = {k: [] for k in names}
    prof = {k: {} for k in names}
    dif = {k: [] for k in names[1:]}
    for tt in ["0"] + common:
        a = field(f"{tA}/{tt}/alpha.wetting", n)[idx]
        res["tensorA"].append(stats(a))
        if tt in ("0.002", "0.01", "0.02", "0.03"):
            prof["tensorA"][tt] = np.bincount(rows, a) / np.bincount(rows)
        for r, nm in zip(runs, names[1:]):
            S = field(f"{r}/{tt}/Sb", m)
            res[nm].append(stats(S))
            dif[nm].append(np.abs(S - a).mean())
            if tt in ("0.002", "0.01", "0.02", "0.03"):
                prof[nm][tt] = np.bincount(rows, S) / np.bincount(rows)
        print(f"  {tt}", end="\r", file=sys.stderr)

    print("\n t[ms] | front [mm]: " + " / ".join(names) + " | yarn water [cells]: " + " / ".join(names)
          + " | ratio | S6, S7: " + " / ".join(names) + " | mean |S - a_tensorA| | S min / max (NaN) of the aniso runs")
    for i, tt in enumerate(t):
        if not (tt in (0, 0.5, 1, 1.5, 2, 3, 5) or tt % 5 == 0):
            continue
        R = [res[k][i] for k in names]
        print(f"{tt:6.1f} | " + " / ".join(f"{r['front']:.3f}" for r in R) + " | "
              + " / ".join(f"{r['water']:6.0f}" for r in R) + " | "
              + " / ".join(f"{r['water'] / R[0]['water']:.3f}" for r in R[1:]) + " | "
              + " / ".join(f"{r['S6']:.3f}, {r['S7']:.3f}" for r in R) + " | "
              + " / ".join(f"{dif[k][i]:.4f}" for k in names[1:]) + " | "
              + " / ".join(f"{r['smin']:.4g} / {r['smax']:.4g} ({r['nan']})" for r in R[1:]))
    print("\nfront fit k [mm/sqrt(s)], c [mm] (ratio to tensorA)")
    for lo, hi in [(2, 10), (2, 20), (2, 25)]:
        ks = [fit(t, np.array([r["front"] for r in res[k]]), lo, hi) for k in names]
        print(f"  {lo}-{hi} ms: " + " | ".join(f"{nm} {k:.2f}, {c:.3f}" + ("" if j == 0 else f" ({k / ks[0][0]:.3f})")
                                           for j, (nm, (k, c)) in enumerate(zip(names, ks))))
    print("\nrow-mean S along y (every 10th row from the bath plane): " + " / ".join(names))
    for tt in ("0.002", "0.01", "0.02", "0.03"):
        if tt not in prof["tensorA"]:
            continue
        print(f"  {float(tt)*1e3:4.0f} ms:")
        for j in range(0, len(yrow), 10):
            print(f"    y {yrow[j]:.3f} mm: " + " / ".join(f"{prof[k][tt][j]:.3f}" for k in names))
    for r in runs:
        logstats(r)


if __name__ == "__main__":
    main()
