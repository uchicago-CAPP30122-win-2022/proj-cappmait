'''
Module to calculate PageRank. 
'''
import pandas as pd
import numpy as np
import random
import csv

def get_pagerank():
    '''
    Calculate the Page Rank value for all countries and save to csv file. 
    The Page Rank here is using the damping factor 0.9. 

    Input: None

    Output: A list of tuple with country code and Page Rank. This data is also saved in csv.
    '''
    partners = pd.read_csv("../data/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})

    pagerank = PageRank(partners, 0.9)
    pagerank.compute_transition()
    print("Running simulation.")
    pagerank_dct = pagerank.compute_pagerank(10000000, 1)

    pagerank_lst = [(pagerank.country_list[i], p) for i, p in pagerank_dct.items()]
    pagerank_lst = sorted(pagerank_lst, key=lambda x:x[1], reverse=True)

    with open('../data/pagerank.csv', 'w') as f:
        write = csv.writer(f)
        for pagerank_tup in pagerank_lst:
            write.writerow(pagerank_tup)

    return pagerank_lst


class PageRank:
    '''
    Class for calculating PageRank.
    '''

    def __init__(self, partners, d):
        '''
        A constructor. 

        Input: 
            partners(Pandas Dataframe): An IMF data of bi-trade (from exporter = source to importer = target) 
            in 2019 and 2020. 
            d(float): A damping factor. Typically 0.9. 

        Attributes:
            n(int): A number of countries
            country_list: A list of country
            out_degree(1d numpy array): Count outflows from each country
            counts(2d numpy array): Count link between countries
            markov(2d numpy array): A transition matrix from row country to column country
            pagerank(dict): The key is country code and value is calculated pagerank value
            d(float): A damping factor. 
        '''
        self.n = len(partners["from_code"].unique())
        self.country_list = list(partners["from_code"].unique())
        self.out_degree = np.zeros(self.n)
        self.counts = np.zeros((self.n, self.n))
        self.markov = np.zeros((self.n, self.n))
        self.pagerank = dict()
        self.d = d
        
        for _, _, _, from_code, _, to_code in partners.itertuples(index=False):
            if to_code in self.country_list:
                from_index = self.country_list.index(from_code)
                to_index = self.country_list.index(to_code)
                self.out_degree[from_index] += 1
                self.counts[from_index, to_index] += 1

    def compute_transition(self):
        '''
        Build a markov chain matrix. 
        '''
        for i in range(self.n):
            for j in range(self.n):
                self.markov[i, j] = (self.d * self.counts[i,j]/self.out_degree[i]) + ((1-self.d)/self.n)

    def compute_pagerank(self, trial, seed):
        '''
        Compute pagerank for each country.

        Input:
            trial(int): A number of trials to move random surfer. 
            seed(int): A random seed. 
        '''
        random.seed(seed)
        page = random.randint(0, self.n - 1)
        for _ in range(trial):
            pre_pagerank = self.pagerank.get(page, 0)
            self.pagerank[page] = pre_pagerank + 1/trial
            r = random.uniform(0.0, 1.0)
            psum = 0.0
            for j in range(self.n):
                psum += self.markov[page, j]
                if psum > r:
                    page = j
                    break
        return self.pagerank

    def __repr__(self):
        return f'(pagerank = {self.pagerank})'
