'''
This module collects bilateral trade data for all countries by IMF API.
To use this module, execute '$python3 imf_api.py' on your command line.

Reference: https://www.bd-econ.com/imfapi1.html
'''
import pandas as pd
import requests

url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'

def create_export_import_data():
    """
    Create bilateral export dataset by running the extract_export_data function
    to the every country and region in IMF dataset.
    And create bilateral export-import dataset from the export dataset.

    Inputs:
        country_codes: every country code in the target dataset.
    Output(csv file): bilateral export-import dataset
    """
    country_codes = find_country_codes()

    df = pd.DataFrame(index=[], columns=['from', 'to', '2019', '2020'])
    for code in country_codes:
        print(f"Getting {code}'s export data...")
        one_country = get_imf_export_data(country_codes, code)
        one_country.reset_index(level=0, inplace=True)
        one_country.rename(columns={'index': 'to'}, inplace=True)
        one_country.insert(0, "from", code, True)
        df = pd.concat([df, one_country])

    return df.to_csv('rawdata/imf_import_export_test.csv')


def find_country_codes():
    """
    Find every country code in the target dataset.
    Returns:
        country_codes: every country code in the target dataset.
    """
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

    return country_codes


def get_imf_export_data(country_codes, target_country):
    '''
    Get one country's trading data with its trading partners in 2019 and 2020
    by IMF API. This process separates the key to four short keys and execute
    individually because there seems to be URL's length limitation.

    Inputs:
        country_codes: every country code in the target dataset.
        target_country(str): a country's code
    Outputs:
        trading data(pd.DataFrame): trading data of the target country
    '''
    key_d3 = []
    code_list = list(country_codes.keys())
    for i in range(4):
        key_d3.append('+'.join(code_list[i*70 : min((i+1)*70, len(country_codes))]))

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
            if 'Obs' not in s.keys() or not isinstance(s['Obs'], list):
                continue
            for i in s['Obs']:
                df_dict_col[i['@TIME_PERIOD']] = round(float(i['@OBS_VALUE']), 1)
            trading_data[s['@COUNTERPART_AREA']] = df_dict_col

    df = pd.DataFrame(trading_data).T
    if '2019' in df.columns:
        df.sort_values(by=['2019'], inplace=True, ascending=False)

    return df


def main():
    print ("Start to create dataset.")
    create_export_import_data()
    print ("Dataset is ready.")


if __name__ == "__main__":
    main()
