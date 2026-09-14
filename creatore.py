import os
import shutil

# describing the path as absolute path to make it general
script_dir = os.path.abspath(os.path.dirname(__file__))
textiles_path = os.path.join(script_dir, "Textiles")
output_path = os.path.join(script_dir, "output")
general_setup_path = os.path.join(script_dir, "general_setup")

# the first time the scrip is run, it will create the output folder
if not os.path.exists(output_path):
    os.makedirs(output_path)

# sniff around the textles folder to find the stl files and create a folder for each one
for file_name in os.listdir(textiles_path):
    if file_name.endswith(".stl"):
        folder_name = os.path.splitext(file_name)[0]
        folder_path = os.path.join(output_path, folder_name)

        # sometimes an stl is added in a second moment and we must be sure that its folder exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # general_setup is the folder with the general OpenFOAM case setup for TexAIles
        for item in os.listdir(general_setup_path):
            s = os.path.join(general_setup_path, item)  # origin
            d = os.path.join(folder_path, item)         # destination
            
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
                tri_surface_path = os.path.join(folder_path, "constant", "triSurface") #in here we copy each stl flle in the triSurface folder for its folder
                if not os.path.exists(tri_surface_path):
                    os.makedirs(tri_surface_path)
                shutil.copy2(os.path.join(textiles_path, file_name), os.path.join(tri_surface_path, file_name))
                
        print(f"Everything copied in: {folder_path}")
