import os
import vtk
import argparse
from TubeFilter import *
from ConvertPathtoVTP import ConvertPath2VTP



class ExtractLumenSegmentation():
    def __init__(self,Args):
        self.Args = Args
        self.Image = Read_vtk_image(self.Args.InputImage)

    def main(self):
        Lumen_points = ConvertPath2VTP(self.Args).main()
        Lumen_tube = dict()
        for _, (vessel, points) in enumerate(Lumen_points.items()):
            print(f"Segmenting {vessel}")
            path = os.path.join(self.Args.InputFolder, f"{vessel}.vtu")
            volume1 = None
            for point in points:
                SphereOutput = SphereClip(self.Image, point, 0.3)
                volume1 = AppendVolume(volume1, SphereOutput)
            volume1 = self.ExtractLumen(volume1)
            WriteVTUFile(path, volume1)
            exit(1)
            dict[vessel] = volume1

    def ExtractLumen(self, volume):
        lumen_gradient = ThresholdByUpper(volume,"Magnitude",4000)
        return lumen_gradient


    
if __name__=="__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("-InputFolder", "--InputFolder", dest="InputFolder", type=str, required=True)
    Parser.add_argument("-InputImage", "--InputImage", dest="InputImage", required=True, type=str)
    args = Parser.parse_args()

    ExtractLumenSegmentation(args).main()
