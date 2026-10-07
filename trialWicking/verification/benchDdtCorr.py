"""ddtCorr test on the 5 x 172 x 3 bench column (task 2026-10-07, step 1).

    ../../.venv/bin/python benchDdtCorr.py [folder with log.<run>(.gz) files, default bench_ddtCorr/]

Bench case (5 x 172 x 3, symmetry sides, fixed dt 1e-7, 2e-4 s) in bench_ddtCorr/case/; the scratch variant
"original + A with ddtCorr x ddtCorrCoeff" is b0c0f67 + bench_ddtCorr/variant_A_ddtCorrCoeff.patch.

Reads the per-step line printed by the transverseSpread function object
("transverse: spread <max over rows of max-min alpha across the row> row <j> maxUt <max |Ux|, |Uz|> meanAlpha <..>")
and the "Time =" lines, prints one table and writes bench_ddtCorr/bench_ddtCorr_spread.png.

The spread does not grow from round-off: it is ~1e-15 after step 1 and jumps to 1e-5..1e-4 at step 2 (reported as
"spread at step 2"), then grows exponentially. Growth factor per step: geometric mean of spread(n+1)/spread(n) over the
steps with 1e-5 < spread < 1e-2 (that exponential phase); rate per second = ln(factor)/dt. Pass: spread <= 1e-6 up to the end time of the
reference run (v).
"""
import gzip
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = [  # folder suffix, label
    ("i_original", "(i) original (be54696)"),
    ("ii_A_c1", "(ii) original + A, ddtCorr x 1"),
    ("iii_A_c0", "(iii) original + A, ddtCorr x 0"),
    ("iv_A_c0.1", "(iv) original + A, ddtCorr x 0.1"),
    ("v_modified", "(v) modified (A+B+C, darcyFaceMaxDa 0.1)"),
    ("e_A_c0_dthalf", "(e) = (iii) with dt 5e-8"),
]
# follow-up tests (same bench, original + A): inertia removed, tight pressure solve
RUNS2 = [
    ("ii_A_c1", "(ii) original + A (reference)"),
    ("v_modified", "(v) modified (reference)"),
    ("T1a_steady", "T1a: ddt(rho,U) steadyState (ddtCorr still Euler)"),
    ("T1b_steady_c0", "T1b: ddt(rho,U) steadyState + ddtCorr x 0"),
    ("T2a_GAMGtight", "T2a: p GAMG tol 1e-12 relTol 0"),
    ("T2b_PCGtight", "T2b: p PCG DIC tol 1e-12 relTol 0"),
]
# reference palette (dataviz skill), fixed order, plus line style
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
STYLES = ["-", "--", "-", ":", "-", "-."]


def lines(log):
    return (gzip.open(log, "rt", errors="replace") if log.endswith(".gz") else open(log, errors="replace")).readlines()


def parse(log):
    t, spread, ut, mean_a = [], [], [], []
    cur = None
    text = lines(log)
    for line in text:
        if line.startswith("Time = "):
            cur = float(line.split()[2])
        elif line.startswith("transverse: spread") and cur is not None:
            f = line.split()
            t.append(cur)
            spread.append(float(f[2]))
            ut.append(float(f[6]))
            mean_a.append(float(f[8]))
    crashed = not any(l.startswith("End") for l in text)
    return np.array(t), np.array(spread), np.array(ut), np.array(mean_a), crashed


def main(folder):
    data = {}
    for key, _ in RUNS + RUNS2:
        for log in (os.path.join(folder, f"log.{key}"), os.path.join(folder, f"log.{key}.gz")):
            if os.path.exists(log):
                data[key] = parse(log)
                break
    t_ref = data["v_modified"][0][-1] if "v_modified" in data else None

    print("| Run | steps | time reached (s) | ended | spread at step 2 | max spread | time spread > 1e-2 "
          "| growth / step | rate (1/s) | max transverse abs(U) (m/s) | mean alpha at end | pass |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    seen = set()
    for key, label in RUNS + RUNS2:
        if key not in data or key in seen:
            continue
        seen.add(key)
        t, s, ut, ma, crashed = data[key]
        win = np.where((s > 1e-5) & (s < 1e-2))[0]
        growth = np.exp(np.mean(np.diff(np.log(s[win])))) if len(win) > 3 else np.nan
        dt = t[1] - t[0]
        big = np.where(s > 1e-2)[0]
        reached_ref = t_ref is not None and t[-1] >= t_ref * (1 - 1e-9)
        ok = (not crashed) and reached_ref and s.max() <= 1e-6
        mean_a = "diverged" if crashed else f"{ma[-1]:.5f}"
        print(f"| {label} | {len(t)} | {t[-1]:.4g} | {'crash' if crashed else 'End'} | {s[1]:.2e} | {s.max():.2e} "
              f"| {f'{t[big[0]]:.2e}' if len(big) else 'never'} | {'—' if np.isnan(growth) else f'{growth:.3f}'} "
              f"| {'—' if np.isnan(growth) else f'{np.log(growth) / dt:.2e}'} | {ut.max():.2e} | {mean_a} "
              f"| {'PASS' if ok else 'FAIL'} |")
    figure(data, RUNS, "bench_ddtCorr_spread.png", "5 x 172 x 3 bench: transverse spread vs time")
    figure(data, RUNS2, "bench_inertia_psolver_spread.png",
           "5 x 172 x 3 bench, original + A: inertia removed / tight pressure solve")


def figure(data, runs, name, title):
    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    for (key, label), col, ls in zip(runs, COLORS, STYLES):
        if key not in data:
            continue
        t, s, ut, ma, crashed = data[key]
        ax.semilogy(t, np.clip(s, 1e-18, 10), color=col, ls=ls, lw=1.5, label=label + (" (crash)" if crashed else ""))
        if crashed:
            ax.plot(t[-1], 10, marker="x", ms=9, color=col)
    ax.axhline(1e-6, color="#222222", lw=1, ls=":", label="pass limit 1e-6")
    ax.set_ylim(1e-16, 10)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("transverse spread of alpha (max over rows, capped at 10)")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, frameon=False)
    fig.savefig(os.path.join(HERE, "bench_ddtCorr", name), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "bench_ddtCorr"))
