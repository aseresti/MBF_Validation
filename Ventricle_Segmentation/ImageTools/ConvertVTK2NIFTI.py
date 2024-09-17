import os
import argparse
import vtk
import nibabel as nib
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy


class ConvertVTK2NIFTI():
    """Converts vtk image formats (.vti, .vtk) into NIFTI image formats (.nii, .nii.gz)
    """
    def __init__(self,Args) -> None:
        self.Args = Args
        output_dir = "ImageNF"
        os.system(f"mkdir {self.Args.InputFolder}/{output_dir}")
        self.output_dir = f"{self.Args.InputFolder}/{output_dir}"

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

    def vtk2numpy(self,Image) -> np.array:
        
        vtk_data = Image.GetPointData().GetScalars()
        dims = Image.GetDimensions()
        numpy_data = vtk_to_numpy(vtk_data)
        numpy_data = numpy_data.reshape(dims,order='F')
        
        return numpy_data
    
    def numpy2NIFTI(self,numpy_data, nfimage_path):

        affine = np.eye(4) #no scaling, rotation, or translation is applied
        nifti_Image = nib.Nifti1Image(numpy_data, affine)
        nib.save(nifti_Image, nfimage_path)

    def main(self) -> None:
        
        vtk_Images = self.GetImages()
        vtk_Images.sort()

        for image in vtk_Images:
            image_path = f"{self.Args.InputFolder}/{image}"
            nfimage_path, _ = f"{os.path.splitext(image_path)}.{self.Args.Nformat}"
            Image = self.ReadVTKImage(image_path)
            numpy_data = self.vtk2numpy(Image)
            self.numpy2NIFTI(numpy_data, nfimage_path)

            
            

if __name__=="__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("-InputFolder", "--InputFolder", type= str, default="./", dest= "InputFolder", required=True, help="the folder containing vtk format images")
    Parser.add_argument("-Nformat", "--Nformat", type= str, default=".nii.gz", dest="Nformat", required= True, help="NIFTI supported file formats: .nii or .nii.gz")
    args = Parser.parse_args()

    ConvertVTK2NIFTI(args).main()