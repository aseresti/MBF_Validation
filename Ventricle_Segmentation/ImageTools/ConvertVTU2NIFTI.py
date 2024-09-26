import vtk
#import nibabel as nib
import numpy as np
import os
import argparse
from vtk.util.numpy_support import vtk_to_numpy
from ConvertVTK2NIFTI import ConvertVTK2NIFTI

class ConvertSurface2NIFTI():
    def __init__(self, Args) -> None:
        self.Args = Args
        output_dir, InputSurfaceName = os.path.split(self.Args.InputSurface)
        InputSurfaceName = os.path.splitext(InputSurfaceName)[0]
        _, ImageName = os.path.split(self.Args.InputImage)
        ImageName = os.path.splitext(ImageName)[0]
        self.output_file_path = os.path.join(output_dir,ImageName + "_" +InputSurfaceName)

    def VTPReader(self,path):
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(path)
        reader.Update()
        return reader.GetOutput()
    
    def CreateLabeledImage(self, Enclosed, Image):
        
        bounds = Image.GetBounds()
        origin = Image.GetOrigin()
        spacing = Image.GetSpacing()

        structuredgrid = vtk.vtkImageData()
        structuredgrid.SetSpacing(spacing)
        structuredgrid.SetOrigin(origin)

        dims = [
            int((bounds[1]-bounds[0]) / spacing[0]),
            int((bounds[3]-bounds[2]) / spacing[1]),
            int((bounds[5]-bounds[4]) / spacing[2])
        ]

        structuredgrid.SetDimensions(dims)

        structuredgrid.AllocateScalars(vtk.VTK_FLOAT, 1)
        
        for i in range(Image.GetNumberOfPoints()):
            (x,y,z) = Image.GetPoint(i)
            scalar = Enclosed.GetValue(i)
            iX = int(round((x-origin[0])/spacing[0]))
            iY = int(round((y-origin[1])/spacing[1]))
            iZ = int(round((z-origin[2])/spacing[2]))

            if 0 <= iX < dims[0] and 0 <= iY < dims[1] and 0 <= iZ < dims[2]:
                structuredgrid.SetScalarComponentFromFloat(iX,iY,iZ,0,scalar)

        return structuredgrid

    def vtk2numpy(self,Image) -> np.array:
        """Converts vtk image scalar data into a numpy array with the same dimensions.

        Args:
            Image (vtk.vtkImageData): The output of ReadVTKImage

        Returns:
            np.array: numpy array of the image scalars
        """
        
        vtk_data = Image
        dims = Image.GetDimensions()
        numpy_data = vtk_to_numpy(vtk_data)
        numpy_data = numpy_data.reshape(dims,order='F')
        
        return numpy_data


    def LabelEnclosedPoints(self, Surface, Image):
        
        PointsVTK=vtk.vtkPoints()
        PointsVTK.SetNumberOfPoints(Image.GetNumberOfPoints())

        #structuredgrid = vtk.vtkImageData()

        for i in range(Image.GetNumberOfPoints()):
            PointsVTK.SetPoint(i,Image.GetPoint(i))
            #structuredgrid.GetPointData().Setpoint(i,Image.GetPoint(i))
		
        print ("--- Converting Image Points into a Polydata")
		#Convert into a polydata format
        pdata_points = vtk.vtkPolyData()
        pdata_points.SetPoints(PointsVTK)

        #labels = np.zeros(num_points, dtype=np.uint8)
        selectEnclosed = vtk.vtkSelectEnclosedPoints()
        selectEnclosed.SetInputData(pdata_points) #Points in the Image
        selectEnclosed.SetSurfaceData(Surface) #Surface Model
        selectEnclosed.SetTolerance(0.000000001)
        selectEnclosed.Update()

        #SelectedArray = selectEnclosed.GetOutput().GetPointData().GetArray("SelectedPoints")
    
        return selectEnclosed.GetOutput().GetPointData().GetArray("SelectedPoints")
    
    def WriteVTK(self, Image):
        writer = vtk.vtkDataSetWriter()#vtkXMLImageDataWriter()
        writer.SetFileName(self.output_file_path + ".vtk")
        writer.SetInputData(Image)
        writer.Write()

    def main(self):
        Surface = self.VTPReader(self.Args.InputSurface)
        class_arguments = argparse.Namespace(InputFolder=None, Nformat=".nii.gzz")
        Image = ConvertVTK2NIFTI(class_arguments).ReadVTKImage(self.Args.InputImage)
        Enclosed = self.LabelEnclosedPoints(Surface, Image)
        Labeled_Image = self.CreateLabeledImage(Enclosed, Image)
        self.WriteVTK(Labeled_Image)
        #todo: convert to nifti (error in vtk2numpy)
        np_array = ConvertVTK2NIFTI(class_arguments).vtk2numpy(Labeled_Image)
        ConvertVTK2NIFTI(class_arguments).numpy2NIFTI(np_array, self.output_file_path + ".nii.gz", Image)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputSurface", "--InputSurface", required=True, dest="InputSurface", type=str)
    parser.add_argument("-InputImage", "--InputImage", required=True, dest="InputImage", type=str)
    args = parser.parse_args()

    ConvertSurface2NIFTI(args).main()