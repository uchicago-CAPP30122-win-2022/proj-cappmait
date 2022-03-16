'''
Module for doing analysis
'''

######## Import Packages & Set Options ###########
import networkx as nx
import pandas as pd
import plotly.express as px
import statsmodels.api as sm

from dash import Dash
from dash import dcc
from dash import html
from pyvis.network import Network
from itertools import combinations

pd.options.mode.chained_assignment = None

###### List of data ######
'''
1. UN comtrade data for top 30 major exporters
2. WTO Merchandise Trade Data (Entire World)
3. IMF Trading Partners Data
4. OWID Covid Data
5. World Bank Economic Data
'''

########## Helper Function ##################
# 1. Plotly
labels = {'country_code': 'Country',
          'comm_desc': 'Commodities',
          'cases_per_pop_percent': 'Total Cases Per Population (%)',
          'growth': 'Merchandise Export Value (%YoY)',
          'stringency_index': 'Stringency Index',
          'continent': 'Continent',
          'current_gdp_2020': '2020 Nominal GDP (USD)',
          'export_2019': 'Export Value in 2019',
          'weighted_stringent' : 'Export-Adjusted Stringency Index',
          'deg_centrality': 'Degree Centrality',
          'bet_centrality': 'Betweeness Centrality',
          'count_open': 'Number of Times in the Open Triangle Status'
         }

def px_scatter(df, x, y, color, hover_name, size, labels, title_text):
    '''
    Create a scatterplot using plotly
    Inputs:
        df (DataFrame): a dataframe
        x (str): Name of a column plotting in x axis
        y (str): Name of a column plotting in y axis
        color (str): Name of a column used to assign color on
        hover_name (str): Name of the column appearing in the hover tooltip
        size (str): Name of a column determining size of mark
        labels (dict): A key value pair for overwriting value on the axis
        title_text (str): A title of graph
    Return:
        (Figure): A scatter plot
    '''

    fig = px.scatter(df, x=x, y=y, color=color, hover_name=hover_name,
                     size=size, size_max=55, height = 550, width = 600,
                     trendline = 'ols', trendline_scope = "overall",
                     range_y = [-20, 20], labels = labels)
    fig.update_traces(textposition = 'top center', showlegend = False)
    fig.update_layout(title_text=title_text,
                      font_family="Arial",
                      uniformtext_minsize=8,
                      uniformtext_mode='hide')
    return fig

def px_hbar(df, x, y, text, range_x, labels, title_text, hover_name=None):
    '''
    Create a horizontal bar chart using plotly
    Inputs:
        df (DataFrame): a dataframe
        x (str): Name of a column plotting in x axis
        y (str): Name of a column plotting in y axis
        text (str): Name of a column appearing in the chart
        range_x (list): A two-member list determine lowest and highest value
            on the x axis
        labels (dict): A key value pair for overwriting value on the axis
        title_text (str): A title of graph
        hover_name (str): A column that appears when hovering
    Return:
        (Figure): A bar plot
    '''

    fig = px.bar(df, x=x, y=y, text=text, range_x=range_x, labels=labels,
                 hover_name=hover_name, orientation='h',
                 text_auto='.4f', height=550, width=600)
    # fig.update_traces(textposition='top center', showlegend = False)
    fig.update_layout(title_text=title_text,
                      font_family="Arial",
                      uniformtext_minsize=8,
                      uniformtext_mode='hide')
    return fig


# 2. Created Undirected Export DataFrame
def undirected_export(df, from_country_col, to_country_col):
    '''
    Transform the DataFrame that have a properties of relationship
    between trade partners to an undirect way
    (First country depends on their first alphabet)

    Inputs:
        df (DataFrame): a trade dataframe
        from_country_col (int): a column index that represents the exporter
        to_country_col (int): a column index that represents the destination

    Return:
        (DataFrame): A New DataFrame that abolish the relationship between
            columns
    '''

    df = df.dropna()
    relation = []
    for row in df.itertuples():
        country_1 = row[from_country_col + 1]
        country_2 = row[to_country_col + 1]
        if country_1 < country_2:
            rel = country_1 + "-" + country_2
        else:
            rel = country_2 + "-" + country_1
        relation.append(rel)

    df['relation'] = relation
    df = df.groupby("relation").agg('sum').reset_index()

    countries = df["relation"].str.split("-", n = 1, expand = True)
    df['country_1'] = countries[0]
    df['country_2'] = countries[1]

    return df


