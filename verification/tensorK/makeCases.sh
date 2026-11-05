#!/bin/bash
# Builds the run folders of the tensor K checks (README.md) from their sources, each with its own `run` script.
# The run folders are not tracked (.gitignore): rebuild them with this script, run them with ./runAll.sh.
#   ./makeCases.sh            all run folders
#   ./makeCases.sh C2_S1_tensor ...   only these
# Sources (inputs only: 0/, constant/ with the mesh, system/, caseSetup):
#   ../wicking1D/ABC                          1D column, stored results to 0.03 s (b995db5)
#   ../../meshing_strat_trial/2D_bench        2D bench, 0/ and mesh from its ./Allpre
#   ../study2d_gapRise/S1_K1e-12_t40          cut REV (K 1e-12, VG 5000/0.5, theta 40, L), from study 2d's makeCases.sh
# Binaries: hybridPorousInterFoam (installed, 8a97d02) and hybridPorousInterFoam_T (solver/T_steps0-5.patch).
set -e
cd "${0%/*}"
R=$(cd ../.. && pwd)
A=$R/verification/wicking1D/ABC
B=$R/meshing_strat_trial/2D_bench
S=$R/verification/study2d_gapRise/S1_K1e-12_t40
PY=$R/.venv/bin/python

for src in "$A" "$B" "$S"; do
    [ -f "$src/constant/polyMesh/owner" ] || [ "$src" = "$A" ] || { echo "no mesh in $src: build it first"; exit 1; }
    [ -f "$src/0/K" ] || { echo "no 0/K in $src: build it first"; exit 1; }
done

copyCase() { # src dst
    rm -rf "$2"; mkdir -p "$2"
    cp -r "$1/0" "$1/constant" "$1/system" "$2/"
    [ -f "$1/caseSetup" ] && cp "$1/caseSetup" "$2/"
    return 0
}
setControl() { # case endTime writeInterval writePrecision
    sed -i -e "s/^endTime .*/endTime         $2;/" -e "s/^writeInterval .*/writeInterval   $3;/" \
           -e "s/^writePrecision .*/writePrecision  $4;/" -e "/dsLocator/d" "$1/system/controlDict"
}
runHeader() { # case comment
    cat > "$1/run" <<EOF
#!/bin/bash
# verification/tensorK: $2
cd "\${0%/*}" || exit 1
. "\$WM_PROJECT_DIR/bin/tools/RunFunctions"
. ../../../meshing_strat_trial/tools/runTools.sh
EOF
    chmod +x "$1/run"
}
runSerial() { # case binary comment
    runHeader "$1" "$3"
    cat >> "$1/run" <<EOF
runTmpLog log.hybridPorousInterFoam $2
EOF
}
runParallel() { # case binary comment
    runHeader "$1" "$3"
    cat >> "$1/run" <<EOF
N=\$(foamDictionary -entry N -value caseSetup)
$2 -postProcess -time 0 > log.precompile 2>&1 || { echo "\$PWD: precompile failed"; exit 1; }
decomposePar -force > log.decomposePar 2>&1 || { echo "\$PWD: decomposePar failed"; exit 1; }
runTmpLog log.hybridPorousInterFoam mpirun -np "\$N" $2 -parallel
status=\$?
reconstructPar -newTimes > log.reconstructPar 2>&1
exit \$status
EOF
}

ALL="$*"
make() { [ -z "$ALL" ] || [[ " $ALL " == *" $1 "* ]]; }

# ---- check 1: scalar K, the change must not move anything
if make C1_1D_T; then
    copyCase "$A" C1_1D_T
    runHeader C1_1D_T "check 1, 1D column (inputs of ../wicking1D/ABC, 0.03 s, writes every 1 ms, 6 digits), hybridPorousInterFoam_T"
    cat >> C1_1D_T/run <<'EOF'
runApplication blockMesh
cp 0/alpha.wetting.orig 0/alpha.wetting
runApplication setFields
runTmpLog log.hybridPorousInterFoam hybridPorousInterFoam_T
EOF
fi
for v in inst T; do
    c=C1_bench_$v
    make $c || continue
    bin=$([ $v = inst ] && echo hybridPorousInterFoam || echo hybridPorousInterFoam_T)
    copyCase "$B" $c
    setControl $c 0.002 5e-4 17
    runSerial $c $bin "check 1, 2D bench 2 ms, scalar K, $bin"
