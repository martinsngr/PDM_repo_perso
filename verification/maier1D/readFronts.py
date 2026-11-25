"""Front positions (S 0.1 and S 0.5) read from the left panels of Maier et al.'s Figs. 16-19 by code, not by eye.

    ../../.venv/bin/python readFronts.py <folder with img50/54/55/59.jpeg> [<tile folder>]

The figures are raster JPEGs in the PDF (extracted with PyMuPDF; a copy in ~/PDM_results/maier1D_figures, not in the repo:
derived from the paper). Calibration from the detected frame of each left panel: x 0 / 150 mm at the left / right frame line,
S 0 at the bottom line, S 1.05 at the top line (= the tick marks within 0.4 px). Each pixel is assigned to the nearest of the
five series colours (one colour per profile time; the simulated and measured curves of a time share it). At each crossing the
pixels of that series in +-8 rows around the level row form connected components; per component the mean x of each row is
fitted by a line and taken at the level row (mm), with the fraction of the 17 rows it covers (a solid line covers all; dots
and dashes fewer). With a tile folder, 8x tiles of every crossing are written with the components lettered, to tell the
measured curve (solid line with markers) from the simulated one (dotted / dashed) by eye. That identification, and the cases
where both curves fall in one component (closer than a line width, ~0.7 mm), are recorded in fitFigures.py (FIG, EXP).
Precision: +-1 px = +-0.3 mm.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import richards1D as r1

# image, x of 0 mm, x of 150 mm, y of S 0, y of S 1.05 (frame lines, px)
CAL = {"f48_PEG": ("img50.jpeg", 62, 601.5, 424, 4), "f128_PEG": ("img54.jpeg", 62, 599, 421.5, 4),
       "f256_PEG": ("img55.jpeg", 62, 599, 421, 4), "f256_EG": ("img59.jpeg", 61, 602, 421.5, 3.5)}
PAL = np.array([(51, 24, 130), (58, 58, 204), (53, 145, 161), (89, 235, 130), (143, 252, 61)], float)  # times 1..5
BAND, Z = 8, 8


def components(cls, case, lev, i):
    _, x0, x150, y0, ytop = CAL[case]
    pxmm, pxs = (x150 - x0) / 150, (y0 - ytop) / 1.05
    y = int(round(y0 - lev * pxs))
    band = cls[y - BAND:y + BAND + 1, :] == i
    band[:, :int(x0) + 2] = False
    band[:, int(x150) - 1:] = False
    if y < 335:
        band[:, 406:] = False                                    # legend box
    lab, n = ndimage.label(band, structure=np.ones((3, 3)))
    out = []
    for c in range(1, n + 1):
        rr, xx = np.nonzero(lab == c)
        if len(rr) < 3:
            continue
        rows = np.unique(rr)
        xm = np.array([xx[rr == q].mean() for q in rows])
        xl = np.polyfit(rows - BAND, xm, 1)[1] if len(rows) >= 2 else xm[0]
        out.append(((xl - x0) / pxmm, len(rows) / (2 * BAND + 1), xl, y))
    return sorted(out)


def main():
    folder = sys.argv[1]
    tiles_out = sys.argv[2] if len(sys.argv) > 2 else None
    for case, (img, x0, x150, y0, ytop) in CAL.items():
        pil = Image.open(os.path.join(folder, img)).convert("RGB")
        im = np.asarray(pil).astype(float)
        dist = np.sqrt(((im[:, :, None, :] - PAL[None, None]) ** 2).sum(axis=3))
        cls = np.where(dist.min(axis=2) < 75, dist.argmin(axis=2), -1)
        pxmm = (x150 - x0) / 150
        print(f"== {case}: candidates at each crossing, mm (row coverage)")
        for lev in (0.1, 0.5):
            row = []
            for i, t in enumerate(r1.TIMES[case]):
                comps = components(cls, case, lev, i)
                print(f"  S {lev} t {t:4d} s: " + "  ".join(f"{'abcdefgh'[j]} {c[0]:6.2f} ({c[1]:.2f})"
                                                             for j, c in enumerate(comps)))
                if not tiles_out or not comps:
                    continue
                y = comps[0][3]
                lo, hi = min(c[0] for c in comps) - 2, max(c[0] for c in comps) + 2
                if hi - lo > 14:
                    mid = float(np.median([c[0] for c in comps]))
                    lo, hi = mid - 7, mid + 7
                xa, xb = int(x0 + lo * pxmm), int(x0 + hi * pxmm) + 1
                tile = pil.crop((xa, y - 30, xb, y + 31))
                tile = tile.resize((tile.width * Z, tile.height * Z), Image.NEAREST)
                d = ImageDraw.Draw(tile)
                d.line([(0, 30 * Z + Z // 2), (tile.width, 30 * Z + Z // 2)], fill=(255, 0, 0), width=1)
                txt = f"{case} {t}s S{lev}"
                for j, c in enumerate(comps):
                    X = (c[2] - xa) * Z + Z // 2
                    d.line([(X, 30 * Z - 40), (X, 30 * Z - 8)], fill=(255, 0, 0), width=2)
                    d.text((X - 3, 30 * Z - 54), "abcdefgh"[j], fill=(255, 0, 0))
                    txt += f"\n{'abcdefgh'[j]}: {c[0]:.2f} mm cov {c[1]:.2f}"
                d.multiline_text((3, 3), txt, fill=(0, 0, 0))
                row.append(tile)
            if row:
                out = Image.new("RGB", (sum(t.width + 6 for t in row), max(t.height for t in row)), (255, 255, 255))
                x = 0
                for t in row:
                    out.paste(t, (x, 0))
                    x += t.width + 6
                out.save(os.path.join(tiles_out, f"fronts_{case}_S{lev}.png"))


if __name__ == "__main__":
    main()
