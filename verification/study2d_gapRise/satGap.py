#!/usr/bin/env python3
"""satGap.py  -  does the gap water follow the yarn saturation? (study2d_gapRise, 2026-10-30)
    ../../.venv/bin/python satGap.py <run> <pc0> <m> <theta> [time ...]     (default times: every write, thinned to about 12)
S_eq = saturation where the yarn pc equals the gap suction 2 sigma cos(theta)/w (solver VG, Se = S/0.999): next to a drier yarn
the gap water is sucked out. Per write: gap water and its top (free box cells, alpha > 0.5), the heights where the mean S of the
y-yarns (yarnID 0-4, per cell row) falls below S_eq for w 300 and 160 um and below 0.1 (front), mean S of the crossing yarns."""

import os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2c_nearSaturation"))
from analyseCut import rlist, field
def pcfun(S, pc0, m):
    s = np.clip(np.asarray(S, float)/0.999, 1e-4, 1-1e-4); return pc0*(s**(-1/m)-1)**(1-m)
def Seq(p, pc0, m):
    s = np.linspace(0.002, 0.9989, 200001); return s[np.argmin(np.abs(pcfun(s, pc0, m)-p))]
def analyse(run, pc0, m, th, times, show=()):
    if not os.path.isfile(f"{run}/0/C"):
        subprocess.run(["postProcess","-func","writeCellCentres","-time","0"],cwd=run,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
    C,_ = rlist(f"{run}/0/C",vec=True); n=len(C)
    P = field(f"{run}/0/eps",n)<=0.99; yid = field(f"{run}/0/yarnID",n)
    v = open(f"{run}/system/blockMeshDict").read().split("vertices",1)[1].split(");",1)[0]
    zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",v)})
    box = (C[:,2]>zv[1])&(C[:,2]<zv[2]); F=~P
    iy = np.round((C[:,1]-C[:,1].min())/20e-6).astype(int); ny=iy.max()+1; yr = np.array([C[iy==j,1][0] for j in range(ny)])*1e3
    Y = P&(yid>=0)&(yid<=4); X = P&(yid>=5)
    ceq = {w: 2*0.072*np.cos(np.radians(th))/(w*1e-6) for w in (160,300)}
    eq = {w: Seq(p,pc0,m) for w,p in ceq.items()}
    print(f"\n== {os.path.basename(run)}: pc0 {pc0}, m {m}, theta {th}; S_eq = {eq[300]:.3f} (300 um) / {eq[160]:.3f} (160 um)")
    print("  t[ms] | gap water | gap top | yarn S=S_eq(300um) at y | S=S_eq(160um) at y | front(S 0.1) | crossing-yarn mean S by row band")
    for t in times:
        a = field(f"{run}/{t}/alpha.wetting",n)
        SY = np.array([a[Y&(iy==j)].mean() if (Y&(iy==j)).any() else np.nan for j in range(ny)])
        w = F&box&(a>0.5)
        top = C[w,1].max()*1e3 if w.any() else np.nan
        def ycross(s):
            k = np.where(SY<s)[0]; return yr[k[0]] if len(k) else yr[-1]
        bands = [(0.0,0.16,'5'),(0.50,0.84,'6'),(1.16,1.50,'7'),(1.83,2.17,'8')]
        bs = []
        for lo,hi,nm in bands:
            m_ = X&(C[:,1]*1e3>=lo)&(C[:,1]*1e3<hi)
            if m_.any(): bs.append(f"{nm}:{a[m_].mean():.2f}")
        print(f"  {float(t)*1e3:5.2f} | {a[F&box].sum():6.0f} | {top:6.3f} | {ycross(eq[300]):6.3f} | {ycross(eq[160]):6.3f} | {ycross(0.1):6.3f} | {' '.join(bs)}")
    for t in show:
        a = field(f"{run}/{t}/alpha.wetting",n)
        print(f"  rows at t = {float(t)*1e3:.2f} ms (y: y-yarn S, water cells / free box cells; gap rows only where water or every 5th)")
        for j in range(ny):
            mm = F&box&(iy==j); nw=(mm&(a>0.5)).sum()
            if nw>0 or j%5==0:
                s = a[Y&(iy==j)].mean() if (Y&(iy==j)).any() else np.nan
                print(f"    y {yr[j]:.3f}: S {s:.3f}, water {nw:4d}/{mm.sum():4d}")

if __name__ == "__main__":
    run, pc0, m, th = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    times = sys.argv[5:]
    if not times:
        d = sorted((x for x in os.listdir(run) if re.fullmatch(r"[0-9.e+-]+", x) and x != "0"
                    and os.path.isfile(os.path.join(run, x, "alpha.wetting"))), key=float)
        times = d[:: max(1, len(d) // 12)]
    analyse(run, pc0, m, th, times)
