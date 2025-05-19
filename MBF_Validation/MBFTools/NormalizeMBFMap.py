import os
import vtk
import numpy as np
import argparse
from utilities import ReadVTUFile, WriteVTUFile, ThresholdInBetween, ExtractSurface
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

class MBFNormalization():
    def __init__(self, args):
        self.args = args
        self.MBF = ReadVTUFile(os.path.join(self.args.InputFolder,self.args.InputMBFMap))
        labels = os.path.join(self.args.InputFolder,self.args.InputLabel)
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
        MedianMBF =np.array([])
        self.TerritoryTags = ""
        for (key, item) in self.Labels.items():
            if self.args.TerritoryTag in key:
                territory_ = ThresholdInBetween(self.MBF, "TerritoryMaps", int(item), int(item))
                if territory_.GetNumberOfPoints() > 0:
                    self.TerritoryTags += os.path.splitext(key)[0] + "+"
                    Volume += self.CalculateVolume(ExtractSurface(territory_))

                    index_mbf_ = vtk_to_numpy(territory_.GetPointData().GetArray("IndexMBF"))
                    IndexMBF_sum += np.sum(index_mbf_)

                    mbf_ = vtk_to_numpy(territory_.GetPointData().GetArray("ImageScalars"))
                    MBF_sum += np.sum(mbf_)

                    MedianMBF = np.append(MedianMBF, mbf_)
        return Volume, MBF_sum, IndexMBF_sum, MedianMBF
        
    def main(self):
        self.Normalize()
        Volume, MBF_sum, IndexMBF_sum, MedianMBFArray = self.CollectTerritoryInfo()
        MBF50 = np.median(MedianMBFArray)
        MBF75 = np.percentile(MedianMBFArray, 75)
        Volume_mL = Volume/1000
        print("MBF:", Volume_mL * MBF_sum)
        print("IndexMBF:", Volume_mL * IndexMBF_sum)
        print("Median MBF:", Volume_mL * MBF50)
        print("75th percentile MBF: ", Volume_mL * MBF75)
        ofile_path = f"./{os.path.splitext(os.path.basename(self.args.InputMBFMap))[0]}_MBFxVolume_{self.args.TerritoryTag}.dat"
        with open(ofile_path, "w") as ofile:
            ofile.writelines("Territory Tags:\n")
            ofile.writelines(f"{self.TerritoryTags}\n")
            ofile.writelines(f"MBF x Volume = {Volume * MBF_sum}")
            ofile.writelines(f"IndexMBF x Volume = {Volume * IndexMBF_sum}")
            ofile.writelines(f"MedianMBF x Volume = {Volume_mL * MBF50}")
            ofile.writelines(f"75th percentile MBF x Volume = {Volume_mL * MBF75}")
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputFolder", "--InputFolder", dest= "InputFolder", type= str, required= True)
    parser.add_argument("-InputMBFMap", "--InputMBFMap", dest = "InputMBFMap", type = str, required = False, default= "MBF_Territories.vtu")
    parser.add_argument("-InputLabel", "--InputLabel", dest = "InputLabel", type= str, required= False, default="MBF_Territories_Labels.dat")
    parser.add_argument("-ArrayName", "--ArrayName", dest = "ArrayName", type = str, required = False, default = "ImageScalars")
    parser.add_argument("-TerritoryTag", "--TerritoryTag", type= str, required=True, dest = "TerritoryTag")
    args = parser.parse_args()
    
    MBFNormalization(args).main()