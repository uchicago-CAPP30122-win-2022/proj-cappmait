# Get all data for project
import requests
import pandas as pd
import time

# COVID our world in data
def get_owid():
    '''
    Gathering COVID-19 data from Our World in Data and making them into
    csv files
    '''
    url = "https://covid.ourworldindata.org/data/owid-covid-data.json"
    resp = requests.get(url)
    owid_json = resp.json()
    gen_infos = []
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
        gen_infos.append(country_info)

    gen_info_df = pd.DataFrame(gen_infos)
    covid_data_df = pd.DataFrame(covid_data)

    gen_info_df.to_csv("rawdata/owid_country_info.csv")
    covid_data_df.to_csv("rawdata/owid_covid_data.csv")