#!/usr/bin/env python3
"""constant/cellDecomposition for the 2D bench (100 x 1 x 24 cells, x fastest): cells with z-index < K on
processor 0, the others on processor 1. K = 8: processor boundary on the lower yarn surface (porous/free faces);
K = 12: in the middle of the gap (free/free faces only).
    python3 makeDecomposition.py <case> <K>"""
import sys
case, K = sys.argv[1], int(sys.argv[2])
n = 100 * 24
lab = [0 if (c // 100) < K else 1 for c in range(n)]
hdr = ('FoamFile\n{\n    version 2.0;\n    format ascii;\n    class labelList;\n    location "constant";\n'
       '    object cellDecomposition;\n}\n')
open(f"{case}/constant/cellDecomposition", "w").write(hdr + f"{n}\n(\n" + "\n".join(map(str, lab)) + "\n)\n")
