#!/usr/bin/env python3
"""Changes H, F' and I on the thick-wall slit (porous walls 8 cells | gap 8 cells | porous walls 8 cells), 2026-10-13.

    ../../.venv/bin/python plot_HFpI.py
Writes figures/H_contact_angle.png, figures/Fp_near_wall_velocity.png, figures/I_no_slip.png, prints the numbers.

Slit: 2 mm x 0.48 mm, 100 x 24 cells of 20 um, gravity -x, reservoir at x = 0 (total-pressure inlet), open at x = 2 mm,
theta 60 deg, 0.1 mm initial water column in the gap, walls eps 0.5 with K as named, G on in all porous-wall runs.
Rows: 0-7 lower wall, 8-15 gap, 16-23 upper wall (S0: 8 gap rows only, real walls with constantAlphaContactAngle).
Runs (copied unchanged from meshing_strat_trial/slit_test/; binary in each log):
  B_nw8_w8_K*        installed solver 1b007d8 (A-G): original porous contact-angle model
  H_nw8_w8_K*        scratch build with H (porousContactAngleWallLike 1)
  HF_nw8_w8_K1e-20   same build, H + F' (porousFreeFluxForce 1)
  P_w8_t60_K1e-20    same build, H + F' + I (porousFreeNoSlip 1) = the committed b525086 (bit-identical, V_* runs)
  S0_w8_t60          real impermeable walls (no porous cells), the reference VOF case
Quantities, from the written alpha.wetting and U (no smoothing):
  meniscus h: first x where the gap-averaged alpha < 0.5, linear interpolation between the two cells (slitReport.py);
  stray water: gap cells with alpha > 0.05 more than 3 cells ahead of the meniscus cell (2D_bench/check.py);
  max |U|: magnitude, over the gap cells;
  Bosanquet slit rise rho d(h h')/dt = 2 sigma cos(theta)/w - 12 mu h h'/w^2 - rho g h from h = 0.1 mm at rest
  (slitReport.analytic, computed from the inputs).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

import foamio as F

SL = os.path.join(F.CASES, "slit")
NX, DX = 100, 20e-6
X = (np.arange(NX) + 0.5) * DX
SIGMA, RHO, MU, G = 0.072, 1000.0, 1e-3, 9.81


def geom(case):
    d = dict(l.split(None, 1) for l in open(os.path.join(SL, case, "slit.info")) if l.strip())
    nw, w, nz = int(d["NW"]), int(d["w"]), int(d["nz"])
    return nw, w, nz


def fields(case, t):
    nw, w, nz = geom(case)
    a = F.read_field(os.path.join(SL, case, t, "alpha.wetting"), NX * nz).reshape(nz, NX)
    U = F.read_field(os.path.join(SL, case, t, "U"), NX * nz).reshape(nz, NX, 3)
    return a, U, nw, w


def meniscus(g):
    i = np.where(g < 0.5)[0]
    if not len(i):
        return NX * DX, NX
    i = i[0]
    if i == 0:
        return 0.0, 0
    return X[i - 1] + (g[i - 1] - 0.5) / (g[i - 1] - g[i]) * DX, i


def series(case):
    out = []
    for t in F.times(os.path.join(SL, case)):
        a, U, nw, w = fields(case, t)
        gap = a[nw:nw + w]
        h, i = meniscus(gap.mean(axis=0))
        stray = int((gap[:, min(i + 3, NX):] > 0.05).sum())
        umag = np.linalg.norm(U[nw:nw + w], axis=2).max()
        out.append((float(t), h, stray, umag))
    return np.array(out)


def bosanquet(w_m, theta, h0=1e-4, T=2e-3):
    A = 2 * SIGMA * np.cos(np.radians(theta)) / (RHO * w_m)
    B = 12 * MU / (RHO * w_m ** 2)
    s = solve_ivp(lambda t, y: [y[1] / y[0], A - B * y[1] - G * y[0]], (0, T), [h0, 0.0], max_step=T / 2000,
                  rtol=1e-8, atol=1e-12)
    return s.t, s.y[0]


def amap(ax, case, t, title):
    a, U, nw, w = fields(case, t)
    nz = a.shape[0]
    im = ax.imshow(a, origin="lower", extent=[0, NX * DX * 1e3, 0, nz * DX * 1e3], aspect="auto", cmap="Blues",
                   vmin=0, vmax=1, interpolation="nearest")
    if nw:
        for z in (nw, nw + w):
            ax.axhline(z * DX * 1e3, color=F.C[1], lw=0.8)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("z [mm]")
    F.style(ax, title)
    ax.grid(False)
    return im


def fig_H():
    print("H:")
    t = "0.001"
    fig, axs = plt.subplots(2, 2, figsize=(13, 7.4), layout="constrained")
    im = amap(axs[0, 0], "B_nw8_w8_K1e-11", t, "(a) K 1e-11, original porous contact angle, t = 1 ms")
    amap(axs[0, 1], "H_nw8_w8_K1e-11", t, "(b) K 1e-11, with H, t = 1 ms")
    fig.colorbar(im, ax=axs[0, :], label="α (cell values)", fraction=0.03, pad=0.01)
    runs = [("B_nw8_w8_K1e-11", "K 1e-11, original", F.C[1], "-"), ("H_nw8_w8_K1e-11", "K 1e-11, H", F.C[0], "-"),
            ("B_nw8_w8_K1e-20", "K 1e-20, original", F.C[1], "--"), ("H_nw8_w8_K1e-20", "K 1e-20, H", F.C[0], "--")]
    ax1, ax2 = axs[1]
    for case, lab, col, ls in runs:
        s = series(case)
        ax1.plot(s[:, 0] * 1e3, s[:, 2], color=col, ls=ls, lw=1.5, label=lab)
        ax2.plot(s[:, 0] * 1e3, s[:, 3], color=col, ls=ls, lw=1.5, label=lab)
        print(f"  {case:18s} {F.log_exec(F.find_log(os.path.join(SL, case))):24s} stray cells max {int(s[:, 2].max()):3d}"
              f"  max|U| {s[:, 3].max():.3g} m/s  h(2 ms) {s[-1, 1]*1e3:.3f} mm")
    ax1.set_xlabel("t [ms]")
    ax1.set_ylabel("gap cells with α > 0.05 ahead of the meniscus")
    F.style(ax1, "(c) stray water (films, droplets) ahead of the meniscus")
    ax1.legend(fontsize=7, frameon=False)
    ax2.set_xlabel("t [ms]")
    ax2.set_ylabel("max |U| in the gap [m/s]")
    F.style(ax2, "(d) max velocity in the gap (H alone does not fix K 1e-20: see F′)")
    ax2.legend(fontsize=7, frameon=False)
    fig.suptitle("Change H — original porous contact-angle model: water films along the walls ahead of the meniscus and "
                 "3–5 m/s currents (K 1e-11); H removes them at K 1e-11, not at K 1e-20", fontsize=9)
    fig.savefig(os.path.join(F.FIGS, "H_contact_angle.png"), dpi=140, bbox_inches="tight")


def fig_Fp():
    print("F':")
    t = "0.001"
    fig, axs = plt.subplots(2, 2, figsize=(13, 7.4), layout="constrained")
    im = amap(axs[0, 0], "H_nw8_w8_K1e-20", t, "(a) K 1e-20, H, t = 1 ms")
    amap(axs[0, 1], "HF_nw8_w8_K1e-20", t, "(b) K 1e-20, H + F′, t = 1 ms")
    fig.colorbar(im, ax=axs[0, :], label="α (cell values)", fraction=0.03, pad=0.01)
    ax1, ax2 = axs[1]
    for case, lab, col in [("H_nw8_w8_K1e-20", "H", F.C[1]), ("HF_nw8_w8_K1e-20", "H + F′", F.C[0])]:
        rows = []
        for tt in F.times(os.path.join(SL, case))[1:]:
            a, U, nw, w = fields(case, tt)
            h, i = meniscus(a[nw:nw + w].mean(axis=0))
            near = U[[nw, nw + w - 1], :max(i, 1)]          # gap rows touching the walls, behind the meniscus
            rows.append((float(tt), np.abs(near[..., 2]).max(), np.abs(near[..., 0]).max()))
        r = np.array(rows)
        ax1.semilogy(r[:, 0] * 1e3, r[:, 1], color=col, lw=1.5, label=f"{lab}: wall-normal |Uz|")
        ax1.semilogy(r[:, 0] * 1e3, r[:, 2], color=col, lw=1.5, ls=":", label=f"{lab}: tangential |Ux|")
        s = series(case)
        ax2.plot(s[:, 0] * 1e3, s[:, 3], color=col, lw=1.5, label=lab)
        print(f"  {case:18s} near-wall rows behind the meniscus, t = {r[0,0]*1e3:.2f} ms: max|Uz| {r[0,1]:.3g}, "
              f"max|Ux| {r[0,2]:.3g}; over the run max|Uz| {r[:,1].max():.3g}; gap max|U| {s[:,3].max():.3g}; "
              f"stray max {int(s[:,2].max())}")
    ax1.set_xlabel("t [ms]")
    ax1.set_ylabel("max velocity component [m/s]")
    F.style(ax1, "(c) gap cells next to the walls, behind the meniscus")
    ax1.legend(fontsize=7, frameon=False, ncol=2)
    ax2.set_xlabel("t [ms]")
    ax2.set_ylabel("max |U| in the gap [m/s]")
    F.style(ax2, "(d) max velocity in the gap")
    ax2.legend(fontsize=7, frameon=False)
    fig.suptitle("Change F′ — K 1e-20 walls with H: wall-normal velocity in the gap cells next to the walls above the "
                 "tangential one, droplets ahead of the meniscus, up to 67 m/s; removed with F′", fontsize=9)
    fig.savefig(os.path.join(F.FIGS, "Fp_near_wall_velocity.png"), dpi=140, bbox_inches="tight")


def fig_I():
    print("I:")
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
    ax = axs[0]
    tb, hb = bosanquet(8 * DX, 60)
    ax.plot(tb * 1e3, hb * 1e3, color=F.MUTED, lw=1.2, ls="--", label="Bosanquet slit rise (analytical)")
    for case, lab, col in [("S0_w8_t60", "real walls (S0)", F.C[2]), ("HF_nw8_w8_K1e-20", "porous walls, H + F′", F.C[1]),
                           ("P_w8_t60_K1e-20", "porous walls, H + F′ + I", F.C[0])]:
        s = series(case)
        ax.plot(s[:, 0] * 1e3, s[:, 1] * 1e3, color=col, marker="o", ms=3, lw=1.5, label=lab)
        print(f"  {case:18s} h at 0.5/1/2 ms: " + " / ".join(
            f"{s[np.argmin(abs(s[:, 0] - tt)), 1]*1e3:.3f}" for tt in (5e-4, 1e-3, 2e-3)) + " mm")
    print(f"  Bosanquet          h at 0.5/1/2 ms: " + " / ".join(
        f"{np.interp(tt, tb, hb)*1e3:.3f}" for tt in (5e-4, 1e-3, 2e-3)) + " mm")
    ax.set_xlabel("t [ms]")
    ax.set_ylabel("meniscus height h [mm]")
    ax.legend(fontsize=7, frameon=False)
    F.style(ax, "(a) gap meniscus, gap 8 cells (160 µm), θ 60°, K 1e-20 walls")

    ax = axs[1]
    t, i = "0.001", 10
    for case, lab, col in [("S0_w8_t60", "real walls (S0)", F.C[2]), ("HF_nw8_w8_K1e-20", "H + F′", F.C[1]),
                           ("P_w8_t60_K1e-20", "H + F′ + I", F.C[0])]:
        a, U, nw, w = fields(case, t)
        ux = U[nw:nw + w, i, 0]
        z = (np.arange(w) + 0.5) * DX * 1e6
        ax.plot(z, ux, color=col, marker="o", ms=4, lw=1.5, label=lab)
        print(f"  {case:18s} Ux across the gap at x = {X[i]*1e3:.2f} mm, t = 1 ms [m/s]: {np.round(ux, 4)}; "
              f"wall cell / gap mean = {ux[0] / ux.mean():.2f}")
    ax.set_xlabel("position across the gap [µm] (cell centres)")
    ax.set_ylabel("Ux [m/s] (cell values)")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=7, frameon=False)
    F.style(ax, f"(b) velocity across the gap at x = {X[i]*1e3:.2f} mm, t = 1 ms")
    fig.suptitle("Change I — without no-slip at the porous surface the gap water slips along the wall (wall cell "
                 "nearly as fast as the centre) and the meniscus rises too fast", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(F.FIGS, "I_no_slip.png"), dpi=140)


if __name__ == "__main__":
    os.makedirs(F.FIGS, exist_ok=True)
    fig_H()
    fig_Fp()
    fig_I()
