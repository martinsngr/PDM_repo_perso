"""Fit of the replica (richards1D.py, their face flux and LSODA) to the simulated fronts read from Maier et al.'s figures.

    ../../.venv/bin/python fitFigures.py

Two factors per case: fD on K (at fixed pc: scales the capillary diffusion and the gravity flux alike, i.e. the time) and
fg on g (gravity against capillarity). (K*fD, pc0) with g*fg is the same family as (K, pc0) moved at fixed K*pc0 plus a time
scale, so the pair covers any other K and pc0. Fronts at S 0.1 and S 0.5 traced in the PDF images by readFronts.py (+-0.3 mm;
README.md). A good fit: RMS <~ 0.5 mm. If no pair fits a figure, the replica's equations differ from what they computed;
if pairs fit, the fitted values say how their run differs from the paper's tables.
    experiments(): the same fit to their measured fronts (EXP), gravity factors above 1 included; with the correct gravity
term fg reads as pc x 1/fg and K x fD*fg (same curves).
"""
import itertools
from multiprocessing import Pool
import numpy as np
import richards1D as r1

# Fronts [mm] at their profile times (r1.TIMES), S 0.1 and S 0.5, from readFronts.py (2026-11-20; replaces readings by eye
# that were off by 0.5-1.3 mm, up to 2.3 mm). Simulated = dotted / dashed component, measured = solid line with markers,
# told apart on the tiles. 'm': both curves in one component (closer than a line width), the same value for both.
# '~': two curves merged in one component, each position read on the tile from the component centre (+-0.3 mm).
FIG = {   # their simulations
    "f128_PEG": ([11.67, 16.20, 27.51, 38.29, 81.99],     # 50 s m
                 [9.92, 14.63, 25.28, 35.5, 74.52]),      # 50, 100, 3000 s m; 600 s mean of two dash pieces
    "f256_PEG": ([10.34, 14.75, 25.28, 35.55, 77.5],      # 100 s mean of two dot pieces, 3000 s of two dash pieces
                 [9.38, 13.58, 23.16, 32.84, 71.22]),     # 50, 100, 300, 600 s m
    "f256_EG": ([10.99, 15.11, 26.20, 37.14, 80.38],      # 10 s m
                [9.70, 13.72, 24.33, 34.31, 73.91]),      # 60, 120, 600 s m
    "f48_PEG": ([11.54, 16.33, 27.66, 38.10, 75.3],       # 100 s ~
                [10.61, 14.94, 25.34, 34.79, 67.32]),     # 50 s ~ (dots right of the measured line), 100 s two dots
}
EXP = {   # their measured fronts (mean of their experiments)
    "f128_PEG": ([11.67, 17.39, 30.79, 42.75, 86.19], [9.92, 14.63, 26.86, 38.55, 74.52]),
    "f256_PEG": ([12.26, 16.57, 27.60, 37.32, 82.07], [9.38, 13.58, 23.16, 32.84, 73.86]),
    "f256_EG": ([10.99, 16.22, 27.52, 39.65, 82.36], [8.36, 13.24, 24.33, 34.31, 73.91]),
    "f48_PEG": ([10.69, 15.46, 26.91, 35.32, 50.27],      # 100 s ~
                [9.60, 14.16, 23.29, 31.74, 46.72]),
}


def fronts(case, fD, fg, scheme="maier"):
    d, phi, mu, rho, a, n, tend = r1.CASES[case]
    r1.CASES["_fit"] = (d * np.sqrt(fD), phi, mu, rho, a, n, tend)   # K ~ d^2
    r1.TIMES["_fit"] = r1.TIMES[case]
    r = r1.run("_fit", scheme=scheme, grav=r1.G * fg)
    f1 = [r1.front(r["z"], S) * 1e3 for S in r["S"]]
    f5 = [r1.front(r["z"], S, 0.5) * 1e3 for S in r["S"]]
    return np.array(f1), np.array(f5)


