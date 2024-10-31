#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 16 12:04:22 2023
Updated on Wed Jun 12 2024

The purpose of this script is to take the dicom file of the CT images and convert them into vti
images. User needs to specify the number of volumes in the stack of images refered to as NofCycle.
If the image stack is CTA the NofCycel is 0.

@author: aseresti@github.com
"""

import glob
import os
import argparse


class ConvertDicomtoVTI():
    def __init__(self,Args):
        self.Args = Args
    
    def convert(self,DCM1:str,OutputPath:str)->None:
        os.system(f'vmtkimagereader -ifile {DCM1} --pipe vmtkimagewriter -ofile {OutputPath}')
    
    
    def main(self):
        filenames = glob.glob(f'{self.Args.InputFolderName}/*.dcm')
        filenames = sorted(filenames)
        
        if self.Args.NumberOfCycles == 0:
            print("Converting CTA DCM data into vti")
            self.convert(filenames[0],"./CTAImage.vti")
        else:
            self.N_file_per_cycle = int(len(filenames)/self.Args.NumberOfCycles)
            for i in range(0,self.Args.NumberOfCycles):
                print("Converting CT-MPI DCM data into vti")
                directoryname = f'perfusion_image_cycle_{i+1}'
                pathDicom = f'{self.Args.InputFolderName}/{directoryname}'
                os.system(f"mkdir {pathDicom}")
                for j in range((i)*self.N_file_per_cycle,(i+1)*self.N_file_per_cycle-1):
                    os.system(f'cp {filenames[j]} {pathDicom}')
            
                print(f'--- Looping over cycle: {i}')
                filenames_ = glob.glob(f'{pathDicom}/*.dcm')
                filenames_ = sorted(filenames_)
                self.convert(filenames_[0], f'{self.Args.InputFolderName}/Cycle_Image_{i+1}.vti')
            

if __name__ == '__main__':
    #descreption
    parser = argparse.ArgumentParser(description='Thsi script takes a dicom folder with N cycles and outputs an averaged vti image')
    #Input
    parser.add_argument('-InputFolder', '--InputFolder', type = str, required = True, dest = 'InputFolderName', help = 'The name of the folder with all of the dicom files')
    #NumberOfCycles
    parser.add_argument('-NofCycle', '--NumberOfCycles', type = int, required = True, dest = 'NumberOfCycles', help = 'The number of perfusion images that are in the dicom folder. if CTA put 0')
    args = parser.parse_args()
    ConvertDicomtoVTI(args).main()
