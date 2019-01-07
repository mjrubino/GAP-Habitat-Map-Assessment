# -*- coding: utf-8 -*-
"""

                        GBIFSummarization.py
        
    Use this to generate Pandas dataframes (and ultimately CSVs)
    of GBIF records and summary stats of those records for a given
    list of species. GBIF records are limited to only those occurrences
    recorded within the United States and have coordinate data (lat/long).
    It uses the pyGBIF API package and the 'occurrences' module.
    Documentaion for the Python pyGBIF API package is located here:
    https://pygbif.readthedocs.io/en/latest/index.html
    
    Currently, this script uses a static species list. It would probably
    be best to implement a more dynamic approach to assemble a species
    list - i.e. from an external database, a taxa information registry, 
    or a connection to the USGS ScienceBase API.
    
    The script contains a function that summarizes information contained
    in the species occurrence records. The purpose being to allow users
    to have information regarding the amount, quality, and depth of data
    available for each species. The summary stats collected are listed
    in the documentation within code for the function. These could 
    certainly be altered to assemble more or less info useful in assessing
    species occurrence records.
    
    INPUTS: + A static (currently) species list in Python format.
    
    OUTPUT: + A Pandas dataframe compiling all GBIF occurrence records for
            the given species in the species list. It can be converted to
            a CSV file for examination outside Python.
            + A Pandas dataframe summarizing info of species' occurrences.
            It can be converted to a CSV file for examination outside Python.
    
    NOTE: Currently (4 Jan 2019) this script 'thins' GBIF fields to only those
          containing the following information:
              species scientific name
              species vernacular name
              occurrence latitude
              occurrence longitude
              coordinate uncertainty in meters
              4 fields with textual info on occurrence location
              occurrence geodetic datum
              occurrence US state or province location
              occurrence recorded year
              occurrence recorded month
              basis of record
              species taxonomic rank
              species taxonomic status
              
          It would certainly be possible to alter which fields are output
          considering there are as many as 135 fields in the GBIF datasets.
          However, many of these fields are blank for most species.

Created on Wed Dec 19 15:10:15 2018

@author: mjrubino
"""

# Import modules
import pygbif, pandas as pd
from pygbif import occurrences as occ
from pygbif import species

# Local variables
tempDir = 'C:/Data/USGS Analyses/ModelAssessment/temp/'


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#   Species list - start with it static 
#   then move toward a more robust, dynamic method - ScienceBase?

#sppList = ['Plethodon chlorobryonis','Desmognathus quadramaculatus']
sppList = ['Plethodon chlorobryonis','Desmognathus quadramaculatus','Pseudacris brimleyi',
'Taricha torosa','Hyla chrysoscelis','Plethodon idahoensis','Ambystoma californiense'
,'Lithobates areolatus','Notophthalmus viridescens','Ensatina eschscholtzii',
'Rana boylii','Anaxyrus cognatus','Ambystoma talpoideum','Spea bombifrons',
'Hyla squirella','Strix varia','Mniotilta varia','Poecile atricapillus','Thryomanes bewickii',
'Polioptila caerulea','Catharus bicknelli','Dolichonyx oryzivorus','Psaltriparus minimus',
'Polioptila californica','Catherpes mexicanus','Nucifraga columbiana','Uria aalge',
'Zonotrichia leucophrys','Parabuteo unicinctus','Mergus serrator','Archilochus colubris',
'Piranga olivacea','Sphyrapicus thyroideus','Microtus californicus',
'Pecari tajacu','Tamiasciurus douglasii','Martes pennanti','Mustela nivalis',
'Tamias speciosus','Alces americanus','Geomys bursarius','Arborimus longicaudus',
'Glaucomys volans','Sorex fumeus','Thomomys mazama','Thamnophis sauritus',
'Kinosternon subrubrum','Senticolis triaspis','Plestiodon egregius','Chrysemys picta',
'Aspidoscelis xanthonota','Nerodia clarkii','Thamnophis elegans','Pseudemys texana',
'Sceloporus jarrovii']

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
    Function to summarize data within GBIF for each species
