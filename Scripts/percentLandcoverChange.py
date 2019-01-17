##import needed modules
import os, sys, arcpy, csv

from arcpy import env  
from arcpy.sa import *

## check out spatial analyst extension
arcpy.CheckOutExtension("Spatial")

## enable overwriting of outputs from tools
arcpy.env.overwriteOutput = 1

##  set workspace, current working directory
arcpy.env.workspace = "Y:\\mrlc"
os.chdir(arcpy.env.workspace)

##  set zone polygons, landcover change raster
hucs = "P://Proj3//USGap//Ancillary//hucs//huc12rng_gap//polygon"
changeRaster = "Y://mrlc//change_pixels//nlcd_2001_to_2006_landcover_change_pixels_2011_edition_2014_10_10//nlcd_2001_to_2006_landcover_change_pixels_2011_edition_2014_10_10.img"

##  reclassify landcover change raster so that changed pixels = 1, unchanged = 0 and 127 (representing no data) = NoData
rc = Reclassify(changeRaster,"Value",RemapRange([[0,0,0],[1,95,1],[96,127,"NODATA"]]), "NODATA")
##  perform zonal mean on landcover change reclass, resulting in floating point raster which represents percent change
zm = ZonalStatistics(hucs, "HUC12RNG", rc, "MEAN", "DATA")
##  integerize and round zonal mean raster
int = Int((zm * 100) + .5)

##  convert input zone polygons to points, forcing inside
arcpy.FeatureToPoint_management(hucs,"huc12_pts","INSIDE")

##  extract integer raster values to points for zone polygons
ExtractValuesToPoints(arcpy.env.workspace + "\\huc12_pts.shp",int,"huc12_pts_pc.shp","NONE","ALL")

##  The following function that creates a csv file from an attribute table.
##  Looks like it was written by Glen Bambrick, and can be found at:
##  https://glenbambrick.com/2016/12/05/table-feature-class-to-csv/

def tableToCSV(input_tbl, csv_filepath):
    fld_list = arcpy.ListFields(input_tbl)
    fld_names = [fld.name for fld in fld_list]
    with open(csv_filepath, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(fld_names)
        with arcpy.da.SearchCursor(input_tbl, fld_names) as cursor:
            for row in cursor:
                writer.writerow(row)
        print csv_filepath + " CREATED"
    csv_file.close()

fc = r"huc12_pts_pc2.shp"
out_csv = r"huc12_changes.csv"

tableToCSV(fc, out_csv)

arcpy.Delete("huc12_pts.shp")
