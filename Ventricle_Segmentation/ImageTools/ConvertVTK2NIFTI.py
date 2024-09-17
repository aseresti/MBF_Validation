import os
import argparse
import vtk
import nibabel
import numpy as np

class ConvertVTK2NIFTI():
    """Converts vtk image formats (.vti, .vtk) into NIFTI image formats (.nii, .nii.gz)
    """
    def __init__(self,Args) -> None:
        self.Args = Args

    def ReadInputImages(self):
        print(self.Args.InputFolder)
        self.vtk_Images = []
        print(os.listdir(self.Args.InputFolder))
        exit(0)
        for filename in os.listdir(self.Args.InputFolder):
            print(filename)
            if filename.endswith('vti') or filename.endswith('vtk'):
                print(filename)
                exit(1)

    def main():
        pass

if __name__=="__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("-InputFolder", "--InputFolder", type= str, default="./", dest= "InputFolder", required=True, help="the folder containing vtk format images")
    Parser.add_argument("-Nformat", "--Nformat", type= str, default=".nii.gz", dest="Nformat", required= True, help="NIFTI supported file formats: .nii or .nii.gz")
    args = Parser.parse_args()

    ConvertVTK2NIFTI(args).ReadInputImages()