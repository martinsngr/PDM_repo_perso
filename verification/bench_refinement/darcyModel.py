"""Darcy-limit model of one hybridPorousInterFoam time step on the strip bench (no momentum equation).

    ../../.venv/bin/python darcyModel.py <orig|A|wideFaceAlpha> [r] [dt] [tEnd] [seed] [darcy|mom|mom0]

Total flux: darcy = Darcy limit (rAUf = Mf); mom = the momentum path of pEqn.H (rAU = 1/(rho/(eps dt) + Drag),
HbyA from the old U, OF9 ddtCorr, U reconstructed from the face fluxes); mom0 = mom without ddtCorr.

wideFaceAlpha (diagnostic, in no solver): the original cell-gradient phase velocities, interpolated, divided by
the face alpha (as A) instead of each cell dividing by its own alpha before interpolation.

Question: does the original discretisation of the porous transport alone (relative flux phirPore from cell-centred
Gauss-linear gradients, interpolated to faces) reproduce the blow-up of the strip bench, without the momentum path?

What it copies from be54696 (alphaEqn.H, updateDarcyVelocities.H, updateVariables.H, pEqn.H), same order per step:
  1. Uwetting, UnonWetting from fvc::grad (Gauss linear) of p, pc, alpha of the previous step; Ur =
     (Uw/max(a, 1e-3) - Un/max(1 - a, 1e-3))/eps; phirPore = interpolate(Ur) & Sf (orig), or, with A (b0c0f67), face
     Darcy fluxes from snGrad. Boundary phirPore: 0, except the outlet (Uwetting fixedValue 0):
     -Un_b.Sf/(eps(1 - a_b) + 0.001).
  2. alpha flux = upwind(alpha, phi) phi + upwind(alpha, G) G, G = phirPore * upwind(alpha2*eps, -phirPore);
     eps (a_new - a)/dt + div = 0, explicit (MULES limiter replaced by a clip to [0, 1], counted).
  3. kr (Brooks-Corey n 3), pc (Van Genuchten m 0.5, Se clipped to [1e-4, 1 - 1e-4]), PcCoeff from the new alpha.
  4. Pressure in the Darcy limit: rAUf = Mf (the momentum equation reduced to drag), phi = Mf(-snGrad p + PcCoeff_f
     snGrad alpha)|Sf| + Mf rho_f g.Sf, div phi = 0 (direct solve). The real solver has rAU = 1/(rho/(eps dt) + Drag):
     at dt 1e-7 inertia dominates the drag, so this model is NOT the real total flux; it isolates the transport part.
BCs: inlet p = 0 - a_b pc(a_b), a_b 0.99 when inflow; outlet p = -a pc(a), a zeroGradient; sides symmetry.
Not copied: correctUBc (outlet flux from the cell air velocity), MULES limiting, the iterative p solve (GAMG relTol
0.1; here the transverse seed is a random 1e-10 on the initial alpha, `seed` = 0 for none).
Prints per step-interval the transverse spread (max over rows of max - min alpha, as the transverseSpread function
object) and the row means near the front.
"""
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

mode = sys.argv[1]
r = int(sys.argv[2]) if len(sys.argv) > 2 else 1
dt = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-7
tEnd = float(sys.argv[4]) if len(sys.argv) > 4 else 3.5e-5
seed = float(sys.argv[5]) if len(sys.argv) > 5 else 1e-10
fluxMode = sys.argv[6] if len(sys.argv) > 6 else "darcy"  # darcy | mom | mom0 (no ddtCorr) | steady (no inertia), + "+V" "+C"
fluxBase, fluxExtras = fluxMode.split("+")[0], set(fluxMode.split("+")[1:])  # V: viscous laplacian, C: upwind convection, T: dev2(T(grad U)), L: linearUpwind correction

import os
nx, ny, nz = int(os.environ.get("NX", 5)) * r, 172 * r, int(os.environ.get("NZ", 3)) * r  # NX=1 NZ=1: 1D column
L = np.array([0.55e-3, 3.446e-3, 0.237e-3])
n = np.array([nx, ny, nz])
h = L / n
V = h.prod()
A = np.array([h[1] * h[2], h[0] * h[2], h[0] * h[1]])  # face area normal to x, y, z
K, eps, mu1, mu2, rho1, rho2, g = 1e-11, 0.5, 1e-3, 1.76e-5, 1000.0, 1.0, -9.81  # g along y
pc0, m, nvg, nBC, Smax = 5000.0, 0.5, 2.0, 3.0, 0.999
aIn = 0.99
N = nx * ny * nz
idx = np.arange(N).reshape(nz, ny, nx)  # [k, j, i] -> cell = i + nx*(j + ny*k)


