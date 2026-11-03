#!/usr/bin/env python3
"""build_mesh.py  -  mesh and eps/K/fYarn/yarnID of a study 2e case: the grid of REV_midbath (job 3068) cut along y.
    python build_mesh.py <case> --below NB --above NA
Runs ../../meshing_strat_trial/REV_midbath/build_fields.py (same STL, x and z extents, padding, K 1e-11 binary cut cells)
with the y range of its rev_domain.json replaced by [y0 - NB*dy, y0 + NA*dy]: y0 = 0.333 mm (the bath plane of job 3068)
and dy = its cell size along y (2.667 mm / 133), so the cells above y0 are those of job 3068. NB rows below y0 are the
bath layer of B_layer (their yarn fields are overwritten by bathLayer.py). Writes system/blockMeshDict and 0/ fields."""
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
sys.argv = ["build_fields.py", case, "--k-mode", "scalar", "--k-scalar", "1e-11", "--cut-cells", "binary",
            "--wick-axis", "y", "--zpad", "3"]
bf.main()
print(f"y rows: {a.below} below and {a.above} above y0 = {y0 * 1e3:.6f} mm, dy {dy * 1e6:.4f} um")
