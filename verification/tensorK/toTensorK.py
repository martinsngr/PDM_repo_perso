#!/usr/bin/env python3
"""Turn a scalar permeability file 0/K (volScalarField) into a tensor one (volTensorField), in place.

    python3 toTensorK.py <case>/0/K                          K*I everywhere (check 2)
    python3 toTensorK.py <case>/0/K --porous Kxx Kyy Kzz     porous cells (K < 1e-3 m2) diag(Kxx, Kyy, Kzz),
                                                              free cells (K_VOID) K*I (check 6)

Each value v (internal field and any `value` entry of the patches) becomes (v 0 0 0 v 0 0 0 v), written with the
same text as the scalar, so that the solver reads exactly the same number on the diagonal. Only `uniform v` and
`nonuniform List<scalar>` are handled; anything else stops the script.
"""
import re
import sys

POROUS = sys.argv[sys.argv.index("--porous") + 1:][:3] if "--porous" in sys.argv else None


def tens(v):
    if POROUS and float(v) < 1e-3:
        return f"({POROUS[0]} 0 0 0 {POROUS[1]} 0 0 0 {POROUS[2]})"
    return f"({v} 0 0 0 {v} 0 0 0 {v})"


def convert(txt):
    if "class       volScalarField;" not in txt:
        raise SystemExit("not a volScalarField (class line not found)")
    txt = txt.replace("class       volScalarField;", "class       volTensorField;", 1)

    def nonuniform(m):
        n, body = int(m.group(2)), m.group(3)
        vals = body.split()
        if len(vals) != n:
            raise SystemExit(f"{m.group(1)}: {len(vals)} values for a list of {n}")
        return f"{m.group(1)}nonuniform List<tensor>\n{n}\n(\n" + "\n".join(tens(v) for v in vals) + "\n)"

    # nonuniform lists (internalField and patch values): "nonuniform List<scalar> <n> ( v v ... )"
    txt, nn = re.subn(r"(\b(?:internalField|value)\s+)nonuniform\s+List<scalar>\s*(\d+)\s*\(([^()]*)\)",
                      nonuniform, txt)
    # uniform values: "uniform v"
    txt, nu = re.subn(r"(\b(?:internalField|value)\s+)uniform\s+([-+0-9.eE]+)",
                      lambda m: f"{m.group(1)}uniform {tens(m.group(2))}", txt)
    if "List<scalar>" in txt or nn + nu == 0:
        raise SystemExit("unhandled entry left in the file")
    return txt, nn, nu


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path) as fh:
        new, nn, nu = convert(fh.read())
    with open(path, "w") as fh:
        fh.write(new)
    what = f"porous cells diag({' '.join(POROUS)}), others K*I" if POROUS else "K*I"
    print(f"{path}: volTensorField {what} ({nn} nonuniform list(s), {nu} uniform value(s))")
