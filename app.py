import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", index_col= "ReporterCode")
covid_data = pd.read_csv("WHO-COVID-19-global-data.csv")

# Clean the data (specifically for covid_data)
covid_data[['Year', 'Month', 'Day']] = covid_data['Date_reported'].\
                                    str.split("-", expand = True)
covid_data_2020 = covid_data[covid_data.Year == '2020'].groupby(\
                                'Country')['Cumulative_cases'].sum()
# also we may want to clean the country of covid_data and of product

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
            options=[{'label': c, 'value': c} \
                        for c in product["Reporter"].unique()],
            value="Japan",
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
    [Output(component_id="worldmap", component_property="figure"),
    Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="lineplot", component_property="figure")],
    [Input(component_id="slt_country", component_property="value")]
)

def update_output(val_selected):
    
    df = product[product["Reporter"]==val_selected]
    df_l = covid_data_2020[covid_data_2020['Country'] == val_selected]
    container = 'The dashboard is for the selected country: {}'.format(val_selected)

    # try with the tentative covid data and use plotly express
    worldmap = px.choropleth(
        data_frame=df_l,
        locations='Country',
        color='Cumulative_cases',
        hover_data=['Country', 'Cumulative_cases'],
        color_continuous_scale=px.colors.sequential.YlOrRd,
        template='plotly_dark'
    )

    bar_plt = px.bar(df[df["ProductCode"] == "TO"], x="Indicator", y="Value", 
                 color="Year", barmode="group")

    # Later change to sankey
    sankey_plt = px.bar(df, x="Year", y="Value", 
                 color="Indicator", barmode="group")

    # Later change to line chart
    line_plt = px.bar(df, x="Year", y="Value", 
                 color="Indicator", barmode="group")

    return (container, worldmap, bar_plt, sankey_plt, line_plt)

if __name__ == '__main__':
    app.run_server(debug=True)