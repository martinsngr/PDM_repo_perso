#!/bin/bash
# makeRun.sh <name> <r> <dt> [solver]
#
# Builds run folder <name>/ from case/ (the 5 x 172 x 3 bench of ../bench_ddtCorr, copied 2026-10-15) with every
# cell split r times in each direction (5r x 172r x 3r cells, same 0.55 x 3.446 x 0.237 mm column) and a fixed
# time step dt, then blockMesh + setFields. The initial ramp (setFieldsDict boxes of 20 um) is the same function
# on every mesh: a fine cell takes the value of the 20 um box its centre falls in.
# Run it with:  cd <name> && ./run
set -e
cd "$(dirname "$0")"
name=$1; r=$2; dt=$3; solver=${4:-hybridPorousInterFoam_be54696}
[ -n "$dt" ] || { echo "usage: $0 <name> <r> <dt> [solver]"; exit 1; }
[ ! -e "$name" ] || { echo "$name exists"; exit 1; }

nx=$((5*r)); ny=$((172*r)); nz=$((3*r))
cp -r case "$name"
cd "$name"
sed -i "s/hex (0 1 2 3 4 5 6 7) (5 172 3)/hex (0 1 2 3 4 5 6 7) ($nx $ny $nz)/" system/blockMeshDict
sed -i "s/const label nx = 5, ny = 172, nz = 3;/const label nx = $nx, ny = $ny, nz = $nz;/" system/controlDict
sed -i "s/^deltaT .*/deltaT          $dt;/" system/controlDict
sed -i "s/^application .*/application     $solver;/" system/controlDict
grep -q "($nx $ny $nz)" system/blockMeshDict
grep -q "nx = $nx, ny = $ny, nz = $nz;" system/controlDict

cp 0/alpha.wetting.orig 0/alpha.wetting
blockMesh > /tmp/blockMesh.$name.log 2>&1
setFields > /tmp/setFields.$name.log 2>&1

cat > run <<EOF
#!/bin/bash
# $name: r = $r ($nx x $ny x $nz cells), dt $dt, $solver
cd "\$(dirname "\$0")"
. ../../runTools.sh
runTmpLog log.$name $solver
EOF
chmod +x run
echo "$name: $nx x $ny x $nz = $((nx*ny*nz)) cells, dt $dt, $solver"
