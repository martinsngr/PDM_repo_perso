"""1D wicking column: the base runs and the 2026-10-08 variants against the similarity solution.

    ../.venv/bin/python wicking1DVariants.py

Variants (verification/wicking1D/):
  impes_muA100, ABC_muA100  air viscosity / 100 (1.76e-7 Pa s): the reference assumes a uniform air pressure, so if the
                            gap is that assumption the runs should move to the reference;
  ABC_waterInlet            modified hybrid with UnonWetting fixedValue 0 on the inlet (switches on the boundary
                            relative flux in alphaEqn.H): the inlet should carry water only.
For each run: front and uptake slopes vs sqrt(t) (t >= 0.01 s) against 18.04 / 6.105 mm/sqrt(s), the first-cell
saturation, the air fraction of the inlet-face flux (hybrids) and the air pressure in the first cell (25 ms).
"""
import os

import numpy as np

import analyseWicking1D as W
from wicking1DPressures import patch_value, AREA

RUNS = [  # folder, field, label
    ("impes", "Sb", "impesFoam"),
    ("impes_muA100", "Sb", "impesFoam, mu_air / 100"),
    ("ABC", "alpha.wetting", "hybrid modified"),
    ("ABC_muA100", "alpha.wetting", "hybrid modified, mu_air / 100"),
    ("ABC_waterInlet", "alpha.wetting", "hybrid modified, inlet UnonWetting = 0"),
]


def main():
    S_ref, eta_ref, _ = W.philip(W.D, W.S0, W.S_IN, W.EPS)
    eta_f = float(np.interp(W.S_FRONT, S_ref, eta_ref))
    sorpt = W.EPS * np.trapezoid(eta_ref, S_ref)
    print(f"Reference: front {eta_f*1e3:.3f}, uptake {sorpt*1e3:.4f} mm/sqrt(s)\n")
    print("| Run | front slope (mm/sqrt(s)) | vs ref | uptake slope (mm/sqrt(s)) | vs ref | first-cell S (10-30 ms) "
          "| inlet air / total flux (25 ms) | p_air first cell (25 ms, Pa) |")
    print("|---|---|---|---|---|---|---|---|")
    for key, field, label in RUNS:
        case = os.path.join(W.CASE, key)
        tl = [t for t in W.times(case) if t[0] > 0] if os.path.isdir(case) else []
        if not tl or tl[-1][0] < 0.0299:
            print(f"| {label} | not run / incomplete | | | | | | |")
            continue
        S_init = W.read_scalar(os.path.join(case, "0", field))
        I0 = W.EPS * np.sum(S_init - W.S0) * W.L / W.NY
        ts, xf, up, s1 = [], [], [], []
        for tv, td in tl:
            S = W.read_scalar(os.path.join(case, td, field))
            ts.append(tv)
            xf.append(W.front(S))
            up.append(W.EPS * np.sum(S - W.S0) * W.L / W.NY - I0)
            if tv >= 0.01:
                s1.append(S[0])
        ts, xf, up = map(np.array, (ts, xf, up))
        late = ts >= 0.01
        kf = np.polyfit(np.sqrt(ts[late]), xf[late], 1)[0]
        ku = np.polyfit(np.sqrt(ts[late]), up[late], 1)[0]
        d = os.path.join(case, "0.025")
        S = W.read_scalar(os.path.join(d, field))
        p = W.read_scalar(os.path.join(d, "p"))
        if field == "Sb":
            air = "—"
            pg0 = p[0]
        else:
            phi = -patch_value(os.path.join(d, "phi")) / AREA
            wat = -patch_value(os.path.join(d, "alphaPhi0.wetting")) / AREA
            air = f"{(phi - wat) / phi:+.2%}"
            pg0 = p[0] + S[0] * W.pc(S[0])
        print(f"| {label} | {kf*1e3:.2f} | {kf/eta_f-1:+.1%} | {ku*1e3:.3f} | {ku/sorpt-1:+.1%} | {np.mean(s1):.4f} "
              f"| {air} | {pg0:.0f} |")


if __name__ == "__main__":
    main()
