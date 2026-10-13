#!/bin/bash
# interFoamSlit.sh - the S0 slit (real walls, gap 8 cells, 20 um, 2 mm, gravity -x) with stock OpenFOAM 9 interFoam,
# as in the previous student's work (interFoam, wall contact-angle BC, inlet alpha inletOutlet 1 / value 1).
# Reference for the hybridPorousInterFoam slit tests (../NOTES.md "Slit tests").
#
#   ./interFoamSlit.sh <name> <fill [m]> <static|total> [theta=60] [T=2e-3]
#
#   fill   : initial water column in the gap from the inlet (0 = empty gap, saturated inlet only)
#   static : inlet p_rgh as prghPressure p = 0 (static pressure 0, the usual interFoam setup)
#   total  : inlet prghTotalPressure p0 = 0 (reservoir at rest)
# Outlet: prghPressure p = 0, alpha inletOutlet 0. Walls: noSlip, constantAlphaContactAngle, fixedFluxPressure.
# Mesh copied from makeSlit.py's blockMeshDict for --walls real --w 8 (100 x 8 cells). Runs serially; log in /tmp.
set -e
name=$1; fill=$2; inlet=$3; theta=${4:-60}; T=${5:-2e-3}
HERE=$(cd "$(dirname "$0")" && pwd)
C=$HERE/$name
rm -rf "$C"; mkdir -p "$C"/{0,constant,system}; touch "$C/$name.foam"
H='FoamFile { format ascii; class dictionary; object'

cat > "$C/system/blockMeshDict" <<EOF
$H blockMeshDict; }
convertToMeters 1;
vertices ( (0 0 0) (0.002 0 0) (0.002 2e-05 0) (0 2e-05 0) (0 0 0.00016) (0.002 0 0.00016) (0.002 2e-05 0.00016) (0 2e-05 0.00016) );
blocks ( hex (0 1 2 3 4 5 6 7) (100 1 8) simpleGrading (1 1 1) );
boundary
(
    inlet  { type patch; faces ((0 4 7 3)); }
    outlet { type patch; faces ((2 6 5 1)); }
    walls  { type wall;  faces ((0 3 2 1) (4 5 6 7)); }
    frontAndBack { type empty; faces ((1 5 4 0) (3 7 6 2)); }
);
EOF
cat > "$C/system/controlDict" <<EOF
$H controlDict; }
application interFoam; startFrom startTime; startTime 0; stopAt endTime; endTime $T;
deltaT 1e-8; writeControl adjustableRunTime; writeInterval 1e-4; purgeWrite 0; writeFormat ascii;
writePrecision 8; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable no;
adjustTimeStep yes; maxCo 0.2; maxAlphaCo 0.2; maxDeltaT 1e-5;
EOF
cat > "$C/system/fvSchemes" <<EOF
$H fvSchemes; }
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    div(rhoPhi,U) Gauss linearUpwind grad(U);
    div(phi,alpha) Gauss interfaceCompression vanLeer 1;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
EOF
cat > "$C/system/fvSolution" <<EOF
$H fvSolution; }
solvers
{
    "alpha.water.*" { nAlphaCorr 2; nAlphaSubCycles 1; MULESCorr yes; nLimiterIter 5; solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0; }
    "pcorr.*" { solver PCG; preconditioner DIC; tolerance 1e-5; relTol 0; }
    p_rgh { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0.05; }
    p_rghFinal { \$p_rgh; relTol 0; }
    U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0; }
}
PIMPLE { momentumPredictor no; nOuterCorrectors 1; nCorrectors 3; nNonOrthogonalCorrectors 0; }
relaxationFactors { equations { ".*" 1; } }
EOF
cat > "$C/system/setFieldsDict" <<EOF
$H setFieldsDict; }
defaultFieldValues ( volScalarFieldValue alpha.water 0 );
regions ( boxToCell { box (-1 -1 -1) ($fill 1 1); fieldValues ( volScalarFieldValue alpha.water 1 ); } );
EOF
cat > "$C/constant/g" <<EOF
FoamFile { format ascii; class uniformDimensionedVectorField; object g; }
dimensions [0 1 -2 0 0 0 0]; value (-9.81 0 0);
EOF
cat > "$C/constant/momentumTransport" <<EOF
$H momentumTransport; }
simulationType laminar;
EOF
cat > "$C/constant/transportProperties" <<EOF
$H transportProperties; }
phases (water air);
water { transportModel Newtonian; nu 1e-6; rho 1000; }
air   { transportModel Newtonian; nu 1.76e-5; rho 1; }
sigma 0.072;
EOF
if [ "$inlet" = total ]; then pin="type prghTotalPressure; p0 uniform 0; value uniform 0;"
else pin="type prghPressure; p uniform 0; value uniform 0;"; fi
cat > "$C/0/p_rgh" <<EOF
FoamFile { format ascii; class volScalarField; object p_rgh; }
dimensions [1 -1 -2 0 0 0 0]; internalField uniform 0;
boundaryField
{
    inlet  { $pin }
    outlet { type prghPressure; p uniform 0; value uniform 0; }
    walls  { type fixedFluxPressure; value uniform 0; }
    frontAndBack { type empty; }
}
EOF
cat > "$C/0/U" <<EOF
FoamFile { format ascii; class volVectorField; object U; }
dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0);
boundaryField
{
    "(inlet|outlet)" { type pressureInletOutletVelocity; value uniform (0 0 0); }
    walls  { type noSlip; }
    frontAndBack { type empty; }
}
EOF
cat > "$C/0/alpha.water" <<EOF
FoamFile { format ascii; class volScalarField; object alpha.water; }
dimensions [0 0 0 0 0 0 0]; internalField uniform 0;
boundaryField
{
    inlet  { type inletOutlet; inletValue uniform 1; value uniform 1; }
    outlet { type inletOutlet; inletValue uniform 0; value uniform 0; }
    walls  { type constantAlphaContactAngle; theta0 $theta; limit gradient; value uniform 0; }
    frontAndBack { type empty; }
}
EOF
cd "$C"
blockMesh > log.blockMesh
[ "$fill" != 0 ] && setFields > log.setFields
cat > slit.info <<EOF
walls real
w 8
theta $theta
K 0
NW 0
nz 8
fill $fill
inlet $inlet
solver interFoam
EOF
interFoam > /tmp/interFoamSlit_$name.log 2>&1; st=$?
ln -sf /tmp/interFoamSlit_$name.log log.interFoam
echo "$name: interFoam exit $st"
