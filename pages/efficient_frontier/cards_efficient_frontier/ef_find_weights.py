import numbers

import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State

import common.update_style


find_weights_description = "Find optimized portfolio weights for a given return (annual value, arithmetic mean)."


card_ef_find_weights = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Find portfolio weights"),
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Label(find_weights_description),
                                        lg=4,
                                        md=4,
                                        sm=12,
                                    ),
                                    dbc.Col(
                                        # html.Label("Namespace"),
                                        lg=8,
                                        md=8,
                                        sm=12,
                                    ),
                                ]
                            ),
                            html.Div(
                                children=[
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Input(
                                                    id="ef-find-portfolio-input",
                                                    placeholder="Rate of return (Format XX.XX)",
                                                    type="number",
                                                ),
                                                lg=4,
                                                md=4,
                                                sm=12,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Div(
                                                        [
                                                            html.P(id="ef-find-portfolio-info-return-range"),
                                                        ],
                                                        id="ef-optimized-find-portfolio-info",
                                                        style={'display': 'inline-block', 'verticalAlign': 'middle'}
                                                    )
                                                ],
                                                lg=8,
                                                md=8,
                                                sm=12,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [dbc.Button(
                                                "Find portfolio",
                                                id="ef-find-portfolio-button",
                                                n_clicks=0,
                                                color="primary"
                                            )],
                                            style={"text-align": "center"},
                                            className="p-3",
                                        )
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                                [
                                                    html.H5("Optimized portfolio data"),
                                                    html.Div(
                                                        [
                                                            html.P(id="ef-find-portfolio-mean-return"),
                                                            html.P(id="ef-find-portfolio-cagr"),
                                                            html.P(id="ef-find-portfolio-risk"),
                                                            html.Pre(id="ef-find-portfolio-weights"),
                                                        ],
                                                    )
                                                ]
                                    )
                                ],
                                style={"display": "none"},
                                id="ef-find-portfolio-output-row",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [dbc.Button(
                                                "Backtest portfolio",
                                                id="ef-backtest-optimized-potfolio-button",
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
                        ],
                    ),
                ]
            ),
            dcc.Store(id="ef_portfolio_file_name"),
        ]
    ),
    class_name="mb-3",
)


@callback(
    Output("ef-find-portfolio-button", "disabled"),
    Input("ef-find-portfolio-input", "value"),
)
def disable_find_portfolio(ror_input) -> bool:
    """
    Disable Find portfolio button.

    conditions:
    - ROR number is incorrect
    """
    if ror_input is not None:
        ror_input_valid = isinstance(ror_input, numbers.Number)
        return not ror_input_valid
    return True


@callback(
    Output(component_id="ef-find-portfolio-output-row", component_property="style"),
    Output(component_id="ef-backtest-optimized-potfolio-button-row", component_property="style"),
    Input(component_id="ef-find-portfolio-button", component_property="n_clicks"),
    State(component_id="ef-find-portfolio-output-row", component_property="style"),
)
def show_find_portfolio_output_row(n_clicks, style):
    style = common.update_style.change_style_for_hidden_row(n_clicks, style)
    return style, style
