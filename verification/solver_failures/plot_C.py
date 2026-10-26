#!/usr/bin/env python3
"""Change C: linearly interpolated kr gives a spurious foot of low saturation ahead of the 1D wicking front.

    ../../.venv/bin/python plot_C.py
Writes figures/C_1D_foot.png, prints the numbers shown.

Data (copied unchanged from verification/wicking1D/, 2026-10-07): 1D column, 172 cells of 20 um, written every 1 ms;
impesFoam (kr upwinded), hybrid original be54696 (kr linear), hybrid A+B+C b995db5. Every cell value plotted on a
log axis (the dry initial value is 0.002). Not isolated: no A+B-only 1D run exists, so A and B are also on in the
"A+B+C" curve. impesFoam upwinds kr like C does.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import foamio as F

W1D = os.path.join(F.CASES, "wicking1D")
L, NY = 3.446e-3, 172
Y = (np.arange(NY) + 0.5) * L / NY
RUNS = [("impes", "Sb", "impesFoam", F.C[2], "o"), ("port", "alpha.wetting", "hybrid original (be54696)", F.C[1], "s"),
        ("ABC", "alpha.wetting", "hybrid A+B+C (b995db5)", F.C[0], "^")]


def main():
    ts = ["0.001", "0.005", "0.01", "0.02"]
    fig, axs = plt.subplots(1, len(ts), figsize=(13, 3.9), sharey=True)
    for ax, t in zip(axs, ts):
        for run, field, lab, col, mk in RUNS:
            a = F.read_field(os.path.join(W1D, run, t, field), NY)
            ax.semilogy(Y * 1e3, a, color=col, marker=mk, ms=2.5, lw=0.8, label=lab)
            wet = np.where(a > 0.01)[0]
            front = np.where(a > 0.1)[0]
            print(f"  t {t} {run:6s}: highest cell with S > 0.1 at {Y[front[-1]]*1e3:.3f} mm, "
                  f"with S > 0.01 at {Y[wet[-1]]*1e3:.3f} mm")
        ax.set_ylim(1e-3, 1.5)
        ax.set_xlabel("height x [mm]")
        F.style(ax, f"t = {float(t)*1e3:g} ms")
    axs[0].set_ylabel("saturation (cell values, log)")
    axs[0].legend(fontsize=7, frameon=False, loc="upper right")
    fig.suptitle("Change C — with linear kr (original) a foot of low saturation (S 0.003–0.07) runs ahead of the front; impesFoam "
                 "and the solver with upwinded kr have none (A and B are also on in the A+B+C run)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "C_1D_foot.png"), dpi=140)


if __name__ == "__main__":
    os.makedirs(F.FIGS, exist_ok=True)
    main()
