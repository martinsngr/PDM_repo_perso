import TexGen.Core as TG
from TexGen.Core import *
import numpy as np
import os
import csv

# 1) Setting geometrical parameters
# NB @1 always refers to warp yarns and @2 refer to weft yarns

# Setting yarns density, expressed in [picks/cm]
D1_values = np.array([22, 29.3])
D2_values = np.array([15, 20])

#[cm]
d1 = 0.0263
d2 = 0.0282

# Parametri variabili
v_values = np.linspace(0.4, 0.4, 1)  # Poisson's Ratio variabile
r_f_values = np.linspace(0.5, 0.5, 1)  # Riduzione fattore variabile
#weave_type = ["PW", "BW", "TW", "FR"]
weave_type = ["BW"]

# Directory di output per salvare i file generati
output_dir = "Textiles"
os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists

# Funzione per generare e salvare la geometria
def generate_and_save_textile(v, r_f, D1, D2, weave):
    s1 = 1 / D1
    s2 = 1 / D2
    t1 = r_f * d1
    t2 = r_f * d2
    w1 = d1 + v * (d1 - t1)
    w2 = d2 + v * (d2 - t2)

    Textile = TG.CTextile()

    # Creazione e definizione delle caratteristiche dei filati
    Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]

    if weave == "PW":
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, -s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 2 * s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 3 * s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 4 * s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 5*s2, t1)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, -s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 0, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 2 * s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 3 * s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 4 * s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 5 * s2, 0)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, -s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 0, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 3 * s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 4 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 5 * s2, t1)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, -s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 0, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 2 * s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 4 * s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 5 * s2, 0)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, -s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 0, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 2 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 3 * s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 5 * s2, t1)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w1, t1)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(7*s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 7*s2, 0))
            Textile.AddYarn(Yarn)
            
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        Yarns[0].AddNode(TG.CNode(TG.XYZ(-s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(2 * s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(3 * s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(4 * s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(5 * s1, 0, 0)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(-s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(0, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(2 * s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(3 * s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(4 * s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(5 * s1, s2, t2)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(-s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(0, 2 * s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 2 * s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(3 * s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(4 * s1, 2 * s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(5 * s1, 2 * s2, 0)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(-s1, 3 * s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(0, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(s1, 3 * s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(2 * s1, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 3 * s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(4 * s1, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(5 * s1, 3 * s2, t2)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(-s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(0, 4 * s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(2 * s1, 4 * s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(3 * s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 4 * s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(5 * s1, 4 * s2, 0)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w2, t2)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(6 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 6 * s2, 0))
            Textile.AddYarn(Yarn)

    if weave == "BW":
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, -s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 2 * s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 3 * s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 4 * s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 5 * s2, t1)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, -s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 0, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 2 * s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 3 * s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 4 * s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 5 * s2, t1)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, -s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 0, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 3 * s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 4 * s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 5 * s2, 0)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, -s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 0, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 2 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 3 * s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 4 * s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 5 * s2, 0)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, -s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 0, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 2 * s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 3 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 5 * s2, t1)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w1, t1)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(5 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 5 * s2, 0))
            Textile.AddYarn(Yarn)
        
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        
        Yarns[0].AddNode(TG.CNode(TG.XYZ(-s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(2 * s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(3 * s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(4 * s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(5 * s1, 0, t2)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(-s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(0, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(2 * s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(3 * s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(4 * s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(5 * s1, s2, 0)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(-s1, 2 * s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(0, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2 * s1, 2 * s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(3 * s1, 2 * s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(4 * s1, 2 * s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(5 * s1, 2 * s2, 0)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(-s1, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(0, 3 * s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(s1, 3 * s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(2 * s1, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3 * s1, 3 * s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(4 * s1, 3 * s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(5 * s1, 3 * s2, t2)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(-s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(0, 4 * s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(s1, 4 * s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(2 * s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(3 * s1, 4 * s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4 * s1, 4 * s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(5 * s1, 4 * s2, t2)))
        
        for Yarn in Yarns:  
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w2, t2)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(5 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 5 * s2, 0))
            Textile.AddYarn(Yarn)

    if weave == "FR":
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, -s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0,  t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 2 * s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 3 * s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 4 * s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 5 * s2, t1)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, -s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 0, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 2*s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 3*s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 4*s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 5*s2, 0)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, -s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 0, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 2*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 3*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 4*s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 5*s2, t1)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, -s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 0, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 2*s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 3*s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 4*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 5*s2, 0)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, -s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 0, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 2*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 3*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 4*s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 5*s2, t1)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w1, t1)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(5 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 5 * s2, 0))
            Textile.AddYarn(Yarn)
            
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        
        Yarns[0].AddNode(TG.CNode(TG.XYZ(-s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(2*s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(3*s1, 0, t2 )))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(4*s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(5*s1, 0, t2)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(-s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(0, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(2*s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(3*s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(4*s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(5*s1, s2, t2)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(-s1, 2*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(0, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(s1, 2*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(3*s1, 2*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(4*s1, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(5*s1, 2*s2, 0)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(-s1, 3*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(0, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(s1, 3*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(2*s1, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 3*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(4*s1, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(5*s1, 3*s2, 0)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(-s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(0, 4*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(2*s1, 4*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(3*s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 4*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(5*s1, 4*s2, t2)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w2, t2)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(5 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 5 * s2, 0))
            Textile.AddYarn(Yarn)
        
    if weave_type == "TW":
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, -s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 2*s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 3*s2, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 4*s2, t1)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 5*s2, 0)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, -s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 0, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, t1)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 2*s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 3*s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 4*s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, 5*s2, t1)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, -s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 0, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 2*s2, t1)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 3*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 4*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 5*s2, 0)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, -s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 0, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 2*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 3*s2, t1)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 4*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 5*s2, 0)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, -s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 0, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 2*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 3*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 4*s2, t1)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 5*s2, 0)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w1, t1)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(5 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 5 * s2, 0))
            Textile.AddYarn(Yarn)
        
        Yarns = [TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn(), TG.CYarn()]
        
        Yarns[0].AddNode(TG.CNode(TG.XYZ(-s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(0, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(2*s1, 0, t2)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(3*s1, 0, t2 )))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(4*s1, 0, 0)))
        Yarns[0].AddNode(TG.CNode(TG.XYZ(5*s1, 0, t2)))
        
        Yarns[1].AddNode(TG.CNode(TG.XYZ(-s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(0, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(s1, s2, 0)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(2*s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(3*s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(4*s1, s2, t2)))
        Yarns[1].AddNode(TG.CNode(TG.XYZ(5*s1, s2, 0)))
        
        Yarns[2].AddNode(TG.CNode(TG.XYZ(-s1, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(0, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(s1, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(2*s1, 2*s2, 0)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(3*s1, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(4*s1, 2*s2, t2)))
        Yarns[2].AddNode(TG.CNode(TG.XYZ(5*s1, 2*s2, t2)))
        
        Yarns[3].AddNode(TG.CNode(TG.XYZ(-s1, 3*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(0, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(s1, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(2*s1, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(3*s1, 3*s2, 0)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(4*s1, 3*s2, t2)))
        Yarns[3].AddNode(TG.CNode(TG.XYZ(5*s1, 3*s2, t2)))
        
        Yarns[4].AddNode(TG.CNode(TG.XYZ(-s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(0, 4*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(2*s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(3*s1, 4*s2, t2)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(4*s1, 4*s2, 0)))
        Yarns[4].AddNode(TG.CNode(TG.XYZ(5*s1, 4*s2, t2)))
        
        for Yarn in Yarns:
            Yarn.AssignInterpolation(TG.CInterpolationCubic())
            Yarn.AssignSection(TG.CYarnSectionConstant(TG.CSectionEllipse(w2, t2)))
            Yarn.SetResolution(20)
            Yarn.AddRepeat(TG.XYZ(5 * s1, 0, 0))
            Yarn.AddRepeat(TG.XYZ(0, 5 * s2, 0))
            Textile.AddYarn(Yarn)
    
    Textile.AssignDomain(TG.CDomainPlanes(TG.XYZ(0, 0, -1.5*t1), TG.XYZ(4*s1, 4*s2, 1.5*t2)))
    textile_name = f"{weave_type}-{D1}-{D2}-{v}-{r_f}"
    TG.AddTextile(textile_name, Textile)
    
    mesh = TG.CMesh()
    TrimDomain = False
    Textile.AddSurfaceToMesh(mesh, TrimDomain)
    mesh.SaveToSTL(os.path.join(output_dir, textile_name + ".stl"))
    
    csv_path = os.path.join(output_dir, "features.csv")
    file_exists = os.path.isfile(csv_path)
    
    with open(csv_path, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            writer.writerow(['strct', 'D1', 'D2', 'v', 'rf'])
        writer.writerow([weave_type, D1, D2, v, r_f])
       
# Loop through all combinations of v and r_f to generate textiles
for weave_type in weave_type:
    for D1 in D1_values:
        for D2 in D2_values:
            for v in v_values:
                for r_f in r_f_values:
                    generate_and_save_textile(v, r_f, D1, D2, weave_type)

