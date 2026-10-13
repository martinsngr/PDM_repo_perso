#!/usr/bin/env python3
"""
makeSlit.py  -  slit capillary-rise benchmarks (gap capillarity, S0-S3 of ../NOTES.md ("Slit tests")).

    ../../.venv/bin/python makeSlit.py <name> --walls real|porous --w 8 --theta 60 [--K 1e-20] [--T 2e-3] [--run]

2D vertical slit along x (gravity -x), 2 mm long, 20 um cells (100 along x), reservoir at x = 0 (inlet: free faces
water at total pressure 0 = reservoir at rest, openFreeTotalPressure 1; --static-inlet: static p = 0; porous faces
alpha 0.99), open to air at x = 2 mm (outlet). The gap starts with a water column of --fill (0.1 mm; without it the
meniscus does not form). Porous walls stop --wall-end cells (3) before the outlet: porous faces on the open outlet
are unstable (../NOTES.md). Across z:
  --walls real   : the gap only (w cells); the z patches are walls with constantAlphaContactAngle theta0 = THETA
                   (standard interFoam wall treatment, the reference for the free-surface model).
  --walls porous : --nw porous cells (4; eps 0.5, permeability K) | gap of w cells | --nw porous cells; behind them closed
                   walls; contact angle from the solver's porous contact-angle model (activatePorousContactAngle 1,
                   theta0 = THETA), as the REV yarn surfaces; change G on (bench default).
Solver settings, function objects (Coats/capillary-wave dt, liquidBalance, waterBudget, stopGuard) and p/U BCs come
from ../2D_bench. Free cells start as pure air; porous walls get the bench's 0.2 mm wetted ramp at the inlet.
--run runs blockMesh, setFields, initFields and the solver (serial, log in /tmp via runTools.sh).
"""
import argparse
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "..", "2D_bench")
NW = 4                 # default porous wall thickness [cells] (--nw)
DX = 20e-6             # default cell size [m] (--dx)
LX = 2e-3              # length along x [m]
NXC = round(LX / DX)   # cells along x (set from --dx in main)


def sub(path, old, new, count=1):
    s = open(path).read()
    if old not in s:
        raise SystemExit(f"{path}: pattern not found: {old[:60]!r}")
    open(path, "w").write(s.replace(old, new, count))


