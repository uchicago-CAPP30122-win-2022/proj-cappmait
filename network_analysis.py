import pandas as pd
import numpy as np
import random
import csv


def get_pagerank_data():
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

def draw_networkgraph():
    partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
    partners = partners.dropna()
    pagerank = pd.read_csv("rawdata/pagerank.csv", names=["country_code", "pagerank"], dtype={"country_code":"str", "pagerank":"float"})

    graph = Graph(partners)
    graph.construct_network()
    graph.update_pagerank(pagerank)
    return graph

def draw_wholenetwork(graph):
    nodes, edges, weight = graph.find_best_partners(1, True)
    return nodes, edges, weight

def draw_countrynetwork(graph, country_code):
    node = graph.get_countrynode(country_code)
    return node, node.children


class PageRank:

    def __init__(self, partners, d):
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
        for i in range(self.n):
            for j in range(self.n):
                self.markov[i, j] = (self.d * self.counts[i,j]/self.out_degree[i]) + ((1-self.d)/self.n)

    def compute_pagerank(self, trial, seed):
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


class Graph:
    def __init__(self, partners):
        self.partners = partners
        self.nodes = dict()
        self.edges = list()
        self.weight = list()
        self.sankeynodes = list()
        self.sankeyedges = list()

    def construct_network(self):
        for volume_2019, volume_2020, from_name, from_code, to_name, to_code in self.partners.itertuples(index=False):
            if from_code not in self.nodes:
                self.nodes[from_code] = Node(from_code, from_name)
            if to_code not in self.nodes:
                self.nodes[to_code] = Node(to_code, to_name)
            if volume_2019 > 0 and volume_2020 > 0:
                self.nodes[from_code].add_children(self.nodes[to_code], volume_2019, volume_2020)
                self.nodes[to_code].add_parents(self.nodes[from_code], volume_2019, volume_2020)

    def update_pagerank(self, pagerank):
        for code, pagerank in pagerank.itertuples(index=False):
            self.nodes[code].pagerank = pagerank

    def find_best_partners(self, num, is_exporter):
        for code, node in self.nodes.items():
            if is_exporter:
                best_partners = node.sort_partners(True, True)
            else:
                best_partners = node.sort_partners(False, True)
            for i in range(num):
                if i < len(best_partners):
                    self.edges.append((code, best_partners[i][0].country_code))
                    self.weight.append((best_partners[i][1], best_partners[i][2]))
        return self.nodes, self.edges, self.weight

    def get_countrynode(self, country_code):
        return self.nodes[country_code]
    
    def draw_sankey(self, country_code):
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
        link = list()
        partners_lst = country_node.sort_partners(is_exporter, is_2019)[:10]
        for i, (partner, vol_2019, vol_2020) in enumerate(partners_lst):
            color = 'lightblue' if is_exporter else 'pink'
            middle = 10 if is_exporter else importer_index

            if is_exporter or partner.label not in self.sankeynodes:
                self.sankeynodes.append(partner.label)

            source = self.sankeynodes.index(partner.label)

            if is_2019:
                link.append((source, middle, vol_2019, color))
            else:
                source = source + importer_index + 1
                link.append((middle, source, vol_2020, color))
        return link



class Node:
    '''
    Class for each no
    '''
    def __init__(self, country_code, label):
        self.country_code = country_code
        self.label = label
        self.parents = []
        self.children = []
        self.pagerank = None

    def add_children(self, othernode, volume_2019, volume_2020):
        self.children.append((othernode, volume_2019, volume_2020))
    
    def add_parents(self, othernode, volume_2019, volume_2020):
        self.parents.append((othernode, volume_2019, volume_2020))

    def sort_partners(self, is_children, is_2019):
        partners = self.children if is_children else self.parents
        if is_2019:
            return sorted(partners, key=lambda x: x[1], reverse=True)
        return sorted(partners, key=lambda x: x[2], reverse=True)

    def __repr__(self):
        return f'(country_code = {self.country_code}, label = {self.label})'

