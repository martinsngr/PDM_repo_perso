#!/usr/bin/env python3
"""analyseCut.py  -  summary of the truncated-REV runs of study2c_nearSaturation (README.md, phase 1c and later).
    ../../.venv/bin/python analyseCut.py [run ...]      (default: every T* folder with a log)
Needs the cell centres in <run>/0/C (written here with postProcess -func writeCellCentres if missing). Porous =
eps <= 0.99; fabric box = z between the padding layers (z vertices of system/blockMeshDict). Per write: max |U| of
the free cells, their number above 1 and 5 m/s, smeared cells (free, 0.05 < alpha < 0.95, sharing a face with a
porous cell), y-yarn front (yarnID 0-4, alpha > 0.1), mean porous S, gap water (free box cells, sum of alpha) and its
top (free box cells with alpha > 0.5). From the log (dsLocator, coatsTimeStep): per-step max free |U| after 0.2 ms
and per 0.05 ms, the fraction of steps above 5 m/s, dt median / dips (< 0.5 x median after 0.1 ms) / min, stopGuard.
Water budget: last imbalance of waterBudget.csv. Writes summaryCut.md."""
import csv
import glob
import os
import re
import subprocess
import sys

import numpy as np


def rlist(path, vec=False):
    txt = open(path).read()
    if "internalField" in txt:
        body = txt.split("internalField", 1)[1]
        m = re.match(r"\s*uniform\s+([^;]+);", body)
        if m:
            return None, m.group(1)
    else:
        body = txt.split("FoamFile", 1)[1].split("}", 1)[1]
    n = int(re.search(r"(\d+)\s*\(", body).group(1))
    data = body.split("(", 1)[1]
    if vec:
        return np.array([s.split() for s in re.findall(r"\(([^()]+)\)", data)[:n]], float), None
    return np.array(data.split(")", 1)[0].split()[:n], float), None


def field(path, n, vec=False):
    a, uni = rlist(path, vec)
    if a is not None:
        return a
    v = np.array(uni.strip("()").split(), float)
    return np.tile(v, (n, 1)) if vec else np.full(n, v[0])


def log_stats(run):
    path = os.path.join(run, "log.hybridPorousInterFoam")
    if not os.path.isfile(path):
        return None
    t = None
    ts, dts, us, stop = [], [], [], ""
    for line in open(path, errors="replace"):
        if line.startswith("Time = "):
            t = float(line.split()[2])
        elif line.startswith("deltaT = ") and t is not None:
            ts.append(t)
            dts.append(float(line.split()[2]))
        elif "uLoc " in line:
            w = line.split()
            w = w[w.index("uLoc") + 1:]
            us.append((float(w[0]), float(w[2])))
        elif line.startswith("stopGuard:"):
            stop = line.strip()
    ts, dts = np.array(ts), np.array(dts)
    late = dts[ts > 1e-4]
    med = np.median(late) if late.size else float("nan")
    u = np.array(us) if us else np.zeros((0, 2))
    after = u[u[:, 0] > 2e-4] if u.size else u
    bins = {}
    for tt, uu in u:
        b = int(tt / 5e-5)
        bins[b] = max(bins.get(b, 0.0), uu)
    return dict(steps=len(dts), t_end=ts[-1] if ts.size else 0.0, dt_med=med,
                dips=int((late < 0.5 * med).sum()) if late.size else 0,
                dt_min=late.min() if late.size else float("nan"),
                umax=after[:, 1].max() if after.size else float("nan"),
                u5=float((after[:, 1] > 5).mean()) if after.size else float("nan"),
                bins=" ".join(f"{bins[b]:.1f}" for b in sorted(bins)), stop=stop)


