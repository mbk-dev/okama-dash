import pickle
from pathlib import Path

import dash
import dash.exceptions
from dash import callback, html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import okama as ok

import common
import common.create_link
import common.math
import common.settings
import common.update_style
from common.parse_query import make_list_from_string

from pages.efficient_frontier.cards_efficient_frontier.ef_description import card_ef_description
from pages.efficient_frontier.cards_efficient_frontier.ef_info import card_ef_info
from pages.efficient_frontier.cards_efficient_frontier.ef_chart import card_graf
from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls
from pages.efficient_frontier.cards_efficient_frontier.ef_chart_transition_map import card_transition_map
from pages.efficient_frontier.cards_efficient_frontier.ef_find_weights import card_ef_find_weights

from common.mobile_screens import adopt_small_screens
from pages.efficient_frontier.prepare_ef_plot import prepare_transition_map, prepare_ef

dash.register_page(
    __name__,
    path="/",
    title="Efficient Frontier : okama",
    name="Efficient Frontier",
    description="Efficient Frontier for the investment portfolios",
)

data_folder = Path(__file__).parent.parent.parent / common.cache_directory

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
            dbc.Row(dbc.Col(card_graf, width=12), align="center", style={"display": "none"}, id="ef-graf-row"),
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
                    ],
                    style={"display": "none"},
                    id="ef-portfolio-data-row",
                ),
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [dbc.Button(
                                "Backtest portfolio",
                                id="ef-backtest-portfolio-button",
                                external_link=True,
                                target="_blank",
                                color="primary"
                            )],
                            style={"text-align": "center"},
                            className="p-3",
                        )
                    ),
                ],
                style={"display": "none"},
                id="ef-backtest-optimized-potfolio-button-row",
            ),
            dbc.Row(
                dbc.Col(card_ef_find_weights, width=12),
                align="center",
                style={"display": "none"},
                id="ef-find-portfolio-row",
            ),
            dbc.Row(
                dbc.Col(card_transition_map, width=12),
                align="center",
                style={"display": "none"},
                id="ef-transition-map-row",
            ),
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
    Output(component_id="ef_portfolio_file_name", component_property="data"),  # save ef file name to session
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
    State(component_id="mdp-line-option", component_property="value"),
    State(component_id="cml-option", component_property="value"),
    State(component_id="risk-free-rate-option", component_property="value"),
    # Monte-Carlo
    State(component_id="monte-carlo-option", component_property="value"),
    prevent_initial_call=True,
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
    mdp_option: str,
    cml_option: str,
    rf_rate: float,
    n_monte_carlo: int,
):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    if not symbols:
        raise dash.exceptions.PreventUpdate
    new_ef_file_name_str = common.create_link.create_filename(tickers_list=sorted(symbols),
                                                          ccy=ccy,
                                                          first_date=fd_value,
                                                          last_date=ld_value
                                                          )
    new_ef_file = data_folder / new_ef_file_name_str
    if new_ef_file.is_file():
        with open(new_ef_file, 'rb') as f:
            print("found cached EF file...")
            ef_object = pickle.load(f)
    else:
        print("Downloading data from API...")
        ef_object = ok.EfficientFrontier(
            symbols,
            first_date=fd_value,
            last_date=ld_value,
            ccy=ccy,
            inflation=False,
            n_points=40,
            full_frontier=True,
        )
    ef_options = dict(
        plot_type=plot_option, mdp=mdp_option, cml=cml_option, rf_rate=rf_rate, n_monte_carlo=n_monte_carlo
    )
    ef = ef_object.ef_points * 100
    # Cache ef to pickle file
    ef_file_name = common.create_link.create_filename(tickers_list=ef_object.symbols,
                                                      ccy=ef_object.currency,
                                                      first_date=ef_object.first_date.strftime('%Y-%m'),
                                                      last_date=ef_object.last_date.strftime('%Y-%m')
                                                      )
    data_file = data_folder / ef_file_name
    with open(data_file, 'wb') as f:  # open a text file
        pickle.dump(ef_object, f, protocol=pickle.HIGHEST_PROTOCOL)  # serialize the EF

    # Cache to redis
    # https://stackoverflow.com/questions/15219858/how-to-store-a-complex-object-in-redis-using-redis-py
    # r = redis.StrictRedis(host='localhost', port=6379, db=0)
    # pickled_object = pickle.dumps(ef)
    # r.set('stored_portfolio', pickled_object)
    # unpacked_object = pickle.loads(r.get('some_key'))
    # print(ef == unpacked_object)

    fig1 = prepare_ef(ef, ef_object, ef_options)
    fig2 = prepare_transition_map(ef)

    # Change layout for mobile screens
    fig1, config1 = adopt_small_screens(fig1, screen)
    fig2, config2 = adopt_small_screens(fig2, screen)
    return fig1, fig2, config1, config2, ef_file_name


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
    risk_str = f"Risk: {risk:.2f}%"

    ror = clickData["points"][0]["y"]
    ror_str = f"Return: {ror:.2f}%"

    weights_str = None
    try:
        weights_list = clickData["points"][0]["customdata"]
    except KeyError:
        pass
    else:
        weights_str = "Weights:" + ",".join([f" {t}={w:.2f}% " for w, t in zip(weights_list, symbols)])
    return risk_str, ror_str, weights_str


