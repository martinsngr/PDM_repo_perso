"""1D wicking runs: phase pressures along the column and the air flux on the inlet face (existing output, no runs).

    ../.venv/bin/python wicking1DPressures.py [time, default 0.025]

Phase pressures (Van Genuchten pc as in the libraries, see analyseWicking1D.py):
  - impesFoam: p is the air pressure (phia = phi - phib = -Ma grad p; phib = -Mb grad(p - pc)):
    p_g = p, p_l = p - pc(S).
  - hybridPorousInterFoam: p is the mixture pressure p_g - alpha pc: p_g = p + alpha pc, p_l = p - (1 - alpha) pc.
Inlet-face fluxes: hybrid total phi and water alphaPhi0.wetting (boundary values), air = phi - water;
impesFoam water/air rebuilt as the code does on the face (p fixed 0, Sb fixed 0.99, point pc'(0.99) times snGrad(Sb)).
Writes wicking1D_pressures.png.
"""
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import analyseWicking1D as W

AREA = 0.55e-3 * 0.237e-3  # column cross-section (blockMeshDict)
MU_A = 1.76e-5
# reference palette slots 1-3 (dataviz skill); line style distinguishes the phase
STYLE = {"impes": "#2a78d6", "port": "#eb6834", "ABC": "#1baf7a"}


def patch_value(path, patch="inlet"):
    txt = open(path).read()
    b = txt[txt.index("boundaryField"):]
    b = b[re.search(r"\n\s*" + patch + r"\s*\n", b).end():]
    m = re.search(r"value\s+uniform\s+(\S+);", b[:b.index("}")])
    return float(m.group(1))


def main(td):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    print(f"t = {td} s")
    for key, field, label in W.RUNS:
        d = os.path.join(W.CASE, key, td)
        S = W.read_scalar(os.path.join(d, field))
        p = W.read_scalar(os.path.join(d, "p"))
        pc = W.pc(S)
        if key == "impes":
            pg, pl = p, p - pc
        else:
            pg, pl = p + S * pc, p - (1 - S) * pc
        xf = W.front(S)
        wet = S > W.S_FRONT
        print(f"  {label}: p_g max {pg.max():.0f} Pa at x = {W.Y[pg.argmax()]*1e3:.3f} mm (front {xf*1e3:.2f} mm); "
              f"p_g first cell {pg[0]:.0f} Pa, at the front {np.interp(xf, W.Y, pg):.0f} Pa, dry zone max abs "
              f"{np.abs(pg[~wet]).max():.0f} Pa; p_l first cell {pl[0]:.0f} Pa, at the front {np.interp(xf, W.Y, pl):.0f} Pa")
        col = STYLE[key]
        axes[0].plot(W.Y * 1e3, pg, color=col, lw=1.6, label=label)
        axes[1].plot(W.Y * 1e3, pl / 1e3, color=col, lw=1.6, label=label)
        # inlet-face fluxes, per unit area (m/s), positive = into the column
        if key == "impes":
            Sf = patch_value(os.path.join(d, "Sb"))
            dx2 = W.L / W.NY / 2
            krw, kra = W.se(Sf) ** 3, (1 - W.se(Sf)) ** 3
            pf = 0.0  # p (air) fixedValue 0 on the inlet
            # as the code builds them on the face (pEqn.H, updateSbProperties.H): phiP = -Mf snGrad(p),
            # phia = Faf phiP, phib = Fbf phiP + phiPc with phiPc = Mbf * dpcdS(face) * snGrad(Sb) (point pc')
            Mb, Ma = W.K * krw / W.MU_W, W.K * kra / MU_A
            gp, gS = (p[0] - pf) / dx2, (S[0] - Sf) / dx2  # snGrad along +x, into the column
            q_a = -Ma * gp
            q_w = -Mb * gp + Mb * W.dpcdS(Sf) * gS
            q_w_sec = -Mb * gp + Mb * (W.pc(S[0]) - W.pc(Sf)) / dx2  # same with the secant instead
            print(f"    inlet face (as coded, face S {Sf}, point pc'): water {q_w:.4e} m/s, air {q_a:.3e} m/s "
                  f"({q_a / (q_w + q_a):+.3%} of the total); with the secant pc' the water flux would be {q_w_sec:.3e}")
        else:
            phi = -patch_value(os.path.join(d, "phi")) / AREA
            wat = -patch_value(os.path.join(d, "alphaPhi0.wetting")) / AREA
            print(f"    inlet face: total {phi:.4e} m/s, water {wat:.4e}, air {phi - wat:.3e} "
                  f"({(phi - wat) / phi:+.2%} of the total; alpha_face {patch_value(os.path.join(d, field))})")
    axes[0].axhline(0, color="#999999", lw=0.8)
    axes[0].set(xlabel="x (mm)", ylabel="air pressure p_g (Pa)", title=f"Air pressure, t = {td} s")
    axes[1].set(xlabel="x (mm)", ylabel="water pressure p_l (kPa)", title=f"Water pressure, t = {td} s")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, frameon=False)
    fig.savefig(os.path.join(W.HERE, "wicking1D_pressures.png"), dpi=130)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "0.025")
