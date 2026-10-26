#!/usr/bin/env python3
"""Change E: Solidf = 0.5 on porous/free faces (upstream bug) empties the yarn edge cells in the first step.

    ../../.venv/bin/python plot_E.py
Writes figures/E_solidf_step1.png, prints the numbers shown.

Data (2026-10-12, strip bench: 50 x 1 x 15 cells of 20 um, porous slab rows k = 3..10, free rows above and below,
wet 0.2 mm ramp at the inlet; cell index = i + 50 k):
  - cases/strip/debug_faceDump_preE/base_step1_faceDump.log.gz: debug build of the pre-E solver (b995db5 + face dump
    patch) on the bench, step 1. Lines "DBGF 1 <quantity> <face>=<value>": faces YG0/YG1/YG2/YG8 = yarn/gap faces
    of the top edge row at i = 0, 1, 2, 8 (owner cells 500, 501, 502, 508, neighbours 550, ...), YY0/YY1 = yarn/yarn
    faces below them, X01/X12 = x-faces along the edge row. Lines "DBGC 1 alpha_in/alpha_out c<i>_<k>=<value>": alpha
    of cell (i, k) before and after the alpha equation of step 1.
  - cases/strip/base_steps: the same bench with E installed (c3a2e6e, run 11:21 on 2026-10-12), fields written at every
    step; alpha after step 1 read from its first time directory.
"""
import gzip
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import foamio as F

DUMP = os.path.join(F.CASES, "strip", "debug_faceDump_preE", "base_step1_faceDump.log.gz")
ESTEPS = os.path.join(F.CASES, "strip", "base_steps")
NX = 50


def dump():
    d = {}
    for line in gzip.open(DUMP, "rt"):
        f = line.split()
        if len(f) > 3 and f[0] in ("DBGF", "DBGC") and f[1] == "1":
            key = f[2]
            if key in d:                        # some quantities are printed twice (two pressure correctors)
                continue
            d[key] = {k: float(v) for k, v in (x.split("=") for x in f[3:])}
    return d


def main():
    d = dump()
    faces = ["YG0", "YG1", "YG2", "YG8", "YY0", "YY1", "X01", "X12"]
    flab = ["i=0", "i=1", "i=2", "i=8", "i=0", "i=1", "0|1", "1|2"]
    cols = [F.C[1]] * 4 + [F.C[0]] * 2 + [F.C[2]] * 2
    print("pre-E dump, step 1:")
    for q in ("Solidf", "phirPore", "alphaPhi10"):
        print(f"  {q:10s}", "  ".join(f"{f}={d[q][f]:.3g}" for f in faces))

    fig, axs = plt.subplots(1, 3, figsize=(14, 4.3), gridspec_kw={"width_ratios": [1, 1, 1.25]})
    ax = axs[0]
    ax.bar(range(8), [d["Solidf"][f] for f in faces], color=cols)
    ax.set_xticks(range(8), flab, fontsize=6.5)
    ax.set_ylabel("Solidf on the face")
    F.style(ax, "(a) pre-E, step 1: Solidf (should be 0 on yarn/gap faces)")
    from matplotlib.patches import Patch
    ax.legend([Patch(color=F.C[1]), Patch(color=F.C[0]), Patch(color=F.C[2])],
              ["yarn/gap faces (z), edge row", "yarn/yarn faces (z) below", "yarn x-faces along the edge row"],
              fontsize=7, frameon=False, loc="upper left")
    ax.set_ylim(0, 1.45)

    ax = axs[1]
    ax.bar(range(8), [abs(d["phirPore"][f]) for f in faces], color=cols)
    ax.set_yscale("log")
    ax.set_xticks(range(8), flab, fontsize=6.5)
    ax.set_ylabel("|phirPore| (relative flux of the α equation)")
    F.style(ax, "(b) pre-E, step 1: relative flux, yarn/gap vs yarn faces")

    ax = axs[2]
    cells = [(0, 10), (1, 10), (8, 10), (0, 11), (1, 11), (8, 11)]
    t1 = F.times(ESTEPS)[1]
    aE = F.read_field(os.path.join(ESTEPS, t1, "alpha.wetting"), 750)
    a0 = F.read_field(os.path.join(ESTEPS, "0", "alpha.wetting"), 750)
    before = [d["alpha_in"][f"c{i}_{k}"] for i, k in cells]
    pre = [d["alpha_out"][f"c{i}_{k}"] for i, k in cells]
    post = [aE[i + NX * k] for i, k in cells]
    print("alpha before step 1 (dump) :", np.round(before, 4), " (E case t=0:", np.round([a0[i + NX * k] for i, k in cells], 4), ")")
    print("alpha after step 1, pre-E   :", np.round(pre, 4))
    print(f"alpha after step 1, E (t={t1}):", np.round(post, 4))
    x = np.arange(len(cells))
    wbar = 0.27
    ax.bar(x - wbar, before, wbar, color=F.MUTED, label="before step 1")
    ax.bar(x, pre, wbar, color=F.C[1], label="after step 1, pre-E (b995db5)")
    ax.bar(x + wbar, post, wbar, color=F.C[0], label="after step 1, with E (c3a2e6e)")
    for xs, vals in ((x - wbar, before), (x, pre), (x + wbar, post)):
        for xi, v in zip(xs, vals):
            ax.text(xi, v + 0.01, f"{v:.3g}", ha="center", va="bottom", fontsize=6, rotation=90)
    ax.set_ylim(0, 1.2)
    ax.set_xticks(x, [f"yarn edge\ni={i}" if k == 10 else f"gap cell\nabove i={i}" for i, k in cells], fontsize=6.5)
    ax.set_ylabel("α of the cell")
    ax.legend(fontsize=7, frameon=False)
    F.style(ax, "(c) top yarn edge row and the gap cells above it")
    fig.suptitle("Change E — Solidf recomputed without clipping gives porous fluxes with K = 0.5 m² and the gap cell's "
                 "pc on yarn/gap faces: the wet edge cells empty into the gap in one step", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "E_solidf_step1.png"), dpi=140)


if __name__ == "__main__":
    os.makedirs(F.FIGS, exist_ok=True)
    main()
