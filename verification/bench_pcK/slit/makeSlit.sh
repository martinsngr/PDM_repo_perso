#!/bin/bash
# makeSlit.sh <name> <pcMul> <KDiv> <solver> [orig]
#
# Builds run folder <name>/ from ../../../meshing_strat_trial/2D_bench (the thick-wall slit: porous wall 8 cells | free gap
# 8 cells | porous wall 8 cells, 100 x 1 x 24 cells of 20 um, 2 ms, Coats dt; copied as it is on 2026-11-18) with Van
# Genuchten pc0 = 5000*pcMul Pa and wall K = 1e-11/KDiv m2 (system/setFieldsDict), run by <solver>, then ./Allpre (mesh,
# eps, K, alpha.wetting). The includes of the shared function objects and of the coded p BC point to
# meshing_strat_trial/tools (unchanged). With "orig" the keywords of the modified solver (B, G, H wall-like, F', I) are
# commented out in constant/transportProperties: an old binary ignores them anyway, this records that they are off.
# activatePorousContactAngle 1 / theta0 60 stay (the original porous contact-angle model).
# Run it with:  cd <name> && ./run
set -e
cd "$(dirname "$0")"
name=$1; pcMul=$2; KDiv=$3; solver=$4; mode=$5
[ -n "$solver" ] || { echo "usage: $0 <name> <pcMul> <KDiv> <solver> [orig]"; exit 1; }
[ ! -e "$name" ] || { echo "$name exists"; exit 1; }
SRC=../../../meshing_strat_trial/2D_bench
TOOLS=../../../../../meshing_strat_trial/tools   # seen from <name>/system and <name>/0

num() { python3 -c "print('%.12g' % ($1))"; }
pc0=$(num "5000*$pcMul"); K=$(num "1e-11/$KDiv")

mkdir "$name"
cp -r $SRC/0.orig $SRC/system $SRC/Allpre $SRC/clean "$name"/
mkdir "$name"/constant
cp $SRC/constant/dynamicMeshDict $SRC/constant/g $SRC/constant/momentumTransport $SRC/constant/transportProperties \
   "$name"/constant/
cd "$name"
sed -i "s#\"\.\./\.\./tools/#\"$TOOLS/#" system/controlDict 0.orig/p
sed -i "s#\.\./tools/initFields\.py#../../../../meshing_strat_trial/tools/initFields.py#" Allpre
sed -i "s#PY=\${PY:-\.\./\.\./\.venv/bin/python}#PY=\${PY:-../../../../.venv/bin/python}#" Allpre
sed -i "s/^\(    pc0 pc0 \[1 -1 -2 0 0 0 0\]\) 5000;/\1 $pc0;/" constant/transportProperties
sed -i "s/volScalarFieldValue K 1e-11 )/volScalarFieldValue K $K )/" system/setFieldsDict
sed -i "s/^application .*/application     $solver;/" system/controlDict
if [ "$mode" = orig ]; then
    for k in darcyFaceMaxDa porousFreeDarcyFaces porousContactAngleWallLike porousFreeFluxForce porousFreeNoSlip; do
        sed -i "s#^\($k .*\)\$#// \1   (off: original solver, makeSlit.sh)#" constant/transportProperties
        ! grep -q "^$k " constant/transportProperties
    done
fi
# every edit must have landed
grep -q "\"$TOOLS/coatsTimeStep\"" system/controlDict
grep -q "\"$TOOLS/pOpenAir\"" 0.orig/p
grep -q "meshing_strat_trial/tools/initFields.py" Allpre
grep -q "PY=\${PY:-../../../../.venv/bin/python}" Allpre
grep -q "pc0 pc0 \[1 -1 -2 0 0 0 0\] $pc0;" constant/transportProperties
[ "$(grep -c "volScalarFieldValue K $K )" system/setFieldsDict)" = 2 ]
grep -q "^application     $solver;" system/controlDict

./Allpre > /dev/null

cat > run <<EOF
#!/bin/bash
# $name: pc0 $pc0 Pa, wall K $K m2, $solver ${mode:+(keywords of the modified solver off)}
cd "\$(dirname "\$0")"
. ../../../runTools.sh
./clean
runTmpLog log.$name $solver
EOF
chmod +x run
echo "$name: pc0 $pc0 Pa, wall K $K m2, $solver ${mode:+(orig)}"
