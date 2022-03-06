import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import data_analysis as da

app = Dash(__name__)

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
country_code = pd.read_csv("rawdata/countries_codes_and_coordinates_new.csv")


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
    dff = extracted_df[extracted_df.Date_reported == '2020/12/31']

    return dff


# Define Layout (dash components inside)
app.layout = html.Div([

    # Title
    html.H1("Dashboard of Covid Impact and World Trading",
            style={'textAlign': 'center'}),

    # Left Top
    html.Div([
        dcc.Dropdown(id='data-type-selected', value='Cumulative_deaths',
                    options = [{'label': 'Cumulative_cases', 'value': 'Cumulative_cases'},
                                {'label': 'Cumulative_deaths', 'value': 'Cumulative_deaths'}]),
        dcc.Graph(id="Covid World Map")], 
        style={"display": "inline-block", "width": "60%","vertical-align": "top"} 
    ),

    # Right
    html.Div([
        dcc.Dropdown(
            id='slt_country',
            options=[{'label': name, 'value': code} \
                        for name, _, code, _, _, _ in country_code.itertuples(index=False)],
            value="JPN",
            searchable=True,),
        dcc.Graph(id="barplot"),
        dcc.Graph(id="sankeyplot")],
    style={"display": "inline-block", "width": "40%"}
    ),
    
    # Bottom
    html.Div([
        dcc.Graph(id="treeplot")], 
    style={"display": "inline-block", "width": "100%","vertical-align": "bottom"} 
    )

])


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
        (A tuple of graph objects
    '''

    df = product[product["ReporterISO3A"] == val_selected] 

    bar_plt = px.bar(df[df["ProductCode"] == "TO"], x="Indicator", y="Value", 
                 color="Year", barmode="group")

    node_df, link_df = da.structure_node_link(partners, val_selected)
    sankey_plt = plot_sankey(node_df, link_df)

    tree_plt = px.treemap(df[df["ProductCode"] != "TO"], path=[px.Constant("Total"), "Indicator", "Year", "Product"], values="Value")

    return (bar_plt, sankey_plt, tree_plt)


def plot_sankey(node_df, link_df):
    '''
    Create a sankey graph object

    Inputs:
        node_df(Pandas Dataframe): a data of nodes
        links_df(Pandas Dataframe): a data of links

    Outputs:
        fig(a graph object)
    '''
    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 15,
        thickness = 5,
        line = dict(color = "black", width = 0.5),
        label = node_df,
        color = "gray"
        ),
        link = dict(
        source = link_df['Source'].to_list(), 
        target = link_df['Target'].to_list(),
        value =  link_df['Value'].to_list(),
        color = link_df['LinkColor'].to_list()
    ))])

    fig.update_layout(title_text="", font_size=10)
    fig.add_annotation(text="2019",
                    xref="paper", yref="paper",
                    x=0.3, y=1.00, showarrow=False), 
    fig.add_annotation(text="2020",
                    xref="paper", yref="paper",
                    x=0.75, y=1.00, showarrow=False)

    fig.update_layout(
        autosize=False,
        width=550,
        height=700,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        )
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

    fig = px.choropleth(dff, locations = 'Alpha-3code',
                    z = np.log(dff[selected]),
                    text = dff['hover_text'],
                    hoverinfo = 'text',
                    marker_line_color='white',
                    autocolorscale = False,
                    reversescale = True,
                    colorscale = "RdBu", marker={'line': {'color': 'rgb(180,180,180)','width': 0.5}})

    fig.update_layout(annotations = [dict(
        x = 0.52,
        y = 0.05,
        text = 'Source : WHO Coronavirus (COVID-19) Dashboard'
    )])

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)