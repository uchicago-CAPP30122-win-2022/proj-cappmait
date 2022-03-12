'''
This module cleans data.
'''
import pandas as pd

country_code = pd.read_csv('rawdata/countries_codes_and_coordinates_new.csv').rename({'Country': 'country_name'}, axis = 1) # Later change the file name?

def clean_imf(path="cleandata/imf_import_export_cleaned.csv"):
    '''
    Clean IMF trading partners data. Add country code and drop irrelevant columns. 

    Inputs:
        path (str): A csv path. Default is defined. 

    Outputs:
        Save to csv. Return is None. 
    '''
    df = pd.read_csv("rawdata/imf_import_export.csv")

    df = df.iloc[: , 1:] # Later modify the imf_api.py and delete the first line?
    df = df.merge(country_code, how ='right', left_on='from', right_on='Alpha-2code')\
                .drop(['Alpha-2code','from','Numeric code', 'Latitude (average)', 'Longitude (average)'], axis = 1)
    df.rename(columns={'Country':'from_name', 'Alpha-3code':'from_code'}, inplace = True)
    df = df.merge(country_code, how ='right', left_on='to', right_on='Alpha-2code')\
                .drop(['Alpha-2code','to','Numeric code', 'Latitude (average)', 'Longitude (average)'], axis = 1)
    df.rename(columns={'Country':'to_name', 'Alpha-3code':'to_code'}, inplace = True)

    df.to_csv(path, sep=',', index=False)


def clean_who(path="cleandata/WHO-COVID-19-global-data_cleaned.csv"):
    '''
    Do data wrangling for covid data:
    i) Join two datasets on 2 digit code
    ii) Align country name to the standard names
    iii) Filter out "2020-12-31" data for all countries
    iv) Extract needed columns for plotting, e.g. alpha 3 code
    Input:
        None, running this py file would call this function and start
            data wrangling
    
    Outputs:
        dff: a cleaned dataframe for next step of plotting
    '''
    covid_data = pd.read_csv('rawdata/WHO-COVID-19-global-data.csv')
    country_code = country_code.rename({'Country': 'Country_name'}, axis = 1)
    dic = {'2020/3/31': '2020Q1', '2020/6/30': '2020Q2', '2020/9/30': '2020Q3', '2020/12/31': '2020Q4'}

    df = covid_data.join(country_code.set_index('Alpha-2code'), on = 'Country_code')
    dff = df[["Country_name", "Date_reported", "Cumulative_cases", "Cumulative_deaths", "Alpha-3code"]]
    dff = dff[dff.Date_reported.isin(dic.keys())]

    dic = {1:'2020Q1', 2:'2020Q2', 3:'2020Q3', 4:'2020Q4'}
    dff['Quarter'] = dff.apply(f, axis=1)

    return dff
