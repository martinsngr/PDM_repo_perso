#!/usr/bin/env python3
"""
refereeCheck.py  -  pass/fail numbers of the yarn/gap interface referee tests (makeVariant.sh R1..R3).

Run from 2D_bench/variants:   ../../../.venv/bin/python refereeCheck.py [tag]
  tag: suffix of the run folders (e.g. "fix" for R1staticWet_run_fix); empty = installed solver.
Prints, per test, the quantities the correct physics fixes:
  R1staticWet       yarn uniform 0.5, air gaps, closed: yarn alpha stays 0.5, gaps stay dry, velocities -> 0
  R2waterGap        dry yarn, water in the top gap, closed: water moves from the gap into the yarn
  R3closedRamp      ramp, inlet closed, gaps: yarn water conserved (none into the gaps) and the yarn alpha(x)
                    profile equals R3closedRampSlab (no gaps), since gaps only supply air
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, "../../tools")
from initFields import read_internal  # noqa: E402

NX, NZ = 50, 15
tag = ("_" + sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else ""


def times(c):
    return sorted((d for d in os.listdir(c) if re.fullmatch(r"[0-9.e+-]+", d)), key=float)


def fields(c, t):
    a = read_internal(f"{c}/{t}/alpha.wetting", NX * NZ).reshape(NZ, NX)
    U = np.linalg.norm(read_internal(f"{c}/{t}/U", NX * NZ, vector=True), axis=1).reshape(NZ, NX)
    return a, U


def status(c):
    log = f"{c}/log.hybridPorousInterFoam"
    txt = open(log).read() if os.path.exists(log) else ""
    m = re.findall(r"^stopGuard: (.*)$", txt, re.M)
    return m[-1] if m else "endTime"


def main():
    for name in ("R1staticWet", "R2waterGap", "R3closedRamp", "R3closedRampSlab"):
        c = f"{name}_run{tag}"
        if not os.path.isdir(c):
            print(f"{c}: missing"); continue
        eps = read_internal(f"{c}/0/eps", NX * NZ).reshape(NZ, NX)
        por = eps <= 0.99
        ts = times(c)
        print(f"\n== {c}  (end {float(ts[-1]):.3g} s, {status(c)})")
        print("   t [s]      yarn water  gap water   yarn mean a  yarn a min/max   gap a max  |U| max yarn/gap [m/s]")
        w0 = None
        for t in ts:
            a, U = fields(c, t)
            yw = (eps * a)[por].sum(); gw = a[~por].sum() if (~por).any() else 0.0
            if w0 is None:
                w0 = yw + gw
            print(f"  {float(t):9.3g}  {yw:10.4f}  {gw:9.4f}   {a[por].mean():11.4f}  {a[por].min():.4f}/{a[por].max():.4f}"
                  f"   {a[~por].max() if (~por).any() else 0:8.4f}  {U[por].max():8.3g} / {U[~por].max() if (~por).any() else 0:8.3g}")
        a, _ = fields(c, ts[-1])
        print(f"   total water change: {((eps*a)[por].sum() + (a[~por].sum() if (~por).any() else 0)) / w0 - 1:+.2%}"
              "  (units: cell volumes of water)")
    # R3: yarn profile vs no-gap reference at every common time
    c1, c2 = f"R3closedRamp_run{tag}", f"R3closedRampSlab_run{tag}"
    if os.path.isdir(c1) and os.path.isdir(c2):
        por1 = read_internal(f"{c1}/0/eps", NX * NZ).reshape(NZ, NX) <= 0.99
        print(f"\n== R3: yarn alpha(x) (mean over yarn rows) vs no-gap reference")
        for t in sorted(set(times(c1)) & set(times(c2)), key=float):
            a1 = fields(c1, t)[0]; a2 = fields(c2, t)[0]
            p1 = np.array([a1[por1[:, x], x].mean() for x in range(NX)]); p2 = a2.mean(axis=0)
            spread = max((a1[por1[:, x], x].max() - a1[por1[:, x], x].min()) for x in range(NX))
            print(f"  t {float(t):9.3g}: max |profile - ref| {np.abs(p1 - p2).max():.4f}, "
                  f"z-spread in yarn {spread:.4f}, x=0,5,10,15: {np.round(p1[[0,5,10,15]],3)} vs {np.round(p2[[0,5,10,15]],3)}")


if __name__ == "__main__":
    main()
