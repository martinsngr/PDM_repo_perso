import os
from stl import mesh
import numpy as np
import glob
import re

d1 = 0.0263
d2 = 0.0282

# Extracting D1 from the folder name
folder_name = os.path.basename(os.getcwd())
match = re.search(r'-([\d.]+)-', folder_name)
if match:
    D1 = float(match.group(1))
    match_d2 = re.search(r'-[\d.]+-([\d.]+)-', folder_name)
    if match_d2:
        D2 = float(match_d2.group(1))
    else:
        raise ValueError("Could not extract D2 from the folder name.")
    
    match_v = re.search(r'-[\d.]+-[\d.]+-([\d.]+)', folder_name)
    if match_v:
        v = float(match_v.group(1))
    else:
        raise ValueError("Could not extract v from the folder name.")
    
    match_rf = re.search(r'(?:-[\d.]+){3}-([\d.]+)', folder_name)
    if match_rf:
        r_f = float(match_rf.group(1))
    else:
        raise ValueError("Could not extract r_f from the folder name.")
else:
    raise ValueError("Could not extract D1 from the folder name.")

# looking for the stl file (no matter that how it is called, in triSurfae it should find just a solid)
stl_files = glob.glob('constant/triSurface/*.stl')

if not stl_files:
    raise FileNotFoundError("No file found in constant/triSurface/")

filename = stl_files[0]
print(f"Looking the file: {filename}")

# spacing between threads
s1=1/D1
s2=1/D2
t1 = r_f * d1
t2 = r_f * d2
w1 = d1 + v * (d1 - t1)
w2 = d2 + v * (d2 - t2)

# formatting the results
w1_str = f"{w1:.4f}"
w2_str = f"{w2:.4f}"
t1_str = f"{t1:.4f}"
t2_str = f"{t2:.4f}"

your_mesh = mesh.Mesh.from_file(filename)

# now it is reading the bounding box given by paraview
min_coords = np.min(your_mesh.vectors.reshape(-1, 3), axis=0)
max_coords = np.max(your_mesh.vectors.reshape(-1, 3), axis=0)

# calculate delta (size of the bounding box in each axis)
delta = max_coords - min_coords
deltaZ = delta[2]

# calculate center of the bounding box
center = deltaZ / 2

# z boundaries
zmin = min_coords[2] - center
zmax = max_coords[2] + center

# formatting the results
zmin_str = f"{zmin:.4f}"
zmax_str = f"{zmax:.4f}"

# checking the x an y bonds now
xmin = 0
xmax = max_coords[0] - s1

xmin_str = f"{xmin:.4f}"
xmax_str = f"{xmax:.4f}"

ymin = 0
ymax = max_coords[1] - s2

ymin_str = f"{ymin:.4f}"
ymax_str = f"{ymax:.4f}"

xloc = xmax/2
yloc = ymax/2

# to be close to the outlet (where there is no solid for sure) but not quite
print("deltaZ: ", deltaZ)
print(f"zmin: {zmin} zmax: {zmax}")
zloc = zmin + deltaZ*0.05 
print(f"zloc: {zloc}")

xloc_str = f"{xloc:.4f}"
yloc_str = f"{yloc:.4f}"
zloc_str = f"{zloc:.4f}"


# the results are saved in a .txt file (maybe it could be avoid but for the moment let's keep it)
output_file = 'boundingBoxDims.txt'
with open(output_file, 'w') as f:
    f.write(f"File: {os.path.basename(filename)}\n\n")
    f.write(f"center: {center}\n\n")
    f.write(f"xmin: {min_coords[0]}\nxmax: {max_coords[0]}\ndeltaX: {delta[0]}\n\n")
    f.write(f"ymin: {min_coords[1]}\nymax: {max_coords[1]}\ndeltaY: {delta[1]}\n\n")
    f.write(f"zmin: {min_coords[2]}\nzmax: {max_coords[2]}\ndeltaZ: {delta[2]}\n")

print(f"Bounding box in: {output_file}")

# this is where openFOAM read the coordinates
case_setup_file = './caseSetup'

with open(case_setup_file, 'r') as f:
    content = f.read()
    geometry_file = os.path.basename(filename)
    fabric_name = os.path.splitext(geometry_file)[0]
    content = re.sub(r'geometryFile\s+.*?;', f'geometryFile\t {geometry_file};', content)
    content = re.sub(r'fabricName\s+.*?;', f'fabricName\t {fabric_name};', content)
    content = re.sub(r'xmin\s*=?\s*[-+e0-9.]+;', f'xmin\t {xmin_str};', content)
    content = re.sub(r'xmax\s*=?\s*[-+e0-9.]+;', f'xmax\t {xmax_str};', content)
    content = re.sub(r'ymin\s*=?\s*[-+e0-9.]+;', f'ymin\t {ymin_str};', content)
    content = re.sub(r'ymax\s*=?\s*[-+e0-9.]+;', f'ymax\t {ymax_str};', content)
    content = re.sub(r'zmin\s*=?\s*[-+e0-9.]+;', f'zmin\t {zmin_str};', content)
    content = re.sub(r'zmax\s*=?\s*[-+e0-9.]+;', f'zmax\t {zmax_str};', content)
    content = re.sub(r'xloc\s*=?\s*[-+e0-9.]+;', f'xloc\t {xloc_str};', content)
    content = re.sub(r'yloc\s*=?\s*[-+e0-9.]+;', f'yloc\t {yloc_str};', content)
    content = re.sub(r'zloc\s*=?\s*[-+e0-9.]+;', f'zloc\t {zloc_str};', content)
    content = re.sub(r'w1\s*=?\s*[-+e0-9.]+;', f'w1\t {w1_str};', content)
    content = re.sub(r'w2\s*=?\s*[-+e0-9.]+;', f'w2\t {w2_str};', content)
    content = re.sub(r't1\s*=?\s*[-+e0-9.]+;', f't1\t {t1_str};', content)
    content = re.sub(r't2\s*=?\s*[-+e0-9.]+;', f't2\t {t2_str};', content)
    content = re.sub(r'D1\s*=?\s*[-+e0-9.]+;', f'D1\t {D1:.2f};', content)
    content = re.sub(r'D2\s*=?\s*[-+e0-9.]+;', f'D2\t {D2:.2f};', content)
    content = re.sub(r'v\s*=?\s*[-+e0-9.]+;', f'v\t {v:.2f};', content)
    content = re.sub(r'r_f\s*=?\s*[-+e0-9.]+;', f'r_f\t {r_f:.2f};', content)

with open(case_setup_file, 'w') as f:
    f.write(content)

print(f"Values of the domain updated in {case_setup_file}")