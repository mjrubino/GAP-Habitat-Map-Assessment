# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 10:00:52 2020

@author: mjrubino
"""

import pandas as pd
from pygbif import occurrences

gbif_id=2428130 #aCATRx# #2422858 = aAGTOx
years='1999,2020'
months='1,12'
latRange=''
lonRange=None
geoIssue=False
coordinate=True
country='US'
poly=None

occ = occurrences.search(gbif_id,
							year=years,
							month=months,
							decimalLatitude=latRange,
							decimalLongitude=lonRange,
							hasGeospatialIssue=geoIssue,
							hasCoordinate=coordinate,
							country=country,
							geometry=poly)

print('Number of records returned =', occ['count'])
#del occ
res = occ['results']


# Here is Nathan's code in the repo functions that is causing errors
# List of informative df columns/dictionary keys to keep (used later)
keeper_keys = ['basisOfRecord', 'individualCount', 'scientificName',
               'decimalLongitude', 'decimalLatitude',
               'coordinateUncertaintyInMeters',
               'eventDate', 'issue', 'issues', 'gbifID', 'id',
               'dataGeneralizations', 'eventRemarks', 'locality',
               'locationRemarks', 'collectionCode',
               'samplingProtocol', 'institutionCode', 'establishmentMeans',
               'institutionID', 'footprintWKT', 'identificationQualifier',
               'occurrenceRemarks', 'datasetName']
keeper_keys.sort()
dfRaw = pd.DataFrame(columns=keeper_keys)
insertDict = {}
for x in keeper_keys:
    insertDict[x] = []
for x in res:
    present_keys = list(set(x.keys()) & set(keeper_keys))
    for y in present_keys:
        insertDict[y] = insertDict[y] + [str(x[y])]
    missing_keys = list(set(keeper_keys) - set(x.keys()))
    for z in missing_keys:
        insertDict[z] = insertDict[z] + ["UNKNOWN"]
insertDF = pd.DataFrame(insertDict)
df0 = dfRaw.append(insertDF, ignore_index=True, sort=False)

df0.rename(mapper={"gbifID": "occ_id",
                           "decimalLatitude": "latitude",
                           "decimalLongitude": "longitude",
                           "eventDate": "occurrenceDate"}, inplace=True, axis='columns')
df0.drop(["issue", "id"], inplace=True, axis=1)

######## Here is where it craps out in the notebook ###########################
df0['coordinateUncertaintyInMeters'].replace(to_replace="UNKNOWN",
                                             value=None, inplace=True)
df0 = df0.astype({'coordinateUncertaintyInMeters': 'float',
                  'latitude': 'string', 'longitude': 'string'})
df0['individualCount'].replace(to_replace="UNKNOWN", value=1,
                               inplace=True)
