#!/usr/bin/env python3
"""
build_fields.py  -  uniform hex mesh + porosity / permeability fields for a DBS
(micro-continuum) solver such as hybridPorousInterFoam, from a TexGen STL.

Run it from the OpenFOAM case directory (edit the CONFIGURATION block first):
    python3 build_fields.py
    blockMesh
    checkMesh

What it does
  1. writes system/blockMeshDict: one block, uniform cells of size ~DX covering the domain
  2. for each yarn (closed body of the STL) computes the yarn fraction f in every cell:
       - inside/outside is evaluated on the mesh NODES (each node is shared by 8 cells -> cheap)
       - all 8 corners inside  -> f = 1       all 8 outside -> f = 0
       - only 'cut' cells (corners disagree) are sub-sampled with SUB^3 points
     (limit: a yarn feature thinner than one cell can slip between corners. With 0.3 mm
      yarns and 10-30 um cells this does not happen, but keep it in mind.)
  3. builds the fields
       eps = 1 - f_total * VF_YARN                         (volume-conserving porosity)
       K   = yarn tensor  if f_total >= K_THRESHOLD, else K_VOID * I
             yarn tensor  K = Kperp*I + (Kpar - Kperp) t t   (t = unit yarn direction)
             Kpar, Kperp from Gebart (1992) with VF_YARN and R_FIBRE
  4. writes 0/eps, 0/K (optionally 0/Kinv) and the check fields 0/fYarn, 0/yarnID

Requires: pip install numpy trimesh rtree      (optional, much faster: pip install embreex)
"""
import json
import math
import os
import time

import numpy as np

# ================================ CONFIGURATION ================================
CASE_DIR    = "."                                  # OpenFOAM case directory
STL_FILE    = "constant/triSurface/PW-22-15-0.4-0.5.stl"
STL_SCALE   = 1e-2          # STL units -> metres (TexGen model in cm -> 1e-2)
DOMAIN_FILE = "rev_domain.json"  # REV written by inspect_stl.py (in metres); used if the file exists
DOMAIN_MIN  = None          # otherwise: REV corner (x, y, z) in STL units; None = STL bounding box
DOMAIN_MAX  = None          #   -> MUST be set if you exported untrimmed yarns
DX          = 20e-6         # target cell size [m]; rounded so an integer number of cells fits
SUB         = 4             # sub-samples per direction in cut cells (4 -> 64 points per cell)

VF_YARN     = 0.50          # fibre volume fraction inside the yarns [-]   <-- ESTIMATE/MEASURE
R_FIBRE     = 7.5e-6        # fibre radius [m]                            <-- MEASURE
PACKING     = "hex"         # Gebart packing: "hex" or "quad"
K_VOID      = 1.0           # permeability of the free space [m2] (as in Boubaker et al. 2026)
K_THRESHOLD = 0.5           # cell gets the yarn permeability if f_total >= this

ORIENTATION  = "axis"       # "axis":   each yarn gets its main in-plane axis (x or y), no crimp
                            # "texgen": local tangent from the TexGen model (follows crimp)
TEXGEN_MODEL = "fabric.tg3" # only used with ORIENTATION = "texgen"

FIELD_EPS   = "eps"         # names expected by YOUR solver -> check its tutorial 0/ folder
FIELD_K     = "K"           # set to None to skip
FIELD_KINV  = None          # e.g. "Kinv" if the solver wants the inverse permeability
WRITE_CHECK_FIELDS = True   # also write fYarn (yarn fraction) and yarnID for ParaView

# boundary faces of the box -> (patch name, type[, neighbour patch for cyclic])
PATCHES = {
    "xmin": ("inlet",  "patch"),
    "xmax": ("outlet", "patch"),
    "ymin": ("sideA",  "cyclic", "sideB"),
    "ymax": ("sideB",  "cyclic", "sideA"),
    "zmin": ("bottom", "patch"),
    "zmax": ("top",    "patch"),
}
CHUNK = 200_000             # points per inside-test call (limits memory use)
# ===============================================================================

# vertex numbering of the single hex block and outward-oriented faces (blockMesh convention)
FACE_VERTS = {"xmin": "(0 4 7 3)", "xmax": "(2 6 5 1)", "ymin": "(1 5 4 0)",
              "ymax": "(3 7 6 2)", "zmin": "(0 3 2 1)", "zmax": "(4 5 6 7)"}


