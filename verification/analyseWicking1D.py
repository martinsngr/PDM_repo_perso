"""1D capillary wicking column vs the similarity solution (2026-10-07).

    ../.venv/bin/python analyseWicking1D.py

Reference (from the inputs only). With the air pressure uniform and gravity neglected, co-current spontaneous
imbibition is the nonlinear diffusion problem
    eps dS/dt = d/dx( D(S) dS/dx ),   D(S) = K kr_w(S)/mu_w |dpc/dS|,   S(0, t) = S_IN,   S(x, 0) = S0,
whose solution depends on eta = x/sqrt(t) only. eta(S) is computed with Philip's iterative integral method:
    F(S) = int_S0^S eta ds,   eta(S) = int_S^S_IN 2 D(s) / (eps F(s)) ds,
iterated to convergence (validated on constant D against the erfc solution, printed first). Front x_f = eta(S_FRONT)
sqrt(t) (S_FRONT 0.1, as wickingFront.ipynb); uptake (water volume per unit area) I = eps F(S_IN) sqrt(t).
Closures as in the solver libraries (both solvers use the same porousModels formulas): Brooks-Corey kr_w = Se^3,
Van Genuchten pc = pc0 (Se^(-1/m) - 1)^(1-m), Se = S/0.999 clipped to [1e-4, 1 - 1e-4]; K 1e-11, eps 0.5, mu_w 1e-3,
pc0 5000, m 0.5, S_IN 0.99, S0 0.002 (1D_vertical_* cases).

Neglected terms (measured in the runs, printed): gravity rho g L ~ 34 Pa; the air pressure drop along the column.
The runs start from a 0.2 mm linear ramp instead of a step, so early times deviate.
"""
import os
import re

import numpy as np
from scipy.special import erfc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(HERE, "wicking1D")
K, EPS, MU_W, PC0, M, SMAX = 1e-11, 0.5, 1e-3, 5000.0, 0.5, 0.999
S_IN, S0, S_FRONT = 0.99, 0.002, 0.1
RHO_W, G = 1000.0, 9.81
L, NY = 3.446e-3, 172
Y = (np.arange(NY) + 0.5) * L / NY
RUNS = [  # folder, saturation field, label
    ("impes", "Sb", "impesFoam"),
    ("port", "alpha.wetting", "hybrid original (be54696)"),
    ("ABC", "alpha.wetting", "hybrid modified (b995db5, darcyFaceMaxDa 0.1)"),
]
# reference palette slots 1-3 (dataviz skill), plus line style and marker
STYLE = {
    "impes": dict(color="#2a78d6", ls="-", marker="o"),
    "port": dict(color="#eb6834", ls="--", marker="s"),
    "ABC": dict(color="#1baf7a", ls=":", marker="^"),
}


def se(S):
    return np.clip(np.asarray(S, float) / SMAX, 1e-4, 1 - 1e-4)


def pc(S):
    return PC0 * (se(S) ** (-1 / M) - 1) ** (1 - M)


def dpcdS(S):
    n = 1 / (1 - M)
    s = se(S)
    return -(1 / (n * M)) * PC0 / SMAX * (s ** (-1 / M) - 1) ** (1 / n - 1) * s ** (-(1 + M) / M)


def D(S):
    return K * se(S) ** 3 / MU_W * np.abs(dpcdS(S))


def cumtrapz(y, x):
    return np.concatenate([[0.0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))])