def rms(case, fD, fg, scheme="maier"):
    f1, f5 = fronts(case, fD, fg, scheme)
    g1, g5 = map(np.array, FIG[case])
    return float(np.sqrt(np.mean(np.concatenate([(f1 - g1) ** 2, (f5 - g5) ** 2]))))


def _job(args):
    case, fD, fg = args
    return (case, fD, fg), rms(case, fD, fg)


def main():
    fDs = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
    fgs = [0.0, 0.25, 0.5, 0.75, 1.0]
    jobs = [(c, fD, fg) for c in FIG for fD, fg in itertools.product(fDs, fgs)]
    with Pool(6) as pool:
        res = dict(pool.map(_job, jobs))
    for case in FIG:
        grid = {(fD, fg): res[(case, fD, fg)] for fD, fg in itertools.product(fDs, fgs)}
        best = min(grid, key=grid.get)
        print(f"{case}: paper's inputs (fD 1, fg 1) RMS {grid[(1.0, 1.0)]:.1f} mm; no gravity (fD 1, fg 0) "
              f"{grid[(1.0, 0.0)]:.1f} mm; best fD {best[0]}, fg {best[1]}: {grid[best]:.1f} mm")
        for fg in fgs:
            row = "  ".join(f"{grid[(fD, fg)]:5.1f}" for fD in fDs)
            print(f"   fg {fg:4.2f} | fD {' '.join(f'{v:5.2f}' for v in fDs) if fg == 0 else ''}\n            {row}" if fg == 0
                  else f"   fg {fg:4.2f} |    {row}")


if __name__ == "__main__":
    main()


def _profile_job(args):
    """Best fD (bounded 1D search on log fD) and RMS at a given gravity factor fg."""
    from scipy.optimize import minimize_scalar
    case, fg = args
    res = minimize_scalar(lambda lf: rms(case, float(np.exp(lf)), fg), bounds=(np.log(0.3), np.log(1.6)),
                          method="bounded", options={"xatol": 0.01})
    return (case, fg), (float(np.exp(res.x)), float(res.fun))


def profile():
    """For each case: the best RMS over fD at fixed fg, i.e. which gravity factors each figure allows."""
    fgs = [0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.5, 0.6, 0.75, 1.0]
    with Pool(8) as pool:
        res = dict(pool.map(_profile_job, [(c, fg) for c in FIG for fg in fgs]))
    print("best RMS [mm] over fD at each gravity factor fg (fD in brackets)")
    print("          " + "".join(f"fg {fg:<9.2f}" for fg in fgs))
    for case in FIG:
        print(f"{case:9s} " + "".join(f"{res[(case, fg)][1]:4.2f} ({res[(case, fg)][0]:.2f})  " for fg in fgs))
        print(f"          paper's inputs (fD 1, fg 1): {rms(case, 1.0, 1.0):.2f} mm")


def _exp_job(args):
    from scipy.optimize import minimize_scalar
    case, fg, first = args
    g1, g5 = map(np.array, EXP[case])

    def err(fD):
        f1, f5 = fronts(case, fD, fg)
        return float(np.sqrt(np.mean(np.concatenate([(f1 - g1)[first:] ** 2, (f5 - g5)[first:] ** 2]))))
    r = minimize_scalar(lambda lf: err(float(np.exp(lf))), bounds=(np.log(0.1), np.log(4.0)), method="bounded",
                        options={"xatol": 0.005})
    return (case, fg, first), (float(np.exp(r.x)), float(r.fun))


