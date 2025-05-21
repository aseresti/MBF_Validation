import os
import vtk
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from utilities import ReadVTUFile, ThresholdInBetween
from NormalizeMBFMap import MBFNormalization
from vtk.util.numpy_support import vtk_to_numpy

class PlotMBFVariabilityPerTerritory():
    def __init__(self, args):
        args.InputFolder = os.path.dirname(args.InputMBF)
        args.InputLabels = f"{os.path.splitext(args.InputMB)[0]}_Labels.dat"
        self.args = args
        self.MBF = ReadVTUFile(self.args.InputMBF)

    def ReadMBFLabels(self):
        MBF_Labels = {"LAD": [], "LCx":[], "Intermedius":[], "Diag":[], "PDA":[], "PL":[]}

        with open(self.InputLabels, "r") as ifile:
            for LINE in ifile:
                line = LINE.split()
                for key in MBF_Labels.keys():
                    if line[1].find(key)>=0: MBF_Labels[key].append(int(line[0]))

        MBF_Labels = {k:v for k, v in MBF_Labels.items() if len(v)>0}
        return MBF_Labels

    def ExtractMBFData(self, MBFMap, MBF_Labels, ArrayName = 0):
        MBF_data = {}
        Territories = {}
        for key, value in MBF_Labels.items():
            MBF_data[key] = np.array([])
            AppendTerritory = vtk.vtkAppendFilter()
            for i in value:
                territory_ = ThresholdInBetween(MBFMap, "TerritoryMaps", i, i)
                AppendTerritory.AddInputData(territory_)
                AppendTerritory.Update()
                MBF_ = vtk_to_numpy(territory_.GetPointData().GetArray(ArrayName))
                MBF_data[key] = np.append(MBF_, MBF_data[key])
            Territories[key] = AppendTerritory.GetOutput()
        
        return MBF_data, Territories

    def BoxPlot(self):
        pass

    def ConvertPointDataToCellData(self, pointdata):
        PointToCell = vtk.vtkPointDataToCellData()
        PointToCell.SetInputData(pointdata)
        PointToCell.Update()

        return PointToCell.GetOutput().GetCellData().GetScalars()
    
    def CalculateVoxelFlow(self, cell):
        pass

    def ExtractIschemicTerritoryMBFStatistics(self):
        pass

    def ExtractFlowInTerritories(self):
        pass

    def ExtractIschemicTerritoryFlowStatistics(self):
        pass

    def main(self):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-InputMBF", "--InputMBF", type= str, required= True, dest = "InputMBF")
    parser.add_argument("-ArrayName", "--ArrayName", dest= "ArrayName", default= "ImageScalars", required= False, type= str)
    parser.add_argument("-TerritoryArray", "--TerritoryArray", dest= "TerritoryArray", default= "TerritoryMap", required= False, type=str)
    parser.add_argument("-Unit", "--Unit", dest= "Unit", default= "mm", required= False, type= str)
    parser.add_argument("-TerritoryTag", "--TerritoryTag", dest="TerritoryTag", default="post", required= False, type= str)
    args = parser.parse_args()

