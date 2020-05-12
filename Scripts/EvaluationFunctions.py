# -*- coding: utf-8 -*-
"""

    EvaluationFunctions.py
    
    GAP Habitat Map Evaluation Functions

Created on Thu Apr  9 15:36:06 2020

@author: mjrubino
"""




############################################################################################
def GDFforPts(sc, sid, req, fltr, dbDir):
    '''
     This function opens a GeoPandas Dataframe directly from a SQLite db
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
     
     INPUTS:
         sc = GAP 6-letter species code
         sid = species_id from parameters database
         req = a request id from parameters database
         fltr = a filter id from parameters database
         dbDir = a path to the species point database
     OUTPUTS:
         geodataframe of point occurrence geometries as points and buffer polygons
    '''
    import pandas as pd
    import geopandas as gpd
    import glob
    import sqlite3
    import numpy as np
    
    print('\nWorking on the Following Species Code:',sc)
    print('\n  Opening Point Buffer Geometries into a GeoPandas Dataframe ....')
    
    dbname = sid + req + fltr
    db = glob.glob(dbDir + f"{dbname}.sqlite")[0]
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
    # After further consideration, I decided to assume that Nathan's repo
    # functions code was sufficient to filter duplicates even though he uses
    # the occurrence timestamp column in GBIF which can be unique by seconds
    # or minutes. I would have used day, month, year columns to assess uniqueness
    #dfPts = df.sort_values('coordinateUncertaintyInMeters').drop_duplicates(subset=['longitude', 'latitude'], keep='first')
    dfPts = df #dfPts.reset_index()
    
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
    return gdfPtBuffs

############################################################################################

