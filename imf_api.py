import requests
import pandas as pd
import csv

url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'

key = 'DataStructure/DOT'
dimension_list = requests.get(f'{url}{key}').json()\
            ['Structure']['KeyFamilies']['KeyFamily']\
            ['Components']['Dimension']

key = f'CodeList/{dimension_list[1]["@codelist"]}'
code_list_d2 = requests.get(f'{url}{key}').json()\
	    ['Structure']['CodeLists']['CodeList']['Code']
country_codes = {}
for code in code_list_d2:
    country_codes[code['@value']] = code['Description']['#text']
code_list = list(country_codes.keys())

with open('rawdata/imf_import_export_country_codes.csv', 'w') as f:
    for key in country_codes.keys():
        f.write("%s;%s\n"%(key,country_codes[key]))

# Separating the key because there seems to be URL's length limitation.
key_d3 = []
for i in range(4):
    key_d3.append('+'.join(code_list[i*70 : min((i+1)*70, len(country_codes))]))

def extract_export_data(target_country):
    '''
    Extract one country's trading data with its trading partners in 2019 and 2020.
    Inputs:
        target_country(str): a country's code
    Outputs:
        trading data(pd.DataFrame): trading data of the target country
        missing_country(list):
            country codes which the target country doesn't have data about
            * including the case when there is data in either 2019 or 2020.
    '''
    trading_data = {}
    for k in key_d3:
        key = f'CompactData/DOT/A.{target_country}.TXG_FOB_USD.{k}\
            ?startPeriod=2019&endPeriod=2020'
        data = requests.get(f'{url}{key}').json()['CompactData']['DataSet']
        if 'Series' not in data.keys():
            continue
        data = data['Series']
        for s in data:
            df_dict_col = {}
            if 'Obs' not in s.keys() or type(s['Obs']) != list:
                continue
            for i in s['Obs']:
                df_dict_col[i['@TIME_PERIOD']] = round(float(i['@OBS_VALUE']), 1)
            trading_data[s['@COUNTERPART_AREA']] = df_dict_col

    df = pd.DataFrame(trading_data).T
    if '2019' in df.columns:
        df.sort_values(by=['2019'], inplace=True, ascending=False)
    return df


def creating_export_import_data():
    df = pd.DataFrame(index=[], columns=['from', 'to', '2019', '2020'])
    for code in country_codes.keys():
#    for code in list(country_codes.keys())[:3]:
        print(code)
        one_country = extract_export_data(code)
        one_country.reset_index(level=0, inplace=True)
        one_country.rename(columns={'index': 'to'}, inplace=True)
        one_country.insert(0, "from", code, True)
        df = pd.concat([df, one_country])
    return df.to_csv('rawdata/imf_import_export.csv')


def extract_import_data(target_country):
    '''
    Extract one country's trading data with its trading partners in 2019 and 2020.
    Inputs:
        target_country(str): a country's code
    Outputs:
        trading data(pd.DataFrame): trading data of the target country
    '''
    trading_data = {}
    for k in key_d3:
        key = f'CompactData/DOT/A.{k}.TMG_FOB_USD.{target_country}\
            ?startPeriod=2019&endPeriod=2020'
        data = requests.get(f'{url}{key}').json()['CompactData']['DataSet']['Series']
        for s in data:
            df_dict_col = {}
            if type(s) != dict:
                continue
            if 'Obs' not in s.keys() or type(s['Obs']) != list:
                continue
            for i in s['Obs']:
                df_dict_col[i['@TIME_PERIOD']] = round(float(i['@OBS_VALUE']), 1)
            trading_data[s['@REF_AREA']] = df_dict_col
    return pd.DataFrame(trading_data).T
