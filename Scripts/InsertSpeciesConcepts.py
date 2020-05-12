# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 08:54:56 2020

@author: mjrubino
"""

'''
    Use this to insert species concepts records into the wildlife
    wrangler parameters database. It will loop over a list of
    species GAP codes, scientific and common names.
    It uses functions created in the TaxaSearch.py script to hit
    various APIs including GBIF, ITIS, IUCN, and NatureServe to
    gather taxonmic information for further examination of each
    species to ensure names and codes match GAP modeled concepts.
    A Pandas dataframe holds all records inserted into the database.
    
    NOTE: The 'notes' column in the parameters dB will be populated
    with NatureServe's taxonomic comments because they tend to be
    the most thorough description of changes and issues of taxonomy.
'''

import sys
import pandas as pd
from datetime import datetime
import sqlite3


workDir = 'D:/USGS Analyses/GAP-Habitat-Map-Assessment/'
dbDir = workDir + 'db/'
paramdb = dbDir + 'wildlife-wrangler.sqlite'
codeDir = workDir + 'Scripts/'
sys.path.append(codeDir)
import TaxaSearch as ts
sppList = workDir + 'Inputs/amphibians.txt'
dfList = pd.read_csv(sppList)

print('\nReading in species list', sppList, ' ....\n')

lst = []
cols=['SearchTerm','id_NS','sciname_NS','comments_NS','country_NS',
      'id_GBIF','sciname_GBIF','comname_GBIF','nameorigin_GBIF','yr_GBIF',
      'id_IUCN','sciname_IUCN','comments_IUCN','country_IUCN','origin_IUCN',
      'id_ITIS','sciname_ITIS','comments_ITIS','country_ITIS','origin_ITIS']

for i in dfList.index:
    
    # Read in the GAP code, scientific name and common name
    gapcode = dfList.at[i,'SpeciesCode']
    sciname = dfList.at[i,'ScientificName']
    comname = dfList.at[i,'CommonName']
    sppid = gapcode.lower()+'0'
    who = 'M. Rubino'
    dt = datetime.now().strftime('%m/%d/%Y')
    dd = 0
    
    print('  Working on', sciname, ' ....')

    gbifR = ts.SearchGBIF(sciname)
    
    kid = ts.keyID
    nsR = ts.SearchNS(sciname,kid)
    
    t = ts.iucnToken
    iucnR = ts.SearchIUCN(sciname,t)
    
    itisR = ts.SearchITIS(sciname)
    
    # Append to the empty list
    lst.append([sciname,nsR[0],nsR[1],nsR[2],nsR[3],
                gbifR[0],gbifR[1],gbifR[2],gbifR[3],gbifR[4],
                iucnR[0],iucnR[1],iucnR[2],iucnR[3],iucnR[4],
                itisR[0],itisR[1],itisR[2],itisR[3],itisR[4]])
    
    tsn = str(itisR[0])
    gid = str(gbifR[0])
    yr = gbifR[4]
    nsc = str(nsR[2]).replace('\"','')
    
    print('  Gathering info from APIs ....')

    conn = sqlite3.connect(paramdb)
    cursor = conn.cursor()
    
    print('   Inserting records into Wildlife Wrangler parameters db ...\n')
    
    sql = """
    INSERT INTO species_concepts (species_id, gap_id, itis_tsn, gbif_id, 
                                  common_name, scientific_name, start_year,
                                  detection_distance_meters, 
                                  vetted_who, vetted_date, notes)
    VALUES
    ("{0}","{1}","{2}","{3}",
     "{4}","{5}",{6},{7},"{8}","{9}","{10}");
    """.format(sppid, gapcode ,tsn, gid, comname, sciname, yr, dd, who, dt, nsc)
    
    cursor.executescript(sql)
    conn.commit()
    
    conn.close()
    del conn,cursor

print('\nWriting API Info to Pandas Dataframe\n')
dfTaxaSearch = pd.DataFrame(lst, columns=cols)
# Export to a CSV
dfTaxaSearch.to_csv(workDir + 'db/dfTaxaSearch.csv',sep='\t')
print('++++++++++++++++++++ DONE +++++++++++++++++++')

