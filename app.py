import warnings

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import navigation

warnings.simplefilter(action="ignore", category=FutureWarning)

app = dash.Dash(
    __name__,
    use_pages=True,
    # title="okama widgets",
    update_title="Loading okama ...",
    # meta_tags=[
    #     {"name": "title", "content": "okama widgets"},
    #     {
    #         "name": "description",
    #         "content": "Okama widget to compare financial assets properties: rate of return, risk, CVAR, drawdowns",
    #     },
    # ],
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
)
server = app.server

app.layout = html.Div([
    dcc.Store(id="store"),
    navigation.navbar,
    # html.H1('Multi-page app with Dash Pages'),
    #
    # html.Div(
    #     [
    #         html.Div(
    #             dcc.Link(
    #                 f"{page['name']} - {page['path']}", href=page["relative_path"]
    #             )
    #         )
    #         for page in dash.page_registry.values()
    #     ]
    # ),

    dash.page_container
])


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
