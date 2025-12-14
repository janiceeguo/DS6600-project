import numpy as np
import pandas as pd
import os
import dotenv
import psycopg
from sqlalchemy import create_engine

import dash
from dash import Dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

dotenv.load_dotenv()
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

dbms = 'postgresql'
package = 'psycopg'
user = 'postgres'
password = POSTGRES_PASSWORD
host = 'postgres'
port = '5432'
db = 'housing'

engine = create_engine(f'{dbms}+{package}://{user}:{password}@{host}:{port}/{db}')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

myquery = '''
SELECT *
FROM acs_zillow_fred_long
'''
acs_annual = pd.read_sql_query(myquery, con=engine)

myquery = '''
SELECT *
FROM zillow_fred_long
'''
zillow_monthly = pd.read_sql_query(myquery, con=engine)

msa_list = acs_annual["msa"].sort_values().unique()

app = Dash(__name__)
app.title = "Housing Affordability Dashboard"

app.layout = html.Div([
    html.H1("US Housing Affordability Dashboard", style={"textAlign": "center"}),

    html.Label("Select Metropolitan Area:"),
    dcc.Dropdown(
        id="msa_dropdown",
        options=[{"label": m, "value": m} for m in msa_list],
        value="Charlottesville, VA"
    ),
    dcc.Tabs([
        dcc.Tab(label="Annual Trends", children=[
            dcc.Graph(id="income_plot"),
            dcc.Graph(id="hvi_plot"),
            dcc.Graph(id="mortgage_plot"),
            dcc.Graph(id="affordability_plot"),
            dcc.Graph(id="scatter_plot"),
        ]),
        dcc.Tab(label="Monthly Trends", children=[
            dcc.Graph(id="monthly_hvi_plot"),
            dcc.Graph(id="monthly_mortgage_plot"),
            dcc.Graph(id="dual_plot"),

        ]),
        dcc.Tab(label="ML Insights", children=[
            dcc.Graph(id="regression_plot"),
            dcc.Graph(id="cluster_plot")
        ])
    ])
])

@app.callback(
    Output("income_plot", "figure"),
    Input("msa_dropdown", "value")
)

def income_plot(msa):
    df_a = acs_annual[acs_annual["msa"] == msa]
    fig_income = px.line(df_a, x="year", y="income", title=f"Income Over Time — {msa}")

    return fig_income

@app.callback(
    Output("hvi_plot", "figure"),
    Input("msa_dropdown", "value")
)

def hvi_plot(msa):
    df_a = acs_annual[acs_annual["msa"] == msa]
    fig_hvi = px.line(df_a, x="year", y="hvi", title=f"Housing Value Over Time — {msa}")

    return fig_hvi

@app.callback(
    Output("mortgage_plot", "figure"),
    Input("msa_dropdown", "value")
)

def mortgage_plot(msa):
    df_a = acs_annual[acs_annual["msa"] == msa]
    fig_mort = px.line(df_a, x="year", y="mortgage_rate", title=f"Mortgage Rate Over Time — {msa}")

    return fig_mort

@app.callback(
    Output("affordability_plot", "figure"),
    Input("msa_dropdown", "value")
)

def affordability_plot(msa):
    df_a = acs_annual[acs_annual["msa"] == msa]
    fig_aff = px.line(df_a, x="year", y="affordability", title=f"Affordability Index — {msa}")

    return fig_aff

@app.callback(
    Output("scatter_plot", "figure"),
    Input("msa_dropdown", "value")
)

def scatter_plot(msa):
    df_a = acs_annual[acs_annual["msa"] == msa]
    fig_scatter = px.scatter(
        df_a, x="income", y="hvi", color="year",
        title="Income vs Home Value",
        #trendline="ols"
    )
    
    return fig_scatter

@app.callback(
    Output("monthly_hvi_plot", "figure"),
    Input("msa_dropdown", "value")
)

def monthly_hvi_plot(msa):
    df_m = zillow_monthly[zillow_monthly["msa"] == msa]

    fig_hvi_m = px.line(df_m, x="month_year", y="hvi",
                        title=f"Monthly Housing Value — {msa}")

    return fig_hvi_m

@app.callback(
    Output("monthly_mortgage_plot", "figure"),
    Input("msa_dropdown", "value")
)

def monthly_mortgage_plot(msa):
    df_m = zillow_monthly[zillow_monthly["msa"] == msa]

    fig_mort_m = px.line(df_m, x="month_year", y="mortgage_rate",
                         title=f"Monthly Mortgage Rate — {msa}")

    return fig_mort_m

@app.callback(
    Output("dual_plot", "figure"),
    Input("msa_dropdown", "value")
)

def dual_plot(msa):
    df_m = zillow_monthly[zillow_monthly["msa"] == msa]

    fig_dual = go.Figure()
    fig_dual.add_trace(go.Scatter(
        x=df_m["month_year"], y=df_m["hvi"], name="HVI"
    ))
    fig_dual.add_trace(go.Scatter(
        x=df_m["month_year"], y=df_m["mortgage_rate"], name="Mortgage Rate", yaxis="y2"
    ))
    fig_dual.update_layout(
        title="Monthly HVI vs Mortgage Rate",
        yaxis=dict(title="HVI"),
        yaxis2=dict(title="Mortgage Rate", overlaying="y", side="right")
    )

    return fig_dual

@app.callback(
    Output("regression_plot", "figure"),
    Input("msa_dropdown", "value")  # dummy trigger
)
def update_regression(_):

    fig = px.scatter(
        acs_annual,
        x="affordability",
        y="predicted_affordability",
        title="Actual vs Predicted Housing Affordability",
        labels={
            "affordability": "Actual Affordability (HVI / Income)",
            "predicted_affordability": "Predicted Affordability"
        }
    )

    fig.add_shape(
        type="line",
        x0=acs_annual["affordability"].min(),
        y0=acs_annual["affordability"].min(),
        x1=acs_annual["affordability"].max(),
        y1=acs_annual["affordability"].max(),
        line=dict(dash="dash")
    )

    return fig

@app.callback(
    Output("cluster_plot", "figure"),
    Input("msa_dropdown", "value")  # dummy trigger
)
def update_cluster(_):

    fig = px.scatter(
        acs_annual,
        x="income",
        y="hvi",
        color="cluster",
        hover_name="msa",
        title="Metro Area Clusters Based on Housing Market Characteristics",
        labels={
            "income": "Median Income",
            "hvi": "Home Value Index"
        }
    )

    return fig

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)