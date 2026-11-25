# check the influence of the pixel size on the pc(S) curve

import numpy as np
import porespy as ps 
import matplotlib.pyplot as plt  
from pathlib import Path
from packing import place_fibres
from pore_morphology import rev_curve 


FIG_DIR = Path(__file__).parent / "figures"   #figures go to poreMorphology/figures, wherever python is launched from
FIG_DIR.mkdir(exist_ok=True) 

pixel_screening = [10,20,40]
radius =5.85 #microm 
vf = 0.16 
n = 25 
seed = 42 
sigma = 0.0412 
theta_w = 36 

centers, L, trials= place_fibres(n=n,radius=radius,vf=vf,seed=seed,max_trials=1000)
fig, ax = plt.subplots()
for px_per_radius in pixel_screening: 
    S, pc, im, _ = rev_curve(centers=centers, L=L, radius=radius, px_per_radius=px_per_radius, sigma=sigma, theta_w=theta_w)
    N = im.shape[0] 
    porosity = ps.metrics.porosity(im)
    print(f"px/R ={px_per_radius}, N={N}, porosity ={porosity:.5f}, number of points = {len(pc)}, pc at S 0.1, 0.5, 0.9 : {np.interp(0.1, S, pc):.0f}, {np.interp(0.5, S, pc):.0f}, {np.interp(0.9, S, pc):.0f}")
    ax.plot(S, pc, marker='.', linestyle='none', label=f"{px_per_radius} px/R") 

ax.set_yscale('log')
ax.set_xlabel("Water saturation [-]")
ax.set_ylabel("Capillary pressure pc [Pa]")
fig.savefig(FIG_DIR / "resolution_check.png")