# 3. Create Network Chart
# Create Network Graph
def create_network(df, node_size_col_name, from_country_col, to_country_col,
                   curr_exp_value_col, prev_exp_value_col, output_path):
    '''
    Create a network graph of export dataframe.

    Inputs:
        df (DataFrame): a dataframe
        node_size_col_name (str): a column name that will be adjust the
            node size
        from_country_col (int): a column index that represents the exporter
        to_country_col (int): a column index that represents the destination
        curr_exp_value_col (int): a column index that
            represents the current export
        prev_exp_value_col (int): a column index that
            represents the previous export
        output_path (str): an output location to keeping file

    Return:
        Network in html file
    '''

    # Size of node
    df_long = (pd.melt(df, [node_size_col_name]).groupby('value').agg('sum'))

    # Create Network
    network = Network(height=575, width=1175, notebook=True)

    for edge in df.itertuples():
        reporter = edge[from_country_col + 1]
        dest = edge[to_country_col + 1]
        export_val = edge[curr_exp_value_col + 1]
        prev_exp_val = edge[prev_exp_value_col +1]
        network.add_node(reporter, reporter,
                         title=reporter,
                         size=float(df_long.loc[reporter]))

        network.add_node(dest, dest, title=dest,
                         size=float(df_long.loc[dest]))

        # Color depend on difference
        if export_val < prev_exp_val:
            network.add_edge(reporter, dest, value=export_val, color='#FF6961')
        else:
            network.add_edge(reporter, dest, value=export_val, color='#3EB489')

    neighbors = network.get_adj_list()

    # add neighbor data to node hover data
    for node in network.nodes:
        node['title'] += ' Partners:<br>' + '<br>'.join(neighbors[node['id']])
        node['value'] = len(neighbors[node['id']])

    network.repulsion(node_distance=200, spring_length=300)
    return network.show(output_path)


# Dict to DataFrame
def dict_to_df(dictionary, col_names, sort_by, top_n):
    '''
    Transform dict to two-column DataFrame (key and value)

    Inputs:
        dictionary (dict): A dictionary
        col_names (list): Two elements list represent column names
        sort_by (str): A value sorter column
        top_n (int): The number of row that we want to return

    Return
        (DataFrame): A two columns dataframe
    '''
    df = pd.DataFrame(dictionary.items(), columns=col_names )
    df = df.sort_values(sort_by, ascending=False)
    df = df.head(top_n)

    return df

# Open Triangle
def pot_triangle(graph, col_names, sort_by, top_n):
    '''
    Identify the potential triangle among three trading partners

    Inputs:
        graph (Graph): A networkx Graph Object
        col_names (list): Two elements list represent column names
        sort_by (str): A value sorter column
        top_n (int): The number of row that we want to return

    Return:
        (DataFrame): a DataFrame of potential pairs that are highly recommended
            to create triangle between them and the count of how many times
            both are the neighborhoods of other nodes.
    '''

    rec = {}
    for node in graph.nodes():
        for nb_1, nb_2 in combinations(graph.neighbors(node), 2):
            if not graph.has_edge(nb_1, nb_2):
                rec[(nb_1, nb_2)] = rec.get((nb_1, nb_2), 0) + 1

    rec_df = dict_to_df(rec, col_names, sort_by, top_n)

    return rec_df


################### Preparing Data ############################
# Read Raw Data
un_comtrade = pd.read_csv('proj_cappmait/data/un_comtrade_top30.csv',
                          dtype = {'rtCode': 'str', 'ptCode': 'str',
                                   'cmdCode': 'str'})

owid_covid = pd.read_csv('proj_cappmait/data/owid_covid_data_cleaned.csv',
                         usecols = ['iso_code', 'period', 'total_cases',
                                    'new_cases', 'stringency_index'])

owid_country = pd.read_csv('proj_cappmait/data/owid_country_info.csv',
                         usecols = ['iso_code', 'continent', 'location',
                                    'population'])

wto_export = pd.read_csv(
    "proj_cappmait/data/merchandise_values_annual_dataset.csv"
)
wto_export = wto_export[(wto_export['Indicator'] == 'Export') &
                        (wto_export['ProductCode'] == 'TO')]

imf_ex_im = pd.read_csv(
    "proj_cappmait/data/imf_import_export_cleaned.csv"
).dropna()

