import warnings

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

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
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server

app.layout = html.Div([
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

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
