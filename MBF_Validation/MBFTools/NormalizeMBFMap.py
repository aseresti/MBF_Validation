import os
import vtk
import numpy as np
import argparse
from utilities import ReadVTUFile, WriteVTUFile, ThresholdInBetween, ExtractSurface
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

class MBFNormalization():
    def __init__(self, args):
        self.args = args
        self.MBF = ReadVTUFile(self.args.InputMBFMap)
        labels = f"{os.path.splitext(self.args.InputMBFMap)[0]}_Labels.dat"
        self.Labels = {}
        with open(labels, "r") as ifile:
            for LINE in ifile:
                line = LINE.split()
                self.Labels[line[1]] = line[0]

    def Normalize(self):
        ImageScalars = self.MBF.GetPointData().GetArray(self.args.ArrayName)
        per_75th = np.percentile(vtk_to_numpy(ImageScalars), 75)
        IndexMBF = numpy_to_vtk(ImageScalars/per_75th)
        IndexMBF.SetName("IndexMBF")
        self.MBF.GetPointData().AddArray(IndexMBF)
        OPath = f"./{os.path.splitext(os.path.basename(self.args.InputMBFMap))[0]}_Normalized.vtu"
        WriteVTUFile(OPath, self.MBF)

    def CalculateVolume(self,ClosedSurface):
        tri_filter = vtk.vtkTriangleFilter()
        tri_filter.SetInputData(ClosedSurface)
        tri_filter.Update()

        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputData(tri_filter.GetOutput())
        cleaner.Update()

        Mass = vtk.vtkMassProperties()
        Mass.SetInputData(cleaner.GetOutput())
        Mass.Update()

        return Mass.GetVolume()
    
    def CollectTerritoryInfo(self):
        Volume = 0
        IndexMBF_sum = 0
        MBF_sum = 0
        self.TerritoryTags = ""
        for (key, item) in self.Labels.items():
            if self.args.TerritoryTag in key:
                self.TerritoryTags += os.path.splitext(key)[0] + "+"
                territory_ = ThresholdInBetween(self.MBF, "TerritoryMaps", int(item), int(item))
                Volume += self.CalculateVolume(ExtractSurface(territory_))

                index_mbf_ = vtk_to_numpy(territory_.GetPointData().GetArray("IndexMBF"))
                IndexMBF_sum += np.sum(index_mbf_)

                mbf_ = vtk_to_numpy(territory_.GetPointData().GetArray("ImageScalars"))
                MBF_sum += np.sum(mbf_)
        return Volume, MBF_sum, IndexMBF_sum
    
    def main(self):
        self.Normalize()
        Volume, MBF_sum, IndexMBF_sum = self.CollectTerritoryInfo()
        Volume_mL = Volume/1000
        print("MBF:", Volume_mL * MBF_sum)
        print("IndexMBF:", Volume_mL * IndexMBF_sum)
        ofile_path = f"./{os.path.splitext(os.path.basename(self.args.InputMBFMap))[0]}_MBFxVolume_{self.args.TerritoryTag}.dat"
        with open(ofile_path, "w") as ofile:
            ofile.writelines("Territory Tags:\n")
            ofile.writelines(f"{self.TerritoryTags}\n")
            ofile.writelines(f"MBFxVolume = {Volume * MBF_sum}")
            ofile.writelines(f"IndexMBFxVolume = {Volume * IndexMBF_sum}")
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputMBFMap", "--InputMBFMap", dest = "InputMBFMap", type = str, required = True)
    parser.add_argument("-InputLabel", "--InputLabel", dest = "InputLabel", type= str, required= True)
    parser.add_argument("-ArrayName", "--ArrayName", dest = "ArrayName", type = str, required = False, default = "ImageScalars")
    parser.add_argument("-TerritoryTag", "--TerritoryTag", type= str, required=True, dest = "TerritoryTag")
    args = parser.parse_args()
    
    MBFNormalization(args).main()