def run_stats(run):
    if not os.path.isfile(os.path.join(run, "0/C")):
        subprocess.run(["postProcess", "-func", "writeCellCentres", "-time", "0"], cwd=run,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        for f in ("Cx", "Cy", "Cz"):
            p = os.path.join(run, "0", f)
            if os.path.isfile(p):
                os.remove(p)
    C, _ = rlist(os.path.join(run, "0/C"), vec=True)
    n = len(C)
    own, _ = rlist(os.path.join(run, "constant/polyMesh/owner"))
    nei, _ = rlist(os.path.join(run, "constant/polyMesh/neighbour"))
    own, nei = own[:len(nei)].astype(int), nei.astype(int)
    P = field(os.path.join(run, "0/eps"), n) <= 0.99
    yid = field(os.path.join(run, "0/yarnID"), n)
    pf = P[own] != P[nei]
    nbP = np.zeros(n, bool)
    nbP[own[pf]] = True
    nbP[nei[pf]] = True
    bm = open(os.path.join(run, "system/blockMeshDict")).read()
    zv = sorted({float(l.split()[2]) for l in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",
                                                        bm.split("vertices", 1)[1].split(");", 1)[0])})
    box = (C[:, 2] > zv[1]) & (C[:, 2] < zv[2])
    F = ~P
    rows = []
    times = sorted((t for t in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", t) and t != "0"
                    and os.path.isfile(os.path.join(run, t, "U"))), key=float)
    for t in times:
        a = field(os.path.join(run, t, "alpha.wetting"), n)
        U = np.linalg.norm(field(os.path.join(run, t, "U"), n, vec=True), axis=1)
        yy = P & (yid >= 0) & (yid <= 4) & (a > 0.1)
        gw = F & box & (a > 0.5)
        iu = np.argmax(np.where(F, U, -1))
        rows.append(dict(t=float(t), umax=U[F].max(), at=C[iu] * 1e3, n1=int((F & (U > 1)).sum()),
                         n5=int((F & (U > 5)).sum()), smear=int((F & nbP & (a > 0.05) & (a < 0.95)).sum()),
                         front=C[yy, 1].max() * 1e3 if yy.any() else float("nan"), S=a[P].mean(),
                         gap=a[F & box].sum(), gtop=C[gw, 1].max() * 1e3 if gw.any() else float("nan")))
    return rows


def budget(run):
    path = os.path.join(run, "waterBudget.csv")
    if not os.path.isfile(path):
        return float("nan")
    r = list(csv.DictReader(open(path)))
    return float(r[-1]["imbalance"]) / float(r[-1]["water_m3"]) if r else float("nan")


def main():
    runs = sys.argv[1:] or sorted(d for d in glob.glob("T[0-9]*") if os.path.isdir(d))
    out = []
    for run in runs:
        L = log_stats(run)
        if not L:
            out.append(f"## {run}: not run\n")
            continue
        R = run_stats(run)
        out.append(f"## {run}\nsteps {L['steps']}, t end {L['t_end']*1e3:.3f} ms, dt median {L['dt_med']:.2e} s, "
                   f"dips {L['dips']}, dt min {L['dt_min']:.1e} s; per-step max free |U| after 0.2 ms "
                   f"{L['umax']:.2f} m/s, steps > 5 m/s {100*L['u5']:.1f} %; imbalance/water {budget(run):.1e}"
                   + (f"; {L['stop']}" if L["stop"] else "") +
                   f"\nper-step max free |U| per 0.05 ms [m/s]: {L['bins']}\n\n"
                   "| t [ms] | max free \\|U\\| [m/s] | at x,y,z [mm] | free > 1 / > 5 m/s | smeared | y-yarn front [mm] "
                   "| mean porous S | gap water [cells] | gap water top [mm] |\n|---|---|---|---|---|---|---|---|---|")
        for r in R:
            out.append(f"| {r['t']*1e3:.2f} | {r['umax']:.2f} | {r['at'][0]:.3f}, {r['at'][1]:.3f}, {r['at'][2]:.3f} | "
                       f"{r['n1']} / {r['n5']} | {r['smear']} | {r['front']:.3f} | {r['S']:.4f} | {r['gap']:.0f} | "
                       f"{r['gtop']:.3f} |")
        out.append("")
    txt = "\n".join(out)
    print(txt)
    open("summaryCut.md", "w").write("# study2c_nearSaturation — truncated-REV runs (analyseCut.py)\n\n" + txt + "\n")


if __name__ == "__main__":
    main()
