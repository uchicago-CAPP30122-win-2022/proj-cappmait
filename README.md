# What is this

In our project, we analyze and reveal some important facts about the trade sector during pandemic by using dashboards and a report. We collected export data from international organizations’ databases (e.g. WB WITS API, WTO Database, UN comtrade and IMF trade flows), COVID-19 and economic indicators data (e.g. Our World in Data & World Bank). Then, we leveraged them by creating interactive dashboards and providing an analysis report. Both products use dash and plotly as the core packages. 


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
 - `quit` for exit the program

7. (Optional) To run data collection modules, run these commands. 
```sh
cd proj_cappmait/getdata/
ipython3 un_api.py # Retrieve data from the UN
ipython3 imf_api.py # Retrieve data from the IMF
ipython3 getready_data.py # Download other files and clean data
```