import vtk
import nibabel as nib
import numpy as np
import os
import argparse
from vtk.util.numpy_support import vtk_to_numpy
from ConvertVTK2NIFTI import ConvertVTK2NIFTI

class ConvertVTU2NIFTI():
    def __init__(self, Args) -> None:
        self.Args = Args
        _, output_dir = os.path.split(self.Args.InputVTUFile)
        self.output_file_path = os.path.join(output_dir,self.Args.OutputFileName)

    def VTUReader(self,path):
        reader = vtk.vtkXMLPolyDataReader()#UnstructuredGridReader()
        reader.SetFileName(path)
        reader.Update()
        unstructuredgrid = reader.GetOutput()
        print(unstructuredgrid.GetPointData())
        print(unstructuredgrid.GetPointData().GetScalars() is None)

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

        return probfilter.GetOutput()

    def labelvolume(self, polydata):
        points = polydata.GetPoints()
        num_points = points.GetNumberOfPoints()

        labels = np.zeros(num_points, dtype=np.uint8)
        #todo: add vtkSelectEnclosedPoints()

    def main(self):
        vtufile = self.VTUReader(self.Args.InputVTUFile)
        #todo: add labelvolume()
        class_arguments = argparse.Namespace(InputFolder=None, Nformat=".nii.gzz")
        np_array = ConvertVTK2NIFTI(class_arguments).vtk2numpy(vtufile)
        ConvertVTK2NIFTI(class_arguments).numpy2NIFTI(np_array, self.output_file_path)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputVTUFile", "--InputVTUFile", required=True, dest="InputVTUFile", type=str)
    parser.add_argument("-OutputFileName", "--OutputFileName", required=True, dest="OutputFileName", type=str)
    args = parser.parse_args()

    ConvertVTU2NIFTI(args).main()