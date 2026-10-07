"""Gravity-capillarity equilibrium (Carrillo et al. 2020, section 4.1.3, Brooks-Corey): port vs A+B+C vs the
analytical static profile.

    ../../.venv/bin/python analyseEquilibrium.py

Writes gravityCapillarityEquilibrium_BC.png (last write: profile, Fig. 6C gradient, error vs time),
gravityCapillarityEquilibrium_BC_evolution.png (profiles at several times for each solver, and the water volume
in the lower half and in the bottom 0.2 m against time on a log axis, to tell "slow" from "frozen"),
and prints the error tables.

Setup (tutorial gravity_Capillarity_BrooksCorey): 1 m column, 1500 cells, K 1e-11 m2, porosity 0.5, g = -9.8 y,
water 1000 kg/m3 / air 1 kg/m3; lower half at S 0.5, upper half dry; bottom closed (U 0), top open (p totalPressure 0).
Capillary pressure as in the solver library (pcBrooksAndCorey.H): pc = pc0 Se^-alpha, Se = (S - Sminpc)/(Smaxpc - Sminpc)
clipped to [1e-4, 1 - 1e-4], pc0 1000 Pa, alpha 0.5, Sminpc 0, Smaxpc 0.999.

At rest both phases are hydrostatic, so dpc/dy = (rho_w - rho_n) |g| (paper eq. 55):
  - local check (paper Fig. 6C, eq. 56): |dS/dy| = (rho_w - rho_n) |g| / |dpc/dS|, independent of any reference;
  - full profile: pc(S(y)) = pc_b + (rho_w - rho_n) |g| y, with the bottom value pc_b set so that the profile holds
    the initial water volume (sum S dy = 0.25 m, an input: no water should leave the column). The run's change of
    water volume is reported separately. Nothing is taken from the runs.

The parameters are the tutorial's, which are those of the paper's Fig. 6: its analytical |dS/dy| reaches 19.5 1/m at
S = 1, i.e. (rho_w - rho_n) |g| / (alpha pc0) with pc0 = 1000 Pa (Table 2 lists p0 = 100 Pa, which would give 196).
"""
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(HERE, "eq_BC")
VARIANTS = ["port", "ABC"]
# reference palette slots 1 and 3 (dataviz skill), plus line style / marker so identity is not colour alone
STYLE = {
    "port": dict(color="#2a78d6", ls="-", marker="o", label="port (be54696, = v8)"),
    "ABC": dict(color="#1baf7a", ls="--", marker="^", label="A+B+C (b995db5, darcyFaceMaxDa 0.1)"),
}
PC0, ALPHA, SMINPC, SMAXPC = 1000.0, 0.5, 0.0, 0.999
RHO_W, RHO_N, G = 1000.0, 1.0, 9.8
H, NY = 1.0, 1500
DY = H / NY
Y = (np.arange(NY) + 0.5) * DY
DRG = (RHO_W - RHO_N) * G


def times(case):
    out = []
    for d in os.listdir(case):
        try:
            out.append((float(d), d))
        except ValueError:
            pass
    return sorted(out)


def read_scalar(path):
    """internalField of an ascii OpenFOAM scalar field."""
    txt = open(path).read()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", txt)
    a = np.array(txt[m.end():txt.index("\n)", m.end())].split(), dtype=float)
    assert len(a) == int(m.group(1)), path
    return a


def se(S):
    return np.clip((np.asarray(S, float) - SMINPC) / (SMAXPC - SMINPC), 1e-4, 1 - 1e-4)


def dpcdS(S):
    return -ALPHA * PC0 * se(S)**(-ALPHA - 1) / (SMAXPC - SMINPC)


def S_of_pc(pc):
    """Inverse of pc(S): S = Smaxpc (clipped) where pc <= pc0 (saturated zone)."""
    pc = np.asarray(pc, float)
    Se = np.where(pc > PC0, (np.maximum(pc, PC0) / PC0)**(-1 / ALPHA), 1.0)
    return SMINPC + np.clip(Se, 1e-4, 1 - 1e-4) * (SMAXPC - SMINPC)


