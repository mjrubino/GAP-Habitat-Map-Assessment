# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 10:20:04 2020

@author: mjrubino
"""

import sqlite3
import pandas as pd
import glob, os

workDir = 'D:/USGS Analyses/GAP-Habitat-Map-Assessment/'
outDir = workDir + 'Outputs/'
dbDir = workDir + 'Outputs/'

sppList = workDir + 'Inputs/EvaluationList.csv'
dfList = pd.read_csv(sppList)

lst=[]
cols=['SppCode','SpeciesID','SciName','ComName','nRecsDB','nRecsHS']
print('\nReading Species List ...')
for i in dfList.index:
    # Read in the GAP species code and common name
    gapcode = dfList.at[i,'SpeciesCode']
    comname = dfList.at[i,'ComName'].replace('\'','')
    sciname = dfList.at[i,'SciName'].replace('\'','')
    sid = gapcode.lower()+'0'
    
    # First check for the number of records in the species dB
    # if there is one in the outputs directory
    db = glob.glob(outDir + '{0}*sqlite'.format(sid))
    if len(db)!= 0:
        print('\nSpecies Occurrence Database Exists for ' + gapcode)
        print('  Working on', sciname, ' ....')
        
        db = glob.glob(outDir + '{0}*sqlite'.format(sid))[0]
        conn = sqlite3.connect(db, isolation_level='DEFERRED')
        cursor = conn.cursor()
        sql = """SELECT COUNT(*) FROM occurrences;"""
        nRecsdb = cursor.execute(sql).fetchall()[0][0]
        conn.close()
        del conn,cursor
    else:
        print('\nSpecies Occurrence dB Does Not Exist')
        nRecsdb = -999
    
    # Next check the number of records in the HabStats file
    fn = workDir + f'HabStats/{gapcode}-HabStats.csv'
    if os.path.exists(fn):
        print('  HabStats table exsits')
        df = pd.read_csv(fn)
        nRecshs = len(df)
    else:
        print('  HabStats table Does Not Exist')
        nRecshs = -999
    
    # Now combine the variables into a single list
    lst.append([gapcode,sid,sciname,comname,nRecsdb,nRecshs])
        
    
print('\nWriting list to Pandas Dataframe and Exporting\n')
dfRecCheck = pd.DataFrame(lst, columns=cols)
# Export to a CSV
dfRecCheck.to_csv(workDir + 'db/dfRecCheck.csv',sep=',')
print('++++++++++++++++++++ DONE +++++++++++++++++++')
