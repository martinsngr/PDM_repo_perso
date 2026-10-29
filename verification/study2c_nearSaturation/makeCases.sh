#!/bin/bash
# Builds the run folders of this study (README.md) from ../standardOpenBC/bench_B (2D thick-wall slit with the REV's
# inlet treatment: G + H + F' + I, J, p totalPressure, alpha 1 on the inlet). Setup files only (0/, constant/ with the
# mesh, system/, run). Overwrites the folders it builds.
#     ./makeCases.sh [run ...]        (no argument: all runs of the table below)
# Run each with the installed solver:  (cd <run> && HPIF=hybridPorousInterFoam ./run)   or  ./runAll.sh <run ...>
#
# Per run (one line of RUNS): name, pc0 [Pa], m, wall saturation, theta0 [deg], edits.
#   Wall saturation: a value (every porous cell, eps <= 0.99), prof:x1:S1:x2:S2:... (x in mm along the slit,
#   linear in between, constant beyond the ends) or keep (bench_B's initial field: dry walls with the 0.2 mm ramp).
#   Free cells start as air except the 0.1 mm water column at the inlet.
#   Edits (comma-separated, optional):
#     -<kw>         removes the line of keyword kw (constant/transportProperties)
#     <kw>=<value>  sets keyword kw (constant/transportProperties)
#     +<kw>=<value> appends keyword kw (the switches of the scratch solver variants in solver/)
#     gap=<n>       gap of n cells in the middle of the 24 z cells (walls (24 - n)/2 cells, eps 0.5, K 1e-11)
#     dtmax=<s>     maxDeltaTCoats in system/controlDict (cap of the coatsTimeStep dt)
cd "${0%/*}" || exit 1
PY=${PY:-../../.venv/bin/python}
SRC=../standardOpenBC/bench_B

RUNS="
N0_lowpc_S091     1000 0.4 0.91  60
N1_lowpc_S097     1000 0.4 0.97  60
N2_lowpc_S050     1000 0.4 0.50  60
N3_REVpc_S091     5000 0.5 0.91  60
N4_REVpc_S0995    5000 0.5 0.995 60
N5_lowpc_prof     1000 0.4 prof:0:0.98:0.2:0.96:0.35:0.83:0.6:0.6:0.97:0.1 60
N6_lowpc_S084_t40 1000 0.4 0.84  40
N7_lowpc_S078_g4  1000 0.4 0.78  60 gap=4
N8_lowpc_S091_dt  1000 0.4 0.91  60 dtmax=2.5e-7
N10_bench_ref     5000 0.5 keep  60
N11_bench_K2      5000 0.5 keep  60 +porousFreeKrAirPorous=on
N12_bench_G2      5000 0.5 keep  60 +porousFreeVofPc=on
N13_bench_G2b     5000 0.5 keep  60 +porousFreeVofPc=on
"

want=" $* "
echo "$RUNS" | while read -r name pc0 m sw theta edits; do
    [ -n "$name" ] || continue
    [ $# -eq 0 ] || [[ "$want" == *" $name "* ]] || continue
    case "$name" in N[0-9]*|A[0-9]*|K[0-9]*) ;; *) echo "bad run name $name"; exit 1 ;; esac
    rm -rf "./$name"
    mkdir "./$name"
    cp -r "$SRC/0" "$SRC/constant" "$SRC/system" "$SRC/run" "./$name/"
    rm -rf "./$name/constant/polyMesh/sets"
    "$PY" - "$name" "$pc0" "$m" "$sw" "$theta" "${edits:-}" <<'EOF'
import re, sys
import numpy as np
name, pc0, m, sw, theta, edits = sys.argv[1:7]
NX, NZ, DX = 100, 24, 20e-6       # bench_B mesh: cell c = i + NX*k


def edit(path, pattern, new, flags=re.M):
    s = open(path).read()
    s, n = re.subn(pattern, new, s, flags=flags)
    assert n == 1, f"{path}: {pattern!r} matched {n} times"
    open(path, "w").write(s)


