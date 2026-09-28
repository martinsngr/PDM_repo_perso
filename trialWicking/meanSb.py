#!/usr/bin/env python3
"""Volume-weighted mean saturation of an impesFoam case, per time folder.

    mean Sb = sum(Sb * V) / sum(V)

Also prints the liquid volume eps * sum(Sb * V), which should match
liquidBalance.csv (column totalLiquidVolume_mL).

Usage (from trialWicking/):
    python3 meanSb.py singleYarn_IMPES_vertical
    python3 meanSb.py 1D_vertical_impes          # the 1D case
    python3 meanSb.py <case> > meanSb.csv        # save as CSV

The cell volumes V come from `postProcess -func writeCellVolumes`. The mesh
does not move, so one V file is enough; if none exists, the script runs
writeCellVolumes on the latest time. Reads reconstructed results only
(run reconstructPar first on a parallel case).
"""
import os
import re
import subprocess
import sys


def read_internal_field(path, n_cells=None):
    """Return the internalField of an ASCII OpenFOAM volScalarField as a list."""
    text = open(path).read()
    head = text.split("internalField", 1)[1]
    first_line = head.split("\n", 1)[0]
    if "nonuniform" not in first_line:
        value = float(re.search(r"uniform\s+([^;]+);", first_line).group(1))
        if n_cells is None:
            raise ValueError(f"{path}: uniform field, number of cells unknown")
        return [value] * n_cells
    body = head.split("(", 1)[1]
    values = []
    for line in body.split("\n"):
        line = line.strip()
        if line == ")":
            break
        if line:
            values.append(float(line))
    return values


def time_dirs(case):
    """Numeric time folders, sorted by time."""
    times = []
    for name in os.listdir(case):
        try:
            t = float(name)
        except ValueError:
            continue
        if os.path.isdir(os.path.join(case, name)):
            times.append((t, name))
    return [name for _, name in sorted(times)]


def read_eps(case):
    """Porosity from constant/transportProperties (eps eps [...] value;)."""
    text = open(os.path.join(case, "constant", "transportProperties")).read()
    m = re.search(r"^\s*eps\s+eps\s+\[[^\]]*\]\s+([^;\s]+)\s*;", text, re.M)
    return float(m.group(1)) if m else None


def cell_volumes(case, times):
    for t in times:
        path = os.path.join(case, t, "V")
        if os.path.exists(path):
            return read_internal_field(path)
    latest = times[-1]
    print(f"# no V file found, running writeCellVolumes on time {latest}",
          file=sys.stderr)
    subprocess.run(["postProcess", "-case", case, "-func", "writeCellVolumes",
                    "-time", latest], check=True, stdout=subprocess.DEVNULL)
    return read_internal_field(os.path.join(case, latest, "V"))


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "."
    times = [t for t in time_dirs(case)
             if os.path.exists(os.path.join(case, t, "Sb"))]
    if not times:
        sys.exit(f"no time folder with an Sb field in {case}")

    V = cell_volumes(case, times)
    total_V = sum(V)
    eps = read_eps(case)

    print("time,meanSb,liquidVolume_mL" if eps else "time,meanSb")
    for t in times:
        Sb = read_internal_field(os.path.join(case, t, "Sb"), len(V))
        if len(Sb) != len(V):
            sys.exit(f"{t}/Sb has {len(Sb)} cells but V has {len(V)}")
        sbv = sum(s * v for s, v in zip(Sb, V))
        if eps:
            print(f"{t},{sbv / total_V:.4f},{eps * sbv * 1e6:.6e}")
        else:
            print(f"{t},{sbv / total_V:.4f}")


if __name__ == "__main__":
    main()