wb_econ = pd.read_csv("proj_cappmait/data/world-bank-econ-data.csv")


# Create Processed Table for analysis
## 1. UN Comtrade
un_comtrade_pivot = un_comtrade.pivot(['reporter_iso', 'partner_iso',
                                       'comm_code', 'comm_desc'],
                                       'year', 'trade_val').reset_index()
un_comtrade_pivot.columns = ['reporter_iso', 'partner_iso', 'comm_code',
                             'comm_desc', 'export_2019', 'export_2020']

## 2. Owid Covid Data
owid_df = owid_covid[owid_covid['period'] == '2020']
owid_df.rename(columns={'period':'year'}, inplace=True)

### Merge to owid_country and add total cases per population
owid_df = owid_df.merge(owid_country, how = 'inner', on = 'iso_code')
owid_df['cases_per_pop_percent'] = (owid_df['total_cases'] /
                                    owid_df['population'] * 100)

## 3. WTO export
wto_export_pivot = wto_export.pivot(['ReporterISO3A', 'Reporter'],
                                    'Year', 'Value').reset_index()
wto_export_pivot['growth'] = ((wto_export_pivot[2020] /
                              wto_export_pivot[2019] - 1) * 100)

## 4. IMF calculate growth and drop 2019
imf_ex_im['growth'] = (imf_ex_im['2020'] / imf_ex_im['2019'] - 1) * 100


############## Plotly Graph #####################
# Part 1
q1_df = wto_export_pivot[wto_export_pivot[2019] > 20000]
q1_df.columns = ['country_code', 'country_name', 'export_2019',
                 'export_2020', 'growth']
q1_winner_df = (q1_df.dropna()
                .sort_values('growth', ascending=False).head(14))
q1_winner_bar = px_hbar(df=q1_winner_df, x='growth',
                        y='country_code', text='growth',
                        range_x=[-5,20], labels=labels,
                        title_text="Top Winner Countries")

q1_loser_df = (q1_df.dropna()
                .sort_values('growth', ascending=True).head(20))
q1_loser_bar = px_hbar(df=q1_loser_df, x='growth',
                        y='country_code', text='growth',
                        range_x=[-100,5], labels=labels,
                        title_text="Top Loser Countries")

q1_comm_df = (un_comtrade_pivot.groupby(['comm_code', 'comm_desc'])
              .agg('sum').reset_index())
q1_comm_df = q1_comm_df[['comm_code', 'comm_desc',
                         'export_2019', 'export_2020']]
q1_comm_df['comm_code'] = q1_comm_df['comm_code'].map(str)
q1_comm_df['growth'] = ((q1_comm_df['export_2020'] /
                         q1_comm_df['export_2019'] - 1) * 100)
q1_comm_winner_df = (q1_comm_df.dropna()
                     .sort_values('growth', ascending=False)
                     .head(20))
q1_comm_winner_bar = px_hbar(df=q1_comm_winner_df, x='growth',
                             y='comm_code', text='growth',
                             range_x=[0,50], labels=labels,
                             title_text="The Star Group of Commodities",
                             hover_name='comm_desc')

q1_comm_loser_df = (q1_comm_df.dropna()
                    .sort_values('growth', ascending=True)
                    .head(20))
q1_comm_loser_bar = px_hbar(df=q1_comm_loser_df, x='growth',
                             y='comm_code', text='growth',
                             range_x=[-100,5], labels=labels,
                             title_text="The Dog Group of Commodities",
                             hover_name='comm_desc')


# Part 2
q2_scat1_df = wto_export_pivot.merge(owid_df, how='inner',
                                     left_on='ReporterISO3A',
                                     right_on='iso_code')
q2_scat1_df = q2_scat1_df.loc[:, ~q2_scat1_df.columns.isin(['iso_code', 
                                                           'year',
                                                           'new_cases',
                                                           'location'])]
q2_scat1_df.columns = ['country_code', 'country_name', 'export_2019',
                       'export_2020', 'growth', 'total_cases',
                       'stringency_index', 'continent', 'population',
                       'cases_per_pop_percent']
q2_scat1_df = q2_scat1_df.dropna()

q2_scat1 = px_scatter(
    q2_scat1_df,
    x="cases_per_pop_percent",
    y="growth",
    color="continent",
    hover_name="country_name",
    size='export_2019',
    labels=labels,
    title_text=
        'Relationship between the cases per population to The Export Growth')