done

# ---- check 2: tensor K = K0*I must give the scalar results
if make C2_bench_tensor; then
    copyCase "$B" C2_bench_tensor
    setControl C2_bench_tensor 0.002 5e-4 17
    "$PY" toTensorK.py C2_bench_tensor/0/K
    runSerial C2_bench_tensor hybridPorousInterFoam_T "check 2, 2D bench 2 ms, tensor K = K*I, hybridPorousInterFoam_T (compare with C1_bench_T)"
fi
for v in scalar tensor; do
    c=C2_S1_$v
    make $c || continue
    copyCase "$S" $c
    setControl $c 5e-4 2.5e-4 17
    [ $v = tensor ] && "$PY" toTensorK.py $c/0/K
    runParallel $c hybridPorousInterFoam_T "check 2, cut REV (study 2d S1) 0.5 ms on 4 cores, $v K, hybridPorousInterFoam_T"
done

# ---- check 3: 1D column along x, y, z, K along the column 2.5e-12, across 1e-11 (README.md)
KA=2.5e-12; KT=1e-11
for c in C3_y_scalar C3_y_tensor C3_x_tensor C3_z_tensor; do
    make $c || continue
    copyCase "$A" $c
    rm -rf $c/constant/polyMesh                      # rebuilt by blockMesh in the run
    setControl $c 0.12 0.004 17
    "$PY" useToolsCoats.py $c/system/controlDict
    case $c in
        C3_y_scalar) K="$KA";                     g="(0 -9.81 0)"; rot="" ;;
        C3_y_tensor) K="($KT 0 0 0 $KA 0 0 0 $KT)"; g="(0 -9.81 0)"; rot="" ;;
        C3_x_tensor) K="($KA 0 0 0 $KT 0 0 0 $KT)"; g="(-9.81 0 0)"; rot="rotate=((0 1 0) (1 0 0))" ;;
        C3_z_tensor) K="($KT 0 0 0 $KT 0 0 0 $KA)"; g="(0 0 -9.81)"; rot="rotate=((0 1 0) (0 0 1))" ;;
    esac
    sed -i "s/^internalField .*/internalField   uniform $K;/" $c/0/K
    [[ $c == *tensor ]] && sed -i "s/^\(\s*class\s*\)volScalarField;/\1volTensorField;/" $c/0/K
    sed -i "s/^value .*/value           $g;/" $c/constant/g
    runHeader $c "check 3, 1D column (inputs of ../wicking1D/ABC) along ${c:3:1}, K $K, g $g, 0.12 s, hybridPorousInterFoam_T"
    cat >> $c/run <<EOF
runApplication blockMesh
cp 0/alpha.wetting.orig 0/alpha.wetting
runApplication setFields
EOF
    [ -n "$rot" ] && echo "transformPoints \"$rot\" > log.transformPoints 2>&1 || exit 1" >> $c/run
    echo "runTmpLog log.hybridPorousInterFoam hybridPorousInterFoam_T" >> $c/run
done

# ---- check 5: saturated column, two layers in series (K_y 1e-11 in cells 0-85, 2.5e-12 in 86-171), p fixed at both ends
for c in C5_scalar C5_tensor; do
    make $c || continue
    copyCase "$A" $c
    rm -rf $c/constant/polyMesh
    setControl $c 1e-3 1e-3 17
    "$PY" useToolsCoats.py $c/system/controlDict
    "$PY" layerK.py $c/0/K ${c#C5_} 86 1e-11 2.5e-12
    # saturated: alpha 1 everywhere and on the inflow
    sed -e "s/^internalField .*/internalField   uniform 1;/" -e "s/uniform 0.99;/uniform 1;/" \
        $c/0/alpha.wetting.orig > $c/0/alpha.wetting
    # pressure fixed at both ends (replaces the coded inlet/outlet BCs)
    cat > $c/0/p <<'EOF'
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      p;
}
// tensorK check 5: saturated column, pressure-driven; p fixed at both ends
dimensions      [1 -1 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 1000;
    }
    outlet
    {
        type            fixedValue;
        value           uniform 0;
    }
    frontAndBack
    {
        type            empty;
    }
}
EOF
    # outlet open to water: Uwetting fixed (0 0 0) there would make correctUBc.H close it
    sed -i '/^    outlet/,/}/{s/type .*fixedValue;/type            zeroGradient;/;/value/d}' $c/0/Uwetting
    sed -i "s/^activateCapillarity .*/activateCapillarity     0;/" $c/constant/transportProperties
    sed -i '/^    p$/,/}/s/tolerance .*/tolerance       1e-12;/' $c/system/fvSolution
    runHeader $c "check 5, saturated 1D column, K_y 1e-11 | 2.5e-12 in series (${c#C5_} K), p 1000 / 0 Pa, hybridPorousInterFoam_T"
    cat >> $c/run <<'EOF'
