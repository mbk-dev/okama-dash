import warnings
from functools import lru_cache

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import dash_bootstrap_components as dbc

import okama as ok

warnings.simplefilter(action='ignore', category=FutureWarning)

inflation_list = ok.symbols_in_namespace('INFL').symbol.tolist()
ccy_list = [x.split(".", 1)[0] for x in inflation_list]

today_str = pd.Timestamp.today().strftime('%Y-%m')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


@lru_cache()
def get_symbols() -> list:
    """
    Get all available symbols (tickers) from assets namespaces.
    """
    namespaces = ['US', 'LSE', 'MOEX', 'INDX', 'COMM', 'FX', 'CC']
    list_of_symbols = [ok.symbols_in_namespace(ns) for ns in namespaces]
    classifier_df = pd.concat(list_of_symbols,
                          axis=0,
                          join="outer",
                          copy="false",
                          ignore_index=True)
    return classifier_df.symbol.to_list()


app.layout = dbc.Container([
    html.H1(
        children='Assets Wealth Indexes',
        style={
            'textAlign': 'center',
            # 'color': colors['text']
        }
    ),

    html.Div([
        html.Div([
            html.Label("Tickers to compare"),
            dcc.Dropdown(
                options=get_symbols(),
                value=['SPY.US', 'BND.US'],
                multi=True,
                placeholder="Select assets",
                id='symbols-list'
            )], style={'width': '48%', 'display': 'inline-block'}),
        # html.Br(),
        html.Div([
            html.Label("Base currency"),
            dcc.Dropdown(
                options=ccy_list,
                value='USD',
                multi=False,
                placeholder="Select a base currency",
                id='base-currency'
            )], style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
        html.Div([
            "First Date: ",
            dcc.Input(id='first-date', value='2000-01', type='text'),
            "Last Date: ",
            dcc.Input(id='last-date', value=today_str, type='text'),
            html.P(
                html.Button(id='submit-button-state', n_clicks=0, children='Submit')
            ),
        ], style={'width': '98%', 'display': 'inline-block'})
    ]),

    dcc.Loading(
        id="loading-1",
        type="default",
        children=html.Div(id="loading-output-1",
                          children=[
                              dcc.Graph(id='wealth-indexes'),
                              daq.BooleanSwitch(id='logarithmic-scale-switch',
                                                on=False,
                                                label="Logarithmic Y-Scale",
                                                labelPosition="bottom"),
                              html.H4(children='Statistics table'),
                              html.Div(id="describe-table"),
                          ]
                          )
    )

],
    # style={'width': '98%', 'display': 'inline-block'},
    fluid=True,
)


@app.callback(
    Output(component_id='wealth-indexes', component_property='figure'),
    Output(component_id='describe-table', component_property='children'),
    Input(component_id='submit-button-state', component_property='n_clicks'),
    State(component_id='symbols-list', component_property='value'),
    State(component_id='base-currency', component_property='value'),
    State(component_id='first-date', component_property='value'),
    State(component_id='last-date', component_property='value'),
    Input(component_id='logarithmic-scale-switch', component_property='on'),
)
def update_graf(n_clicks, selected_symbols: list, ccy: str, fd_value: str, ld_value: str, on: bool):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    al = ok.AssetList(symbols, first_date=fd_value, last_date=ld_value, ccy=ccy, inflation=True)
    df = al.wealth_indexes
    ind = df.index.to_timestamp('D')
    table = al.describe().iloc[:-4, :]  # there is a problem with dates '2020-08' in the last 4 rows
    columns = [
        dict(id=i, name=i, type='numeric', format=dash_table.FormatTemplate.percentage(2))
        for i in table.columns
    ]
    fig = px.line(df, x=ind, y=df.columns[:-1],
                  log_y=on,
                  title='Assets Wealth indexes',
                  # width=800,
                  height=800
                  )
    # Plot Inflation
    fig.add_trace(go.Scatter(x=ind, y=df.iloc[:, -1],
                             mode="none",
                             fill="tozeroy",
                             fillcolor="rgba(226,150,65,0.5)",
                             name="Inflation")
                  )
    # Plot Financial crisis historical data (sample)
    crisis_first_date = pd.to_datetime('2007-10', format='%Y-%m')
    crisis_last_date = pd.to_datetime('2009-09', format='%Y-%m')
    if (al.first_date < crisis_first_date) and (al.last_date > crisis_last_date):
        fig.add_vrect(x0=crisis_first_date.strftime(format='%Y-%m'), x1=crisis_last_date.strftime(format='%Y-%m'),
                      annotation_text="US Housing Bubble",
                      annotation_position="top left",
                      fillcolor="red",
                      opacity=0.25,
                      line_width=0)

    # Plot x-axis slider
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        xaxis_title="Date",
        legend_title="Assets",
        # font=dict(
        #     family="Courier New, monospace",
        #     size=18,
        #     color="RebeccaPurple"
        # )
    )

    table = dash_table.DataTable(
        data=table.to_dict(orient='records'),
        columns=columns,
        # page_size=4
    )
    return fig, table


if __name__ == '__main__':
    app.run_server(debug=True)
