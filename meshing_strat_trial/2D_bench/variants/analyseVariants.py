#!/usr/bin/env python3
"""
analyseVariants.py  -  figures and summary table of the 2D bench variants (makeVariant.sh).

Run from 2D_bench/variants:   ../../../.venv/bin/python analyseVariants.py [mode]
  mode = steps (default) or run: which variant folders (<variant>_<mode>) to read.
Writes figures/<mode>_alpha.png   alpha.wetting maps (x-z) at t = 0, after step 1 and at the last write
       figures/<mode>_p.png       p maps after step 1 and at the last write
       figures/<mode>_dt.png      deltaT per time step (log scale)
       figures/<mode>_summary.md  one row per variant
Mesh: the bench block, 50 x 1 x 15 cells (x fastest, then z), 20 um cells; porous cells from 0/eps.
"""
import glob
import gzip
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, SymLogNorm

sys.path.insert(0, "../../tools")
from initFields import read_internal  # noqa: E402

NX, NZ, DX = 50, 15, 20e-3            # cells, cell size [mm]
ORDER = ["base", "ca90", "sigma0", "pcMild", "noRamp", "airZero0", "fullSlab", "paperLike", "closedTB", "fullSlabClosed"]
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948", "#6b6a64", "#1f1f1e"]
SEQ = LinearSegmentedColormap.from_list("blue", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div", ["#104281", "#3987e5", "#f0efec", "#e66767", "#a32020"])
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
plt.rcParams.update({"font.size": 9, "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": MUTED, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb"})


def times(case):
    return sorted((d for d in os.listdir(case) if re.fullmatch(r"[0-9.e+-]+", d)), key=float)


def grid(a):
    return a.reshape(NZ, NX)


def log_dt(case):
    f = os.path.join(case, "log.hybridPorousInterFoam")
    txt = open(f).read() if os.path.exists(f) else gzip.open(f + ".gz", "rt").read()
    dts = [float(x) for x in re.findall(r"^deltaT = (\S+)", txt, re.M)]
    stop = re.findall(r"^stopGuard: (.*)$", txt, re.M)
    crash = "Floating point exception" in txt or "FOAM FATAL" in txt
    return np.array(dts), (stop[-1] if stop else ("crash" if crash else "endTime")), crash


def slab_edges(porous):
    """z (mm) of the porous/free boundaries, for the dashed outline."""
    col = grid(porous)[:, 0]
    return [DX * k for k in range(1, NZ) if col[k] != col[k - 1]]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "steps"
    cases = {os.path.basename(c)[:-len(mode) - 1]: c for c in glob.glob(f"*_{mode}") if os.path.isdir(c)}
    names = [v for v in ORDER if v in cases]
    if not names:
        raise SystemExit(f"no *_{mode} folders")
    os.makedirs("figures", exist_ok=True)
    ext = [0, NX * DX, 0, NZ * DX]
    data, rows = {}, []
    for v in names:
        c = cases[v]
        ts = times(c)
        n = NX * NZ
        eps = read_internal(f"{c}/0/eps", n)
        porous = eps <= 0.99
        A = {t: read_internal(f"{c}/{t}/alpha.wetting", n) for t in (ts[0], ts[min(1, len(ts) - 1)], ts[-1])}
        P = {t: read_internal(f"{c}/{t}/p", n) for t in ts[1:2] + ts[-1:] if t != "0"}
        dts, reason, crash = log_dt(c)
        data[v] = dict(ts=ts, A=A, P=P, dts=dts, porous=porous, eps=eps)
        a0, a1 = A[ts[0]], A[ts[min(1, len(ts) - 1)]]
        # porous cells that touch a free cell (edge cells of the slab)
        g = grid(porous)
        edge = np.zeros_like(g)
        edge[1:] |= g[1:] & ~g[:-1]
        edge[:-1] |= g[:-1] & ~g[1:]
        edge = edge.ravel()
        liq = lambda a: (eps * a).sum()
        p_last = P[ts[-1]] if ts[-1] in P else np.zeros(n)
        rows.append(dict(
            variant=v, steps=len(dts), t=float(ts[-1]), dt_min=dts.min() if len(dts) else np.nan,
            dt_last=dts[-1] if len(dts) else np.nan, stop=reason,
            edge_wet0=a0[edge].max() if edge.any() else np.nan,
            edge_wet1=a1[edge].max() if edge.any() else np.nan,
            liq_change=(liq(A[ts[-1]]) - liq(a0)) / max(liq(a0), 1e-30) * 100,
            pfree=np.abs(p_last[~porous]).max() if (~porous).any() else 0.0,
            alpha_max=A[ts[-1]].max()))

    # --- alpha maps
    cols = ["t = 0", "after step 1" if mode == "steps" else "first write", "last write"]
    fig, axs = plt.subplots(len(names), 3, figsize=(10, 1.25 * len(names) + 0.8), squeeze=False,
                            constrained_layout=True)
    for i, v in enumerate(names):
        d = data[v]
        ts = d["ts"]
        for j, t in enumerate((ts[0], ts[min(1, len(ts) - 1)], ts[-1])):
            ax = axs[i, j]
            im = ax.imshow(grid(d["A"][t]), origin="lower", extent=ext, cmap=SEQ, vmin=0, vmax=1,
                           aspect="equal", interpolation="nearest")
            for z in slab_edges(d["porous"]):
                ax.axhline(z, color=MUTED, lw=0.8, ls="--")
            ax.set_xticks([0, 0.5, 1.0]); ax.set_yticks([0, 0.3])
            if i == 0:
                ax.set_title(cols[j], fontsize=9, color=INK)
            ax.text(0.99, 0.94, f"t = {float(t):.3g} s", transform=ax.transAxes, ha="right", va="top",
                    fontsize=7, color=MUTED)
            if j == 0:
                ax.set_ylabel(v, rotation=0, ha="right", va="center", fontsize=9)
            if i < len(names) - 1:
                ax.set_xticklabels([])
    axs[-1, 1].set_xlabel("x [mm] (inlet at x = 0, gravity -x); z [mm]; dashed = yarn surface")
    fig.colorbar(im, ax=axs, shrink=0.6, label="alpha.wetting")
    fig.suptitle(f"2D bench variants ({mode}): water saturation", fontsize=11)
    fig.savefig(f"figures/{mode}_alpha.png", dpi=150)
    plt.close(fig)

    # --- p maps (symlog: kPa to MPa), diverging around 0
    fig, axs = plt.subplots(len(names), 2, figsize=(7.5, 1.25 * len(names) + 0.8), squeeze=False,
                            constrained_layout=True)
    pmax = max([np.abs(p).max() for d in data.values() for p in d["P"].values()] + [1e3])
    norm = SymLogNorm(linthresh=1e3, vmin=-pmax, vmax=pmax, base=10)
    for i, v in enumerate(names):
        d = data[v]
        keys = list(d["P"].keys())
        for j in range(2):
            ax = axs[i, j]
            if j < len(keys):
                t = keys[min(j, len(keys) - 1)]
                im = ax.imshow(grid(d["P"][t]), origin="lower", extent=ext, cmap=DIV, norm=norm,
                               aspect="equal", interpolation="nearest")
                ax.text(0.99, 0.94, f"t = {float(t):.3g} s", transform=ax.transAxes, ha="right",
                        va="top", fontsize=7, color=MUTED)
            for z in slab_edges(d["porous"]):
                ax.axhline(z, color=MUTED, lw=0.8, ls="--")
            ax.set_xticks([0, 0.5, 1.0]); ax.set_yticks([0, 0.3])
            if i == 0:
                ax.set_title(["after step 1" if mode == "steps" else "first write", "last write"][j], fontsize=9)
            if j == 0:
                ax.set_ylabel(v, rotation=0, ha="right", va="center", fontsize=9)
            if i < len(names) - 1:
                ax.set_xticklabels([])
    fig.colorbar(im, ax=axs, shrink=0.6, label="p (mixture) [Pa], symlog, linear within ±1 kPa")
    fig.suptitle(f"2D bench variants ({mode}): pressure", fontsize=11)
    fig.savefig(f"figures/{mode}_p.png", dpi=150)
    plt.close(fig)

    # --- dt per step
    fig, ax = plt.subplots(figsize=(7.5, 4), constrained_layout=True)
    for v in names:
        dts = data[v]["dts"]
        if len(dts):
            ax.semilogy(np.arange(1, len(dts) + 1), dts, lw=2, marker="o", ms=4,
                        color=CAT[ORDER.index(v)], label=v)
    ax.axhline(1e-14, color=MUTED, lw=1, ls=":")
    ax.text(1, 1.6e-14, "stop guard (minDeltaTStop)", color=MUTED, fontsize=7)
    ax.set_xlabel("time step"); ax.set_ylabel("deltaT [s]")
    ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, ncol=2, fontsize=8)
    ax.set_title(f"2D bench variants ({mode}): time step", fontsize=11)
    fig.savefig(f"figures/{mode}_dt.png", dpi=150)
    plt.close(fig)

    # --- summary table
    hdr = ("| variant | steps | t reached [s] | min dt [s] | last dt [s] | stop | edge-cell max alpha t=0 → step 1 "
           "| liquid change [%] | max abs(p) free cells, last [Pa] | max alpha, last |\n"
           "|---|---|---|---|---|---|---|---|---|---|\n")
    body = "".join(
        f"| {r['variant']} | {r['steps']} | {r['t']:.3g} | {r['dt_min']:.2g} | {r['dt_last']:.2g} | {r['stop']} "
        f"| {r['edge_wet0']:.3g} → {r['edge_wet1']:.3g} | {r['liq_change']:+.1f} | {r['pfree']:.3g} "
        f"| {r['alpha_max']:.3g} |\n" for r in rows)
    with open(f"figures/{mode}_summary.md", "w") as fh:
        fh.write(hdr + body)
    print(hdr + body)


if __name__ == "__main__":
    main()
