'''
This module executes downloading all data other than api, 
clean whole data, and generate pagerank data.
'''

from proj_cappmait.getdata import clean_data, download_data, pagerank

def create_csv_data():
    """
    Execute download csvs and clean all the dataset
    """

    print ("Start Downloading csv data.")
    print("Downloading OWID data.")
    download_data.get_owid()
    print("Downloading WTO data.")
    download_data.get_wto()
    print("Downloading World bank data.")
    download_data.get_wb()
    print("Downloading Country code data.")
    download_data.get_countrycode()
    print("Cleaning all csv data.")
    clean_data.clean_imf()
    clean_data.clean_countrycode()
    clean_data.clean_owid()
    print("Calculating page rank.")
    pagerank.get_pagerank()
    print("Data is ready.")
