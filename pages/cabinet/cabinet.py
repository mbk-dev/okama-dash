import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, dcc, html
from dash.exceptions import PreventUpdate

from common.auth.helpers import current_user_id
from common.auth.service import delete_config, list_configs, rename_config

dash.register_page(
    __name__,
    path="/cabinet",
    title="Personal cabinet : okama",
    name="Cabinet",
    description="Your saved widget configurations.",
)

PAGE_TYPE_LABELS = {
    "portfolio": "Portfolio",
    "ef": "Efficient Frontier",
    "compare": "Compare Assets",
    "benchmark": "Benchmark",
}


def layout(**kwargs):  # Dash passes URL query params (e.g. utm_*) as kwargs
    return dbc.Container(
        [
            dcc.Store(id="cabinet-refresh", data=0),
            dcc.Store(id="cabinet-rename-id"),
            html.H4("Saved configurations", className="mt-3"),
            html.Div(id="cabinet-list"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Rename configuration")),
                    dbc.ModalBody(dbc.Input(id="cabinet-rename-input", type="text")),
                    dbc.ModalFooter(dbc.Button("Save", id="cabinet-rename-confirm", color="primary", n_clicks=0)),
                ],
                id="cabinet-rename-modal",
                is_open=False,
            ),
        ],
        class_name="mt-2",
        fluid="md",
    )


def _config_row(config) -> html.Tr:
    return html.Tr(
        [
            html.Td(config.name),
            html.Td(PAGE_TYPE_LABELS.get(config.page_type, config.page_type)),
            html.Td(config.created_at.strftime("%Y-%m-%d")),
            html.Td(dcc.Link("Open", href=config.url)),
            html.Td(
                dbc.Button(
                    "Rename",
                    id={"type": "cabinet-rename", "index": config.id},
                    size="sm",
                    color="link",
                    n_clicks=0,
                )
            ),
            html.Td(
                dbc.Button(
                    "Delete",
                    id={"type": "cabinet-delete", "index": config.id},
                    size="sm",
                    color="link",
                    class_name="text-danger",
                    n_clicks=0,
                )
            ),
        ]
    )


@callback(Output("cabinet-list", "children"), Input("cabinet-refresh", "data"))
def render_list(_refresh):
    user_id = current_user_id()
    if user_id is None:
        # The before_request guard already redirects anonymous /cabinet visits;
        # this is defense in depth for the callback POST itself.
        return dbc.Alert("Please log in to see your saved configurations.", color="warning")
    configs = list_configs(user_id)
    if not configs:
        return html.P("No saved configurations yet. Press Save on any widget page.")
    header = html.Thead(
        html.Tr(
            [
                html.Th("Name"),
                html.Th("Page"),
                html.Th("Saved"),
                html.Th(""),
                html.Th(""),
                html.Th(""),
            ]
        )
    )
    return dbc.Table(
        [header, html.Tbody([_config_row(c) for c in configs])], striped=True, hover=True
    )


def _triggered_click_value() -> int | None:
    """n_clicks of the input that actually fired this callback (None on mount-fire)."""
    triggered = ctx.triggered
    if not triggered:
        return None
    return triggered[0]["value"]


@callback(
    Output("cabinet-refresh", "data"),
    Input({"type": "cabinet-delete", "index": ALL}, "n_clicks"),
    State("cabinet-refresh", "data"),
    prevent_initial_call=True,
)
def do_delete(_n_clicks_list, refresh):
    # Dynamically created buttons fire on mount with n_clicks None/0 —
    # only a real click carries a truthy value (2026-06-05 xlsx incident).
    if not _triggered_click_value():
        raise PreventUpdate
    user_id = current_user_id()
    if user_id is None:
        raise PreventUpdate
    delete_config(user_id, ctx.triggered_id["index"])
    return (refresh or 0) + 1


@callback(
    Output("cabinet-rename-modal", "is_open"),
    Output("cabinet-rename-id", "data"),
    Output("cabinet-rename-input", "value"),
    Input({"type": "cabinet-rename", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_rename(_n_clicks_list):
    if not _triggered_click_value():
        raise PreventUpdate
    user_id = current_user_id()
    if user_id is None:
        raise PreventUpdate
    config_id = ctx.triggered_id["index"]
    current = {c.id: c.name for c in list_configs(user_id)}.get(config_id, "")
    return True, config_id, current


@callback(
    Output("cabinet-rename-modal", "is_open", allow_duplicate=True),
    Output("cabinet-refresh", "data", allow_duplicate=True),
    Input("cabinet-rename-confirm", "n_clicks"),
    State("cabinet-rename-id", "data"),
    State("cabinet-rename-input", "value"),
    State("cabinet-refresh", "data"),
    prevent_initial_call=True,
)
def confirm_rename(n_clicks, config_id, new_name, refresh):
    if not n_clicks or config_id is None:
        raise PreventUpdate
    user_id = current_user_id()
    if user_id is None:
        raise PreventUpdate
    rename_config(user_id, config_id, new_name)
    return False, (refresh or 0) + 1
