"""Comparisons of the standardOpenBC runs (README.md).

    ../../.venv/bin/python compare.py identical <run> <reference>   bit-identity: every field and file of every write
    ../../.venv/bin/python compare.py bench                         bench table (check.py of 2D_bench, inlet split)
    ../../.venv/bin/python compare.py 1D                            1D table (slopes vs the similarity solution)
    ../../.venv/bin/python compare.py rev <run> <reference>         REV table (per write, inlet split)

identical: per field the internal field text and the value of every patch are compared (not the rest of the patch
dictionary: the BC type and its keywords are expected to differ); other files (uniform/time, csv) as text.
Inlet split: water and air flux through the yarn faces (owner cell eps <= 0.99) and the gap faces of the inlet,
from the written phi and alphaPhi0.wetting (m3/s, out > 0).
"""
import csv
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(REPO, "meshing_strat_trial", "tools"))
from initFields import read_boundary, read_internal, read_owner  # noqa: E402

TIME = re.compile(r"[0-9.e+-]+")


def times(case):
    return sorted((d for d in os.listdir(case) if TIME.fullmatch(d) and d != "0"
                   and os.path.isdir(os.path.join(case, d))), key=float)


# ------------------------------------------------------------------ bit-identity
def parse_field(path):
    s = re.sub(r"#\{.*?#\}", "", open(path).read(), flags=re.S)        # sources of coded BCs
    if "internalField" not in s:
        return s, {}
    head, bf = s.split("boundaryField", 1)
    patches = {}
    for m in re.finditer(r"\n    (\S+)\s*\n    \{\n(.*?)\n    \}", bf, re.S):
        v = re.search(r"(?m)^\s+value\s+(.*?);", m.group(2), re.S)
        patches[m.group(1)] = v.group(1).split() if v else None
    return head.split("internalField", 1)[1].split(), patches


def identical(run, ref):
    tr, tf = times(run), times(ref)
    common = [t for t in tf if t in tr]
    print(f"{run} vs {ref}: writes {len(tr)} / {len(tf)}, compared {len(common)}")
    diffs, nfiles = {}, 0
    for t in common:
        for root, _, files in os.walk(os.path.join(ref, t)):
            for f in files:
                pf = os.path.join(root, f)
                rel = os.path.relpath(pf, ref)
                pr = os.path.join(run, rel)
                if not os.path.isfile(pr):
                    diffs.setdefault(rel, []).append("missing")
                    continue
                nfiles += 1
                (ia, pa), (ib, pb) = parse_field(pr), parse_field(pf)
                what = [] if ia == ib else ["internal"]
                what += [p for p in sorted(set(pa) | set(pb)) if pa.get(p) != pb.get(p)]
                if what:
                    diffs.setdefault(os.path.basename(rel), set()).update(what)
    for f in ("waterBudget.csv", "liquidBalance.csv"):
        a, b = os.path.join(run, f), os.path.join(ref, f)
        if os.path.isfile(a) and os.path.isfile(b):
            nfiles += 1
            if open(a).read() != open(b).read():
                diffs[f] = {"text"}
    print(f"files compared: {nfiles}")
    if not diffs:
        print("bit-identical (all compared values)")
    for k, v in sorted(diffs.items()):
        print(f"  differs: {k}: {', '.join(sorted(v)) if isinstance(v, set) else v}")


# ------------------------------------------------------------------ inlet split
def patch_values(path, patch):
    blk = re.sub(r"#\{.*?#\}", "", open(path).read(), flags=re.S).split("boundaryField", 1)[1]
    blk = blk.split(f"\n    {patch}\n", 1)[1]
    blk = blk[:blk.index("\n    }")]
    m = re.search(r"value\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", blk)
    if not m:
        u = re.search(r"value\s+uniform\s+([^;]+);", blk)
        return float(u.group(1)) if u else 0.0
    return np.array(blk[m.end():].split(")", 1)[0].split()[:int(m.group(1))], float)


