"""1D Richards model of Maier et al. 2025 (Textile Res. J. 95, 937), written from their paper: predictions for the
OpenFOAM runs of this folder (README.md).

    ../../.venv/bin/python richards1D.py [case] [--dx 5e-4] [--k4] [--bath] [--scheme maier|ours] [--nograv] [--save out.npz]

phi dS/dt = -dq/dz,  q = -(K kr/mu) (dp_w/dz + rho g),  p_w = -pc(S)  (air at 0 Pa everywhere: no air equation),
Van Genuchten pc (their eq. 9, pc0 = 1/alpha, m = 1 - 1/n), Mualem kr (eq. 10), Gebart K along the fibres (eq. 11,
c = 57 as they state, fibre radius; --k4: 4x, i.e. the diameter in their formula). Column 0.15 m, S(0) = 0.99,
S(0.15 m) = 0.01, initial 0.01 (their Table 3); --bath: S(0) = 1 (water at 0 Pa, the N2c bath of the REV).
Se clipped to [1e-4, 1 - 1e-4] in pc and kr, as the solver library.

Two discretisations of the face flux, finite volumes on the same cells:
  maier: their diffusion form, q = -D_f dS/dz - (K rho g/mu) kr_f, D = (K kr/mu)|dpc/dS|, D_f and kr_f the mean of the
         two cells ("linear interpolation of the fluxes"); time integration: scipy solve_ivp LSODA, as they did;
  ours:  the solver's form, q = -(K kr_up/mu) (dp_w/dz + rho g), kr of the upstream cell (change C), integrated with
         BDF (implicit; the solver is explicit, so only the space discretisation is the solver's).
"""
import argparse
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import diags

CASES = {  # name: fibre diameter (m), porosity, mu (Pa s), rho (kg/m3), VG alpha (1/Pa), VG n, end time (s)
    "f48_PEG": (18.6e-6, 0.86, 0.0948, 1120.0, 0.00123, 4.41, 3000.0),
    "f128_PEG": (11.7e-6, 0.84, 0.0948, 1120.0, 0.000605, 4.48, 3000.0),
    "f256_PEG": (8.5e-6, 0.86, 0.0948, 1120.0, 0.000407, 4.32, 3000.0),
    "f256_EG": (8.5e-6, 0.86, 0.01661, 1140.0, 0.000385, 4.33, 600.0),
}
TIMES = {  # their profile times (Figs. 16-19)
    "f48_PEG": [50, 100, 300, 600, 3000], "f128_PEG": [50, 100, 300, 600, 3000],
    "f256_PEG": [50, 100, 300, 600, 3000], "f256_EG": [10, 20, 60, 120, 600],
}
G, L = 9.81, 0.15


def laws(m, n, pc0):
    def se(S):
        return np.clip(S, 1e-4, 1 - 1e-4)

    def pc(S):
        s = se(S)
        return pc0 * (s ** (-1 / m) - 1) ** (1 / n)

    def dpc(S):  # |dpc/dS|
        s = se(S)
        return pc0 * (1 / n) * (s ** (-1 / m) - 1) ** (1 / n - 1) * (1 / m) * s ** (-1 / m - 1)

    def kr(S):
        s = se(S)
        return s ** 0.5 * (1 - (1 - s ** (1 / m)) ** m) ** 2

    return pc, dpc, kr


def run(case, dx=5e-4, k4=False, bath=False, scheme="maier", grav=G):
    d, phi, mu, rho, a, n, tend = CASES[case]
    m, pc0 = 1 - 1 / n, 1 / a
    K = 8 * (d / 2) ** 2 / 57 * phi ** 3 / (1 - phi) ** 2 * (4 if k4 else 1)
    pc, dpc, kr = laws(m, n, pc0)
    N = int(round(L / dx))
    Sb, St = (1.0 if bath else 0.99), 0.01
    c = K / mu

    def fluxes(S):
        # cell values with the boundary values as ghost cells at half a cell (the faces z = 0 and z = L)
        Sx = np.concatenate(([Sb], S, [St]))
        h = np.full(N + 1, dx)
        h[0] = h[-1] = dx / 2
        if scheme == "maier":
            D = c * kr(Sx) * dpc(Sx)
            Df = 0.5 * (D[1:] + D[:-1])
            krf = 0.5 * (kr(Sx)[1:] + kr(Sx)[:-1])
            return -Df * (Sx[1:] - Sx[:-1]) / h - c * rho * grav * krf
        pw = -pc(Sx)
        drive = -((pw[1:] - pw[:-1]) / h + rho * grav)  # q = c*kr*drive, positive upwards
        k = kr(Sx)
        krf = np.where(drive > 0, k[:-1], k[1:])
        return c * krf * drive

    def rhs(t, S):
        q = fluxes(S)
        return -(q[1:] - q[:-1]) / (dx * phi)

    sparsity = diags([1, 1, 1], [-1, 0, 1], shape=(N, N))
    times = TIMES[case]
    sol = solve_ivp(rhs, (0, tend), np.full(N, 0.01), method="LSODA" if scheme == "maier" else "BDF",
                    t_eval=times, rtol=1e-6, atol=1e-8,
                    # tridiagonal Jacobian: LSODA takes the band widths, BDF the sparsity pattern (same results,
                    # far fewer function calls than a dense finite-difference Jacobian)
                    **({"lband": 1, "uband": 1} if scheme == "maier" else {"jac_sparsity": sparsity}))
    z = (np.arange(N) + 0.5) * dx
    return dict(case=case, z=z, t=sol.t, S=sol.y.T, phi=phi, K=K, status=sol.message)


def front(z, S, level=0.1):
    above = np.nonzero(S >= level)[0]
    if len(above) == 0:
        return 0.0
    i = above[-1]
    if i + 1 >= len(S):
        return z[-1]
    return z[i] + (S[i] - level) / (S[i] - S[i + 1]) * (z[i + 1] - z[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case", nargs="?", default="f128_PEG", choices=CASES)
    ap.add_argument("--dx", type=float, default=5e-4)
    ap.add_argument("--k4", action="store_true")
    ap.add_argument("--bath", action="store_true")
    ap.add_argument("--scheme", default="maier", choices=["maier", "ours"])
    ap.add_argument("--nograv", action="store_true", help="g = 0")
    ap.add_argument("--save")
    a = ap.parse_args()
    r = run(a.case, a.dx, a.k4, a.bath, a.scheme, 0.0 if a.nograv else G)
    print(f"{a.case} dx {a.dx * 1e3:g} mm, K {r['K']:.3e}{' (4x)' if a.k4 else ''}, inlet S "
          f"{'1 (bath)' if a.bath else '0.99'}, scheme {a.scheme}{', g = 0' if a.nograv else ''}: {r['status']}")
    dz = r["z"][1] - r["z"][0]
    for t, S in zip(r["t"], r["S"]):
        upt = r["phi"] * np.sum(S - 0.01) * dz
        print(f"  t {t:6g} s: front (S 0.1) {front(r['z'], S) * 1e3:6.1f} mm, (S 0.5) {front(r['z'], S, 0.5) * 1e3:6.1f} mm, "
              f"uptake {upt * 1e3:6.2f} mm (liquid volume per cross-section), S first cell {S[0]:.3f}")
    if a.save:
        np.savez(a.save, **{k: v for k, v in r.items() if k not in ("case", "status")})


if __name__ == "__main__":
    main()