q2_scat2 = px_scatter(
    q2_scat1_df,
    x="stringency_index",
    y="growth",
    color="continent",
    hover_name="country_name",
    size='export_2019',
    labels=labels,
    title_text=
        'Relationship between the Stringency Index to the Export Growth')

## Commodities Scatterplot
q2_scat2_df = un_comtrade_pivot.merge(owid_df, how = 'inner',
                                     left_on = 'reporter_iso',
                                     right_on = 'iso_code')
q2_scat2_df['weighted_stringent'] = (q2_scat2_df['export_2019'] *
                                     q2_scat2_df['stringency_index'])
q2_scat2_df = q2_scat2_df.loc[:,
                              q2_scat2_df.columns.isin(['comm_desc',
                                                        'export_2019',
                                                        'export_2020',
                                                        'weighted_stringent'])
                             ]
q2_scat2_df = q2_scat2_df.groupby('comm_desc').agg('sum').reset_index()
q2_scat2_df['growth'] = ((q2_scat2_df['export_2020'] /
                          q2_scat2_df['export_2019'] - 1) * 100)
q2_scat2_df['weighted_stringent'] = (q2_scat2_df['weighted_stringent'] /
                                     q2_scat2_df['export_2019'])

q2_scat3 = px_scatter(
    q2_scat2_df,
    x="weighted_stringent",
    y="growth",
    color="comm_desc",
    hover_name="comm_desc",
    size='export_2019',
    labels=labels,
    title_text='The Government Stringency Index to Commodities'
)

## Regression
wb_econ_2020 = wb_econ[wb_econ["time"] == 2020]

q2_reg_df = wto_export_pivot.merge(wb_econ_2020, how='inner',
                            left_on='ReporterISO3A',
                            right_on='country_code')
q2_reg_df = q2_reg_df.merge(owid_df, how='left',
                            left_on=['ReporterISO3A'],
                            right_on=['iso_code'])
q2_reg_df = q2_reg_df.dropna()

### Filter Outlier
q2_reg_df = q2_reg_df[(q2_reg_df['growth'] >= -100) &
                      (q2_reg_df['growth'] <= 100)]

### Linear Regression
endog = q2_reg_df['growth']
exo = q2_reg_df[['cases_per_pop_percent', 'stringency_index',
                 'inflation', 'exchange_rate']]

exo = sm.add_constant(exo)
mod = sm.OLS(endog, exo)
results = mod.fit()
summary = results.summary()
summary_table_html = summary.tables[1].as_html()


# Part 3
## IMF whole world
imf_undirect = undirected_export(imf_ex_im, 3 ,5)
imf_undirect  = imf_undirect[['country_1', 'country_2', '2019', '2020']]
imf_und_filter = imf_undirect[imf_undirect['2019'] > 5000]

create_network(imf_und_filter,'2020', 0, 1, 3, 2,
               'proj_cappmait/product/assets/imf_2020.html')

## UN Export
un_undirect = undirected_export(un_comtrade_pivot, 0, 1)
un_undirect.columns = ['year', 'relation', 'export_2019',
                       'export_2020', 'country_1', 'country_2']

create_network(un_undirect,'export_2020', 4, 5, 3, 2,
               'proj_cappmait/product/assets/un_2020.html')

## Example Some Product
### Pharmaceutical Products
un_pharma = un_comtrade_pivot[un_comtrade_pivot['comm_code'] == 30]
un_pharma = undirected_export(un_pharma, 0, 1)
un_pharma.columns = ['year', 'relation', 'export_2019',
                     'export_2020', 'country_1', 'country_2']

create_network(un_pharma,'export_2020', 4, 5, 3, 2,
               'proj_cappmait/product/assets/un_pharma_2020.html')

### Vehicle
un_vehicle = un_comtrade_pivot[un_comtrade_pivot['comm_code'] == 87]
un_vehicle = undirected_export(un_vehicle, 0, 1)
un_vehicle.columns = ['year', 'relation', 'export_2019',
                      'export_2020', 'country_1', 'country_2']

create_network(un_vehicle,'export_2020', 4, 5, 3, 2,
               'proj_cappmait/product/assets/un_vehicle_2020.html')

## Centrality
imf_net = nx.from_pandas_edgelist(imf_undirect, 'country_1', 'country_2')

deg_cent = nx.degree_centrality(imf_net)
deg_df = dict_to_df(deg_cent, ['country', 'deg_centrality'],
                    'deg_centrality', 20)
