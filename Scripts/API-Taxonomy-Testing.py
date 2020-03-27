# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 11:39:50 2020

@author: mjrubino
"""
'''

    Sample scripting to use various species-centric database APIs to
    compare taxonomic concepts with a focus on using GAP taxonomies
    as the search parameter - both scientific and common names.

    Currently this scripting has example API search functions for:
    NatureServe
    IUCN
    ITIS
    GBIF
    Global Names Resolver


    PYTHON 3.6


'''

import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import urllib
import requests
import re
import string
from datetime import datetime
from io import StringIO



pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 100)

############### API TOKENS AND KEYS ###############
# NatureServe key ID
keyID = 'cd08be35-cef1-46ec-a402-f108541b600e'
# IUCN token
iucnToken = '9367077434703397072e089e4d2940bfd973ff3238b03e6de326cb3948847403'
userGBIF = 'mjrubino'
pwdGBIF= 'warbler'
emailGBIF = 'matt_rubino@ncsu.edu'


##### Search terms using GAP scientific or common names #####
stGAPsci = "Ammodramus henslowii"
stGAPsci = "Centronyx henslowii"
stGAPsci = "Charadrius alexandrinus"
stGAPsci = "Charadrius nivosus"
stGAPsci = "Terrapene carolina carolina"
stGAPsci = "Gopherus agassizii"
stGAPsci = "Equus caballus"
stGAPcom = "Henslow's sparrow"
stGAPcom = "Snowy plover"



#############################################################################################################
'''
    NatureServe API Navigation - REST Web services

'''
def SearchNS(st, keyID):

    # Search the global species list service using either Scientific Name or Common Name
    urlName = "https://services.natureserve.org/idd/rest/ns/v1/globalSpecies/list/nameSearch?name=" + \
                st.replace(" ", "%20") + "&NSAccessKeyId=" + keyID

    # Parse the XML holding species data using the URL above
    tree = ET.parse(urllib.request.urlopen(urlName))
    root = tree.getroot()
    # Find the global species unique id element in the root
    rTxt = ".//{http://services.natureserve.org/docs/schemas/biodiversityDataFlow/1}"
    elID = root.findall(rTxt + "globalSpeciesUid")

    try:
        # Get the global species unique id text if the taxonomy is acceptable
        guid = elID[0].text
        # Search the global comprehensive species service
        # Go into the comprehensive species report tree using the global id
        urlComp = "https://services.natureserve.org/idd/rest/ns/v1.1/globalSpecies/comprehensive?uid=" + \
                   guid + "&NSAccessKeyId=" + keyID
        # Parse the XML holding species data using the URL above
        tree = ET.parse(urllib.request.urlopen(urlComp))
        root = tree.getroot()
        # Find the scientific name element in the root
        elName = root.findall(rTxt + "unformattedName")
        nameNS = elName[0].text
        # Find the taxonomic comments in the root
        # Make sure there are comments prior to setting the variable
        elComm = root.findall(rTxt + "taxonomicComments")
        if len(elComm) != 0:
            comm = elComm[0].text
            # Remove the HTML tags in the comments text
            commNS = re.sub('<[^<]+?>', '', comm)
        else:
            commNS = ''
        # Find if US national status is Native
        path = root.findall(rTxt + "nation[@nationCode='US']")
        if len(path) != 0:
            cntyNS = 'US'
            # Iterate through multiple 'nationalDistribution' records to find the origin
            for child in path[0][0]:
                origNS = child[0].text
        else:
            cntyNS = ''
            origNS = ''

    except IndexError:
        guid = 'NA'
        nameNS = 'NA'
        commNS = ''
        cntyNS = ''
        origNS = ''


    # Return a tuple of information from the API search
    return guid, nameNS, commNS, cntyNS, origNS

#############################################################################################################
'''
    IUCN API Navigation - REST Web services

'''
def SearchIUCN(st, iucnToken):

    rTxt = "https://apiv3.iucnredlist.org/api/v3/species/"
    # Search by individual species
    urlName = rTxt + st.replace(" ", "%20") + "?token=" + iucnToken
    # Return the JSON holding species data using the URL above
    jName = requests.get(urlName).json()

    try:
        # Get the IUCN scientific name and taxon id if the taxonomy is acceptable
        nameIUCN = jName['result'][0]['scientific_name']
        tid = jName['result'][0]['taxonid']

        # Return the JSON using the country occurrence by species name
        # to make sure the species US origin is native
        urlCnty = rTxt + "countries/name/" + st.replace(" ", "%20") + "?token=" + iucnToken
        jCnty = requests.get(urlCnty).json()
        try:
            # See if the taxonomic concept occurs in the US
            r = jCnty['result']
            # Line below will check for both US and that the taxon is Native
            #if not any(val['code'] == 'US' and val['origin'] == 'Native' for val in r):
            # Check only for presence in the US
            if not any(val['code'] == 'US' for val in r):
                cntyIUCN = ''
                origIUCN = ''
            else:
                cntyIUCN = 'US'
                # Get the index of the location of the US code to find origin
                i=next((index for (index, d) in enumerate(r) if d['code'] == 'US'), None)
                origIUCN = r[i]['origin']

        except:
            cntyIUCN = ''
            origIUCN = ''

        # Return the JSON using the species narrative information by species name
        # to get the taxonomic comments within the full species narrative
        urlComm = rTxt + "narrative/" + st.replace(" ", "%20") + "?token=" + iucnToken
        jComm = requests.get(urlComm).json()
        comm = jComm['result'][0]['taxonomicnotes']
        # Remove the HTML tags in the comments text if there are any
        if comm != None:
            commIUCN = re.sub('<[^<]+?>', '', comm)
        else:
            commIUCN = ''
    except:
        nameIUCN = 'NA'
        tid = 'NA'
        origIUCN = ''
        commIUCN = ''
        cntyIUCN = ''


    # Return a tuple of information from the API search
    return tid, nameIUCN, commIUCN, cntyIUCN, origIUCN

#############################################################################################################
'''
    ITIS API Navigation - Apache SOLR Web services for scientific name search
                        - ITIS web services for common name search

'''

def SearchITIS(st):

    ################# Search using common name #################
    ## NOTE: This will return only Common Name and TSN for the species since that
    ##       is all this API search returns. If a scientific name is passed it
    ##       will use the scientific name search section and return all values
    wsTxt = "https://www.itis.gov/ITISWebService/services/ITISService/searchByCommonName?srchKey="
    urlCom = wsTxt + st.replace(" ", "%20").replace("'", "%27")
    crTxt = requests.get(urlCom).text
    try:
        crLst = crTxt.split('<')
        stc = string.capwords(st)
        cs = [i for i in crLst if stc in i]
        if len(cs) > 0:
            nameITIS = stc
        else:
            nameITIS = ''
        # Find all the tsn values in the common name request list
        tsnlst = [i for i in crLst if (re.findall(r'>([0-9]+)', i))]
        # Make an empty tsn list that will contain only the numbers
        tsn = []
        if len(tsnlst) > 0:
            for t in tsnlst:
                # Remove spurious text in each element's string to get all TSNs
                e = t.replace(r'ax21:tsn>','')
                tsn.append(e)
        else:
            tsn = ''

        # Set these 3 variables as blank because the common name search
        # doesn't return any information regarding country, origin, or comments
        cntyITIS = ''
        origITIS = ''
        commITIS = ''

    except:
        nameITIS = 'NA'
        tsn = 'NA'
        cntyITIS = ''
        origITIS = ''
        commITIS = ''

    ################# Search using taxonomic name with rank indicators #################
    s = st.replace(" ","\ ")
    urlITIS = "https://services.itis.gov/?q=nameWInd:{0}&rows=10&wt=json".format(s)
    # Return the JSON holding species data using the URL above
    jsonITIS = requests.get(urlITIS).json()
    res = jsonITIS['response']
    try:
        # Check for return of acceptable taxonomy
        if res['numFound'] != 0:
            # Get the ITIS taxonomic serial number (TSN) and ITIS scientific name
            tsn = res['docs'][0]['tsn']
            nameITIS = res['docs'][0]['nameWInd']
            # Get the ITIS taxonomic publication references
            # This will return a list with tags in it which can be removed later
            commITIS = res['docs'][0]['publication']
            # See if the taxonomic concept is present in the US
            j = res['docs'][0]['jurisdiction']
            cnty = [i for i in j if 'Continental US' in i]
            if len(cnty) > 0:
                cntyITIS = 'US'
                # Get the origin
                origITIS = cnty[0][16:].split('$')[0]
            else:
                cntyITIS = ''
                origITIS = ''


    except:
        nameITIS = 'NA'
        tsn = 'NA'
        cntyITIS = ''
        origITIS = ''
        commITIS = ''



    # Return a tuple of information from the API search
    return tsn, nameITIS, commITIS, cntyITIS, origITIS

#############################################################################################################
'''
    GBIF Records Navigation - REST JSON API

'''

def SearchGBIF(st, user, pwd, email):

    gbifTxt = "http://api.gbif.org/v1/"
    urlName = gbifTxt + "species?name=" + st
    urlName = gbifTxt + "species/search?q=" + st + "&rank=SPECIES"
    jName = requests.get(urlName).json()
    r = jName['results']



#############################################################################################################
'''
    Global Names Resolver Records Navigation - REST web services

'''

def SearchGNR(st):

    # Search the Global Names Resolver API. This is a compilation of
    # a variety of database sources with a ranking score of taxonomic match
    gnrTxt = "http://resolver.globalnames.org/name_resolvers.json?names="
    urlGNR = gnrTxt + st.replace(" ", "+")
    jsonGNR = requests.get(urlGNR).json()










'''
###################### RUN THE API SEARCH FUNCTIONS ########################
'''
###   Run the search functions on Scientific Name
snNS = SearchNS(stGAPsci, keyID)
snIUCN = SearchIUCN(stGAPsci, iucnToken)
snITIS = SearchITIS(stGAPsci)


###  Run the search functions on Common Name
# NOTE: The IUCN API cannot be searched by common name
cnNS = SearchNS(stGAPcom, keyID)
cnITIS = SearchITIS(stGAPcom)