def props(a):
    """kr1, kr2, pc, dpcdS, PcCoeff, M1, M2 for an array of alpha (pcVanGenuchten.H, krBrooksAndCorey.H)."""
    Se = np.clip(a / Smax, 1e-4, 1 - 1e-4)
    kr1, kr2 = Se ** nBC, (1 - Se) ** nBC
    pc = pc0 * (Se ** (-1 / m) - 1) ** (1 / nvg)
    dpc = -(1 / (nvg * m)) * (pc0 / Smax) * (Se ** (-1 / m) - 1) ** (1 / nvg - 1) * Se ** (-(1 + m) / m)
    M1, M2 = K * kr1 / mu1, K * kr2 / mu2
    PcC = -pc + (M1 * (1 - a) - M2 * a) / (M1 + M2) * dpc
    return kr1, kr2, pc, dpc, PcC, M1, M2


# internal faces per direction: owner / neighbour cell arrays
faces = []
for d, sl in enumerate([(slice(None), slice(None), slice(0, -1)), (slice(None), slice(0, -1), slice(None)),
                        (slice(0, -1), slice(None), slice(None))]):
    o = idx[sl].ravel()
    nb = o + [1, nx, nx * ny][d]
    faces.append((d, o, nb))
inl = idx[:, 0, :].ravel()      # inlet cells (face normal -y)
out = idx[:, -1, :].ravel()     # outlet cells (+y)
sym = [(0, idx[:, :, 0].ravel(), -1), (0, idx[:, :, -1].ravel(), 1),
       (2, idx[0, :, :].ravel(), -1), (2, idx[-1, :, :].ravel(), 1)]


def boundary_alpha(a, phi_in):
    """inlet alpha: 0.99 where the flux enters (inletOutlet), cell value otherwise; outlet zeroGradient."""
    ab_in = np.where(phi_in < 0, aIn, a[inl])  # phi_in = outward flux at the inlet
    return ab_in, a[out].copy()


def grad(f, fin, fout):
    """Gauss linear cell gradient, boundary values fin (inlet), fout (outlet), symmetry = cell value."""
    G = np.zeros((N, 3))
    for d, o, nb in faces:
        ff = 0.5 * (f[o] + f[nb]) * A[d]
        np.add.at(G[:, d], o, ff)
        np.add.at(G[:, d], nb, -ff)
    np.add.at(G[:, 1], inl, -fin * A[1])
    np.add.at(G[:, 1], out, fout * A[1])
    for d, c, s in sym:
        np.add.at(G[:, d], c, s * f[c] * A[d])
    return G / V


