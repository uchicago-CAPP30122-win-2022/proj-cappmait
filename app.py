import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)

# Load Data
product = pd.read_csv("rawdata/merchandise_values_annual_dataset.csv", index_col= "ReporterCode")
product = product[["Indicator", "ReporterISO3A", "Reporter", "ProductCode", "Product", "Year", "Value"]]
product.loc[product["Indicator"]=="Merchandise imports by product group - annual", "Indicator"] = "Import"
product.loc[product["Indicator"]=="Merchandise exports by product group - annual", "Indicator"] = "Export"
product["Year"] = product["Year"].astype('category')

# Define Layout
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

@app.callback(
    [Output(component_id="barplot", component_property="figure"),
    Output(component_id="sankeyplot", component_property="figure"),
    Output(component_id="lineplot", component_property="figure")],
    [Input(component_id="slt_country", component_property="value")]
)

def update_output(val_selected):
    
    df = product[product["Reporter"]==val_selected]

    
    bar_plt = px.bar(df[df["ProductCode"] == "TO"], x="Indicator", y="Value", 
                 color="Year", barmode="group")

    # Later change to sankey
    sankey_plt = px.bar(df, x="Year", y="Value", 
                 color="Indicator", barmode="group")

    # Later change to line chart
    line_plt = px.bar(df, x="Year", y="Value", 
                 color="Indicator", barmode="group")

    return (bar_plt, sankey_plt, line_plt)

if __name__ == '__main__':
    app.run_server(debug=True)