runApplication blockMesh
runTmpLog log.hybridPorousInterFoam hybridPorousInterFoam_T
EOF
done

# ---- check 6: 2D bench with anisotropic walls (diag(1e-11, 2.2e-12, 2.2e-12)), serial and split on the lower wall surface
P=$R/verification/parallel_H
for c in C6_scalar_serial C6_scalar_split C6_aniso_serial C6_aniso_split C6_scalar_mid C6_aniso_mid; do
    make $c || continue
    copyCase "$B" $c
    setControl $c 0.002 5e-05 17
    cp "$B/check.py" $c/                                             # its imports: ../tools, ../slit_test
    [[ $c == C6_aniso_* ]] && "$PY" toTensorK.py $c/0/K --porous 1e-11 2.2e-12 2.2e-12
    if [[ $c == *_split || $c == *_mid ]]; then
        # _split: processor boundary between z-cells 7 and 8 (lower wall surface); _mid: between 11 and 12 (mid-gap)
        kp=$([[ $c == *_split ]] && echo 8 || echo 12)
        cp "$P/decomposeParDict" $c/system/
        "$PY" "$P/makeDecomposition.py" $c $kp
        echo "N 2;" > $c/caseSetup
        runParallel $c hybridPorousInterFoam_T "check 6, 2D bench 2 ms, ${c#C6_}, 2 processors split below z-cell $kp, hybridPorousInterFoam_T"
    else
        runSerial $c hybridPorousInterFoam_T "check 6, 2D bench 2 ms, ${c#C6_}, hybridPorousInterFoam_T"
    fi
done

# ---- check 4: 2D anisotropic spreading, Kxx 2.5e-12, Kyy 1e-11, no gravity (README.md)
I=$R/trialWicking/1D_vertical_impes_inletRes
for c in C4_tensor C4_stretched C4_aniso_impes; do
    make $c || continue
    if [ $c = C4_aniso_impes ]; then
        copyCase "$I" $c
        rm -rf $c/constant/polyMesh $c/0/Sb.org
        "$PY" make2D.py $c impes 1 tensor 2.5e-12 1e-11 1e-11
        sed -i "s/^application .*/application     anisoImpesFoam;/" $c/system/controlDict
        # OpenFOAM has no harmonic interpolation for tensors; K is uniform here, so linear gives the same faces
        sed -i "s/^\(\s*K\s*\)harmonic;/\1linear;   \/\/ tensorK check 4: harmonic exists for scalars only/" $c/system/fvSchemes
        # the tensor Laplacian interpolates grad(p) for its cross term (zero here: diagonal K, axis faces); as its tutorials
        sed -i "/interpolationSchemes/,/}/s/^\(\s*default\s*\)none;/\1linear;   \/\/ tensorK check 4: as the anisoImpesFoam tutorials/" $c/system/fvSchemes
        bin=anisoImpesFoam
    else
        copyCase "$A" $c
        rm -rf $c/constant/polyMesh $c/0/alpha.wetting.orig
        "$PY" useToolsCoats.py $c/system/controlDict
        if [ $c = C4_tensor ]; then
            "$PY" make2D.py $c hybrid 1 tensor 2.5e-12 1e-11 1e-11
        else
            "$PY" make2D.py $c hybrid 2 scalar 1e-11
        fi
        bin=hybridPorousInterFoam_T
    fi
    setControl $c 0.01 5e-4 17
    sed -i "s/^value .*/value           (0 0 0);/" $c/constant/g
    runHeader $c "check 4, 2D spreading box, ${c#C4_}, no gravity, 10 ms, $bin"
    cat >> $c/run <<EOF
runApplication blockMesh
postProcess -func writeCellCentres -time 0 > log.writeCellCentres 2>&1
runTmpLog log.$bin $bin
EOF
done
ls -d C[0-9]*_*/
