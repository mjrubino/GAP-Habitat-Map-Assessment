# -*- coding: utf-8 -*-
"""


    Use this to convert an R data file with an .rda extension
    into a Pandas dataframe.
    
    This example is for converting the rda file 'institutions.rda'
    compiled by Alexander Zizka (et al.) with rOpenSci for use in their
    R package CoordinateCleaner available on GitHub:
    https://github.com/ropensci/CoordinateCleaner/tree/master/data
    
    This data is a compilation of known institutions throughout the
    world that house species data collections and the coordinates of
    those institutions to be used to assess species locations that
    may have lat/long info at that location. The rOpenSci project is
    encouranging data providers and collectors to gather newer info
    to keep this file up to date:
    https://ropensci.github.io/CoordinateCleaner/articles
    /Background_the_institutions_database.html
    
    It requires installing the rpy2 package for Python as well as
    Pandas. The rpy2 package allows access to R functionality within
    Python. It can be installed using Anaconda but note that it 
    requires installing a number of R packages as well which can
    take awhile to load and requires some hard drive space. It also
    needs the package tzlocal.



Created on Fri Feb 15 11:20:03 2019

@author: mjrubino
"""

import pandas as pd
from rpy2.robjects import r, pandas2ri
from rpy2.robjects.packages import importr
pandas2ri.activate()

# this is a local copy of the institutions.rda file
rfileloc = 'C:/Data/USGS Analyses/GAP-Habitat-Map-Assessment/temp/'
fname = 'institutions.rda'

# read in the rda file using R
base = importr('base')
base.load(rfileloc + 'institutions.rda')
rdf = base.mget(base.ls())

# make an empty Python dictionary
pydf_dict = {}
# loop through the R file and append it to the Python dictionary
for i,f in enumerate(base.names(rdf)):
    pydf_dict[f] = pandas2ri.ri2py_dataframe(rdf[i])

# get the values in the dictionary
RData = pydf_dict['institutions']
# then make it a dataframe
df = pd.DataFrame(RData)

# export to csv
df.to_csv(rfileloc + "Institutions.csv")