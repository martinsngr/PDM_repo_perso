#visualisation of the packing 

import numpy as np 
import matplotlib.pyplot as plt 
from packing import place_fibres, relax_fibres
from pathlib import Path

FIG_DIR = Path(__file__).parent / "figures"   #figures go to poreMorphology/figures, wherever python is launched from
FIG_DIR.mkdir(exist_ok=True)

n=32
radius= 27.5
vf = 0.7
seed = 42 
max_trials = 10000
max_iter = 10000
tol = 0.01
#centers, L, trials = place_fibres(n=n,radius=radius,vf=vf,seed=seed,max_trials=max_trials)
centers, L, trials = relax_fibres(n=n,radius=radius,vf=vf,seed=seed,max_iter=max_iter,tol=tol)


fig, ax =plt.subplots()   #creates a figure and one drawing area 
for fibre in centers:
    for i in range(-1,2): 
        for j in range (-1,2):
            cx =fibre[0]+i*L
            cy =fibre[1]+j*L
            if i == 0 and j == 0:
                circle = plt.Circle((cx, cy), radius, color='blue', alpha=0.5)
            else:
                circle = plt.Circle((cx, cy), radius, color='grey', alpha=0.3)
            ax.add_patch(circle)

ax.set_xlim(-L, 2*L)
ax.set_ylim(-L, 2*L)
ax.set_aspect('equal')
ax.axvline(x=0,linestyle =":", color ='black',linewidth=1)
ax.axvline(x=L,linestyle =":", color ='black',linewidth=1)
ax.axhline(y=0,linestyle =":", color ='black',linewidth=1)
ax.axhline(y=L,linestyle =":", color ='black',linewidth=1)
central_box= plt.Rectangle((0, 0), L, L, fill=False, color='red')
ax.add_patch(central_box)
ax.set_title(f"Representative REV with {n} fiber and vf ={vf}")
fig.savefig(FIG_DIR / 'packing_3x3.png', dpi=150)

print(f"Box size: {L:.2f}")
print(f"Number of fibres: {len(centers)}")
print(f"Number of trials: {trials}")