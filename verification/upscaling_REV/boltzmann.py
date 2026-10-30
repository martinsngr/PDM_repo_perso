#!/usr/bin/env python3
"""boltzmann.py  -  does the REV behave as a 1D diffusive medium? (2026-10-30, README.md)
    ../../.venv/bin/python boltzmann.py [run]     (default: the copy of job 3055/3058, ~/PDM_results/REV_run3055_3058)
Boltzmann collapse of the row-mean yarn saturation (mean over a 0.67 mm window, half a weave period along y) and front and uptake vs sqrt(t)."""
import csv, os, re, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2c_nearSaturation"))
from analyseCut import rlist, field
run = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/PDM_results/REV_run3055_3058")
C,_ = rlist(f"{run}/0/C", vec=True); n = len(C)
eps = field(f"{run}/0/eps", n); P = eps <= 0.99; F = ~P
yid = field(f"{run}/0/yarnID", n)
v = open(f"{run}/system/blockMeshDict").read().split("vertices",1)[1].split(");",1)[0]
zv = sorted({float(t.split()[2]) for t in re.findall(r"\(\s*([-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+)\s*\)",v)})
box = (C[:,2]>zv[1])&(C[:,2]<zv[2])
iy = np.round((C[:,1]-C[:,1].min())/20e-6).astype(int); ny = iy.max()+1
yr = np.array([C[iy==j,1][0] for j in range(ny)])*1e3
nP = np.bincount(iy[P],minlength=ny); nF = np.bincount(iy[F&box],minlength=ny)
print(f"rows {ny}; porous cells {P.sum()}, free box cells {(F&box).sum()}; pore volume yarns {eps[P].sum():.0f} cell vols, free box {(F&box).sum()} cell vols: yarn share {eps[P].sum()/(eps[P].sum()+(F&box).sum()):.3f} of the fabric pore space")
T = ["0.002","0.004","0.006","0.008","0.01","0.012","0.015","0.02"]
levels = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
print("\nBoltzmann test: eta = y/sqrt(t) [mm/sqrt(s)] at which the row-mean yarn S (all yarns, 0.67 mm window) falls below the level")
Y0 = 0.1
def smooth(s, w):
    k = np.ones(w)/w
    return np.convolve(np.pad(s,(w//2,w-1-w//2),mode='edge'),k,mode='valid')
res = {}
print("  t[ms] | " + " ".join(f"S{l:.1f}  " for l in levels))
for t in T:
    a = field(f"{run}/{t}/alpha.wetting",n)
    wat = np.bincount(iy[P],weights=a[P],minlength=ny)
    S = wat/np.maximum(nP,1)
    Ss = smooth(S,33)  # 0.67 mm window: half a weave period along y
    row=[]
    for l in levels:
        k = np.where(Ss<l)[0]
        row.append((yr[k[0]]-Y0)/np.sqrt(float(t)) if len(k) else np.nan)
    res[t]=row
    print(f"  {float(t)*1e3:5.1f} | " + " ".join(f"{v:5.1f} " for v in row))
A = np.array([res[t] for t in T])
print("  spread | " + " ".join(f"{100*np.nanstd(A[:,i])/np.nanmean(A[:,i]):4.0f}% " for i in range(len(levels))) + " (std/mean over 2-20 ms)")
print("  mean   | " + " ".join(f"{np.nanmean(A[:,i]):5.1f} " for i in range(len(levels))))
# front of the y-yarns, uptake
print("\nFront (y-yarns alpha>0.1) and uptake vs sqrt(t):")
rows = list(csv.DictReader(open(f"{run}/waterBudget.csv")))
tb = np.array([float(r["time"]) for r in rows]); wb = np.array([float(r["water_m3"]) for r in rows])
Ainlet = 1.818e-3*0.282e-3   # fabric cross-section normal to y [m2]
tt=[]; ff=[]; ww=[]
for t in ["0.002","0.004","0.006","0.008","0.01","0.012","0.015","0.02","0.025"]:
    a = field(f"{run}/{t}/alpha.wetting",n)
    yy = P&(yid>=0)&(yid<=4)&(a>0.1)
    f = C[yy,1].max()*1e3
    W = np.interp(float(t),tb,wb)
    tt.append(float(t)); ff.append(f); ww.append(W)
    print(f"  t {float(t)*1e3:5.1f} ms: front {f:.3f} mm, water {W/8.05e-15:8.0f} cell vols")
st=np.sqrt(tt); pf=np.polyfit(st[:7],ff[:7],1); pw=np.polyfit(st[:7],np.array(ww[:7])/Ainlet*1e3,1)
print(f"  fit 2-15 ms: front = {pf[0]:.1f} mm/sqrt(s) sqrt(t) + {pf[1]:.2f} mm; uptake per fabric section = {pw[0]:.2f} mm/sqrt(s) sqrt(t) + {pw[1]:.3f} mm")
print(f"  1D yarn column: front 18.04, uptake 6.105 mm/sqrt(s); yarn volume fraction of the box {P.sum()/(P.sum()+(F&box).sum()):.3f}")
print(f"  extrapolated front 10 mm at t = {(10/pf[0])**2:.2f} s, 20 mm at {(20/pf[0])**2:.2f} s (no gravity)")
Vcell, Aplane = 8.05e-15, 1.818e-3*2.667e-3  # m3, fabric plane m2
print(f"  water per fabric area, yarns full: {eps[P].sum()*Vcell/Aplane*1e6:.0f} g/m2; yarns and all free box cells full: {(eps[P].sum()+(F&box).sum())*Vcell/Aplane*1e6:.0f} g/m2")
