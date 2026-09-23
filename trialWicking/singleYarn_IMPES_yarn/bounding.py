import os
import glob
import re
import numpy as np
from stl import mesh

# -----------------------------
# User parameters
# -----------------------------
margin_x = 0.10
margin_y = 0.50
margin_z_bottom = 0.50
margin_z_top = 0.50

# -----------------------------
# Find STL
# -----------------------------
stl_files = glob.glob("constant/triSurface/*.stl")

if not stl_files:
    raise FileNotFoundError("No STL file found in constant/triSurface/")

filename = stl_files[0]
geometry_file = os.path.basename(filename)
fabric_name = os.path.splitext(geometry_file)[0]

print(f"Reading STL file: {filename}")

# -----------------------------
# Read STL bounding box
# -----------------------------
your_mesh = mesh.Mesh.from_file(filename)
points = your_mesh.vectors.reshape(-1, 3)

min_coords = np.min(points, axis=0)
max_coords = np.max(points, axis=0)
delta = max_coords - min_coords

print("STL bounding box:")
print(f"x: {min_coords[0]} -> {max_coords[0]}   deltaX = {delta[0]}")
print(f"y: {min_coords[1]} -> {max_coords[1]}   deltaY = {delta[1]}")
print(f"z: {min_coords[2]} -> {max_coords[2]}   deltaZ = {delta[2]}")

# -----------------------------
# Domain around the single yarn
# -----------------------------
xmin = min_coords[0] + margin_x * delta[0]
xmax = max_coords[0] - margin_x * delta[0]

ymin = min_coords[1] - margin_y * delta[1]
ymax = max_coords[1] + margin_y * delta[1]

zmin = min_coords[2] - margin_z_bottom * delta[2]
zmax = max_coords[2] + margin_z_top * delta[2]

# -----------------------------
# locationInMesh: point in fluid region
# -----------------------------
xloc = 0.5 * (xmin + xmax)
yloc = 0.5 * (ymin + ymax)
zloc = zmin + 0.10 * (zmax - zmin)

# -----------------------------
# point inside solid yarn
# -----------------------------
xcat = 0.5 * (min_coords[0] + max_coords[0])
ycat = 0.5 * (min_coords[1] + max_coords[1])
zcat = 0.5 * (min_coords[2] + max_coords[2])

zWater = min_coords[2]
zWater_str = f"{zWater:.6f}"

# -----------------------------
# Format values
# -----------------------------
xmin_str = f"{xmin:.6f}"
xmax_str = f"{xmax:.6f}"
ymin_str = f"{ymin:.6f}"
ymax_str = f"{ymax:.6f}"
zmin_str = f"{zmin:.6f}"
zmax_str = f"{zmax:.6f}"

xloc_str = f"{xloc:.6f}"
yloc_str = f"{yloc:.6f}"
zloc_str = f"{zloc:.6f}"

xcat_str = f"{xcat:.6f}"
ycat_str = f"{ycat:.6f}"
zcat_str = f"{zcat:.6f}"

zWater_str = f"{zWater:.6f}"

# -----------------------------
# Save diagnostic file
# -----------------------------
output_file = "boundingBoxDims.txt"

with open(output_file, "w") as f:
    f.write(f"File: {geometry_file}\n\n")

    f.write("Original STL bounding box\n")
    f.write(f"xmin_stl: {min_coords[0]}\n")
    f.write(f"xmax_stl: {max_coords[0]}\n")
    f.write(f"deltaX_stl: {delta[0]}\n\n")

    f.write(f"ymin_stl: {min_coords[1]}\n")
    f.write(f"ymax_stl: {max_coords[1]}\n")
    f.write(f"deltaY_stl: {delta[1]}\n\n")

    f.write(f"zmin_stl: {min_coords[2]}\n")
    f.write(f"zmax_stl: {max_coords[2]}\n")
    f.write(f"deltaZ_stl: {delta[2]}\n\n")

    f.write("OpenFOAM domain\n")
    f.write(f"xmin: {xmin}\n")
    f.write(f"xmax: {xmax}\n")
    f.write(f"ymin: {ymin}\n")
    f.write(f"ymax: {ymax}\n")
    f.write(f"zmin: {zmin}\n")
    f.write(f"zmax: {zmax}\n\n")

    f.write("locationInMesh fluid point\n")
    f.write(f"xloc: {xloc}\n")
    f.write(f"yloc: {yloc}\n")
    f.write(f"zloc: {zloc}\n\n")

    f.write("pointInsideSolid yarn point\n")
    f.write(f"xcat: {xcat}\n")
    f.write(f"ycat: {ycat}\n")
    f.write(f"zcat: {zcat}\n")
    
    f.write(f"zWater: {zWater}\n")
    
print(f"Bounding box saved in: {output_file}")

def replace_or_append(content, name, value):
    pattern = rf"{name}\s*=?\s*[-+eE0-9.]+;"
    replacement = f"{name}\t {value};"

    if re.search(pattern, content):
        return re.sub(pattern, replacement, content)
    else:
        return content + f"\n{replacement}"

# -----------------------------
# Update caseSetup
# -----------------------------
case_setup_file = "./caseSetup"

with open(case_setup_file, "r") as f:
    content = f.read()

content = replace_or_append(content, "xmin", xmin_str)
content = replace_or_append(content, "xmax", xmax_str)
content = replace_or_append(content, "ymin", ymin_str)
content = replace_or_append(content, "ymax", ymax_str)
content = replace_or_append(content, "zmin", zmin_str)
content = replace_or_append(content, "zmax", zmax_str)

content = replace_or_append(content, "xloc", xloc_str)
content = replace_or_append(content, "yloc", yloc_str)
content = replace_or_append(content, "zloc", zloc_str)

content = replace_or_append(content, "xcat", xcat_str)
content = replace_or_append(content, "ycat", ycat_str)
content = replace_or_append(content, "zcat", zcat_str)

content = replace_or_append(content, "zWater", zWater_str)

with open(case_setup_file, "w") as f:
    f.write(content)

print(f"Values of the domain updated in: {case_setup_file}")
print(f"geometryFile = {geometry_file}")
print(f"fabricName   = {fabric_name}")
print(f"locationInMesh = ({xloc_str} {yloc_str} {zloc_str})")
print(f"pointInsideSolid = ({xcat_str} {ycat_str} {zcat_str})")
print(f"zWater = {zWater_str}")