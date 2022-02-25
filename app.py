import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", dtype={"Value":"int", "Year":"category"})
partners = pd.read_excel("rawdata/Direction_of_Trade_Statistics_Japan_test.xlsx")
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
    
    df = product[product["Reporter"]==val_selected]
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

    sankey_plt = px.bar(df[df["ProductCode"] == "TO"], x="Indicator", y="Value", 
                 color="Year", barmode="group")

    line_plt = plot_line(df)
    # line_plt.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
    #                 margin=dict(l=60, r=60, t=50, b=50))

    return (bar_plt, sankey_plt, line_plt)

def plot_line(df):
    '''
    Create a slopgraph given the product details df and selected country.

    Inputs:
        df(Pandas Dataframe) : Product details in the selected country.

    Outputs:
        line_plt(graph object)
    '''

    grouped_product = df[df["ProductCode"] != "TO"].groupby(["Product","Year"]).sum().sort_values(by="Value", ascending=False).reset_index()
    selected_products = grouped_product[grouped_product["Year"]=="2019"].nlargest(3, "Value")["Product"]

    line_plt = px.line(grouped_product[grouped_product["Product"].isin(selected_products)], x="Year", y="Value", color="Product")

    return line_plt

if __name__ == '__main__':
    app.run_server(debug=True)