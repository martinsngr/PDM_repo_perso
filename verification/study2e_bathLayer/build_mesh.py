#!/usr/bin/env python3
"""build_mesh.py  -  mesh and eps/K/fYarn/yarnID of a study 2e case: the grid of REV_midbath (job 3068) cut along y.
    python build_mesh.py <case> --below NB --above NA [--pad N Q]
Runs ../../meshing_strat_trial/REV_midbath/build_fields.py (same STL, x and z extents, padding, K 1e-11 binary cut cells)
with the y range of its rev_domain.json replaced by [y0 - NB*dy, y0 + NA*dy]: y0 = 0.333 mm (the bath plane of job 3068)
and dy = its cell size along y (2.667 mm / 133), so the cells above y0 are those of job 3068. NB rows below y0 are the
bath layer of B_layer (their yarn fields are overwritten by bathLayer.py). Writes system/blockMeshDict and 0/ fields.
--pad N Q (2026-11-05): graded padding, N free layers below and above the box growing by Q from the box cell size
(cell order and fields unchanged, only the outer z levels and the grading of the padding blocks)."""
import argparse
import importlib.util
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, "..", "..", "meshing_strat_trial", "REV_midbath")

ap = argparse.ArgumentParser()
ap.add_argument("case")
ap.add_argument("--below", type=int, required=True, help="rows below the bath plane y0 (bath layer)")
ap.add_argument("--above", type=int, required=True, help="rows above y0 (fabric)")
ap.add_argument("--pad", nargs=2, metavar=("N", "Q"), default=None,
                help="graded padding (2026-11-05): N free cell layers below and above the box instead of 3, the first one "
                     "the box cell size, each next one Q times larger (padding thickness dz (Q^N - 1)/(Q - 1)); "
                     "without it: 3 layers of the box cell size, as job 3068")
a = ap.parse_args()

rev = json.load(open(os.path.join(src, "rev_domain.json")))
y0, y1 = rev["min_m"][1], rev["max_m"][1]
dy = (y1 - y0) / 133                          # job 3068: 133 rows from y0 to y1
rev["min_m"][1] = y0 - a.below * dy
rev["max_m"][1] = y0 + a.above * dy
case = os.path.abspath(a.case)
os.makedirs(os.path.join(case, "system"), exist_ok=True)
dom = os.path.join(case, "system", "rev_domain.json")
json.dump(rev, open(dom, "w"), indent=2)

spec = importlib.util.spec_from_file_location("build_fields", os.path.join(src, "build_fields.py"))
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)
bf.DOMAIN_FILE = dom                          # absolute: os.path.join(here, DOMAIN_FILE) returns it unchanged
npad = int(a.pad[0]) if a.pad else 3
sys.argv = ["build_fields.py", case, "--k-mode", "scalar", "--k-scalar", "1e-11", "--cut-cells", "binary",
            "--wick-axis", "y", "--zpad", str(npad)]
bf.main()
print(f"y rows: {a.below} below and {a.above} above y0 = {y0 * 1e3:.6f} mm, dy {dy * 1e6:.4f} um")

if a.pad:
    # graded padding: build_fields.py wrote 3 z blocks (npad uniform layers, the box, npad uniform layers) and the fields
    # on that grid (the padding cells are free whatever their size: no yarn outside the box). Only the outer z levels
    # (vertices 0-3 and 12-15) and the grading of the two padding blocks change; the box cells stay where they are.
    import re
    q = float(a.pad[1])
    p = os.path.join(case, "system", "blockMeshDict")
    s = open(p).read()
    head, rest = s.split("vertices\n(\n", 1)
    vtxt, tail = rest.split(");", 1)
    verts = [[float(t) for t in l.strip()[1:-1].split()] for l in vtxt.strip().splitlines()]
    assert len(verts) == 16, "expected 4 z levels (padding, box, padding)"
    zb0, zb1 = verts[4][2], verts[8][2]                 # box limits
    nbox = int(re.findall(r"hex \(4 5 6 7 8 9 10 11\) \(\d+ \d+ (\d+)\)", tail)[0])
    dz = (zb1 - zb0) / nbox
    T = dz * (q ** npad - 1) / (q - 1)
    for i in range(4):
        verts[i][2] = zb0 - T
        verts[12 + i][2] = zb1 + T
    r = q ** (npad - 1)                                 # last / first cell of a block along z
    tail, n0 = re.subn(r"(hex \(0 1 2 3 4 5 6 7\) \(\d+ \d+ \d+\)) simpleGrading \(1 1 1\)",
                       rf"\1 simpleGrading (1 1 {1 / r:.9g})", tail)
    tail, n2 = re.subn(r"(hex \(8 9 10 11 12 13 14 15\) \(\d+ \d+ \d+\)) simpleGrading \(1 1 1\)",
                       rf"\1 simpleGrading (1 1 {r:.9g})", tail)
    assert n0 == 1 and n2 == 1
    vtxt = "".join(f"    ({x:.9g} {y:.9g} {z:.9g})\n" for x, y, z in verts)
    open(p, "w").write(head + "vertices\n(\n" + vtxt + ");" + tail)
    print(f"graded padding: {npad} layers of {dz * 1e6:.3f} um x {q}^k below and above the box, "
          f"{T * 1e3:.4f} mm each (outermost cell {dz * r * 1e6:.1f} um)")
