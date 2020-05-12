# Import modules
import arcpy
import pandas as pd
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

# Set Environments and variables
workDir = 'C:/Data/temp/AccuracyMockup/'
tmpDir = workDir + 'tmp/'
randDir = workDir + 'random/'
shpBuff = workDir + 'PointBuffers.shp'
HabMap = workDir + 'BESA.tif'
# The percent habitat in range threshold for simulated landscape
percHabThr = 0.024

arcpy.env.overwriteOutput = True
env.extent = HabMap

# Iterate over a pre-defined number of simulations
i = 1
while i in range(25):
    # Execute CreateRandomRaster
    print("Creating Random Raster ....")
    outRandomRaster = CreateRandomRaster(30, HabMap)
    # Create simulated habitat landscape using a percentage
    # of habitat in range value based on a species' habitat map
    print("Creating Simulated Habitat Map ....\n")
    outSimHab = outRandomRaster <= percHabThr
    # Save the output
    outSimHab.save(randDir + 'SimulatedHab{0}.tif'.format(i))
    i+=1

print("\n +++++++++++++ DONE +++++++++++++")
