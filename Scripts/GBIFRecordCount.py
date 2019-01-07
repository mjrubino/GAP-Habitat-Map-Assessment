# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 15:16:19 2019

@author: mjrubino
"""

# Import modules
import pygbif, pandas as pd
from pygbif import occurrences as occ
from pygbif import species



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

n = 0
# Loop over each species in the species list
for spp in sppList:
    recs = occ.search(scientificName = spp, 
                      hasCoordinate=True,
                      country='US', 
                      geoSpatialIssue=False)
    cnt = recs['count']
    n = n + cnt
    print('The species', spp, 'has', cnt, 'records')

print('n\TOTAL NUMBER OF RECORDS FOR THIS SPECIES LIST =',n)
print('************ DONE **************')