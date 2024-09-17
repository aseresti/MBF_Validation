import os
import argparse
import vtk
import nibabel as nib
import numpy as np


class ConvertVTK2NIFTI():
    """Converts vtk image formats (.vti, .vtk) into NIFTI image formats (.nii, .nii.gz)
    """
    def __init__(self,Args) -> None:
        self.Args = Args

    def GetImages(self) -> list:
        """Gets all of the vtk images within the input directory

        Returns:
            list:a list of str 
        """
        vtk_Images = []
        
        for filename in os.listdir(self.Args.InputFolder):
            if filename.endswith('vti') or filename.endswith('vtk'):
                vtk_Images.append(filename)
        
        return vtk_Images
    
    def ReadVTKImage(self,path) -> vtk.vtkImageData:

        reader = vtk.vtkImageReader()
        reader.SetFileName(path)
        reader.Update()
        return reader.GetOutput()

    def vtk_to_numpy(self,Image) -> np.array:
        
        vtk_data = Image.GetPointData().GetScalars()
        dims = Image.GetDimensions()
        numpy_data = vtk.util.numpy_support.vtk_to_numpy(vtk_data)
        numpy_data = numpy_data.reshape(dims,order='F')
        
        return numpy_data
    
    def main(self) -> None:
        
        vtk_Images = self.GetImages()
        vtk_Images.sort()

        vtk_dict = dict()
        for image in vtk_Images:
            image_path = f"{self.Args.InputFolder}/{image}"
            Image = self.ReadVTKImage(image_path)
            print(self.vtk_to_numpy(Image))
            exit(1)
            vtk_dict.update({f"{image}":f"{Image}"})
            
            

if __name__=="__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("-InputFolder", "--InputFolder", type= str, default="./", dest= "InputFolder", required=True, help="the folder containing vtk format images")
    Parser.add_argument("-Nformat", "--Nformat", type= str, default=".nii.gz", dest="Nformat", required= True, help="NIFTI supported file formats: .nii or .nii.gz")
    args = Parser.parse_args()

    ConvertVTK2NIFTI(args).main()