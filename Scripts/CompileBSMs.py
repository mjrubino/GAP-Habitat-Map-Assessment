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
import matplotlib.pyplot as plt
import seaborn as sns

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
'''
statslst = []
cols=['SppCode','30m','100m','500m','1000m','2000m','5000m','10000m']
'''
# Make a master dataframe to hold all species sensitivity values
dfAllSens = pd.DataFrame()

for i in dfList.index:
    print('Reading in Habitat Statistics for', dfList.at[i,'SciName'])
    # Read in the GAP species code
    gapcode = dfList.at[i,'SpeciesCode']
    # Get a path to the hab stats file using species code
    hsfile = statsDir + f'{gapcode}-HabStats.csv'
    # Open the species hab stats csv as a dataframe if it exists
    if os.path.exists(hsfile):
        dfHS = pd.read_csv(hsfile)
        # Use the SensCalcs function to get a sensitivity dataframe
        # for the species. The proportion habitat parameter is meaningless here
        dfSens = ef.SensCalcs(dfHS=dfHS, prophab=0.010)
        
        # Pull out the buffer category and their sensitivity values
        df0 = dfSens[['BufferCat','Sensitivity']]
        # Concatenate it to the master dataframe
        dfAllSens = pd.concat([df0, dfAllSens], axis=0)
        
        '''
        # Get the sensitivity values as a list
        slst = list(dfSens['Sensitivity'])
        # Add the species code to this list
        slst = [gapcode] + slst

        # Append stats to the list
        statslst.append(slst)
        '''
    else:
        print('No Hab Stats CSV for GAP Code',gapcode)
        print('Moving on...')
    
# Make the stats list a dataframe
#print('\nWriting list to Pandas Dataframe\n')
#dfAllSens = pd.DataFrame(statslst, columns=cols)
#dfm = pd.melt(dfProp, id_vars=[''],var_name='month', value_name='data')

'''
    Plot box plots for each buffer category using Seaborn
'''

fig, ax = plt.subplots(figsize=(10,6))
#plt.xticks(rotation=45)
a = sns.boxplot(data = dfAllSens,
                x = 'BufferCat',
                y = 'Sensitivity',
                color='white',
                showmeans=True,
                medianprops={'color':'red'},
                meanprops={'marker':'d',
                           'markeredgecolor':'tab:blue',
                           'markerfacecolor':'tab:blue'},
                width=0.5,
                ax=ax)
a.set_xlabel('Buffer Distance Category', fontsize=12)
a.set_ylabel('Sensitivity', fontsize=12)
a.set_title('Sensitivity Measures for All Species', fontsize=16)

plt.show()

# Save figure output as image file
print('\nSaving BSM figure')
fn = figDir + 'All-Species-BSM.png'
# Remove any existing files first
if os.path.exists(fn):
    os.remove(fn)
fig.savefig(fname=fn,res=None)
plt.close()

print('++++++++++++++++++++ DONE +++++++++++++++++++')



