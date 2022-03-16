'''
Module for interactive dashboard.
'''
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, MultiplexerTransform, Input, Output
import dash_cytoscape as cyto
from proj_cappmait.helper import network_analysis as net

app = DashProxy(transforms=[MultiplexerTransform()],
                prevent_initial_callbacks=True)

# Load Data
product = pd.read_csv(
    "proj_cappmait/data/merchandise_values_annual_dataset.csv",
     dtype={"Value":"int", "Year":"category"})
country_code = pd.read_csv(
    "proj_cappmait/data/countries_codes_and_coordinates_cleaned.csv")
covid_data = pd.read_csv('proj_cappmait/data/owid_covid_data_cleaned.csv')

# Functions for drawing graphs
def plot_world_map(time_selected, val_selected):
    '''
    Plot worldwide covid cases situation
    Inputs:
        time_selected(str): the quarter selected by user
        val_selected(str): the data type selected by user
    Outputs:
        fig: the world map graph
    '''
    dic = {1:'2020Q1', 2:'2020Q2', 3:'2020Q3', 4:'2020Q4'}
    dff = covid_data[covid_data.period == dic.get(time_selected)]
    dff['hover_text'] = dff['Country_name'] + ": " + \
                        dff[val_selected].apply(str)

    np.seterr(divide = 'ignore') 
    fig = go.Figure(data = go.Choropleth(
                    locations = dff['iso_code'],
                    z = np.log(dff[val_selected]),
                    text = dff['hover_text'],
                    hoverinfo = 'text',
                    marker_line_color='black',
                    colorbar_title = 'Log Value',
                    autocolorscale = False,
                    reversescale = True,
                    colorscale = "RdBu", 
                    marker={'line': {'color': 'rgb(180,180,180)','width': 0.5}}))

    fig.update_layout(
    paper_bgcolor= "rgba(0,0,0,0)",
    plot_bgcolor = "rgba(0,0,0,0)",
    font_color= "#edeff7",
    height = 500,
    geo_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=25, r=50, t=80, b=50)
    )

    return fig


def build_networkelements(is_exporter):
    '''
    Build a network elements. Node is each country. Source of edge 
    is country node, and target is the best trading partner. In the exporter 
    view, the country serve as an exporter and export the most to the best 
    trading partner. In the importer view, the country serve as an importer and
    import the most from the best trading partner. 
    Input:
        is_exporter(boolean): True if the country node is exporter, and False 
            otherwise. 
    Output:
        elements(list): A list of graph nodes and edges. 
    '''
    graph = net.construct_networkgraph()
    nodes, edges = graph.find_best_partners(1, is_exporter)

    graph_nodes = [
        {'data': {'id': node.country_code, 
                  'label': node.label, 
                  'pagerank': node.pagerank}} for node in nodes.values()
    ]

    graph_edges = [
        {'data': {'source': source, 
                  'target': target, 
                  'weight': weight}} for source, target, weight in edges
    ]

    return graph_nodes + graph_edges


def network_legend():
    '''
    Draw a network map legend since legend is not
    automatically created by cytoscape. 
    Input: 
        None
    Output: 
        fig(a graph legend object)
    '''
    fig = go.Figure()
    fig.add_shape(type="circle",
                line_color="grey", 
                fillcolor="grey",
                x0=1, y0=0, x1=1.03, y1=2
    )

    fig.add_trace(go.Scatter(
                x=[1.14, 1.41, 1.70],
                y=[1, 1, 1],
                text=[": PageRank(=centrality) size", 
                      ": Trade Increased(2019\u21922020)", 
                      ": Trade Decreased(2019\u21922020)"],
                mode="text",
                textfont=dict(
                    color="#edeff7",
                    size=12,
                    )
    ))

    fig.add_shape(type="line",
                x0=1.26, y0=1, x1=1.29, y1=1,
                line=dict(
                    color="blue",
                    width=2,
                    )
    )

    fig.add_shape(type="line",
                x0=1.55, y0=1, x1=1.58, y1=1,
                line=dict(
                    color="red",
                    width=2,
                )
    )

    fig.add_shape(type="line",
                x0=1.77, y0=1, x1=1.84, y1=1,
                line=dict(
                    color="rgba(0,0,0,0)",
                    width=2,
                )
    )

    fig.update_xaxes(
                showticklabels=False,
                    showgrid=False,
                    zeroline=False,
    )

    fig.update_yaxes(
                showticklabels=False,
                showgrid=False,
                zeroline=False,
    )

    fig.update_layout(
                paper_bgcolor= "rgba(0,0,0,0)",
                plot_bgcolor = "rgba(0,0,0,0)",
                font_color= "#edeff7",
                height = 100,
                width = 750,
                geo_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=0, l=50)
    )

    return fig