def exact_profile(water):
    """Static profile holding the given water volume (sum S dy): bisection on the bottom capillary pressure."""
    lo, hi = -2e4, 2e4
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if np.sum(S_of_pc(mid + DRG * Y)) * DY > water:
            lo = mid
        else:
            hi = mid
    pc_b = 0.5 * (lo + hi)
    return S_of_pc(pc_b + DRG * Y), pc_b


def main():
    fig, (axp, axg, axt) = plt.subplots(1, 3, figsize=(16, 5), constrained_layout=True)
    rows = []
    final = {}
    for v in VARIANTS:
        case = os.path.join(CASE, v)
        tl = times(case)
        if len(tl) < 3:
            continue
        S_init = read_scalar(os.path.join(case, tl[0][1], "alpha.wetting"))
        water0 = np.sum(S_init) * DY
        st = STYLE[v]

        Sa, pc_b = exact_profile(water0)
        # approach to equilibrium: error against the static profile
        ts, errs = [], []
        for tv, td in tl[1:]:
            S = read_scalar(os.path.join(case, td, "alpha.wetting"))
            ts.append(tv)
            errs.append(np.max(np.abs(S - Sa)))
        axt.semilogy(ts, errs, color=st["color"], ls=st["ls"], lw=1.6, label=st["label"])

        S = read_scalar(os.path.join(case, tl[-1][1], "alpha.wetting"))
        S_prev = read_scalar(os.path.join(case, tl[-2][1], "alpha.wetting"))
        water = np.sum(S) * DY
        if v == VARIANTS[0]:
            axp.plot(S_init, Y, color="#999999", lw=1, ls=":", label="initial")
            axp.plot(Sa, Y, color="#222222", lw=1.2, label="analytical")
        axp.plot(S, Y, color=st["color"], ls=st["ls"], lw=1.6, label=st["label"])

        # paper Fig. 6C: |dS/dy| against S (central differences), away from the clipped ends of Se
        dSdy = -np.gradient(S, DY)
        keep = (S > 0.01) & (S < 0.99)
        every = max(1, keep.sum() // 50)
        axg.plot(S[keep][::every], dSdy[keep][::every], ls="none", marker=st["marker"], ms=5, mfc="none",
                 color=st["color"], label=st["label"])
        exact_g = DRG / np.abs(dpcdS(S[keep]))
        rel_g = np.abs(dSdy[keep] - exact_g) / exact_g

        rows.append((v, tl[-1][0], (water - water0) / water0, np.max(np.abs(S - S_prev)),
                     np.max(np.abs(S - Sa)), np.mean(np.abs(S - Sa)), np.median(rel_g), np.percentile(rel_g, 95)))
        final[v] = S

    Sg = np.linspace(0.005, 0.998, 400)
    axg.plot(Sg, DRG / np.abs(dpcdS(Sg)), color="#222222", lw=1.2, label="analytical (eq. 56)")
    axp.set(xlabel="water saturation", ylabel="height y (m)", title="Profile at the last write")
    axg.set(xlabel="water saturation", ylabel="|dS/dy| (1/m)", title="Equilibrium gradient (paper Fig. 6C)")
    axt.set(xlabel="time (s)", ylabel="max |S - static profile|", title="Approach to equilibrium")
    for ax in (axp, axg, axt):
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, frameon=False)
    fig.suptitle("Gravity-capillarity equilibrium, Brooks-Corey (paper section 4.1.3)")
    fig.savefig(os.path.join(HERE, "gravityCapillarityEquilibrium_BC.png"), dpi=130)

    print("| Solver | t (s) | water change | max abs(dS) since previous write | max abs(S - exact) "
          "| mean abs(S - exact) | dS/dy rel. error, median | dS/dy rel. error, 95th pct |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| {} | {:.0f} | {:+.2e} | {:.1e} | {:.4f} | {:.5f} | {:.2%} | {:.2%} |".format(*r))
    if len(final) == 2:
        d = np.abs(final["port"] - final["ABC"])
        print(f"\nport vs A+B+C at the last write: max abs(dS) {d.max():.2e} (y = {Y[d.argmax()]:.3f} m), "
              f"mean {d.mean():.2e}")