def experiments():
    """Their measured fronts (EXP) against the replica with the correct gravity term: best RMS over fD at each fg, all
    profile times and without the first two (their measured early rise is slower than any model: dynamic contact angle,
    their discussion). fg = 1/(pc factor), K factor = fD*fg."""
    fgs = [0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    with Pool(12) as pool:
        res = dict(pool.map(_exp_job, [(c, fg, first) for first in (0, 2) for c in EXP for fg in fgs]))
    for first in (0, 2):
        print("measured fronts, " + ("all profile times" if first == 0 else "without the first two profile times")
              + ": best RMS [mm] over fD at each fg (fD in brackets)")
        print("          " + "".join(f"fg {fg:<10.2f}" for fg in fgs))
        for case in EXP:
            print(f"{case:9s} " + "".join(f"{res[(case, fg, first)][1]:5.2f} ({res[(case, fg, first)][0]:.2f})  "
                                          for fg in fgs))
    print("paper's inputs (fD 1, fg 1), last time, model - measured (S 0.1 / S 0.5, mm):")
    for case in EXP:
        f1, f5 = fronts(case, 1.0, 1.0)
        print(f"  {case}: {f1[-1] - EXP[case][0][-1]:+.1f} / {f5[-1] - EXP[case][1][-1]:+.1f}   (model {f1[-1]:.1f} / "
              f"{f5[-1]:.1f}, measured {EXP[case][0][-1]} / {EXP[case][1][-1]})")


def _candidate(args):
    """RMS against the figure for one possible misreading of the paper's inputs, full gravity, their scheme."""
    case, name = args
    d, phi, mu, rho, a, n, tend = r1.CASES[case]
    mods = {
        "as read": {},
        "Gebart with the diameter (K x4)": {"d": d * 2},
        "c2 = 53 instead of 57": {"d": d * np.sqrt(57 / 53)},
        "porosity from their footnote formula": {"phi": {"f48_PEG": 0.852, "f128_PEG": 0.844, "f256_PEG": 0.836, "f256_EG": 0.836}[case]},
        "f128 porosity 0.856 (their REV study)": {"phi": 0.856} if case == "f128_PEG" else {},
        "f256 diameter 8.05 um (180 dtex/256, porosity 0.853)": {"d": 8.05e-6, "phi": 0.853} if case.startswith("f256") else {},
        "EG density 1113 (literature)": {"rho": 1113.0} if case == "f256_EG" else {},
        "inlet S 1 instead of 0.99": {"bath": True},
        "our face flux instead of theirs": {"scheme": "ours"},
    }[name]
    r1.CASES["_c"] = (mods.get("d", d), mods.get("phi", phi), mu, mods.get("rho", rho), a, n, tend)
    r1.TIMES["_c"] = r1.TIMES[case]
    r = r1.run("_c", scheme=mods.get("scheme", "maier"), bath=mods.get("bath", False))
    f1 = np.array([r1.front(r["z"], S) * 1e3 for S in r["S"]])
    f5 = np.array([r1.front(r["z"], S, 0.5) * 1e3 for S in r["S"]])
    g1, g5 = map(np.array, FIG[case])
    return (case, name), float(np.sqrt(np.mean(np.concatenate([(f1 - g1) ** 2, (f5 - g5) ** 2])))), \
        (f1[-1], g1[-1]), bool(mods) or name == "as read"


def candidates():
    names = ["as read", "Gebart with the diameter (K x4)", "c2 = 53 instead of 57", "porosity from their footnote formula",
             "f128 porosity 0.856 (their REV study)", "f256 diameter 8.05 um (180 dtex/256, porosity 0.853)",
             "EG density 1113 (literature)", "inlet S 1 instead of 0.99", "our face flux instead of theirs"]
    with Pool(9) as pool:
        out = pool.map(_candidate, [(c, nm) for nm in names for c in FIG])
    res = {k: (v, last, applies) for k, v, last, applies in out}
    print("RMS [mm] against their simulated fronts, full gravity ('-': does not apply to that case)")
    print(f"{'variant':55s}" + "".join(f"{c:>10s}" for c in FIG))
    for nm in names:
        print(f"{nm:55s}" + "".join(f"{res[(c, nm)][0]:10.1f}" if res[(c, nm)][2] else f"{'-':>10s}" for c in FIG))


def _literal_fronts(case, fD, variant):
    """Their eq. 6 coded literally: phi dS/dt = d/dz(|D| dS/dz) (mean D on faces) + K*(S) dS/dz (central, cells), LSODA,
    with K* = rho g K/eta * G(S) and G one of: 'dkr' (correct, eq. 8 with the derivative), 'kr' (eq. 8 as printed, no
    derivative), 'dkr_1term' (only the derivative of S^0.5), 'dkr_int' (exponent 1/m instead of 1/m - 1/2), 'none' (g = 0)."""
    from scipy.integrate import solve_ivp
    d, phi, mu, rho, a, n, tend = r1.CASES[case]
    m, pc0 = 1 - 1 / n, 1 / a
    K = 8 * (d / 2) ** 2 / 57 * phi ** 3 / (1 - phi) ** 2 * fD
    pc, dpc, kr = r1.laws(m, n, pc0)

    def G(S):
        s = np.clip(S, 1e-4, 1 - 1e-4)
        X = s ** (1 / m); Y = 1 - X; Ym = Y ** m
        t1 = 0.5 * (1 - Ym) ** 2 / np.sqrt(s)
        t2 = 2 * (1 - Ym) * Y ** (m - 1) * X / np.sqrt(s)
        return {"dkr": t1 + t2, "kr": kr(S), "dkr_1term": t1, "dkr_int": t1 + t2 * np.sqrt(s), "none": 0 * s}[variant]

    dx, L = 5e-4, 0.15
    N = int(round(L / dx)); z = (np.arange(N) + 0.5) * dx
    zc = np.concatenate(([0.0], z, [L])); c = K / mu

    def rhs(t, S):
        Sx = np.concatenate(([0.99], S, [0.01])); h = np.full(N + 1, dx); h[0] = h[-1] = dx / 2
        D = c * kr(Sx) * dpc(Sx); Df = 0.5 * (D[1:] + D[:-1])
        q = -Df * (Sx[1:] - Sx[:-1]) / h
        grav = rho * r1.G * c * G(S) * (Sx[2:] - Sx[:-2]) / (zc[2:] - zc[:-2])
        return (-(q[1:] - q[:-1]) / dx + grav) / phi

    sol = solve_ivp(rhs, (0, tend), np.full(N, 0.01), method="LSODA", t_eval=r1.TIMES[case], rtol=1e-6, atol=1e-8,
                    lband=1, uband=1)
    return np.array([r1.front(z, S) * 1e3 for S in sol.y.T]), np.array([r1.front(z, S, 0.5) * 1e3 for S in sol.y.T])


def _literal_job(args):
    from scipy.optimize import minimize_scalar
    case, variant = args
    g1, g5 = map(np.array, FIG[case])

    def err(fD):
        f1, f5 = _literal_fronts(case, fD, variant)
        return float(np.sqrt(np.mean(np.concatenate([(f1 - g1) ** 2, (f5 - g5) ** 2]))))
    r = minimize_scalar(lambda lf: err(float(np.exp(lf))), bounds=(np.log(0.3), np.log(2.0)), method="bounded",
                        options={"xatol": 0.01})
    return (case, variant), (err(1.0), float(np.exp(r.x)), float(r.fun))


def gravityVariants():
    variants = ["dkr", "kr", "dkr_1term", "dkr_int", "none"]
    with Pool(10) as pool:
        res = dict(pool.map(_literal_job, [(c, v) for v in variants for c in FIG]))
    print("their eq. 6 literally, gravity term K* = rho g K/eta * G(S); RMS [mm] with the paper's inputs | best K factor (RMS)")
    print(f"{'G(S)':12s}" + "".join(f"{c:>26s}" for c in FIG))
    for v in variants:
        print(f"{v:12s}" + "".join(f"{res[(c, v)][0]:8.1f} | x{res[(c, v)][1]:.2f} ({res[(c, v)][2]:.1f})    " for c in FIG))