def plot_bar(df, country_name):
    '''
    Create a bar graph object, which represents 
    trade volume of export/import in 2019/2020. 
    Inputs:
        df (Pandas Dataframe): product data for the country
        country_name(str): the country name
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
                title=f'{country_name}\'s Total Trade Volume before/after Covid',
                xaxis=dict(
                    title= '',
                    titlefont_size=14,
                    tickfont_size=14,
                    title_standoff=50
                ),
                yaxis=dict(
                    title= 'Trade Volume',
                    titlefont_size=14,
                    tickfont_size=14,
                ),
                autosize=False,
                width=600,
                height=400,
                margin=dict(
                    l=100,
                    r=0,
                    b=100,
                    t=100,
                    pad=4
                ),
                paper_bgcolor= 'rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                bargap=0.15,
                bargroupgap=0.1
    )

    return fig


def plot_sankey(val_selected, country_name):
    '''
    Create a sankey graph object, which represents 
    top10 trade flows of each export/import in 2019/2020. 
    Inputs:
        val_selected(str): the country code
        country_name(str): the country name
    Outputs:
        fig(a sankey graph object)
    '''
    graph = net.construct_networkgraph()
    nodes, edges = graph.draw_sankey(val_selected)

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
                x=0.2, y=1.00, showarrow=False)
    fig.add_annotation(text="2020",
                xref="paper", yref="paper",
                x=0.75, y=1.00, showarrow=False)

    fig.update_layout(
                title = f'{country_name}\'s Trade Partners before/after Covid',
                font_color="#e7ecf5",
                autosize=False,
                width=600,
                height=700,
                margin=dict(
                    l=50,
                    r=20,
                    b=50,
                    t=30,
                    pad=4
                ),
                paper_bgcolor= 'rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def plot_dot(df, country_name):
    '''
    Create a dot graph object, which represents 
    total trade (import+export) in top5 product categories. 
    Inputs:
        df (Pandas Dataframe): product data for the country
        country_name(str): the country name
    Outputs:
        fig(a tree graph object)
    '''
    df_new = df[df["ProductCode"]!="TO"].pivot(
        index=["ReporterISO3A", "Reporter", "ProductCode", "Product"], 
        values="Value", columns=["Indicator", "Year"]).reset_index()

    if len(df_new) > 0:
        df_new.columns = df_new.columns.map(' '.join).str.strip()
        df_new["Total 2020"] = (df_new["Import 2020"] + 
            df_new["Export 2020"])
        df_new["Total 2019"] = (df_new["Import 2019"] + 
            df_new["Export 2019"])
        df_new = df_new.sort_values("Total 2019").tail(5)
        df_new["Product"] = df_new["Product"].str.replace("equipment", "")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
                    x=df_new["Total 2019"],
                    y=df_new["Product"],
                    opacity=0.7,
                    marker=dict(color='#36559c', 
                        size=12, line=dict(color="#aab0bf",width=1)
                    ),
                    mode="markers",
                    name="2019",
                    customdata = df_new[["Import 2019", "Export 2019"]],
                    hovertemplate=
                        "<b>%{y}</b><br><br>" +
                        "Import: %{customdata[0]}<br>" +
                        "Export: %{customdata[1]}<br>" +
                        "<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
                    x=df_new["Total 2020"],
                    y=df_new["Product"],
                    opacity=0.7,
                    marker=dict(color='#b5442d', 
                        size=12, 
                        line=dict(color="#aab0bf",width=1)
                    ),
                    mode="markers",
                    name="2020",
                    customdata = df_new[["Import 2020", "Export 2020"]],
                    hovertemplate=
                        "<b>%{y}</b><br><br>" +
                        "Import: %{customdata[0]}<br>" +
                        "Export: %{customdata[1]}<br>" +
                        "<extra></extra>",
        ))

        fig.update_layout(
                    xaxis = dict(showgrid=False, showline=True),
                    xaxis_title="Total volume of import and export",
                    legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=0.98,
                            xanchor="right",
                            x=1
        ))

    # If data is missing, show a message
    else:
        fig = go.Figure()
        fig.update_layout(
                    xaxis = {"visible": False},
                    yaxis = {"visible": False},
                    annotations = [{
                            "text": "Missing Data",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {"size": 20}}]            
        )

    fig.update_layout(
                title = f'{country_name}\'s Product Category before/after Covid',
                font_color="#e7ecf5",
                autosize=False,
                width=600,
                height=314,
                margin=dict(
                    l=50,
                    r=20,
                    b=0,
                    t=50,
                    pad=4
                ),
                paper_bgcolor= 'rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


def update_countrydashboard(val_selected):
    '''
    Update country dashboard(RHS) given the user selected country. 
    Inputs:
        val_selected(str) : The user selected country code
    Outputs:
        A tuple of graph objects
    '''
    df = product[product["ReporterISO3A"] == val_selected] 
    country_name = (country_code.loc[country_code["Alpha-3code"] == 
        val_selected, "Country"].item())

    bar_plt = plot_bar(df, country_name)

    sankey_plt = plot_sankey(val_selected, country_name)

    dot_plt = plot_dot(df, country_name)

    return (bar_plt, sankey_plt, dot_plt)

# Style for network graph
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
                    children='''Left-hand-side of the dashboard presents 
                    worldwide situation of covid and trade network, 
                    while right-hand-side dive into specific countries'  
                    trading volumes, partners and categories from 2019 to 2020.
                    Users can interact with the dashboard through clicking into 
                    covid & network map; or select / input in dropdown box.''',
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
                    id = 'covidmap-container',
                    children = [
                        html.P(id = 'up-left-header',
                                children = 'Clickable Board - Click Country of Interest',
                        ),
                        html.P(id="covidmap-title",
                                children = "Covid World Map",
                        ),
                        dcc.RadioItems(id='data-type-selected', 
                                value='total_cases_per_million',
                                options = [
                                    {'label': 'Total cases per million', 
                                        'value': 'total_cases_per_million'
                                    },
                                    {'label': 'Total deaths per million', 
                                        'value': 'total_deaths_per_million'
                                    }]
                        ),
                        dcc.Graph(id="covid-map", 
                                figure=plot_world_map(1, 
                                    'total_cases_per_million'
                                ) 
                        )
                    ]),
                    html.Div(
                    id = 'slider-container',
                    children = [
                        html.P(id='slider-text',
                                children='Drag the slider to choose timespan: ',
                        ),
                        dcc.Slider(id = 'time-slider',
                                step=None,
                                marks = {
                                    1: '2020Q1',
                                    2: '2020Q2',
                                    3: '2020Q3',
                                    4: '2020Q4',
                                },
                                value = 1
                            ),
                    ]),
                    
                    html.Div(
                        id="network",
                        children=[
                            html.P(id = "bottom-left-header",
                                    children = "Clickable Board - Click Country of Interest",
                            ),
                            html.P(id="chart-selector-2",
                                    children = "Global Trading Network",
                            ),
                            dcc.RadioItems(id='import-or-export', 
                                    options=[
                                            {'label':'Exporter view', 'value':True},
                                            {'label':'Importer view', 'value':False}
                                        ], 
                                        value=True, 
                                        inline=True
                            ),
                            cyto.Cytoscape(id='network-graph',
                                    elements=build_networkelements(True),
                                    style={'width': '100%', 'height': '600px'},
                                    layout={'name': 'cose','animate': 'end'},
                                    stylesheet=network_stylesheet,
                                    autoungrabify=True,
                                    minZoom=0.4,
                                    maxZoom=1
                            ),
                            dcc.Graph(id="network-legend", 
                                    figure=network_legend()
                            ),
                        ]
                    )]
                )],
            style={
                "display": "inline-block", 
                "width": "50%", 
                "vertical-align":"top"
            }
        ),

    # Right
        html.Div(
            id="graph-container",
            children=[
                html.Div(
                id="countrydashboard",
                children=[
                    html.P(id = 'up-right-header', 
                            children = 'Country Deep-Dive'
                    ),
                    html.P(id = 'dropdown-text',
                            children = 'Select country:'
                    ),
                    dcc.Dropdown(id='slt_country',
                        options=[
                            {'label': name, 
                             'value': code
                            } for name, _, code, _, _, _ in \
                                country_code.itertuples(index=False)
                        ],
                        searchable=True,
                        value="USA"
                    ),
                    dcc.Graph(id="barplot", 
                        figure=plot_bar(
                            product[product["ReporterISO3A"] == "USA"], 
                            "United States"
                        )
                    ),
                    dcc.Graph(id="sankeyplot", 
                        figure=plot_sankey("USA", "United States")
                    ),
                    dcc.Graph(id="dotplot", 
                        figure=plot_dot(
                            product[product["ReporterISO3A"] == "USA"], 
                            "United States"
                        )
                    )]
                )],
            style={
                "display": "inline-block", 
                "width": "40%", 
                "vertical-align":"top"
            }
        )
    ]
)

# Define user inputs and callbacks
@app.callback(
    Output("covid-map", "figure"),
    [Input('time-slider', 'value'),
    Input("data-type-selected", "value")],
)

def update_world_map(time_selected, val_selected):
    '''
    Update world map given user selected time and data.
    Inputs:
        time_selected(int): the quarter selected by user
        val_selected(str): the data type selected by user
    Output:
        fig: updated world map graph
    '''
    return plot_world_map(time_selected, val_selected)


@app.callback(
    Output(component_id="network-graph", component_property="elements"),
    [Input(component_id="import-or-export", component_property="value")]
)

def update_networkgraph(val_selected):
    '''
    Update network graph given user selected data. 
    Inputs:
        val_selected(boolean): True if exporter view and false if importer view. 
    Output:
        fig: updated network graph
    '''
    return build_networkelements(val_selected)

@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="dotplot", component_property="figure")],
    [Input(component_id="slt_country", component_property="value")]
)

def update_fromdropdown(val_selected):
    '''
    Update country dashboard give user selected country
    from dropdown list
    Input:
        val_selected(str): The user selected country code
    Output:
        figs: updated country dashboard
    '''
    return update_countrydashboard(val_selected)

@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="dotplot", component_property="figure"),
    Output(component_id="slt_country", component_property="value")],
    [Input(component_id="covid-map", component_property="clickData")]
)

def update_frommap(map_clicked):
    '''
    Update country dashboard and dropdown list selection
    given user selected country from world map
    Input:
        map_clicked(dict): The mouse clicked data
    Output:
        A tuple of updated country dashboard figs and a dropdown list value
    '''
    if map_clicked:
        val_selected = map_clicked["points"][0]["location"]
        return update_countrydashboard(val_selected) + (val_selected,)
    raise PreventUpdate

@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="dotplot", component_property="figure"),
    Output(component_id="slt_country", component_property="value")],
    [Input(component_id="network-graph", component_property="tapNodeData")]
)

def update_fromnode(node_clicked):
    '''
    Update country dashboard and dropdown list selection
    given user selected country from network map
    Input:
        node_clicked(dict): The mouse clicked data
    Output:
        A tuple of updated country dashboard figs and a dropdown list value
    '''
    if node_clicked:
        val_selected = node_clicked["id"]
        return update_countrydashboard(val_selected) + (val_selected,)
    raise PreventUpdate

