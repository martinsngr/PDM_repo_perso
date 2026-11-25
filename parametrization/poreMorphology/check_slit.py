"""Check of PoreSpy's capillary pressure on a straight slit (2026-11-23).

A 2D image is read as the cross-section of parallel fibres: the meniscus is curved in the cross-section only,
pc = sigma*cos(theta)/r (Maier et al. 2025, eq. 12). A slit of width w fills with wetting liquid at r = w/2,
i.e. pc = 2*sigma*cos(theta)/w.
Result: spacing=np.inf gives that (0.999 x for even widths, 0.92-0.95 x for odd ones: edt overestimates the
radius by half a pixel); spacing=None (the 2D default) gives 2 x (sphere formula).
Run: ~/venvs/porespy/bin/python check_slit.py
"""
import numpy as np
import porespy as ps

ps.settings.tqdm['disable'] = True               # no progress bars
sigma, theta_w, h = 0.072, 70.0, 0.5e-6          # water on PET (guess), pixel size 0.5 um
for w in (10, 11, 20, 21, 40):                    # slit width in pixels
    im = np.zeros((w + 2, 200), dtype=bool)       # True = pore; rows 0 and w+1 solid, rows 1..w pore
    im[1:-1, :] = True
    dt = ps.tools.get_edt()(im)                    # distance to the nearest solid pixel (pixels)
    expect = 2 * sigma * np.cos(np.radians(theta_w)) / (w * h)
    out = [f"w {w:3d} px  dt max {dt[im].max():5.2f}  expected {expect:7.0f} Pa"]
    for spacing in (None, np.inf):
        # theta is measured through the non-wetting phase (air): 180 - theta_w
        pc = ps.filters.capillary_transform(im, dt=dt, sigma=sigma, theta=180 - theta_w,
                                            voxel_size=h, spacing=spacing)
        # explicit pressures down below min(pc): with steps=None the slit never fills
        steps = np.geomspace(5 * expect, expect / 5, 1200)    # 0.27 % per step
        res = ps.simulations.imbibition(im, pc=pc, dt=dt, steps=steps)   # no inlets: Maier's assumption
        p_full = res.im_pc[im].min()               # pressure at which the last pixel turns wet
        out.append(f"spacing={spacing}: full at {p_full:7.0f} Pa ({p_full / expect:.3f} x expected)")
    print("  ".join(out))
