import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output  # pip install dash (version 2.0.0 or higher)

app = Dash(__name__)

# import and clean the data
df = pd.read_csv("owid_covid_data.csv")