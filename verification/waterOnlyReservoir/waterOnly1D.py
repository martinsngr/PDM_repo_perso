"""1D wicking column with the water-only reservoir (change J) against the similarity solution, with the reference
runs of ../wicking1D (same table as ../wicking1DVariants.py: front and uptake slopes vs sqrt(t) for t >= 0.01 s,
first-cell saturation, air fraction of the inlet flux and air pressure of the first cell at 25 ms).

    ../../.venv/bin/python waterOnly1D.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import analyseWicking1D as W      # noqa: E402
import wicking1DVariants as V     # noqa: E402

W.CASE = "/"                      # the run folders below are absolute paths
REF = os.path.join(os.path.dirname(HERE), "wicking1D")
V.RUNS = [
    (os.path.join(REF, "impes"), "Sb", "impesFoam (reference run)"),
    (os.path.join(REF, "ABC"), "alpha.wetting", "hybrid, current inlet (reference run)"),
    (os.path.join(HERE, "1D_regression"), "alpha.wetting", "J build, no keyword"),
    (os.path.join(HERE, "1D_waterOnly"), "alpha.wetting", "J, water-only inlet, water at -pc(0.99)"),
    (os.path.join(HERE, "1D_bath0"), "alpha.wetting", "J, water-only inlet, water at 0 Pa"),
]

if __name__ == "__main__":
    V.main()
