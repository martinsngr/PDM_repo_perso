#!/usr/bin/env python3
"""Check 4: turn a copy of a 1D twin case into the 2D spreading box (README.md, check 4), in place.

    python3 make2D.py <case> hybrid|impes <xscale> scalar <K> | tensor <Kxx> <Kyy> <Kzz>

- system/blockMeshDict: 40 x 80 x 1 cells of (20 um * xscale) x 20 um x 20 um in two blocks, A (5 cells, x < 0.1 mm
  * xscale) and B (35 cells); patches inlet (bottom of A), walls (bottom of B, left, right), outlet (top),
  frontAndBack (empty). Cells are numbered block by block, A then B (x fastest), whatever xscale.
- every field of 0/ (and constant/K for impes): a `walls` entry before `frontAndBack` (hybrid: wall patch, U noSlip,
  p fixedFluxPressure, the others zeroGradient; impes: symmetry patch, all fields symmetry, see below).
- alpha.wetting (hybrid) or Sb (impes): max(0.002, 0.99 - 4.94 r[mm]), r = distance of the (unstretched) cell
  centre to the inlet segment, so that the stretched case gets the same value per cell.
- K (0/K hybrid, constant/K impes): uniform scalar or diagonal tensor.
"""
import math
import re
import sys

case, mode, xs = sys.argv[1], sys.argv[2], float(sys.argv[3])
kmode, kvals = sys.argv[4], sys.argv[5:]
NA, NB, NY, D = 5, 35, 80, 0.02                     # cells in A, B, along y; cell size [mm]


def blockmesh():
    x1, x2, ly, dz = NA * D * xs, (NA + NB) * D * xs, NY * D, D
    wtype = "wall" if mode == "hybrid" else "symmetry"
    v = [(0, 0, 0), (x1, 0, 0), (x2, 0, 0), (x2, ly, 0), (x1, ly, 0), (0, ly, 0)]
    v += [(x, y, dz) for x, y, _ in v]
    verts = "\n".join(f"    ({x:.12g} {y:.12g} {z:.12g})" for x, y, z in v)
    txt = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// tensorK check 4: 2D spreading box, x stretched by {xs:g} (make2D.py)
convertToMeters 0.001;
vertices
(
{verts}
);
blocks
(
    hex (0 1 4 5 6 7 10 11) ({NA} {NY} 1) simpleGrading (1 1 1)
    hex (1 2 3 4 7 8 9 10) ({NB} {NY} 1) simpleGrading (1 1 1)
);
edges ();
boundary
(
    inlet  {{ type patch; faces ((0 1 7 6)); }}
    walls  {{ type {wtype};  faces ((1 2 8 7) (0 6 11 5) (2 3 9 8)); }}
    outlet {{ type patch; faces ((4 5 11 10) (3 4 10 9)); }}
    frontAndBack {{ type empty; faces ((0 5 4 1) (1 4 3 2) (6 7 10 11) (7 8 9 10)); }}
);
mergePatchPairs ();
"""
    open(f"{case}/system/blockMeshDict", "w").write(txt)


def centres():
    """unstretched cell centres [mm], blockMesh order: block A then B, x fastest within a block"""
    out = []
    for n, x0 in ((NA, 0.0), (NB, NA * D)):
        for j in range(NY):
            for i in range(n):
                out.append((x0 + (i + 0.5) * D, (j + 0.5) * D))
    return out


def add_walls(path, entry):
    txt = open(path).read()
    if re.search(r"\n\s*walls\s*\n", txt):
        return
    new, n = re.subn(r"(\n)(\s*frontAndBack\s*\n)", r"\1    walls\n    {\n" + entry + r"    }\n\2", txt, count=1)
    if n != 1:
        raise SystemExit(f"{path}: no frontAndBack entry")
    open(path, "w").write(new)


def set_internal(path, text, cls=None):
    txt = open(path).read()
    new, n = re.subn(r"internalField\s+(uniform\s+[^;]+|nonuniform\s+List<\w+>\s*\d+\s*\([^)]*\))\s*;",
                     lambda m: f"internalField   {text};", txt, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: internalField not replaced")
    if cls:
        new = re.sub(r"(\n\s*class\s+)vol\w+Field;", rf"\1{cls};", new, count=1)
    open(path, "w").write(new)


zg = "        type            zeroGradient;\n"
blockmesh()
if mode == "hybrid":
    walls = {"U": "        type            noSlip;\n",
             "p": "        type            fixedFluxPressure;\n        value           uniform 0;\n"}
    for f in ("K", "U", "UnonWetting", "Uwetting", "alpha.wetting", "eps", "p"):
        add_walls(f"{case}/0/{f}", walls.get(f, zg))
    sat, kfile = f"{case}/0/alpha.wetting", f"{case}/0/K"
else:
    # walls as `symmetry` patches: anisoImpesFoam's darcyGradPressureAniso looks g up in the Time registry and
    # fails on OpenFOAM 9 (g is registered on the mesh); with g = 0 a symmetry patch carries no flux in its
    # formulation (zero normal gradient of p and Sb, diagonal K)
    sym = "        type            symmetry;\n"
    for f in ("Sb", "Ua", "Ub", "p"):
        add_walls(f"{case}/0/{f}", sym)
    add_walls(f"{case}/constant/K", sym)
    sat, kfile = f"{case}/0/Sb", f"{case}/constant/K"
vals = []
for x, y in centres():
    r = math.hypot(max(x - NA * D, 0.0), y)
    vals.append(f"{max(0.002, 0.99 - 4.94 * r):.10g}")
set_internal(sat, f"nonuniform List<scalar>\n{len(vals)}\n(\n" + "\n".join(vals) + "\n)")
if kmode == "scalar":
    set_internal(kfile, f"uniform {kvals[0]}", "volScalarField")
else:
    set_internal(kfile, f"uniform ({kvals[0]} 0 0 0 {kvals[1]} 0 0 0 {kvals[2]})", "volTensorField")
nwet = sum(float(v) > 0.002 for v in vals)
print(f"{case}: 2D box x{xs:g}, {mode}, K {kmode} {' '.join(kvals)}, {len(vals)} cells, {nwet} in the initial ramp")