# ------------------------------------------------------------------ physics
def gebart(vf, rf, packing="hex"):
    """Permeability of a unidirectional fibre bundle along (Kpar) and across (Kperp) the fibres."""
    if packing == "hex":
        c, C1, vf_max = 53.0, 16 / (9 * math.pi * math.sqrt(6)), math.pi / (2 * math.sqrt(3))
    elif packing == "quad":
        c, C1, vf_max = 57.0, 16 / (9 * math.pi * math.sqrt(2)), math.pi / 4
    else:
        raise ValueError("PACKING must be 'hex' or 'quad'")
    k_par = 8 * rf**2 / c * (1 - vf)**3 / vf**2
    k_perp = C1 * (math.sqrt(vf_max / vf) - 1)**2.5 * rf**2
    return k_par, k_perp


# ------------------------------------------------------------------ geometry
def load_yarns(stl_file, scale):
    """Return a list of closed bodies (one per yarn), in metres.
    Each body must provide .bounds (2x3), .volume, .is_watertight and .contains(points)."""
    import trimesh
    mesh = trimesh.load(stl_file, force="mesh")
    mesh.apply_scale(scale)
    bodies = mesh.split(only_watertight=False)
    bad = [i for i, b in enumerate(bodies) if not b.is_watertight]
    if bad:
        raise SystemExit(f"Bodies {bad} are not closed -> inside test unreliable. "
                         "Run inspect_stl.py and fix the STL first.")
    return bodies


def inside(body, pts):
    """Inside test in chunks (ray-based tests in trimesh are memory-hungry)."""
    out = np.empty(len(pts), dtype=bool)
    for s in range(0, len(pts), CHUNK):
        out[s:s + CHUNK] = body.contains(pts[s:s + CHUNK])
    return out


def yarn_fraction(body, lo, d, n, sub):
    """Yarn fraction f[i,j,k] of one body in every cell of the uniform grid (0 outside its bbox).
    Returns (i0, j0, k0) offset and the local f block, to keep memory small."""
    bmin = np.maximum(body.bounds[0], lo)
    bmax = np.minimum(body.bounds[1], lo + n * d)
    if np.any(bmin >= bmax):
        return None                                           # yarn entirely outside the REV
    i0 = np.maximum(np.floor((bmin - lo) / d).astype(int) - 1, 0)       # first cell
    i1 = np.minimum(np.ceil((bmax - lo) / d).astype(int) + 1, n)        # last cell + 1
    m = i1 - i0                                                         # cells in the block

    # 1) inside/outside on the (m+1)^3 nodes of the block
    ax = [lo[a] + d[a] * np.arange(i0[a], i1[a] + 1) for a in range(3)]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    nodes_in = inside(body, np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]))
    nodes_in = nodes_in.reshape(m[0] + 1, m[1] + 1, m[2] + 1).astype(np.int8)

    # 2) count inside corners for every cell
    c = sum(nodes_in[a:a + m[0], b:b + m[1], e:e + m[2]]
            for a in (0, 1) for b in (0, 1) for e in (0, 1))
    f = (c == 8).astype(np.float32)
    cut = np.argwhere((c > 0) & (c < 8))

    # 3) sub-sample the cut cells only
    if len(cut):
        s = (np.arange(sub) + 0.5) / sub - 0.5                          # offsets in (-0.5, 0.5)
        off = np.array(np.meshgrid(s, s, s, indexing="ij")).reshape(3, -1).T * d
        centres = lo + (cut + i0 + 0.5) * d
        pts = (centres[:, None, :] + off[None, :, :]).reshape(-1, 3)
        frac = inside(body, pts).reshape(len(cut), -1).mean(axis=1)
        f[cut[:, 0], cut[:, 1], cut[:, 2]] = frac
    return i0, f, len(cut)


def texgen_tangents(points_m, model, scale):
    """Local yarn tangent at each point from the TexGen model (API names: see 02_texgen_timing.py).
    Returns (tangents Nx3, valid mask). Tangent sign does not matter: K uses t t."""
    from TexGen.Core import ReadFromXML, GetTextile, XYZ, XYZVector, PointInfoVector
    ReadFromXML(model)
    textile = GetTextile()
    pts = XYZVector()
    for p in points_m / scale:                                # back to TexGen units
        pts.push_back(XYZ(*map(float, p)))
    info = PointInfoVector()
    textile.GetPointInformation(pts, info)
    tang = np.zeros((len(points_m), 3))
    valid = np.zeros(len(points_m), dtype=bool)
    for k, pi in enumerate(info):
        if pi.iYarnIndex >= 0:
            t = pi.YarnTangent
            tang[k] = (t.x, t.y, t.z)
            valid[k] = True
    norm = np.linalg.norm(tang, axis=1)
    valid &= norm > 0
    tang[valid] /= norm[valid, None]
    return tang, valid


