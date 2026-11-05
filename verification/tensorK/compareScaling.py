#!/usr/bin/env python3
"""Check 3, prediction 3: the 1D column with K/f at time f*t against the column with K at time t.

    python3 compareScaling.py <run, K/f> <reference, K> <f>

Both runs are the 172-cell column of ../wicking1D/ABC (cells of 20 um, numbered from the inlet). For every write t of
the reference with a write f*t in the run: front = largest distance where alpha = 0.1 (linear between cell centres),
mean alpha, and the largest cell difference. Pass: front within one cell (20 um) and mean alpha within 0.5 % at every
common write.
"""
import os
import re
import sys

import numpy as np

DX = 20e-6


def alpha(run, tname):
    txt = open(os.path.join(run, tname, "alpha.wetting")).read()
    body = txt.split("internalField", 1)[1]
    n = int(re.search(r"\n(\d+)\n\(", body).group(1))
    vals = body.split("(", 1)[1].split(")", 1)[0].split()
    a = np.array(vals, float)
    assert len(a) == n
    return a


def front(a, level=0.1):
    x = (np.arange(len(a)) + 0.5) * DX
    above = np.where(a >= level)[0]
    if len(above) == 0:
        return 0.0
    i = above[-1]
    if i + 1 >= len(a):
        return x[-1]
    return x[i] + (a[i] - level) / (a[i] - a[i + 1]) * DX


def writes(run):
    out = {}
    for d in os.listdir(run):
        try:
            t = float(d)
        except ValueError:
            continue
        if t > 0 and os.path.isfile(os.path.join(run, d, "alpha.wetting")):
            out[round(t, 9)] = d
    return out


run, ref, f = sys.argv[1], sys.argv[2], float(sys.argv[3])
wr, wf = writes(run), writes(ref)
rows, ok = [], True
for t in sorted(wf):
    ts = round(f * t, 9)
    if ts not in wr:
        continue
    ar, af = alpha(run, wr[ts]), alpha(ref, wf[t])
    dfront = front(ar) - front(af)
    dmean = ar.mean() / af.mean() - 1
    rows.append((t, ts, front(af), front(ar), dfront, af.mean(), ar.mean(), dmean, np.abs(ar - af).max()))
    ok &= abs(dfront) <= DX and abs(dmean) <= 0.005
print(f"== {os.path.basename(run.rstrip('/'))} at {f:g} t vs {os.path.basename(ref.rstrip('/'))} at t: {len(rows)} writes")
print("   t ref [ms]  front ref / run [mm]   diff [um]   mean alpha ref / run   rel diff   max |d alpha|")
for t, ts, fa, fr, dfr, ma, mr, dm, dmax in rows:
    print(f"   {t * 1e3:9.3f}   {fa * 1e3:7.4f} / {fr * 1e3:7.4f}   {dfr * 1e6:+8.3f}   {ma:.5f} / {mr:.5f}   {dm:+.2e}   {dmax:.2e}")
if rows:
    t = np.array([r[0] for r in rows]); fa = np.array([r[2] for r in rows]); fr = np.array([r[3] for r in rows])
    m = t >= 2e-3
    ka = np.polyfit(np.sqrt(t[m]), fa[m], 1)[0]; kr = np.polyfit(np.sqrt(f * t[m]), fr[m], 1)[0]
    print(f"   front fit t >= 2 ms (front = k sqrt(t) + c): ref {ka * 1e3:.3f} mm/sqrt(s), run {kr * 1e3:.3f} mm/sqrt(s), "
          f"ratio {kr / ka:.4f} (sqrt(1/{f:g}) = {f ** -0.5:.4f})")
print(f"   {'PASS' if ok and rows else 'FAIL'} (front within {DX * 1e6:.0f} um, mean alpha within 0.5 %)")
sys.exit(0 if ok and rows else 1)
