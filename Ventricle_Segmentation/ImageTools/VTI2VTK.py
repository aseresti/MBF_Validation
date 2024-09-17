import os
import argparse
from pathlib import Path

def VTI2VTK(args):
    """This script is specific to Japanese dataset. Modify for other uses. 

    Args:
        args (string): InputFoldername
    """
    directory_path = Path(args.InputFolder)
    all_entries = os.listdir(directory_path)
    # Filter out the files
    files = [file.name for file in directory_path.iterdir() if file.is_dir()]
    
    for file in files:
        print(file)
        digit = ''.join([char for char in file if char.isdigit()])
        print(digit)
        os.system(f"vmtkimagewriter -ifile {directory_path}/{file}/CTAImage.vti -ofile ./CTAImage{digit}.vtk")

if __name__=="__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("-InputFolder", "--InputFoler", type=str, required=True, dest="InputFolder")
    args = Parser.parse_args()
    VTI2VTK(args)