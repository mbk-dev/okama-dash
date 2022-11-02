import warnings

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import plotly.io as pio

import navigation, footer

warnings.simplefilter(action="ignore", category=FutureWarning)

pio.templates.default = "plotly_white"

app = dash.Dash(
    __name__,
    use_pages=True,
    update_title="Loading okama ...",
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    # suppress_callback_exceptions=True
)
server = app.server

app.layout = html.Div([dcc.Store(id="store"), navigation.navbar, dash.page_container, footer.footer()])

app.clientside_callback(
    """
    function(trigger) {
        //  can use any prop to trigger this callback - we just want to store the info on startup
        const inner_width  = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
        const inner_height = window.innerHeight|| document.documentElement.clientHeight|| document.body.clientHeight;
        const screenInfo = {height :screen.height, width: screen.width, in_width: inner_width, in_height: inner_height};

        return screenInfo
    }
    """,
    Output("store", "data"),
    Input("store", "data"),
)


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