def solve_p(a, ab_in, ab_out, coefI=None, coefB=None, extraI=None, extraB=None):
    """Pressure equation div(phi) = 0 with phi = coef*(-snGrad p + PcCoeff_f snGrad alpha)|Sf| + coef rho_f g.Sf + extra.
    Darcy limit: coef = Mf, extra = 0. Momentum path (pEqn.H): coef = rAUf, extra = phiHbyA (+ ddtCorr).
    Returns p, internal face fluxes (per direction, +e_d), inlet/outlet outward fluxes."""
    _, _, _, _, PcC, M1, M2 = props(a)
    Mc = M1 + M2
    rho = a * rho1 + (1 - a) * rho2
    _, _, pcI, _, PcI, M1I, M2I = props(ab_in)
    _, _, pcO, _, PcO, M1O, M2O = props(ab_out)
    if coefI is None:
        coefI = [0.5 * (Mc[o] + Mc[nb]) for d, o, nb in faces]
        coefB = [M1I + M2I, M1O + M2O]
    if extraI is None:
        extraI = [0.0] * 3
        extraB = [0.0, 0.0]
    rows, cols, vals = [], [], []
    rhs = np.zeros(N)
    flux_parts = []
    for (d, o, nb), cf, ex in zip(faces, coefI, extraI):
        T = cf * A[d] / h[d]
        src = cf * A[d] * 0.5 * (PcC[o] + PcC[nb]) * (a[nb] - a[o]) / h[d] + ex
        if d == 1:
            src = src + cf * 0.5 * (rho[o] + rho[nb]) * g * A[d]
        # phi = -T (p_nb - p_o) + src ; div: owner +phi, neighbour -phi
        rows += [o, o, nb, nb]; cols += [o, nb, nb, o]; vals += [T, -T, T, -T]
        np.add.at(rhs, o, -src); np.add.at(rhs, nb, src)
        flux_parts.append((T, src))
    pin, pout = -ab_in * pcI, -ab_out * pcO
    bnd = []
    for c, ab, pb, cf, Pb, sgn, ex in [(inl, ab_in, pin, coefB[0], PcI, -1, extraB[0]),
                                       (out, ab_out, pout, coefB[1], PcO, 1, extraB[1])]:
        T = cf * A[1] / (h[1] / 2)
        rhob = ab * rho1 + (1 - ab) * rho2
        src = cf * A[1] * Pb * (ab - a[c]) / (h[1] / 2) + cf * rhob * g * sgn * A[1] + ex
        # outward phi = -T (pb - pc) + src
        rows.append(c); cols.append(c); vals.append(T)
        np.add.at(rhs, c, T * pb - src)
        bnd.append((T, pb, src))
    M = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))
    p = spla.spsolve(M.tocsc(), rhs)
    phis = [-T * (p[nb] - p[o]) + src for (T, src), (d, o, nb) in zip(flux_parts, faces)]
    phib = [-T * (pb - p[c]) + src for (T, pb, src), c in zip(bnd, [inl, out])]
    return p, phis, phib


