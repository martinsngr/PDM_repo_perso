#!/usr/bin/env python3
"""
slitReport.py  -  meniscus rise in the slit benchmarks (makeSlit.py) vs the analytical slit rise.

    ../../.venv/bin/python slitReport.py            (from this folder)
Writes figures/slit_*.png and figures/summary.md.

Meniscus height h(t): along x, mean alpha over the gap cells; h = first x where it drops below 0.5 (interpolated).
Reference: rise in a slit of width w with inertia, viscous (plane Poiseuille) drag and gravity (Bosanquet form),
    rho d(h dh/dt)/dt = 2 sigma cos(theta)/w - 12 mu h (dh/dt)/w^2 - rho g h,   h(0) = fill (0.1 mm), dh/dt(0) = 0
(water accelerated from rest in the reservoir: matches the total-pressure inlet of makeSlit.py). No dynamic contact
angle, air neglected. Wall front (porous walls): first x where the wall-averaged alpha < 0.1.
Only the cases of the current setup (slit.info "inlet total") are reported; old runs are in old_runs/.
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, "../tools")
from initFields import read_internal  # noqa: E402

DX = 20e-6
NXC = 100
SIGMA, RHO, MU, G = 0.072, 1000.0, 1e-3, 9.81
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
plt.rcParams.update({"font.size": 9, "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": MUTED, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.spines.top": False,
                     "axes.spines.right": False})


def info(c):
    d = dict(l.split() for l in open(f"{c}/slit.info"))
    return d["walls"], int(d["w"]), float(d["theta"]), float(d["K"]), int(d["NW"]), int(d["nz"])


def fill(c):
    d = dict(l.split() for l in open(f"{c}/slit.info"))
    return float(d.get("fill", 0)), d.get("inlet", "static")


def readU(path):
    s = open(path).read()
    m = re.search(r"internalField\s+nonuniform List<vector>\s*\n\d+\s*\n\(", s)
    if not m:
        return 0.0
    v = [l.strip("()").split() for l in s[m.end():s.index("\n)", m.end())].split("\n") if l.strip()]
    return float(np.abs(np.array(v, dtype=float)).max())


def times(c):
    return sorted((t for t in os.listdir(c) if re.fullmatch(r"[0-9.e+-]+", t)), key=float)


def meniscus(c):
    walls, w, th, K, nw, nz = info(c)
    out = []
    for t in times(c):
        a = read_internal(f"{c}/{t}/alpha.wetting", NXC * nz).reshape(nz, NXC)
        g = a[nw:nw + w].mean(axis=0)                       # gap-averaged alpha along x
        x = (np.arange(NXC) + 0.5) * DX
        i = np.where(g < 0.5)[0]
        if not len(i):
            h = NXC * DX
        elif i[0] == 0:
            h = 0.0
        else:
            i = i[0]; h = x[i - 1] + (g[i - 1] - 0.5) / (g[i - 1] - g[i]) * DX
        wf = np.nan
        if nw:
            gw = np.concatenate([a[:nw], a[nw + w:]]).mean(axis=0)
            j = np.where(gw < 0.1)[0]
            wf = x[j[0]] if len(j) else NXC * DX
        out.append((float(t), h, wf, readU(f"{c}/{t}/U")))
    return np.array(out)


def analytic(w_m, theta, h0=1e-4, T=2e-3):
    A = 2 * SIGMA * np.cos(np.radians(theta)) / (RHO * w_m)
    B = 12 * MU / (RHO * w_m ** 2)

    def f(t, y):
        h, q = y                                  # q = h dh/dt
        return [q / h, A - B * q - G * h]
    s = solve_ivp(f, (0, T), [h0, 0.0], max_step=T / 2000, rtol=1e-8, atol=1e-12)
    return s.t, s.y[0]


def status(c):
    f = f"{c}/log.hybridPorousInterFoam"
    txt = open(f).read() if os.path.exists(f) else ""
    m = re.findall(r"^stopGuard: (.*)$", txt, re.M)
    return m[-1] if m else "ok"


def main():
    os.makedirs("figures", exist_ok=True)
    cases = sorted(d for d in os.listdir(".") if d.startswith("S") and os.path.isfile(f"{d}/slit.info")
                   and fill(d)[1] == "total")
    H = {c: meniscus(c) for c in cases}

    def curve(ax, c, col, ls="-", lab=None, k=1):
        if c in H:
            ax.plot(H[c][:, 0] * 1e3, H[c][:, k] * 1e3, color=col, lw=2, ls=ls, label=lab)

    def style(ax, title):
        ax.set_title(title, fontsize=9); ax.set_xlabel("t [ms]"); ax.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True); ax.set_ylim(0, 2.1); ax.axhline(2.0, color=MUTED, lw=0.6, ls=":")

    def sweep(fname, params, title):
        fig, axs = plt.subplots(2, 3, figsize=(12, 6.4), constrained_layout=True,
                                gridspec_kw={"height_ratios": [2, 1]}, sharex=True)
        for j, (w, th) in enumerate(params):
            ax = axs[0, j]
            ta, ha = analytic(w * DX, th)
            ax.plot(ta * 1e3, ha * 1e3, color=MUTED, lw=1.2, ls="--", label="analytical slit rise (Bosanquet)")
            curve(ax, f"S0_w{w}_t{th}", CAT[0], lab="real walls + contact-angle BC (S0)")
            curve(ax, f"S1_w{w}_t{th}", CAT[1], lab="porous walls K 1e-20 + porous contact angle (S1)")
            style(ax, f"gap {w} cells ({w * 20} µm), θ = {th}°")
            b = axs[1, j]
            for c, col in ((f"S0_w{w}_t{th}", CAT[0]), (f"S1_w{w}_t{th}", CAT[1])):
                if c in H:
                    b.plot(H[c][1:, 0] * 1e3, H[c][1:, 3], color=col, lw=2)
            b.set_yscale("log"); b.set_xlabel("t [ms]"); b.grid(True, color=GRID, lw=0.6)
        axs[0, 0].set_ylabel("meniscus height in the gap [mm]"); axs[1, 0].set_ylabel("max |U| [m/s]")
        axs[0, 0].legend(frameon=False, fontsize=7)
        fig.suptitle(title, fontsize=11); fig.savefig(f"figures/{fname}", dpi=150); plt.close(fig)

    sweep("slit_widths.png", [(4, 60), (8, 60), (15, 60)], "Slit rise vs gap width (0.1 mm initial column, reservoir at rest)")
    sweep("slit_angles.png", [(8, 40), (8, 60), (8, 80)], "Slit rise vs contact angle, gap 8 cells")

    # wall permeability: gap meniscus, wall front, max |U|
    seq = [("K 1e-20 (S1)", "S1_w8_t60", CAT[1]), ("K 1e-17 (S3)", "S3_w8_t60_K1e-17", CAT[2]),
           ("K 1e-14 (S3)", "S3_w8_t60_K1e-14", CAT[3]), ("K 1e-11, yarn-like (S2)", "S2_w8_t60_K1e-11", CAT[4])]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.9), constrained_layout=True)
    ta, ha = analytic(8 * DX, 60)
    axs[0].plot(ta * 1e3, ha * 1e3, color=MUTED, lw=1.2, ls="--", label="analytical slit rise (impermeable)")
    curve(axs[0], "S0_w8_t60", CAT[0], lab="real walls (S0)")
    for lab, c, col in seq:
        curve(axs[0], c, col, lab=lab)
        curve(axs[1], c, col, lab=lab, k=2)
        if c in H:
            axs[2].plot(H[c][1:, 0] * 1e3, H[c][1:, 3], color=col, lw=2, label=lab)
    xs = np.linspace(0, 2e-3, 100)
    axs[1].plot(xs * 1e3, 18.04 * np.sqrt(xs), color=MUTED, lw=1.2, ls="--", label="yarn alone, 1D (18.04 mm/√s)")
    style(axs[0], "gap meniscus"); style(axs[1], "wall front (wall-averaged α < 0.1)")
    axs[2].set_yscale("log"); axs[2].set_xlabel("t [ms]"); axs[2].grid(True, color=GRID, lw=0.6)
    axs[2].set_title("max |U| (spurious currents)", fontsize=9)
    axs[0].set_ylabel("height [mm]"); axs[2].set_ylabel("max |U| [m/s]")
    axs[0].legend(frameon=False, fontsize=7); axs[1].legend(frameon=False, fontsize=7)
    fig.suptitle("Gap 8 cells, θ = 60°: porous walls of increasing permeability", fontsize=11)
    fig.savefig("figures/slit_permeability.png", dpi=150); plt.close(fig)

    # summary
    L = ["# Slit tests: meniscus height vs analytical slit rise (Bosanquet from the 0.1 mm column)", "",
         "| case | walls | gap [cells] | θ | K walls | end | h(0.5 ms) sim / analytic [mm] | h(1 ms) | h(2 ms) "
         "| wall front 2 ms [mm] | max \\|U\\| [m/s] |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cases:
        walls, w, th, K, nw, nz = info(c)
        ta, ha = analytic(w * DX, th, fill(c)[0] or 1e-6)
        A = H[c]

        def at(t, k=1):
            return np.interp(t, A[:, 0], A[:, k]) * 1e3 if A[-1, 0] >= t - 1e-9 else np.nan
        cells = [f"{at(t):.2f} / {np.interp(t, ta, ha) * 1e3:.2f}" for t in (5e-4, 1e-3, 2e-3)]
        L.append(f"| {c} | {walls} | {w} | {th:g}° | {K:g} | {A[-1, 0] * 1e3:.2f} ms ({status(c)}) | "
                 + " | ".join(cells) + f" | {at(2e-3, 2):.2f} | {A[1:, 3].max():.2g} |")
    open("figures/summary.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
