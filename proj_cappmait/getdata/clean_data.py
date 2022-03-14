'''
This module cleans following data.
    1) IMF trade partner
    2) Country code
    3) OWID Covid
'''
import pandas as pd

def clean_imf():
    '''
    Clean IMF trading partners data and save it to csv.
    1) Merge ISO3 country code
    2) Drop missing rows
    3) Select data that trade exists in both 2019 and 2020
    '''
    df = pd.read_csv("../data/archived/imf_import_export.csv")
    country_code = pd.read_csv('../data/archived/countries_codes_and_coordinates.csv').rename({'Country': 'Country_name'}, axis = 1)

    df = df.iloc[: , 1:]
    df = df.merge(country_code, how ='right', left_on='from', right_on='Alpha-2code')\
                .drop(['Alpha-2code','from','Numericcode', 'Latitude(average)', 'Longitude(average)'], axis = 1)
    df.rename(columns={'Country_name':'from_name', 'Alpha-3code':'from_code'}, inplace = True)
    df = df.merge(country_code, how ='right', left_on='to', right_on='Alpha-2code')\
                .drop(['Alpha-2code','to','Numericcode', 'Latitude(average)', 'Longitude(average)'], axis = 1)
    df.rename(columns={'Country_name':'to_name', 'Alpha-3code':'to_code'}, inplace = True)

    df = df.dropna()
    df = df[(df["2019"] > 0.0) & df["2020"] > 0.0]

    df.to_csv("../data/imf_import_export_cleaned.csv", index=False)

def clean_countrycode():
    '''
    Clean country code data and save it to csv. 
    1) Drop countries that do not appear in trade dataset
    2) Drop countries that do not appear in product dataset
    3) Drop duplicated country codes. 
    '''
    partners = pd.read_csv("../data/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
    product = pd.read_csv("../data/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
    df = pd.read_csv('../data/archived/countries_codes_and_coordinates.csv')

    dff = df.merge(partners["from_code"], left_on='Alpha-3code', right_on='from_code', how='right').drop('from_code', axis=1)
    dff = dff.drop_duplicates().reset_index(drop=True)
    dff = dff.merge(product["ReporterISO3A"], left_on='Alpha-3code', right_on='ReporterISO3A', how='inner').drop('ReporterISO3A', axis=1)
    dff = dff.drop_duplicates().reset_index(drop=True)
    dff = dff.sort_values("Alpha-3code")

    dff.to_csv("../data/countries_codes_and_coordinates_cleaned.csv", index=False)

def clean_owid():
    '''
    Clean OWID Covid data and save it to csv.
    1) Aggregate to quarterly and yearly data.
    2) Merge country name
    3) Drop irrelevant columns
    4) Replace missing values with 0 
    5) Select data in 2020

    Inputs:
        path (str): A csv path. Default is defined. 

    Outputs:
        Save to csv. Return is None. 
    '''
    owid_covid = pd.read_csv('../data/archived/owid_covid_data.csv') 
    country_code = pd.read_csv('../data/countries_codes_and_coordinates_cleaned.csv').rename({'Country': 'Country_name'}, axis = 1)

    owid_covid['date'] = pd.to_datetime(owid_covid['date'])
    owid_covid['year'] = owid_covid['date'].dt.year
    owid_covid['quarter'] = owid_covid['date'].dt.to_period('Q')

    agg = {'total_cases': 'last', 'total_cases_per_million': 'last', 'total_deaths': 'last', 'total_deaths_per_million': 'last',
        'new_cases': 'sum', 'new_cases_per_million' : 'sum', 'new_deaths': 'sum', 'new_deaths_per_million': 'sum',
       'stringency_index': 'mean'}
    owid_covid_quarter = (owid_covid.groupby(['iso_code', 'quarter'])
                        .agg(agg).reset_index()).rename(columns={'quarter':'period'})
    owid_covid_year = (owid_covid.groupby(['iso_code', 'year'])
                      .agg(agg).reset_index()).rename(columns={'year':'period'})
    owid_covid_grouped = pd.concat([owid_covid_quarter, owid_covid_year], ignore_index=True, sort=False)
    owid_covid_grouped["period"] = owid_covid_grouped["period"].astype(str)
    owid_covid_grouped = owid_covid_grouped.sort_values(by=["iso_code", "period"])

    owid_covid_grouped = owid_covid_grouped.merge(country_code, left_on="iso_code", right_on="Alpha-3code", how="inner")
    owid_covid_grouped = owid_covid_grouped[["iso_code", "Country_name", "period", "total_cases", "total_cases_per_million",
                            "total_deaths", "total_deaths_per_million", "new_cases", "new_cases_per_million", "new_deaths", 
                            "new_deaths_per_million", "stringency_index"]]
    owid_covid_grouped = owid_covid_grouped.fillna(0)
    owid_covid_grouped = owid_covid_grouped[owid_covid_grouped["period"].str.contains("2020")]

    owid_covid_grouped.to_csv("../data/owid_covid_data_cleaned.csv", index=False)

