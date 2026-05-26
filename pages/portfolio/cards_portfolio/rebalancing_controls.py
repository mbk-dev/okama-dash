from dash import html, dcc, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def rebalancing_accordion_item(rebal=None, abs_dev=None, rel_dev=None):
    return dbc.AccordionItem(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Rebalancing period",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-rebalancing",
                                    ),
                                ]
                            ),
                            dcc.Dropdown(
                                options=[
                                    {"label": "Monthly", "value": "month"},
                                    {"label": "Quarterly", "value": "quarter"},
                                    {"label": "Half-year", "value": "half-year"},
                                    {"label": "Yearly", "value": "year"},
                                    {"label": "No rebalancing (buy & hold)", "value": "none"},
                                ],
                                value=rebal if rebal else "month",
                                multi=False,
                                clearable=False,
                                placeholder="Select a rebalancing period",
                                id="pf-rebalancing-period",
                            ),
                            dbc.Tooltip(
                                tl.pf_rebalancing_period,
                                target="pf-info-rebalancing",
                            ),
                        ],
                        lg=12,
                        md=12,
                        sm=12,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Absolute deviation",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-rebal-abs-dev",
                                    ),
                                ]
                            ),
                            dbc.Input(
                                id="pf-rebal-abs-deviation",
                                type="number",
                                min=0,
                                max=100,
                                step=1,
                                value=abs_dev,
                                placeholder="e.g. 5",
                            ),
                            dbc.FormText("0-100 (%)"),
                            dbc.Tooltip(
                                tl.pf_rebal_abs_deviation,
                                target="pf-info-rebal-abs-dev",
                            ),
                        ],
                        lg=6,
                        md=6,
                        sm=12,
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Relative deviation",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-rebal-rel-dev",
                                    ),
                                ]
                            ),
                            dbc.Input(
                                id="pf-rebal-rel-deviation",
                                type="number",
                                min=0,
                                step=1,
                                value=rel_dev,
                                placeholder="e.g. 10",
                            ),
                            dbc.FormText("0-100+ (%)"),
                            dbc.Tooltip(
                                tl.pf_rebal_rel_deviation,
                                target="pf-info-rebal-rel-dev",
                            ),
                        ],
                        lg=6,
                        md=6,
                        sm=12,
                    ),
                ],
                id="pf-rebal-deviation-row",
                class_name="mt-2",
            ),
        ],
        title="Rebalancing Strategy",
        item_id="rebalancing",
    )


@callback(
    Output("pf-rebal-deviation-row", "style"),
    Input("pf-rebalancing-period", "value"),
)
def toggle_deviation_controls(period):
    if period == "none":
        return {"display": "none"}
    return None
