import requests
import pandas as pd
import matplotlib.pyplot as plt

url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'
key = 'CompactData/IFS/Q.JP+GB.TXG_D_FOB_USD_IX?startPeriod=2017&endPeriod=2020'

'''
Key should be
    CompactData/{database ID}/{frequency}
    .{item1 from dimension1}+{item2 from dimension1}+{item N from dimension1}
    .{item1 from dimension2}+{item2 from dimension2}+{item M from dimension2}
    ?startPeriod={start date}&endPeriod={end date}

This retrieves
    data type: CompactData
    database ID: the International Financial Statistics (IFS) series.
    frequency: quarterly (frequency: Q)
    dimension1: countries, which are Japan and the U.K. (reference area: JP, GB)
    dimension2: External Trade, Goods, Deflator/Unit Value of Exports, 
                Free on Board (FOB), in US Dollars, Index (indicator: TXG_D_FOB_USD_IX)
    time period: startPeriod = 2017 and endPeriod = 2020
'''

data = (requests.get(f'{url}{key}').json()['CompactData']['DataSet']['Series'])

# In the following process, I only use Japan as my test. (Japan is in data[0])
country_code = data[0]['@REF_AREA']

data_list = [[obs.get('@TIME_PERIOD'), obs.get('@OBS_VALUE')]
             for obs in data[0]['Obs']]
df = pd.DataFrame(data_list, columns=['date', 'value'])
df = df.set_index(pd.to_datetime(df['date']))['value'].astype('float')

plt.figure()
title = f'{country_code}, External Trade, Goods, Deflator/Unit Value of Exports,\n\
        Free on Board (FOB)'
df.plot(title=title, colormap='Set1')
plt.xlabel('date')
plt.ylabel('US Dollars')
plt.show()