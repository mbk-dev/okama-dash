"""
test URL:
http://127.0.0.1:8050/portfolio?tickers=SPY.US,BND.US,GLD.US&weights=30,20,50&first_date=2015-01&last_date=2020-12&ccy=RUB&rebal=year

Assembles the Portfolio controls card from the per-feature sections
(constructor / options / monte_carlo) plus the small generic rows below; the
section callbacks live in their own modules.
"""

from typing import Optional

import dash_bootstrap_components as dbc
from dash import html, dcc

import pandas as pd

from common import inflation as inflation
from common.html_elements.submit_spinner import create_submit_spinner
from common.html_elements.copy_link_div import create_copy_link_div
from common.parse_query import make_list_from_string
from common.date_input import date_input, register_date_validation
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl
from pages.portfolio.cards_portfolio.rebalancing_controls import rebalancing_accordion_item
from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item
from .constructor import tickers_weights_block
from .options import options_section
from .monte_carlo import monte_carlo_section


today_str = pd.Timestamp.today().strftime("%Y-%m")


def _accordion_active_items(abs_dev, rel_dev, cf_strategy, cf_amount, cf_pct, vds_pct, cwd_amount, cf_ts):
    active = []
    if abs_dev is not None or rel_dev is not None:
        active.append("rebalancing")
    has_cf = (
        (cf_strategy is not None and cf_strategy != "indexation")
        or (cf_amount is not None and cf_amount != 0)
        or (cf_pct is not None and cf_pct != 0)
        or vds_pct is not None
        or (cwd_amount is not None and cwd_amount != 0)
        or cf_ts is not None
    )
    if has_cf:
        active.append("cashflow")
    return active or []


def _base_currency_row(ccy, currency_list):
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Base currency"),
                    dcc.Dropdown(
                        options=currency_list,
                        # URL values are normalized and validated: dcc.Dropdown
                        # silently clears a value missing from its options.
                        value=inflation.resolve_url_currency(ccy, currency_list),
                        multi=False,
                        clearable=False,
                        placeholder="Select a base currency",
                        id="pf-base-currency",
                    ),
                ],
            ),
        ]
    )


def _dates_row(first_date, last_date):
    return dbc.Row(
        [
            dbc.Col(
                [html.Label("First Date")] + date_input("pf-first-date", first_date if first_date else "2000-01")
            ),
            dbc.Col(
                [html.Label("Last Date")] + date_input("pf-last-date", last_date if last_date else today_str)
            ),
        ]
    )


# Portfolio ticker — a portfolio identity attribute (okama symbol), not a
# cash-flow parameter; kept outside the accordion so it stays visible even when
# the Cash Flow Strategy accordion is collapsed.
def _portfolio_ticker_row(symbol):
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Label(
                        [
                            "Portfolio ticker",
                            html.I(
                                className="bi bi-info-square ms-2",
                                id="pf-info-ticker",
                            ),
                        ]
                    ),
                    dbc.Input(
                        id="pf-ticker",
                        type="text",
                        value=symbol if symbol else "PORTFOLIO",
                    ),
                    dbc.FormText("Symbols without spaces"),
                    dbc.Tooltip(
                        tl.pf_options_tooltip_ticker,
                        target="pf-info-ticker",
                    ),
                ],
                lg=6,
                md=6,
                sm=12,
            ),
        ],
        class_name="mt-2 mb-2",
    )


def _copy_link_row():
    return dbc.Row(
        [
            dbc.Col(
                # copy link to clipboard button
                create_copy_link_div(
                    location_id="pf-url",
                    hidden_div_with_url_id="pf-show-url",
                    button_id="pf-copy-link-button",
                    card_name="Portfolio",
                    # style={"textAlign": "right"}
                ),
            ),
        ]
    )


def _submit_row():
    return html.Div(
        [
            dbc.Button(
                children="Submit",
                id="pf-submit-button",
                n_clicks=0,
                color="primary",
            ),
            dbc.DropdownMenu(
                label="Go to",
                id="pf-goto-menu",
                # Outline look to match the previous Go to EF button:
                # DropdownMenu has no outline prop; btn-outline-primary
                # supplies the outline palette while assets/forms.css
                # neutralizes the solid btn-primary background that the
                # default color leaves behind. d-inline-block keeps the
                # menu wrapper on the Submit line (its default div is block).
                toggle_class_name="btn-outline-primary",
                class_name="d-inline-block ms-2",
                children=[
                    dbc.DropdownMenuItem(
                        "Efficient Frontier", id="pf-goto-ef", external_link=True, target="_blank"
                    ),
                    dbc.DropdownMenuItem(
                        "Compare Assets", id="pf-goto-compare", external_link=True, target="_blank"
                    ),
                    dbc.DropdownMenuItem(
                        "Benchmark", id="pf-goto-benchmark", external_link=True, target="_blank"
                    ),
                ],
            ),
            create_submit_spinner("pf-submit-spinner"),
        ],
        style={"textAlign": "center"},
        className="p-3",
    )