@callback(
    Output(component_id="ef-graf-row", component_property="style"),
    Output(component_id="ef-portfolio-data-row", component_property="style"),
    Output(component_id="ef-find-portfolio-row", component_property="style"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-graf-row", component_property="style"),
)
def show_graf_and_portfolio_data_and_find_portfolio_rows(n_clicks, style):
    style = common.update_style.change_style_for_hidden_row(n_clicks, style)
    return style, style, style


@callback(
    Output(component_id="ef-transition-map-row", component_property="style"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-transition-map-row", component_property="style"),
    State(component_id="transition-map-option", component_property="value"),
)
def show_transition_map_row(n_clicks, style, tr_map_option):
    if tr_map_option == "On":
        style = None
    elif tr_map_option == "Off":
        style = {"display": "none"}
    return style


@callback(
    Output("ef-find-portfolio-mean-return", "children"),
    Output("ef-find-portfolio-cagr", "children"),
    Output("ef-find-portfolio-risk", "children"),
    Output("ef-find-portfolio-weights", "children"),
    Output("ef-backtest-optimized-potfolio-button", "href"),
    # Target return & ef file name
    Input(component_id="ef-find-portfolio-button", component_property="n_clicks"),
    State(component_id="ef-find-portfolio-input", component_property="value"),
    State(component_id="ef_portfolio_file_name", component_property="data")
)
def find_portfolio(n_clicks, ror, file_name):
    """
    Find optimized portfolio weights by rate of return (arithmetic mean).
    """
    if n_clicks ==0 or file_name is None:
        raise dash.exceptions.PreventUpdate
    with open(data_folder / file_name, 'rb') as f:
        ef_object = pickle.load(f)
    try:
        optimized_portfolio: dict = ef_object.minimize_risk(target_return=ror, monthly_return=False)
        optimized_portfolio.update((x , y * 100) for x, y in optimized_portfolio.items())
        mean_return = optimized_portfolio.pop('Mean return')
        cagr = optimized_portfolio.pop('CAGR')
        risk = optimized_portfolio.pop('Risk')
        mean_return_str = f"Mean return: {mean_return:.2f}%"
        cagr_str = f"CAGR: {cagr:.2f}%"
        risk_str = f"Risk: {risk:.2f}%"
        weights_str = "Weights:" + ",".join([f" {t}={w:.2f}% " for t, w in optimized_portfolio.items()])
        print(weights_str)
        weights_for_link = common.math.round_list(list(optimized_portfolio.values()), 2)
        link = common.create_link.create_link(
            href='/portfolio/',
            tickers_list=ef_object.symbols,
            ccy=ef_object.currency,
            first_date=ef_object.first_date.strftime('%Y-%m'),
            last_date = ef_object.last_date.strftime('%Y-%m'),
            weights_list=weights_for_link
        )
        print(link)
    except RecursionError:
        mean_return_str = ''
        cagr_str = ''
        risk_str = ''
        weights_str = "No solution was found."
        link = None
    return mean_return_str, cagr_str, risk_str, weights_str, link


@callback(
    Output(component_id="ef-find-portfolio-info-return-range", component_property="children"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    Input(component_id="ef_portfolio_file_name", component_property="data")
)
def show_max_min_return(n_clicks, file_name):
    """
    Show max and min annual rate of return (arithmetic mean).
    """
    if n_clicks ==0 or file_name is None:
        raise dash.exceptions.PreventUpdate
    with open(data_folder / file_name, 'rb') as f:
        ef_object = pickle.load(f)
    mean_return_range = ef_object.mean_return_range
    min_ror = (mean_return_range[0] + 1.) ** common.settings.MONTHS_PER_YEAR - 1.
    max_ror = (mean_return_range[-1] + 1.) ** common.settings.MONTHS_PER_YEAR - 1.
    return f"Portfolios rate of return range: {min_ror:.2f} - {max_ror:.2f} ({min_ror * 100:.2f} - {max_ror * 100:.2f}%)"
