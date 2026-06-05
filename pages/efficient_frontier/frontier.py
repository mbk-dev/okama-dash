import dash
import dash.exceptions
from dash import callback, html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.graph_objects as go

import common
import common.create_link
import common.math
import common.update_style
from common.parse_query import make_list_from_string
from common.ef_grid import parse_grid_step_value

from pages.efficient_frontier.cards_efficient_frontier.ef_description import card_ef_description
from pages.efficient_frontier.cards_efficient_frontier.ef_info import card_ef_info
from pages.efficient_frontier.cards_efficient_frontier.ef_chart import card_graf
from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls
from pages.efficient_frontier.cards_efficient_frontier.ef_chart_transition_map import card_transition_map
from pages.efficient_frontier.cards_efficient_frontier.ef_find_weights import card_ef_find_weights
from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import build_portfolio_card

from common.html_elements.submit_spinner import submit_spinner_running
from common.mobile_screens import adopt_small_screens, is_small_screen
from pages.efficient_frontier.prepare_ef_plot import prepare_transition_map, prepare_ef, compact_ef_for_small_screens
from pages.efficient_frontier.ef_cache import get_minimized_risk_portfolio, get_or_create_ef_object, load_ef_object

dash.register_page(
    __name__,
    path="/",
    title="Efficient Frontier : okama",
    name="Efficient Frontier",
    description="Efficient Frontier for the investment portfolios",
)


def _parse_url_portfolio(tickers_list, weights, symbol) -> dict | None:
    """Parse the portfolio section of the URL (weights + symbol) into store data.

    Returns None when the section is absent or invalid (unparseable weights,
    count mismatch with tickers, sum far from 100): the portfolio overlay must
    never break the frontier or the form prefill.
    """
    if not tickers_list or not weights:
        return None
    try:
        weights_list = make_list_from_string(weights, char_type="float")
    except (ValueError, TypeError):
        return None
    if not weights_list or len(weights_list) != len(tickers_list):
        return None
    # Inverted comparison so a NaN sum (empty CSV field) also fails the check.
    if not abs(sum(weights_list) - 100.0) < 1e-6:
        return None
    return {"tickers": tickers_list, "weights": weights_list, "symbol": symbol}


def layout(tickers=None, first_date=None, last_date=None, ccy=None, rebal=None, weights=None, symbol=None, **kwargs):
    tickers_list = make_list_from_string(tickers)
    page = dbc.Container(
        [
            # Portfolio handed off from the Portfolio page via URL; None for
            # ordinary share links without a portfolio section.
            dcc.Store(id="ef-url-portfolio", data=_parse_url_portfolio(tickers_list, weights, symbol)),
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers_list, first_date, last_date, ccy, rebal), lg=7),
                    dbc.Col(card_ef_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf, width=12), align="center", style={"display": "none"}, id="ef-graf-row"),
            dbc.Row(
                html.Div(
                    [
                        html.H4("Selected portfolio"),
                        html.P(
                            "Click on points to get portfolio data.",
                            id="ef-click-hint",
                            className="text-muted",
                        ),
                        html.Div(id="ef-selected-portfolio"),
                        dcc.Store(id="ef-trace-names"),
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
                            style={"textAlign": "center"},
                            className="p-3",
                        )
                    ),
                ],
                style={"display": "none"},
                id="ef-backtest-portfolio-button-row",
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
    Output(component_id="ef-trace-names", component_property="data"),  # trace names for the click badge
    # Inputs
    Input(component_id="store", component_property="data"),
    # Main input for EF
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
    State(component_id="ef-base-currency", component_property="value"),
    State(component_id="ef-first-date", component_property="value"),
    State(component_id="ef-last-date", component_property="value"),
    # Options
    State(component_id="ef-rebalancing-frequency", component_property="value"),
    State(component_id="ef-plot-options", component_property="value"),
    State(component_id="mdp-line-option", component_property="value"),
    State(component_id="cml-option", component_property="value"),
    State(component_id="risk-free-rate-option", component_property="value"),
    # Monte-Carlo
    State(component_id="monte-carlo-option", component_property="value"),
    # Simulation mode + grid step
    State(component_id="ef-sim-mode", component_property="value"),
    State(component_id="ef-grid-step", component_property="value"),
    # Show the spinner under the Submit button while computing (the chart's
    # own dcc.Loading spinner is below the fold on mobile).
    running=submit_spinner_running("ef-submit-spinner"),
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
    rebalancing_period: str,
    plot_option: str,
    mdp_option: str,
    cml_option: str,
    rf_rate: float,
    n_monte_carlo: int,
    sim_mode: str,
    grid_step_value: str,
):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    if not symbols:
        raise dash.exceptions.PreventUpdate
    try:
        ef_object, ef_file_name = get_or_create_ef_object(
            symbols=symbols,
            ccy=ccy,
            first_date=fd_value,
            last_date=ld_value,
            rebalancing_period=rebalancing_period,
        )
        grid_step = None
        effective_n_monte_carlo = 0
        if sim_mode == "Grid":
            grid_step = parse_grid_step_value(grid_step_value, len(symbols))
        elif sim_mode == "Monte Carlo":
            effective_n_monte_carlo = n_monte_carlo
        ef_options = {
            "plot_type": plot_option,
            # The Y-axis selector was removed from the UI: the chart always plots CAGR.
            "return_type": "Geometric",
            "mdp": mdp_option,
            "cml": cml_option,
            "rf_rate": rf_rate,
            "n_monte_carlo": effective_n_monte_carlo,
            "grid_step": grid_step,
        }
        ef = ef_object.ef_points * 100

        fig1 = prepare_ef(ef, ef_object, ef_options, ef_cache_key=ef_file_name)
        fig2 = prepare_transition_map(ef)

        if is_small_screen(screen):
            fig1 = compact_ef_for_small_screens(fig1)
        fig1, config1 = adopt_small_screens(fig1, screen)
        fig2, config2 = adopt_small_screens(fig2, screen)
        trace_names = [getattr(trace, "name", "") or "" for trace in fig1.data]
        return fig1, fig2, config1, config2, ef_file_name, trace_names
    except Exception as e:
        alert_fig = go.Figure()
        alert_fig.add_annotation(text=str(e), showarrow=False, font={"color": "red", "size": 14})
        return alert_fig, go.Figure(), {}, {}, None, []