# ------------------------------------------------------------------ OpenFOAM output
def foam_header(cls, obj, location=None):
    loc = f'    location    "{location}";\n' if location else ""
    return ("/*--------------------------------*- C++ -*----------------------------------*/\n"
            "FoamFile\n{\n    version     2.0;\n    format      ascii;\n"
            f"    class       {cls};\n{loc}    object      {obj};\n}}\n"
            "// generated by 03_build_fields.py\n\n")


def write_block_mesh(case, lo, hi, n):
    v = [(lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]), (hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]),
         (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]), (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2])]
    txt = foam_header("dictionary", "blockMeshDict", "system")
    txt += "convertToMeters 1;\n\nvertices\n(\n"
    txt += "".join(f"    ({x:.9g} {y:.9g} {z:.9g})\n" for x, y, z in v) + ");\n\n"
    txt += f"blocks\n(\n    hex (0 1 2 3 4 5 6 7) ({n[0]} {n[1]} {n[2]}) simpleGrading (1 1 1)\n);\n\n"
    txt += "edges\n(\n);\n\nboundary\n(\n"
    for face, spec in PATCHES.items():
        name, typ = spec[0], spec[1]
        extra = f"        neighbourPatch {spec[2]};\n" if typ == "cyclic" else ""
        txt += (f"    {name}\n    {{\n        type {typ};\n{extra}"
                f"        faces ({FACE_VERTS[face]});\n    }}\n")
    txt += ");\n\nmergePatchPairs\n(\n);\n"
    os.makedirs(os.path.join(case, "system"), exist_ok=True)
    with open(os.path.join(case, "system", "blockMeshDict"), "w") as fh:
        fh.write(txt)


def write_field(case, name, values, dims):
    """values: (N,) -> volScalarField, (N,3,3) -> volTensorField. Cells in OpenFOAM order."""
    tensor = values.ndim == 3
    cls, kind = ("volTensorField", "tensor") if tensor else ("volScalarField", "scalar")
    lines = (["(" + " ".join(f"{x:.8g}" for x in t.ravel()) + ")" for t in values]
             if tensor else [f"{x:.8g}" for x in values])
    txt = foam_header(cls, name, "0")
    txt += f"dimensions      {dims};\n\n"
    txt += f"internalField   nonuniform List<{kind}>\n{len(values)}\n(\n"
    txt += "\n".join(lines) + "\n);\n\nboundaryField\n{\n"
    for spec in PATCHES.values():
        typ = "cyclic" if spec[1] == "cyclic" else "zeroGradient"
        txt += f"    {spec[0]}\n    {{\n        type {typ};\n    }}\n"
    txt += "}\n"
    os.makedirs(os.path.join(case, "0"), exist_ok=True)
    with open(os.path.join(case, "0", name), "w") as fh:
        fh.write(txt)


