import pandas as pd

def clean_imfdata(path="rawdata/imf_import_export_cleaned.csv"):
    '''
    Clean IMF trading partners data.

    Inputs:
        path (str): A csv path. Default is defined. 

    Outputs:
        Save to csv. Return is None. 
    '''
    df = pd.read_csv("rawdata/imf_import_export.csv")
    country_code = pd.read_csv('rawdata/countries_codes_and_coordinates_new.csv') # Later change the file name?

    df = df.iloc[: , 1:] # Later modify the imf_api.py and delete the first line?
    df = df.merge(country_code, how ='right', left_on='from', right_on='Alpha-2code')\
                .drop(['Alpha-2code','from','Numeric code', 'Latitude (average)', 'Longitude (average)'], axis = 1)
    df.rename(columns={'Country':'from_name', 'Alpha-3code':'from_code'}, inplace = True)
    df = df.merge(country_code, how ='right', left_on='to', right_on='Alpha-2code')\
                .drop(['Alpha-2code','to','Numeric code', 'Latitude (average)', 'Longitude (average)'], axis = 1)
    df.rename(columns={'Country':'to_name', 'Alpha-3code':'to_code'}, inplace = True)

    df.to_csv(path, sep=',', index=False)