def momentum_step(a_new, a_old, ab_in, ab_out, U, phis_old, rhoPhiI=None, rhoPhiB=None, Ucur=None):
    """pEqn.H of be54696 with momentumPredictor off, UEqn = (1/eps) ddt(rho, U) + Drag U (convection and viscous
    terms only with "+V" / "+C" in the flux mode). Returns p, phis, phib, U."""
    Mc = sum(props(a_new)[5:7])
    MbI, MbO = sum(props(ab_in)[5:7]), sum(props(ab_out)[5:7])
    rho_n, rho_o = a_new * rho1 + (1 - a_new) * rho2, a_old * rho1 + (1 - a_old) * rho2
    # Drag = fvc::average(1/Mf): area-weighted mean over the 6 faces (symmetry faces: cell value)
    num, den = np.zeros(N), np.zeros(N)
    for d, o, nb in faces:
        df = 1.0 / (0.5 * (Mc[o] + Mc[nb]))
        np.add.at(num, o, df * A[d]); np.add.at(num, nb, df * A[d])
        np.add.at(den, o, A[d]); np.add.at(den, nb, A[d])
    for c, Mb in [(inl, MbI), (out, MbO)]:
        np.add.at(num, c, A[1] / Mb); np.add.at(den, c, A[1])
    for d, c, _ in sym:
        np.add.at(num, c, A[d] / Mc[c]); np.add.at(den, c, A[d])
    Drag = num / den
    # UEqn = (1/eps)(ddt(rho,U) + div(rhoPhiByEps,U) + divDevTau) + Drag U, per unit volume: aP U_P - sum aN U_N = b
    Uc = U if Ucur is None else Ucur  # current U for the off-diagonal terms; U = old time
    aP = Drag.copy()
    Hs = np.zeros((N, 3))
    if fluxBase != "steady":  # Euler ddt(rho,U)
        aP += rho_n / (eps * dt)
        Hs += rho_o[:, None] * U / (eps * dt)
    if "V" in fluxExtras:  # -(1/eps) laplacian(mu_f, U), compact; symmetry: normal component 0 at the wall
        mu = a_new * mu1 + (1 - a_new) * mu2
        for d, o, nb in faces:
            c = 0.5 * (mu[o] + mu[nb]) * A[d] / h[d] / (eps * V)
            np.add.at(aP, o, c); np.add.at(aP, nb, c)
            np.add.at(Hs, o, c[:, None] * Uc[nb]); np.add.at(Hs, nb, c[:, None] * Uc[o])
        for d, cc, _ in sym:  # only the wall-normal component sees U_b = 0: kept as an explicit source
            np.add.at(Hs[:, d], cc, -mu[cc] * A[d] / (h[d] / 2) / (eps * V) * Uc[cc, d])
    if "C" in fluxExtras:  # (1/eps) div(rhoPhiByEps, U), upwind (linearUpwind correction left out)
        for (d, o, nb), F in zip(faces, rhoPhiI):
            F = F / eps / eps / V  # rhoPhiByEps = rhoPhi/eps_f, times 1/eps of UEqn
            out_o, in_o = np.maximum(F, 0), np.maximum(-F, 0)
            np.add.at(aP, o, out_o); np.add.at(aP, nb, in_o)
            np.add.at(Hs, o, in_o[:, None] * Uc[nb]); np.add.at(Hs, nb, out_o[:, None] * Uc[o])
        for c, F in zip([inl, out], rhoPhiB):  # outflow: face value = cell value; inflow: value set by the BC, not on the diagonal
            np.add.at(aP, c, np.maximum(F, 0) / eps / eps / V)
    if "T" in fluxExtras or "L" in fluxExtras:
        # cell gradient tensor GU[c, i, j] = d U_j / d x_i (Gauss linear); boundaries: zeroGradient, symmetry mirror
        GU = np.zeros((N, 3, 3))
        for j in range(3):
            Uj = Uc[:, j]
            Gj = grad(Uj, Uj[inl], Uj[out])
            for d, c, sgn in sym:  # the wall-normal component is 0 on the symmetry face, not the cell value
                if j == d:
                    np.add.at(Gj[:, d], c, -sgn * Uj[c] * A[d] / V)
            GU[:, :, j] = Gj
    if "T" in fluxExtras:  # + (1/eps) fvc::div(mu_f dev2(T(grad U))_f . Sf), internal faces
        mu = a_new * mu1 + (1 - a_new) * mu2
        for d, o, nb in faces:
            Gf = 0.5 * (GU[o] + GU[nb])
            tr = np.trace(Gf, axis1=1, axis2=2)
            # dev2(T(G)) . Sf, Sf = A e_d, G_ij = d_i U_j: (T(G) . e_d)_k = G_dk
            vec = Gf[:, d, :].copy()
            vec[:, d] -= 2.0 / 3.0 * tr
            fl = 0.5 * (mu[o] + mu[nb])[:, None] * vec * A[d] / (eps * V)
            np.add.at(Hs, o, fl); np.add.at(Hs, nb, -fl)
    if "L" in fluxExtras and "C" in fluxExtras:  # linearUpwind explicit correction: - (1/eps) div(F (x_f - x_up) . grad(U)_up)
        for (d, o, nb), F in zip(faces, rhoPhiI):
            F = F / eps / eps / V
            up = np.where(F > 0, o, nb)
            dx = np.where(F > 0, 0.5, -0.5) * h[d]  # x_f - x_up along d
            corr = F[:, None] * dx[:, None] * GU[up, d, :]
            np.add.at(Hs, o, -corr); np.add.at(Hs, nb, corr)
    rAU = 1.0 / aP
    HbyA = rAU[:, None] * Hs
    rAUf = [0.5 * (rAU[o] + rAU[nb]) for d, o, nb in faces]
    rAUb = [rAU[inl], rAU[out]]
    extraI = []
    for (d, o, nb), ph_old in zip(faces, phis_old):
        e = 0.5 * (HbyA[o, d] + HbyA[nb, d]) * A[d]
        if fluxBase == "mom":  # fvc::ddtCorr(U, phi), Euler, flux-normalised coupling coefficient (OF9)
            corr = ph_old - 0.5 * (U[o, d] + U[nb, d]) * A[d]
            cc = 1 - np.minimum(np.abs(corr) / (np.abs(ph_old) + 1e-300), 1)
            e = e + 0.5 * (rho_n[o] * rAU[o] + rho_n[nb] * rAU[nb]) * cc * corr / dt
        extraI.append(e)
    extraB = [-HbyA[inl, 1] * A[1], HbyA[out, 1] * A[1]]  # boundary HbyA = cell value; ddtCorr 0 on patches
    p, phis, phib = solve_p(a_new, ab_in, ab_out, rAUf, rAUb, extraI, extraB)
    # U = HbyA + rAU reconstruct((phiG + phiPc - pEqn.flux)/rAUf) = HbyA + rAU reconstruct((phi - extra)/rAUf)
    rec = np.zeros((N, 3))
    for (d, o, nb), ph, ex, cf in zip(faces, phis, extraI, rAUf):
        psi = (ph - ex) / cf / (2 * A[d])
        np.add.at(rec[:, d], o, psi); np.add.at(rec[:, d], nb, psi)
    np.add.at(rec[:, 1], inl, -(phib[0] - extraB[0]) / rAUb[0] / (2 * A[1]))
    np.add.at(rec[:, 1], out, (phib[1] - extraB[1]) / rAUb[1] / (2 * A[1]))
    U = HbyA + rAU[:, None] * rec
    return p, phis, phib, U


