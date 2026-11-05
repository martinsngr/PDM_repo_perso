#!/usr/bin/env python3
"""leakFaces.py  -  where water leaves through the open top/bottom patches (study 2e, 2026-11-05).
    .venv/bin/python -I leakFaces.py <run> [time ...]      (default: 5, 10, 15, 20, 25, 30 ms)
Needs 0/C (compare3068.py writes it). Per write and patch (bottom, top): water out (alphaPhi0.wetting, m3/s) and
total out/in (phi); the water outflow binned by y of the face (owner cell) and by alpha of the owner cell; the share
leaving within 0.1 / 0.3 mm of the bath plane; the faces carrying 90 % of it. Then the padding cells (free cells outside
the fabric box, above y0) with alpha > 0.5 per y band and z layer, and the fabric-box cells of the outermost box
layers next to the padding (free and porous) with alpha > 0.5, to see where the padding water comes from."""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2c_nearSaturation"))
from analyseCut import field, rlist  # noqa: E402


def patches(run):
    txt = open(f"{run}/constant/polyMesh/boundary").read()
    out = {}
    for name, body in re.findall(r"\n\s*(\w+)\s*\n\s*\{([^}]*)\}", txt):
        nf = re.search(r"nFaces\s+(\d+)", body)
        sf = re.search(r"startFace\s+(\d+)", body)
        if nf and sf:
            out[name] = (int(sf.group(1)), int(nf.group(1)))
    return out


def bvalue(path, patch, nfaces):
    """boundary value of a surfaceScalarField / volScalarField on a patch"""
    txt = open(path).read().split("boundaryField", 1)[1]
    m = re.search(r"\n\s*" + patch + r"\s*\n\s*\{", txt)
    body = txt[m.end():]
    v = re.search(r"\bvalue\s+(uniform\s+[^;]+|nonuniform\s+List<scalar>\s*(\d+)\s*\()", body)
    if v.group(1).startswith("uniform"):
        return np.full(nfaces, float(v.group(1).split()[1]))
    n = int(v.group(2))
    return np.array(body[v.end():].split(")", 1)[0].split()[:n], float)


def main():
    run = sys.argv[1]
    times = sys.argv[2:] or ["0.005", "0.01", "0.015", "0.02", "0.025", "0.03"]
    C, _ = rlist(f"{run}/0/C", vec=True)
    n = len(C)
    eps = field(f"{run}/0/eps", n)
    P = eps <= 0.99
    own, _ = rlist(f"{run}/constant/polyMesh/owner")
    own = own.astype(int)
    pt = patches(run)
    v = open(f"{run}/system/blockMeshDict").read().split("vertices", 1)[1].split(");", 1)[0]
    zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)", v)})
    box = (C[:, 2] > zv[1]) & (C[:, 2] < zv[2])
    # bath plane: the inlet is the layer bottom; the layer has no porous cells and spans 5 rows below y0
    ylow = C[:, 1].min()
    y0 = ylow - 10e-6 + 5 * 20e-6
    zc = np.unique(np.round(C[:, 2] * 1e9))                 # z layers by index (uniform or graded padding)
    zlay = np.searchsorted(zc, np.round(C[:, 2] * 1e9))
    nzl = zlay.max() + 1
    print(f"{os.path.basename(run)}: y0 {y0*1e3:.4f} mm, z layers {nzl} (box {zlay[box].min()}-{zlay[box].max()})")
    ybands = [0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.01]
    for t in times:
        print(f"\n== t = {float(t)*1e3:.1f} ms")
        a = field(f"{run}/{t}/alpha.wetting", n)
        for pn in ("bottom", "top"):
            s0, nf = pt[pn]
            o = own[s0:s0 + nf]
            aphi = bvalue(f"{run}/{t}/alphaPhi0.wetting", pn, nf)
            phi = bvalue(f"{run}/{t}/phi", pn, nf)
            wout = np.clip(aphi, 0, None)
            y = (C[o, 1] - y0) * 1e3
            tot = wout.sum()
            print(f"  {pn}: water out {tot:.3e} m3/s (net water {aphi.sum():.3e}), total out {phi[phi>0].sum():.3e} "
                  f"in {phi[phi<0].sum():.3e} m3/s; faces with water out > 0: {(wout > 1e-18).sum()}")
            if tot <= 0:
                continue
            hb = np.histogram(y, bins=ybands, weights=wout)[0] / tot
            print("    by y above y0 [mm]: " + ", ".join(f"{ybands[i]}-{ybands[i+1]}: {hb[i]*100:.1f} %" for i in range(len(hb))))
            ao = a[o]
            ab = [0, 0.05, 0.5, 0.95, 1.01]
            ha = np.histogram(ao, bins=ab, weights=wout)[0] / tot
            print("    by owner alpha: " + ", ".join(f"{ab[i]}-{ab[i+1]}: {ha[i]*100:.1f} %" for i in range(len(ha))))
            k = np.argsort(-wout)
            c90 = np.searchsorted(np.cumsum(wout[k]) / tot, 0.9) + 1
            top = k[:5]
            print(f"    90 % through {c90} faces; largest: " + "; ".join(
                f"x {C[o[i],0]*1e3:.3f} y {y[i]:.3f} a {ao[i]:.2f} {wout[i]:.2e}" for i in top))
        # padding water per y band and z layer (above y0)
        pad = ~box & ~P & (C[:, 1] > y0)
        w = pad & (a > 0.5)
        yy = (C[:, 1] - y0) * 1e3
        print(f"  padding cells alpha > 0.5: {w.sum()} (water {a[pad].sum():.0f} cell volumes); by z layer: "
              + ", ".join(f"{l}: {(w & (zlay == l)).sum()}" for l in sorted(set(zlay[pad]))))
        hb = np.histogram(yy[w], bins=ybands)[0]
        print("    by y above y0 [mm]: " + ", ".join(f"{ybands[i]}-{ybands[i+1]}: {hb[i]}" for i in range(len(hb))))
        for l in (zlay[box].min(), zlay[box].max()):
            m = box & (zlay == l) & (C[:, 1] > y0)
            mf, mp = m & ~P, m & P
            hf = np.histogram(yy[mf & (a > 0.5)], bins=ybands)[0]
            print(f"  outer box layer {l}: free {mf.sum()} cells, {(mf & (a > 0.5)).sum()} water; porous {mp.sum()}, "
                  f"mean S {a[mp].mean() if mp.any() else np.nan:.3f}, {(mp & (a > 0.9)).sum()} at S > 0.9; "
                  f"free water by y: " + ", ".join(f"{ybands[i]}-{ybands[i+1]}: {hf[i]}" for i in range(len(hf))))


if __name__ == "__main__":
    main()
