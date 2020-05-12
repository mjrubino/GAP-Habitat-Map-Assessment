'''

    Use this to copy the wrangler occurrence running notebook template - 
      Occurrence-Record-Report.ipynb
    The copy will be a species specific notebook with the GAP species code
    as the file name. The species ID and common name will be inserted into
    the very first code cell of the notebook so it can be run for that
    species when appropriate fields in the parameters dB are filled out.
    
    It runs off a file with GAP species code, scientific name, and
    common name columns. It is set as the sppList variable.

'''

import pandas as pd
from shutil import copyfile
import nbformat

workDir = 'D:/USGS Analyses/GAP-Habitat-Map-Assessment/'
noteDir = workDir + 'Inputs/notebooks/'
fn = 'Occurrence-Record-Report.ipynb'

sppList = workDir + 'Inputs/amphibians.txt'
dfList = pd.read_csv(sppList)


for i in dfList.index:
    # Read in the GAP species code and common name
    gapcode = dfList.at[i,'SpeciesCode']
    comname = dfList.at[i,'CommonName'].replace('\'','')
    sid = gapcode.lower()+'0'
    
    print('Making Notebook Copy for GAP Code',gapcode)
    
    # Copy the notebook using the species code as the name
    ntpath = noteDir + f'{gapcode}.ipynb'
    copyfile(workDir + fn, ntpath)
    
    # Read in the notebook
    nb = nbformat.read(ntpath,nbformat.NO_CONVERT)
    # Get the first code cell where the species ID and common name to change reside
    ccode = nb['cells'][2]
    
    strrep = f'species_id = \'{sid}\'\nsummary_name = \'{comname}\'\ngbif_req_id = \'EvalGBIFRequest\'\ngbif_filter_id = \'EvalGBIFFilter\'\ndefault_coordUncertainty = False       # Note above.\nworkDir = \'D:/USGS Analyses/GAP-Habitat-Map-Assessment/\'   # Be sure to create folders named "Inputs" and "Outputs" here.\ncodeDir = workDir + \'Scripts/\'\ndbDir = workDir + \'db/\'\nparamdb = dbDir + \'wildlife-wrangler.sqlite\'\nconfigDir = workDir  # Path to folder where saved your wildlifeconfig file.'
    # This is really a list so make it one
    lstrep = [strrep]
    # Update the source cell
    ccode.update({'source':lstrep})
    
    # Write it to a new notebook file
    nbformat.write(nb, ntpath, version=nbformat.NO_CONVERT)



print('******************* DONE *********************')
