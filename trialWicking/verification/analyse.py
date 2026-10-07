"""Buckley-Leverett, Brooks-Corey (Carrillo et al. 2020, sections 4.1.1 and 4.1.2): port vs A+B+C vs the
analytical solution.

    ../../.venv/bin/python analyse.py                # both cases
    ../../.venv/bin/python analyse.py BL_flow_BC     # one case

Writes buckleyLeverett_<flow|gravity>_BC.png and prints one error table per case.

Closures as in the solver library (porousModels): Se = (S - Smin)/(Smax - Smin) clipped to [1e-4, 1 - 1e-4],
kr_w = Se^n, kr_n = (1 - Se)^n. Parameters from the tutorials (constant/transportProperties, constant/g, 0/K):
K 1e-11 m2, porosity 0.5, n 3, Smin 0, Smax 0.999, water 1e-3 Pa s / 1000 kg/m3, air 1.76e-5 Pa s / 1 kg/m3,
4 m, 2000 cells, initial S 0.002. Gravity along the column (+x): 9.81 m/s2 (BL_grav_BC), none (BL_flow_BC).

The analytical solution is the self-similar Riemann solution of eps dS/dt + dF_w/dx = 0 with the fractional-flow
water flux F_w(S) = f_w u + lambda_w lambda_n/(lambda_w + lambda_n) (rho_w - rho_n) g: the upper concave envelope of
F_w between the initial and the inlet saturation. Everything follows from the inputs; nothing is taken from the runs.
Both tutorials inject water only, at U_INJ = 1e-5 m/s (0/Uwetting (1e-5 0 0), 0/UnonWetting 0 on leftWall), so the
total Darcy velocity is u = U_INJ:
  - BL_flow_BC: U fixedValue 1e-5 on leftWall (p fixedFluxPressure, see setupCases). No gravity: the inlet state is
    pure water, S_in = Smax; the solution is a rarefaction behind a shock (Welge tangent).
  - BL_grav_BC: U zeroGradient on leftWall (the solver sets the inlet flux from Uwetting/UnonWetting in
    correctUBc.H). The inlet (plateau) saturation S_P solves F_w(S_P) = U_INJ on the rising branch of F_w, then a
    single shock. The paper (eq. 54) drops the f_w u term and gets kr_w(S) = U_INJ mu_w/(K rho_w g), S = 0.467.
  - BL_grav_BC_FFP: the same problem with U fixedValue 1e-5 and p fixedFluxPressure on leftWall (see setupCases).
"""
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = ["port", "ABC"]
# reference palette slots 1 and 3 (dataviz skill), plus line style so identity is not colour alone
STYLE = {
    "port": dict(color="#2a78d6", ls="-", label="port (be54696, = v8)"),
    "ABC": dict(color="#1baf7a", ls="--", label="A+B+C (b995db5, darcyFaceMaxDa 0.1)"),
}
K, EPS, S0, N_KR, SMAX = 1e-11, 0.5, 0.002, 3, 0.999
MU_W, MU_N, RHO_W, RHO_N = 1e-3, 1.76e-5, 1000.0, 1.0
U_INJ = 1e-5  # injected water Darcy velocity, 0/Uwetting on leftWall
AREA = 0.1 * 0.1  # face area of the column (blockMeshDict ly1 x lz1)
L, NX = 4.0, 2000
X = (np.arange(NX) + 0.5) * L / NX
CASES = {
    "BL_flow_BC": dict(g=0.0, title="Flow-driven Buckley-Leverett, Brooks-Corey (paper 4.1.1), inlet p fixedFluxPressure",
                       fig="buckleyLeverett_flow_BC.png", ylim=1.02),
    "BL_grav_BC": dict(g=9.81, title="Gravity-driven Buckley-Leverett, Brooks-Corey (paper 4.1.2)",
                       fig="buckleyLeverett_gravity_BC.png", ylim=0.6),
    "BL_grav_BC_FFP": dict(g=9.81, title="Gravity-driven Buckley-Leverett, Brooks-Corey (paper 4.1.2), "
                           "inlet U fixed + p fixedFluxPressure",
                           fig="buckleyLeverett_gravity_BC_FFP.png", ylim=0.6),
}


def times(case):
    out = []
    for d in os.listdir(case):
        try:
            out.append((float(d), d))
        except ValueError:
            pass
    return sorted(out)


def read_field(path):
    """internalField of an ascii OpenFOAM scalar or vector field."""
    txt = open(path).read()
    m = re.search(r"internalField\s+nonuniform\s+List<(\w+)>\s*(\d+)\s*\(", txt)
    n, start = int(m.group(2)), m.end()
    body = txt[start:txt.index("\n)", start)]
    if m.group(1) == "scalar":
        return np.array(body.split(), dtype=float)
    return np.array(body.replace("(", " ").replace(")", " ").split(), dtype=float).reshape(n, 3)


def kr(S):
    Se = np.clip(np.asarray(S, float) / SMAX, 1e-4, 1 - 1e-4)
    return Se**N_KR, (1 - Se)**N_KR


def water_flux(S, u, g):
    krw, krn = kr(S)
    lw, ln = K * krw / MU_W, K * krn / MU_N
    return lw / (lw + ln) * u + lw * ln / (lw + ln) * (RHO_W - RHO_N) * g


