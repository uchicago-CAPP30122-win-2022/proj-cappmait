import requests
import pandas as pd
from zipfile import ZipFile
from io import BytesIO


def get_wtodata():
    '''
    Download zip data from WTO website and convert to Pandas dataframe.

    Inputs: 
        None

    Outputs: 
        df (Pandas Dataframe)
    '''
    r = requests.get("http://stats.wto.org/assets/UserGuide/merchandise_values_annual_dataset.zip")
    file = ZipFile(BytesIO(r.content))
    df = pd.read_csv(file.open("merchandise_values_annual_dataset.csv"), encoding = "ISO-8859-1", 
                    dtype={"ReporterCode":"string", "PartnerCode":"string", "Year":"category", "Value":"int"})

    return df

def clean_wtodata(df, path="rawdata/merchandise_values_annual_dataset.csv"):
    '''
    Clean WTO data. Extract product details of 2019 and 2020 of total imports and exports in each country.

    Inputs:
        df (Pandas data frame): WTO data
        path (str): A csv path. Default is defined. 
    
    Outputs:
        Save to csv. Return is None. 
    '''
    df = df[(df["Year"]=="2019") | (df["Year"]=="2020")]
    df = df[df["Partner"]=="World"]
    df = df[["Indicator", "ReporterCode", "ReporterISO3A", "Reporter", "ProductCode", "Product","Year", "Value"]]
    df["Indicator"].replace(regex={r'.+imports.+': 'Import', r'.+exports.+': 'Export'}, inplace=True)

    df.to_csv(path, sep=',')

