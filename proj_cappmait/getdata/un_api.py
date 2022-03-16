"""
This module collects UN trade product/partner detail for top30 countries
by UN api.

We retrieve each country files via call_un_comtrade function and concatinate
these files together by using concat_un_comtrade, storing the result in 
data/data_from_prog
"""

import json
import time
import os
import pandas as pd
import requests

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
    df.to_csv(filename, index = False)


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


# Concatenate all UN comtrade files and create new csv
def concat_un_comtrade(raw_folder, csv_folder, partners_path):
    '''
    concatenate all UN Comtrade files and export to csv

    Args:
        raw_folder (str): Folder that keeping the UN Comtrade csv file
        csv_folder (str): Folder that we want to the csv kept
        partners_path (path): a path of partners file
    '''
    
    df = pd.DataFrame()
    dir_list = os.listdir(raw_folder)
    for file in dir_list:
        path = raw_folder + file
        un_comtrade = pd.read_csv(path,
                                  usecols = ['yr', 'rtCode', 'rtTitle', 
                                             'rt3ISO', 'ptCode', 'ptTitle', 
                                             'pt3ISO', 'cmdCode', 
                                             'cmdDescE', 'TradeValue'],
                                  dtype = {'rtCode': 'str', 'ptCode': 'str', 
                                           'cmdCode': 'str'})
        df = pd.concat([df, un_comtrade])
    
    major_importers = un_comtrade_countries(partners_path) 
    major_importers = pd.DataFrame(major_importers)

    # Filter out not major importers
    un_comtrade = df.merge(major_importers, how = "inner", 
                           left_on = "ptCode", right_on="id")
    un_comtrade = un_comtrade.loc[:, ~un_comtrade.columns.isin(['id', 'text'])]
    un_comtrade.columns = ['year', 'reporter_code','reporter_title', 
                           'reporter_iso', 'partner_code', 'partner_title', 
                           'partner_iso', 'comm_code', 'comm_desc', 'trade_val']
    un_comtrade = un_comtrade.sort_values(by = ['year', 'reporter_title', 
                                                'partner_title', 'comm_code'])
    
    # Due to political reason, hard code for Taiwan ISO
    un_comtrade.fillna({'reporter_iso':'TWN', 'partner_iso':'TWN'}, 
                       inplace = True)
    
    # create csv file
    filename = csv_folder + "un_comtrade_top30" + ".csv"
    un_comtrade.to_csv(filename, index = False)


def create_un_data():
    """
    Create UN comtrade data
    """

    reporters = "proj_cappmait/data/archived/reporterAreas_top30.json"
    partners = "proj_cappmait/data/archived/partnerAreas_top30.json"
    raw_un_comtrade_path = ("proj_cappmait/data/data_from_prog" + 
                            "/rawdata/uncomtrade/")
    final_csv_path = "proj_cappmait/data/data_from_prog/cleandata/"
    call_un_comtrade(reporters, partners, raw_un_comtrade_path)
    concat_un_comtrade(raw_un_comtrade_path, final_csv_path, partners)


def check_error(path):
    '''
    List the error file, use when we want to
    check some files might be corrupted

    Input:
        path (str): a folder kept files
    
    Return:
        (list): list of error files
    '''
    dir_list = os.listdir(path)
    blank = []
    for file in dir_list:
        path = path + file
        df = pd.read_csv(path)
        if df.shape[0] == 0:
            blank.append(file)
    
    return blank