def card_controls(
    tickers: Optional[list],
    weights: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
    rebal: Optional[str],
    # advanced
    initial_amount: Optional[float],
    cashflow: Optional[float],
    discount_rate: Optional[float],
    symbol: Optional[str],
    # rebalancing deviation
    abs_dev: Optional[float] = None,
    rel_dev: Optional[float] = None,
    # cashflow strategy
    cf_strategy: Optional[str] = None,
    cf_freq: Optional[str] = None,
    cf_amount: Optional[float] = None,
    cf_indexation: Optional[float] = None,
    cf_pct: Optional[float] = None,
    vds_pct: Optional[float] = None,
    vds_min: Optional[float] = None,
    vds_max: Optional[float] = None,
    vds_adj_mm: Optional[bool] = None,
    vds_floor: Optional[float] = None,
    vds_ceil: Optional[float] = None,
    vds_adj_fc: Optional[bool] = None,
    vds_indexation: Optional[float] = None,
    cwd_amount: Optional[float] = None,
    cwd_indexation: Optional[float] = None,
    # parsed CSV pairs: list of (str, str) tuples or None
    cwd_tr: Optional[list] = None,
    cf_ts: Optional[list] = None,
):
    tickers_list = make_list_from_string(tickers, char_type="str")
    weights_list = make_list_from_string(weights, char_type="float")
    currency_list = inflation.get_currency_list()
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Investment Portfolio", className="card-title"),
                tickers_weights_block(),
                _base_currency_row(ccy, currency_list),
                html.Div(
                    [
                        # Attributes
                        _dates_row(first_date, last_date),
                        # Rebalancing & Cash Flow Strategy
                        dbc.Row(
                            [
                                dbc.Accordion(
                                    [
                                        rebalancing_accordion_item(
                                            rebal=rebal,
                                            abs_dev=abs_dev,
                                            rel_dev=rel_dev,
                                        ),
                                        cashflow_accordion_item(
                                            initial_amount=initial_amount,
                                            cashflow=cashflow,
                                            discount_rate=discount_rate,
                                            cf_strategy=cf_strategy,
                                            cf_freq=cf_freq,
                                            cf_amount=cf_amount,
                                            cf_indexation=cf_indexation,
                                            cf_pct=cf_pct,
                                            vds_pct=vds_pct,
                                            vds_min=vds_min,
                                            vds_max=vds_max,
                                            vds_adj_mm=vds_adj_mm,
                                            vds_floor=vds_floor,
                                            vds_ceil=vds_ceil,
                                            vds_adj_fc=vds_adj_fc,
                                            vds_indexation=vds_indexation,
                                            cwd_amount=cwd_amount,
                                            cwd_indexation=cwd_indexation,
                                            cwd_tr=cwd_tr,
                                            cf_ts=cf_ts,
                                        ),
                                    ],
                                    active_item=_accordion_active_items(
                                        abs_dev=abs_dev,
                                        rel_dev=rel_dev,
                                        cf_strategy=cf_strategy,
                                        cf_amount=cf_amount,
                                        cf_pct=cf_pct,
                                        vds_pct=vds_pct,
                                        cwd_amount=cwd_amount,
                                        cf_ts=cf_ts,
                                    ),
                                    flush=True,
                                    class_name="p-0",
                                    always_open=True,
                                )
                            ],
                        ),
                        _portfolio_ticker_row(symbol),
                        _copy_link_row(),
                        *options_section(),
                        *monte_carlo_section(),
                    ]
                ),
                _submit_row(),
                dcc.Store(id="pf_tickers_url", data=tickers_list),
                dcc.Store(id="pf_weights_url", data=weights_list),
                dcc.Store(id="pf_saved_portfolios_file_names", storage_type="session"),
            ]
        ),
        class_name="mb-3",
    )
    return card


register_date_validation("pf-first-date")
register_date_validation("pf-last-date")
