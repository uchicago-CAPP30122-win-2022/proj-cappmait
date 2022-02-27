import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import data_analysis as da

app = Dash(__name__)

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})
country_code = pd.read_csv("rawdata/countries_codes_and_coordinates_new.csv") # Later delete? 
# covid_data = pd.read_csv("WHO-COVID-19-global-data.csv")

# # Clean the data (specifically for covid_data)
# covid_data[['Year', 'Month', 'Day']] = covid_data['Date_reported'].\
#                                     str.split("-", expand = True)
# covid_data_2020 = covid_data[covid_data.Year == '2020'].groupby(\
#                                 'Country')['Cumulative_cases'].sum()

# Define Layout (dash components should be inside app layout)
app.layout = html.Div([

    # Title
    html.H1("Dashboard of Covid Trade Impact",
            style={'textAlign': 'center'}),

    # Left Top
    html.Div([
        dcc.Graph(id="worldmap")], 
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

        dcc.Graph(id="sankeyplot"),

        dcc.Graph(id="lineplot")],
        style={"display": "inline-block", "width": "40%"}
    )

])

# callback is supposed to connect graphs with dash components
# added worldmap as an output, added component to be shown on the dashboard
@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="lineplot", component_property="figure")],
    [Input(component_id="slt_country", component_property="value")]
)

# @app.callback(
#     [Output(component_id="worldmap", component_property="figure"),
#     Output(component_id="barplot", component_property="figure"),
#     Output(component_id="sankeyplot", component_property="figure"),
#     Output(component_id="lineplot", component_property="figure")],
#     [Input(component_id="slt_country", component_property="value")]
# )

def update_output(val_selected):
    '''
    Update graphs given the user selected country

    Inputs:
        val_selected(str) : The user selected country
    
    Outputs:
        (A tuple of graph objects
    '''
    df = product[product["ReporterISO3A"] == val_selected] 

    # df_l = covid_data_2020[covid_data_2020['Country'] == val_selected]
    # container = 'The dashboard is for the selected country: {}'.format(val_selected)

    # try with the tentative covid data and use plotly express
    # worldmap = px.choropleth(
    #     data_frame=df_l,
    #     locations='Country',
    #     color='Cumulative_cases',
    #     hover_data=['Country', 'Cumulative_cases'],
    #     color_continuous_scale=px.colors.sequential.YlOrRd,
    #     template='plotly_dark'
    # )

    bar_plt = px.bar(df[df["ProductCode"] == "TO"], x="Indicator", y="Value", 
                 color="Year", barmode="group")

    node_df, link_df = da.structure_node_link(partners, val_selected)
    sankey_plt = plot_sankey(node_df, link_df)

    print(node_df)
    line_plt = px.line(da.find_top3_products(df), x="Year", y="Value", color="Product")

    return (bar_plt, sankey_plt, line_plt)

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
        width=500,
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

if __name__ == '__main__':
    app.run_server(debug=True)