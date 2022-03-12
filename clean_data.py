'''
This module cleans data.
'''
import pandas as pd


def clean_imf(path="cleandata/imf_import_export_cleaned.csv"):
    '''
    Clean IMF trading partners data. Add country code and drop irrelevant columns. 

    Inputs:
        path (str): A csv path. Default is defined. 

    Outputs:
        Save to csv. Return is None. 
    '''
    df = pd.read_csv("rawdata/imf_import_export.csv")
    country_code = pd.read_csv('rawdata/countries_codes_and_coordinates_new.csv').rename({'Country': 'Country_name'}, axis = 1)

    df = df.iloc[: , 1:] # Later modify the imf_api.py and delete the first line?
    df = df.merge(country_code, how ='right', left_on='from', right_on='Alpha-2code')\
                .drop(['Alpha-2code','from','Numeric code', 'Latitude (average)', 'Longitude (average)'], axis = 1)
    df.rename(columns={'Country':'from_name', 'Alpha-3code':'from_code'}, inplace = True)
    df = df.merge(country_code, how ='right', left_on='to', right_on='Alpha-2code')\
                .drop(['Alpha-2code','to','Numeric code', 'Latitude (average)', 'Longitude (average)'], axis = 1)
    df.rename(columns={'Country':'to_name', 'Alpha-3code':'to_code'}, inplace = True)

    df = df.dropna()
    df = df[(df["2019"] > 0) | df["2020"] > 0]

    df.to_csv(path, sep=',', index=False)


def clean_who(path="cleandata/WHO-COVID-19-global-data_cleaned.csv"):
    '''
    Clean WHO covid data. Add country code and drop irrelevant columns add quarter column. 

    Inputs:
        path (str): A csv path. Default is defined. 
    
    Outputs:
        Save to csv. Return is None. 
    '''
    df = pd.read_csv('rawdata/WHO-COVID-19-global-data.csv')
    country_code = pd.read_csv('rawdata/countries_codes_and_coordinates_new.csv').rename({'Country': 'Country_name'}, axis = 1)
    dic = {'2020/3/31': '2020Q1', '2020/6/30': '2020Q2', '2020/9/30': '2020Q3', '2020/12/31': '2020Q4'}

    df = df.join(country_code.set_index('Alpha-2code'), on = 'Country_code')
    dff = df[["Country_name", "Date_reported", "Cumulative_cases", "Cumulative_deaths", "Alpha-3code", "Country_code"]]
    dff = dff.rename(columns = {"Country_code":"Alpha-2code"})
    dff = dff[dff.Date_reported.isin(dic.keys())]

    dff['Quarter'] = dff["Date_reported"].map(dic)

    dff.to_csv(path, sep=',', index=False)


def clean_countrycode(path="cleandata/countries_codes_and_coordinates_cleaned.csv"):
    '''
    Clean country code data. Drop countries that do not appear in trade dataset and
    drop duplicated country codes. 

    Inputs:
        path (str): A csv path. Default is defined. 
    
    Outputs:
        Save to csv. Return is None. 
    '''
    partners = pd.read_csv("cleandata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
    product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
    df = pd.read_csv('rawdata/countries_codes_and_coordinates_new.csv')
    dff = df.merge(partners["from_code"], left_on='Alpha-3code', right_on='from_code', how='right').drop('from_code', axis=1)
    dff = dff.drop_duplicates().reset_index(drop=True)
    dff = dff.merge(product["ReporterISO3A"], left_on='Alpha-3code', right_on='ReporterISO3A', how='inner').drop('ReporterISO3A', axis=1)
    dff = dff.drop_duplicates().reset_index(drop=True)
    dff = dff.drop_duplicates(subset='Alpha-3code', keep='last')

    dff.to_csv(path, sep=',', index=False)


def create_aggdata(path="cleandata/agg_covid_trade.csv"):
    '''
    Create an aggregate dataframe of covid and trade data. 

    Inputs:
        path (str): A csv path. Default is defined. 
    
    Outputs:
        Save to csv. Return is None. 
    '''
    covid_data = pd.read_csv('cleandata/WHO-COVID-19-global-data_cleaned.csv')
    product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
    country_code = pd.read_csv("cleandata/countries_codes_and_coordinates_cleaned.csv")

    covid_data = covid_data.merge(country_code["Alpha-2code"], left_on = 'Alpha-2code', right_on = 'Alpha-2code', how='right')
    covid_data = covid_data[covid_data["Date_reported"]=="2020/12/31"].drop('Date_reported', axis=1).reset_index(drop=True)

    product = product[product["ProductCode"]=="TO"].pivot(index=["ReporterISO3A", "Reporter", "ProductCode", "Product"], values="Value", columns=["Indicator", "Year"]).reset_index()
    product.columns = product.columns.map('_'.join)

    whole_df = covid_data.merge(product, left_on="Alpha-3code", right_on="ReporterISO3A_", how="left")
    whole_df = whole_df[["Alpha-3code", "Country_name", "Cumulative_cases", "Cumulative_deaths", "Import_2020", "Export_2020"]]
    whole_df = whole_df.sort_values("Alpha-3code")

    whole_df.to_csv(path, sep=',', index=False)
