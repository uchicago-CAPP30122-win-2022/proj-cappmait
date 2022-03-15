# The Worldwide Trade Impact of COVID-19

In our project, we analyze and reveal some important facts about the trade 
sector during pandemic by using dashboards and a report. We collected export 
data from international organizations’ databases (e.g.WTO Database, UN comtrade 
and IMF trade flows), COVID-19 and economic indicators data (e.g. Our World in 
Data & World Bank). Then, we leveraged them by creating an interactive dashboard 
and providing an analysis report. 

### Built with
* Python
* Plotly
* Dash/Cytoscape
* Networkx
* Pyvis.network
* HTML/CSS

### Data sources
* [WTO Merchandise trade values annual dataset](https://www.wto.org/english/res_e/statis_e/trade_datasets_e.htm) : overall trade volume in product details (SITC)
* [IMF Direction of Trade Statistics (DOTS)](https://data.imf.org/?sk=9d6028d4-f14a-464c-a2f2-59b2cd424b85) : trade flows for worldwide countries
* [UN Comtrade](https://comtrade.un.org) : trade flows between top30 countries in product details (HS code)
* [Our World in Data Covid-19 data](https://github.com/owid/covid-19-data/tree/master/public/data) : covid death/cases and stringent index
* [World Bank World Development Indicators](https://databank.worldbank.org/source/world-development-indicators) : gdp, inflation, exchange rate
* [Country code](https://gist.github.com/tadast/8827699) : map alpha 2/3 codes to country name

# How to use
To use this application, run the following steps.

1. Make clone the repository.
```sh
git clone git@github.com:uchicago-CAPP30122-win-2022/proj-cappmait.git
```
2. Navigate to the repository.
```sh
cd ./proj-cappmait
```
3. Install Environment.
```sh
bash ./install.sh
```
4. Activate the virtual environment.
```sh
source env/bin/activate
```
5. Launch the dashboard and open the address on the command line
```sh
ipython3 -m proj_cappmait
```
6. When you successfully run our program, please input either of these arguments
for running our products
 - `dashboard` for open dashboards
 - `analysis` for open analysis report
 - `getdata` for download data from various sources (optional)
 - anything else for exit the program

7. The `getdata` has subcommands. Users can input these arguments to 
run the specific commands
 - `unapi` for retrieve data from the UN
  - `imfapi` for retrieve data from the IMF
 - `loadcsv` for download other files (such as WTO, OWID, World bank) 
   and clean these data
 - anything else for exit the program


