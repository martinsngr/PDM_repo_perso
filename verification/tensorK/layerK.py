#!/usr/bin/env python3
"""Check 5: write a layered permeability into <case>/0/K (the 1D column of ../wicking1D/ABC, cells numbered from the inlet).

    python3 layerK.py <case>/0/K scalar|tensor <n1> <K1> <K2> [<Kt>]

Cells 0 .. n1-1 get K1 along y, the others K2. scalar: volScalarField K_y; tensor: volTensorField diag(Kt, K_y, Kt)
(Kt default 1e-11; no face across the column in 1D, so it cannot act). The boundaryField of the existing file is kept.
"""
import re
import sys

path, mode, n1, k1, k2 = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
kt = sys.argv[6] if len(sys.argv) > 6 else "1e-11"
N = 172
txt = open(path).read()
ky = [k1] * n1 + [k2] * (N - n1)
if mode == "tensor":
    txt = re.sub(r"(\n\s*class\s+)volScalarField;", r"\1volTensorField;", txt, count=1)
    vals, kind = [f"({kt} 0 0 0 {k} 0 0 0 {kt})" for k in ky], "tensor"
else:
    vals, kind = ky, "scalar"
new = f"internalField   nonuniform List<{kind}>\n{N}\n(\n" + "\n".join(vals) + "\n);"
txt, n = re.subn(r"internalField\s+uniform\s+[^;]+;", new, txt, count=1)
if n != 1:
    raise SystemExit(f"{path}: no 'internalField uniform ...;' to replace")
open(path, "w").write(txt)
print(f"{path}: {mode} K, cells 0-{n1 - 1} K_y {k1}, cells {n1}-{N - 1} K_y {k2}")
