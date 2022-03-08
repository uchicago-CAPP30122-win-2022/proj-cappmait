import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import data_analysis as da
import network_analysis as net

app = Dash(__name__)

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
country_code = pd.read_csv("rawdata/countries_codes_and_coordinates_new.csv")

# go to another file? 
def prepare_covid_data():
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

    df = covid_data.join(country_code.set_index('Alpha-2code'), on = 'Country_code')
    dff = df[["country_name", "Date_reported", "Cumulative_cases", "Cumulative_deaths", "Alpha-3code"]]
    dff = dff[dff.Date_reported == '2020/12/31']

    return dff


# Define Layout (dash components inside)
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
        children=[
            html.H1("Dashboard of Covid Impact and World Trading"),
            html.P(id="description",
                    children="† Description here",
                )]
        ),

    # Left Top
        html.Div(
            id="app-container",
            children=[html.Div(
                id="world-map",
                children=[
                    html.P(id="chart-selector", children="Select chart:"),
                    dcc.Dropdown(id='data-type-selected', value='Cumulative_deaths',
                                options = [{'label': 'Cumulative_cases', 'value': 'Cumulative_cases'},
                                            {'label': 'Cumulative_deaths', 'value': 'Cumulative_deaths'}]),
                    dcc.Graph(id="covid-graph"),
                        ]
                    )],
                style={"display": "inline-block", "width": "60%", "vertical-align":"top", "backgroundColor":"#252e3f"}
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
                style={"display": "inline-block", "width": "30%"}
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


# Use callback to connect graphs with dash components
@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="treeplot", component_property="figure")],
    [Input(component_id="slt_country", component_property="value")]
)


def update_output(val_selected):
    '''
    Update graphs given the user selected country

    Inputs:
        val_selected(str) : The user selected country
    
    Outputs:
        A tuple of graph objects
    '''
    df = product[product["ReporterISO3A"] == val_selected] 
    country_name = country_code.loc[country_code["Alpha-3code"] ==val_selected, "Country"].item()

    bar_plt = plot_bar(df, country_name)

    graph = net.draw_networkgraph()
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
                 color="Year", barmode="group")

    fig.update_layout(
        font_color="#7fafdf",
        title=f'{country_name}\'s Total Trade Volume in before/after Covid',
        xaxis=dict(
            title= '',
            titlefont_size=16,
            tickfont_size=14,
            title_standoff=50
        ),
        yaxis=dict(
            title= 'Trade Volume',
            titlefont_size=16,
            tickfont_size=14,
        ),
        autosize=False,
        width=550,
        height=450,
        margin=dict(
            l=150,
            r=0,
            b=50,
            t=100,
            pad=4
        ),
        paper_bgcolor= '#1f2630',
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
        line = dict(color = "black", width = 0.5),
        label = nodes,
        color = "gray"
        ),
        link = dict(
        source = [source for source, _, _, _ in edges], 
        target = [target for _, target, _, _ in edges],
        value =  [value for _, _, value, _ in edges],
        color = [color for _, _, _, color in edges]
    ))])

    fig.add_annotation(text="2019",
                    xref="paper", yref="paper",
                    x=0.3, y=1.00, showarrow=False), 
    fig.add_annotation(text="2020",
                    xref="paper", yref="paper",
                    x=0.75, y=1.00, showarrow=False)

    fig.update_layout(
        title = f'{country_name}\'s Trade flows in before/after Covid',
        font_color="#7fafdf",
        autosize=False,
        width=550,
        height=700,
        margin=dict(
            l=50,
            r=20,
            b=50,
            t=50,
            pad=4
        ),
        paper_bgcolor="#1f2630",
        plot_bgcolor="#1f2630"
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
        path=[px.Constant("Total"), "Indicator", "Year", "Product"], values="Value")
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(
        title=dict(
            text=f'{country_name}\'s Tree map in before/after Covid',
            font_color="#7fafdf"
        ),
        autosize=False,
        paper_bgcolor= '#1f2630'
    )

    return fig


@app.callback(
    Output("covid-graph", "figure"),
    [Input("data-type-selected", "value")]
)


def update_world_map(selected):
    '''
    Plot worldwide covid cases situation

    Inputs:
        selected: the data type selected by user

    Outputs:
        fig: the world map graph
    '''

    dff = prepare_covid_data()
    dff['hover_text'] = dff['country_name'] + ": " + dff[selected].apply(str)

    fig = go.Figure(data = go.Choropleth(
                    locations = dff['Alpha-3code'],
                    z = np.log(dff[selected]),
                    text = dff['hover_text'],
                    hoverinfo = 'text',
                    marker_line_color='white',
                    autocolorscale = False,
                    reversescale = True,
                    colorscale = "RdBu", marker={'line': {'color': 'rgb(180,180,180)','width': 0.5}}))

    fig.update_layout(annotations = [dict(
        x = 0.52,
        y = 0.05,
        text = 'Source : WHO Coronavirus (COVID-19) Dashboard'
    )],
    paper_bgcolor= "#252e3f",
    font_color="#7fafdf"
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)