def phir(a, p, ab_in, ab_out):
    """phirPore on internal faces (list per direction) and the outlet; inlet 0."""
    kr1, kr2, pc, dpc, PcC, M1, M2 = props(a)
    _, _, pcI, _, _, _, _ = props(ab_in)
    _, _, pcO, _, _, _, M2O = props(ab_out)
    pin, pout = -ab_in * pcI, -ab_out * pcO
    gp, gpc, ga = grad(p, pin, pout), grad(pc, pcI, pcO), grad(a, ab_in, ab_out)
    gv = np.array([0, g, 0])
    Uw = M1[:, None] * (-gp + (1 - a)[:, None] * gpc - pc[:, None] * ga + rho1 * gv)
    Un = M2[:, None] * (-gp - a[:, None] * gpc - pc[:, None] * ga + rho2 * gv)
    out_phir = -(Un[out, 1] * A[1]) / (eps * (1 - ab_out) + 0.001)
    if mode == "orig":
        Ur = (Uw / np.maximum(a, 1e-3)[:, None] - Un / np.maximum(1 - a, 1e-3)[:, None]) / eps
        return [0.5 * (Ur[o, d] + Ur[nb, d]) * A[d] for d, o, nb in faces], out_phir
    if mode == "wideFaceAlpha":  # diagnostic: wide (cell-gradient) phase velocities, divided by the face alpha as in A
        res = []
        for d, o, nb in faces:
            af = 0.5 * (a[o] + a[nb])
            uw, un = 0.5 * (Uw[o, d] + Uw[nb, d]) * A[d], 0.5 * (Un[o, d] + Un[nb, d]) * A[d]
            res.append((uw / np.maximum(af, 1e-3) - un / np.maximum(1 - af, 1e-3)) / eps)
        return res, out_phir
    res = []
    for d, o, nb in faces:
        af = 0.5 * (a[o] + a[nb]); pcf = 0.5 * (pc[o] + pc[nb])
        sg = lambda f: (f[nb] - f[o]) / h[d]
        gd = g if d == 1 else 0.0
        pw = 0.5 * (M1[o] + M1[nb]) * ((-sg(p) + (1 - af) * sg(pc) - pcf * sg(a)) * A[d] + rho1 * gd * A[d])
        pn = 0.5 * (M2[o] + M2[nb]) * ((-sg(p) - af * sg(pc) - pcf * sg(a)) * A[d] + rho2 * gd * A[d])
        res.append((pw / np.maximum(af, 1e-3) - pn / np.maximum(1 - af, 1e-3)) / eps)
    return res, out_phir


def spread(a):
    b = a.reshape(nz, ny, nx)
    s = (b.max(axis=(0, 2)) - b.min(axis=(0, 2)))
    return s.max(), int(s.argmax())


# initial state (setFieldsDict: 0.2 mm ramp in 20 um boxes, dry 0.002), p uniform -4995, phi = 0
yc = (np.arange(ny) + 0.5) * h[1]
box = np.floor(yc / 20e-6).astype(int)
ramp = np.where(box < 10, 0.99 - 0.988 * (box + 0.5) / 10, 0.002)
a = np.broadcast_to(ramp[None, :, None], (nz, ny, nx)).ravel().copy()
a = np.round(a, 4)  # setFieldsDict values have 4 decimals
rng = np.random.default_rng(1)
noise = seed * rng.standard_normal(N)
if os.environ.get("SEEDRAMP"):  # seed only in the initial ramp (rows below 0.2 mm), as the solver's spread sits at the front
    noise *= np.broadcast_to((yc < 0.2e-3)[None, :, None], (nz, ny, nx)).ravel()