def exact_profile(u, t, S_in, g):
    """Upper concave envelope of F_w on [S0, S_in] -> S(x) at time t, and the front (largest jump)."""
    S = np.linspace(S0, S_in, 4001)
    F = water_flux(S, u, g)
    hull = [0]
    for i in range(1, len(S)):
        while len(hull) >= 2:
            i1, i2 = hull[-2], hull[-1]
            if (F[i2] - F[i1]) * (S[i] - S[i1]) <= (F[i] - F[i1]) * (S[i2] - S[i1]):
                hull.pop()
            else:
                break
        hull.append(i)
    Sh, Fh = S[hull], F[hull]
    speed = np.diff(Fh) / np.diff(Sh) / EPS  # decreasing with S
    x, Sp = [0.0], [S_in]
    for k in range(len(speed) - 1, -1, -1):
        x += [speed[k] * t, speed[k] * t]
        Sp += [Sh[k + 1], Sh[k]]
    x.append(10.0)
    Sp.append(S0)
    jump = np.argmax(np.diff(Sh))
    return np.array(x), np.array(Sp), dict(S=Sh[jump + 1], x=speed[jump] * t)


def front_position(S, level):
    i = np.where(S >= level)[0][-1]
    return X[i] + (level - S[i]) / (S[i + 1] - S[i]) * (X[i + 1] - X[i])


def inlet_saturation(g):
    """Pure water (Smax) without gravity; with gravity S_P, F_w(S_P) = U_INJ on the rising branch (bisection)."""
    if g == 0:
        return SMAX
    S = np.linspace(S0, SMAX, 20001)
    lo, hi = S0, S[np.argmax(water_flux(S, U_INJ, g))]
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if water_flux(mid, U_INJ, g) < U_INJ else (lo, mid)
    return 0.5 * (lo + hi)


def inlet_face_flux(phi_file):
    """|phi| on leftWall per unit area."""
    b = open(phi_file).read()
    b = b[b.index("leftWall"):]
    m = re.search(r"value\s+(uniform\s+(\S+);|nonuniform\s+List<scalar>\s*\d+\s*\(([^)]*)\))", b)
    return abs(float(m.group(2) or m.group(3).split()[0])) / AREA


def analyse_case(name):
    c = CASES[name]
    case, g = os.path.join(HERE, name), c["g"]
    S_in = inlet_saturation(g)
    print(f"\n### {name}: inputs only, u = {U_INJ:g} m/s, inlet saturation {S_in:.4f}"
          + (" (paper eq. 54: 0.467)" if g else " (pure water, Smax)"))
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    rows, final = [], {}
    # write times reached by both runs
    tl = sorted(set(times(os.path.join(case, "port"))) & set(times(os.path.join(case, "ABC"))))
    tl = [t for t in tl if t[0] > 0]
    picks = [tl[int(len(tl) * f) - 1] for f in (1 / 4, 1 / 2, 3 / 4)] + [tl[-1]]
    for j, (tv, td) in enumerate(picks):
        xa, Sa, fr = exact_profile(U_INJ, tv, S_in, g)
        ax.plot(xa, Sa, color="#222222", lw=1.2, label="analytical" if j == 0 else None)
        for v in VARIANTS:
            d = os.path.join(case, v, td)
            S = read_field(os.path.join(d, "alpha.wetting"))
            phi = read_field(os.path.join(d, "phi")) / AREA
            st = STYLE[v]
            ax.plot(X, S, color=st["color"], ls=st["ls"], lw=1.6, label=st["label"] if j == 0 else None)
            xf = front_position(S, 0.5 * (fr["S"] + S0))
            xm = 0.5 * fr["x"]  # halfway between the inlet and the exact front (plateau or rarefaction)
            stored = EPS * np.sum(S - S0) * L / NX
            rows.append((tv, v, inlet_face_flux(os.path.join(d, "phi")), phi.mean(), stored / (tv * U_INJ),
                         np.interp(xm, xa, Sa), np.interp(xm, X, S), fr["x"], xf, (xf - fr["x"]) / fr["x"],
                         np.mean(np.abs(S - np.interp(X, xa, Sa)))))
            final[v] = S
        ax.annotate(f"t = {tv:.0f} s", (fr["x"], min(fr["S"] + 0.03, c["ylim"] - 0.05)), ha="center",
                    fontsize=8, color="#555555")
    ax.set_xlim(0, L)
    ax.set_ylim(0, c["ylim"])
    ax.set_xlabel("x (m)")
    ax.set_ylabel("water saturation")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.set_title(c["title"])
    fig.savefig(os.path.join(HERE, c["fig"]), dpi=130)
    plt.close(fig)

    print("| t (s) | Solver | inlet flux (m/s) | interior flux, mean (m/s) | water stored / injected "
          "| S at x_front/2 exact | num | x front exact (m) | num (m) | front error | mean abs(S - exact) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| {:.0f} | {} | {:.4e} | {:.4e} | {:.5f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:+.2%} | {:.5f} |"
              .format(*r))
    d = np.abs(final["port"] - final["ABC"])  # profiles at the last common write time
    print(f"\nport vs A+B+C at t = {tl[-1][0]:.0f} s: max abs(dS) {d.max():.3e} (cell x = {X[d.argmax()]:.3f} m), "
          f"mean {d.mean():.2e}")


if __name__ == "__main__":
    for name in sys.argv[1:] or list(CASES):
        analyse_case(name)
