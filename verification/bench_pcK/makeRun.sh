#!/bin/bash
# makeRun.sh <name> <pcDiv> <KDiv> <dtMul> [solver]
#
# Builds run folder <name>/ from case/ (the 5 x 172 x 3 all-porous bench of ../bench_ddtCorr, copied 2026-11-18)
# with Van Genuchten pc0 = 5000/pcDiv Pa, K = 1e-11/KDiv m2, fixed time step dt = 1e-7*dtMul s, end time
# 2e-4*dtMul s and write interval 5e-5*dtMul s (always 2,000 steps), then blockMesh + setFields.
# The uniform initial p (-alpha*pc at the dry state, only the first guess) is scaled with pc0; the patch values
# of p are computed from transportProperties at every step (codedFixedValue), nothing to change there.
# Everything else as case/ (gravity, fluids, eps, mesh, initial ramp, solver settings).
# Run it with:  cd <name> && ./run
set -e
cd "$(dirname "$0")"
name=$1; pcDiv=$2; KDiv=$3; dtMul=$4; solver=${5:-hybridPorousInterFoam_b0c0f67}
[ -n "$dtMul" ] || { echo "usage: $0 <name> <pcDiv> <KDiv> <dtMul> [solver]"; exit 1; }
[ ! -e "$name" ] || { echo "$name exists"; exit 1; }

num() { python3 -c "print('%.12g' % ($1))"; }
pc0=$(num "5000/$pcDiv"); p0=$(num "-4995/$pcDiv"); K=$(num "1e-11/$KDiv")
dt=$(num "1e-7*$dtMul"); tEnd=$(num "2e-4*$dtMul"); tWrite=$(num "5e-5*$dtMul")

cp -r case "$name"
cd "$name"
sed -i "s/^\(    pc0 pc0 \[1 -1 -2 0 0 0 0\]\) 5000;/\1 $pc0;/" constant/transportProperties
sed -i "s/^internalField   uniform -4995;/internalField   uniform $p0;/" 0/p
sed -i "s/^internalField   uniform 1e-11;/internalField   uniform $K;/" 0/K
sed -i "s/^application .*/application     $solver;/" system/controlDict
sed -i "s/^deltaT .*/deltaT          $dt;/" system/controlDict
sed -i "s/^endTime .*/endTime         $tEnd;/" system/controlDict
sed -i "s/^writeInterval .*/writeInterval   $tWrite;/" system/controlDict
# every edit must have landed (a silent sed miss would leave the base value)
grep -q "pc0 pc0 \[1 -1 -2 0 0 0 0\] $pc0;" constant/transportProperties
grep -q "^internalField   uniform $p0;" 0/p
grep -q "^internalField   uniform $K;" 0/K
grep -q "^application     $solver;" system/controlDict
grep -q "^deltaT          $dt;" system/controlDict
grep -q "^endTime         $tEnd;" system/controlDict
grep -q "^writeInterval   $tWrite;" system/controlDict

cp 0/alpha.wetting.orig 0/alpha.wetting
blockMesh > /dev/null
setFields > /dev/null

cat > run <<EOF
#!/bin/bash
# $name: pc0 $pc0 Pa, K $K m2, dt $dt s, end $tEnd s, $solver
cd "\$(dirname "\$0")"
. ../../runTools.sh
runTmpLog log.$name $solver
EOF
chmod +x run
echo "$name: pc0 $pc0 Pa, K $K m2, dt $dt s, end $tEnd s, $solver"
