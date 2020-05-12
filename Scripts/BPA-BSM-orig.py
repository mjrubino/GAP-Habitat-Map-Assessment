# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 13:08:30 2020

@author: mjrubino
"""

'''

                                BPA-BSM.py


    This script generates the Buffer Point Assessment (BPA) and
    Buffer Sensitivity Metric (BSM) used to evaluate species habitat maps.
    It assumes that a database of point occurrence locations has already
    been generated and that a species habitat TIF raster map of 0-1s is
    available to be masked by point buffers created using coordinate
    uncertainty values from the occurrence location source (i.e. GBIF).



    All spatial operations are performed with open source software for Python
    including:

        RasterIO - version 1.1.0 or higher
        Shapely - version 1.6.4 or higher
        GDAL - version 3.0.2 or higher
        GeoPandas - version 0.4.1 or higher
        libtiff - version 4.10.0 or higher

        NOTE: Processing with RasterIO requires the ability to handle BigTIFF
        files for species with large habitat extents. GDAL must be version 3
        or higher, RasterIO must be version 1 or higher and the libtiff library
        must be version 4 or higher. Inability to handle large TIFFs will cause
        errors in code execution.
        
    It uses functions stored in the EvaluationFunctions.py file
    which needs to be loaded in with sys.path.append.
    
    It also uses an input file - EvaluationRuns.csv - that holds all info
    for running evaluations species by species. Necessary columns include:
        SpeciesCode = GAP 6-letter species code
        SpeciesID = species ID from the Wrangler parameters db
        RequestID = request ID from the Wrangler parameters db
        FilterID = filter ID from the Wrangler parameters db
        PropHab = proportion of habitat in range for given species
        HabCellValue = raster cell value in species habitat raster


    The outputs include:
        Pandas dataframe of habitat stats within point occurrence buffers
        Pandas dataframe of summarized habitat metrics
        Figures for illustrating BPA and BSM made using matplotlib

    Version = Python 3.6

'''
# git token: 73728fba00352368f0a86f895e207b58fff494a3

import sqlite3
import pandas as pd
from datetime import datetime
import glob
import sys, os



pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 100)

t0 = datetime.now()

# Directory variables
# Macbook specific
#workDir = '/Users/matthewrubino/GAP-Habitat-Map-Assessment/'
# Windows specific
workDir = "D:/USGS Analyses/GAP-Habitat-Map-Assessment/"
dbDir = workDir + 'Outputs/'
inputDir = workDir + 'Inputs/'
figDir = workDir + 'figures/'
sppDir = 'P:/Proj3/USGap/Vert/Model/Output/CONUS/01/Any/'
codeDir = workDir + 'Scripts/'

sys.path.append(codeDir)

# Import the habitat map evaluation functions in the code directory
import EvaluationFunctions as ef

# The habitat evaluation file to loop over. It contains the needed
# values for reading the occurrence database:
    # the species ID
    # the request ID
    # the filter ID
# as well as the species GAP code
# the species proportion of habitat in range
# the species raster cell value indicating suitable habitat

evalFile = inputDir + 'EvaluationRuns.csv'
dfEvals = pd.read_csv(evalFile)

print('\nReading in species evaluation list', evalFile, ' ....\n')

for i in dfEvals.index:
    
    # Read in the GAP code
    gapcode = dfEvals.at[i,'SpeciesCode']
    # Read in the species ID, filter ID and reques ID from the parameters db
    sppid = dfEvals.at[i,'SpeciesID']
    req = dfEvals.at[i,'RequestID']
    fltr = dfEvals.at[i,'FilterID']
    
    # The variable prophab is the proportion of habitat in the species range estimated
    # by the habitat model. It is compared with the mean proportion of habitat within
    # point buffers - BPA. It is also used in a binomial test of each buffer distance
    # sensitivity measurement (true positive fraction) of occurrence points with at
    # least one (or >= proportion habitat in range threshold) habitat cell within the
    # coordinate uncertainty buffer area - BSM
    prophab = dfEvals.at[i,'PropHab']
    # Suitable habitat raster value
    # For original GAP habitat map rasters values are seasonal:
    #  1 = summer only
    #  2 = winter only
    #  3 = year-round
    # NOTE: these values could be altered to just 1s if all seasons are used
    habval = int(dfEvals.at[i,'HabCellValue'])
    

    # This TIF raster is a 0-1 species habitat map. It assumes that all habitat
    # cells in the raster are 1s and all non-habitat cells are 0s. If different
    # habitat TIFs are used, the code will need to be altered.
    HabMap = sppDir + f'{gapcode}_CONUS_01A_2001v1.tif'
    
    
    '''
      Prior to running the evalutation for a species, check to make
      sure there is a database with the given request and filter.
      If not, skip that species-request-filter combination.
    
    '''
    sppdb = dbDir + sppid + req + fltr + '.sqlite'
    if os.path.exists(sppdb):
        print('\nSpecies Occurrence Database Exists for ' + gapcode)
        print('Continuing With Habitat Map Evaluation')

        # Conduct habitat map evaluation using functions below
        
        # Get the occurrence points and buffers into a GeoDataframe
        gdfOcc = ef.GDFforPts(sc=gapcode, sid=sppid, req=req, fltr=fltr, dbDir=dbDir)
        
        # Mask the species habitat raster with occurrence point buffers
        # First make sure there is a habitat stats dataframe
        try:
            
            d = ef.MaskHabMap(gdf=gdfOcc, HabMap=HabMap, habval=habval)
            if 'HabStats' in d:
                dfHabStats = d['HabStats']
                # Get the mean proportion of habitat in point buffers
                # and its standard deviation and number of records
                pbmean = round(dfHabStats['PropHab'].mean(),3)
                pbsd = round(dfHabStats['PropHab'].std(),3)
                nRecs = len(dfHabStats)
                # Save the hab stats to a file
                # Remove an older version if it exists
                fn = workDir + f'HabStats/{gapcode}-HabStats.csv'
                if os.path.exists(fn):
                    os.remove(fn)
                dfHabStats.to_csv(fn, sep=',')
            if 'NonOverlaps' in d:
                dfNonOverlaps = d['NonOverlaps']
                # Save the non-overlaps to a file
                # Remove any previous versions
                nofn = workDir + f'db/{gapcode}-NonOverlaps.csv'
                if os.path.exists(nofn):
                    os.remove(nofn)
                dfNonOverlaps.to_csv(nofn, sep=',')
            
            # Calculate Sensitivity metrics
            dfSens = ef.SensCalcs(dfHS=dfHabStats, prophab=prophab)
            
            # Plot Buffer Proportion Assessment and output an image file
            ef.PlotBPA(pbmean=pbmean, prophab=prophab, nRecs=nRecs, pth=figDir, sc=gapcode)
            
            # Plot Buffer Sensitivity Metric and output an image file
            ef.PlotBSM(df=dfSens, pth=figDir, sc=gapcode)
        except KeyError:
            print('!!!! No Masking Output !!!!')
    else:
        print('\n---> No Species Occurrence Database for ' + gapcode)
        print('Moving To Next Species-Request-Filter Combination')
    print('+'*70)




t1 = datetime.now()
print("\n+++++ Processing time was", t1 - t0, '+++++')

