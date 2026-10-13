"""Scan saturation fields for odd-even (cell-to-cell) patterns, on any mesh.

    ../.venv/bin/python scanOddEven.py

For every write time of each case: the cells that are strict local extrema of S (above or below ALL their face
neighbours) by more than AMP, their number and largest amplitude, and the largest |S_c - mean of face neighbours|.
A monotone wicking profile has (almost) no such extrema, even at a sharp front; an odd-even pattern has many.
Positive control: verification/eq_BC (the modified solver oscillates there, the original does not).
Neighbours from constant/polyMesh/owner and neighbour (ASCII). Prints one table, writes oddEvenScan.png.
"""
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AMP = 1e-3
CASES = [  # folder (relative to the repo root), saturation field, label
    ("verification/eq_BC/port", "alpha.wetting", "eq_BC original (control)"),
    ("verification/eq_BC/ABC", "alpha.wetting", "eq_BC modified (control)"),
    ("trialWicking/1D_vertical_impes_inletRes", "Sb", "1D impesFoam"),
    ("trialWicking/1D_vertical_hybrid", "alpha.wetting", "1D hybrid modified"),
    ("trialWicking/1D_vertical_hybrid/results_oldsolver", "alpha.wetting", "1D hybrid original"),
    ("trialWicking/singleYarn_vertical_impes_inletRes", "Sb", "yarn impesFoam"),
    ("trialWicking/singleYarn_vertical_hybrid", "alpha.wetting", "yarn hybrid modified"),
]
# reference palette (dataviz skill), fixed order, plus line style
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#222222"]
STYLES = ["-", "--", "-", ":", "-", "-.", "--"]


def read_list(path, dtype=float):
    txt = open(path).read()
    txt = txt[txt.index("FoamFile"):]
    txt = txt[txt.index("}") + 1:]
    m = re.search(r"\n(\d+)\s*\n?\(", txt)
    n, start = int(m.group(1)), m.end()
    return np.array(txt[start:txt.index(")", start)].split(), dtype=dtype)[:n]


def read_scalar(path, ncells):
    txt = open(path).read()
    m = re.search(r"internalField\s+uniform\s+(\S+);", txt)
    if m:
        return np.full(ncells, float(m.group(1)))
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", txt)
    a = np.array(txt[m.end():txt.index("\n)", m.end())].split(), dtype=float)
    assert len(a) == ncells, path
    return a


def times(case):
    out = []
    for d in os.listdir(case):
        try:
            out.append((float(d), d))
        except ValueError:
            pass
    return sorted(out)


def scan(S, own, nei, ncells):
    """Strict local extrema with amplitude > AMP, and max |S - neighbour mean|."""
    lo = np.full(ncells, np.inf)   # min over neighbours
    hi = np.full(ncells, -np.inf)  # max over neighbours
    sm = np.zeros(ncells)
    cnt = np.zeros(ncells)
    for a, b in ((own, nei), (nei, own)):
        np.minimum.at(lo, a, S[b])
        np.maximum.at(hi, a, S[b])
        np.add.at(sm, a, S[b])
        np.add.at(cnt, a, 1)
    has = cnt > 0
    amp = np.where(has, np.maximum(S - hi, lo - S), -np.inf)  # > 0 only for a strict extremum
    ext = amp > AMP
    dev = np.where(has, np.abs(S - sm / np.maximum(cnt, 1)), 0)
    return int(ext.sum()), (amp[ext].max() if ext.any() else 0.0), dev.max()


def main():
    rows = []
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    for (rel, field, label), col, ls in zip(CASES, COLORS, STYLES):
        case = os.path.join(ROOT, rel)
        mesh = os.path.join(ROOT, rel.split("/results_oldsolver")[0], "constant", "polyMesh")
        own = read_list(os.path.join(mesh, "owner"), int)
        nei = read_list(os.path.join(mesh, "neighbour"), int)
        own = own[:len(nei)]  # internal faces only
        ncells = int(max(own.max(), nei.max())) + 1
        ts, ns, amps, devs = [], [], [], []
        for tv, td in times(case):
            f = os.path.join(case, td, field)
            if tv == 0 or not os.path.exists(f):
                continue
            n, amp, dev = scan(read_scalar(f, ncells), own, nei, ncells)
            ts.append(tv); ns.append(n); amps.append(amp); devs.append(dev)
        if not ts:
            continue
        rows.append((label, ncells, len(ts), ts[0], ts[-1], max(ns), int(np.median(ns)), max(amps), max(devs)))
        a1.plot(ts, np.array(ns) / ncells * 100, color=col, ls=ls, lw=1.5, marker="o", ms=3, label=label)
        a2.plot(ts, np.maximum(amps, 1e-6), color=col, ls=ls, lw=1.5, marker="o", ms=3, label=label)
    for ax in (a1, a2):
        ax.set_xscale("log")
        ax.set_xlabel("time (s, log)")
        ax.grid(alpha=0.25, which="both")
    a1.set_ylabel(f"cells that are strict local extrema by > {AMP:g} (% of cells)")
    a2.set_yscale("log")
    a2.set_ylabel("largest extremum amplitude (floored at 1e-6)")
    a1.legend(fontsize=8, frameon=False)
    fig.suptitle("Odd-even scan of saturation fields (eq_BC = positive control)")
    fig.savefig(os.path.join(HERE, "oddEvenScan.png"), dpi=130)

    print(f"| Case | cells | writes | t first | t last | max extrema (> {AMP:g}) | median extrema "
          "| max extremum amplitude | max abs(S - neighbour mean) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| {} | {} | {} | {:g} | {:g} | {} | {} | {:.2e} | {:.2e} |".format(*r))


if __name__ == "__main__":
    main()
