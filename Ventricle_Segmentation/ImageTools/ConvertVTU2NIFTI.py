import vtk
import nibabel as nib
import numpy as np
import os
import argparse
from vtk.util.numpy_support import vtk_to_numpy
from ConvertVTK2NIFTI import ConvertVTK2NIFTI

class ConvertSurface2NIFTI():
    def __init__(self, Args) -> None:
        self.Args = Args
        output_dir, _ = os.path.split(self.Args.InputSurface)
        self.output_file_path = os.path.join(output_dir,self.Args.OutputFileName)

    def VTPReader(self,path):
        reader = vtk.vtkXMLPolyDataReader()#UnstructuredGridReader()
        reader.SetFileName(path)
        reader.Update()
        unstructuredgrid = reader.GetOutput()
        #print(unstructuredgrid.GetPointData())
        #print(unstructuredgrid.GetPointData().GetScalars() is None)

        '''
        bounds = unstructuredgrid.GetBounds()

        structuredgrid = vtk.vtkImageData()
        structuredgrid.SetSpacing(0.5,0.5,0.5)
        structuredgrid.SetOrigin(bounds[0], bounds[2], bounds[4])

        dims = [
            int((bounds[1]-bounds[0]) / 0.5),
            int((bounds[3]-bounds[2]) / 0.5),
            int((bounds[5]-bounds[4]) / 0.5)
        ]

        structuredgrid.SetDimensions(dims)


        probfilter = vtk.vtkProbeFilter()
        probfilter.SetInputData(structuredgrid)
        probfilter.SetSourceData(unstructuredgrid)
        probfilter.Update()

        print(probfilter.GetOutput().GetPointData().GetScalars() is None)
        exit(0)
        '''
        return unstructuredgrid
    
    def probfilter(self, Enclosed, Image):
        
        bounds = Image.GetBounds()

        structuredgrid = vtk.vtkImageData()
        structuredgrid.SetSpacing(0.5,0.5,0.5)
        structuredgrid.SetOrigin(bounds[0], bounds[2], bounds[4])

        dims = [
            int((bounds[1]-bounds[0]) / 0.5),
            int((bounds[3]-bounds[2]) / 0.5),
            int((bounds[5]-bounds[4]) / 0.5)
        ]

        structuredgrid.SetDimensions(dims)
        
        #print(dir(structuredgrid.GetPointData()))
        #exit(0)
        Image.GetPointData().AddArray(Enclosed)
        Image.Modified()

        '''
        probfilter = vtk.vtkProbeFilter()
        probfilter.SetInputData(structuredgrid)
        probfilter.SetSourceData(Enclosed)
        probfilter.Update()
        '''
        return Image

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


    def labelvolume(self, Surface, Image):
        
        PointsVTK=vtk.vtkPoints()
        PointsVTK.SetNumberOfPoints(Image.GetNumberOfPoints())

        for i in range(Image.GetNumberOfPoints()):
            PointsVTK.SetPoint(i,Image.GetPoint(i))
		
        print ("--- Converting Image Points into a Polydata")
		#Convert into a polydata format
        pdata_points = vtk.vtkPolyData()
        pdata_points.SetPoints(PointsVTK)

        #labels = np.zeros(num_points, dtype=np.uint8)
        selectEnclosed = vtk.vtkSelectEnclosedPoints()
        selectEnclosed.SetInputData(pdata_points) #Points in the Image
        selectEnclosed.SetSurfaceData(Surface) #Surface Model
        selectEnclosed.SetTolerance(0.00000000001)
        selectEnclosed.Update()

        return selectEnclosed.GetOutput().GetPointData().GetArray("SelectedPoints")
    
    def WriteVTK(self, Image):
        writer = vtk.vtkDataSetWriter()#vtkXMLImageDataWriter()
        writer.SetFileName(self.output_file_path)
        writer.SetInputData(Image)
        writer.Write()

    def main(self):
        Surface = self.VTPReader(self.Args.InputSurface)
        #todo: add labelvolume()
        class_arguments = argparse.Namespace(InputFolder=None, Nformat=".nii.gzz")
        Image = ConvertVTK2NIFTI(class_arguments).ReadVTKImage(self.Args.InputImage)
        Enclosed = self.labelvolume(Surface, Image)
        Labeled_Image = self.probfilter(Enclosed, Image)
        self.WriteVTK(Labeled_Image)
        #np_array = self.vtk2numpy(Labeled_Image)#ConvertVTK2NIFTI(class_arguments).vtk2numpy(Labeled_Image)
        #ConvertVTK2NIFTI(class_arguments).numpy2NIFTI(np_array, self.output_file_path)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputSurface", "--InputSurface", required=True, dest="InputSurface", type=str)
    parser.add_argument("-InputImage", "--InputImage", required=True, dest="InputImage", type=str)
    parser.add_argument("-OutputFileName", "--OutputFileName", required=True, dest="OutputFileName", type=str)
    args = parser.parse_args()

    ConvertSurface2NIFTI(args).main()