# ------------------------------------------------------------------ main
def main():
    t_start = time.perf_counter()
    bodies = load_yarns(os.path.join(CASE_DIR, STL_FILE), STL_SCALE)
    print(f"{len(bodies)} yarn bodies loaded")

    # domain and grid
    domain_file = os.path.join(CASE_DIR, DOMAIN_FILE) if DOMAIN_FILE else None
    if domain_file and os.path.isfile(domain_file):
        with open(domain_file) as fh:
            rev = json.load(fh)
        if not math.isclose(rev["stl_scale"], STL_SCALE):
            raise SystemExit(f"{DOMAIN_FILE} was made with scale {rev['stl_scale']}, "
                             f"but STL_SCALE = {STL_SCALE}. Re-run inspect_stl.py.")
        lo, hi = np.array(rev["min_m"]), np.array(rev["max_m"])
        print(f"REV read from {DOMAIN_FILE} (made from {rev['stl_file']}, zgap {rev['zgap']})")
    elif DOMAIN_MIN is None:
        lo = np.min([b.bounds[0] for b in bodies], axis=0)
        hi = np.max([b.bounds[1] for b in bodies], axis=0)
    else:
        lo, hi = np.array(DOMAIN_MIN) * STL_SCALE, np.array(DOMAIN_MAX) * STL_SCALE
    n = np.maximum(np.round((hi - lo) / DX).astype(int), 1)
    d = (hi - lo) / n
    ncells = int(np.prod(n))
    print(f"Domain [mm]: {lo * 1e3} -> {hi * 1e3}")
    print(f"Cells: {n[0]} x {n[1]} x {n[2]} = {ncells:,}   cell size [um]: {d * 1e6}")
    if d.max() / d.min() > 1.2:
        print("  note: cells are not cubic (aspect ratio > 1.2); adjust DX or the domain if possible")
    write_block_mesh(CASE_DIR, lo, hi, n)

    # yarn fraction per cell, per yarn
    f_total = np.zeros(n, dtype=np.float32)
    f_best = np.zeros(n, dtype=np.float32)
    owner = np.full(n, -1, dtype=np.int32)
    n_cut = 0
    for y, body in enumerate(bodies):
        t0 = time.perf_counter()
        res = yarn_fraction(body, lo, d, n, SUB)
        if res is None:
            continue
        i0, f, nc = res
        n_cut += nc
        sl = tuple(slice(i0[a], i0[a] + f.shape[a]) for a in range(3))
        f_total[sl] += f
        better = f > f_best[sl]
        f_best[sl] = np.where(better, f, f_best[sl])
        owner[sl] = np.where(better, y, owner[sl])
        print(f"  yarn {y:2d}: {nc:7d} cut cells  ({time.perf_counter() - t0:.1f} s)")

    overlap = int(np.sum(f_total > 1 + 1e-6))
    f_total = np.minimum(f_total, 1.0)

    # flatten to OpenFOAM cell order (x fastest, then y, then z) == Fortran order
    F = f_total.ravel(order="F")
    OWN = owner.ravel(order="F")
    eps = 1.0 - F * VF_YARN
    is_yarn = F >= K_THRESHOLD

    # orientation of each yarn cell
    tang = np.zeros((ncells, 3))
    main_axis = np.array([np.argmax(b.extents[:2]) for b in bodies])     # 0 = x, 1 = y
    idx = np.where(is_yarn)[0]
    tang[idx, main_axis[OWN[idx]]] = 1.0
    if ORIENTATION == "texgen":
        ijk = np.column_stack(np.unravel_index(idx, n, order="F"))
        centres = lo + (ijk + 0.5) * d
        t_tg, ok = texgen_tangents(centres, TEXGEN_MODEL, STL_SCALE)
        tang[idx[ok]] = t_tg[ok]
        print(f"TexGen tangent found for {ok.mean() * 100:.1f} % of yarn cells "
              "(others keep the main-axis direction)")

    # permeability
    k_par, k_perp = gebart(VF_YARN, R_FIBRE, PACKING)
    I = np.eye(3)
    tt = tang[:, :, None] * tang[:, None, :]
    K = np.broadcast_to(K_VOID * I, (ncells, 3, 3)).copy()
    K[idx] = k_perp * I + (k_par - k_perp) * tt[idx]

    # write
    write_field(CASE_DIR, FIELD_EPS, eps, "[0 0 0 0 0 0 0]")
    if FIELD_K:
        write_field(CASE_DIR, FIELD_K, K, "[0 2 0 0 0 0 0]")
    if FIELD_KINV:
        Kinv = np.broadcast_to(I / K_VOID, (ncells, 3, 3)).copy()
        Kinv[idx] = I / k_perp + (1 / k_par - 1 / k_perp) * tt[idx]
        write_field(CASE_DIR, FIELD_KINV, Kinv, "[0 -2 0 0 0 0 0]")
    if WRITE_CHECK_FIELDS:
        write_field(CASE_DIR, "fYarn", F, "[0 0 0 0 0 0 0]")
        write_field(CASE_DIR, "yarnID", OWN.astype(float), "[0 0 0 0 0 0 0]")

    # report
    v_cell = np.prod(d)
    v_body = sum(b.volume for b in bodies)
    print("\n=========== summary ===========")
    print(f"Gebart ({PACKING}, Vf={VF_YARN}, rf={R_FIBRE * 1e6:.1f} um): "
          f"Kpar = {k_par:.3e} m2, Kperp = {k_perp:.3e} m2, ratio {k_par / k_perp:.2f}")
    print(f"Cut cells: {n_cut:,} ({n_cut / ncells * 100:.1f} % of mesh; overlapping yarns counted twice)")
    print(f"Yarn volume, fractional (sum f*V):   {F.sum() * v_cell * 1e9:.4f} mm3")
    print(f"Yarn volume, thresholded (f>={K_THRESHOLD}): {is_yarn.sum() * v_cell * 1e9:.4f} mm3")
    print(f"Yarn volume, STL bodies (whole bodies, incl. parts outside REV): {v_body * 1e9:.4f} mm3")
    print(f"Yarn fraction of REV: {F.mean():.3f}    mean porosity of REV: {eps.mean():.3f}")
    print(f"Cells where yarns overlap: {overlap:,}")
    print(f"First cell centres (compare with 0/C from 'postProcess -func writeCellCentres'):")
    for c in (0, 1, int(n[0])):
        ijk = np.array(np.unravel_index(c, n, order="F"))
        print(f"   cell {c}: {lo + (ijk + 0.5) * d}")
    print(f"Done in {time.perf_counter() - t_start:.1f} s. Next: blockMesh, checkMesh, paraFoam.")


if __name__ == "__main__":
    main()