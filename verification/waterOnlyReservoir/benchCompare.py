"""2D bench with and without the water-only reservoir (change J): the bench checks of
../../meshing_strat_trial/2D_bench/check.py on each run folder (check_summary.md, check.png written there) and the
inlet flux split by face type (yarn faces / gap faces, water / air, m3/s per unit depth of the 20 um slab; out > 0).

    ../../.venv/bin/python benchCompare.py [run ...]      (default: bench_regression bench_waterOnly)
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "..", "..", "meshing_strat_trial", "2D_bench")
sys.path.insert(0, BENCH)
import check as C  # noqa: E402


def patch_values(path, patch):
    s = open(path).read().split("boundaryField", 1)[1]
    blk = s.split(f"\n    {patch}\n", 1)[1]
    blk = blk[:blk.index("\n    }")]
    m = re.search(r"value\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", blk)
    if not m:
        u = re.search(r"value\s+uniform\s+([^;]+);", blk)
        return float(u.group(1)) if u else 0.0
    n = int(m.group(1))
    return np.array(blk[m.end():].split(")", 1)[0].split()[:n], float)


def inlet_split(run):
    eps = C.field("0", "eps")                         # [k, i]
    por = eps[:, 0] <= 0.99                           # inlet faces ordered by k
    print(f"\n{run}: inlet flux by face type (m3/s, out > 0)")
    print("| t (ms) | yarn faces water | yarn faces air | gap faces water | gap faces air |")
    print("|---|---|---|---|---|")
    for t in ("5e-05", "0.0001", "0.0005", "0.001", "0.002"):
        d = os.path.join(C.HERE, t)
        if not os.path.isdir(d):
            continue
        phi = patch_values(os.path.join(d, "phi"), "inlet")
        aphi = patch_values(os.path.join(d, "alphaPhi0.wetting"), "inlet")
        print(f"| {float(t)*1e3:.2f} | {aphi[por].sum():+.2e} | {(phi - aphi)[por].sum():+.2e} | "
              f"{aphi[~por].sum():+.2e} | {(phi - aphi)[~por].sum():+.2e} |")


for run in sys.argv[1:] or ["bench_regression", "bench_waterOnly"]:
    C.HERE = os.path.join(HERE, run)
    print(f"\n==================== {run}")
    try:
        C.main()                                      # ends with sys.exit(0 if all checks pass else 1)
    except SystemExit as e:
        print(f"check.py: {'all checks pass' if not e.code else 'some checks fail'}")
    print(open(os.path.join(C.HERE, "check_summary.md")).read())
    inlet_split(run)
