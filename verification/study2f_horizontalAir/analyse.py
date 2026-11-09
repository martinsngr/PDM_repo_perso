#!/usr/bin/env python3
"""analyse.py <case> [<case> ...]  -  study 2f: air at the yarn surface in the horizontal REV case.
    .venv/bin/python -I analyse.py <case dirs>          (needs <case>/0/C: written here with writeCellCentres if missing)
Mesh: REV_pipeline/cases/horizontal (91 x 133 x 24 cells, z layers 0-4 bath, 5-18 fabric box, 19-23 air; x, y cyclic).
Per write (times in us):
  - yarn -> free air: air flux out of porous cells through porous/free faces, into free cells at alpha > 0.5 (water) and
    at alpha <= 0.5 (air), cell volumes per us
  - bath surface (faces between layers 4 and 5): air going down into the bath through the crest faces (yarn above) and
    through the faces under free cells; water going up through the crest faces; bath air (sum of 1 - alpha below the
    surface); bath cells under crests still water (alpha > 0.5, of 747)
  - second route: of the air going down through the faces under free cells, the share whose free cell above is air-rich
    and connected to the open top through air-rich free cells (it could have escaped upwards) / not connected (trapped)
  - fastest free cell of the write
From the log (dsLocator): the fastest free cell every 50 steps."""
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "REV_pipeline", "tools"))
from analyseCut import field, rlist  # noqa: E402

NX, NY, NZ = 91, 133, 24
V0 = 8.07e-15                       # cell volume [m3] (19.98 x 20.05 x 20.14 um)


def times(case):
    return sorted((x for x in os.listdir(case) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0"
                   and os.path.isfile(os.path.join(case, x, "alpha.wetting"))), key=float)


def connected_to_top(air):
    """air: (NZ, NY, NX) bool of air-rich free cells; returns the cells connected to the top layer through face
    neighbours (periodic in x and y)"""
    reach = np.zeros_like(air)
    reach[NZ - 1] = air[NZ - 1]
    while True:
        grow = reach.copy()
        grow[:-1] |= reach[1:]
        grow[1:] |= reach[:-1]
        grow |= np.roll(reach, 1, axis=1) | np.roll(reach, -1, axis=1)
        grow |= np.roll(reach, 1, axis=2) | np.roll(reach, -1, axis=2)
        grow &= air
        if (grow == reach).all():
            return reach
        reach = grow


def main():
    for case in sys.argv[1:]:
        if not os.path.isfile(f"{case}/0/C"):
            subprocess.run("source /opt/openfoam9/etc/bashrc && postProcess -func writeCellCentres -time 0",
                           shell=True, cwd=case, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        C, _ = rlist(f"{case}/0/C", vec=True)
        n = len(C)
        P = field(f"{case}/0/eps", n) <= 0.99
        own, _ = rlist(f"{case}/constant/polyMesh/owner")
        nei, _ = rlist(f"{case}/constant/polyMesh/neighbour")
        own, nei = own.astype(int), nei.astype(int)
        nf = len(nei)
        o = own[:nf]
        iz = np.arange(n) // (NX * NY)
        pf = np.where(P[o] != P[nei])[0]
        fpor = np.where(P[o[pf]], o[pf], nei[pf])
        ffree = np.where(P[o[pf]], nei[pf], o[pf])
        out_sign = np.where(P[o[pf]], 1.0, -1.0)            # + = from the porous cell into the free cell
        lo, hi = np.minimum(iz[o], iz[nei]), np.maximum(iz[o], iz[nei])
        bp = np.where((lo == 4) & (hi == 5))[0]
        up = np.where(iz[nei[bp]] > iz[o[bp]], 1.0, -1.0)
        above = np.where(up > 0, nei[bp], o[bp])
        below = np.where(up > 0, o[bp], nei[bp])
        crest = P[above]
        print(f"== {os.path.basename(case.rstrip('/'))}: {len(pf)} porous/free faces, bath surface {len(bp)} faces "
              f"({crest.sum()} under crests)")
        print("  t[us] | yarn->free air: into water / into air | air down into bath: crest / free faces | water up crests"
              " | bath air | crest bath cells water | 2nd route: escape possible / trapped | max free |U|")
        for t in times(case):
            a = field(f"{case}/{t}/alpha.wetting", n)
            U = np.linalg.norm(field(f"{case}/{t}/U", n, vec=True), axis=1)
            phi = field(f"{case}/{t}/phi", nf)
            aphi = field(f"{case}/{t}/alphaPhi0.wetting", nf)
            air = phi - aphi
            out = np.clip(air[pf] * out_sign, 0, None)
            wet = a[ffree] > 0.5
            down = -air[bp] * up                              # air going down into the bath
            wup = aphi[bp] * up
            airfree = (~P) & (a <= 0.5) & (iz >= 5)
            reach = connected_to_top(airfree.reshape(NZ, NY, NX)).ravel()
            fd = (~crest) & (down > 0)
            esc = fd & reach[above]
            trap = fd & ~reach[above]
            k = lambda x: x / V0 * 1e-6
            print(f"{float(t)*1e6:7.2f} | {k(out[wet].sum()):8.2f} / {k(out[~wet].sum()):8.2f} | "
                  f"{k(down[crest].sum()):8.2f} / {k(down[~crest].sum()):8.2f} | {k(wup[crest].sum()):8.2f} | "
                  f"{(1 - a[iz < 5]).sum():8.1f} | {(a[below[crest]] > 0.5).sum():4d} | "
                  f"{k(down[esc].sum()):8.2f} / {k(down[trap].sum()):8.2f} | {U[~P].max():.3g}")
        log = os.path.join(case, "log.hybridPorousInterFoam")
        if os.path.exists(log):
            step, rows = 0, []
            for line in open(log, errors="replace"):
                if line.startswith("Time = "):
                    step += 1
                elif " uLoc " in line:
                    w = line.split()
                    w = w[w.index("uLoc") + 1:]
                    if step % 50 == 0:
                        rows.append(f"step {step}: {float(w[2]):.3g} m/s at ({float(w[3])*1e3:.3f} {float(w[4])*1e3:.3f} "
                                    f"{float(w[5])*1e3:.3f}) mm a {float(w[6]):.3f}")
            stop = [l.strip() for l in open(log, errors="replace") if l.startswith("stopGuard")]
            print("  fastest free cell (dsLocator): " + "; ".join(rows[::1]))
            print(f"  steps {step}; {stop[-1] if stop else 'no stopGuard line'}")


if __name__ == "__main__":
    main()
