#calculation of the Pc(S) curve
import numpy as np 
import porespy as ps
import matplotlib.pyplot as plt
from pathlib import Path
from packing import place_fibres, fibre_image

FIG_DIR = Path(__file__).parent / "figures"   #figures go to poreMorphology/figures, wherever python is launched from
FIG_DIR.mkdir(exist_ok=True)

def pc_curve(im, h, sigma, theta_w): 
    padded = np.tile(im,(3,3))
    pc = ps.filters.capillary_transform(im=padded, sigma=sigma,theta=180- theta_w,voxel_size=h*1e-6,spacing=np.inf) #porespy tool to calculate pc For each pore pixel: pc = σcosθ_w / (distance to the nearest fibre). That is the pressure at which a disc centred on that pixel, as large as fits there, is exactly the size limit r. On fibre pixels the distance is 0, so pc is infinite (inf); ignore those. This map is the input of the imbibition (step 2), which turns it into the filling pressure of each pixel.
    pc_pores = pc[padded]                  #discard the inf value of the yarns 
    pc_max = pc_pores.max()
    pc_min = pc_pores.min()
    pressures = np.geomspace(start=pc_max*1.1,stop=pc_min*0.9,num =100)
    res = ps.simulations.imbibition(im=padded, pc=pc, steps=pressures)
    return res                 #return the whole inhibition process 

def rev_curve(centers, L, radius, px_per_radius, sigma, theta_w): 
    h,im = fibre_image(centers,L,radius,px_per_radius)
    res = pc_curve(im,h,sigma,theta_w)  
    N =im.shape[0] 
    central = res.im_pc[N:2*N, N:2*N]
    curve = ps.metrics.pc_map_to_pc_curve(pc=central, im=im, mode='imbibition') 
    S = 1- curve.snwp
    return S ,curve.pc, im , res,                       # res holds the full 3×3 maps (filling pressure, sequence, saturation…)

def plot_results(res,im):
    N =im.shape[0]                                                         #[N:2*N, N:2*N] the map is calculated for the 3x3 doamin but only the central square is plotted
    fig, ax = plt.subplots(1, 3, figsize=[15, 4])

    h = ax[0].imshow(res.im_seq[N:2*N, N:2*N] / im, origin="lower")         #the sequence map, for each pixel, the number of the pressure step (1 to 100) at which it turned to water
    cbar = fig.colorbar(h, aspect=10, format="{x:.0f}")
    cbar.ax.set_title("Invasion Sequence", rotation=90, y=0, c="w")
    ax[0].axis(False)
    ax[0].set_title("(a) Sequence Map")

    h = ax[1].imshow(res.im_snwp[N:2*N, N:2*N] / im, origin="lower")       # the saturation map, for each pixel, the air saturation of the whole image just after that pixel filled
    cbar = fig.colorbar(h, aspect=10, format="{x:.1f}")
    cbar.ax.set_title("Non-Wetting Phase Saturation", rotation=90, y=0, c="w")
    ax[1].axis(False)
    ax[1].set_title("(b) Saturation Map")

    h = ax[2].imshow(np.log10(res.im_pc[N:2*N, N:2*N]) / im, origin="lower")  #the pressure map: the filling pressure of each pixe
    cbar = fig.colorbar(h, aspect=10, format="{x:.1f}")
    cbar.ax.set_title("log(Capillary Pressure)", rotation=90, y=0, c="w")
    ax[2].axis(False)
    ax[2].set_title("(c) Capillary Pressure Map")

    fig.savefig(FIG_DIR / "invasion sequence map , the saturation map, and capillary pressure map.png")

def plot_curve(S,pc): 
    fig, ax = plt.subplots() 
    ax.plot(S, pc, marker='.',linestyle="none")
    ax.set_xlim(0, 1)
    ax.set_yscale('log')
    ax.set_xlabel("Water saturation [-]")
    ax.set_ylabel("Capillary pressure pc [Pa]")
    fig.savefig(FIG_DIR / "pc_curve.png")


if __name__ == "__main__":

    centers,L, trials = place_fibres(n=32, radius=27.5, vf=0.3,seed=42, max_trials=20000)
    S, pc, im, res = rev_curve(centers=centers, L=L, radius=27.5, px_per_radius=20, sigma=0.072, theta_w=70)
    print(len(pc),pc[0],S[0])
    #plot_results(res=res,im=im)
    plot_curve(S,pc)
