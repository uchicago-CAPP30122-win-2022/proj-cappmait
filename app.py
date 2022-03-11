from platform import node
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_html_components as html
import dash_core_components as dcc
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, MultiplexerTransform, Input, Output
import dash_cytoscape as cyto
import network_analysis as net

app = DashProxy(transforms=[MultiplexerTransform()])

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
country_code = pd.read_csv("rawdata/countries_codes_and_coordinates_new.csv")

# go to another file? 
def f(row):
    if row['Date_reported'] == '2020/3/31':
        val = '2020Q1'
    elif row['Date_reported'] == '2020/6/30':
        val = '2020Q2'
    elif row['Date_reported'] == '2020/9/30':
        val = '2020Q3'
    else:
        val = '2020Q4'
    return val

def prepare_covid_data(time_selected):
    '''
    Do data wrangling for covid data:
    i) Join two datasets on 2 digit code
    ii) Align country name to the standard names
    iii) Filter out "2020-12-31" data for all countries
    iv) Extract needed columns for plotting, e.g. alpha 3 code

    Input:
        None, running this py file would call this function and start
            data wrangling
    
    Outputs:
        dff: a cleaned dataframe for next step of plotting
    '''

    covid_data = pd.read_csv('rawdata/WHO-COVID-19-global-data.csv')
    country_code = pd.read_csv("rawdata/countries_codes_and_coordinates_new.csv")
    country_code = country_code.rename({'Country': 'country_name'}, axis = 1)
    dic = {'2020/3/31': '2020Q1', '2020/6/30': '2020Q2', '2020/9/30': '2020Q3', '2020/12/31': '2020Q4'}

    df = covid_data.join(country_code.set_index('Alpha-2code'), on = 'Country_code')
    dff = df[["country_name", "Date_reported", "Cumulative_cases", "Cumulative_deaths", "Alpha-3code"]]
    dff = dff[dff.Date_reported.isin(dic.keys())]

    dic = {1:'2020Q1', 2:'2020Q2', 3:'2020Q3', 4:'2020Q4'}
    dff['Quarter'] = dff.apply(f, axis=1)

    return dff[dff.Quarter == dic.get(time_selected)]

def build_networkelements(is_exporter):
    '''
    Build a network elements. Node is each country. Source of edge is country node, 
    and target is the best trading partner. In the exporter view, the country serve as an exporter and 
    export the most to the best trading partner. In the importer view, the country serve as an importer and
    import the most from the best trading partner. 

    Input:
        is_exporter(boolean): True if the country node is exporter, and False otherwise. 

    Output:
        elements(list): A list of graph nodes and edges. 
    '''
    graph = net.construct_networkgraph()
    nodes, edges = graph.find_best_partners(1, is_exporter)

    graph_nodes = [
        {'data': {'id': node.country_code, 'label': node.label, 'pagerank': node.pagerank}} for node in nodes.values()
    ]

    graph_edges = [
        {'data': {'source': source, 'target': target, 'weight': weight}} for source, target, weight in edges
    ]

    return graph_nodes + graph_edges

def draw_countrydashboard(val_selected):
    '''
    Update graphs given the user selected country

    Inputs:
        val_selected(str) : The user selected country
    
    Outputs:
        A tuple of graph objects
    '''
    df = product[product["ReporterISO3A"] == val_selected] 
    country_name = country_code.loc[country_code["Alpha-3code"] == val_selected, "Country"].item()

    bar_plt = plot_bar(df, country_name)

    graph = net.construct_networkgraph()
    sankey_nodes, sankey_links = graph.draw_sankey(val_selected)
    sankey_plt = plot_sankey(sankey_nodes, sankey_links, country_name)

    tree_plt = plot_tree(df, country_name)

    return (bar_plt, sankey_plt, tree_plt)


