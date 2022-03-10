import dash
import dash_cytoscape as cyto
import dash_html_components as html
import pandas as pd

app = dash.Dash(__name__)

partners = pd.read_csv("rawdata/imf_import_export_cleaned.csv", dtype={"2019":"float", "2020":"float"})

partners = partners[partners["to_name"]=="Japan"]

nodes = [
    {
        'data': {'id': iso, 'label': country}
    }
    for iso, country in zip(partners.from_code.unique(),partners.from_name.unique())
]

nodes.append({
        'data': {'id': "JPN", 'label': "Japan"}
    })

edges = [
    {'data': {'source': source, 'target': target}}
    for source, target in zip(partners.from_code ,partners.to_code)
]

elements = nodes + edges

app.layout = html.Div([
    cyto.Cytoscape(
        id='network',
        elements=elements,
        style={'width': '100%', 'height': '500px'},
        layout={
            'name': 'random'
        }
    )
])


if __name__ == '__main__':
    app.run_server(debug=True)