def internal(path):
    txt = open(path).read()
    head, rest = txt.split("internalField", 1)
    n = int(re.search(r"nonuniform List<scalar>\s*(\d+)", rest).group(1))
    body = rest.split("(", 1)[1]
    vals = body.split(")", 1)[0].split()[:n]
    assert len(vals) == n == NX * NZ
    return head, vals, body.split(")", 1)[1]


def write_internal(path, head, vals, tail):
    open(path, "w").write(head + "internalField   nonuniform List<scalar> \n" + f"{len(vals)}\n(\n"
                          + "\n".join(vals) + "\n)" + tail)


tp = f"{name}/constant/transportProperties"
edit(tp, r"^    pc0 pc0 \[1 -1 -2 0 0 0 0\] [^;]+;", f"    pc0 pc0 [1 -1 -2 0 0 0 0] {pc0};")
edit(tp, r"^    m [^;]+;", f"    m {m};")
edit(tp, r"^theta0\s+[^;]+;", f"theta0                     {theta};")
gap = None
for e in filter(None, edits.split(",")):
    if e.startswith("gap="):
        gap = int(e[4:])
    elif e.startswith("dtmax="):
        edit(f"{name}/system/controlDict", r"^maxDeltaTCoats\s+[^;]+;", f"maxDeltaTCoats  {e[6:]};")
    elif e.startswith("+"):
        kw, val = e[1:].split("=", 1)
        s = open(tp).read()
        assert re.search(rf"^{re.escape(kw)}\s", s, re.M) is None, kw
        open(tp, "w").write(s.rstrip("\n").removesuffix("// ************************************************************************* //").rstrip("\n")
                            + f"\n\n// study2c scratch solver variant switch (solver/)\n{kw} {val};\n\n"
                            "// ************************************************************************* //\n")
    elif e.startswith("-"):
        edit(tp, rf"^{re.escape(e[1:])}\s[^\n]*\n", "")
    else:
        kw, val = e.split("=", 1)
        edit(tp, rf"^{re.escape(kw)}\s+[^;]+;", f"{kw} {val};")

i = np.arange(NX * NZ) % NX
k = np.arange(NX * NZ) // NX
x = (i + 0.5) * DX
he, eps, te = internal(f"{name}/0/eps")
if gap is not None:
    # walls (NZ - gap)/2 cells on each side, ending 3 cells before the outlet as bench_B
    nw = (NZ - gap) // 2
    assert 2 * nw + gap == NZ
    por = (i < NX - 3) & ((k < nw) | (k >= NZ - nw))
    hk, K, tk = internal(f"{name}/0/K")
    eps = ["0.5" if p else "1" for p in por]
    K = ["1e-11" if p else "1" for p in por]
    write_internal(f"{name}/0/eps", he, eps, te)
    write_internal(f"{name}/0/K", hk, K, tk)
por = np.array([float(e) <= 0.99 for e in eps])

# initial alpha: porous cells at the wall saturation (value or profile along x), free cells air except the 0.1 mm
# water column at the inlet (the bench_B column)
ha, old, ta = internal(f"{name}/0/alpha.wetting")
if sw == "keep":
    Sw = old
elif sw.startswith("prof:"):
    p = [float(v) for v in sw[5:].split(":")]
    xs, ss = np.array(p[0::2]) * 1e-3, np.array(p[1::2])
    Sw = [f"{v:.6g}" for v in np.interp(x, xs, ss)]
else:
    Sw = [sw] * len(x)
new = [Sw[c] if por[c] else ("1" if x[c] < 1e-4 else "0") for c in range(NX * NZ)]
if gap is None:   # the template's free cells are exactly this column
    assert all(n == o for n, o, p in zip(new, old, por) if not p)
write_internal(f"{name}/0/alpha.wetting", ha, new, ta)

# per-step locator of the largest porous |d alpha|/dt and the fastest free cell
edit(f"{name}/system/controlDict", r'^(    waterBudget   \{ #include "\.\./\.\./tools/waterBudget" \}\n)',
     r'\1    dsLocator     { #include "../../tools/dsLocator" }\n')
print(f"{name}: pc0 {pc0}, m {m}, wall S {sw}, theta {theta}, edits [{edits}], {int(por.sum())} porous cells, "
      f"{sum(1 for c in range(NX * NZ) if not por[c] and new[c] == '1')} free water cells")
EOF
done
