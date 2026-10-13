#!/usr/bin/env python3
"""
benchReport.py  -  figures and pass/fail summary of the 2D bench run set with change G.

Run from 2D_bench/variants after
    for v in fullSlabClosed gapInletAir base R1staticWet R2waterGap R3closedRamp R3closedRampSlab; do
        WRITE=1e-4 ./makeVariant.sh $v run 5e-3; done
with:  ../../../.venv/bin/python benchReport.py
Writes figures/*.png and figures/summary.md.

Bench: 50 x 1 x 15 cells of 20 um (x along the yarn, z across); yarn (porous slab) rows k = 3..10 except in the
all-porous runs; reference for the front: 1D similarity solution of ../../trialWicking/verification (same K, eps,
Brooks-Corey n 3, Van Genuchten pc0 5000 Pa m 0.5, S_in 0.99, S0 0.002): x_f = 18.04 mm/sqrt(s) * sqrt(t) at S = 0.1.
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, "../../tools")
from initFields import read_internal, read_owner, read_boundary, strip_header, read_list  # noqa: E402

NX, NZ, DX = 50, 15, 20e-3            # cells, cell size [mm]
A = (DX * 1e-3) ** 2                  # face area [m2] (2D, depth one cell of 20 um)
XF_SLOPE = 18.04                      # mm/sqrt(s), 1D similarity front at S = 0.1
PC0, M_VG, SMAX = 5000.0, 0.5, 0.999

INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
C_REF, C_GAP, C_BASE = "#2a78d6", "#eb6834", "#1baf7a"      # categorical slots 1-3
SEQ = LinearSegmentedColormap.from_list("blue", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
TIME_RAMP = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]    # ordinal, light -> dark = early -> late
plt.rcParams.update({"font.size": 9, "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": MUTED, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.spines.top": False,
                     "axes.spines.right": False})

RUNS = {"fullSlabClosed": "fullSlabClosed_run", "gapInletAir": "gapInletAir_run", "base": "base_run",
        "R1": "R1staticWet_run", "R2": "R2waterGap_run", "R3": "R3closedRamp_run", "R3ref": "R3closedRampSlab_run"}
LABEL = {"fullSlabClosed": "yarn alone (no gaps): reference", "gapInletAir": "yarn + air gaps",
         "base": "yarn + gaps, reservoir water also in the gaps"}


def times(c):
    return sorted((d for d in os.listdir(c) if re.fullmatch(r"[0-9.e+-]+", d)), key=float)


def field(c, t, name, vector=False):
    v = read_internal(f"{c}/{t}/{name}", NX * NZ, vector=vector)
    return v.reshape(NZ, NX, 3) if vector else v.reshape(NZ, NX)


def porous(c):
    return field(c, "0", "eps") <= 0.99


def pc_vg(a):
    se = np.clip(a / SMAX, 1e-4, 1 - 1e-4)
    return PC0 * (se ** (-1 / M_VG) - 1) ** (1 - M_VG)


def yarn_profile(a, por):
    return np.array([a[por[:, i], i].mean() for i in range(NX)])


def front(p, level=0.1):
    x = (np.arange(NX) + 0.5) * DX
    i = np.where(p < level)[0]
    if not len(i) or i[0] == 0:
        return np.nan
    i = i[0]
    return x[i - 1] + (p[i - 1] - level) / (p[i - 1] - p[i]) * DX


def read_csv(path):
    lines = open(path).read().split()
    head = lines[0].split(",")
    rows = np.array([[float(v) for v in ln.split(",")] for ln in lines[1:]])
    return head, rows


def flux_velocity(c, t):
    """cell velocity from the face fluxes (uniform orthogonal grid), as in the earlier analyses"""
    own = read_owner(c)
    nei = np.array(read_list(strip_header(open(f"{c}/constant/polyMesh/neighbour").read()))[1].split(), int)
    txt = strip_header(open(f"{c}/{t}/phi").read())
    n, body = read_list(txt, re.search(r"internalField\s+nonuniform", txt).end())
    phi = np.array(body.split(), float)
    sx = np.zeros(NX * NZ); sz = np.zeros(NX * NZ)
    for f, (o, nn) in enumerate(zip(own[:len(nei)], nei)):
        (sx if nn - o == 1 else sz)[[o, nn]] += phi[f]
    return np.hypot(sx, sz).reshape(NZ, NX) / 2 / A      # boundary faces omitted (interior cells exact)


def main():
    os.makedirs("figures", exist_ok=True)
    have = {k: os.path.isdir(v) for k, v in RUNS.items()}
    missing = [RUNS[k] for k, h in have.items() if not h]
    if missing:
        print("missing:", missing)
    summary = []

    # ---------------------------------------------------------------- 1. alpha maps
    show = [k for k in ("fullSlabClosed", "gapInletAir", "base") if have[k]]
    tshow = ["0.0005", "0.0015", "0.003", "0.005"]
    fig, axs = plt.subplots(len(show), len(tshow), figsize=(11, 1.35 * len(show) + 1.0), squeeze=False,
                            constrained_layout=True)
    for i, k in enumerate(show):
        c = RUNS[k]; por = porous(c); ts = times(c)
        for j, t in enumerate(tshow):
            ax = axs[i, j]
            if t not in ts:      # run stopped before this time
                ax.set_xlim(0, NX * DX); ax.set_ylim(0, NZ * DX); ax.set_aspect("equal")
                ax.text(0.5, 0.5, f"run stopped at\n{float(ts[-1]) * 1e3:.2f} ms", transform=ax.transAxes,
                        ha="center", va="center", color=MUTED, fontsize=8)
                ax.set_xticks([0, 0.5, 1.0]); ax.set_yticks([0, 0.3])
                if i == 0:
                    ax.set_title(f"t = {float(t) * 1e3:g} ms", fontsize=9)
                if i < len(show) - 1:
                    ax.set_xticklabels([])
                continue
            tt = t
            im = ax.imshow(field(c, tt, "alpha.wetting"), origin="lower", extent=[0, NX * DX, 0, NZ * DX],
                           cmap=SEQ, vmin=0, vmax=1, aspect="equal", interpolation="nearest")
            if not por.all():
                for z in (3 * DX, 11 * DX):
                    ax.axhline(z, color=MUTED, lw=0.7, ls="--")
            ax.set_xticks([0, 0.5, 1.0]); ax.set_yticks([0, 0.3])
            if i == 0:
                ax.set_title(f"t = {float(tt) * 1e3:g} ms", fontsize=9)
            if j == 0:
                ax.set_ylabel(LABEL[k], rotation=0, ha="right", va="center", fontsize=8)
            if i < len(show) - 1:
                ax.set_xticklabels([])
    axs[-1, 0].set_xlabel("x [mm] (reservoir at x = 0); z [mm]; dashed = yarn surface")
    fig.colorbar(im, ax=axs, shrink=0.7, label="water saturation alpha")
    fig.suptitle("2D bench with change G: water saturation", fontsize=11)
    fig.savefig("figures/bench_alpha_maps.png", dpi=150); plt.close(fig)

    # ---------------------------------------------------------------- 2. front vs sqrt(t)
    fig, ax = plt.subplots(figsize=(6.5, 4.2), constrained_layout=True)
    st = np.linspace(0, np.sqrt(5e-3), 50)
    ax.plot(st, XF_SLOPE * st, color=MUTED, lw=1.2, ls="--", label="1D similarity solution, 18.04 mm/√s")
    fits = {}
    for k, col in (("fullSlabClosed", C_REF), ("gapInletAir", C_GAP), ("base", C_BASE)):
        if not have[k]:
            continue
        c = RUNS[k]; por = porous(c); ts = [t for t in times(c) if float(t) > 0]
        tv = np.array([float(t) for t in ts]); xf = np.array([front(yarn_profile(field(c, t, "alpha.wetting"), por)) for t in ts])
        ax.plot(np.sqrt(tv), xf, color=col, lw=2, label=LABEL[k])
        ok = (tv >= 5e-4) & (xf < 0.9) & np.isfinite(xf)
        if ok.sum() >= 3:
            b, a0 = np.polyfit(np.sqrt(tv[ok]), xf[ok], 1)
            fits[k] = (b, a0, tv[ok].min(), tv[ok].max())
    ax.axhline(NX * DX, color=MUTED, lw=0.8, ls=":")
    ax.text(np.sqrt(5e-3), NX * DX + 0.02, "outlet", color=MUTED, fontsize=8, ha="right")
    ax.set_xlabel("√t [√s]"); ax.set_ylabel("front position (yarn mean saturation 0.1) [mm]")
    ax.set_ylim(0, 1.15); ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Front position vs √t", fontsize=11)
    fig.savefig("figures/bench_front_sqrt_t.png", dpi=150); plt.close(fig)

    # ---------------------------------------------------------------- 3. yarn profiles
    if have["fullSlabClosed"] and have["gapInletAir"]:
        fig, ax = plt.subplots(figsize=(6.5, 4.0), constrained_layout=True)
        x = (np.arange(NX) + 0.5) * DX
        porG = porous(RUNS["gapInletAir"]); porR = porous(RUNS["fullSlabClosed"])
        maxdiff = []
        for col, t in zip(TIME_RAMP, ("0.0005", "0.001", "0.002", "0.003")):
            pg = yarn_profile(field(RUNS["gapInletAir"], t, "alpha.wetting"), porG)
            pr = yarn_profile(field(RUNS["fullSlabClosed"], t, "alpha.wetting"), porR)
            maxdiff.append((t, np.abs(pg - pr).max()))
            ax.plot(x, pg, color=col, lw=2, label=f"{float(t) * 1e3:g} ms, yarn + air gaps")
            ax.plot(x, pr, color=col, lw=1.2, ls="--")
        ax.plot([], [], color=MUTED, ls="--", label="dashed: yarn alone (reference)")
        ax.set_xlabel("x [mm]"); ax.set_ylabel("yarn mean water saturation")
        ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8)
        ax.set_title("Yarn saturation profiles: with air gaps vs alone", fontsize=11)
        fig.savefig("figures/bench_profiles.png", dpi=150); plt.close(fig)

    # ---------------------------------------------------------------- 4. water budget
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), constrained_layout=True)
    budget = {}
    for k, col in (("fullSlabClosed", C_REF), ("gapInletAir", C_GAP), ("base", C_BASE)):
        if not have[k] or not os.path.exists(f"{RUNS[k]}/waterBudget.csv"):
            continue
        head, r = read_csv(f"{RUNS[k]}/waterBudget.csv")
        t = r[:, 0] * 1e3; w = r[:, 1]; tin = r[:, head.index("in_total")]; imb = r[:, head.index("imbalance")]
        axs[0].plot(t, (w - w[0]) * 1e12, color=col, lw=2, label=f"{LABEL[k]}: stored")
        axs[0].plot(t, tin * 1e12, color=col, lw=1.2, ls="--")
        rel = imb / np.maximum(np.abs(w - w[0]), 1e-30)
        axs[1].plot(t, np.abs(imb) * 1e12, color=col, lw=2, label=LABEL[k])
        budget[k] = (w[-1] - w[0], tin[-1], imb[-1], np.abs(imb).max())
    axs[0].plot([], [], color=MUTED, ls="--", label="dashed: entered through the boundaries")
    axs[0].set_xlabel("t [ms]"); axs[0].set_ylabel("water volume change [1e-12 m³]")
    axs[0].legend(frameon=False, fontsize=7); axs[0].grid(True, color=GRID, lw=0.6)
    axs[1].set_yscale("log"); axs[1].set_xlabel("t [ms]"); axs[1].set_ylabel("|stored − entered| [1e-12 m³]")
    axs[1].grid(True, color=GRID, lw=0.6); axs[1].legend(frameon=False, fontsize=7)
    fig.suptitle("Water budget (waterBudget function object)", fontsize=11)
    fig.savefig("figures/bench_water_budget.png", dpi=150); plt.close(fig)

    # ---------------------------------------------------------------- 5. pressure check at the yarn surface
    pres = {}
    if have["gapInletAir"]:
        c = RUNS["gapInletAir"]; ts = [t for t in times(c) if float(t) > 0]
        tv, dmax, scale, dmax1, dmed = [], [], [], [], []
        for t in ts:
            a = field(c, t, "alpha.wetting"); p = field(c, t, "p")
            pair = p + a * pc_vg(a)                     # air pressure in porous cells
            d = np.concatenate([pair[10] - p[11], pair[3] - p[2]])
            tv.append(float(t)); dmax.append(np.abs(d).max())
            d1 = np.concatenate([(pair[10] - p[11])[1:], (pair[3] - p[2])[1:]])     # without the inlet column
            dmax1.append(np.abs(d1).max()); dmed.append(np.median(np.abs(d)))
            scale.append(np.concatenate([(a * pc_vg(a))[10], (a * pc_vg(a))[3]]).max())
        fig, ax = plt.subplots(figsize=(6.5, 3.8), constrained_layout=True)
        ax.semilogy(np.array(tv) * 1e3, scale, color=MUTED, lw=1.2, ls="--", label="α·pc in the yarn edge cells (size of the jump)")
        ax.semilogy(np.array(tv) * 1e3, dmax, color=C_GAP, lw=2, label="max |p_air(yarn edge) − p(gap)|, incl. inlet column")
        ax.semilogy(np.array(tv) * 1e3, dmax1, color=C_REF, lw=2, label="same, without the inlet column")
        ax.semilogy(np.array(tv) * 1e3, np.maximum(dmed, 1e-2), color=C_BASE, lw=1.5, label="median over the yarn surface")
        ax.set_xlabel("t [ms]"); ax.set_ylabel("pressure [Pa]"); ax.grid(True, color=GRID, lw=0.6)
        ax.legend(frameon=False, fontsize=8)
        ax.set_title("Air pressure across the yarn surface (yarn + air gaps)", fontsize=11)
        fig.savefig("figures/bench_pressure_jump.png", dpi=150); plt.close(fig)
        pres = (max(dmax), max(dmax1), max(dmed), min(scale), max(scale))

    # ---------------------------------------------------------------- 6. referees
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), constrained_layout=True)
    ref = {}
    if have["R1"]:
        c = RUNS["R1"]; por = porous(c); eps = field(c, "0", "eps"); ts = times(c)
        w0 = (eps * field(c, "0", "alpha.wetting"))[por].sum()
        tv = [float(t) * 1e3 for t in ts]; ww = [((eps * field(c, t, "alpha.wetting"))[por].sum() / w0 - 1) * 100 for t in ts]
        gu = [flux_velocity(c, t)[~por].max() for t in ts[1:]]
        axs[0].plot(tv, ww, color=C_REF, lw=2, label="yarn water change [%]")
        ax2 = axs[0].twinx(); ax2.semilogy(tv[1:], gu, color=C_GAP, lw=1.5); ax2.set_ylabel("max gap velocity [m/s]", color=C_GAP)
        axs[0].set_title("R1: wet yarn at rest next to air gaps", fontsize=9); axs[0].set_xlabel("t [ms]")
        axs[0].set_ylabel("yarn water change [%]"); axs[0].grid(True, color=GRID, lw=0.6)
        ref["R1"] = (ww[-1], max(gu))
    if have["R2"]:
        c = RUNS["R2"]; por = porous(c); eps = field(c, "0", "eps"); ts = times(c)
        tv = [float(t) * 1e3 for t in ts]; yw = [(eps * field(c, t, "alpha.wetting"))[por].sum() for t in ts]
        axs[1].plot(tv, yw, color=C_REF, lw=2)
        axs[1].set_title("R2: dry yarn next to a water-filled gap", fontsize=9); axs[1].set_xlabel("t [ms]")
        axs[1].set_ylabel("water in the yarn [cell volumes]"); axs[1].grid(True, color=GRID, lw=0.6)
        ref["R2"] = (yw[0], yw[-1], (eps * 1)[por].sum())
    if have["R3"] and have["R3ref"]:
        c, r = RUNS["R3"], RUNS["R3ref"]; por = porous(c); eps = field(c, "0", "eps")
        ts = sorted(set(times(c)) & set(times(r)), key=float)
        w0 = (eps * field(c, "0", "alpha.wetting"))[por].sum()
        tv, dd, wl = [], [], []
        for t in ts:
            a = field(c, t, "alpha.wetting"); b = field(r, t, "alpha.wetting")
            tv.append(float(t) * 1e3); dd.append(np.abs(yarn_profile(a, por) - b.mean(0)).max())
            wl.append(((eps * a)[por].sum() / w0 - 1) * 100)
        axs[2].semilogy(tv[1:], dd[1:], color=C_GAP, lw=2, label="max |yarn profile − reference|")
        axs[2].set_title("R3: wet ramp redistributing, gaps vs no gaps", fontsize=9); axs[2].set_xlabel("t [ms]")
        axs[2].set_ylabel("max profile difference [–]"); axs[2].grid(True, color=GRID, lw=0.6)
        ref["R3"] = (max(dd[1:]), dd[-1], min(wl), wl[-1])
    fig.suptitle("Referee tests (closed walls, no reservoir)", fontsize=11)
    fig.savefig("figures/bench_referees.png", dpi=150); plt.close(fig)

    # ---------------------------------------------------------------- summary
    L = ["# 2D bench with change G: summary", "",
         "Installed solver (of9-port 1b007d8), `porousFreeDarcyFaces on`, free cells initialised as pure air, 5 ms, writes every 0.1 ms.", ""]
    L.append("| Check | Result | Criterion | Pass |")
    L.append("|---|---|---|---|")
    for k in ("fullSlabClosed", "gapInletAir", "base"):
        if not have[k]:
            continue
        st = open(f"{RUNS[k]}/log.hybridPorousInterFoam").read() if os.path.exists(f"{RUNS[k]}/log.hybridPorousInterFoam") else ""
        end = times(RUNS[k])[-1]
        L.append(f"| {LABEL[k]}: reaches 5 ms | ended at {float(end) * 1e3:g} ms | 5 ms | {'yes' if float(end) >= 5e-3 - 1e-12 else 'NO'} |")
    for k, (b, a0, t0, t1) in fits.items():
        L.append(f"| front slope, {LABEL[k]} | {b:.2f} mm/√s (fit {t0 * 1e3:g}–{t1 * 1e3:g} ms, offset {a0:+.3f} mm) | ≈ 18.04 (1D similarity; gaps: slightly faster expected) | {'yes' if abs(b / XF_SLOPE - 1) < 0.1 or k == 'base' else 'check'} |")
    for k, (dw, tin, imb, imbmax) in budget.items():
        L.append(f"| water budget, {LABEL[k]} | stored {dw:.3e} m³, entered {tin:.3e} m³, max imbalance {imbmax:.1e} m³ ({imbmax / max(abs(dw), 1e-30):.1e} rel.) | imbalance ≪ stored | {'yes' if imbmax < 1e-3 * abs(dw) else 'check'} |")
    if have["fullSlabClosed"] and have["gapInletAir"]:
        L.append(f"| yarn profile, air gaps vs alone | max diff {', '.join(f'{float(t) * 1e3:g} ms: {d:.3f}' for t, d in maxdiff)} | small (air escape speeds the gap case up) | see figure |")
    if pres:
        L.append(f"| air pressure across the yarn surface (G's condition) | max {pres[1]:.0f} Pa without the inlet column (median ≤ {pres[2]:.0f} Pa); inlet column up to {pres[0]:.0f} Pa (air back-pressure next to the reservoir, physical); α·pc {pres[3]:.0f}–{pres[4]:.0f} Pa (difference without G) | ≪ α·pc away from the inlet | {'yes' if pres[1] < 0.05 * pres[3] else 'check'} |")
    if "R1" in ref:
        L.append(f"| R1 static: yarn water change / max gap velocity | {ref['R1'][0]:+.4f} % / {ref['R1'][1]:.1e} m/s | ~0 / small | {'yes' if abs(ref['R1'][0]) < 0.01 else 'NO'} |")
    if "R2" in ref:
        L.append(f"| R2 dry yarn next to water: yarn water | {ref['R2'][0]:.2f} → {ref['R2'][1]:.2f} (capacity {ref['R2'][2]:.0f}) | increases | {'yes' if ref['R2'][1] > 10 * ref['R2'][0] else 'NO'} |")
    if "R3" in ref:
        L.append(f"| R3 closed ramp: profile vs no-gap reference / yarn water | max {ref['R3'][0]:.1e}, at 5 ms {ref['R3'][1]:.1e} / min {ref['R3'][2]:+.4f} %, end {ref['R3'][3]:+.4f} % | ≪ 0.01 / ~0 | {'yes' if ref['R3'][0] < 0.01 and abs(ref['R3'][3]) < 0.01 else 'NO'} |")
    open("figures/summary.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
