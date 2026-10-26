#!/usr/bin/env python3
"""Changes A and B: transverse instability of the yarn in 2D/3D, and the staircase 1D profile.

    ../../.venv/bin/python plot_AB.py
Writes figures/A_original_vs_A.png and figures/B_Aonly_vs_ABC.png, prints the numbers shown.

Data (copied unchanged from verification/bench_ddtCorr/ and verification/wicking1D/, runs of 2026-10-07):
  - cases/bench5x172/log.*: the 1D yarn column widened to 5 x 172 x 3 cells (symmetry sides), fixed dt 1e-7, 0.2 ms.
    Every step the transverseSpread function object (case/system/controlDict) prints
    "transverse: spread S row j maxUt U meanAlpha a", S = max over the rows of (max - min of alpha across the row).
    A 1D solution has S = 0: any growth is the transverse mode.
  - cases/wicking1D/{port,ABC,impes}: 1D column, 172 cells of 20 um, written every 1 ms.
Plotted as read: S per step from the logs; alpha / Sb of every cell (no interpolation, no smoothing).
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import foamio as F

BENCH = os.path.join(F.CASES, "bench5x172")
W1D = os.path.join(F.CASES, "wicking1D")
L, NY = 3.446e-3, 172
Y = (np.arange(NY) + 0.5) * L / NY


def spread(run):
    """time, transverse spread per step, and whether the run ended normally."""
    t, s, cur = [], [], None
    lines = F.log_lines(os.path.join(BENCH, f"log.{run}"))
    for line in lines:
        if line.startswith("Time = "):
            cur = float(line.split()[2])
        elif line.startswith("transverse: spread") and cur is not None:
            t.append(cur)
            s.append(float(line.split()[2]))
    exe = next(l.split(":", 1)[1].strip() for l in lines if l.startswith("Exec"))
    return np.array(t), np.array(s), any(l.startswith("End") for l in lines), exe


def profile(run, field, t):
    return F.read_field(os.path.join(W1D, run, t, field), NY)


def spread_axis(ax, runs, title):
    for k, (run, lab, col, ls) in enumerate(runs):
        t, s, ended, exe = spread(run)
        s = np.where(s > 0, s, np.nan)
        ax.semilogy(t * 1e3, s, color=col, ls=ls, lw=1.6,
                    label=f"{lab}" + ("" if ended else f" — diverged at {t[-1]*1e3:.4f} ms"))
        print(f"  {run:16s} {exe:32s} steps {len(t):5d}  end {t[-1]:.3e} s  {'End' if ended else 'CRASH'}  "
              f"max spread {np.nanmax(s):.3g}  spread at end {s[-1]:.3g}")
    ax.set_ylim(1e-11, 1e3)
    ax.set_xlabel("t [ms]")
    ax.set_ylabel("transverse spread of α (max over rows)")
    ax.axhline(1, color=F.MUTED, lw=0.6, ls=":")
    F.style(ax, title)
    ax.legend(fontsize=7, frameon=False, loc="lower right")


def fig_A():
    print("A: bench 5 x 172 x 3")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    spread_axis(axs[0], [("i_original", "original (be54696)", F.C[1], "-"),
                         ("ii_A_c1", "original + A (b0c0f67)", F.C[0], "-")],
                "(a) 5 × 172 × 3 bench: transverse spread per step")
    ax = axs[1]
    t = "0.001"
    lab = {"port": "hybrid original (be54696)", "ABC": "hybrid A+B+C (b995db5)", "impes": "impesFoam"}
    for run, field, col, mk in [("impes", "Sb", F.C[2], "o"), ("port", "alpha.wetting", F.C[1], "s"),
                                ("ABC", "alpha.wetting", F.C[0], "^")]:
        a = profile(run, field, t)
        sel = Y < 1.0e-3
        ax.plot(Y[sel] * 1e3, a[sel], color=col, marker=mk, ms=3.5, lw=0.9, label=lab[run])
        d = np.diff(a[Y < 0.8e-3])
        print(f"  1D {run}: cells with alpha increasing upward (inverted pairs) below 0.8 mm at 1 ms: "
              f"{int((d > 1e-6).sum())}")
    ax.set_xlabel("height x [mm] (cell centres)")
    ax.set_ylabel("saturation (cell values)")
    F.style(ax, "(b) 1D wicking column at t = 1 ms: every cell")
    ax.legend(fontsize=7, frameon=False)
    ins = ax.inset_axes([0.52, 0.42, 0.45, 0.3])
    for run, field, col, mk in [("port", "alpha.wetting", F.C[1], "s"), ("ABC", "alpha.wetting", F.C[0], "^")]:
        a = profile(run, field, t)
        sel = (Y > 0.44e-3) & (Y < 0.72e-3)
        ins.plot(Y[sel] * 1e3, a[sel], color=col, marker=mk, ms=3, lw=0.8)
    ins.set_title("zoom 0.44–0.72 mm", fontsize=7)
    ins.tick_params(labelsize=6)
    F.style(ins)
    fig.suptitle("Change A — original solver: the 2D bench diverges and the 1D profile has cell-pair steps "
                 "(odd-even pattern not damped by the cell-gradient relative flux)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "A_original_vs_A.png"), dpi=140)


def fig_B():
    print("B: bench 5 x 172 x 3")
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    spread_axis(ax, [("ii_A_c1", "A only", F.C[0], "-"),
                     ("iii_A_c0", "A, ddtCorr × 0", F.C[3], "--"),
                     ("iv_A_c0.1", "A, ddtCorr × 0.1", F.C[4], ":"),
                     ("T2a_GAMGtight", "A, p GAMG tol 1e-12", F.C[5], "-."),
                     ("T2b_PCGtight", "A, p PCG tol 1e-12", F.MUTED, "--"),
                     ("v_modified", "A + B + C (b995db5, darcyFaceMaxDa 0.1)", F.C[2], "-")],
                "Change B — with A alone the transverse mode still grows to 0.14–0.20 ;\n"
                "ddtCorr and pressure tolerance do not remove it, the Darcy total flux (B) does")
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "B_Aonly_vs_ABC.png"), dpi=140)


if __name__ == "__main__":
    os.makedirs(F.FIGS, exist_ok=True)
    fig_A()
    fig_B()