def _ef_rebalancing_period(ef_object) -> str | None:
    """Rebalancing period the frontier was computed with, for backtest links.

    Falls back to None (link omits rebal) for cached EF pickles created before
    the rebalancing_strategy era or with an older okama lacking the kwarg.
    """
    strategy = getattr(ef_object, "rebalancing_strategy", None)
    return getattr(strategy, "period", None)


@callback(
    Output("ef-selected-portfolio", "children"),
    Output("ef-backtest-portfolio-button", "href"),
    Input("ef-graf", "clickData"),
    # Portfolio data
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
    State(component_id="ef_portfolio_file_name", component_property="data"),
    State(component_id="risk-free-rate-option", component_property="value"),
    State(component_id="ef-trace-names", component_property="data"),
)
def display_click_data(clickData, n_click, symbols, file_name, rf_rate, trace_names):
    """
    Render the Selected portfolio card for the clicked chart point.
    """
    if not clickData:
        raise dash.exceptions.PreventUpdate
    if _is_submit_trigger():
        # A re-submit renders a new frontier: the previously clicked point no
        # longer belongs to it — reset the section to the hint instead of
        # re-rendering stale clickData (whose weights crash the strict zip
        # when the ticker set changed; live incident 2026-06-05).
        return None, None
    point_data = clickData["points"][0]
    risk = point_data["x"]
    ror = point_data["y"]
    stats = _point_stats(ror, risk, rf_rate)
    badge = _trace_badge(point_data, trace_names)

    weights_list = point_data.get("customdata")
    if weights_list is None or len(weights_list) != len(symbols):
        card = build_portfolio_card(
            stats=stats,
            symbols=symbols,
            weights=None,
            badge=badge,
            note="Weights: unavailable for this point.",
        )
        return card, None

    card = build_portfolio_card(stats=stats, symbols=symbols, weights=weights_list, badge=badge)
    weights_for_link = common.math.round_list(weights_list, 2)
    ef_object = load_ef_object(file_name)
    link = common.create_link.create_link(
        href='/portfolio/',
        tickers_list=ef_object.symbols,
        ccy=ef_object.currency,
        first_date=ef_object.first_date.strftime('%Y-%m'),
        last_date=ef_object.last_date.strftime('%Y-%m'),
        weights_list=weights_for_link,
        rebal=_ef_rebalancing_period(ef_object),
    )
    return card, link


def _is_submit_trigger() -> bool:
    """True when the running callback was triggered by the Submit button."""
    try:
        return dash.ctx.triggered_id == "ef-submit-button-state"
    except dash.exceptions.MissingCallbackContextException:
        # Direct invocation (component tests) — treat as a click trigger.
        return False


def _point_stats(ror: float, risk: float, rf_rate: float | None) -> list[tuple[str, str]]:
    """Stat blocks for a clicked point; Sharpe is skipped when risk is zero."""
    stats = [("CAGR", f"{ror:.2f}%"), ("Risk Σ", f"{risk:.2f}%")]
    if abs(risk) > 1e-9:
        sharpe = (ror - (rf_rate or 0.0)) / risk
        stats.append(("Sharpe", f"{sharpe:.2f}"))
    return stats


