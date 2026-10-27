#!/bin/bash
# Builds the bench and 1D run folders of this study (README.md) from the change-J cases of ../waterOnlyReservoir
# (setup files only: 0/, constant/ with the bench mesh, system/, run). Overwrites the folders.
#     ./makeCases.sh
# Run each with the installed solver:  (cd <case> && HPIF=hybridPorousInterFoam ./run)
# The REV runs (scratch copies of ../../meshing_strat_trial/REV) are described in README.md.
cd "${0%/*}" || exit 1
PY=${PY:-../../.venv/bin/python}
SRC=../waterOnlyReservoir

copyCase()   # <source case> <new case>
{
    rm -rf "$2"
    mkdir -p "$2"
    cp -r "$SRC/$1/0" "$SRC/$1/constant" "$SRC/$1/system" "$SRC/$1/run" "$2/"
}

copyCase bench_waterOnly bench_ref
copyCase bench_waterOnly bench_A
copyCase bench_waterOnly bench_B
copyCase bench_waterOnly bench_B0
copyCase 1D_bath0 1D_ref
copyCase 1D_bath0 1D_B
copyCase 1D_bath0 1D_B0

"$PY" - <<'EOF'
import re

def edit(path, old, new):
    s = open(path).read()
    assert s.count(old) == 1, f"{path}: {old!r}"
    open(path, "w").write(s.replace(old, new))

TOTAL = """        type            totalPressure;
        p0              uniform 0;
"""
ZERO_GRADIENT = """boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"

    ".*"
    {
        type            zeroGradient;
    }
}
"""

def phase_velocities_zero_gradient(case):
    for f in ("Uwetting", "UnonWetting"):
        path = f"{case}/0/{f}"
        s = open(path).read()
        head, tail = s.split("boundaryField", 1)
        tail = tail[tail.index("\n}\n") + 3:]
        open(path, "w").write(head + ZERO_GRADIENT + tail)

def inlet_alpha_one(path):
    s = open(path).read()
    head, bf = s.split("boundaryField", 1)
    blk = re.search(r"\n    inlet\n    \{\n.*?\n    \}\n", bf, re.S)
    new = ("\n    inlet\n    {\n        type            inletOutlet;\n        inletValue      uniform 1;\n"
           "        value           uniform 1;\n    }\n")
    open(path, "w").write(head + "boundaryField" + bf[:blk.start()] + new + bf[blk.end():])

OPEN = """    "(inlet|outlet)"
    {
        #include "../../tools/pOpenAir"
    }
"""
# bench_A: outlet (free faces only) totalPressure, inlet still pOpenAir; phase velocities zeroGradient
edit("bench_A/0/p", OPEN, """    inlet
    {
        #include "../../tools/pOpenAir"
    }
    outlet
    {
""" + TOTAL + """    }
""")
# bench_B, bench_B0: totalPressure on both open patches
for c in ("bench_A", "bench_B", "bench_B0"):
    phase_velocities_zero_gradient(c)
for c in ("bench_B", "bench_B0"):
    edit(f"{c}/0/p", OPEN, """    "(inlet|outlet)"
    {
""" + TOTAL + """    }
""")
# bench_B: alpha 1 on the whole inlet; keywords read by pOpenAir only removed
inlet_alpha_one("bench_B/0/alpha.wetting")
tp = "bench_B/constant/transportProperties"
s = open(tp).read()
for kw in ("openPorousAirZero", "openFreeTotalPressure", "reservoirWaterPressure"):
    s, n = re.subn(rf"^{kw}\s[^\n]*\n", "", s, flags=re.M)
    assert n == 1, kw
open(tp, "w").write(s)

# 1D_B, 1D_B0: inlet totalPressure (the porous outlet face keeps its coded air-at-0 BC)
for c in ("1D_B", "1D_B0"):
    path = f"{c}/0/p"
    s = open(path).read()
    head, bf = s.split("boundaryField", 1)
    blk = re.search(r"\n    inlet\n    \{\n.*?\n    \}\n", bf, re.S)
    assert "waterPressureZeroInlet" in blk.group(0)
    new = "\n    inlet\n    {\n" + TOTAL + "    }\n"
    open(path, "w").write(head + "boundaryField" + bf[:blk.start()] + new + bf[blk.end():])
# 1D_B: alpha 1 on the inlet (run copies alpha.wetting.orig to alpha.wetting)
for f in ("alpha.wetting.orig", "alpha.wetting"):
    inlet_alpha_one(f"1D_B/0/{f}")
edit("1D_B/0/alpha.wetting.orig", """    // enters through the inlet is at alpha 0.99, the same value as the
    // impesFoam case (../1D_vertical_impes_inletRes)
""", """    // enters through the inlet is at alpha 1 (saturated by the bath: p = 0
    // there is the bath water pressure, ../README.md)
""")
EOF
