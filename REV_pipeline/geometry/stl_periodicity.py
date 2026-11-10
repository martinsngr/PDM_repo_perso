#!/usr/bin/env python3
"""stl_periodicity.py  -  is a TexGen STL periodic over its REV box? (README, Weave test; 2026-11-10)
    .venv/bin/python -I stl_periodicity.py Textiles/<weave>.stl rev_domain_<weave>.json [--strip 150]
Needs an STL exported without domain trimming (yarns longer than the box, as funge.py writes them). Unlike
check_periodicity.py (first and last cell layers of a built mesh, equal only for a weave mirror-symmetric about the box
planes, as the plain weave), this works for any weave.
Periodicity of a TexGen STL over a REV box: every STL vertex within `strip` of a box plane x = lo or y = lo (and inside the
box along the other in-plane axis) is moved by +L along that axis and its distance to the STL surface measured; the same
from the hi planes with -L. A periodic geometry gives the facet chord error only. Per yarn (warp i at x = lo + i*L_x/4,
weft 5 + j at y = lo + j*L_y/4, from each body's centre): median, p95 and max distance [um], and the share above 10 um."""
import json
import sys

import numpy as np
import trimesh

stl, dom = sys.argv[1], sys.argv[2]
strip = float(sys.argv[sys.argv.index("--strip") + 1]) if "--strip" in sys.argv else 150.0
m = trimesh.load(stl, force="mesh")
m.apply_scale(1e4)                                    # cm -> um
d = json.load(open(dom))
lo, hi = np.array(d["min_m"]) * 1e6, np.array(d["max_m"]) * 1e6
L = hi - lo
lab_f = trimesh.graph.connected_component_labels(m.face_adjacency, node_count=len(m.faces))
lab_v = np.full(len(m.vertices), -1)
lab_v[m.faces.ravel()] = np.repeat(lab_f, 3)
name = {}
for c in np.unique(lab_f):
    v = m.vertices[np.unique(m.faces[lab_f == c])]
    ext = v.max(axis=0) - v.min(axis=0)
    cen = v.mean(axis=0)
    if ext[1] > ext[0]:   # along y: warp
        name[c] = int(round((cen[0] - lo[0]) / (L[0] / 4)))
    else:
        name[c] = 5 + int(round((cen[1] - lo[1]) / (L[1] / 4)))
print(f"{stl}: {len(m.vertices):,} vertices, {len(m.faces):,} faces, {len(name)} bodies "
      f"(yarn names {sorted(name.values())}); box {lo.round(1)} - {hi.round(1)} um; strip {strip:g} um")
pq = trimesh.proximity.ProximityQuery(m)
V = m.vertices
for a, ax in ((0, "x"), (1, "y")):
    b = 1 - a
    inside = (V[:, b] >= lo[b]) & (V[:, b] <= hi[b])
    res = {}
    for side, sel, shift in (("lo", inside & (V[:, a] >= lo[a]) & (V[:, a] <= lo[a] + strip), L[a]),
                             ("hi", inside & (V[:, a] <= hi[a]) & (V[:, a] >= hi[a] - strip), -L[a])):
        P = V[sel].copy()
        P[:, a] += shift
        _, dist, _ = pq.on_surface(P)
        for c, dd in zip(lab_v[sel], dist):
            res.setdefault(name[c], []).append(dd)
    print(f"  {ax} planes: yarn: n, median / p95 / max [um], share > 10 um")
    for k in sorted(res):
        dd = np.array(res[k])
        print(f"    {k}: {dd.size:6d}, {np.median(dd):6.2f} / {np.percentile(dd, 95):6.2f} / {dd.max():6.2f}, "
              f"{(dd > 10).mean() * 100:5.1f} %")
    alld = np.concatenate([np.array(v) for v in res.values()])
    print(f"    all: {alld.size:6d}, {np.median(alld):6.2f} / {np.percentile(alld, 95):6.2f} / {alld.max():6.2f}, "
          f"{(alld > 10).mean() * 100:5.1f} %")
