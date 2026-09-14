#!/usr/bin/python3
import inspect, os

frame = inspect.currentframe()
filePath = inspect.getfile(frame)
currentDir = os.path.realpath(os.path.abspath(os.path.dirname(filePath)))

if os.path.exists(currentDir + '/log0f.checkMesh_post'):
    print('Opening log0f.checkMesh_post file')
    f=open("log0f.checkMesh_post")
    lines=f.readlines()
    f.close()
else:
    print('Opening log0d.checkMesh file')
    f=open("log0d.checkMesh")
    lines=f.readlines()
    f.close()

# Scan through the lines to find the bounding box
# Look for line of the form:
# Overall domain bounding box (-0.00015 -0.00015 0.0001) (0.000153159 0.00015 0.000400066)

for line in lines:
    if (line.find("cells:")>(-1)):
        p1=line.find("cells:")
        numCells=line[(p1+18):(-1)]
    elif (line.find("Overall domain bounding box ")>(-1)):
        pcoords=line.find("box")
        orcoords=line[(pcoords+4):(-1)]
s1=orcoords.replace("(","")
s2=s1.replace(")","")
coords=s2.split()
x_len=(float(coords[3])-float(coords[0]))
y_len=(float(coords[4])-float(coords[1]))
z_len=(float(coords[5])-float(coords[2]))

# Print all lengths
print("X side: \n",x_len)
print("Y side: \n",y_len)
print("Z side: \n",z_len)
print("\n")

f=open(currentDir+'/log1.postProcess')
lines=f.readlines()
f.close()
for line in lines:
    if (line.find("Create mesh for time =")>(-1)):
        p1 = line.find("=")
        time = str(line[(p1+2):-1])
    """ if (line.find("Tau: ")>(-1)):
        p2 = line.find(":")
        tau = float(line[(p2+2):-1])
        tau=-tau
        break """
print("Final time:", time)
#print("Tau:", tau)

vel = [0, 0, 0]

# Scan through the lines to find area (or volume) and velocity
# Look for lines of the form:
# "Area(Volume)   :    "
# 44            	(1.352724e-04 4.150867e-06 3.760801e-06)

#
resultsDir=os.path.join(currentDir, './postProcessing/volume_average/{}/'.format(time))
f=open(resultsDir + "volFieldValue.dat")
lines=f.readlines()
f.close()
for line in lines:
    if (line.find("# Volume      : ")>(-1)):
        p1=line.find("# Volume      : ")
        p2=line.find("\n")
        totVol=line[(p1+16):p2]
        print("\nTotal mesh volume: ", totVol)
    if (line == lines[-1]):
        p1=line.find("(")
        p2=line[(p1+1):(-2)]
        coords=p2.split()
        print("Velocity:")
        for i in range(len(coords)):
            vel[i]=float(coords[i])
            print("%.5e" % vel[i])


# Determine principal direction of fluid
# 0 for x, 1 for y, 2 for z
dir = 0
for i in range(len(coords)):
    if (abs(vel[i]) > abs(vel[dir])):
        dir = i


if os.path.exists(currentDir + '/Outfile.txt'):
    f=open(currentDir + '/Outfile.txt', 'r')    # Outfile.txt file can be obtained from yade simulation performed to create packing
    lines=f.readlines()
    f.close()
    for line in lines:
        if (line.find("Mean Size (micro_m):")>(-1)):
            p1=line.find(':')
            dg=float(line[(p1+2):(-1)])/(10**6)     # If the packing is created in another way, comment the previous lines and insert manually the grain mean size
else:
    f=open(currentDir + '/caseSetup', 'r')
    lines=f.readlines()
    f.close()
    for line in lines:
        if (line.find("dg")>(-1)):
            dg_line=line.find('dg')
            dg=float(line[(dg_line+3):(-2)])
         
f=open(currentDir + '/constant/transportProperties', 'r')  
lines=f.readlines()
f.close()
for line in lines:
    if (line.find("nu")>(-1)):
        p1=line.find(']')
        nu=float(line[(p1+2):(-2)])
f=open(currentDir + '/caseSetup', 'r')
lines=f.readlines()
f.close()
for line in lines:
    if (line.find("p0")>(-1)):
        p1=line.find('p0')
        deltaP=float(line[(p1+3):(-2)])


# Calculate darcyan velocity, porosity, permeability and Reynolds number
porosity = float(totVol) / (x_len*y_len*z_len)
darcyanVel = vel[dir]*porosity
reynolds = abs(darcyanVel)* dg / nu
permeability = abs(darcyanVel) * x_len * nu / deltaP


# Write output file
fResults=open("Results.dat","w")
fResults.write("ZONE: Volume\n\n")
fResults.write("Number of cells: %.5e\n" % (float(numCells)))
fResults.write("Mesh volume (m^3): %.5e\n" % (float(totVol)))
fResults.write("REV volume (m^3): %.5e\n" % (x_len*y_len*z_len))
fResults.write("Porosity: %.5f\n\n" % porosity)
fResults.write("Velocity (m/s): %.5e  %.5e  %.5e\n" % (vel[0], vel[1], vel[2]))
fResults.write("Darcyan velocity (m/s): %.5e\n" % darcyanVel)
fResults.write("Reynolds: %.5f\n" % reynolds)
fResults.write("Permeability (m^2): %.5e" % permeability)
fResults.write("\n\n\n")
#fResults.write("Tortuosity: %.4f" % tau)
fResults.close()