def plot_bar(df, country_name):
    '''
    Create a bar graph object

    Inputs:
        df (Pandas Dataframe): a data of products

    Outputs:
        fig(a bar graph object)
    '''
    fig = px.bar(df[df["ProductCode"] == "TO"], x="Indicator", y="Value", 
                 color="Year", barmode="group",
                 color_discrete_map = {
                    '2019': '#36559c',
                    '2020': '#b5442d'}
                 )

    fig.update_layout(
        font_color="#e7ecf5",
        title=f'{country_name}\'s Total Trade Volume in before/after Covid',
        xaxis=dict(
            title= '',
            titlefont_size=12,
            tickfont_size=10,
            title_standoff=50
        ),
        yaxis=dict(
            title= 'Trade Volume',
            titlefont_size=12,
            tickfont_size=10,
        ),
        autosize=False,
        width=600,
        height=450,
        margin=dict(
            l=100,
            r=0,
            b=50,
            t=100,
            pad=4
        ),
        paper_bgcolor= 'rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    return fig


def plot_sankey(nodes, edges, country_name):
    '''
    Create a sankey graph object

    Inputs:
        node_df(Pandas Dataframe): a data of nodes
        links_df(Pandas Dataframe): a data of links

    Outputs:
        fig(a sankey graph object)
    '''
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 5,
        thickness = 5,
        line = dict(color = "#aab0bf", width = 0.5),
        label = nodes,
        color = "#aab0bf"
        ),
        link = dict(
        source = [source for source, _, _, _ in edges], 
        target = [target for _, target, _, _ in edges],
        value =  [value for _, _, value, _ in edges],
        color = [color for _, _, _, color in edges]
    ))])

    fig.add_annotation(text="2019",
                    xref="paper", yref="paper",
                    x=0.2, y=1.00, showarrow=False), 
    fig.add_annotation(text="2020",
                    xref="paper", yref="paper",
                    x=0.75, y=1.00, showarrow=False)

    fig.update_layout(
        title = f'{country_name}\'s Trade flows in before/after Covid',
        font_color="#e7ecf5",
        autosize=False,
        width=600,
        height=700,
        margin=dict(
            l=50,
            r=20,
            b=50,
            t=50,
            pad=4
        ),
        paper_bgcolor= 'rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def plot_tree(df, country_name):
    '''
    Create a tree graph object

    Inputs:
        df (Pandas Dataframe): a data of products

    Outputs:
        fig(a tree graph object)
    '''
    fig = px.treemap(df[df["ProductCode"] != "TO"], \
        path=[px.Constant("Total"), "Indicator", "Year", "Product"], 
        color = 'Value',
        color_continuous_scale = px.colors.sequential.ice,
        values="Value")

    fig.update_layout(
        title=dict(
            text=f'{country_name}\'s Tree map in before/after Covid',
            font_color="#e7ecf5"
        ),
        autosize=False,
        paper_bgcolor= 'rgb(0,0,0,0)',
        plot_bgcolor='rgb(0,0,0,0)',
    )

    return fig


network_stylesheet = [
    {
        "selector": "node",
        "style": {
            "width": "mapData(pagerank, 0, 0.02, 1, 100)",
            "height": "mapData(pagerank, 0, 0.02, 1, 100)",
            "content": "data(id)",
            "font-size": "12px",
            "text-valign": "center",
            "text-halign": "center",
        }
    },
    {
        "selector": "edge",
        "style": {
            "line-color": "mapData(weight, -0.01, 0.01, red, blue)"
    }
    }
]

# Define Layout (dash components inside)
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
        children=[
            html.H1("Dashboard of Covid Impact and World Trading"),
            html.P(id="description",
                    children="LHS of dashboard presents worldwide situation of covid and trade network, while RHS and bottom parts enable users to\
                    dive into countries of interest and view changes in trading volumes, partners and categories from 2019 to 2020.",
                )]
        ),

    # Left
        html.Div(
            id="app-container",
            children=[
                html.Div(
                id="left-top",
                children=[
                    html.Div(
                        id = 'slider-container',
                        children = [
                            html.P(
                                id = 'slider-text',
                                children = 'Drag the slider to choose time span: ',
                            ),
                            dcc.Slider(
                                id = 'time-slider',
                                step=None,
                                marks = {
                                    1: '2020Q1',
                                    2: '2020Q2',
                                    3: '2020Q3',
                                    4: '2020Q4',
                                },
                                value = 4
                            ),
                        ],
                    ),
                    html.Div(
                        id = 'covidmap-container',
                        children = [
                            html.P(
                                "Worldwide covid cases of selected quarter",
                                id="covidmap-title",),
                                dcc.RadioItems(id='data-type-selected', value='Cumulative_deaths',
                                options = [{'label': 'cumulative cases', 'value': 'Cumulative_cases'},
                                            {'label': 'cumulative deaths', 'value': 'Cumulative_deaths'}]),
                                dcc.Graph(id="covid-map")]
                            ),
                    
                    html.Div(
                        id="network",
                        children=[
                            html.P("Global Trading Network",
                            id="chart-selector-2",),
                            dcc.RadioItems(id='import-or-export', options=[{'label':'Exporter view', 'value':True},
                                                                            {'label':'Importer view', 'value':False}], value=True, inline=True),
                            cyto.Cytoscape(id='network-graph',
                                elements=build_networkelements(True),
                                style={'width': '100%', 'height': '600px'},
                                layout={'name': 'cose','animate': 'end'},
                                stylesheet=network_stylesheet)
                                ]
                            )],
                        ),
                ],
            style={"display": "inline-block", "width": "50%", "vertical-align":"top"}
        ),

    # Right
        html.Div(
            id="graph-container",
            children=[html.Div(
                id="countrydashboard",
                children=[
                    dcc.Dropdown(
                        id='slt_country',
                        options=[{'label': name, 'value': code} \
                                    for name, _, code, _, _, _ in country_code.itertuples(index=False)],
                        value="JPN",
                        searchable=True,),
                    dcc.Graph(id="barplot"),
                    dcc.Graph(id="sankeyplot")]
                )],
                style={"display": "inline-block", "width": "40%", "vertical-align":"top"}
                ),
        
    # Bottom
        html.Div(
            id="graph-container-bottom",
            children=[html.Div(
                id="countrydashboard-bottom",
                children=[dcc.Graph(id="treeplot")], 
                style={"display": "inline-block", "width": "100%","vertical-align": "bottom"} 
            )]
        )]       
)


