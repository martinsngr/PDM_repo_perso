#!/usr/bin/env python3
"""Section-averaged saturation profile along the yarn axis, for the 3D yarn cases.

A line probe (sampleDict) misses parts of a crimped yarn, so instead every write
time is cut into slices of thickness dx along x, and each slice gets the
volume-weighted mean of the field over its cells. Output, in the same format as
the 1D sampleDict profiles read by wickingFront.ipynb:

    postProcessing/sectionProfile/<time>/alongYarn_<field>.csv
    columns: x (distance from the inlet face x = xmin, in m), <field>

Run from a reconstructed case folder, after
    postProcess -func writeCellCentres -time 0
    postProcess -func writeCellVolumes -time 0
(0/Cx and 0/V). Usage: python3 ../sectionProfile.py <field> [dx, default 20e-6]
Standard library only (the system python3 has no numpy).
"""
import os
import re
import sys


def read_internal(path, n_cells=None):
    """internalField of an ascii volScalarField, as a list (uniform is expanded)."""
    with open(path) as f:
        text = f.read()
    m = re.search(r"internalField\s+uniform\s+([^;\s]+)\s*;", text)
    if m:
        if n_cells is None:
            raise ValueError(f"{path}: uniform field, cell count unknown")
        return [float(m.group(1))]*n_cells
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", text)
    if not m:
        raise ValueError(f"{path}: no ascii internalField")
    n = int(m.group(1))
    values = text[m.end():].split(None, n)[:n]
    return [float(v) for v in values]


def main():
    field = sys.argv[1]
    dx = float(sys.argv[2]) if len(sys.argv) > 2 else 50e-6

    x = read_internal("0/Cx")
    V = read_internal("0/V")
    x0 = min(x)
    # the slices start at the inlet face, not at the first cell centre
    xmin = float(re.search(r"^xmin\s+([^;\s]+)", open("caseSetup").read(), re.M).group(1))
    if x0 < xmin:
        raise ValueError("cell centre below xmin of caseSetup")
    nBins = int((max(x) - xmin)/dx) + 1
    binOf = [int((xi - xmin)/dx) for xi in x]
    vol = [0.0]*nBins
    for b, v in zip(binOf, V):
        vol[b] += v

    times = []
    for d in os.listdir("."):
        try:
            t = float(d)
        except ValueError:
            continue
        if os.path.isfile(os.path.join(d, field)):
            times.append((t, d))

    for t, d in sorted(times):
        S = read_internal(os.path.join(d, field), len(x))
        num = [0.0]*nBins
        for b, s, v in zip(binOf, S, V):
            num[b] += s*v
        out = os.path.join("postProcessing", "sectionProfile", d)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"alongYarn_{field}.csv"), "w") as f:
            f.write(f"x,{field}\n")
            for b in range(nBins):
                if vol[b] > 0:
                    f.write(f"{(b + 0.5)*dx:.6g},{num[b]/vol[b]:.6g}\n")
        print(f"t = {d}: {sum(1 for v in vol if v > 0)} slices")


if __name__ == "__main__":
    main()
