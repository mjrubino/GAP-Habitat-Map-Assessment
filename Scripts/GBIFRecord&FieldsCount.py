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

sppList=['Coccyzus americanus']
#sppList = config.LessThan30000



# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

'''
    Function to write an error log if a species' occurrence records
    server connection cannot be made - i.e. a 5xx number error.
'''
log = workDir + 'Species-Data-Access-Error-Log.txt'
def Log(content):
    with open(log, 'a') as logDoc:
        logDoc.write(content + '\n')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
    Function to assemble GBIF occurrences for a given species
'''
def GetGBIF(spp):
    
    # Make an empty dataframe with required field names using an empty dictionary
    df0 = pd.DataFrame()
    
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

        eor = recs['endOfRecords']
        tablelst = tablelst + recs['results']
        n+=300
        
    # Make a dataframe out of the compiled lists
    df = pd.DataFrame(data=tablelst)
    # Append it to the empty dataframe
    dfAppended = df0.append(df, ignore_index=True, sort=False)
    return dfAppended

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++




# Make an empty list to append each species' records
reclst = []
# Make column names for the list
lstcols = ['SppName','nRecords','maxFields']


n = 0
# Loop over each species in the full species list in the config file
for sp in sppList:
    
    try:
        print('Working on the following species:', sp, '....')
        dfSppRecs = GetGBIF(sp)
        ncols = len(dfSppRecs.columns)
        nrecs = len(dfSppRecs)
        # Append to the records list
        reclst.append([sp,nrecs,ncols])
    except:
        print('   Had problems connecting to GBIF.\n\
           Writing species name to error log and moving to next species...')
        Log(sp)




# Make a dataframe out of the compiled lists and save as CSV
dfRecordCount = pd.DataFrame(data=reclst, columns=lstcols)
dfRecordCount.to_csv(workDir + "SpeciesOccurrenceCounts-GBIF.csv")

#del reclst,lstcols,spp,recs,cnt,dfRecordCount

endTime = datetime.now(); procDelta = endTime - beginTime
print("\n\nProcessing time = " + str(procDelta) + "\n")
print('*'*35,'DONE','*'*35)