deg_hbar = px_hbar(
    df=deg_df, x='deg_centrality', y='country', text='deg_centrality',
    range_x = [0.9,1], labels=labels,
    title_text="Top 20 of Countries Having the Highest Degree Centrality")

bet_cent = nx.betweenness_centrality(imf_net)
bet_df = dict_to_df(bet_cent, ['country', 'bet_centrality'],
                    'bet_centrality', 20)
bet_hbar = px_hbar(
    df=bet_df, x='bet_centrality', y='country', text='bet_centrality',
    range_x = [0.005,0.015], labels=labels,
    title_text="Top 20 of Countries Having the Highest Betweeness Centrality")

rec_df = pot_triangle(imf_net, ['pairs', 'count'], 'count', 20)
rec_df['pairs'] = rec_df['pairs'].map(str)
rec_hbar = px_hbar(
    df=rec_df, x='count', y='pairs', text='count', range_x=[100, 160],
    labels=labels, title_text = "Top 20 of Potential Partners")


######## List of Text ###############
TITLE = "The Analysis of Export Sector During Pandemic"
INTRODUCTION = '''The COVID-19 was one of the significant adverse event to our 
    world. It made our world more vulnerable, and it drastically impacted to 
    the global economy. One of the sector that experienced downfall was the 
    trade sector. It is because the government all over the world implemented 
    the tightening policies, particularly in manufacturing and transportation. 
    As a result, there are more restriction in the export process, 
    which made the decrease in export. Some exporters experienced supply 
    shortage because the factory could not deliver commodities on time, 
    some of them cannot find ships, cruises or cargos since the workers 
    cannot work at full capacity. These adverse events made the export sector 
    slowdown,and it is very interesting to find out what happenned
    to the export sector during the pandemic in detail

    In this part, we will analyse the impact of the pandemic to the 
    global trade. We divide the analysis into three parts. In part one, 
    we will find which countries are the winner and loser during pandemic. 
    Then, in part two, we will do the correlation analysis 
    between the export growths and major important factor that occured 
    during the pandemic. Lastly, we will observe the network of trade. 
    How the pandemic affect the network of trade?. Which country is the 
    most important hub and become the center in terms of export?. Which 
    supply chain of commodities were damaged during the pandemic?'''
TOPIC1 = 'Part 1: The Winners / Losers of the Pandemic Crisis'
CONTENT1_1 = '''We begin the first part by looking at the winners and
    losers during the pandemic. We use the WTO data that has all exporters data.
    Filtering out some very small countries. In summarize, The winners were
    Vietnam, Chile, Ireland. China and Hong Kong also grew at 3.63 
    percent and 2.59 percent respectively. Meanwhile, the losers were Libya, 
    Iraq, Nigeria and lots of countries suffered from decrease in export 
    in this period.'''
CONTENT1_2 = '''In terms of commodities, as classified by the HS Code. We use
    the UN comtrade data that has the commodities export data
    The stars of this group are textiles, vegetables, food,
    phamaceutical products and electronic devices. Meanwhile, the dogs 
    of this group are artworks, aircraft, vehicles and travel goods.'''
TOPIC2 = 'Part 2: Impact of the Pandemic to the World Trade Sector'
CONTENT2_1 = '''In this part, we will focus on the correlation analysis between 
    the merchandise trade and the pandemic. Besides the pandemic affect 
    the number of workers for whichever reasons. For example, restriction on 
    the number of workers working on the site and the shortage of worksers 
    due to the infection and quarantine. Moreover, the downfall in trade 
    are directly caused by the government policy. As the government must 
    maintain balance between life and economy, and, perhaps, life is more 
    important than the economy.

    We use the data from WTO to measure the impact of the pandemic to 
    the growth in export. The scatterplot is shown below. We see that 
    there are some 'negative' correlation between the total cases 
    per population (%) to the export growth (2020 to 2019), although it 
    somewhat vague.'''