def main():
    global DX, NXC
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--walls", choices=("real", "porous"), required=True)
    ap.add_argument("--w", type=int, default=8, help="gap width [cells]")
    ap.add_argument("--theta", type=float, default=60.0)
    ap.add_argument("--nw", type=int, default=NW, help="porous wall thickness [cells] (REV half yarn width ~8)")
    ap.add_argument("--K", type=float, default=1e-20, help="porous wall permeability [m2]")
    ap.add_argument("--T", type=float, default=2e-3, help="end time [s]")
    ap.add_argument("--write", type=float, default=5e-5)
    ap.add_argument("--fill", type=float, default=1e-4,
                    help="initial water column in the gap from the inlet [m] (the meniscus must start inside the domain)")
    ap.add_argument("--wall-end", type=int, default=3,
                    help="porous walls stop this many cells before the outlet (keeps porous faces off the open outlet, "
                         "which is unstable like an open porous lateral boundary; 0 = walls to the outlet)")
    ap.add_argument("--inlet-alpha", choices=("inletOutlet", "fixed"), default="inletOutlet",
                    help="alpha.wetting on the inlet: inletOutlet (bench; zeroGradient while the flux is 0, so an empty "
                         "gap sees no water at t = 0) or fixed (fixedValue = the inletValue: reservoir always in contact)")
    ap.add_argument("--static-inlet", action="store_true",
                    help="free inlet faces at static p = 0 (old setup); default: total pressure 0 (reservoir at rest)")
    ap.add_argument("--solver", default="hybridPorousInterFoam")
    ap.add_argument("--alphaScheme", default=None,
                    help="div(phi,alpha) scheme for free faces, e.g. 'Gauss vanLeer' (default: as 2D_bench)")
    ap.add_argument("--alphaSubCycles", type=int, default=None)
    ap.add_argument("--dx", type=float, default=DX, help="cell size [m] (gap/wall widths and --wall-end are in cells)")
    ap.add_argument("--add", action="append", default=[],
                    help="add a transportProperties keyword KEY=VALUE (e.g. porousContactAngleWallLike=1)")
    ap.add_argument("--set", action="append", default=[],
                    help="extra transportProperties edit KEY=VALUE (e.g. activatePorousContactAngle=0)")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    DX = a.dx
    NXC = round(LX / DX)

    case = os.path.join(HERE, a.name)
    if os.path.exists(case):
        shutil.rmtree(case)
    os.makedirs(case)
    for d in ("system", "constant", "0.orig"):
        shutil.copytree(os.path.join(BENCH, d), os.path.join(case, d), ignore=shutil.ignore_patterns("polyMesh"))
    open(os.path.join(case, f"{a.name}.foam"), "w").close()
    porous = a.walls == "porous"
    nz = a.w + (2 * a.nw if porous else 0)

    # ---- mesh
    zmax = nz * DX
    open(os.path.join(case, "system/blockMeshDict"), "w").write(f"""FoamFile {{ format ascii; class dictionary; object blockMeshDict; }}
// generated by makeSlit.py: slit {a.name}, walls {a.walls}, gap {a.w} cells, {nz} cells across
convertToMeters 1;
vertices
(
    (0 0 0) ({LX} 0 0) ({LX} {DX} 0) (0 {DX} 0)
    (0 0 {zmax:.9g}) ({LX} 0 {zmax:.9g}) ({LX} {DX} {zmax:.9g}) (0 {DX} {zmax:.9g})
);
blocks ( hex (0 1 2 3 4 5 6 7) ({NXC} 1 {nz}) simpleGrading (1 1 1) );
boundary
(
    inlet  {{ type patch; faces ((0 4 7 3)); }}
    outlet {{ type patch; faces ((2 6 5 1)); }}
    bottom {{ type {'patch' if porous else 'wall'}; faces ((0 3 2 1)); }}
    top    {{ type {'patch' if porous else 'wall'}; faces ((4 5 6 7)); }}
    frontAndBack {{ type empty; faces ((1 5 4 0) (3 7 6 2)); }}
);
""")
    # ---- porous walls: setFields boxes
    if porous:
        z1, z2 = a.nw * DX, (a.nw + a.w) * DX
        x2 = LX - a.wall_end * DX + (0 if a.wall_end else 1)
        open(os.path.join(case, "system/setFieldsDict"), "w").write(f"""FoamFile {{ format ascii; class dictionary; object setFieldsDict; }}
// generated by makeSlit.py: porous walls z < {z1:.6g} and z > {z2:.6g}, K {a.K:g}
defaultFieldValues ( volScalarFieldValue eps 1 volScalarFieldValue K 1 );
regions
(
    boxToCell {{ box (-1 -1 -1) ({x2:.9g} 1 {z1:.9g}); fieldValues ( volScalarFieldValue eps 0.5 volScalarFieldValue K {a.K:g} ); }}
    boxToCell {{ box (-1 -1 {z2:.9g}) ({x2:.9g} 1 1); fieldValues ( volScalarFieldValue eps 0.5 volScalarFieldValue K {a.K:g} ); }}
);
""")
    # ---- contact angle
    tp = os.path.join(case, "constant/transportProperties")
    sub(tp, "activatePorousContactAngle 0;", f"activatePorousContactAngle {1 if porous else 0};")
    sub(tp, "theta0                     90;", f"theta0                     {a.theta:g};")
    if not a.static_inlet:
        sub(tp, "openFreeTotalPressure 0;", "openFreeTotalPressure 1;")
    if a.add:
        open(tp, "a").write("\n// added by makeSlit.py --add\n"
                           + "".join(f"{kv.split('=', 1)[0]} {kv.split('=', 1)[1]};\n" for kv in a.add))
    for kv in a.set:
        k, v = kv.split("=", 1)
        s = open(tp).read()
        s, n = re.subn(rf"\n{re.escape(k)}(\s+)[^;]*;", lambda m: f"\n{k}{m.group(1)}{v};", s)
        if not n:
            raise SystemExit(f"--set: {k} not found in transportProperties")
        open(tp, "w").write(s)
    if a.alphaScheme:
        fs = os.path.join(case, "system/fvSchemes")
        t = open(fs).read()
        t, n = re.subn(r"(\n\s*div\(phi,alpha\)\s+)[^;]*;", lambda m: m.group(1) + a.alphaScheme + ";", t)
        if not n:
            raise SystemExit("div(phi,alpha) not found")
        open(fs, "w").write(t)
    if a.alphaSubCycles:
        sol = os.path.join(case, "system/fvSolution")
        t = open(sol).read()
        t, n = re.subn(r"(\n\s*nAlphaSubCycles\s+)\d+;", lambda m: m.group(1) + str(a.alphaSubCycles) + ";", t)
        open(sol, "w").write(t)
    # ---- control
    cd = os.path.join(case, "system/controlDict")
    s = open(cd).read()
    s = re.sub(r"\nendTime\s+[^;]+;", f"\nendTime         {a.T:g};", s)
    s = re.sub(r"\nwriteInterval\s+[^;]+;", f"\nwriteInterval   {a.write:g};", s)
    s = re.sub(r"\ntimePrecision\s+[^;]+;", "\ntimePrecision   12;", s)
    open(cd, "w").write(s)
    # ---- 0.orig: z patches closed (behind porous walls) or contact-angle walls (real walls)
    wall = {"p": "type fixedFluxPressure; value uniform 0;", "U": "type noSlip;",
            "Uwetting": "type fixedValue; value uniform (0 0 0);", "UnonWetting": "type fixedValue; value uniform (0 0 0);",
            "eps": "type zeroGradient;", "K": "type zeroGradient;"}
    for f, bc in wall.items():
        p = os.path.join(case, "0.orig", f)
        s = open(p).read().replace('"(inlet|outlet|top|bottom)"', '"(inlet|outlet)"')
        i = s.rindex("}")
        s = s[:i] + '    "(top|bottom)"\n    {\n        ' + bc + "\n    }\n" + s[i:]
        open(p, "w").write(s)
    with open(os.path.join(case, "slit.info"), "w") as fh:
        fh.write(f"walls {a.walls}\nw {a.w}\ntheta {a.theta}\nK {a.K}\nNW {a.nw if porous else 0}\nnz {nz}\n"
                 f"fill {a.fill}\ninletAlpha {a.inlet_alpha}\ninlet {'static' if a.static_inlet else 'total'}\nwallEnd {a.wall_end}\nsolver {a.solver}\nset {','.join(a.set) or '-'}\n"
                 f"dx {DX:g}\nadd {','.join(a.add) or '-'}\n"
                 f"alphaScheme {(a.alphaScheme or 'bench').replace(' ', '_')}\nalphaSubCycles {a.alphaSubCycles or 'bench'}\n")
    print(f"{a.name}: walls {a.walls}, gap {a.w} cells ({a.w * DX * 1e6:.0f} um), theta {a.theta:g}, "
          + (f"K {a.K:g}, " if porous else "") + f"{NXC} x {nz} cells, T {a.T:g} s")
    if a.run:
        run(case, a, porous)