def philip(Dfun, s_lo, s_hi, eps, n=20001, tol=1e-12, itmax=5000):
    """eta(S) on a grid clustered near s_lo (the front). Returns S, eta."""
    u = np.linspace(0, 1, n)
    S = s_lo + (s_hi - s_lo) * u ** 2  # clustered towards s_lo
    S[0] = s_lo + 1e-12 * (s_hi - s_lo)
    d = Dfun(S)
    eta = np.sqrt(np.trapezoid(d, S) / (s_hi - s_lo) / eps) * (1 - (S - S[0]) / (s_hi - S[0]))  # initial guess
    for it in range(itmax):
        F = cumtrapz(eta, S)
        F[0] = max(F[1], 1e-300) * 0.5  # F ~ (S - s_lo) eta_f at the front
        g = 2 * d / (eps * F)
        new = cumtrapz(g[::-1], -S[::-1])[::-1]  # int_S^s_hi g ds
        if np.max(np.abs(new - eta)) < tol * max(new.max(), 1e-30):
            return S, new, it
        eta = 0.5 * eta + 0.5 * new
    return S, eta, itmax


def validate():
    """Constant D: S = S0 + (S_IN - S0) erfc(eta / (2 sqrt(D/eps)))."""
    Dc = 1e-6
    S, eta, it = philip(lambda s: np.full_like(s, Dc), S0, S_IN, EPS)
    mid = (S > S0 + 0.05) & (S < S_IN - 0.05)
    exact = S0 + (S_IN - S0) * erfc(eta[mid] / (2 * np.sqrt(Dc / EPS)))
    print(f"Validation (constant D = {Dc:g}): {it} iterations, max |S - S_erfc| over S in (0.05, 0.94): "
          f"{np.max(np.abs(S[mid] - exact)):.1e}")


def times(case):
    out = []
    for d in os.listdir(case):
        try:
            out.append((float(d), d))
        except ValueError:
            pass
    return sorted(out)


def read_scalar(path):
    txt = open(path).read()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", txt)
    a = np.array(txt[m.end():txt.index("\n)", m.end())].split(), dtype=float)
    assert len(a) == int(m.group(1)), path
    return a


def front(S, level=S_FRONT):
    i = np.where(S >= level)[0]
    if len(i) == 0:
        return 0.0
    i = i[-1]
    if i + 1 >= len(S):
        return Y[i]
    return Y[i] + (level - S[i]) / (S[i + 1] - S[i]) * (Y[i + 1] - Y[i])


