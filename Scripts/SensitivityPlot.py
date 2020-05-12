# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 08:50:46 2020

@author: mjrubino
"""

import pandas as pd
import numpy as np
import math
from scipy import stats
import matplotlib.pyplot as plt


pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 100)

####### Path locations ##################################
workDir = 'C:/Data/temp/AccuracyMockup/'
csvDir = workDir + 'csv/'


# The variable prophab is the proportion of habitat in the species range estimated
# by the habitat model. It is used in a binomial test of each buffer distance
# sensitivity measurement (true positive fraction) of occurrence points with at
# least one (or >= proportion habitat in range threshold) habitat cell within the
# coordinate uncertainty buffer area
sppcode = 'bWHSOx'
prophab = 0.137

statlst = []
buffcats = [30,100,500,1000,2000,5000,10000]
plotcols = ['BufferCat','TruePos','FalseNeg','Sensitivity','nPts','p-Value']


dfSppCSV = pd.read_csv(csvDir + 'HabStats-' + sppcode + '.csv')

print('\nLooping over 7 buffer distance categories to get sensitivity plot data ...\n')
# Loop over each buffer distance category to generate data for sensitivity plot
for c in buffcats:
    # Subset the dataframe by buffer distance category
    df = dfSppCSV[dfSppCSV['BufferDist'] <= c]
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

# Get the mean proportion of habitat in point buffers and its standard deviation
pbmean = round(dfSppCSV['PropHab'].mean(),3)
pbsd = round(dfSppCSV['PropHab'].std(),3)
nRecs = len(dfSppCSV)

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
ln = ax2.plot(dfSens['BufferCat'].astype(str), dfSens['Sensitivity'], marker='o')
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