def _trace_badge(point_data: dict, trace_names: list | None) -> str | None:
    """Trace name for the badge, resolved from the clicked curve number."""
    curve_number = point_data.get("curveNumber")
    if trace_names and curve_number is not None and 0 <= curve_number < len(trace_names):
        return trace_names[curve_number] or None
    return None


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
    Output(component_id="ef-backtest-portfolio-button-row", component_property="style"),
    Output(component_id="ef-click-hint", component_property="style"),
    Input(component_id="ef-selected-portfolio", component_property="children"),
)
def show_backtest_portfolio_button_row(children):
    if children:
        return None, {"display": "none"}
    return {"display": "none"}, None


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
    Output("ef-find-portfolio-output", "children"),
    Output("ef-backtest-optimized-potfolio-button", "href"),
    # Target return & ef file name
    Input(component_id="ef-find-portfolio-button", component_property="n_clicks"),
    State(component_id="ef-find-portfolio-input", component_property="value"),
    State(component_id="ef_portfolio_file_name", component_property="data"),
    State(component_id="risk-free-rate-option", component_property="value"),
)
def find_portfolio(n_clicks, ror, file_name, rf_rate):
    """
    Find optimized portfolio weights by rate of return and render the card.
    """
    if n_clicks == 0 or file_name is None:
        raise dash.exceptions.PreventUpdate
    ef_object = load_ef_object(file_name)
    no_solution = html.P("No solution was found.", className="text-muted")
    try:
        target_value = ror / 100.
        optimized_portfolio = get_minimized_risk_portfolio(file_name, target_value)

        mean_return = optimized_portfolio.get('Mean return')
        cagr = optimized_portfolio.get('CAGR')
        risk = optimized_portfolio.get('Risk')

        asset_weights = {
            ticker: optimized_portfolio[ticker]
            for ticker in ef_object.symbols
            if ticker in optimized_portfolio
        }
        if not asset_weights and "Weights" in optimized_portfolio:
            asset_weights = dict(zip(ef_object.symbols, optimized_portfolio["Weights"], strict=True))
        if not asset_weights:
            return no_solution, None

        weights_percent = [w * 100 for w in asset_weights.values()]
        card = build_portfolio_card(
            stats=_optimized_stats(mean_return, cagr, risk, rf_rate),
            symbols=list(asset_weights),
            weights=weights_percent,
            title="Optimized portfolio",
        )
        weights_for_link = common.math.round_list(weights_percent, 2)
        link = common.create_link.create_link(
            href='/portfolio/',
            tickers_list=ef_object.symbols,
            ccy=ef_object.currency,
            first_date=ef_object.first_date.strftime('%Y-%m'),
            last_date=ef_object.last_date.strftime('%Y-%m'),
            weights_list=weights_for_link,
            rebal=_ef_rebalancing_period(ef_object),
        )
        return card, link
    except RecursionError:
        return no_solution, None


def _optimized_stats(
    mean_return: float | None,
    cagr: float | None,
    risk: float | None,
    rf_rate: float | None,
) -> list[tuple[str, str]]:
    """Stat blocks for the optimized portfolio; None values are skipped."""
    stats = []
    if mean_return is not None:
        stats.append(("Mean return", f"{mean_return * 100:.2f}%"))
    if cagr is not None:
        stats.append(("CAGR", f"{cagr * 100:.2f}%"))
    if risk is not None:
        stats.append(("Risk Σ", f"{risk * 100:.2f}%"))
    if cagr is not None and risk is not None and abs(risk) > 1e-9:
        sharpe = (cagr * 100 - (rf_rate or 0.0)) / (risk * 100)
        stats.append(("Sharpe", f"{sharpe:.2f}"))
    return stats


@callback(
    Output(component_id="ef-find-portfolio-info-return-range", component_property="children"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    Input(component_id="ef_portfolio_file_name", component_property="data")
)
def show_max_min_return(n_clicks, file_name):
    """
    Show max and min annual rate of return (CAGR).
    """
    if n_clicks ==0 or file_name is None:
        raise dash.exceptions.PreventUpdate
    ef_object = load_ef_object(file_name)
    ef_points = ef_object.ef_points
    if "CAGR" not in ef_points.columns:
        raise dash.exceptions.PreventUpdate
    min_ror = ef_points["CAGR"].min()
    max_ror = ef_points["CAGR"].max()
    return f"Portfolios CAGR range: {min_ror * 100:.2f} - {max_ror * 100:.2f}%"
