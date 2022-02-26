# Get all data for project
import requests
import json
import pandas as pd
import time

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
    else:
        return []

# COVID our world in data
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

    df.to_csv(path)


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


# UN Comtrade
def un_comtrade_countries(path):
    '''
    Read json file of id and name of countries from the local machine
    for gathering UN comtrade data
    
    Input:
        path (str): json file path
    
    Output:
        (list of dict): list of dict with id and text as keys  
    '''

    f = open(path, 'r')
    data = json.loads(f.read())

    return data

def un_comtrade_json(year, reporter, partner = {'id':'all', 'text':'all'}):
    '''
    Download UN comtrade JSON data from API
    
    Inputs:
        year (int): year
        reporter (dict): a reporter dict with id, text as keys
        partner (dict): a trade partner dict with id, text as keys
    Return:
        (list of dicts): a list of dict of data that we get
    '''

    reporter_id = reporter["id"]
    partner_id = partner["id"]
    params = {'r':reporter_id, 'px':'HS', 'ps':year, 'p':partner_id, 
              'rg':2, 'cc':'AG2', 'max':100000}
    url = "https://comtrade.un.org/api/get"
    json_data = get_json(url, params)
    return json_data


def un_comtrade_to_csv(data, path, year, reporter, 
                       partner = {'id':'all', 'text':'all'}):
    '''
    Transfrom list of dict into dataframe and write to csv

    Inputs:
        data (list): a list of dict of data
        path (str): a path of csv file
        reporter (dict): a reporter dict with id, text as keys
        partner (dict): a trade partner dict with id, text as keys
        year (int): year
    '''

    df = pd.DataFrame(data)
    filename = path + reporter['text'] + "_to_" + partner['text'] + "_" +\
               str(year) + ".csv"
    df.to_csv(filename)


def large_un_comtrade_json(path, year, reporter, partners):
    '''
    In case of the data too large to retrieve (Error 5003), 
    collect data from each of the reporter's partner instead.

    Inputs:
        path (str): a path of csv file
        year (int): year
        reporter (dict): a reporter dict with id, text as keys
        partners (list): a list of trade partner dict with id, text as keys
    '''

    for i in range(0, len(partners), 5):
        partner = {}
        partner["id"] = ",".join([coun["id"] for coun in partners[i:i + 5]])
        partner["text"] = ",".join([coun["text"] for coun in partners[i:i + 5]])
        
        export = un_comtrade_json(year, reporter, partner)
        print(reporter["text"], " to ", partner["text"])
        un_comtrade_to_csv(export['dataset'], path, year, reporter, partner)


def download_un_comtrade(path, year, reporters, partners):
    '''
    Gathering export data from UN comtrade database

    Inputs:
        path (str): a path of csv file
        year (int): year
        reporters (list of dict): list of the dictionaries of reporters
        partners (list of dict): list of the dictionaries of reporters
    '''

    for reporter in reporters:
        export = un_comtrade_json(year, reporter)
        print(reporter["text"])
    
        if export['validation']['status']['value'] == 5003:
            # Encounter large dataset limit
            large_un_comtrade_json(path, year, reporter, partners)
        else:
            un_comtrade_to_csv(export['dataset'], path, year, reporter)


def call_un_comtrade(reporters_path, partners_path, csv_path):
    '''
    Main Program for Downloading UN comtrade

    Inputs:
        reporters_path (path): a path of reporters file
        partners_path (path): a path of partners file
        csv_path (str): a path of csv file
    '''
    reporters = un_comtrade_countries(reporters_path)
    partners = un_comtrade_countries(partners_path) 
    download_un_comtrade(csv_path, 2019, reporters, partners)
    download_un_comtrade(csv_path, 2020, reporters, partners)