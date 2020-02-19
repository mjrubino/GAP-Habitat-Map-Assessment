# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 13:08:30 2020

@author: mjrubino
"""

'''

        BPA-BSM-from-PointBuffer-Shapefile.py


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


import rasterio
import rasterio.mask
from shapely.geometry import mapping
import pandas as pd
import geopandas as gpd
import numpy as np
from datetime import datetime
import math
from scipy import stats
import matplotlib.pyplot as plt



pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 100)

t0 = datetime.now()

# Set some variables

# The variable prophab is the proportion of habitat in the species range estimated
# by the habitat model. It is compared with the mean proportion of habitat within
# point buffers - BPA. It is also used in a binomial test of each buffer distance
# sensitivity measurement (true positive fraction) of occurrence points with at
# least one (or >= proportion habitat in range threshold) habitat cell within the
# coordinate uncertainty buffer area - BSM
sppcode = 'aBESAx'
prophab = 0.040
# Suitable habitat raster value
# For original GAP habitat map rasters values are seasonal:
#  1 = summer only
#  2 = winter only
#  3 = year-round
# NOTE: these values could be altered to just 1s if all seasons are used
habval = 3

# Directory variables
workDir = 'C:/Data/temp/AccuracyMockup/'
sppDir = workDir + 'species/'
# This is a pre-defined shapefile of occurrence points buffered using each
# records coordinate uncertainty. This is input to a GeoPandas dataframe in
# this workflow. If this spatial data is created using other processes and 
# IS NOT a shapefile, this code will need to be altered.
shpBuff = workDir + '{0}_GBIF_Buffered.shp'.format(sppcode)
# This TIF raster is a 0-1 species habitat map. It assumes that all habitat
# cells in the raster are 1s and all non-habitat cells are 0s. If different
# habitat TIFs are used, the code will need to be altered.
#HabMap = sppDir + '{0}.tif'.format(sppcode)
HabMap = sppDir + '{0}_CONUS_HabMap_2001v1.tif'.format(sppcode)


# Make an empty final habitat/non-habitat stats list
statslst = []
statcols = ['BufferDist','nCellsHab',
        'nCellsNon','nCells',
        'PropHab','PropNonHab']

print('\nWorking on the Following Species Code:',sppcode)
print('\n  Opening Point Buffer Shapefile into a GeoPandas Dataframe ....')
# Open the point buffer shapefile with GeoPandas
gdfPtBuffs = gpd.read_file(shpBuff)
# Extract the geometries in GeoJSON format
geoms = gdfPtBuffs.geometry.values

# Loop over each point buffer to mask the species habitat raster
print('  Masking species habitat map with each point buffer in the shapefile ....')
for i in gdfPtBuffs.index:
    
    # Select a single point buffer from an index value in the GeoJSON geometries
    buff = [mapping(geoms[i])]
    
    # Get the buffer distance value
    dist = gdfPtBuffs.at[i,'BUFF_DIST']
    
    # Mask with the species habitat map raster
    #kwargs.update(BIGTIFF="IF_SAFER")
    #with rasterio.open(HabMap, "r", **kwargs) as habras:
    with rasterio.open(HabMap) as habras:
        mask_arr, mask_transform = rasterio.mask.mask(habras, buff, crop=True)
        mask_meta = habras.meta
        
    # Create a rasterized version of the point buffer polygon
    b = geoms[i]
    xdiff = b.bounds[2] - b.bounds[0]
    ydiff = b.bounds[3] - b.bounds[1]
    rows = int(math.ceil(xdiff/30))
    cols = int(math.ceil(ydiff/30))
    '''
    shpgen = [(shape, 3) for shape in gdfPtBuffs['geometry']]
    transform = rasterio.transform.from_bounds(*df['geometry'].total_bounds, *shape)
    ma = rasterio.enums.MergeAlg
    mask = rasterio.features.rasterize(b, out_shape=(rows,cols),
                                       fill=0,
                                       merge_alg=ma.replace,
                                       dtype=np.uint8
                                        )
    '''
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
    # Count 'habitat presence' as anything not 0 in hab cell count
    fn = df.loc[df['nCellsHab'] == 0, 'nCellsHab'].count()
    tp = n - fn
    # Count 'habitat presence' using a threshold (prop hab in range)
    #tp = df.loc[df['PropHab'] >= prophab, 'nCellsHab'].count()
    #fn = n - tp
    sens = tp / n
    # Calculate an exact one-sided binomial test for each buffer distance
    p = stats.binom_test(tp, n=n, p=prophab, alternative='greater')
    if p < 0.0001:
        pv = "< 0.0001"
    else:
        pv = str(round(p,4))
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

ax2.set_ylim(0,1)
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

plt.show()

t1 = datetime.now()
print("+++++ Processing time was", t1 - t0, '+++++') 


