import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from flask_login import login_user

from common.auth.service import verify_credentials

dash.register_page(
    __name__,
    path="/login",
    title="Login : okama",
    name="Login",
    description="Log in to your okama account.",
)


def layout(**kwargs):  # Dash passes URL query params (e.g. utm_*) as kwargs
    return dbc.Container(
        [
            dcc.Location(id="login-redirect", refresh=True),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Div(
                                [
                                    html.H4("Log in"),
                                    dbc.Input(id="login-email", type="email", placeholder="Email"),
                                    dbc.Input(id="login-password", type="password", placeholder="Password"),
                                    html.Div(id="login-error", className="text-danger"),
                                    html.Div(
                                        dbc.Button("Log in", id="login-submit", color="primary", n_clicks=0),
                                        className="p-3",
                                        style={"textAlign": "center"},
                                    ),
                                    html.Div(dcc.Link("No account? Register", href="/register")),
                                ],
                                className="vstack gap-2",
                            )
                        )
                    ),
                    lg=4,
                    md=6,
                    sm=12,
                ),
                justify="center",
            ),
        ],
        class_name="mt-4",
        fluid="md",
    )


@callback(
    Output("login-redirect", "href"),
    Output("login-error", "children"),
    Input("login-submit", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def do_login(n_clicks, email, password):
    user = verify_credentials(email, password)
    if user is None:
        return dash.no_update, "Wrong email or password."
    login_user(user, remember=True)
    return "/cabinet", ""