def MaskHabMap(gdf, HabMap, habval):
    '''
     This function masks an input species habitat raster with buffer polygons
     extracted from an input Pandas Geodataframe and calculates stats needed
     for the evaluation metrics. Those stats are stored in a dataframe for
     further manipulation and plotting. Any point buffers that do not overlap
     with the species raster are stored in another dataframe for later
     examination and potential point occurrence data and GAP species range
     differences.
     
     INPUTS:
         gdf = Geopandas dataframe of points and point buffer polygons
         HabMap = species habitat raster of 1s and 0s **Important**
         habval = cell value indicating suitable habitat in species raster
     OUTPUTS:
         dfHabStats = dataframe of point buffer-raster overlap statistics
         dfNonOverlaps = dataframe of point buffer-raster non-overlaps
   
    '''
    
    import pandas as pd
    import geopandas as gpd
    import rasterio
    import rasterio.mask
    from shapely.geometry import mapping

    # Make an empty final habitat/non-habitat stats list
    statslst = []
    statcols = ['BufferDist','nCellsHab',
            'nCellsNon','nCells',
            'PropHab','PropNonHab']
    dfHabStats = None
    
    # Make an empty list of non-overlapping buffers
    nonlst = []
    noncols = ['OccID','BufferDist']
    dfNonOverlaps = None
    
    
    # Get the geometry values of the point buffer polygons
    geoms = gdf.poly_buff.values
    
    # Loop over each point buffer to mask the species habitat raster
    print('  Masking species habitat map with each point buffer ....')
    for i in gdf.index:
    
        # Select a single point buffer from an index value in dataframe geometries
        buff = [mapping(geoms[i])]
    
        # Get the buffer distance value
        dist = gdf.at[i,'buff_dist']
    
        try:
    
            # Mask with the species habitat map raster
            with rasterio.open(HabMap) as habras:
                mask_arr, mask_transform = rasterio.mask.mask(habras, buff, crop=True)
            '''
            Here is a way to count the number of habitat cells in a species raster
            using rasterio and numpy. It takes a while because it loads the raster
            as a numpy array to do the counting
            import rasterio
            import numpy as np
            # read in the raster using rasterio
            ras = rasterio.open(HabMap)
            band1 = ras.read(1) # this is the returned array from band 1 of the raster
            habcnt = np.count_nonzero(band1 == 1)
            
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
    
        except ValueError:
            print('   Buffer does not overlap with species habitat raster')
            # Assemble info on the buffers that did not overlap into a dataframe
            oid = gdf.at[i,'occ_id']
            nonlst.append([oid,dist])
            dfNonOverlaps = pd.DataFrame(nonlst, columns=noncols)
    
   
    # Make the DataFrame by using the appended raster data list and export to CSV
    print("\n\nCreating DataFrame dfHabStats")
    dfHabStats = pd.DataFrame(statslst, columns=statcols)
    
    if dfHabStats is not None and dfNonOverlaps is not None:
        # Return both dataframes in a dictionary
        return {'HabStats':dfHabStats, 'NonOverlaps':dfNonOverlaps}
    elif dfHabStats is not None and dfNonOverlaps is None:
        # Return only the hab stats dataframe in a dictionary
        return {'HabStats':dfHabStats}
    elif dfHabStats is None and dfNonOverlaps is not None:
        # Return only the non-overlaps dataframe in a dictionary
        return {'NonOverlaps':dfNonOverlaps}


############################################################################################
def SensCalcs(dfHS, prophab):
    '''
     This function calculates Sensitivity statistics for 7 preset buffer
     categories including p-values generated using a one-sided binomial
     test at each buffer distance. The output dataframe is used for plotting
     the Buffer Sensitivity Metric graphic.
     
     INPUTS:
         dfHS = a dataframe of habitat stats for point buffer-raster overlaps
         prophab = a species specific proportion of habitat amount across
                   the species range as predicted by the habitat model
     OUTPUTS:
         dataframe of buffer sensitivity stats with binomial test p-values
    '''
    import pandas as pd
    from scipy import stats
    

    statlst = []
    buffcats = [30,100,500,1000,2000,5000,10000]
    plotcols = ['BufferCat','TruePos','FalseNeg','Sensitivity','nPts','p-Value']
    
    
    print('\nLooping over 7 buffer distance categories to get sensitivity plot data ...')
    # Loop over each buffer distance category to generate data for sensitivity plot
    for c in buffcats:
        # Subset the dataframe by buffer distance category
        df = dfHS[dfHS['BufferDist'] <= c]
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
    return dfSens


############################################################################################
def PlotBPA(pbmean, prophab, nRecs, pth, sc, res=None):
    '''
    This function plots the Buffer Proportion Assessment metric graphic for a
    given species habitat map evaluation. It saves the figure as a PNG file
    in the specified location.

    INPUTS:
        pbmean = mean proportion of habitat in buffers
        prophab = proportion habitat in range
        nRecs = number of occurrence records
        pth = path location to store the output figure image
        sc = GAP species code to use in the output filename
        res = DPI resolution of output image (default is None)
    ----------
    OUTPUTS:
        An image file of the plot stored in the given path location


    '''
    import math
    from scipy import stats
    import matplotlib.pyplot as plt
    import numpy as np
    import os

    
    #colors = np.random.rand()
    
    fig, ax = plt.subplots(figsize=(8,8))
    # Set axes limits and labels
    ax.set_xlim(0,1)
    ax.set_ylim(0,1)
    ax.set_xlabel("Proportion Habitat in Range")
    ax.set_ylabel("Mean Proportion Habitat in Point Buffers")
    ax.set_title('Buffer Proportion Assessment - {0}'.format(sc))
    
    # Draw a y=x line to illustrate 'better than random'
    # and 'worse than random' parts of the plot
    ax.plot([0,1],[0,1], transform=ax.transAxes, c='dimgray')
    # Plot prop. hab in range on x and mean prop. hab in buffers on y
    # and a standard deviation 'error' line
    # Use the number of records for the species for the marker size
    ax.scatter(prophab, pbmean, s=nRecs, c='forestgreen', alpha=0.5)
    #ax.errorbar(prophab, pbmean, yerr=pbsd, marker='o', c='forestgreen', ms=math.sqrt(nRecs), alpha=0.5)
    
    # Save the plot as an image file
    print('\nSaving BPA figure')
    fn = pth + f'{sc}-BPA.png'
    # Remove any existing files first
    if os.path.exists(fn):
        os.remove(fn)
    plt.savefig(fname=fn, dpi=res)
    plt.close()


############################################################################################

def PlotBSM(df, pth, sc, res=None):
    '''
    This function plots the Buffer Sensitivity Metric graphic for a given
    species habitat evaluation. It saves the plot as a PNG file in the
    specified location.

    INPUTS:
        df = dataframe of Sensitivity statistics for buffer categories
        pth = path location to store the output figure image
        sc = GAP species code to use in the output filename
        res = DPI resolution of output image (default is None)
    ----------
    OUTPUTS:
        An image file of the plot stored in the given path location


    '''
    import math, os
    from scipy import stats
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, ax1 = plt.subplots(figsize=(10,8))
    ax2 = ax1.twinx()
    # Get the maximum number of occurrence points to set the right y limit in plot
    nmax = df['nPts'].max()
    ymax = 10**(int(np.log10(nmax))+1)
    # Set data and parameters for each set of axes NOTE: axis 2 draws last i.e. on top
    ln = ax2.plot(df['BufferCat'].astype(str), df['Sensitivity'], marker='o', label='Sensitivity')
    br = ax1.bar(df['BufferCat'].astype(str), df['nPts'], color='steelblue', label='Number of Points')
    br2 = ax1.bar(df['BufferCat'].astype(str), df['TruePos'], color='lightblue', label='True Positives')
    ax2.yaxis.tick_left()
    ax1.yaxis.tick_right()
    
    ax2.set_ylim(0,1.1)
    ax1.set_ylim(0,ymax)
    
    ax1.set_xlabel("Buffer Distance Category (m)")
    ax1.set_ylabel("Sensitiviy",labelpad=35)
    ax2.set_ylabel("Number of Occurrence Points",labelpad=35)
    ax1.set_title('Sensitivity by Buffer Distance - {0}'.format(sc))
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
    
    pvals = df['p-Value']
    plabel(ax1,br,pvals,'center')
    #plt.show()
    
    # Save the plot as an image file
    print('\nSaving BSM figure')
    fn = pth + f'{sc}-BSM.png'
    # Remove any existing files first
    if os.path.exists(fn):
        os.remove(fn)
    plt.savefig(fname=fn, dpi=res)
    plt.close()

############################################################################################


