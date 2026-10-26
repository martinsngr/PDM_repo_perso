"""Readers for the raw OpenFOAM output used by the plot_*.py scripts of this folder.

Only reads: written fields (ASCII), polyMesh, solver logs and the csv files of the function objects.
No smoothing, filtering or fitting of the data. The one derived quantity is reconstruct(phi) (cell velocity from the
face fluxes, OpenFOAM's fvc::reconstruct formula), used for change F.
"""
import gzip
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases")
FIGS = os.path.join(HERE, "figures")

# reference palette (dataviz skill), fixed order
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
GRID, MUTED = "#e3e3e3", "#6b6b6b"


def style(ax, title=None):
    if title:
        ax.set_title(title, fontsize=9, loc="left")
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def strip_comments(txt):
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    return re.sub(r"//[^\n]*", "", txt)


def _list_after(txt, pos):
    """n ( ... ) starting at pos: returns n and the body between the outer parentheses."""
    m = re.compile(r"\s*(\d+)\s*\(").match(txt, pos)
    n, i, depth = int(m.group(1)), m.end(), 1
    j = i
    while depth:
        c = txt[j]
        depth += (c == "(") - (c == ")")
        j += 1
    return n, txt[i:j - 1]


def _values(body, n, vector):
    a = np.array(body.replace("(", " ").replace(")", " ").split(), float)
    return a.reshape(n, 3) if vector else a


def read_field(path, ncells=None, vector=None):
    """internalField of a volume or surface field; uniform values need ncells."""
    txt = strip_comments(open(path).read())
    if vector is None:
        vector = "volVectorField" in txt or "surfaceVectorField" in txt
    m = re.search(r"internalField\s+uniform\s+([^;]+);", txt)
    if m:
        v = np.array(m.group(1).strip("() ").split(), float)
        return np.tile(v, (ncells, 1)) if vector else np.full(ncells, v[0])
    m = re.search(r"internalField\s+nonuniform\s+List<\w+>", txt)
    n, body = _list_after(txt, m.end())
    return _values(body, n, vector)


def read_boundary_values(path, patch, nfaces):
    """'value' of a patch in a scalar field (uniform or nonuniform)."""
    txt = strip_comments(open(path).read())
    b = txt[txt.index("boundaryField"):]
    m = re.search(r"\b" + re.escape(patch) + r"\s*\{", b)
    i, depth = m.end(), 1
    j = i
    while depth:
        depth += (b[j] == "{") - (b[j] == "}")
        j += 1
    blk = b[i:j - 1]
    mu = re.search(r"\bvalue\s+uniform\s+([^;]+);", blk)
    if mu:
        return np.full(nfaces, float(mu.group(1)))
    mn = re.search(r"\bvalue\s+nonuniform\s+List<scalar>", blk)
    if mn:
        n, body = _list_after(blk, mn.end())
        return _values(body, n, False)
    return np.zeros(nfaces)          # no value entry (e.g. empty): no flux


def times(case):
    """Written time directories (numeric names, 0 included), sorted by value."""
    out = []
    for d in os.listdir(case):
        try:
            out.append((float(d), d))
        except ValueError:
            pass
    return [d for _, d in sorted(out)]


def read_mesh(case):
    """points, faces (list of int arrays), owner, neighbour, patches {name: (start, n)} from constant/polyMesh."""
    pm = os.path.join(case, "constant", "polyMesh")

    def lst(name):
        txt = strip_comments(open(os.path.join(pm, name)).read())
        txt = txt[txt.index("}") + 1:] if "FoamFile" in txt else txt
        m = re.search(r"\d+\s*\(", txt)
        return _list_after(txt, m.start())

    n, body = lst("points")
    pts = _values(body, n, True)
    n, body = lst("faces")
    faces = [np.array(f.split(), int) for f in re.findall(r"\d+\(([^)]*)\)", body)]
    own = np.array(lst("owner")[1].split(), int)
    nei = np.array(lst("neighbour")[1].split(), int)
    btxt = strip_comments(open(os.path.join(pm, "boundary")).read())
    btxt = btxt[btxt.index("}") + 1:]
    patches = {}
    for name, blk in re.findall(r"(\w+)\s*\{([^}]*)\}", btxt):
        nf = int(re.search(r"nFaces\s+(\d+)", blk).group(1))
        st = int(re.search(r"startFace\s+(\d+)", blk).group(1))
        typ = re.search(r"type\s+(\w+)", blk).group(1)
        patches[name] = (st, nf, typ)
    return pts, faces, own, nei, patches


def face_area_vectors(pts, faces):
    """Sf of each face (triangle fan about the face centre, as OpenFOAM for planar faces)."""
    S = np.zeros((len(faces), 3))
    for i, f in enumerate(faces):
        p = pts[f]
        c = p.mean(axis=0)
        S[i] = 0.5 * np.cross(p - c, np.roll(p, -1, axis=0) - c).sum(axis=0)
    return S


def reconstruct_phi(case, t, mesh=None):
    """fvc::reconstruct(phi): U_P = inv(sum_f Sf Sf/|Sf|) . sum_f (Sf/|Sf|) phi_f over the faces of each cell
    (sign: outward). Boundary flux from the 'value' of phi on each non-empty patch."""
    pts, faces, own, nei, patches = mesh or read_mesh(case)
    S = face_area_vectors(pts, faces)
    nc = own.max() + 1
    nint = len(nei)
    phi = np.zeros(len(faces))
    path = os.path.join(case, t, "phi")
    phi[:nint] = read_field(path, vector=False)
    for name, (st, nf, typ) in patches.items():
        if typ != "empty":
            phi[st:st + nf] = read_boundary_values(path, name, nf)
    magS = np.linalg.norm(S, axis=1)
    n = S / magS[:, None]
    T = np.zeros((nc, 3, 3))
    b = np.zeros((nc, 3))
    for f in range(len(faces)):
        if f >= nint and any(st <= f < st + nf and typ == "empty" for st, nf, typ in patches.values()):
            continue
        outer = np.outer(S[f], S[f]) / magS[f]
        T[own[f]] += outer
        b[own[f]] += n[f] * phi[f]
        if f < nint:
            T[nei[f]] += outer
            b[nei[f]] += n[f] * phi[f]          # (-n)(-phi) for the neighbour
    U = np.zeros((nc, 3))
    for c in range(nc):
        idx = [i for i in range(3) if T[c, i, i] > 0]
        U[c, idx] = np.linalg.solve(T[c][np.ix_(idx, idx)], b[c, idx])
    return U


def log_lines(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", errors="replace") as f:
        return f.readlines()


def find_log(case):
    for f in sorted(os.listdir(case)):
        if f.startswith("log.hybridPorousInterFoam") and not f.endswith(".tail"):
            return os.path.join(case, f)
    return None


def log_exec(path):
    for line in log_lines(path)[:40]:
        if line.startswith("Exec"):
            return line.split(":", 1)[1].strip()
    return "?"


def read_csv(path):
    """Header line starting with '#' (or plain), comma or whitespace separated."""
    lines = [l for l in open(path) if l.strip()]
    head = lines[0].lstrip("#").strip()
    sep = "," if "," in head else None
    names = [h.strip() for h in head.split(sep)]
    data = np.array([[float(v) for v in l.split(sep)] for l in lines[1:] if not l.startswith("#")])
    return names, data
