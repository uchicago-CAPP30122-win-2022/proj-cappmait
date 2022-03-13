'''
This module downloads data from websites. 
Data Sources:
    WTO trade products
    COVID OWID
    WHO covid
    World Bank econ data
'''
import json
import time
import os
from zipfile import ZipFile
from io import BytesIO
import requests
import pandas as pd
# pip install wbgapi to get world bank data
import wbgapi as wb

# Helper function
def get_json(url, params = None):
    '''
    Get JSON from the website
    
    Inputs:
        url (str): url
        params (dict): parameters following url. Default value is None
    
    Output:
        (dict): the JSON data in terms of Python dict
    '''

    resp = requests.get(url, params = params)
    time.sleep(5)
    if resp.status_code == 200:    
        return resp.json()
    if resp.status_code == 409:
        # if encounter this error, wait for 1 hr as complying to the API 
        # provider rule
        time.sleep(3600)
        return get_json(url, params)
    return []

# Download COVID our world in data
def owid_csv(data, path):
    '''
    Take OWID data in list of dicts format and create a csv file

    Input:
        data (list of dicts): A list of dict
        path (str): A csv path
    '''

    df = pd.DataFrame(data)
    
    # Move iso_code to the first column
    col = df.pop("iso_code")
    df.insert(0, "iso_code", col)

    df.to_csv(path, index = False)


def get_owid():
    '''
    Gathering COVID-19 data from Our World in Data and making them into
    csv files
    '''
    url = "https://covid.ourworldindata.org/data/owid-covid-data.json"
    owid_json = get_json(url)
    country_infos = []
    covid_data = []

    for country_code, rows in owid_json.items():
        country_info = {}
        country_info["iso_code"] = country_code
        for col, val in rows.items():
            if col != "data":
                country_info[col] = val
            else:
                for day in val:
                    day["iso_code"] = country_code
                    covid_data.append(day)
        country_infos.append(country_info)

    owid_csv(country_infos, "rawdata/owid_country_info.csv")
    owid_csv(covid_data, "rawdata/owid_covid_data.csv")


# Download WTO trade product data
def get_wto():
    '''
    Download zip data from WTO websit and extract product details of 
    2019 and 2020 of total imports and exports in each country.
    Save it to csv. 
    '''
    r = requests.get("http://stats.wto.org/assets/UserGuide/merchandise_values_annual_dataset.zip")
    file = ZipFile(BytesIO(r.content))
    df = pd.read_csv(file.open("merchandise_values_annual_dataset.csv"), \
        encoding = "ISO-8859-1", dtype="object")

    df = df[(df["Year"]=="2019") | (df["Year"]=="2020")]
    df = df[df["Partner"]=="World"]
    df = df[["Indicator", "ReporterCode", "ReporterISO3A", \
        "Reporter", "ProductCode", "Product","Year", "Value"]]
    df["Indicator"].replace(
        regex={r'.+imports.+': 'Import', r'.+exports.+': 'Export'}, inplace=True)

    df.to_csv("rawdata/merchandise_values_annual_dataset.csv", sep=',', index=False)


# Download WHO Covid data

# Download World Bank data
def get_wb():
    '''
    Download World Bank data, which are real gdp, nominal gdp, 
    inflation, tariff, exchange rate and total labor
    '''

    inds = ['NY.GDP.MKTP.CD', 'NY.GDP.MKTP.KD', 'FP.CPI.TOTL.ZG', 
            'TM.TAX.MRCH.SM.AR.ZS', 'PA.NUS.FCRF', 'SL.TLF.TOTL.IN']
    wb_data = wb.data.DataFrame(inds, time=[2019, 2020]).reset_index()
    wb_data = wb_data.melt(['economy', 'series'])
    wb_data = wb_data.pivot(['economy', 'variable'], 'series').reset_index()
    wb_data.columns = ['country_code', 'time_code', 'inflation', 
                       'nominal_gdp', 'real_gdp', 'exchange_rate', 
                       'labor_force', 'tariff']
    wb_data['time'] = wb_data['time_code'].str[2:]
    wb_data.to_csv("rawdata/world-bank-econ-data.csv", index=False)


def main():
    print ("Downloading csv data.")
    get_owid()
    get_wto()
    get_wb()
    print ("Data is ready.")


if __name__ == "__main__":
    main()