a += noise
p = np.full(N, -4995.0)
phis = [np.zeros(len(o)) for _, o, _ in faces]
phib = [np.zeros(len(inl)), np.zeros(len(out))]
U = np.zeros((N, 3))

nSteps = int(round(tEnd / dt))
clipped = 0
first = {"spread>1e-6": None, "nonMonotone": None, "clip": None}
every = max(1, nSteps // 25)
print(f"{mode} / {fluxMode}: {nx} x {ny} x {nz}, dt {dt}, seed {seed}")
for step in range(1, nSteps + 1):
    ab_in, ab_out = boundary_alpha(a, phib[0])
    pr, pr_out = phir(a, p, ab_in, ab_out)
    a2e = (1 - a) * eps
    div = np.zeros(N)
    rhoPhiI = []
    for (d, o, nb), ph, rr in zip(faces, phis, pr):
        G = rr * np.where(-rr > 0, a2e[o], a2e[nb])
        F = ph * np.where(ph > 0, a[o], a[nb]) + G * np.where(G > 0, a[o], a[nb])
        np.add.at(div, o, F); np.add.at(div, nb, -F)
        rhoPhiI.append(F * (rho1 - rho2) + ph * rho2)
    # inlet: phirPore 0; outlet: G with boundary alpha2*eps = cell value (zeroGradient)
    Fin = phib[0] * np.where(phib[0] > 0, a[inl], ab_in)
    np.add.at(div, inl, Fin)
    Gout = pr_out * np.where(-pr_out > 0, a2e[out], (1 - ab_out) * eps)
    Fout = phib[1] * np.where(phib[1] > 0, a[out], ab_out) + Gout * np.where(Gout > 0, a[out], ab_out)
    np.add.at(div, out, Fout)
    rhoPhiB = [Fin * (rho1 - rho2) + phib[0] * rho2, Fout * (rho1 - rho2) + phib[1] * rho2]
    a_old = a
    a = a - dt / (eps * V) * div
    clipped += int(((a < 0) | (a > 1)).sum())
    a = np.clip(a, 0, 1)
    ab_in, ab_out = boundary_alpha(a, phib[0])
    if fluxBase == "darcy":
        p, phis, phib = solve_p(a, ab_in, ab_out)
    else:
        Ucur, phis_old = U, phis
        for corr in range(int(os.environ.get("NCORR", 1))):  # PIMPLE nCorrectors: H rebuilt from the corrected U
            p, phis, phib, Ucur = momentum_step(a, a_old, ab_in, ab_out, U, phis_old, rhoPhiI, rhoPhiB, Ucur)
        U = Ucur
    s, row = spread(a)
    rm = a.reshape(nz, ny, nx).mean(axis=(0, 2))
    for key, cond in [("spread>1e-6", s > 1e-6), ("nonMonotone", bool((np.diff(rm) > 1e-6).any())), ("clip", clipped > 0)]:
        if cond and first[key] is None:
            first[key] = step
    if not np.isfinite(s) or s > 1:
        print(f"step {step} t {step*dt:.3g}: spread {s:.3g} row {row} -> stop")
        break
    if step <= 5 or step % every == 0 or step in (2, 20, 100, 200) or (os.environ.get("TRACE") and step % int(os.environ["TRACE"]) == 0):
        rm = a.reshape(nz, ny, nx).mean(axis=(0, 2))
        print(f"step {step:4d} t {step*dt:.2e} spread {s:.2e} row {row:3d} clipped {clipped:4d} maxU {np.abs(U).max():.2e} maxUt {np.abs(U[:, [0, 2]]).max():.2e} | rows 0-{12*r}:",
              " ".join(f"{v:.3f}" for v in rm[:12 * r + 1]))
rm = a.reshape(nz, ny, nx).mean(axis=(0, 2))
front = (np.argmax(rm < 0.1) + 0.5) * h[1] * 1e3
print("SUMMARY", mode, fluxMode, f"t {step*dt:.2e}: mean alpha {a.mean():.5f}, front (row mean < 0.1) {front:.3f} mm, spread {spread(a)[0]:.2e};", f"dt {dt}", f"{nx}x{ny}x{nz}", "first step with:",
      ", ".join(f"{k} {v if v is None else f'{v} ({v*dt:.2e} s)'}" for k, v in first.items()), f"| steps run {step}")
