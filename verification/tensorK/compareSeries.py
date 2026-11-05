#!/usr/bin/env python3
"""Check 5: steady flux and pressure of the saturated two-layer column against the exact series solution.

    python3 compareSeries.py <run> harmonic|linear

The column of ../wicking1D/ABC: 172 cells along y, Delta x = L/172, L = 3.446 mm, cross-section A = 0.55 x 0.237 mm,
K_y 1e-11 in cells 0-85 and 2.5e-12 in 86-171 (layerK.py), alpha 1 (Se clipped to 0.9999), p 1000 Pa at y = 0 and
0 at y = L, gravity 9.81 m/s2 against the flow. Two references, from the inputs:
  harmonic: the face between two cells carries their two half cells in series (exact for the continuous problem);
  linear:   the jump face carries (K1 + K2)/2 (what the scalar path does between porous cells).
Expected model: tensor run -> harmonic, scalar run -> linear (README.md). Prints the flux (mean, spread along the
column, relative difference to both references), the largest cell-centre pressure difference to both profiles and
the alpha range of the last write. Exit 0 when the run matches its expected model (flux 1e-8, p 1e-5 Pa).
"""
import os
import re
import sys

import numpy as np

run, model = sys.argv[1], sys.argv[2]
N, N1 = 172, 86
L, A, G, DP = 3.446e-3, 0.55e-3 * 0.237e-3, 9.81, 1000.0
DX = L / N
K1, K2 = 1e-11, 2.5e-12
K = np.array([K1] * N1 + [K2] * (N - N1))

tp = open(os.path.join(run, "constant/transportProperties")).read()
def phase(name, key):
    blk = re.search(name + r"\s*\{([^}]*)\}", tp).group(1)
    return float(re.search(key + r"\s+\[[^\]]*\]\s+([-+0-9.eE]+)", blk).group(1))
rw, ra = phase(r"\bwetting", "rho"), phase(r"nonWetting", "rho")
mw, ma = rw * phase(r"\bwetting", "nu"), ra * phase(r"nonWetting", "nu")
n = float(re.search(r"BrooksAndCoreyCoeffs\s*\{[^}]*\bn\s+([-+0-9.eE]+)", tp).group(1))
smax = float(re.search(r"alpha\.wettingmax\s+alpha\.wettingmax\s+\[[^\]]*\]\s+([-+0-9.eE]+)", tp).group(1))
se = min(max(1.0 / smax, 1e-4), 1 - 1e-4)
krw, kra = se ** n, (1 - se) ** n
lam = krw / mw + kra / ma
rho = (rw * krw / mw + ra * kra / ma) / lam

# resistances (sum of Delta x / K over the path), harmonic and linear jump face
half = DX / 2 / K                                   # half cell of each cell
face_h = half[:-1] + half[1:]                       # internal faces, harmonic = two half cells in series
face_l = face_h.copy()
face_l[N1 - 1] = DX / ((K1 + K2) / 2)               # the jump face, linear interpolation
refs = {}
for name, face in (("harmonic", face_h), ("linear", face_l)):
    R = half[0] + face.sum() + half[-1]
    phi = A * lam * (DP - rho * G * L) / R
    rcum = half[0] + np.concatenate(([0.0], np.cumsum(face)))   # inlet boundary -> each cell centre
    y = (np.arange(N) + 0.5) * DX
    p = DP - phi / (A * lam) * rcum - rho * G * y
    refs[name] = (phi, p)

def internal(path, ncomp=1):
    txt = open(path).read().split("internalField", 1)[1]
    m = re.search(r"nonuniform\s+List<\w+>\s*(\d+)\s*\(", txt)
    if not m:
        v = float(re.search(r"uniform\s+([-+0-9.eE]+)", txt).group(1))
        return None, v
    body = txt[m.end():].split("\n)", 1)[0]
    return np.array(body.split(), float), None

t = max((d for d in os.listdir(run) if re.fullmatch(r"[0-9.eE+-]+", d) and float(d) > 0), key=float)
phi_int, _ = internal(os.path.join(run, t, "phi"))
p_cells, _ = internal(os.path.join(run, t, "p"))
a_cells, a_uni = internal(os.path.join(run, t, "alpha.wetting"))
amin, amax = (a_uni, a_uni) if a_cells is None else (a_cells.min(), a_cells.max())

pm = phi_int.mean()
print(f"== {os.path.basename(run.rstrip('/'))} at t = {t} s (expected model: {model})")
print(f"   kr_w {krw:.10f}, kr_a {kra:.3e}, lambda_t {lam:.6f} 1/(Pa s), rho_eff {rho:.9f} kg/m3")
print(f"   flux: mean {pm:.12e} m3/s over {len(phi_int)} internal faces, spread (max-min)/mean "
      f"{(phi_int.max() - phi_int.min()) / pm:.2e}")
ok = True
for name, (phi_ref, p_ref) in refs.items():
    dphi = pm / phi_ref - 1
    dp = np.abs(p_cells - p_ref).max()
    mark = ""
    if name == model:
        good = abs(dphi) <= 1e-8 and dp <= 1e-5 and (phi_int.max() - phi_int.min()) / pm <= 1e-8
        ok &= good
        mark = "  <- expected: " + ("matches" if good else "DOES NOT MATCH")
    print(f"   {name:8s} reference {phi_ref:.12e} m3/s: flux {dphi:+.3e} relative, "
          f"largest cell p difference {dp:.3e} Pa{mark}")
print(f"   exact (harmonic) / linear-face flux = {refs['linear'][0] / refs['harmonic'][0] - 1:+.4%} (linear larger)")
print(f"   alpha in [{amin:.15g}, {amax:.15g}]")
print(f"   {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
