'''

    Scripting for rasterizing a point buffer shapefile
    and intersecting it with a 30m habitat map to calculate
    the proportion of habitat and non-habitat cells within
    each point's buffer radius.
    
    Version = Python 2.7

'''

# Import modules
import arcpy
import os, shutil
import pandas as pd
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

# Set Environments and variables
snapgrid = "D:/Vert/Model/data/snapgrid"
arcpy.env.overwriteOutput = True
arcpy.env.snapRaster = snapgrid


sppcode = 'mBTJAx'
workDir = 'C:/Data/temp/AccuracyMockup/'
csvDir = workDir + 'csv/'
tmpDir = workDir + 'tmp/'
sppDir = workDir + 'species/'
shpBuff = workDir + '{0}_GBIF_Buffered.shp'.format(sppcode)
HabMap = sppDir + '{0}.tif'.format(sppcode)

# Make temporary directory for buffer shapefiles
#  remove it if it already exists
print('----- Removing Temporary Directory -----\n\n')
if os.path.exists(tmpDir):
    shutil.rmtree(tmpDir)
    os.mkdir(tmpDir)
else:
    os.mkdir(tmpDir)

# Set field names for looping and data extraction
idfld = 'FID'
distfld = 'BufferDist'
flds = [idfld,distfld]

# Make an empty final habitat/non-habitat stats list
statslst = []
statcols = ['BufferDist','nCellsHab',
        'nCellsNon','nCells',
        'PropHab','PropNonHab']

# Start looping over the point buffer shapefile's table
# Loop using the FID field and Precision field
# set a counter for iterative naming
i = 0
for row in arcpy.da.SearchCursor(shpBuff, flds):
    i+=1
    recid = int(row[0])  # make sure these fields are integers
    dist = int(row[1])   # 'row' is a tuple

    # Make individual buffer polygons into features using FID
    exp = "\"FID\" = {0}".format(recid)
    outshp = str(dist) + "_" + str(recid) + ".shp"
    print("Working on output shapefile named " + outshp + " ....")
    arcpy.FeatureClassToFeatureClass_conversion(shpBuff, tmpDir, outshp, exp)

    # Rasterize individual buffer polygons
    print("   Rasterizing buffer polygon ...")
    rasBuff = tmpDir + "rasBuffer"
    arcpy.FeatureToRaster_conversion(tmpDir + outshp, "CellVal", rasBuff, 30)
    # Add the rasterized buffer with the habitat map to generate
    # the number of cells with and without habitat within the buffer
    roHabBuff = Raster(rasBuff) + Raster(HabMap)

    # make an empty list and set column names
    tablelst = []
    tablecols = ['freq','value']
    
    # loop through the raster table to create a dataframe
    rasrows = arcpy.SearchCursor(roHabBuff)
    for r in rasrows:
        frequency = r.getValue("COUNT")
        value = r.getValue("VALUE")
        tablelst.append([frequency,value])
    # make the table a dataframe using the appended list
    dftable = pd.DataFrame(tablelst,columns=tablecols)

    # now calculate cell counts and proportions of habitat and non-habitat
    habcells = float(dftable.loc[dftable['value'] == 1, 'freq'].sum())
    nonhabcells = float(dftable.loc[dftable['value'] == 0, 'freq'].sum())
    ncells = habcells + nonhabcells
    propHab = (habcells/ncells)
    propNon = (nonhabcells/ncells)
    statslst.append([dist,habcells,nonhabcells,ncells,propHab,propNon])



    # Delete objects
    print("   Deleting temp objects ...")
    del recid,dist,exp,outshp,roHabBuff,tablelst,rasrows,r,frequency,value
    arcpy.Delete_management(rasBuff)



# Make the DataFrame by using the appended raster data list and export to CSV
print("\n\nExporting DataFrame to CSV File")
dfHabStats = pd.DataFrame(statslst, columns=statcols)
dfHabStats.to_csv(csvDir + "HabStats-{0}.csv".format(sppcode))

print("\n\n~~~~~~~~~ DONE ~~~~~~~~~~")
        