def inlet_mask(case, patch="inlet"):
    owner = read_owner(case)
    eps = read_internal(os.path.join(case, "0", "eps"), owner.max() + 1)
    _, _, nf, sf = [p for p in read_boundary(case) if p[0] == patch][0]
    return eps[owner[sf:sf + nf]] <= 0.99


def inlet_split(case, t, por):
    phi = patch_values(os.path.join(case, t, "phi"), "inlet")
    aphi = patch_values(os.path.join(case, t, "alphaPhi0.wetting"), "inlet")
    return aphi[por].sum(), (phi - aphi)[por].sum(), aphi[~por].sum(), (phi - aphi)[~por].sum()


# ------------------------------------------------------------------ bench
def bench():
    sys.path.insert(0, os.path.join(REPO, "meshing_strat_trial", "2D_bench"))
    import check as C
    runs = [os.path.join(HERE, "..", "waterOnlyReservoir", "bench_waterOnly")] + \
        [os.path.join(HERE, r) for r in ("bench_ref", "bench_A", "bench_B", "bench_B0")]
    for run in runs:
        if not os.path.isfile(os.path.join(run, "waterBudget.csv")):
            print(f"\n{run}: not run")
            continue
        C.HERE = run
        print(f"\n==================== {os.path.relpath(run, HERE)}")
        try:
            C.main()
        except SystemExit as e:
            print(f"check.py: {'all checks pass' if not e.code else 'some checks fail'}")
        por = C.field("0", "eps")[:, 0] <= 0.99                       # inlet faces ordered by k
        print("| t (ms) | yarn faces water | yarn faces air | gap faces water | gap faces air |\n|---|---|---|---|---|")
        for t in ("5e-05", "0.0001", "0.0005", "0.001", "0.002"):
            if os.path.isdir(os.path.join(run, t)):
                print(f"| {float(t)*1e3:.2f} | " + " | ".join(f"{v:+.3e}" for v in inlet_split(run, t, por)) + " |")


# ------------------------------------------------------------------ 1D
def one_d():
    sys.path.insert(0, os.path.join(REPO, "verification"))
    import analyseWicking1D as W
    import wicking1DVariants as V
    W.CASE = "/"
    V.RUNS = [(os.path.join(HERE, "..", "waterOnlyReservoir", "1D_bath0"), "alpha.wetting", "1D_bath0 (stored)")] + \
        [(os.path.join(HERE, r), "alpha.wetting", r) for r in ("1D_ref", "1D_B", "1D_B0")]
    V.main()
    for r in ("1D_ref", "1D_B", "1D_B0"):
        log = os.path.join(HERE, r, "log.hybridPorousInterFoam")
        if os.path.isfile(log):
            n = sum(1 for line in open(log) if line.startswith("Time = "))
            print(f"{r}: {n} steps")


# ------------------------------------------------------------------ REV
def rev(run, ref):
    for case in (ref, run):
        print(f"\n==================== {case}")
        print(subprocess.run([sys.executable, os.path.join(case, "check.py"), case],
                             capture_output=True, text=True).stdout)
        por = inlet_mask(case)
        wb = {r["time"]: r for r in csv.DictReader(open(os.path.join(case, "waterBudget.csv")))}
        print("| t (ms) | water in domain (m3) | inflow inlet, cumulative (m3) | yarn faces water | yarn faces air "
              "| gap faces water | gap faces air |\n|---|---|---|---|---|---|---|")
        for t in times(case):
            r = wb.get(t, {})
            print(f"| {float(t)*1e3:.3f} | {float(r.get('water_m3', 'nan')):.5e} | {float(r.get('in_inlet', 'nan')):+.4e} | "
                  + " | ".join(f"{v:+.3e}" for v in inlet_split(case, t, por)) + " |")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "identical":
        identical(sys.argv[2], sys.argv[3])
    elif mode == "bench":
        bench()
    elif mode == "1D":
        one_d()
    elif mode == "rev":
        rev(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