@app.callback(
    Output("covid-map", "figure"),
    [Input('time-slider', 'value'),
    Input("data-type-selected", "value"),
    ],
)

def update_world_map(time_selected, val_selected):
    '''
    Plot worldwide covid cases situation

    Inputs:
        val_selected: the data type selected by user

    Outputs:
        fig: the world map graph
    '''

    dff = prepare_covid_data(time_selected)
    dff['hover_text'] = dff['country_name'] + ": " + dff[val_selected].apply(str)

    fig = go.Figure(data = go.Choropleth(
                    locations = dff['Alpha-3code'],
                    z = np.log(dff[val_selected]), # need to fix log(0) here? maybe with list compre?
                    text = dff['hover_text'],
                    hoverinfo = 'text',
                    marker_line_color='black',
                    colorbar_title = 'Log Value',
                    autocolorscale = False,
                    reversescale = True,
                    colorscale = "RdBu", marker={'line': {'color': 'rgb(180,180,180)','width': 0.5}}))

    fig.update_layout(
    paper_bgcolor= "#252e3f",
    plot_bgcolor = "#252e3f",
    font_color= "#edeff7",
    height = 500,
    margin=dict(l=15, r=50, t=80, b=50)
    )

    return fig


@app.callback(
    Output(component_id="network-graph", component_property="elements"),
    [Input(component_id="import-or-export", component_property="value")]
)

def update_networkgraph(val_selected):
    '''
    Update the network graph

    Inputs:
        val_selected(boolean): True if exporter view and false if importer view. 

    Output:
        elements(list): A list of graph nodes and edges. 
    '''
    return build_networkelements(val_selected)


@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="treeplot", component_property="figure")],
    [Input(component_id="slt_country", component_property="value")]
)

def update_fromdropdown(val_selected):
    return draw_countrydashboard(val_selected)

@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="treeplot", component_property="figure")],
    [Input(component_id="network-graph", component_property="tapNodeData")]
)

def update_fromnode(node_clicked):
    if node_clicked:
        return draw_countrydashboard(node_clicked["id"])
    else:
        raise PreventUpdate

@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="treeplot", component_property="figure")],
    [Input(component_id="covid-map", component_property="clickData")]
)

def update_frommap(map_clicked):
    if map_clicked:
        return draw_countrydashboard(map_clicked["points"][0]["location"])
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True, port=3003)