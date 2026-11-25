"""OpenFOAM run of a Maier 1D case against the replica (richards1D.py): predictions P1-P3 of README.md.

    ../../.venv/bin/python compare.py [case_dir] [--case f128_PEG] [--k4] [--bath] [--nograv]

Reads alpha.wetting at the replica's profile times (writes every 50 s; the times must be writes), waterBudget.csv and the
solver log (or its .tail); prints front (S 0.1, 0.5), uptake and first-cell S for the run, the replica with the solver's
face flux ("ours") and with theirs ("maier"), and the relative differences.
"""
import argparse
import os
import re
import numpy as np
import richards1D as r1
import fitFigures as ff

# their simulated / measured fronts traced in the PDF figures (fitFigures.FIG / EXP from readFronts.py, +-0.3 mm):
# {case: {"sim" | "exp": {level: [mm per profile time]}}}
FIGURE = {c: {"sim": {0.1: ff.FIG[c][0], 0.5: ff.FIG[c][1]}, "exp": {0.1: ff.EXP[c][0], 0.5: ff.EXP[c][1]}}
          for c in ff.FIG}


def read_alpha(path):
    txt = open(path).read()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", txt)
    if m:
        vals = np.array(txt[m.end():].split(")", 1)[0].split(), float)
        assert len(vals) == int(m.group(1))
        return vals
    return None


def metrics(z, S, dz, phi):
    return (r1.front(z, S) * 1e3, r1.front(z, S, 0.5) * 1e3, phi * np.sum(S - 0.01) * dz * 1e3, S[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", nargs="?", default="f128_PEG")
    ap.add_argument("--case", default="f128_PEG", choices=r1.CASES)
    ap.add_argument("--k4", action="store_true")
    ap.add_argument("--bath", action="store_true")
    ap.add_argument("--nograv", action="store_true")
    a = ap.parse_args()
    g = 0.0 if a.nograv else r1.G
    d, phi = a.case_dir, r1.CASES[a.case][1]
    times = r1.TIMES[a.case]
    ours = r1.run(a.case, k4=a.k4, bath=a.bath, scheme="ours", grav=g)
    theirs = r1.run(a.case, k4=a.k4, bath=a.bath, scheme="maier", grav=g)
    z = ours["z"]
    dz = z[1] - z[0]
    print(f"{d}: front S 0.1 / S 0.5 [mm], uptake [mm], first-cell S; replica 'ours' (P1 reference) and 'maier'")
    worst = 0.0
    for k, t in enumerate(times):
        p = os.path.join(d, f"{t:g}", "alpha.wetting")
        mo = metrics(z, ours["S"][k], dz, phi)
        mm = metrics(z, theirs["S"][k], dz, phi)
        if not os.path.exists(p):
            print(f"  t {t:5g} s: no write (run not there yet)")
            continue
        S = read_alpha(p)
        mr = metrics(z, S, dz, phi)
        rel = [(x / y - 1) * 100 for x, y in zip(mr[:3], mo[:3])]
        worst = max(worst, max(abs(v) for v in rel))
        fig = FIGURE.get(a.case)
        if fig:
            fs = " | figure sim " + " / ".join(f"{fig['sim'][lv][k]:g}" for lv in (0.1, 0.5)) + \
                 ", exp " + " / ".join(f"{fig['exp'][lv][k]:g}" for lv in (0.1, 0.5)) + \
                 " mm; run - sim " + " / ".join(f"{m - fig['sim'][lv][k]:+.1f}" for m, lv in ((mr[0], 0.1), (mr[1], 0.5)))
        else:
            fs = ""
        print(f"  t {t:5g} s: run {mr[0]:6.2f} / {mr[1]:6.2f} / {mr[2]:6.2f} / {mr[3]:.4f} | ours {mo[0]:6.2f} / {mo[1]:6.2f} / "
              f"{mo[2]:6.2f} / {mo[3]:.4f} | maier {mm[0]:6.2f} / {mm[1]:6.2f} / {mm[2]:6.2f} | run vs ours "
              f"{rel[0]:+.2f} / {rel[1]:+.2f} / {rel[2]:+.2f} %{fs}")
    print(f"  largest |run/ours - 1| (fronts, uptake): {worst:.2f} % (P1: <= 2 %)")
    allS = [read_alpha(os.path.join(d, t, "alpha.wetting")) for t in os.listdir(d)
            if re.fullmatch(r"[0-9.e+-]+", t) and t != "0"]
    allS = [s for s in allS if s is not None]
    if allS:
        print(f"  alpha over the writes: min {min(s.min() for s in allS):.3e}, max {max(s.max() for s in allS):.6f}")
    wb = os.path.join(d, "waterBudget.csv")
    if os.path.exists(wb):
        rows = np.atleast_1d(np.genfromtxt(wb, delimiter=",", names=True))
        last = rows[-1]
        print(f"  water budget at {last['time']:g} s: water {last['water_m3']:.4e} m3, inflow {last['in_total']:.4e} m3, "
              f"imbalance {last['imbalance']:.2e} m3 ({abs(last['imbalance']) / last['water_m3']:.1e} of the water)")
    for log in ("log.hybridPorousInterFoam.tail", "log.hybridPorousInterFoam"):
        p = os.path.join(d, log)
        if os.path.exists(p):
            txt = open(p, errors="replace").read()
            steps = re.findall(r"^Time = ", txt, re.M)
            stop = "stopGuard" in txt
            print(f"  {log}: {'stopGuard in the log' if stop else 'no stopGuard'}; last 'Time =' lines in file: {len(steps)}")
            break


if __name__ == "__main__":
    main()