CONTENT2_2 = '''Note that the horizontal axis is total cases per population and 
    the vertical axis is the growth in export value (%YoY), and the color 
    represents its continent. Despite the fact that, in general, more cases, 
    more slowdown in trade, some countries still experienced
    growth such as China, Viet Nam and Hong Kong.

    In the next graph, we analyse the effect of the government policies 
    response to COVID-19 to the export sector

    To measure the "strictness" of policy responses, The University of Oxford 
    released the stringency index, which measures the level of "tightening" in 
    the government policies during the pandemic.
    We hypothesised that if countries imposed policies more tighter, 
    the level of export values value should lower as the business activities 
    had to temporarily shut down. As consistent to our hypothesis, the following 
    graph show that more tightening the policies are, more 
    decreasing in the economic activity, particularly in the export sector. 
    This trend is quite general for almost all country, 
    except for one country - China, which have a very high degree of lockdown, 
    but still experience growth. The potential reason is that China can quickly 
    control the pandemic (by implementing a high degree of lockdown), and 
    limit the number of cases, and then boost its economy after the situation 
    seemed recovered. '''
CONTENT2_3 = '''In the next subpart, we shift our analysis into the commodities
    side. We classify the products by using the standard HS Code that we got 
    from the UN commodities trade data. However, since the UN trade data 
    is enormous, we can get only part of them. Specifically, we only get 
    top 30 major exporters, which are enough, because they cover around 
    70 percent of global trade.

    We plot the relationship between the exported-adjusted stringent index and 
    the export of commodities. At first sight, you might wonder why the 
    correlation between growth and stringency is mildly positive, but if we 
    look closely, the main drivers during the pandemic was electrotronic 
    devices (which we must need to setup our home office!), and phamaceutical 
    products. This products had lots of demand. Even the government restricted 
    some activities, it cannot slowdown the production and eventually must 
    export in some way. However, durable goods such as vehicle and clothes 
    experienced slow down in growth.'''
CONTENT2_4 = '''We conclude this section by running a regression analysis of 
    the export growth ,the number of patients, the stringent index, average 
    inflation, and average exchange rate. The regression results show that 
    there are very modest negative relationship between the cases, the 
    stringency index and the export growth. However, due to the limited time, 
    this is not a super accurate model. There are lots of things to do for
    improvement, for example, this model still suffers from the 
    autocorrelation problem as suggest by Durbin-Watson statistics
    is very close to 2.''' 
TOPIC3 = 'Part 3: The Trading System Network'
CONTENT3_1 = '''In this part, we will analyse the global trade as a network.
    The network of trade is like other network that we know in everyday lives 
    like social network. Moreover, the network of trade also comprises 
    of the nodes that represent country and edges that represent the connection. 
    To make things simple, we consider for undirected graphs (rather than 
    using directed graph as contradict to basic intuition). First of all, 
    we calculate the sum of trade for two countries, if the value is high, 
    it means two countries have a strong connection in terms of export, 
    and vice versa. Then, we use this calculation to plot these data as the 
    undirected graph by the vertices are a country and the edges are the sum 
    of export between two countries. Moreover, the color on edges represents 
    the change in trade value (green means trade value in 2020 was higher, 
    and red means trade in 2020 was lower) and the size of edges represents 
    the magnitude of trade value.

    We start the analysis by looking at the network of trade of entire world by
    using the IMF data. The IMF data provides the trade value between 
    two countries over the world. 
    As we can see in the below network, in general
    most countries usually trade with other distance-proximity countries, 
    for example, USA has close ties in trading with Canada and Mexico. 
    While China has close ties with Hong Kong, Japan and Vietnam. Moreover, 
    most countries experienced the contraction in trade during the pandemic. 
    We can see their are many reds all over the graph. Except one country, 
    China, which the export grews during the pandemic. Note that we cut 
    some insignificant trading partners out of graph by filtering out the 
    connection that has the export value less than USD5,000M per year. '''
CONTENT3_2 = '''
    To be more specific (and reduce over-dimensionality of graph), 
    we look at the network of top30 major exporters in the world (Its 
    network looks nice!, like a sphere). We reiterate that China were the winner 
    during the pandemic! It had a very strong bond with other top countries like
    Hong Kong, Viet Nam, Japan, or even USA.'''
CONTENT3_3 = '''In the next part, we monitor a winner and loser in terms
    of commodity. We choose 'pharmaceutical product' as a winner. We can see
    lots of green line in this graph, and we choose 'vehicle' as loser. We
    see lots of red line in this graph, particularly the big red line connecting
    the USA to Mexico, Canada and Japan.'''
