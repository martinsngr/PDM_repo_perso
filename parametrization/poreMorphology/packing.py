# functions that generates the REV 
import numpy as np 
import porespy as ps

def place_fibres(n,radius, vf, seed,max_trials): 
    L = np.sqrt(n*np.pi*radius**2/vf) #box size
    rng =np.random.default_rng(seed)
    centers =[]
    trials =0 
    while len(centers)< n:
        trials +=1
        if trials > max_trials: 
            raise RuntimeError(f"Too many trials: {len(centers)} were placed out of {n} fibers")
        else: 
            fibre_loc = rng.uniform(0,L, size=2)
            overlap = False
            for center in centers:
                dx = fibre_loc[0] - center[0]
                dy = fibre_loc[1] - center[1]
                dx -= L * np.round(dx / L)         # distance taken to the nearest copy of the fibre, periodic REV, take the example of a fiber at the edge to visualize it 
                dy -= L * np.round(dy / L)
                distance = np.sqrt(dx**2 + dy**2)
                if distance < 2 * radius:
                    overlap = True
                    break
            if overlap is False:
                centers.append(fibre_loc)

    centers = np.array(centers)
    return(centers,L,trials)

# for high Vf allows the packing by mooving the overlapping fibres
                
def relax_fibres(n, radius, vf, seed, max_iter, tol):
    L = np.sqrt(n*np.pi*radius**2/vf)          # box size, as in place_fibres
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, L, size=(n, 2))   # all fibres at once, overlaps allowed

    for sweep in range(1, max_iter + 1):
        max_overlap = 0.0
        for i in range(n):
            for j in range(i + 1, n):           # each pair once
                dx = centers[i, 0] - centers[j, 0]
                dy = centers[i, 1] - centers[j, 1]
                dx -= L * np.round(dx / L)      # minimum image
                dy -= L * np.round(dy / L)
                distance = np.sqrt(dx**2 + dy**2)
                if distance < 2 * radius:
                    overlap = 2 * radius - distance
                    max_overlap = max(max_overlap, overlap)
                    ux = dx / distance          # unit vector from j to i
                    uy = dy / distance
                    centers[i, 0] += 0.5 * overlap * ux    # i moves half the overlap away from j
                    centers[i, 1] += 0.5 * overlap * uy
                    centers[j, 0] -= 0.5 * overlap * ux    # j moves the other half the opposite way
                    centers[j, 1] -= 0.5 * overlap * uy
                    centers[i] %= L                         # back into the box (periodic)
                    centers[j] %= L
        if max_overlap < tol * radius:          # no overlap left (within tol, relative to R)
            return centers, L, sweep
    raise RuntimeError(f"Not relaxed after {max_iter} sweeps: largest overlap {max_overlap/radius:.2e} R")
    


#create the pixel grid, returns the image and the pixel size h. The image is a 2D boolean array: True = pore, False = fibre( PoreSpy's convention)
def fibre_image(centers,L,radius,px_per_radius): 
    target_size = radius/px_per_radius
    N = int(round(L/target_size))      #number of pixel per side, must be a whole number (i.e im.shape[0])
    h= L/N                             #actual pixel size 
    x = (np.arange(N) + 0.5) * h      #je me place au centre de chaque pixel et j'obtiens ces coordonnées en * par h 
    X, Y = np.meshgrid(x, x)          # X holds the x of every pixel centre, Y the y, Rows go with y, columns go with x

    im = np.ones((N, N), dtype=bool)  #creer un array N x N rempli de 1 (True=pore)

    for center in centers:     #main loop that decide wether a pixel sit inside a fibre or a gap
        dx = X - center[0]
        dy = Y - center[1]
        dx -= L * np.round(dx / L)    # every pixel takes its gap to the nearest copy of the fibre, periodic REV, take the example of a fiber at the edge to visualize it 
        dy -= L * np.round(dy / L)
        inside = dx**2 + dy**2 <= radius**2     #donne un NxN array with true or false suivant si le pixel est dans le fil ou non 
        im[inside] = False                      # ca tag tout les pixels qui sont true dans inside en faux dans im (i.e dans la fibre)

    return  h, im 



if __name__ == "__main__": 
    import matplotlib.pyplot as plt
    from pathlib import Path

    FIG_DIR = Path(__file__).parent / "figures"   #figures go to poreMorphology/figures, wherever python is launched from
    FIG_DIR.mkdir(exist_ok=True)

    centers,L, trials = place_fibres(n=32, radius=27.5, vf=0.3,seed=42, max_trials=20000)
    h, im =fibre_image(centers=centers,L=L,radius=27.5,px_per_radius=20)
    print(f"{h} {im.shape}")
    print(ps.metrics.porosity(im))
    grid=np.tile(im,(3,3))
    fig, ax = plt.subplots() 
    ax.imshow(grid, origin='lower', cmap='gray')
    fig.savefig(FIG_DIR / "pixel_grid.png")

