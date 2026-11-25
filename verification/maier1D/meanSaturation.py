"""Normalised mean saturation S_av(t)/S_av(t_end) (right panels of Maier et al.'s Figs. 16-19) against the replica.

    ../../.venv/bin/python meanSaturation.py <folder with img50/54/55/59.jpeg> [<overlay folder>]

S_av (their eq. 3) is the sum of the local saturations over the sample, i.e. the uptake; divided by its end value only the
shape in time is left. Without gravity the uptake grows as sqrt(t) (the curve is sqrt(t/t_end)); gravity bends it over.
1) Digitises their simulated curve (blue line) and the mean of their experiments (green line) by colour, axes calibrated on
   the tick marks (pixel positions below), and writes meanSaturation_digitised.csv next to this script.
2) Computes the same quantity for the replica variants and prints the RMS against both curves:
   A: their equations with the paper's inputs (correct gravity term);
   typo: their eq. 6 with eq. 8 as printed (k_rel instead of dk_rel/dS), K factor of the front fit (README);
   fg0.35: correct term, gravity x0.35, K factor of the front fit; none: g = 0, K factor of the front fit.
3) With an overlay folder, draws the variants on their panels.
4) Local growth exponents b = d ln S_av / d ln t over three windows (t_end/16 - t_end/4, t_end/4 - t_end/2, t_end/2 -
   0.98 t_end): 0.5 for sqrt(t); gravity lowers b, more in the late window; a slow start (time origin, start-up) raises b
   in the early window. The normalisation cancels in the ratios.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.integrate import solve_ivp
import richards1D as r1

# right panel: image, t at x0 / x1 (px), S_av/S_end = 0 / 1 at y (px), legend box to skip (x > , y >)
PANEL = {
    "f48_PEG": ("img50.jpeg", 705, 975, 3000, 424, 24, (770, 290)),
    "f128_PEG": ("img54.jpeg", 702, 970, 3000, 421.5, 23.5, (770, 290)),
    "f256_PEG": ("img55.jpeg", 702, 970, 3000, 421, 23.5, (770, 290)),
    "f256_EG": ("img59.jpeg", 705, 975.5, 600, 421.5, 23.5, (770, 290)),
}
# K factors from the fits to their simulated fronts (fitFigures.py on the traced readings, README): eq. 8 as printed
# (gravityVariants, 'kr'), gravity x0.35 (profile), no gravity (gravityVariants, 'none')
KF = {"typo": {"f128_PEG": 1.12, "f256_PEG": 0.88, "f256_EG": 0.79, "f48_PEG": 0.63},
      "fg0.35": {"f128_PEG": 1.21, "f256_PEG": 0.92, "f256_EG": 0.83, "f48_PEG": 0.73},
      "none": {"f128_PEG": 1.02, "f256_PEG": 0.84, "f256_EG": 0.75, "f48_PEG": 0.52}}


def digitise(folder, case):
    """Each curve on the pixel columns where its colour shows: (t, value) for their simulation and for the experiment mean
    (the green line is hidden where the thicker blue one is drawn over it)."""
    img, x0, x1, tend, y0, y1, (lx, ly) = PANEL[case]
    im = np.asarray(Image.open(os.path.join(folder, img)).convert("RGB")).astype(int)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    masks = {"sim": (B > 150) & (R < 130) & (G < 150) & (B - R > 70),       # their simulation
             "exp": (G > 170) & (B < 160) & (G - B > 60) & (G - R > 20)}    # mean of their experiments
    out = {}
    ys = np.arange(im.shape[0])
    for name, mk in masks.items():
        t, v = [], []
        for x in range(int(x0) + 2, int(x1) - 1):
            keep = (ys > 6) & (ys < y0 - 2) & ~((x > lx) & (ys > ly))
            s = ys[keep & mk[:, x]]
            if len(s):
                t.append((x - x0) / (x1 - x0) * tend)
                v.append((y0 - np.median(s)) / (y0 - y1))
        out[name] = (np.array(t), np.array(v))
    return out


def uptake_curve(case, variant, times):
    d, phi, mu, rho, a, n, tend = r1.CASES[case]
    m, pc0 = 1 - 1 / n, 1 / a
    fD = 1.0 if variant == "A" else KF[variant][case]
    K = 8 * (d / 2) ** 2 / 57 * phi ** 3 / (1 - phi) ** 2 * fD
    g = {"A": r1.G, "typo": r1.G, "fg0.35": 0.35 * r1.G, "none": 0.0}[variant]
    pc, dpc, kr = r1.laws(m, n, pc0)
    dx, L = 5e-4, 0.15
    N = int(round(L / dx)); z = (np.arange(N) + 0.5) * dx; zc = np.concatenate(([0.0], z, [L])); c = K / mu

    def dkr(S):
        s = np.clip(S, 1e-4, 1 - 1e-4); X = s ** (1 / m); Y = 1 - X; Ym = Y ** m
        return 0.5 * (1 - Ym) ** 2 / np.sqrt(s) + 2 * (1 - Ym) * Y ** (m - 1) * X / np.sqrt(s)

    def rhs(t, S):     # their eq. 6: d/dz(|D| dS/dz) + K* dS/dz, K* = rho g K/eta * (dk_rel/dS, or k_rel for the typo)
        Sx = np.concatenate(([0.99], S, [0.01])); h = np.full(N + 1, dx); h[0] = h[-1] = dx / 2
        D = c * kr(Sx) * dpc(Sx); Df = 0.5 * (D[1:] + D[:-1]); q = -Df * (Sx[1:] - Sx[:-1]) / h
        G = kr(S) if variant == "typo" else dkr(S)
        grav = rho * g * c * G * (Sx[2:] - Sx[:-2]) / (zc[2:] - zc[:-2])
        return (-(q[1:] - q[:-1]) / dx + grav) / phi

    sol = solve_ivp(rhs, (0, tend), np.full(N, 0.01), method="LSODA", t_eval=times, rtol=1e-6, atol=1e-8, lband=1, uband=1)
    U = phi * np.sum(sol.y - 0.01, axis=0) * dx
    return U / U[-1]


def main():
    folder = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    rows = ["case,curve,t_s,S_av_normalised"]
    variants = ["A", "typo", "fg0.35", "none"]
    expo = {}
    print("RMS of S_av/S_av(t_end) against their simulation | their experiment mean (each curve on its own pixel columns)")
    print(f"{'case':10s}" + "".join(f"{v:>18s}" for v in variants) + "   their sim vs exp")
    for case in PANEL:
        dg = digitise(folder, case)
        (ts, sim), (te, exp) = dg["sim"], dg["exp"]
        for name, (tt, vv) in dg.items():
            rows += [f"{case},{name},{a:.1f},{b:.4f}" for a, b in zip(tt, vv)]
        tend = r1.CASES[case][6]
        grid = np.unique(np.concatenate((ts, te)))
        times = np.concatenate((grid[grid < tend], [tend]))
        res = {}
        for v in variants:
            u = uptake_curve(case, v, times)[:-1]
            us, ue = np.interp(ts, times[:-1], u), np.interp(te, times[:-1], u)
            res[v] = (u, np.sqrt(np.mean((us - sim) ** 2)), np.sqrt(np.mean((ue - exp) ** 2)))
        both = (te >= ts.min()) & (te <= ts.max())
        print(f"{case:10s}" + "".join(f"{res[v][1]:8.3f} |{res[v][2]:6.3f}  " for v in variants)
              + f"   {np.sqrt(np.mean((np.interp(te[both], ts, sim) - exp[both]) ** 2)):.3f}")
        t3 = min(0.98 * tend, ts.max(), te.max())      # late window ends where both traces still exist
        tw = np.array([tend / 16, tend / 4, tend / 2, t3])
        curves = {"their exp": np.interp(tw, te, exp), "their sim": np.interp(tw, ts, sim)}
        curves.update({v: np.interp(tw, times[:-1], res[v][0]) for v in variants})
        expo[case] = (t3 / tend, {k: np.log(c[1:] / c[:-1]) / np.log(tw[1:] / tw[:-1]) for k, c in curves.items()})
        if out:
            img, x0, x1, _, y0, y1, _ = PANEL[case]
            im = Image.open(os.path.join(folder, img)).convert("RGB"); W, H = im.size; sc = 3
            im = im.resize((W * sc, H * sc), Image.LANCZOS); dr = ImageDraw.Draw(im)
            px = lambda tt: (x0 + tt / tend * (x1 - x0)) * sc
            py = lambda s: (y0 - s * (y0 - y1)) * sc
            colors = {"A": (0, 0, 0), "typo": (230, 0, 0), "fg0.35": (255, 140, 0), "none": (160, 160, 160)}
            for v in variants:
                tt = times[:-1]
                dr.line([(px(a), py(b)) for a, b in zip(tt, res[v][0])], fill=colors[v], width=3)
            dr.text((px(0.05 * tend), py(0.97)), "black: correct gravity, paper's inputs\nred: eq. 8 as printed\n"
                    "orange: gravity x0.35\ngrey: no gravity", fill=(0, 0, 0))
            im.crop((int(x0 * sc) - 60, 0, int(x1 * sc) + 10, H * sc)).save(os.path.join(out, f"overlay_Sav_{case}.png"))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "meanSaturation_digitised.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")
    print("\nlocal exponent b of S_av over t_end/16-1/4 | 1/4-1/2 | 1/2-t3 (sqrt(t): 0.5)")
    for case in PANEL:
        f3, ex = expo[case]
        print(f"{case} (t3 = {f3:.3f} t_end):")
        for k, b in ex.items():
            print(f"   {k:10s} " + "  ".join(f"{x:5.3f}" for x in b))


if __name__ == "__main__":
    main()
