#generates the REV that will be used for the VG fitting 

import numpy as np
import porespy as ps 
from pathlib import Path
from packing import place_fibres
from pore_morphology import rev_curve 

radius =5.85 #microm 
vf = 0.16 
n = 25         #number of fibres in the REV 
sigma = 0.0412 
theta_w = 36 

px_per_radius = 20      #determined after check resolution, higher number of pixels = longer generation times 
config_name = f"f128_px{px_per_radius}" 

n_rev = 1000      # as much as you want 

RES_DIR = Path(__file__).parent / "results" / config_name    #create a folder for every yarn config 
RES_DIR.mkdir(parents=True, exist_ok=True) 


for seed in range(n_rev): 
    res_file = RES_DIR / f"rev_{seed:04d}.npz"
    if res_file.exists() :
        continue
    else: 
        centers, L, trials= place_fibres(n=n,radius=radius,vf=vf,seed=seed,max_trials=10000)
        S, pc, im, _ = rev_curve(centers=centers, L=L, radius=radius, px_per_radius=px_per_radius, sigma=sigma, theta_w=theta_w)
        N = im.shape[0] 
        porosity = ps.metrics.porosity(im)
        np.savez(res_file,S=S, pc=pc, porosity=porosity,L=L,radius=radius, vf=vf, n=n, sigma=sigma, theta_w=theta_w, px_per_radius= px_per_radius, seed=seed)
        print(f"seed={seed},porosity={porosity:.5f},number of points= {len(pc)}")