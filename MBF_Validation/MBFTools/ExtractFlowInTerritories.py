import os
import vtk
import numpy as np
import argparse
from utilities import ReadVTUFile, ThresholdInBetween
from NormalizeMBFMap import MBFNormalization

class ExtractSubtendedFlow():
    def __init__(self, args):
        args.InputFolder = ""
        args.InputLabels = f"{os.path.splitext(args.InputMBF)[0]}_Labels.dat"
        self.MBF = ReadVTUFile(args.InputMBF)
        self.args = args
        self.Labels = {}
        with open(args.InputLabels, "r") as ifile:
            for LINE in ifile:
                line = LINE.split()
                self.Labels[line[1]] = line[0]


    def CalculateVoxelFlow(self, Array, voxel):
        id_list = voxel.GetPointIds()
        cell_bounds = voxel.GetBounds()
        cell_volume = abs(cell_bounds[0] - cell_bounds[1]) * abs(cell_bounds[2] - cell_bounds[3]) * abs(cell_bounds[4] - cell_bounds[5])

        average_cell_mbf = 0
        for i in range(id_list.GetNumberOfIds()):
            average_cell_mbf += Array.GetValue(id_list.GetId(i))
        
        if self.args.Unit == 'mm':
            return average_cell_mbf/id_list.GetNumberOfIds()*cell_volume/1000/100
        elif self.args.Unit == 'cm':
            return average_cell_mbf/id_list.GetNumberOfIds()*cell_volume/100

    def CalculateFlowInVoluem(self, Volume, ArrayName):
        MBFScalarArray = Volume.GetPointData().GetArray(ArrayName)
        NCells = Volume.GetNumberOfCells()
        Flow = 0
        for i in range(NCells):
            voxel = Volume.GetCell(i)
            Flow += self.CalculateVoxelFlow(MBFScalarArray, voxel)
        
        return Flow, NCells
    
    def ExtractSubtendedTerritory(self, MBF, ArrayName):
        SubtendedFlow = 0
        self.TerritoryTags = ""
        NCells = 0
        for (key, item) in self.Labels.items():
            if self.args.TerritoryTag in key:
                self.TerritoryTags += os.path.splitext(key)[0] + "+"
                territory_ = ThresholdInBetween(MBF, "TerritoryMaps", int(item), int(item))
                flow_, nCells = self.CalculateFlowInVoluem(territory_, ArrayName)
                SubtendedFlow += flow_
                NCells += nCells
        
        return SubtendedFlow, NCells
    
    def main(self):
        SubtendedFlow, NCells = self.ExtractSubtendedTerritory(self.MBF, self.args.ArrayName)
        NormalizedSubtendedFlow = SubtendedFlow/NCells

        IndexMBF = MBFNormalization(self.args).Normalize(self.MBF)
        IndexFlow, _ = self.ExtractSubtendedTerritory(IndexMBF, "IndexMBF")
        NormalizedIndexFlow = IndexFlow/NCells

        print("Number of Cells per territory: ", NCells)
        print("--- MBF Flow:")
        print("Territory Flow = ", int(SubtendedFlow*1000)/1000, "mL/min")
        print("Normalized Flow = ", int(NormalizedSubtendedFlow*1000*1000)/1000, "\u00b5L/min/Voxel")

        print("--- Index MBF Flow:")
        print("Territory Index Flow = ", int(IndexFlow*1000)/1000, "1/min")
        print("Normalized Index Flow = ", int(NormalizedIndexFlow*1000000*1000)/1000, "\u00b5/min/Voxel")

        ofile_path = f"./{os.path.splitext(os.path.basename(self.args.InputMBF))[0]}_MBFxVolume_{self.args.TerritoryTag}.dat"
        with open(ofile_path, "w") as ofile:
            ofile.writelines("Territory Tags:\n")
            ofile.writelines(f"{self.TerritoryTags}\n")
            ofile.writelines(f"Number of voxels in territory: {NCells}\n")
            ofile.writelines("-"*10)
            ofile.writelines("\n")
            ofile.writelines("MBF Flow:\n")
            ofile.writelines(f"Territory Flow: {int(SubtendedFlow*1000)/1000} mL/min\n")
            ofile.writelines(f"Flow per Voxel: {int(NormalizedSubtendedFlow*1000*1000)/1000} \u00b5L/min/Voxel\n")
            ofile.writelines("-"*10)
            ofile.writelines("\n")
            ofile.writelines("Index MBF Flow:\n")
            ofile.writelines(f"Territory Index Flow: {int(IndexFlow*1000)/1000}  1/min\n")
            ofile.writelines(f"Index Flow per Voxel: {int(NormalizedIndexFlow*1000000*1000)/1000} \u00b5/min/Voxel")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputMBF", "--InputMBF", dest= "InputMBF", type= str, required= True)
    #parser.add_argument("-InputLabel", "--InputLabel", dest= "InputLabel", type= str, required= True)
    parser.add_argument("-ArrayName", "--ArrayName", dest = "ArrayName", type = str, required = False, default = "ImageScalars")
    parser.add_argument("-TerritoryTag", "--TerritoryTag", type= str, required=True, dest = "TerritoryTag")
    parser.add_argument("-Unit", "--Unit", type= str, dest= "Unit", default="mm", required=False)
    args = parser.parse_args()
    
    ExtractSubtendedFlow(args).main()
