import os
import vtk
import numpy as np
import argparse
from utilities import ReadVTUFile, ThresholdInBetween
from NormalizeMBFMap import MBFNormalization
from vtk.util.numpy_support import vtk_to_numpy

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
    
    def ThresholdInBetween(self, Volume,arrayname,value1,value2):
        Threshold=vtk.vtkThreshold()
        Threshold.SetInputData(Volume)
        #Threshold.ThresholdBetween(value1,value2)
        Threshold.SetLowerThreshold(value1)
        Threshold.SetUpperThreshold(value2)
        #Threshold.SetThresholdFunction(ThresholdInBetween)
        Threshold.SetInputArrayToProcess(0,0,0,vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,arrayname)
        Threshold.Update()
        return Threshold.GetOutput()
    
    def ConvertPointDataToCellData(self, pointdata):
        PointToCell = vtk.vtkPointDataToCellData()
        PointToCell.SetInputData(pointdata)
        PointToCell.Update()

        return PointToCell.GetOutput()

    def CalculateCellDataFlow(self, Territory, ArrayName):
        CellData = Territory.GetCellData()
        ImageScalars = vtk_to_numpy(CellData.GetArray(ArrayName))
        NCells = Territory.GetNumberOfCells()
        TerritoryVolume = 0
        TerritoryFlow = []
        for i in range(NCells):
            cell = Territory.GetCell(i)
            cell_bounds = cell.GetBounds()
            cell_volume = abs(cell_bounds[0] - cell_bounds[1]) * abs(cell_bounds[2] - cell_bounds[3]) * abs(cell_bounds[4] - cell_bounds[5])
            TerritoryFlow.append(ImageScalars[i]*cell_volume)
            TerritoryVolume += cell_volume

        if self.args.Unit == 'mm':
            return np.array(TerritoryFlow)/1000/100, TerritoryVolume/1000, NCells
        elif self.args.Unit == 'cm':
            return np.array(TerritoryFlow)/100, TerritoryVolume, NCells

    def ExtractCellDataSubtendedTerritory(self, MBF, ArrayName):
        SubtendedFlow = 0
        self.TerritoryTags = ""
        NCells = 0
        TerritoryVolume = 0
        for (key, item) in self.Labels.items():
            if self.args.TerritoryTag in key:
                self.TerritoryTags += os.path.splitext(key)[0] + "+"
                territory_ = self.ThresholdInBetween(MBF, "TerritoryMaps", int(item), int(item))
                flow_, volume_, nCells = self.CalculateCellDataFlow(territory_, ArrayName)
                SubtendedFlow += np.sum(flow_)
                NCells += nCells
                TerritoryVolume += volume_
        
        return SubtendedFlow, NCells, TerritoryVolume

    def main(self):
        SubtendedFlow, NCells = self.ExtractSubtendedTerritory(self.MBF, self.args.ArrayName)
        NormalizedSubtendedFlow = SubtendedFlow/NCells

        IndexMBF = MBFNormalization(self.args).Normalize(self.MBF)
        IndexFlow, _ = self.ExtractSubtendedTerritory(IndexMBF, "IndexMBF")
        NormalizedIndexFlow = IndexFlow/NCells

        #CellData
        SubtendedFlow2, NCells2, TerritoryVolume = self.ExtractCellDataSubtendedTerritory(self.ConvertPointDataToCellData(self.MBF), self.args.ArrayName)
        NormalizedSubtendedFlow2 = SubtendedFlow2/NCells2

        IndexFlow2, _, _ = self.ExtractCellDataSubtendedTerritory(self.ConvertPointDataToCellData(IndexMBF), "IndexMBF")
        NormalizedIndexFlow2 = IndexFlow2/NCells2
        print(self.TerritoryTags)
        print("Number of Cells per territory: ", NCells, NCells2)
        print("--- MBF Flow:")
        print("----- Point Data:")
        print("Territory Flow = ", int(SubtendedFlow*1000)/1000, "mL/min")
        print("Average Flow = ", int(NormalizedSubtendedFlow*1000*1000)/1000, "\u00b5L/min/Voxel")
        print("----- Cell Data:")
        print("Territory Volume = ", int(TerritoryVolume*1000)/1000, "mL")
        print("Territory Flow = ", int(SubtendedFlow2*1000)/1000, "mL/min")
        print("Average Flow = ", int(NormalizedSubtendedFlow2*1000*1000)/1000, "\u00b5L/min/Voxel")

        print("--- Index MBF Flow:")
        print("----- Point Data:")
        print("Territory Index Flow = ", int(IndexFlow*1000)/1000, "1/min")
        print("Average Index Flow = ", int(NormalizedIndexFlow*1000000*1000)/1000, "\u00b5/min/Voxel")
        print("----- Cell Data:")
        print("Territory Index Flow = ", int(IndexFlow2*1000)/1000, "1/min")
        print("Average Index Flow = ", int(NormalizedIndexFlow2*1000000*1000)/1000, "\u00b5/min/Voxel")

        ofile_path = f"./{os.path.splitext(os.path.basename(self.args.InputMBF))[0]}_MBFxVolume_{self.args.TerritoryTag}.dat"
        with open(ofile_path, "w") as ofile:
            ofile.writelines("Territory Tags:\n")
            ofile.writelines(f"{self.TerritoryTags}\n")
            ofile.writelines(f"Number of voxels in territory: {NCells}\n")
            ofile.writelines("PPINT DATA: \n")
            ofile.writelines("-"*10)
            ofile.writelines("\n")
            ofile.writelines("MBF Flow:\n")
            ofile.writelines(f"Territory Flow: {int(SubtendedFlow*1000)/1000} mL/min\n")
            ofile.writelines(f"Average Flow per Voxel: {int(NormalizedSubtendedFlow*1000*1000)/1000} \u00b5L/min/Voxel\n")
            ofile.writelines("-"*10)
            ofile.writelines("\n")
            ofile.writelines("Index MBF Flow:\n")
            ofile.writelines(f"Territory Index Flow: {int(IndexFlow*1000)/1000}  1/min\n")
            ofile.writelines(f"Average Index Flow per Voxel: {int(NormalizedIndexFlow*1000000*1000)/1000} \u00b5/min/Voxel")
            ofile.writelines("\n\nCELL DATA: \n")
            ofile.writelines("-"*10)
            ofile.writelines("\n")
            ofile.writelines("MBF Flow:\n")
            ofile.writelines(f"Territory Flow: {int(SubtendedFlow2*1000)/1000} mL/min\n")
            ofile.writelines(f"Average Flow per Voxel: {int(NormalizedSubtendedFlow2*1000*1000)/1000} \u00b5L/min/Voxel\n")
            ofile.writelines("-"*10)
            ofile.writelines("\n")
            ofile.writelines("Index MBF Flow:\n")
            ofile.writelines(f"Territory Index Flow: {int(IndexFlow2*1000)/1000}  1/min\n")
            ofile.writelines(f"Average Index Flow per Voxel: {int(NormalizedIndexFlow2*1000000*1000)/1000} \u00b5/min/Voxel")
            ofile.writelines(f"Territory Volume: {int(TerritoryVolume*1000)/1000} mL")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputMBF", "--InputMBF", dest= "InputMBF", type= str, required= True)
    #parser.add_argument("-InputLabel", "--InputLabel", dest= "InputLabel", type= str, required= True)
    parser.add_argument("-ArrayName", "--ArrayName", dest = "ArrayName", type = str, required = False, default = "ImageScalars")
    parser.add_argument("-TerritoryTag", "--TerritoryTag", type= str, required=True, dest = "TerritoryTag")
    parser.add_argument("-Unit", "--Unit", type= str, dest= "Unit", default="mm", required=False)
    args = parser.parse_args()
    
    ExtractSubtendedFlow(args).main()
