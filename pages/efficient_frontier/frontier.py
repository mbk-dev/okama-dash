import dash
import dash.exceptions
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
from pages.efficient_frontier.cards_efficient_frontier.ef_chart_transition_map import card_transition_map
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
            dbc.Row(dbc.Col(card_transition_map, width=12), align="center"),
            dbc.Row(dbc.Col(card_ef_description, width=12), align="left"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="ef-graf", component_property="figure"),
    Output(component_id="ef-transition-map-graf", component_property="figure"),
    Output(component_id="ef-graf", component_property="config"),
    Output(component_id="ef-transition-map-graf", component_property="config"),
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
    if not symbols:
        raise dash.exceptions.PreventUpdate
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
    fig1 = prepare_ef(ef, ef_object, ef_options)
    fig2 = prepare_transition_map(ef)

    # Change layout for mobile screens
    fig1, config1 = adopt_small_screens(fig1, screen)
    fig2, config2 = adopt_small_screens(fig2, screen)
    return fig1, fig2, config1, config2

@callback(
    Output(component_id="ef-transition-map-graf-div", component_property="hidden"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="transition-map-option", component_property="value"),
)
def hide_ef_transition_map_graf(n_clicks: int, tr_map_option: str) -> bool:
    return (tr_map_option != "On") or (n_clicks == 0)

@callback(
    Output("ef-click-data-risk", "children"),
    Output("ef-click-data-return", "children"),
    Output("ef-click-data-weights", "children"),
    Input("ef-graf", "clickData"),
    # List of tickers
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
)
def display_click_data(clickData, n_click, symbols):
    """
    Display portfolio weights, risk and return.
    """
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
        weights_str = "Weights:" + ",".join([f" {t}={w:.2f}% " for w, t in zip(weights_list, symbols)])
    return rist_str, ror_str, weights_str
