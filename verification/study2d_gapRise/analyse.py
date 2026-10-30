#!/usr/bin/env python3
"""analyse.py  -  gap-rise table of the screening runs of study2d_gapRise (README.md), with the reference T12 of study 2c.
    ../../.venv/bin/python analyse.py [run ...]      (default: every S* folder and T12)
Reuses ../study2c_nearSaturation/analyseCut.py (log statistics, per-write quantities). Added per write: gap water top
for alpha > 0.1, free box cells with alpha > 0.5 above y 0.25 and 0.5 mm, water in the padding (cell volumes), water
lost through top and bottom (waterBudget.csv, cell volumes). Writes summary.md."""
import csv
import glob
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2c_nearSaturation"))
from analyseCut import budget, field, log_stats, rlist, run_stats  # noqa: E402

VCELL = (20e-6) ** 3
REF = "../study2c_nearSaturation/T12_cut_t40_K2"


def extra(run, times):
    C, _ = rlist(os.path.join(run, "0/C"), vec=True)
    n = len(C)
    F = field(os.path.join(run, "0/eps"), n) > 0.99
    bm = open(os.path.join(run, "system/blockMeshDict")).read()
    zv = sorted({float(l.split()[2]) for l in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",
                                                        bm.split("vertices", 1)[1].split(");", 1)[0])})
    box = (C[:, 2] > zv[1]) & (C[:, 2] < zv[2])
    rows = {}
    for t in times:
        a = field(os.path.join(run, t, "alpha.wetting"), n)
        w = F & box & (a > 0.5)
        w01 = F & box & (a > 0.1)
        rows[float(t)] = dict(top01=C[w01, 1].max() * 1e3 if w01.any() else float("nan"),
                              n25=int((w & (C[:, 1] > 0.25e-3)).sum()), n50=int((w & (C[:, 1] > 0.5e-3)).sum()),
                              pad=a[F & ~box].sum())
    return rows


def lost(run):
    path = os.path.join(run, "waterBudget.csv")
    if not os.path.isfile(path):
        return []
    return [(float(r["time"]), -(float(r["in_top"]) + float(r["in_bottom"])) / VCELL) for r in csv.DictReader(open(path))]


def main():
    runs = sys.argv[1:] or sorted(d for d in glob.glob("S[0-9]*") if os.path.isdir(d)) + [REF]
    out = []
    for run in runs:
        L = log_stats(run)
        if not L:
            out.append(f"## {run}: not run\n")
            continue
        R = run_stats(run)
        times = sorted((t for t in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", t) and t != "0"
                        and os.path.isfile(os.path.join(run, t, "U"))), key=float)
        X = extra(run, times)
        B = lost(run)
        out.append(f"## {os.path.basename(run)}\nsteps {L['steps']}, t end {L['t_end']*1e3:.3f} ms, dt median {L['dt_med']:.2e} s, "
                   f"dips {L['dips']}, dt min {L['dt_min']:.1e} s; per-step max free |U| after 0.2 ms {L['umax']:.2f} m/s, "
                   f"steps > 5 m/s {100*L['u5']:.1f} %; imbalance/water {budget(run):.1e}"
                   + (f"; {L['stop']}" if L["stop"] else "") +
                   f"\nper-step max free |U| per 0.05 ms [m/s]: {L['bins']}\n\n"
                   "| t [ms] | y-yarn front [mm] | mean porous S | gap water [cells] | gap top a>0.5 / a>0.1 [mm] "
                   "| cells a>0.5 above 0.25 / 0.5 mm | padding water [cells] | lost top+bottom [cells] "
                   "| max free \\|U\\| [m/s] | free > 1 / > 5 m/s |\n|---|---|---|---|---|---|---|---|---|---|")
        for r in R:
            x = X[r["t"]]
            ls = [v for tt, v in B if tt <= r["t"] * (1 + 1e-9)]
            out.append(f"| {r['t']*1e3:.2f} | {r['front']:.3f} | {r['S']:.4f} | {r['gap']:.0f} | {r['gtop']:.3f} / {x['top01']:.3f} "
                       f"| {x['n25']} / {x['n50']} | {x['pad']:.0f} | {ls[-1] if ls else float('nan'):.0f} | {r['umax']:.2f} | {r['n1']} / {r['n5']} |")
        out.append("")
    txt = "\n".join(out)
    print(txt)
    open("summary.md", "w").write("# study2d_gapRise — screening runs (analyse.py)\n\n" + txt + "\n")


if __name__ == "__main__":
    main()