SUBTOPIC3_1 = "Graph Statistics and Analysis"
CONTENT3_1_1 = '''We conclude this part with presents some key finding in 
    the network. We want to find which countries are the most important 
    countries in terms of export, and there are any recommendation to find 
    the new trade partners for any country. we turn back to the IMF entire 
    world trade data for do an analysis.

    First, we measure the centrality or the importance of node. We calculate two 
    centrality measures, the degree centrality and the betweeness centrality

    The degree centrality gives you a number measuring the numbers of
    adjacent neighbors to each node. We plot the top 20 countries who have
    the highest degree centrality in the folowing graph. The Great Britain,
    The Netherlands, Italy and USA  are the group of countries that are 
    important in terms of export (They are connected with lots of
    countries).'''
CONTENT3_1_2 = '''Another number that measures centrality is called 
    betweeness centrality. The betweeness centrality quantifies 
    how many of times that the shortest path between any two nodes 
    cross this nodes. We plot the top countries below. Consistent to the
    earlier result, The Great Britain, The Netherlands, USA, and Italy
    are the most important countries'''
CONTENT3_1_3 = '''Suppose that the trading network is well-connected. There
    is still a room to tighten the network. In this part, we build a 
    recommendation system to find out a new pair in the trade network. 
    In summary, we use a concept of the open triangle, which we search for 
    three countries that have just two connection. The left one connection 
    is called the open triangle. Then, we count the number of times that the 
    open triangle appears in every node. More number is, more potential 
    partners should become!. We plot the results in the following graph. 
    The result is quite interesting. Many countries are very close in 
    terms of distance and have a strong connection with other members in 
    region. But why they cannot do a bilateral trade? It is because of the 
    polictical conflicts between two partners. For example, 
    the conflicts among lots of countries in the middle east makes the
    bilateral trading between Saudi Arabia to Qatar, Iran, Israel impossible.'''
FOOTER = "\n Analysed by CAPPMAIT, part of the project in CAPP 30102"

############### Dash Report ########################
app = Dash(__name__)

app.layout = html.Div([
    html.H1(TITLE),
    html.P(INTRODUCTION),
    html.H2(TOPIC1),
    html.P(CONTENT1_1),
    dcc.Graph(id='winner_coun', figure=q1_winner_bar),
    dcc.Graph(id='loser_coun', figure=q1_loser_bar),
    html.P(CONTENT1_2),
    dcc.Graph(id='winner_comm', figure=q1_comm_winner_bar),
    dcc.Graph(id='loser_comm', figure=q1_comm_loser_bar),
    html.H2(TOPIC2),
    html.P(CONTENT2_1),
    dcc.Graph(id='scatter_1', figure=q2_scat1),
    html.P(CONTENT2_2),
    dcc.Graph(id='scatter_2', figure=q2_scat2),
    html.P(CONTENT2_3),
    dcc.Graph(id='scatter_3', figure=q2_scat3),
    html.P(CONTENT2_4),
    html.H2(TOPIC3),
    html.P(CONTENT3_1),
    html.H3("Global Trading Network"),
    html.Iframe(src=app.get_asset_url("assets/imf_2020.html"),
                style={"height": "600px", "width": "1200px"},
                title="Global Trading Network"),
    html.P(CONTENT3_2),
    html.H3("Top 30 Exporters Trading Network"),
    html.Iframe(src=app.get_asset_url("assets/un_2020.html"),
                style={"height": "600px", "width": "1200px"}),
    html.P(CONTENT3_3),
    html.H3("Pharmaceutical Trading Network"),
    html.Iframe(src=app.get_asset_url("assets/un_pharma_2020.html"),
                style={"height": "600px", "width": "1200px"}),
    html.H3("Vehicle Trading Network"),
    html.Iframe(src=app.get_asset_url("assets/un_vehicle_2020.html"),
                style={"height": "600px", "width": "1200px"}),
    html.H3(SUBTOPIC3_1),
    html.P(CONTENT3_1_1),
    dcc.Graph(id='cen_deg', figure=deg_hbar),
    html.P(CONTENT3_1_2),
    dcc.Graph(id="between", figure=bet_hbar),
    html.P(CONTENT3_1_3),
    dcc.Graph(id="triangle" ,figure=rec_hbar),
    html.Footer(FOOTER)
    ],
    style={'marginLeft': 100, 'marginRight': 100, 'marginTop': 50, 
           'marginBottom': 50, 
           'backgroundColor':'#FAFAFA',
           'border': 'thin lightgrey groove', 
           'padding': '40px 40px 40px 40px',
           'font-family': 'Arial',
           'color': '#000000',
           'line-height': '150%'}
)