# sequential one-hue ramp (light -> dark = early -> late), from the dataviz reference palette
RAMP = ["#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#256abf", "#184f95", "#0d366b"]
SNAP_TIMES = [250, 1000, 2500, 5000, 10000, 20000]  # plus the last write


def nearest(tl, t):
    return min(tl, key=lambda x: abs(x[0] - t))


def evolution():
    water0 = 0.25  # 0.5 m at S 0.5, the initial state of the tutorial
    Sa, _ = exact_profile(water0)
    low, bot = Y < 0.5, Y < 0.2
    vol_low_exact, vol_bot_exact = np.sum(Sa[low]) * DY, np.sum(Sa[bot]) * DY
    fig, axes = plt.subplots(1, 4, figsize=(19, 5), constrained_layout=True,
                             gridspec_kw=dict(width_ratios=[1, 1, 1.2, 1.2]))
    rows = []
    for ax, v in zip(axes[:2], VARIANTS):
        case = os.path.join(CASE, v)
        tl = [t for t in times(case) if t[0] > 0]
        if not tl:
            continue
        picks = [nearest(tl, t) for t in SNAP_TIMES if t < tl[-1][0]] + [tl[-1]]
        ax.plot(read_scalar(os.path.join(case, "0", "alpha.wetting")), Y, color="#999999", lw=1, ls=":",
                label="t = 0")
        for (tv, td), col in zip(picks, RAMP[-len(picks):]):
            ax.plot(read_scalar(os.path.join(case, td, "alpha.wetting")), Y, color=col, lw=1.4, label=f"t = {tv:g} s")
        ax.plot(Sa, Y, color="#222222", lw=1.2, ls="--", label="analytical (static)")
        ax.set(xlabel="water saturation", ylabel="height y (m)", xlim=(0, 1.02), ylim=(0, 1),
               title=STYLE[v]["label"])
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7, frameon=False, loc="upper right")
        # water volumes against time
        ts, vl, vb = [], [], []
        for tv, td in tl:
            S = read_scalar(os.path.join(case, td, "alpha.wetting"))
            ts.append(tv)
            vl.append(np.sum(S[low]) * DY)
            vb.append(np.sum(S[bot]) * DY)
        st = STYLE[v]
        axes[2].semilogx(ts, vl, color=st["color"], ls=st["ls"], lw=1.6, label=st["label"])
        axes[3].semilogx(ts, vb, color=st["color"], ls=st["ls"], lw=1.6, label=st["label"])
        for tv in SNAP_TIMES + [tl[-1][0]]:
            if tv <= tl[-1][0]:
                i = int(np.argmin(np.abs(np.array(ts) - tv)))
                rows.append((v, ts[i], vl[i], vb[i]))
    for ax, ex, name, v0 in ((axes[2], vol_low_exact, "lower half (y < 0.5 m)", 0.25),
                             (axes[3], vol_bot_exact, "bottom 0.2 m", 0.1)):
        ax.axhline(ex, color="#222222", lw=1.2, ls="--", label=f"static profile: {ex:.4f} m")
        ax.axhline(v0, color="#999999", lw=1, ls=":", label=f"initial: {v0:.3f} m")
        ax.set(xlabel="time (s, log)", ylabel="water volume per unit area (m)", title=f"Water in the {name}")
        ax.grid(alpha=0.25, which="both")
        ax.legend(fontsize=8, frameon=False)
    fig.suptitle("Gravity-capillarity equilibrium, Brooks-Corey: evolution (paper section 4.1.3)")
    fig.savefig(os.path.join(HERE, "gravityCapillarityEquilibrium_BC_evolution.png"), dpi=130)
    plt.close(fig)

    print(f"\nWater volume per unit area (sum S dy): static profile {vol_low_exact:.4f} m in y < 0.5, "
          f"{vol_bot_exact:.4f} m in y < 0.2 (initial 0.25 / 0.10)")
    print("| Solver | t (s) | water in y < 0.5 m | water in y < 0.2 m |")
    print("|---|---|---|---|")
    for r in rows:
        print("| {} | {:g} | {:.4f} | {:.4f} |".format(*r))


if __name__ == "__main__":
    main()
    evolution()
