import pandas as pd
import numpy as np
import random
import csv

def get_pagerank_data():
    '''
    Calculate the Page Rank value for all countries and save to csv file. 
    The Page Rank here is using the damping factor 0.9. 
    The calculation is based on existence of trade both in 2019 and 2020. 
    (Count as trade when volume is more than 0 in both 2019 and 2020)

    Input: None

    Output: A list of tuple with country code and Page Rank. This data is also saved in csv.
    '''
    partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
    partners = partners.dropna()

    pagerank = PageRank(partners, 0.9)
    pagerank.compute_transition()
    pagerank_dct = pagerank.compute_pagerank(10000000, 1)

    pagerank_lst = [(pagerank.country_list[i], p) for i, p in pagerank_dct.items()]
    pagerank_lst = sorted(pagerank_lst, key=lambda x:x[1], reverse=True)

    with open('rawdata/pagerank.csv', 'w') as f:
        write = csv.writer(f)
        for pagerank_tup in pagerank_lst:
            write.writerow(pagerank_tup)

    return pagerank_lst


def construct_networkgraph():
    '''
    Construct a network graph. 
    Load the partners data and pagerank data, construct country node and edge objects, 
    and add pagerank attribute to each country node. 

    Input: None

    Output: A graph object. 
    '''
    partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
    partners = partners.dropna()
    pagerank = pd.read_csv("rawdata/pagerank.csv", names=["country_code", "pagerank"], \
                dtype={"country_code":"str", "pagerank":"float"})

    graph = Graph(partners)
    graph.update_network()
    graph.update_pagerank(pagerank)
    return graph


class Graph:
    '''
    A class for network graph with nodes and edges. 
    '''

    def __init__(self, partners):
        '''
        A constructor. 

        Input: 
            partners(Pandas Dataframe): An IMF data of bi-trade (from exporter = source to importer = target) 
            in 2019 and 2020. 
        
        Attribute:
            partners(Pandas Dataframe)
            nodes(list) : A list of country node objects for whole network graph
            edges(list) : A tuple of edges for whole network graph. Each element is a tuple of 
                        source(str), target(str), and growth rate of trade volume between 2020 and 2019(float). 
            sankeynodes(list) : A list of country node objects for sankey graph
            sankeyedges(list) : A list of edges for sankey graph. Each element is a tuple of
                        source(str), target(str), trade volume in either 2019 or 2020, and color. 
        '''
        self.partners = partners
        self.nodes = dict()
        self.edges = list()
        self.sankeynodes = list()
        self.sankeyedges = list()

    def update_network(self):
        '''
        Process the partner dataframe, and build up the country node objects. 
        '''
        for volume_2019, volume_2020, from_name, from_code, to_name, to_code in self.partners.itertuples(index=False):
            if from_code not in self.nodes:
                self.nodes[from_code] = Node(from_code, from_name)
            if to_code not in self.nodes:
                self.nodes[to_code] = Node(to_code, to_name)
            if volume_2019 > 0 and volume_2020 > 0:
                self.nodes[from_code].add_partner(True, self.nodes[to_code], volume_2019, volume_2020)
                self.nodes[to_code].add_partner(False, self.nodes[from_code], volume_2019, volume_2020)

    def update_pagerank(self, pagerank):
        '''
        Process the pagerank dataframe, and add pagerank attribute to each country node. 

        Input:
            pagerank(Pandas Dataframe): A pagerank for each country. 
        '''
        for code, pagerank in pagerank.itertuples(index=False):
            self.nodes[code].pagerank = pagerank

    def find_best_partners(self, num, is_exporter):
        '''
        Find the best trading partners and add to edges. And draw a whole world network graph. 

        Input:
            num(int) : A number of best partne
            is_exporter(boolean): True if the country node is exporter, and False otherwise. 

        Output:
            nodes(list) : A list of country node objects
            edges(list) : A tuple of source(str), target(str), and growth rate of trade volume between 2020 and 2019(float). 
        '''
        for code, node in self.nodes.items():
            if is_exporter:
                best_partners = node.sort_partners(True, True)
            else:
                best_partners = node.sort_partners(False, True)
            for i in range(num):
                if i < len(best_partners):
                    self.edges.append((code, best_partners[i][0].country_code, \
                    (best_partners[i][2] - best_partners[i][1])/best_partners[i][1]))
        return self.nodes, self.edges
    
    def draw_sankey(self, country_code):
        '''
        Draw a sankey diagram. 

        Input:
            country_code(str): A country code the user selected

        Output:
            sankeynodes(list) : A list of country node objects for sankey graph
            sankeyedges(list) : A list of edges for sankey graph. Each element is a tuple of
                        source index(int), target index(int), trade volume in either 2019 or 2020, and color. 
        '''
        country_node = self.nodes[country_code]

        edges_2019_ex = self.construct_sankey(country_node, True, True)
        self.sankeynodes.append(u'\u2190 Export \u2192')
    
        edges_2019_im = self.construct_sankey(country_node, False, True)
        self.sankeynodes.append('\u2192 Import \u2190')

        importer_index = len(self.sankeynodes) - 1
        for i, (source, target, vol, color) in enumerate(edges_2019_im):
            edges_2019_im[i] = (source, importer_index, vol, color)

        edges_2020_ex = self.construct_sankey(country_node, True, False, importer_index)
        edges_2020_im = self.construct_sankey(country_node, False, False, importer_index)

        self.sankeyedges = edges_2019_ex + edges_2019_im + edges_2020_ex + edges_2020_im

        return self.sankeynodes, self.sankeyedges

    def construct_sankey(self, country_node, is_exporter, is_2019, importer_index = 0):
        '''
        Helper function for constructing a sankey diagram. 

        Input: 
            country_code(str): A country code the user selected
            is_exporter(boolean): True if the country node is exporter, and False otherwise. 
            is_2019(boolean): True if interested in 2019, and False if 2020.
            importer_index(int): The index of country serves as an importer in sankeynodes list. 
                                First it is unknown until finish processing the whole trading partners
                                in 2019, so default is 0. 

        Output:
            link(list): A temporary list of edge list       
        '''
        link = list()
        partners_lst = country_node.sort_partners(is_exporter, is_2019)[:10]
        for i, (partner, vol_2019, vol_2020) in enumerate(partners_lst):
            color = '#36559c' if is_exporter else '#b5442d'

            # Set the index of country serves as an exporter to 10 because we only look up 
            # top 10 partners. If the country serves as an importer, set to the given inporter_index. 
            middle = 10 if is_exporter else importer_index

            if is_exporter or partner.label not in self.sankeynodes:
                self.sankeynodes.append(partner.label)

            partner_idx = self.sankeynodes.index(partner.label)

            if is_2019:
                link.append((partner_idx, middle, vol_2019, color))
            else:
                partner_idx = partner_idx + importer_index + 1
                link.append((middle, partner_idx, vol_2020, color))
        return link


