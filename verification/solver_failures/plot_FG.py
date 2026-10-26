#!/usr/bin/env python3
"""Changes F and G on the strip bench (porous slab between free layers, reservoir at x = 0), 2026-10-12.

    ../../.venv/bin/python plot_FG.py
Writes figures/F_mixed_cell_velocity.png and figures/G_yarn_drains.png, prints the numbers shown.

Bench: 50 x 1 x 15 cells of 20 um, porous slab rows k = 3..10 (eps 0.5, K 1e-11), free rows 0-2 and 11-14 (pure
gap), wet 0.2 mm ramp at the inlet, gaps initialised at alpha 0.002 (setup of that day). Mixed cells = slab rows 3 and
10 (porous cells with one yarn/gap face: Darcy faces inside the yarn, a momentum face to the gap).
Runs (copied unchanged from meshing_strat_trial/2D_bench_strip/variants/old_variants/):
  base_steps          E (c3a2e6e), 10 steps, fields at every step
  base_run            E, run to 0.2 ms (stopped by stopGuard at 1.8e-5 s, dt < 1e-14)
  base_run_F          scratch build E + F + G (hybridPorousInterFoamFG) with G off (no porousFreeDarcyFaces): E + F
  base_run_G          same build, porousFreeDarcyFaces on: E + F + G
  fullSlabClosed_run  E, slab everywhere (no free cells), top/bottom closed: the yarn without gaps
  R3closedRamp_run(_G), R3closedRampSlab_run(_G): referee R3, all patches closed (no reservoir), the ramp water
                      can only redistribute; Slab = without gaps. No suffix = E, _G = E + F + G.
Quantities: |U - reconstruct(phi)| per cell (foamio.reconstruct_phi, OpenFOAM's fvc::reconstruct formula) from the
written U and phi; deltaT per step from the logs; yarn saturation and water from liquidBalance.csv (written by the
liquidBalance function object during the run).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import foamio as F

S = os.path.join(F.CASES, "strip")
NX, NZ = 50, 15
CLASSES = [("mixed cells (yarn edge rows)", [3, 10], F.C[1]), ("interior yarn cells", list(range(4, 10)), F.C[0]),
           ("free (gap) cells", [0, 1, 2, 11, 12, 13, 14], F.C[2])]


def mismatch(case):
    mesh = F.read_mesh(os.path.join(S, case))
    out = []
    for t in F.times(os.path.join(S, case))[1:]:
        U = F.read_field(os.path.join(S, case, t, "U"), NX * NZ).reshape(NZ, NX, 3)
        Ur = F.reconstruct_phi(os.path.join(S, case), t, mesh).reshape(NZ, NX, 3)
        d = np.linalg.norm(U - Ur, axis=2)
        out.append([float(t)] + [d[rows].max() for _, rows, _ in CLASSES])
    return np.array(out)


def dt_history(case):
    t, dt = [], []
    for line in F.log_lines(F.find_log(os.path.join(S, case))):
        if line.startswith("deltaT = "):
            dt.append(float(line.split()[2]))
        elif line.startswith("Time = ") and len(t) < len(dt):
            t.append(float(line.split()[2]))
    n = min(len(t), len(dt))
    return np.array(t[:n]), np.array(dt[:n])


def fig_F():
    print("F:")
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    m = mismatch("base_steps")
    ax = axs[0]
    for k, (lab, _, col) in enumerate(CLASSES):
        ax.semilogy(np.arange(1, len(m) + 1), m[:, k + 1], color=col, marker="o", ms=3.5, label=lab)
    print("  E base_steps, max |U - reconstruct(phi)| per step [m/s]:")
    for k, (lab, _, _) in enumerate(CLASSES):
        print(f"    {lab:30s}", " ".join(f"{v:.3g}" for v in m[:, k + 1]))
    ax.set_xlabel("time step")
    ax.set_ylabel("max |U − reconstruct(φ)| [m/s]")
    ax.legend(fontsize=7, frameon=False)
    F.style(ax, "(a) with E: cell U vs face fluxes, first 10 steps")

    ax = axs[1]
    for case, lab, col in [("base_run", "E (c3a2e6e)", F.C[1]), ("base_run_F", "E + F (G off)", F.C[0])]:
        t, dt = dt_history(case)
        ax.loglog(t, dt, color=col, lw=1.2, label=f"{lab}: {len(t)} steps, last t = {t[-1]:.3g} s")
        print(f"  {case}: {F.log_exec(F.find_log(os.path.join(S, case)))}  steps {len(t)}  last t {t[-1]:.4g}  "
              f"last dt {dt[-1]:.3g}")
    ax.set_xlabel("t [s]")
    ax.set_ylabel("deltaT [s]")
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    F.style(ax, "(b) time step: E collapses at 18 µs, E + F reaches 0.2 ms")

    ax = axs[2]
    mF = mismatch("base_run_F")
    for k, (lab, _, col) in enumerate(CLASSES):
        ax.semilogy(mF[:, 0] * 1e3, mF[:, k + 1], color=col, marker="o", ms=3.5, label=lab)
    print("  E+F base_run_F, max |U - reconstruct(phi)| per write [m/s]:")
    for k, (lab, _, _) in enumerate(CLASSES):
        print(f"    {lab:30s}", " ".join(f"{v:.3g}" for v in mF[:, k + 1]))
    ax.set_xlabel("t [ms]")
    ax.set_ylabel("max |U − reconstruct(φ)| [m/s]")
    ax.set_ylim(axs[0].get_ylim())
    F.style(ax, "(c) E + F: mismatch bounded, not zero (writes every 20 µs)")
    fig.suptitle("Change F — with E, the velocity of the mixed cells (Darcy faces + one momentum face) drifts from the "
                 "face fluxes by m/s per step and the run collapses; with F it reaches 0.2 ms", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "F_mixed_cell_velocity.png"), dpi=140)


def fig_G():
    print("G:")
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
    ax = axs[0]
    for case, lab, col, ls in [("fullSlabClosed_run", "yarn without gaps (E)", F.MUTED, "-"),
                               ("base_run_F", "yarn + gaps, E + F (no capillary jump)", F.C[1], "-"),
                               ("base_run_G", "yarn + gaps, E + F + G (reservoir water also climbs the gaps)", F.C[0], "--")]:
        names, d = F.read_csv(os.path.join(S, case, "liquidBalance.csv"))
        s = d[:, names.index("meanSaturationPorous")]
        ax.plot(d[:, 0] * 1e3, s, color=col, ls=ls, marker="o", ms=3.5, lw=1.6, label=lab)
        print(f"  {case:20s} yarn mean saturation:", " ".join(f"{v:.4f}" for v in s))
    ax.set_xlabel("t [ms]")
    ax.set_ylabel("mean saturation of the yarn (porous cells)")
    ax.legend(fontsize=7, frameon=False)
    F.style(ax, "(a) wicking bench (reservoir at x = 0): the yarn drains instead of wicking")

    ax = axs[1]
    for case, lab, col, ls in [("R3closedRampSlab_run", "no gaps (E)", F.MUTED, "-"),
                               ("R3closedRampSlab_run_G", "no gaps (E + F + G)", F.C[2], ":"),
                               ("R3closedRamp_run", "yarn + gaps, E", F.C[1], "-"),
                               ("R3closedRamp_run_G", "yarn + gaps, E + F + G", F.C[0], "--")]:
        names, d = F.read_csv(os.path.join(S, case, "liquidBalance.csv"))
        w = d[:, names.index("porousLiquid_mL")]
        ax.plot(d[:, 0] * 1e3, 100 * (w / w[0] - 1), color=col, ls=ls, marker="o", ms=3.5, lw=1.6, label=lab)
        print(f"  {case:24s} yarn water change [%]:", " ".join(f"{100*(v/w[0]-1):.3g}" for v in w))
    ax.set_xlabel("t [ms]")
    ax.set_ylabel("yarn water, change from t = 0 [%]")
    ax.legend(fontsize=7, frameon=False)
    F.style(ax, "(b) referee R3, all patches closed: the yarn water should stay constant")
    fig.suptitle("Change G — without a capillary condition on yarn/gap faces the yarn loses its water to the gaps "
                 "(wicking bench and closed referee R3)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "G_yarn_drains.png"), dpi=140)


if __name__ == "__main__":
    os.makedirs(F.FIGS, exist_ok=True)
    fig_F()
    fig_G()
