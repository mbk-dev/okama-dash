"""Save-to-cabinet button, rendered next to Copy link on the 4 widget pages.

Always present in the layout but hidden for anonymous users (a callback on the
global auth-url Location toggles visibility — uniform regardless of whether the
page builds its controls card at import time or per request). The saved URL is
read from the page's existing hidden show-url div — the exact string Copy link
copies, written by the page's link callback after Submit.
"""

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate

from common.auth.helpers import current_user_id, user_is_authenticated
from common.auth.service import save_config


def create_save_config_div(prefix: str, card_name: str) -> html.Div:
    return html.Div(
        [
            dbc.Button(
                ["Save", html.I(className="bi bi-bookmark ms-2")],
                id=f"{prefix}-save-config-button",
                color="link",
                n_clicks=0,
            ),
            dbc.Tooltip(
                f"Save {card_name} settings to your cabinet",
                target=f"{prefix}-save-config-button",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(f"Save {card_name} configuration")),
                    dbc.ModalBody(
                        html.Div(
                            [
                                dbc.Input(id=f"{prefix}-save-config-name", type="text", placeholder="Name"),
                                html.Div(id=f"{prefix}-save-config-feedback"),
                            ],
                            className="vstack gap-2",
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Save", id=f"{prefix}-save-config-confirm", color="primary", n_clicks=0)
                    ),
                ],
                id=f"{prefix}-save-config-modal",
                is_open=False,
            ),
        ],
        id=f"{prefix}-save-config-div",
        hidden=True,  # un-hidden by the visibility callback for logged-in users
        style={"textAlign": "center"},
    )


def save_button_hidden(_pathname: str | None) -> bool:
    return not user_is_authenticated()


def open_save_modal(n_clicks: int | None) -> bool:
    if not n_clicks:
        raise PreventUpdate
    return True


def do_save_config(page_type: str, n_clicks: int | None, name: str | None, url: str | None):
    if not n_clicks:
        raise PreventUpdate
    user_id = current_user_id()
    if user_id is None:
        return False, ""  # button is hidden for anonymous users; defense in depth
    _, error = save_config(user_id, name, page_type, url)
    if error:
        return True, dbc.Alert(error, color="danger", class_name="mb-0")
    return False, ""


def register_save_config(prefix: str, page_type: str) -> None:
    """Register the 3 per-page callbacks (same closure pattern as register_macro_download)."""
    callback(
        Output(f"{prefix}-save-config-div", "hidden"),
        Input("auth-url", "pathname"),
    )(save_button_hidden)

    callback(
        Output(f"{prefix}-save-config-modal", "is_open"),
        Input(f"{prefix}-save-config-button", "n_clicks"),
        prevent_initial_call=True,
    )(open_save_modal)

    def _do_save(n_clicks, name, url):
        return do_save_config(page_type, n_clicks, name, url)

    callback(
        Output(f"{prefix}-save-config-modal", "is_open", allow_duplicate=True),
        Output(f"{prefix}-save-config-feedback", "children"),
        Input(f"{prefix}-save-config-confirm", "n_clicks"),
        State(f"{prefix}-save-config-name", "value"),
        State(f"{prefix}-show-url", "children"),
        prevent_initial_call=True,
    )(_do_save)