def main():
    validate()
    S_ref, eta_ref, it = philip(D, S0, S_IN, EPS)
    eta_f = float(np.interp(S_FRONT, S_ref, eta_ref))  # S_ref increasing, eta_ref decreasing
    sorpt = EPS * np.trapezoid(eta_ref, S_ref)  # I / sqrt(t), m/sqrt(s) (the run excess is above S0)
    print(f"Similarity solution: {it} iterations; front (S = {S_FRONT}) x_f = {eta_f*1e3:.3f} mm/sqrt(s) * sqrt(t); "
          f"uptake I = {sorpt*1e3:.4f} mm/sqrt(s) * sqrt(t); front reaches the top (L = {L*1e3:.3f} mm) at "
          f"t = {(L/eta_f)**2:.4f} s")

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), constrained_layout=True)
    rows = []
    for key, field, label in RUNS:
        case = os.path.join(CASE, key)
        tl = [t for t in times(case) if t[0] > 0]
        if not tl:
            continue
        S_init = read_scalar(os.path.join(case, "0", field)) if os.path.exists(os.path.join(case, "0", field)) else None
        I0 = EPS * np.sum(S_init - S0) * L / NY
        st = STYLE[key]
        ts, xf, up = [], [], []
        for tv, td in tl:
            S = read_scalar(os.path.join(case, td, field))
            ts.append(tv)
            xf.append(front(S))
            up.append(EPS * np.sum(S - S0) * L / NY - I0)  # uptake since t = 0
            if td in ("0.005", "0.015", "0.025"):
                axes[0].plot(Y / np.sqrt(tv) * 1e3, S, color=st["color"], ls=st["ls"], lw=1.3,
                             label=f"{label}" if td == "0.005" else None)
        ts, xf, up = np.array(ts), np.array(xf), np.array(up)
        axes[1].plot(np.sqrt(ts), xf * 1e3, color=st["color"], ls="none", marker=st["marker"], ms=4, mfc="none",
                     label=label)
        axes[2].plot(np.sqrt(ts), up * 1e3, color=st["color"], ls="none", marker=st["marker"], ms=4, mfc="none",
                     label=label)
        late = ts >= 0.01  # after the start-up ramp, before the front reaches the top
        k_fit, c_fit = np.polyfit(np.sqrt(ts[late]), xf[late], 1)
        s_fit, d_fit = np.polyfit(np.sqrt(ts[late]), up[late], 1)
        for tv in (0.005, 0.01, 0.02, 0.03):
            i = int(np.argmin(np.abs(ts - tv)))
            rows.append((label, ts[i], xf[i] * 1e3, eta_f * np.sqrt(ts[i]) * 1e3, xf[i] / (eta_f * np.sqrt(ts[i])) - 1,
                         up[i] * 1e6, sorpt * np.sqrt(ts[i]) * 1e6, up[i] / (sorpt * np.sqrt(ts[i])) - 1))
        rows.append((label + " — slope of x_f, I vs sqrt(t) for t >= 0.01 s", None, k_fit * 1e3, eta_f * 1e3,
                     k_fit / eta_f - 1, s_fit * 1e6, sorpt * 1e6, s_fit / sorpt - 1))
    axes[0].plot(eta_ref * 1e3, S_ref, color="#222222", lw=1.4, label="similarity solution")
    tq = np.linspace(0, np.sqrt(0.031), 50)
    axes[1].plot(tq, eta_f * tq * 1e3, color="#222222", lw=1.4, label=f"similarity: {eta_f*1e3:.2f} mm/sqrt(s)")
    axes[2].plot(tq, sorpt * tq * 1e3, color="#222222", lw=1.4, label=f"similarity: {sorpt*1e3:.3f} mm/sqrt(s)")
    axes[0].set(xlabel="x / sqrt(t) (mm/sqrt(s))", ylabel="water saturation", xlim=(0, 1.2 * eta_ref.max() * 1e3),
                title="Profiles at 5, 15, 25 ms vs eta = x/sqrt(t)")
    axes[1].set(xlabel="sqrt(t) (sqrt(s))", ylabel=f"front x_f, S = {S_FRONT} (mm)", title="Front position")
    axes[2].set(xlabel="sqrt(t) (sqrt(s))", ylabel="uptake (mm of water per unit area)", title="Water uptake")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, frameon=False)
    fig.suptitle("1D wicking column (K 1e-11, VG pc0 5000 Pa, BC n 3) vs similarity solution")
    fig.savefig(os.path.join(HERE, "wicking1D.png"), dpi=130)

    print("\n| Run | t (s) | x_f run (mm) | x_f exact (mm) | error | uptake run (µm) | uptake exact (µm) | error |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        t = "slope" if r[1] is None else f"{r[1]:g}"
        print(f"| {r[0]} | {t} | {r[2]:.4f} | {r[3]:.4f} | {r[4]:+.2%} | {r[5]:.3f} | {r[6]:.3f} | {r[7]:+.2%} |")

    # neglected terms, from the modified hybrid run: p = p_air - alpha pc(alpha) -> p_air
    case = os.path.join(CASE, "ABC")
    for td in ("0.005", "0.015", "0.025"):
        a = read_scalar(os.path.join(case, td, "alpha.wetting"))
        p = read_scalar(os.path.join(case, td, "p"))
        p_air = p + a * pc(a)
        wet = a > S_FRONT
        print(f"t = {td} s: air pressure range over the column {p_air.max() - p_air.min():.1f} Pa, over the wet zone "
              f"{p_air[wet].max() - p_air[wet].min():.1f} Pa; pc at S = 0.5 {pc(0.5):.0f} Pa, at the front "
              f"(S = {S_FRONT}) {pc(S_FRONT):.0f} Pa; rho g x_f {RHO_W * G * front(a):.1f} Pa")


if __name__ == "__main__":
    main()
