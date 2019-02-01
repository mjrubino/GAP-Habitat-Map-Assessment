# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 10:10:40 2019

@author: mjrubino
"""
# Import modules
import pandas as pd
from pygbif import occurrences as occ

# Local variables
workDir = 'C:/Data/USGS Analyses/GAP-Habitat-Map-Assessment/'
tempDir = workDir + 'temp/'

spp='Blarina carolinensis'

df0 = pd.DataFrame()

print('Working on the following species:', spp)
# Make an empty list to store data iterations
tablelst = []
n = 0
eor = False
# Because the pyGBIF occurrences module returns only 300 records at a time,
# loop through all the records for a given species until its
# reached the end of the records, i.e. endOfRecords is True
while eor == False:
    # Gather the occurrences dictionary using the appropriate criteria
    recs = occ.search(scientificName = spp, 
                       hasCoordinate=True,
                       country='US',
                       geoSpatialIssue=False,
                       offset=n) #geoSpatialIssue=False
    # Not all species have COUNT in their occurrence record dictionary
    # !!!!!!!!! WHAT THE FUCK GBIF !!!!!!!!!!!!!!!
    # If it does, print the count, otherwise print UNKNOWN RECORD COUNT
    if 'count' in recs:
        cnt = recs['count']
        print('  This species has', cnt, 'records')
    else:
        #cnt = 0.9
        print('  This species has an UNKNOWN RECORD COUNT')
    eor = recs['endOfRecords']
    tablelst = tablelst + recs['results']
    n+=300
    
# Make a dataframe out of the compiled lists
df = pd.DataFrame(data=tablelst)
# Append it to the empty dataframe
dfAppended = df0.append(df, ignore_index=True, sort=False)
print('Exporting occurrence records to CSV....')
dfAppended.to_csv(tempDir + "GBIF-{0}.csv".format(spp))
dfIssuesCol = dfAppended[['issues']]