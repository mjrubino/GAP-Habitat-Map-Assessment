# -*- coding: utf-8 -*-
"""

    Use this to make a single plot of Buffer Proportion Assessment
    for multiple species. It reads CSV files of individual species
    habitat stats stored in a directory (statsDir). It has to run
    using a file with species code, proportion habitat in range and
    scientific name in it - EvaluationList.csv in this case.
    It uses the evaluation function PlotBPA in the scripts directory
    to plot and save the scatterplot figure.



Created on Wed Apr 22 11:01:30 2020

@author: mjrubino
"""


import pandas as pd
import os, sys

pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 100)

workDir = 'D:/USGS Analyses/GAP-Habitat-Map-Assessment/'
statsDir = workDir + 'HabStats/'
codeDir = workDir + 'Scripts/'
figDir = workDir + 'figures/'

sys.path.append(codeDir)
# Import the habitat map evaluation functions in the code directory
import EvaluationFunctions as ef

sppList = workDir + 'Inputs/EvaluationList.csv'
#sppList = workDir + 'Inputs/LessThan10Species.csv'
dfList = pd.read_csv(sppList)

statslst = []
cols = ['SppCode','BuffMean','PropHab','nRecs']

for i in dfList.index:
    print('Reading in Habitat Statistics for', dfList.at[i,'SciName'])
    # Read in the GAP species code
    gapcode = dfList.at[i,'SpeciesCode']
    # Get a path to the hab stats file using species code
    hsfile = statsDir + f'{gapcode}-HabStats.csv'
    # Open the species hab stats csv as a dataframe if it exists
    if os.path.exists(hsfile):
        dfHS = pd.read_csv(hsfile)
        # Calculate the mean proportion of habitat in point buffers
        pbmean = round(dfHS['PropHab'].mean(),3)
        pbsd = round(dfHS['PropHab'].std(),3)
        nRecs = len(dfHS)
        # Get the proportion habitat in range from the file
        prophab = dfList.at[i,'PropHab']
        # Append stats to the list
        statslst.append([gapcode,pbmean,prophab,nRecs])
        
    else:
        print('No Hab Stats CSV for GAP Code',gapcode)
        print('Moving on...')
    
# Make the stats list a dataframe
print('\nWriting list to Pandas Dataframe\n')
dfProp = pd.DataFrame(statslst, columns=cols)


# Use the evaluation function PlotBPA to put all species BPAs on a single plot
print('Plotting Buffer Proportion Assessment and Creating Image File...')
ef.PlotBPA(pbmean=dfProp['BuffMean'], 
           prophab=dfProp['PropHab'], 
           nRecs=dfProp['nRecs'], 
           pth=figDir, sc='All-Species')

print('++++++++++++++++++++ DONE +++++++++++++++++++')



