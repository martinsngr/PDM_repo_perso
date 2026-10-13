#!/usr/bin/env python3
"""
check.py  -  expected-behaviour checks and figure of the 2D bench (after ./Allpre and ./run).

    ../../.venv/bin/python check.py
Writes check_summary.md and check.png in this folder (results: not committed, see ../.gitignore).

Measured per written time: gap meniscus h (gap-averaged alpha < 0.5); wall fronts (alpha < 0.1) in the wall rows
next to the gap ("surface"), against the closed walls ("back") and wall-averaged; wall water (sum eps*alpha over
the porous cells, cell volumes); max |U|; stray water (gap cells with alpha > 0.05 more than 3 cells ahead of the
meniscus: droplets or films). Water budget from waterBudget.csv.

References (no exact solution for the coupled case, see ../../NOTES_solver.md "Verification"):
  - gap with impermeable walls: Bosanquet slit rise (gap 8, theta 60, from the 0.1 mm column); porous walls of
    K 1e-20 and real walls give it +8 % at 2 ms;
  - walls without gap: 1D similarity solution of the yarn, front 18.04 mm/sqrt(s), shifted so that it starts at the
    initial ramp front (x_f = 18.04 sqrt(t + t0)).
Expected: runs to the end, water budget closed, velocities ~1 m/s, no stray water; the yarn walls take water from
the gap (meniscus below the impermeable rise) and the gap feeds the walls sideways (wall front ahead of the walls
alone, uniform across the wall thickness).
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "slit_test"))
from initFields import read_internal  # noqa: E402
from slitReport import CAT, GRID, INK, MUTED, analytic  # noqa: E402

DX, NX, NW, W = 20e-6, 100, 8, 8          # cell size, cells along x, wall and gap cells (system/blockMeshDict)
NZ = 2 * NW + W
LX = NX * DX
T_END = 2e-3                              # system/controlDict endTime
LW_1D = 18.04                             # mm/sqrt(s), 1D similarity solution (front at S = 0.1)
x = (np.arange(NX) + 0.5) * DX


def times():
    return sorted((d for d in os.listdir(HERE) if re.fullmatch(r"[0-9.e+-]+", d)), key=float)


def field(t, name, vector=False):
    v = read_internal(os.path.join(HERE, t, name), NX * NZ, vector=vector)
    return v.reshape(NZ, NX, 3) if vector else v.reshape(NZ, NX)


def first_below(row, lim):
    j = np.where(row < lim)[0]
    return x[j[0]] if len(j) else LX


def stop_status():
    f = os.path.join(HERE, "log.hybridPorousInterFoam")
    txt = open(f).read() if os.path.exists(f) else ""
    m = re.findall(r"^stopGuard: (.*)$", txt, re.M)
    return m[-1] if m else "ok"


def main():
    ts = times()
    if len(ts) < 2:
        raise SystemExit("no results: run ./Allpre and ./run first")
    eps = field("0", "eps")
    por = eps <= 0.99
    R = []
    for t in ts:
        a = field(t, "alpha.wetting")
        U = np.linalg.norm(field(t, "U", True), axis=2)
        h = first_below(a[NW:NW + W].mean(axis=0), 0.5)
        ih = int(np.searchsorted(x, h))
        s = (a > 0.05) & ~por
        s[:, :ih + 3] = False
        R.append({"t": float(t), "h": h, "stray": int(s.sum()), "U": float(U.max()),
                  "wSurf": first_below((a[NW - 1] + a[NW + W]) / 2, 0.1),
                  "wBack": first_below((a[0] + a[-1]) / 2, 0.1),
                  "wMean": first_below(np.concatenate([a[:NW], a[NW + W:]]).mean(axis=0), 0.1),
                  "wallW": float((eps * a)[por].sum())})
    budget = [l.split(",") for l in open(os.path.join(HERE, "waterBudget.csv")).read().split()[1:]]
    stored = max(abs(float(b[1])) for b in budget)
    imb = max(abs(float(b[-1])) for b in budget) / stored

    tb, hb = analytic(W * DX, 60.0, T=T_END)
    bos = lambda t: float(np.interp(t, tb, hb))                     # noqa: E731
    t0 = (R[0]["wMean"] * 1e3 / LW_1D) ** 2                         # start of the similarity front at the ramp
    sim = lambda t: LW_1D * np.sqrt(t + t0) * 1e-3                  # noqa: E731
    at = lambda t, k: min(R, key=lambda r: abs(r["t"] - t))[k]      # noqa: E731
    end = R[-1]

    checks = []

    def check(name, value, ok, crit):
        checks.append((name, value, "yes" if ok else "**NO**", crit))

    check("reaches the end time", f"{end['t'] * 1e3:.2f} ms ({stop_status()})",
          end["t"] >= T_END - 1e-9 and stop_status() == "ok", f"{T_END * 1e3:g} ms, no stopGuard")
    check("water budget", f"max imbalance/stored {imb:.1e}", imb < 1e-10, "< 1e-10")
    umax = max(r["U"] for r in R[1:])
    check("max |U| (all writes)", f"{umax:.2f} m/s", umax < 2.0, "< 2 m/s (real-wall slit ~1)")
    smax = max(r["stray"] for r in R)
    check("stray water ahead of the meniscus", f"max {smax} cells", smax <= 5, "<= 5 cells")
    for t in (1e-3, T_END):
        check(f"walls take water from the gap, {t * 1e3:.0f} ms",
              f"meniscus {at(t, 'h') * 1e3:.3f} < {bos(t) * 1e3:.3f} mm (impermeable, Bosanquet)",
              at(t, "h") < bos(t), "below the impermeable rise")
        check(f"gap feeds the walls, {t * 1e3:.0f} ms",
              f"wall front {at(t, 'wMean') * 1e3:.3f} > {sim(t) * 1e3:.3f} mm (walls alone, 1D)",
              at(t, "wMean") > sim(t), "ahead of the walls alone")
    dfr = max(abs(r["wSurf"] - r["wBack"]) for r in R if r["t"] >= 5e-4)
    check("wall front uniform across the wall (from 0.5 ms)", f"max |surface - back| {dfr * 1e6:.0f} um",
          dfr <= 2 * DX + 1e-12, "<= 2 cells (lateral imbibition faster than the front)")
    wl = [r["wallW"] for r in R]
    check("wall water increases", f"{wl[0]:.1f} -> {wl[-1]:.1f} cell volumes",
          all(b >= a - 1e-6 for a, b in zip(wl, wl[1:])), "monotone")

    with open(os.path.join(HERE, "check_summary.md"), "w") as f:
        f.write("# 2D bench: expected-behaviour checks\n\n| Check | Value | Pass | Criterion |\n|---|---|---|---|\n")
        for n, v, ok, cr in checks:
            f.write(f"| {n} | {v} | {ok} | {cr} |\n")
        f.write("\n| t [ms] | gap meniscus [mm] | wall front surface / back / mean [mm] | wall water [cell vol.] "
                "| max \\|U\\| [m/s] |\n|---|---|---|---|---|\n")
        for t in (2.5e-4, 5e-4, 1e-3, 1.5e-3, T_END):
            f.write(f"| {t * 1e3:.2f} | {at(t, 'h') * 1e3:.3f} | {at(t, 'wSurf') * 1e3:.3f} / {at(t, 'wBack') * 1e3:.3f}"
                    f" / {at(t, 'wMean') * 1e3:.3f} | {at(t, 'wallW'):.0f} | {at(t, 'U'):.2f} |\n")
    print(open(os.path.join(HERE, "check_summary.md")).read())

    # ---- figure: gap meniscus and wall front vs t with their references, alpha map at the end
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.0), gridspec_kw={"width_ratios": [1, 1, 1.25]})
    tm = [r["t"] * 1e3 for r in R]
    ax[0].plot(tm, [r["h"] * 1e3 for r in R], color=CAT[0], lw=2, label="gap meniscus (yarn walls)")
    ax[0].plot(tb * 1e3, hb * 1e3, color=INK, lw=1, ls=(0, (2, 2)), label="impermeable walls (Bosanquet)")
    ax[0].set(xlabel="t [ms]", ylabel="height [mm]", title="Gap: meniscus rise")
    ax[1].plot(tm, [r["wMean"] * 1e3 for r in R], color=CAT[1], lw=2, label="wall front, wall average")
    ax[1].plot(tm, [r["wSurf"] * 1e3 for r in R], color=CAT[2], lw=2, ls="--", label="wall front, gap side")
    tt = np.linspace(0, T_END, 80)
    ax[1].plot(tt * 1e3, sim(tt) * 1e3, color=INK, lw=1, ls=(0, (2, 2)), label="walls alone (1D similarity)")
    ax[1].set(xlabel="t [ms]", ylabel="front position (α = 0.1) [mm]", title="Walls: imbibition front")
    for a in ax[:2]:
        a.grid(color=GRID, lw=0.6)
        a.set_xlim(0, T_END * 1e3)
        a.set_ylim(bottom=0)
        a.legend(frameon=False, fontsize=7.5, loc="upper left")
    im = ax[2].imshow(field(ts[-1], "alpha.wetting"), origin="lower", cmap="Blues", vmin=0, vmax=1, aspect="auto",
                      extent=(0, LX * 1e3, 0, NZ * DX * 1e3))
    for zz in (NW * DX * 1e3, (NW + W) * DX * 1e3):
        ax[2].axhline(zz, color=MUTED, lw=0.8, ls="--")
    ax[2].text(1.95, (NW + W / 2) * DX * 1e3, "gap", ha="right", va="center", color=INK, fontsize=8)
    ax[2].text(1.95, NW / 2 * DX * 1e3, "yarn wall", ha="right", va="center", color=INK, fontsize=8)
    ax[2].set(xlabel="x, wicking direction [mm]", ylabel="z [mm]",
              title=f"Water saturation α at t = {end['t'] * 1e3:.1f} ms")
    fig.colorbar(im, ax=ax[2], label="α (pore saturation in the walls)", shrink=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "check.png"), dpi=150)
    print("check.png written")
    sys.exit(0 if all(ok == "yes" for _, _, ok, _ in checks) else 1)


if __name__ == "__main__":
    main()
