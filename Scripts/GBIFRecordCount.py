# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 15:16:19 2019

@author: mjrubino
"""

# Import modules
import pandas as pd
from pygbif import occurrences as occ
from pygbif import species

import sys
sys.path.append('C:/Data/USGS Analyses/GAP-Habitat-Map-Assessment/')
import config
from datetime import datetime

workDir = 'C:/Data/USGS Analyses/GAP-Habitat-Map-Assessment/'

beginTime = datetime.now()
print("*"*40); print('Began ' + str(beginTime)); print("*"*40)

sppList=['Accipiter cooperii','Myodes gapperi']

# Make an empty list to append each species' records
reclst = []
# Make column names for the list
lstcols = ['SppName','nRecords']


n = 0
# Loop over each species in the full species list in the config file
for spp in config.sciNames1590:
    
    print('Working on the following species:', spp)
    recs = occ.search(scientificName = spp,
                      hasCoordinate=True,
                      country='US', 
                      geoSpatialIssue=False)
    # Not all species have COUNT in their occurrence record dictionary
    # !!!!!!!!! WHAT THE FUCK GBIF !!!!!!!!!!!!!!!
    # Make sure it does otherwise make it 0.9
    if 'count' in recs:
        cnt = recs['count']
        n = n + cnt
        print('  it has', cnt, 'records')
    else:
        print('  it has UNKNOWN NUMBER of records',)
        cnt = 0.9
    # Append to the record list
    reclst.append([spp,cnt])


print('\n   TOTAL NUMBER OF RECORDS FOR THIS SPECIES LIST =',n)

# Make a dataframe out of the compiled lists and save as CSV
dfRecordCount = pd.DataFrame(data=reclst, columns=lstcols)
dfRecordCount.to_csv(workDir + "SpeciesOccurrenceCounts-GBIF.csv")

del reclst,lstcols,spp,recs,cnt,dfRecordCount

endTime = datetime.now(); procDelta = endTime - beginTime
print("\n\nProcessing time = " + str(procDelta) + "\n")
print('*'*35,'DONE','*'*35)