class Node:
    '''
    Class for each country node.
    '''

    def __init__(self, country_code, label):
        '''
        A constructor. 

        Input: 
            country_code(str): An ISO3 country code.
            label(str): A country name.

        Attributes:
            country_code(str)
            label(str)
            parents(list): A list of trading partners (node objects) which the country import from. 
            children(list): A list of trading partners (node objects) which the country export to. 
            pagerank(float): A pagerank value. 
        '''
        self.country_code = country_code
        self.label = label
        self.parents = []
        self.children = []
        self.pagerank = None

    def add_partner(self, is_children, othernode, volume_2019, volume_2020):
        '''
        Append a partner object to the partners list. 

        Input:
            is_children(boolean): If True, append to the children list. Otherwise append to the parent list.
            othernode(Node object): A node object of partner.
            volume_2019(float): A trading volume in 2019.
            volume_2020(float): A trading volume in 2020.

        Output:
            None
        '''
        if is_children:
            self.children.append((othernode, volume_2019, volume_2020))
        else:
            self.parents.append((othernode, volume_2019, volume_2020))

    def sort_partners(self, is_children, is_2019):
        '''
        Sort the partners list.

        Input:
            is_children(boolean): If True, sort to the children list. Otherwise sort to the parent list.
            is_2019(boolean): If true, sort based on 2019 trading volume. Otherwise sort based on 2020. 
        
        Output:
            A sorted list
        '''
        partners = self.children if is_children else self.parents
        if is_2019:
            return sorted(partners, key=lambda x: x[1], reverse=True)
        return sorted(partners, key=lambda x: x[2], reverse=True)

    def __repr__(self):
        return f'(country_code = {self.country_code}, label = {self.label})'


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
        
        for volume_2019, volume_2020, from_name, from_code, to_name, to_code in partners.itertuples(index=False):
            if to_code in self.country_list and volume_2019 > 0 and volume_2020 > 0:
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
        for i in range(trial):
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
