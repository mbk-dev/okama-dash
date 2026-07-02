import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from flask_login import login_user

from common.auth.service import create_user

dash.register_page(
    __name__,
    path="/register",
    title="Register : okama",
    name="Register",
    description="Create an okama account to save widget configurations.",
)


def layout(**kwargs):  # Dash passes URL query params (e.g. utm_*) as kwargs
    return dbc.Container(
        [
            dcc.Location(id="register-redirect", refresh=True),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Div(
                                [
                                    html.H4("Create account"),
                                    dbc.Input(id="register-email", type="email", placeholder="Email"),
                                    dbc.Input(
                                        id="register-password",
                                        type="password",
                                        placeholder="Password (8+ characters)",
                                    ),
                                    dbc.Input(
                                        id="register-password2",
                                        type="password",
                                        placeholder="Repeat password",
                                    ),
                                    html.Div(id="register-error", className="text-danger"),
                                    html.Div(
                                        dbc.Button("Register", id="register-submit", color="primary", n_clicks=0),
                                        className="p-3",
                                        style={"textAlign": "center"},
                                    ),
                                    html.Div(dcc.Link("Already have an account? Log in", href="/login")),
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
    Output("register-redirect", "href"),
    Output("register-error", "children"),
    Input("register-submit", "n_clicks"),
    State("register-email", "value"),
    State("register-password", "value"),
    State("register-password2", "value"),
    prevent_initial_call=True,
)
def do_register(n_clicks, email, password, password2):
    if (password or "") != (password2 or ""):
        return dash.no_update, "Passwords do not match."
    user, error = create_user(email, password)
    if error:
        return dash.no_update, error
    login_user(user, remember=True)
    return "/cabinet", ""
