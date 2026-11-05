#!/usr/bin/env python3
"""Compare two runs of verification/tensorK: every file of every common write, and the time step of every step.

    python3 compare.py <runA> <runB> [--expect-differ K Uwetting UnonWetting Ur]

- Writes: the numeric time folders present in both runs (reconstructed ones for parallel runs), every file in
  them (uniform/ included), compared byte by byte. For a file that differs, the largest absolute and relative
  difference of its numbers is printed. Files listed after --expect-differ are reported but do not fail the check.
- Log: when both runs have log.hybridPorousInterFoam, the "Coats CFL Number" and "deltaT =" lines of every step
  are compared as text (the runs write 17 digits, so equal text = equal numbers).
Exit status 0 when everything not listed in --expect-differ is identical.
"""
import os
import re
import sys

NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def times(run):
    out = {}
    for d in os.listdir(run):
        try:
            t = float(d)
        except ValueError:
            continue
        if t > 0 and os.path.isdir(os.path.join(run, d)):
            out[t] = d
    return out


def files(root):
    for dp, _, fs in os.walk(root):
        for f in fs:
            yield os.path.relpath(os.path.join(dp, f), root)


def numbers(path):
    with open(path, errors="replace") as fh:
        txt = fh.read()
    body = txt.split("internalField", 1)[-1]          # skip the header (version, object name, ...)
    return [float(x) for x in NUM.findall(body)]


def numdiff(a, b):
    na, nb = numbers(a), numbers(b)
    if len(na) != len(nb):
        return f"different number of values ({len(na)} / {len(nb)}, e.g. scalar vs tensor)"
    dabs = max((abs(x - y) for x, y in zip(na, nb)), default=0.0)
    drel = max((abs(x - y) / max(abs(x), abs(y)) for x, y in zip(na, nb) if x != y), default=0.0)
    return f"max |diff| {dabs:.3g}, max relative diff {drel:.3g}"


def steplines(run):
    """Coats and deltaT lines grouped by the time step they appear in (key: the last "Time =" line before them).
    A log filtered by runTmpLog (LOG_EVERY) keeps whole steps, so its steps are compared where both logs have them."""
    p = os.path.join(run, "log.hybridPorousInterFoam")
    if not os.path.isfile(p):
        return None
    out, key = {}, "start"
    with open(p, errors="replace") as fh:
        for l in fh:
            if l.startswith("Time ="):
                key = l.strip()
            elif l.startswith("Coats CFL Number") or l.startswith("deltaT ="):
                out.setdefault(key, []).append(l.rstrip("\n"))
    return out


def main():
    a, b = sys.argv[1], sys.argv[2]
    expect = set(sys.argv[sys.argv.index("--expect-differ") + 1:]) if "--expect-differ" in sys.argv else set()
    ok = True
    ta, tb = times(a), times(b)
    common = sorted(set(ta) & set(tb))
    print(f"== {os.path.basename(a.rstrip('/'))} vs {os.path.basename(b.rstrip('/'))}: {len(common)} common writes "
          f"(only in A: {len(set(ta) - set(tb))}, only in B: {len(set(tb) - set(ta))})")
    if not common:
        print("   no common write: FAIL")
        ok = False
    nsame, differ = 0, {}
    for t in common:
        da, db = os.path.join(a, ta[t]), os.path.join(b, tb[t])
        fa, fb = set(files(da)), set(files(db))
        for f in sorted(fa ^ fb):
            print(f"   {ta[t]}/{f}: only in {'A' if f in fa else 'B'}")
        for f in sorted(fa & fb):
            pa, pb = os.path.join(da, f), os.path.join(db, f)
            with open(pa, "rb") as x, open(pb, "rb") as y:
                same = x.read() == y.read()
            if same:
                nsame += 1
            else:
                differ.setdefault(f, []).append((ta[t], numdiff(pa, pb)))
    print(f"   identical files: {nsame}")
    for f, lst in differ.items():
        name = os.path.basename(f)
        tag = "differs (expected)" if name in expect else "DIFFERS"
        if name not in expect:
            ok = False
        print(f"   {f} {tag} at {len(lst)} write(s); last {lst[-1][0]}: {lst[-1][1]}")
    la, lb = steplines(a), steplines(b)
    if la is not None and lb is not None:
        keys = [k for k in la if k in lb]                       # steps present in both logs, in log order
        bad = [k for k in keys if la[k] != lb[k]]
        nl = sum(len(la[k]) for k in keys)
        cover = f"{len(keys)} steps in both logs (A {len(la)}, B {len(lb)})"
        if not keys:
            ok = False
            print("   log: no common step: FAIL")
        elif not bad:
            print(f"   log: Coats and deltaT lines identical at all {cover}, {nl} lines")
        else:
            ok = False
            print(f"   log: Coats/deltaT lines DIFFER at {len(bad)} of {cover}; first: {bad[0]}")
            print(f"     A: {la[bad[0]]}\n     B: {lb[bad[0]]}")
    print(f"   {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
