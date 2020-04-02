# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 13:08:30 2020

@author: mjrubino
"""

'''

                                BPA-BSM.py


    This script generates the Buffer Point Assessment (BPA) and
    Buffer Sensitivity Metric (BSM) used to evaluate species habitat maps.
    It assumes that a shapefile of point occurrence locations has already
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


    The outputs include:
        Pandas dataframe of habitat stats within point occurrence buffers
        Pandas dataframe of summarized habitat metrics
        Figures for illustrating BPA and BSM made using matplotlib

    Version = Python 3.6

'''
# git token: 73728fba00352368f0a86f895e207b58fff494a3

import rasterio
import rasterio.mask
from shapely.geometry import mapping
import sqlite3
import pandas as pd
import geopandas as gpd
import numpy as np
from datetime import datetime
import math
from scipy import stats
import matplotlib.pyplot as plt
import glob



pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 100)

t0 = datetime.now()

# Directory variables
# Macbook specific
#workDir = '/Users/matthewrubino/GAP-Habitat-Map-Assessment/'
# Windows specific
workDir = "D:/USGS Analyses/GAP-Habitat-Map-Assessment/"
dbDir = workDir + 'Outputs/'
sppDir = 'P:/Proj3/USGap/Vert/Model/Output/CONUS/01/Any/'

# This TIF raster is a 0-1 species habitat map. It assumes that all habitat
# cells in the raster are 1s and all non-habitat cells are 0s. If different
# habitat TIFs are used, the code will need to be altered.
HabMap = sppDir + f'{sppcode}_CONUS_01A_2001v1.tif'
#HabMap = sppDir + '{0}_CONUS_HabMap_2001v1.tif'.format(sppcode)

# The variable prophab is the proportion of habitat in the species range estimated
# by the habitat model. It is compared with the mean proportion of habitat within
# point buffers - BPA. It is also used in a binomial test of each buffer distance
# sensitivity measurement (true positive fraction) of occurrence points with at
# least one (or >= proportion habitat in range threshold) habitat cell within the
# coordinate uncertainty buffer area - BSM
sppcode = 'aBESAx'
prophab = 0.040

# Using the occurrence db naming convention, set a variable using
# the species code in the designated db that was searched
# This is the 'species_id' in the species_concept table
# 
paramdb = workDir + 'db/' + 'wildlife-wrangler.sqlite'
conn = sqlite3.connect(paramdb, isolation_level='DEFERRED')
dfPdb = pd.read_sql_query("SELECT species_id FROM species_concepts", conn)
# Get a list of the species IDs that contain the species code
idlist = [i for i in dfPdb['species_id'] if sppcode.lower() in i]
print('The parameters db has the following list of species IDs containing the species code',sppcode,':\n')
for sid in idlist:
    print(sid)
s = input('Enter the species ID you would like to run: ')
while s not in idlist:
    print('That species ID is not in the list.')
    s = input('Enter a valid ID: ')

print('You are running the following species ID: ' + s)
species_id = s
del s
conn.close()

# Suitable habitat raster value
# For original GAP habitat map rasters values are seasonal:
#  1 = summer only
#  2 = winter only
#  3 = year-round
# NOTE: these values could be altered to just 1s if all seasons are used
habval = 1


print('\nWorking on the Following Species Code:',sppcode)
print('\n  Opening Point Buffer Geometries into a GeoPandas Dataframe ....')

'''
 This uses a point buffer shapefile as the data source

# Open the point buffer shapefile with GeoPandas
gdfPtBuffs = gpd.read_file(shpBuff)
# Extract the geometries in GeoJSON format
geoms = gdfPtBuffs.geometry.values
'''

'''
 This opens a GeoPandas Dataframe directly from a SQLite db
 located in the workDir/db directory and pulls out 4 columns
 from the 'occurrences' table:
   occ_id,
   longitude,
   latitude,
   coordinateUncertaintyInMeters
 A geometery column is created using each record's latitude and longitude
 and then resets the CRS from WGS84 (EPSG:4326) to Albers EA (EPSG:5070)
 Another column is created (buff_dist) to set buffer distance for each point
 with a minimum of 30 meters based on coordinate uncertainty.
'''

db = glob.glob(dbDir + f"{species_id}*.sqlite")[0]
conn = sqlite3.connect(db, isolation_level='DEFERRED')
# Bring the occurrence id, latitude and longitude, and coordinate uncertainty
# in the species SQLite db into a Pandas dataframe
# Set the column data types using a dictionary
dtdict = {'occ_id':'str','longitude':'float','latitude':'float',
          'coordinateUncertaintyInMeters':'int16'} 

df = pd.read_sql_query("SELECT occ_id, longitude, latitude, \
                        coordinateUncertaintyInMeters FROM occurrences", conn)

df = df.astype(dtdict)
# Some duplicate points may have gotten through. Keep the ones with
# the lowest coordinate uncertainty.
dfPts = df.sort_values('coordinateUncertaintyInMeters').drop_duplicates(subset=['longitude', 'latitude'], keep='first')
dfPts = dfPts.reset_index()

# Bring the lat-longs into a geometry for GeoPandas
gdf = gpd.GeoDataFrame(dfPts, geometry=gpd.points_from_xy(dfPts.longitude, dfPts.latitude),
                       crs="EPSG:4326")

# Reset the CRS to EPSG:5070
gdfPtBuffs = gdf.to_crs("EPSG:5070")

# Make a new polygon geometry column of point buffers using coordinate uncertainty
# --> Point buffers must be a minimum of 30 meters for proper overlay with species raster
#     so make a new column 'buff_dist' with all values < 30 as 30
gdfPtBuffs['buff_dist'] = np.where(gdfPtBuffs.coordinateUncertaintyInMeters < 30, 30,
                                gdfPtBuffs.coordinateUncertaintyInMeters)
gdfPtBuffs['poly_buff'] = gdfPtBuffs.apply(lambda row:
                                     row.geometry.buffer(row.buff_dist),
                                     axis=1)
# Get the geometry values of the point buffer polygons
geoms = gdfPtBuffs.poly_buff.values

# Make an empty final habitat/non-habitat stats list
statslst = []
statcols = ['BufferDist','nCellsHab',
        'nCellsNon','nCells',
        'PropHab','PropNonHab']

# Make an empty list of non-overlapping buffers
nonlst = []
noncols = ['OccID','OrigIndex','BufferDist']


# Loop over each point buffer to mask the species habitat raster
print('  Masking species habitat map with each point buffer ....')
for i in gdfPtBuffs.index:

    # Select a single point buffer from an index value in dataframe geometries
    buff = [mapping(geoms[i])]

    # Get the buffer distance value
    dist = gdfPtBuffs.at[i,'buff_dist']

    try:

        # Mask with the species habitat map raster
        with rasterio.open(HabMap) as habras:
            mask_arr, mask_transform = rasterio.mask.mask(habras, buff, crop=True)

        # Get the count of the number of habitat cells: habval variable set above
        cnt1 = len(mask_arr[mask_arr==habval])
        # Get the count of the number of non-habitat cells: in this case = 0
        cnt0 = len(mask_arr[mask_arr==0])
        # Get the total number of cells in the point buffer mask
        ncells = cnt0 +  cnt1
        # Get the proportion of habitat and non-habitat in the point buffer
        propHab = (cnt1/ncells)
        propNon = (cnt0/ncells)
        # Append to the stats list
        statslst.append([dist,cnt1,cnt0,ncells,propHab,propNon])

    except ValueError:
        print('   Buffer does not overlap with species habitat raster')
        # Assemble info on the buffers that did not overlap into a dataframe
        oid = gdfBuffs401.at[i,'occ_id']
        idx = gdfBuffs401.at[i,'index']
        nonlst.append([oid,idx,dist])
        dfNonOverlaps = pd.DataFrame(nonlst, columns=noncols)




# Make the DataFrame by using the appended raster data list and export to CSV
print("\n\nCreating DataFrame dfHabStats")
dfHabStats = pd.DataFrame(statslst, columns=statcols)

print("\n\n~~~~~~~~~ DONE ~~~~~~~~~~")


statlst = []
buffcats = [30,100,500,1000,2000,5000,10000]
plotcols = ['BufferCat','TruePos','FalseNeg','Sensitivity','nPts','p-Value']


print('\nLooping over 7 buffer distance categories to get sensitivity plot data ...')
# Loop over each buffer distance category to generate data for sensitivity plot
for c in buffcats:
    # Subset the dataframe by buffer distance category
    df = dfHabStats[dfHabStats['BufferDist'] <= c]
    # Calculate buffer category sensitivity stats
    n = len(df)
    if n > 0:
        # Count 'habitat presence' as anything not 0 in hab cell count
        fn = df.loc[df['nCellsHab'] == 0, 'nCellsHab'].count()
        tp = n - fn
        # Count 'habitat presence' using a threshold (prop hab in range)
        #tp = df.loc[df['PropHab'] >= prophab, 'nCellsHab'].count()
        #fn = n - tp
        sens = tp / n
    else:
        tp = 0
        fn = 0
        sens = 0
    # Calculate an exact one-sided binomial test for each buffer distance
    p = stats.binom_test(tp, n=n, p=prophab, alternative='greater')
    if p < 0.0001:
        pv = "< 0.0001"
    else:
        pv = "= " + str(round(p,4))
    # Add to the stats list
    statlst.append([c,tp,fn,sens,n,pv])

# Make the final dataframe of the sensitivity stats
dfSens = pd.DataFrame(statlst, columns=plotcols)



#################################### Start plotting BPA #######################################################
print('\n\n','>'*35, 'BPA and BSM PLOTS', '<'*35)
# Get the mean proportion of habitat in point buffers and its standard deviation
pbmean = round(dfHabStats['PropHab'].mean(),3)
pbsd = round(dfHabStats['PropHab'].std(),3)
nRecs = len(dfHabStats)

#colors = np.random.rand()

fig, ax = plt.subplots(figsize=(8,8))
# Set axes limits and labels
ax.set_xlim(0,1)
ax.set_ylim(0,1)
ax.set_xlabel("Proportion Habitat in Range")
ax.set_ylabel("Mean Proportion Habitat in Point Buffers")
ax.set_title('Buffer Proportion Assessment - {0}'.format(sppcode))

# Draw a y=x line to illustrate 'better than random'
# and 'worse than random' parts of the plot
ax.plot([0,1],[0,1], transform=ax.transAxes, c='dimgray')
# Plot prop. hab in range on x and mean prop. hab in buffers on y
# and a standard deviation 'error' line
# Use the number of records for the species for the marker size
#ax.scatter(prophab, pbmean, s=nRecs, c=colors, alpha=0.5)
ax.errorbar(prophab, pbmean, yerr=pbsd, marker='o', c='forestgreen', ms=math.sqrt(nRecs), alpha=0.5)

#################################### Start plotting BSM #######################################################

fig, ax1 = plt.subplots(figsize=(10,8))
ax2 = ax1.twinx()
# Get the maximum number of occurrence points to set the right y limit in plot
nmax = dfSens['nPts'].max()
ymax = 10**(int(np.log10(nmax))+1)
# Set data and parameters for each set of axes NOTE: axis 2 draws last i.e. on top
ln = ax2.plot(dfSens['BufferCat'].astype(str), dfSens['Sensitivity'], marker='o', label='Sensitivity')
br = ax1.bar(dfSens['BufferCat'].astype(str), dfSens['nPts'], color='steelblue', label='Number of Points')
br2 = ax1.bar(dfSens['BufferCat'].astype(str), dfSens['TruePos'], color='lightblue', label='True Positives')
ax2.yaxis.tick_left()
ax1.yaxis.tick_right()

ax2.set_ylim(0,1.1)
ax1.set_ylim(0,ymax)

ax1.set_xlabel("Buffer Distance Category (m)")
ax1.set_ylabel("Sensitiviy",labelpad=35)
ax2.set_ylabel("Number of Occurrence Points",labelpad=35)
ax1.set_title('Sensitivity by Buffer Distance - {0}'.format(sppcode))
# Make a single legend for both axes plots
lb = ln+[br]+[br2]
labs = [l.get_label() for l in lb]
ax2.legend(lb, labs, loc='upper left', fontsize=12)
bars, labels = ax1.get_legend_handles_labels()

# Define a function that will insert p-values above each bar of buffer categories
# The p-values are taken from the dfSens dataframe and represent a test of
# significance using an exact one-sided binomial test of number of TPs and
# total number of points used in each buffer category
def plabel(a, rects, pvalue, xpos='center'):
    """
    Attach a text label above each bar.

    *xpos* indicates which side to place the text with respect to
    the center of the bar. It can be one of the following:
    {'center', 'right', 'left'}.
    
    parameters:
    a = matplotlib axis to plot on
    rects = the rectangles representing the bars in the chart
    pvalue = the label values to insert
    xpos = center, right, left postion
    """

    xpos = xpos.lower()  # normalize the case of the parameter
    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

    for i, rect in enumerate(rects):
        height = rect.get_height()
        a.text(rect.get_x() + rect.get_width()*offset[xpos], 1.0*height,
                r'$p {}$'.format(pvalue[i]), ha=ha[xpos], va='bottom')

pvals = dfSens['p-Value']
plabel(ax1,br,pvals,'center')

plt.show()

t1 = datetime.now()
print("+++++ Processing time was", t1 - t0, '+++++')
