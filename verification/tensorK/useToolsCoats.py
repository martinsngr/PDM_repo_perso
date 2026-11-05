#!/usr/bin/env python3
"""Replace the coded coatsTimeStep block of a controlDict by the shared function object, in place.

    python3 useToolsCoats.py <case>/system/controlDict

The 1D cases (../wicking1D) carry their own copy of the Coats function object, which reads K as a volScalarField
(fatal with a tensor K). The block from the line "    coatsTimeStep" to the next line "    }" becomes
    coatsTimeStep { #include "../../tools/coatsTimeStep" }
(path relative to system/: <case>/../tools, i.e. verification/tensorK/tools). The controlDict keeps its CoatsMaxCo,
dSmax, maxDeltaTCoats and minDeltaTCoats entries, which the shared function object reads.
"""
import sys

path = sys.argv[1]
lines = open(path).read().split("\n")
i = next(k for k, l in enumerate(lines) if l.rstrip() == "    coatsTimeStep")
if lines[i + 1].rstrip() != "    {":
    raise SystemExit(f"{path}: no block after line {i + 1}")
j = next(k for k in range(i + 2, len(lines)) if lines[k].rstrip() == "    }")
lines[i:j + 1] = ['    coatsTimeStep { #include "../../tools/coatsTimeStep" }']
open(path, "w").write("\n".join(lines))
print(f"{path}: coded coatsTimeStep (lines {i + 1}-{j + 1}) replaced by tools/coatsTimeStep")