'''

def SummaryInfo(sp, dframe):
    '''
    The dataframe returned by this function generates summary info
    into the following columns:
      SppName:        Species scientific name       
      nRecords:       Number of records for species in US with coordinates
      nCoordUncty:    Number of records with values for coordinate uncertainty
      minCoordUncty:  Lowest coordinate uncertainty
      maxCoordUncty:  Highest coordinate uncertainty
      nTextDesc:      Number of times textual location information was entered for any occurrence
      nGeoDatum:      Number of records listing geodetic datum
      nMonth:         Number of records listing a collection month
      nYear:          Number of records listing a collection year
      nSciNameRecs:   Number of records listing a latin binomial
      nComNameRecs:   Number or records listing a vernacular name
      ComNames:       Unique vernacular names for the given species' records in a Python list
      TaxRanks:       Unique taxonomic ranks for the given species' records in a Python list
      TaxStatuses:    Unique taxonomic statuses for the given species' records in a Python list
        
    The required parameters for the function are a species scientific name,
    and a Pandas dataframe containing GBIF record results for that species.
    
    '''
    
    # Make an empty list and set column names
    reclst = []
    lstcols = ['SppName','nRecords','nCoordUncty','minCoordUncty','maxCoordUncty',
               'nTextDesc',
               'nGeoDatum','nMonth','nYear',
               'nSciNameRecs','nComNameRecs','ComNames',
               'TaxRanks','TaxStatuses']
    
    # Get the number of records for species in the US with coordinates
    cntRecs = len(dframe)
    
    # Get the number of records with values for coordinate uncertainty
    # and the minimum and maximum values of uncertainty
    cntCoUn = dframe['coordinateUncertaintyInMeters'].count()
    minCoUn = dframe['coordinateUncertaintyInMeters'].min()
    maxCoUn = dframe['coordinateUncertaintyInMeters'].max()
    
    # Get the number of times textual location information was entered for any occurrence
    cntText = dframe['eventRemarks'].count() + \
              dframe['locality'].count() + \
              dframe['locationRemarks'].count() + \
              dframe['occurrenceRemarks'].count()
    
    # Get the number of records listing geodetic datum
    cntGeDa = dframe['geodeticDatum'].count()
    
    # Get the number of records listing a collection month
    cntMnth = dframe['month'].count()
    
    # Get the number of records listing a collection year
    cntYear = dframe['year'].count()
    
    # Get the number of records listing a latin binomial
    cntScNm = dframe['species'].count()
    
    # Get the number of records listing a vernacular(common) name
    cntCoNm = dframe['vernacularName'].count()
    
    # List of vernacular names
    sVNameUnique = dframe['vernacularName'].drop_duplicates()
    lstCN = list(sVNameUnique)
    # remove NaNs from this list
    lstCoNm = [el for el in lstCN if str(el) != 'nan']
    
    # List of taxonomic ranks
    sTaxRanksUnique = dframe['taxonRank'].drop_duplicates()
    lstTR = list(sTaxRanksUnique)
    # remove NaNs from the list
    lstTxRn = [el for el in lstTR if str(el) != 'nan']
    
    # List of taxonomic statuses
    sTaxStatsUnique = dframe['taxonomicStatus'].drop_duplicates()
    lstTS = list(sTaxStatsUnique)
    # remove NaNs from the list
    lstTxSt = [el for el in lstTS if str(el) != 'nan']
    

    # Append all the data into the empty list with column names
    reclst.append([sp,cntRecs,cntCoUn,minCoUn,maxCoUn,cntText,
                   cntGeDa,cntMnth,cntYear,
                   cntScNm,cntCoNm,lstCoNm,
                   lstTxRn,lstTxSt])
    
    # Make it a dataframe
    dfSummTable = pd.DataFrame(reclst,columns=lstcols)
    return dfSummTable

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# Make an empty master dataframe to append each species' records
dfMaster = pd.DataFrame()
# Make an empty species info master dataframe to append each species' records summary
dfSppInfoMaster = pd.DataFrame()



'''
    NOTE: Not all species have all required fields in their set of records.
          To avoid an error when combining species data, create a dictionary
          with the required fields and no data, making it into a dataframe.
          Then its possible to append this empty dataframe with all the data
          for a given species regardless of whether that field exists for that
          species. Subsequently, this dataframe can be thinned back to the required
          fields and reordered. Finally, it can appended to the master dataframe.
'''
# Make an empty dataframe with required field names using an empty dictionary
data0 = {'species':[],'vernacularName':[],
         'decimalLatitude':[],'decimalLongitude':[],
        'coordinateUncertaintyInMeters':[],'geodeticDatum':[],
        'eventRemarks':[],'locality':[],'locationRemarks':[],'occurrenceRemarks':[],
        'stateProvince':[],'year':[],'month':[],
        'basisOfRecord':[],'taxonRank':[],'taxonomicStatus':[]}
df0 = pd.DataFrame(data=data0, index=None)

# Loop over each species in the species list
for spp in sppList:
    
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
                           offset=n)
        cnt = recs['count']
        print('  This species has', cnt, 'records')
        eor = recs['endOfRecords']
        tablelst = tablelst + recs['results']
        n+=300
        
    # Make a dataframe out of the compiled lists
    df = pd.DataFrame(data=tablelst)
    # Append it to the empty dataframe
    dfAppended = df0.append(df, ignore_index=True, sort=False)
    # Thin out the final dataframe to only the required fields
    # and make sure they are in the appropriate order
    dfThinned = dfAppended[['species','vernacularName','decimalLatitude','decimalLongitude',
        'coordinateUncertaintyInMeters','geodeticDatum',
        'eventRemarks','locality','locationRemarks','occurrenceRemarks',
        'stateProvince','year','month',
        'basisOfRecord','taxonRank','taxonomicStatus']]
    
    # Now append this thinned dataframe to the master
    dfMaster = dfMaster.append(dfThinned, ignore_index=True, sort=False)
    
    # -------------------------------------------------------------
    # Call the SummaryInfo function to assemble some stats on 
    # GBIF records for each of the assessed species
    dfSppInfo = SummaryInfo(spp, dfThinned)
    # Append this to the master species info dataframe
    dfSppInfoMaster = dfSppInfoMaster.append(dfSppInfo, ignore_index=True, sort=False)
    # -------------------------------------------------------------

    print('\n')


# Export to CSV
#dfMaster.to_csv(tempDir + "SpeciesOccurrences-GBIF.csv")
dfSppInfoMaster.to_csv(tempDir + "Species GBIF Summary Stats.csv")

# Delete temporary objects
#del tablelst, n, eor, recs, cnt, df, data0, df0, dfMaster, dfAppended


print('\n*********************** DONE *******************************')
