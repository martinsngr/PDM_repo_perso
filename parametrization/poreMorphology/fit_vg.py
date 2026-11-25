import numpy as np 
import porespy as ps
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd 
from scipy.optimize import curve_fit


FIG_DIR = Path(__file__).parent / "figures"   #figures go to poreMorphology/figures, wherever python is launched from
FIG_DIR.mkdir(exist_ok=True)

config_name = "f256_px20"
RES_DIR = Path(__file__).parent / "results" / config_name
files = sorted(RES_DIR.glob("rev_*.npz"))    #glob finds every name matching the pattern (* = anything) et sorted puts them in seed order.
inputs = ["radius", "vf", "n", "sigma", "theta_w", "px_per_radius"]


def load_files(files): 
    first = np.load(files[0])
    S_list =[]
    pc_list =[]

    for file in files : 
        d = np.load(file)
        for key in inputs :
            if d[key] != first[key]: 
                raise ValueError(f" File {file.name} as different {key} compared to the first file")
        S_list.append(d["S"])
        pc_list.append(d["pc"])
    return S_list, pc_list, first
    
def plot_clouds(S_list, pc_list,config_name): 
    fig, ax = plt.subplots()
    for S, pc in zip(S_list, pc_list):
        ax.plot(S, pc, color='grey', alpha=0.3, linewidth=0.5)
    ax.set_xlim(0, 1.1)
    ax.set_yscale('log')
    ax.set_xlabel("Water saturation [-]")
    ax.set_ylabel("Capillary pressure pc [Pa]")
    ax.set_title(config_name)
    fig.savefig(FIG_DIR / f"ensemble_{config_name}.png", dpi=150)

def vg_log_pc(S,pc0,n): 
    m = 1 - 1/n 
    pc = pc0*(S**(-1/m)-1)**(1/n)
    return np.log10(pc)

def make_table(S_list, pc_list ):     #one table with all case config points in it, each row a point (S, pc)
    S_list = np.concatenate(S_list)     #joins the n REV arrays into one long array
    pc_list = np.concatenate(pc_list)
    df = pd.DataFrame({"S": S_list, "pc":pc_list}) #Each dictionary key becomes a column name
    df["log_pc"]= np.log10(df["pc"])        # add the log10 colum for the fit 
    print(len(df))
    df = df[(df["S"] > 0) & (df["S"] < 1)]     # keep only the rows with 0 < S < 1
    print(len(df))
    return df 

def balanced_sample(df, n_bins, seed):   #cut the S range into bins of equal width, then draw the same number of points from each bin. Each part of the curve then weighs the same in the fit.

    edges = np.linspace(0, 1, n_bins+1)
    df["bin"] = pd.cut(df["S"], bins=edges)            #looks at each S and writes the interval it falls  
    k = df.groupby("bin", observed=True).size().min()  # counts the points per bin and takes the smallest count
    sample = df.groupby("bin", observed=True).sample(n=k, random_state=seed) 
    return sample, k 

def fit_vg(sample): 
    popt, pcov = curve_fit(vg_log_pc, sample["S"], sample["log_pc"], p0=[2000, 4], bounds=([100, 1.01], [1e5, 20]))
    return popt[0], popt[1]  #(pc0 and n) 



if __name__ == "__main__":

    S_list, pc_list, first = load_files(files)
    #print(len(files))
    #print(sum(len(pc) for pc in pc_list))
    # key in inputs: 
        #print(f"{key}= {first[key]}")

    #plot_clouds(S_list=S_list,pc_list=pc_list, config_name=config_name)

    df = make_table(S_list=S_list, pc_list=pc_list)
    #print(df["S"].describe()) #donne les quartiles, l'immense majorité des points est à des basses saturation --> balanced sampling with pandas

    sample, k = balanced_sample(df=df , n_bins=10, seed=42)
    #print(sample["S"].describe())
    #print(len(sample))
    pc0 , n = fit_vg(sample=sample)
    print(pc0, n)

    plot_fitted_vg(pc0=pc0, n=n)