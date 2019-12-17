# -*- coding: utf-8 -*-
"""
Created on Fri May  3 11:36:04 2019

@author: mjrubino
"""

# Import modules
import pandas as pd
from pygbif import occurrences as occ
from pygbif import species
import os

# Local variables
workDir = 'C:/Data/USGS Analyses/GAP-Habitat-Map-Assessment/'
tempDir = workDir + 'temp/'

os.chdir(workDir)

import config
sppList = config.sciNames1719

df0 = pd.DataFrame()


reclst =[]
lstcols=['ScienticName','nRecords']

print('+'*60)
print('\n')

for spp in sppList:
    print('Working on the following species:', spp)
    # First use the species module to get the taxonKey for a species scientific name
    tkey = species.name_backbone(name = spp, rank='species')['usageKey']
    # Gather the occurrences dictionary using the appropriate criteria
    recs = occ.search(taxonKey=tkey, 
                      hasCoordinate=True,
                      country='US',
                      geoSpatialIssue=False)

    if 'count' in recs:
        cnt = recs['count']
        print('  This species has', cnt, 'records')
    else:
        print('  This species has an UNKNOWN RECORD COUNT')
        cnt = -99
    reclst.append([spp,cnt])

print('+'*60)

# Make a dataframe out of the compiled lists and save as CSV
dfRecordCount = pd.DataFrame(data=reclst, columns=lstcols)
dfRecordCount.to_csv(workDir + "SpeciesRecordCountGBIF.csv")