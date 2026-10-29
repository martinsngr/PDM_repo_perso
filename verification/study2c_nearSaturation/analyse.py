#!/usr/bin/env python3
"""analyse.py  -  summary of the study2c_nearSaturation runs (README.md).
    ../../.venv/bin/python analyse.py [run ...]      (default: every N*/A*/K* folder with a log)
Mesh: bench_B, 100 x 1 x 24 cells of 20 um (cell c = i + 100 k), porous = eps <= 0.99 (walls k 0-7 and 16-23 for
i < 97), gap k 8-15 (or the free rows at mid-length for other gap widths). Per write: max |U| of the free cells and their number above 1 m/s; smeared cells = free cells
with 0.05 < alpha < 0.95 that share a face with a porous cell; gap meniscus = largest x where the gap-averaged alpha
> 0.5; mean wall saturation. From the log (dsLocator, coatsTimeStep): max free |U| per step after 0.2 ms, the fraction
of steps above 5 m/s, dt dips (dt < 0.5 x median dt after 0.1 ms), min dt, stopGuard. Water budget: last imbalance of
waterBudget.csv. Writes summary.md."""
import csv
import glob
import os
import re
import sys

import numpy as np

NX, NZ, DX = 100, 24, 20e-6


def read(path, vec=False):
    body = open(path).read().split("internalField", 1)[1]
    m = re.match(r"\s*uniform\s+([^;]+);", body)
    if m:
        v = np.array(m.group(1).strip("()").split(), float)
        return np.tile(v, (NX * NZ, 1)) if vec else np.full(NX * NZ, v[0])
    n = int(re.search(r">\s*(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if vec:
        return np.array([s.split() for s in re.findall(r"\(([^()]+)\)", data)[:n]], float)
    return np.array(data.split(")", 1)[0].split()[:n], float)


def grid(a):
    return a.reshape(NZ, NX).T          # [i, k]


def times(run):
    return sorted((t for t in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", t) and t != "0"
                   and os.path.isfile(os.path.join(run, t, "U"))), key=float)


def log_stats(run):
    path = os.path.join(run, "log.hybridPorousInterFoam")
    if not os.path.isfile(path):
        return {}
    t = dt = None
    dts, ts, us, stop = [], [], [], ""
    for line in open(path, errors="replace"):
        if line.startswith("Time = "):
            t = float(line.split()[2])
        elif line.startswith("deltaT = ") and t is not None:
            dts.append(float(line.split()[2]))
            ts.append(t)
        elif line.startswith("uLoc "):
            w = line.split()
            us.append((float(w[1]), float(w[3])))
        elif line.startswith("stopGuard:"):
            stop = line.strip()
    ts, dts = np.array(ts), np.array(dts)
    late = dts[ts > 1e-4]
    med = np.median(late) if late.size else float("nan")
    u = np.array([x for x in us if x[0] > 2e-4])
    return dict(steps=len(dts), t_end=ts[-1] if ts.size else 0, dt_med=med,
                dips=int((late < 0.5 * med).sum()) if late.size else 0,
                dt_min=late.min() if late.size else float("nan"),
                umax=u[:, 1].max() if u.size else float("nan"),
                u5=float((u[:, 1] > 5).mean()) if u.size else float("nan"), stop=stop)


def run_stats(run):
    P = grid(read(os.path.join(run, "0/eps")) <= 0.99)
    F = ~P
    nbP = np.zeros_like(P)
    nbP[1:, :] |= P[:-1, :]
    nbP[:-1, :] |= P[1:, :]
    nbP[:, 1:] |= P[:, :-1]
    nbP[:, :-1] |= P[:, 1:]
    gap = ~P[NX // 2, :]                # free rows at mid-length = the gap
    rows = []
    for t in times(run):
        a = grid(read(os.path.join(run, t, "alpha.wetting")))
        U = np.linalg.norm(read(os.path.join(run, t, "U"), vec=True), axis=1).reshape(NZ, NX).T
        gapA = a[:, gap].mean(axis=1)
        wet = np.nonzero(gapA > 0.5)[0]
        rows.append(dict(t=float(t), umax=U[F].max(), n1=int((F & (U > 1)).sum()),
                         smear=int((F & nbP & (a > 0.05) & (a < 0.95)).sum()),
                         men=(wet.max() + 1) * DX * 1e3 if wet.size else 0.0, Sw=a[P].mean()))
    return rows


def budget(run):
    path = os.path.join(run, "waterBudget.csv")
    if not os.path.isfile(path):
        return float("nan"), float("nan")
    r = list(csv.DictReader(open(path)))
    return (float(r[-1]["imbalance"]), float(r[-1]["water_m3"])) if r else (float("nan"), float("nan"))


def main():
    runs = sys.argv[1:] or sorted(d for d in glob.glob("[NAK][0-9]*") if os.path.isdir(d))
    out = ["| run | steps | t end [ms] | max \\|U\\| free per step > 0.2 ms [m/s] | steps > 5 m/s | dt median [s] | "
           "dt dips | dt min [s] | max \\|U\\| free at writes [m/s] | free > 1 m/s (max over writes) | "
           "smeared cells at 0.5 / 1 / 2 ms | meniscus at 1 / 2 ms [mm] | wall S 0 → end | imbalance / water |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for run in runs:
        L = log_stats(run)
        R = run_stats(run)
        if not L or not R:
            out.append(f"| {run} | not run | | | | | | | | | | | | |")
            continue
        at = {round(r["t"] * 1e4): r for r in R}
        sm = " / ".join(str(at[k]["smear"]) if k in at else "–" for k in (5, 10, 20))
        mn = " / ".join(f"{at[k]['men']:.2f}" if k in at else "–" for k in (10, 20))
        S0 = float(read(os.path.join(run, "0/alpha.wetting"))[grid(read(os.path.join(run, "0/eps")) <= 0.99).T.ravel()].mean())
        imb, w = budget(run)
        out.append(f"| {run} | {L['steps']} | {L['t_end']*1e3:.3f} | {L['umax']:.2f} | {100*L['u5']:.1f} % | "
                   f"{L['dt_med']:.2e} | {L['dips']} | {L['dt_min']:.1e} | {max(r['umax'] for r in R):.2f} | "
                   f"{max(r['n1'] for r in R)} | {sm} | {mn} | {S0:.3f} → {R[-1]['Sw']:.3f} | {imb / w:.1e} |"
                   + (f" {L['stop']}" if L["stop"] else ""))
    txt = "\n".join(out)
    print(txt)
    open("summary.md", "w").write("# study2c_nearSaturation — summary (analyse.py)\n\n" + txt + "\n")


if __name__ == "__main__":
    main()
