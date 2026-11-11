# viewBath.py (Python 2: ParaView 5.6's pvbatch)  -  pictures of the bath region of a study 2g case (README, Results), with ParaView's built-in OpenFOAM reader
# (paraFoam's default reader returns ~0 for the inlet patch values of pressureInletOutletVelocity; the built-in one reads them).
#   /opt/paraviewopenfoam56/bin/pvbatch --force-offscreen-rendering viewBath.py <case> [time] [x_mm]
# Writes <case>/viewBath_<time>_inlet.png and <case>/viewBath_<time>_slice.png:
#   inlet: the bath patch seen from below, coloured by U_y (the inflow velocity, + = into the fabric), x horizontal, z vertical;
#   slice: plane x = x_mm (default 0.709, through an outermost-layer cell with a strong inflow), bath at the bottom, top padding
#          on the right, coloured by alpha.wetting, arrows = U (mixture velocity), region y 0.33-0.53 mm, z 0.10-0.27 mm.
import os
import sys

from paraview.simple import (CellCenters, ColorBy, CreateRenderView, ExtractBlock, GetColorTransferFunction, Glyph, Hide,
                             OpenFOAMReader, Render, SaveScreenshot, Show, Slice)

case = sys.argv[1].rstrip("/")
t = float(sys.argv[2]) if len(sys.argv) > 2 else 0.003
xs = (float(sys.argv[3]) if len(sys.argv) > 3 else 0.709) * 1e-3
foam = [f for f in os.listdir(case) if f.endswith(".foam")]
fn = os.path.join(case, foam[0]) if foam else os.path.join(case, "case.foam")
if not foam:
    open(fn, "w").close()
r = OpenFOAMReader(FileName=fn)
r.MeshRegions = ["internalMesh", "inlet"]
r.CellArrays = ["U", "alpha.wetting", "p"]
r.UpdatePipeline(t)
v = CreateRenderView()
v.ViewTime = t
v.Background = [1, 1, 1]
v.OrientationAxesVisibility = 1

inl = ExtractBlock(Input=r)
inl.BlockIndices = [2]                      # block 1 internalMesh, block 2 the patches (inlet)
d = Show(inl, v)
ColorBy(d, ("CELLS", "U", "Y"))
lut = GetColorTransferFunction("U")
lut.VectorMode = "Component"
lut.VectorComponent = 1
lut.ApplyPreset("Cool to Warm", True)
lut.RescaleTransferFunction(-0.3, 0.3)
d.SetScalarBarVisibility(v, True)
v.CameraPosition = [0.000909, -0.01, 0.0000705]
v.CameraFocalPoint = [0.000909, 0.0003, 0.0000705]
v.CameraViewUp = [0, 0, 1]
v.ResetCamera()
Render(v)
tag = "%gms" % (t * 1e3)
SaveScreenshot(os.path.join(case, "viewBath_%s_inlet.png" % tag), v, ImageResolution=[1400, 500])
Hide(inl, v)

sl = Slice(Input=r)
sl.SliceType.Origin = [xs, 0.0004, 0.0001]
sl.SliceType.Normal = [1, 0, 0]
ds = Show(sl, v)
ColorBy(ds, ("CELLS", "alpha.wetting"))
al = GetColorTransferFunction("alpha.wetting")
al.ApplyPreset("Blue Orange (divergent)", True)
al.RescaleTransferFunction(0, 1)
ds.SetScalarBarVisibility(v, True)
gl = Glyph(Input=CellCenters(Input=sl), GlyphType="Arrow")
gl.OrientationArray = ["POINTS", "U"]
gl.ScaleArray = ["POINTS", "U"]
gl.ScaleFactor = 2.5e-5
gl.GlyphMode = "All Points"
dg = Show(gl, v)
ColorBy(dg, None)
dg.DiffuseColor = [0, 0, 0]
v.CameraPosition = [-0.01, 0.00043, 0.000185]        # looking along +x: y up, z to the right
v.CameraFocalPoint = [xs, 0.00043, 0.000185]
v.CameraViewUp = [0, 1, 0]
v.CameraParallelProjection = 1
v.CameraParallelScale = 0.000105
Render(v)
SaveScreenshot(os.path.join(case, "viewBath_%s_slice.png" % tag), v, ImageResolution=[1000, 1200])
print("written " + os.path.join(case, "viewBath_%s_*.png" % tag))
