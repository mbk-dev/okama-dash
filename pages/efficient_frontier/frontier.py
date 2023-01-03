import dash
import okama
from dash import callback, html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import okama as ok

from common.parse_query import make_list_from_string
from pages.efficient_frontier.cards_efficient_frontier.ef_description import card_ef_description
from pages.efficient_frontier.cards_efficient_frontier.ef_info import card_ef_info
from pages.efficient_frontier.cards_efficient_frontier.ef_chart import card_graf
from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls
from common.mobile_screens import adopt_small_screens
from pages.efficient_frontier.prepare_ef_plot import prepare_transition_map, prepare_ef

dash.register_page(
    __name__,
    path="/",
    title="Efficient Frontier : okama",
    name="Efficient Frontier",
    description="Efficient Frontier for the investment portfolios",
)


def layout(tickers=None, first_date=None, last_date=None, ccy=None, **kwargs):
    tickers_list = make_list_from_string(tickers)
    page = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers_list, first_date, last_date, ccy), lg=7),
                    dbc.Col(card_ef_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf, width=12), align="center"),
            dbc.Row(
                html.Div(
                    [
                        dcc.Markdown(
                            """
                        **Portfolio data**  
                        Click on points to get portfolio data.
                        """
                        ),
                        html.P(id="ef-click-data-risk"),
                        html.P(id="ef-click-data-return"),
                        html.Pre(id="ef-click-data-weights"),
                    ]
                ),
            ),
            dbc.Row(dbc.Col(card_ef_description, width=12), align="left"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="ef-graf", component_property="figure"),
    Output(component_id="ef-graf", component_property="config"),
    # Inputs
    Input(component_id="store", component_property="data"),
    # Main input for EF
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
    State(component_id="ef-base-currency", component_property="value"),
    State(component_id="ef-first-date", component_property="value"),
    State(component_id="ef-last-date", component_property="value"),
    # Options
    State(component_id="ef-plot-options", component_property="value"),
    State(component_id="cml-option", component_property="value"),
    State(component_id="risk-free-rate-option", component_property="value"),
    # Monte-Carlo
    State(component_id="monte-carlo-option", component_property="value"),
    # Input(component_id="ef-return-type-checklist-input", component_property="value"),
    prevent_initial_call=False,
)
def update_ef_cards(
    screen,
    n_clicks,
    # Main input
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    # Options
    plot_option: str,
    cml_option: str,
    rf_rate: float,
    n_monte_carlo: int,
):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    ef_object = ok.EfficientFrontier(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=False,
        n_points=40,
        full_frontier=True,
    )
    ef_options = dict(plot_type=plot_option, cml=cml_option, rf_rate=rf_rate, n_monte_carlo=n_monte_carlo)
    ef = ef_object.ef_points * 100
    if ef_options["plot_type"] in ["Arithmetic", "Geometric"]:
        fig = prepare_ef(ef, ef_object, ef_options)
    elif ef_options["plot_type"] == "Transition":
        fig = prepare_transition_map(ef, ef_object, ef_options)
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    return fig, config


@callback(
    Output("ef-click-data-risk", "children"),
    Output("ef-click-data-return", "children"),
    Output("ef-click-data-weights", "children"),
    Input("ef-graf", "clickData"),
)
def display_click_data(clickData):
    if not clickData:
        raise dash.exceptions.PreventUpdate
    risk = clickData["points"][0]["x"]
    rist_str = f"Risk: {risk:.2f}%"

    ror = clickData["points"][0]["y"]
    ror_str = f"Return: {ror:.2f}%"

    weights_str = None
    try:
        weights_list = clickData["points"][0]["customdata"]
    except KeyError:
        pass
    else:
        weights_str = "Weights:" + ",".join([f"{x:.2f}% " for x in weights_list])
    return rist_str, ror_str, weights_str
