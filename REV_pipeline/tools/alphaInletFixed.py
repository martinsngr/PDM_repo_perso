#!/usr/bin/env python3
"""alphaInletFixed.py [case]  -  the N2 bath of study 2g (../../verification/study2g_noJ/README.md): alpha fixedValue 1 on the
patch inlet of <case>/0/alpha.wetting (initFields.py writes inletOutlet there). Every flux through the bath faces is then
booked as water, as J does, but without J's face closure (J off: no waterOnlyPatches in constant/transportProperties).
Run it in Allpre after initFields.py. Same text as study 2g's makeCases.sh, so the fields match N2_full / N2c_full."""
import os
import re
import sys

p = os.path.join(sys.argv[1] if len(sys.argv) > 1 else ".", "0", "alpha.wetting")
s = open(p).read()
head, bf = s.split("boundaryField", 1)
new, n = re.subn(r"\n    inlet\n    \{\n.*?\n    \}\n",
                 "\n    inlet\n    {\n        type fixedValue;\n        value uniform 1;\n    }\n", bf, count=1, flags=re.S)
assert n == 1, f"{p}: no inlet entry"
open(p, "w").write(head + "boundaryField" + new)
print(f"{p}: inlet fixedValue 1")
