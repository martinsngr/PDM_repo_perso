"""pc0 and K series on the 5 x 172 x 3 all-porous bench, solver A only (b0c0f67): table and figure.

    ../../.venv/bin/python benchPcK.py

Reads log.<run> in each run folder (README.md, runs A0, FP*, FK*, SP*, SK*) and the Darcy-limit reference
../bench_ddtCorr/log.v_modified (A + B + C, same bench, dt 1e-7 s, 2e-4 s). Per-step line of the transverseSpread
function object: "transverse: spread <max over rows of max-min alpha across the row> row <j> maxUt <max |Ux|,|Uz|>
meanAlpha <..>". Prints a markdown table and writes bench_pcK_spread.png.

Wicking time t* = t * (K pc0) / (K pc0)_base: in the Darcy limit a run at t is the base run at t* (exact for the K runs, where
gravity scales with K too; approximate for the pc0 runs). Uptake = (mean alpha - initial mean alpha) against the reference at
the same t*. Growth per step: geometric mean of spread(n+1)/spread(n) over the steps with 1e-5 < spread < 1e-2, as
../benchDdtCorr.py. Transverse velocity scale: max |U_t| / (K pc0 / (K pc0)_base), i.e. in units of the base run's velocities.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from benchDdtCorr import parse  # noqa: E402  (same log format)

# name, pc0 divisor, K divisor, dt multiplier
RUNS = [
    ("A0", 1, 1, 1),
    ("FP10", 10, 1, 1), ("FP100", 100, 1, 1), ("FK10", 1, 10, 1), ("FK100", 1, 100, 1),
    ("SP10", 10, 1, 10), ("SP100", 100, 1, 100), ("SK10", 1, 10, 10), ("SK100", 1, 100, 100),
    # follow-up 1: high pc with low K
    ("HP10_K10", 0.1, 10, 1), ("HP100_K10", 0.01, 10, 0.1),
]
LAMBDA0 = 1000 * 1e-11 / (1e-3 * 0.5 * 1e-7)  # rho K / (mu eps dt), water, base run: 200


def initial_mean_alpha(run):
    """Volume mean of the initial alpha (uniform cells): 0/alpha.wetting written by setFields."""
    with open(os.path.join(HERE, run, "0", "alpha.wetting")) as f:
        txt = f.read()
    body = txt.split("internalField")[1]
    n = int(body.split("nonuniform List<scalar>")[1].split("(")[0])
    vals = np.array(body.split("(", 1)[1].split(")")[0].split(), float)
    assert len(vals) == n
    return vals.mean()


def analyse(t, s, ut, ma, crashed, scale, dt):
    win = np.where((s > 1e-5) & (s < 1e-2))[0]
    growth = np.exp(np.mean(np.diff(np.log(s[win])))) if len(win) > 3 else np.nan
    big = np.where(s > 1e-2)[0]
    return dict(
        steps=len(t), end=t[-1], crashed=crashed, seed=s[1], growth=growth,
        rate=np.log(growth) / dt if np.isfinite(growth) else np.nan,
        step_big=(big[0] + 1) if len(big) else None,
        tstar_big=t[big[0]] * scale if len(big) else None,
        smax=s.max(), slate=s[len(s) // 2:].max(), utmax=ut.max() / scale)


def main():
    ref = parse(os.path.join(HERE, "..", "bench_ddtCorr", "log.v_modified"))
    a0 = initial_mean_alpha("A0")
    rows, data = [], {}
    for name, pd, kd, tm in RUNS:
        log = os.path.join(HERE, name, f"log.{name}")
        if not os.path.exists(log):
            continue
        t, s, ut, ma, crashed = parse(log)
        scale = 1.0 / (pd * kd)  # (K pc0) / (K pc0)_base
        dt = 1e-7 * tm
        co = scale * tm
        lam = LAMBDA0 / (kd * tm)
        r = analyse(t, s, ut, ma, crashed, scale, dt)
        tstar = t[-1] * scale
        ma_ref = np.interp(tstar, ref[0], ref[3])
        r["uptake"] = (ma[-1] - a0) / (ma_ref - a0)
        r.update(name=name, co=co, lam=lam, tstar_end=tstar)
        rows.append(r)
        data[name] = (t, s, scale, co, lam)

    print("| Run | Co / Co_base | Λ | steps | end | seed (step 2) | growth / step | rate (1/s) | spread > 1e-2 at step "
          "| (t*) | max spread | max spread, 2nd half | max transverse U (base units) | uptake / Darcy ref at t* |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        g = "—" if np.isnan(r["growth"]) else f"{r['growth']:.3f}"
        rate = "—" if np.isnan(r["rate"]) else f"{r['rate']:.2e}"
        sb = "never" if r["step_big"] is None else str(r["step_big"])
        tb = "—" if r["tstar_big"] is None else f"{r['tstar_big']:.2e} s"
        print(f"| {r['name']} | {r['co']:g} | {r['lam']:g} | {r['steps']} | {'crash' if r['crashed'] else 'End'} "
              f"| {r['seed']:.2e} | {g} | {rate} | {sb} | {tb} | {r['smax']:.3g} | {r['slate']:.3g} "
              f"| {r['utmax']:.3g} | {r['uptake']:.3f} |")
    figure(rows, data, ref)
    return rows, data, ref


# figure: light surface, text inks and categorical slots 1-4 of the dataviz reference palette (adjacent pairlist, lines);
# slots 3-4 are below 3:1 contrast, so every series is also labelled directly
SURFACE, INK, INK2, GRID, REF = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#8d8c87"
HUE = {"P10": "#2a78d6", "P100": "#eb6834", "K10": "#1baf7a", "K100": "#eda100", "HP10_K10": "#e87ba4",
       "HP100_K10": "#008300"}
EARLIER = [("ii_A_c1", "ddtCorr × 1"), ("iii_A_c0", "ddtCorr × 0"), ("iv_A_c0.1", "ddtCorr × 0.1"),
           ("e_A_c0_dthalf", "dt ÷ 2"), ("T2a_GAMGtight", "tight p"), ("T2b_PCGtight", "tight p, PCG")]


def colour(name):
    """colour follows the change (pc0 / 10 has one colour at fixed and at scaled dt)"""
    return INK if name == "A0" else HUE.get(name, HUE.get(name[1:]))


def group(name):
    """tau_I / tau_D = rho K^2 pc0 / (mu^2 eps^2 dy^2), water, dy 20 um: 5 for the base run."""
    pd, kd = next((p, k) for n, p, k, _ in RUNS if n == name)
    return 5.0 / (pd * kd ** 2)


def figure(rows, data, ref):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                         "ytick.color": INK2, "text.color": INK})
    fig, axs = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True, facecolor=SURFACE)
    axes = axs.ravel()
    panels = [("(a) fixed dt 1e-7 s: Co and Λ lowered", ["A0", "FP10", "FP100", "FK10", "FK100"]),
              ("(b) dt × 10 / × 100: Co kept, Λ lowered", ["A0", "SP10", "SP100", "SK10", "SK100"]),
              ("(c) high pc with low K (Co kept)", ["A0", "HP100_K10", "HP10_K10", "SP10"])]
    labels = {"A0": "A0 base", "FP10": "pc0 ÷ 10", "FP100": "pc0 ÷ 100", "FK10": "K ÷ 10", "FK100": "K ÷ 100",
              "SP10": "pc0 ÷ 10, dt × 10", "SP100": "pc0 ÷ 100, dt × 100", "SK10": "K ÷ 10, dt × 10",
              "SK100": "K ÷ 100, dt × 100", "HP10_K10": "pc0 × 10, K ÷ 10",
              "HP100_K10": "pc0 × 100, K ÷ 10, dt ÷ 10"}
    for ax, (title, names) in zip(axes[:3], panels):
        ax.set_facecolor(SURFACE)
        ax.semilogy(np.arange(1, len(ref[1]) + 1), ref[1], color=REF, lw=1.5, ls=":", label="A + B + C (Darcy faces)")
        ends = []
        for n in names:
            if n not in data:
                continue
            s = data[n][1]
            ax.semilogy(np.arange(1, len(s) + 1), s, color=colour(n), lw=1.5, label=labels[n])
            ends.append([np.log10(s[-1]), n, len(s)])
        # direct labels at the line ends, pushed apart to at least 0.4 decade (no overlap)
        ends.sort()
        for i in range(1, len(ends)):
            ends[i][0] = max(ends[i][0], ends[i - 1][0] + 0.4)
        for y, n, x in ends:
            short = labels[n] if n.startswith("HP") else labels[n].split(",")[0]
            ax.annotate(short.replace(", dt ÷ 10", ""), (x, 10 ** y), xytext=(4, 0), textcoords="offset points",
                        va="center", fontsize=8, color=INK2)
        ax.set_xlim(0, 2700)
        ax.set_ylim(1e-11, 1)
        ax.set_xlabel("time step (2,000 per run)")
        ax.set_ylabel("transverse spread of α (max over rows of max − min)")
        ax.set_title(title, loc="left", fontsize=10)
        ax.grid(color=GRID, lw=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(fontsize=8, frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.82))

    ax = axes[3]
    ax.set_facecolor(SURFACE)
    ax.axhspan(1e-11, ref[1].max(), color=GRID, lw=0)
    ax.text(25, ref[1].max() * 0.4, "max spread of A + B + C", fontsize=8, color=INK2, va="top", ha="right")
    ear = []
    for key, lab in EARLIER:
        p = os.path.join(HERE, "..", "bench_ddtCorr", f"log.{key}")
        if os.path.exists(p):
            ear.append(parse(p)[1].max())
    ax.scatter([5.0] * len(ear), ear, s=40, facecolors="none", edgecolors=INK, lw=1.2, zorder=3,
               label="earlier A runs (ddtCorr, dt ÷ 2, tight p)")
    for r in rows:
        n = r["name"]
        ax.scatter(group(n), r["smax"], s=48, color=colour(n),
                   marker="^" if n.startswith("HP") else "s" if n.startswith("S") else "o",
                   edgecolors=SURFACE, lw=1.0, zorder=4)
        if n != "A0":
            ax.annotate(n, (group(n), r["smax"]), xytext=(6, -10 if n == "HP10_K10" else 0),
                        textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.annotate("A0", (5.0, data["A0"][1].max()), xytext=(-18, 0), textcoords="offset points", va="center",
                fontsize=8, color=INK2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-4, 30)
    ax.set_ylim(1e-11, 1)
    ax.set_xlabel("τ_I / τ_D = ρK²pc0 / (μ²ε²Δy²)  (water, Δy 20 µm)")
    ax.set_ylabel("max transverse spread over 2,000 steps")
    ax.set_title("(d) max spread against τ_I / τ_D (● fixed dt, ■ scaled dt, ▲ high pc, low K)", loc="left", fontsize=10)
    ax.grid(color=GRID, lw=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    fig.savefig(os.path.join(HERE, "bench_pcK_spread.png"), dpi=150, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    main()
