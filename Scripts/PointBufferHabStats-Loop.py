'''

    Scripting for rasterizing a point buffer shapefile
    and intersecting it with a 30m habitat map to calculate
    the percentage of habitat and non-habitat cells within
    each point's buffer radius.
    
    PYTHON 2.7  -- required when running ArcPy 10.x
    

'''

# Import modules
import arcpy
import pandas as pd
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

# Set Environments and variables
arcpy.env.overwriteOutput = True

workDir = 'C:/Data/temp/AccuracyMockup/'
tmpDir = workDir + 'tmp/'
randDir = workDir + 'random/'
shpBuff = workDir + 'PointBuffers.shp'
HabMap = workDir + 'BESA.tif'


# Set field names for looping and data extraction
idfld = 'FID'
distfld = 'Precision'
flds = [idfld,distfld]

# Make an empty final habitat/non-habitat stats list
statslst = []
statcols = ['HabMap','BufferDist','nCellsHab',
        'nCellsNon','nCells',
        'PercentHab','PercentNonHab']

# Loop over the simulated habitat rasters in the 'random' directory
arcpy.env.workspace = randDir
sims = arcpy.ListRasters()

for ras in sims:

    print("\n");print("+")*40
    print("Using Simulated Landscape Raster{0} ....".format(ras))
    # Get the simulated habitat raster name
    simName = ras[0:-4]

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
        rasBuff = tmpDir + "rasBuffer"
        arcpy.FeatureToRaster_conversion(tmpDir + outshp, "Id", rasBuff, 30)
        # Add the rasterized buffer with the habitat map to generate
        # the number of cells with and without habitat within the buffer
        roHabBuff = Raster(rasBuff) + Raster(ras)

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

        # now calculate cell counts and percentages of habitat and non-habitat
        habcells = float(dftable.loc[dftable['value'] == 1, 'freq'].sum())
        nonhabcells = float(dftable.loc[dftable['value'] == 0, 'freq'].sum())
        ncells = habcells + nonhabcells
        percHab = (habcells/ncells) * 100
        percNon = (nonhabcells/ncells) * 100
        statslst.append([simName,dist,habcells,nonhabcells,ncells,percHab,percNon])



        # Delete objects
        print("   Deleting temp objects ...\n")
        del recid,dist,exp,outshp,roHabBuff,tablelst,rasrows,r,frequency,value
        arcpy.Delete_management(rasBuff)



# Make the DataFrame by using the appended raster data list and export to CSV
print("\n\nExporting DataFrame to CSV File - Hab-NonHabStats-SimulatedMaps.csv")
dfHabStats = pd.DataFrame(statslst, columns=statcols)
dfHabStats.to_csv(workDir + "Hab-NonHabStats-SimulatedMaps.csv")

print("\n\n~~~~~~~~~ DONE ~~~~~~~~~~")
        