def run(case, a, porous):
    py = os.path.abspath(os.path.join(HERE, "..", "..", ".venv", "bin", "python"))
    pre = (f'set -e; cd "{case}"; . "$WM_PROJECT_DIR/bin/tools/RunFunctions"; '
           'rm -rf 0 constant/polyMesh; cp -r 0.orig 0; runApplication blockMesh > /dev/null; '
           + ('runApplication setFields > /dev/null; ' if porous else '')
           + 'runApplication -s writeCellCentres postProcess -func writeCellCentres -time 0 > /dev/null; '
           f'{py} ../../tools/initFields.py > log.initFields; rm -f 0/C 0/Cx 0/Cy 0/Cz')
    if subprocess.run(["bash", "-c", pre]).returncode:
        raise SystemExit(f"{case}: pre-processing failed")
    # alpha.wetting z patches: zeroGradient behind porous walls, contact angle on real walls
    f = os.path.join(case, "0", "alpha.wetting")
    s = open(f).read()
    bc = ("type zeroGradient;" if porous else
          f"type constantAlphaContactAngle; theta0 {a.theta:g}; limit gradient; value uniform 0;")
    s = re.sub(r"\n    (top|bottom)\n    \{[^}]*\}", "", s)
    i = s.rindex("}")
    s = s[:i] + '    "(top|bottom)"\n    {\n        ' + bc + "\n    }\n" + s[i:]
    if a.inlet_alpha == "fixed":
        s, n = re.subn(r"(\n    inlet\n    \{\n\s*type\s+)inletOutlet;", r"\1fixedValue;", s)
        if not n:
            raise SystemExit("inlet inletOutlet not found in 0/alpha.wetting")
    # initial water column in the gap (free cells with x < fill)
    m = re.search(r"internalField\s+nonuniform List<scalar>\s*\n(\d+)\s*\n\(", s)
    n = int(m.group(1)); j = s.index(")", m.end())
    vals = [float(v) for v in s[m.end():j].split()]
    eps = open(os.path.join(case, "0", "eps")).read()
    me = re.search(r"internalField\s+nonuniform List<scalar>\s*\n\d+\s*\n\(", eps)
    epsv = ([float(v) for v in eps[me.end():eps.index(")", me.end())].split()] if me else [1.0] * n)
    for c in range(n):
        if epsv[c] > 0.99 and ((c % NXC) + 0.5) * DX < a.fill:
            vals[c] = 1.0
    s = s[:m.end()] + "\n" + "\n".join(f"{v:.6g}" for v in vals) + "\n" + s[j:]
    open(f, "w").write(s)
    solve = (f'cd "{case}"; . "$WM_PROJECT_DIR/bin/tools/RunFunctions"; . ../../tools/runTools.sh; '
             f'runTmpLog log.hybridPorousInterFoam {a.solver}; st=$?; rm -rf dynamicCode; '
             '[ "$(stat -c %s log.hybridPorousInterFoam)" -gt 2000000 ] && gzip -f log.hybridPorousInterFoam; exit $st')
    r = subprocess.run(["bash", "-c", solve])
    print(f"{os.path.basename(case)}: solver exit {r.returncode}")


if __name__ == "__main__":
    main()
