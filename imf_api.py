import requests
import pandas as pd

url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'
key = 'CompactData/IFS/Q.JP+GB.TXG_D_FOB_USD_IX?startPeriod=2017&endPeriod=2020'

'''
Key should be
    CompactData/{database ID}/{frequency}
    .{item1 from dimension1}+{item2 from dimension1}+{item N from dimension1}
    .{item1 from dimension2}+{item2 from dimension2}+{item M from dimension2}
    ?startPeriod={start date}&endPeriod={end date}

This retrieves
    dimension1: quarterly (frequency: Q)
    dimension2: countries, which are Japan and the U.K. (reference area: JP, GB)
    dimension3: External Trade, Goods, Deflator/Unit Value of Exports, 
                Free on Board (FOB), in US Dollars, Index (indicator: TXG_D_FOB_USD_IX)
    database ID: the International Financial Statistics (IFS) series.
    time period: startPeriod = 2017 and endPeriod = 2020
'''

data = (requests.get(f'{url}{key}').json()['CompactData']['DataSet']['Series'])

# In the following process, I only use Japan as my test. (Japan is in data[0])
country_code = data[0]['@REF_AREA']

data_list = [[obs.get('@TIME_PERIOD'), obs.get('@OBS_VALUE')]
             for obs in data[0]['Obs']]
df = pd.DataFrame(data_list, columns=['date', 'value'])
print(df.head())
df['date'] = pd.to_datetime(df['date'])
#df = df.set_index(pd.to_datetime(df['date']))['value'].astype('float')

print('Country Code:', country_code)
print(df.head())