import typing

import dash
import dash.exceptions
import dash_ag_grid as dag
import plotly
from dash import State, callback, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import pandas as pd

import plotly.express as px

import okama as ok

import common.settings as settings
from common.object_cache import get_or_create, TTL_ASSET_LIST
import common.update_style
from common.chart_helpers import (
    add_inflation_trace,
    add_crisis_rectangles,
    add_last_value_annotations,
    add_sharpe_ratio_row,
    add_return_type_subtitle,
    format_points,
    make_error_alert,
)
from common.url_portfolio import (
    get_or_create_url_portfolio,
    parse_url_portfolio_group,
    pf_cache_token,
    split_portfolio_from_selection,
)
import plotly.graph_objects as go

from common.html_elements.submit_spinner import submit_spinner_running
from common.mobile_screens import adopt_small_screens
from pages.compare.cards_compare.asset_list_controls import card_controls
from pages.compare.cards_compare.assets_info import card_assets_info
from pages.compare.cards_compare.compare_description import card_compare_description
from pages.compare.cards_compare.statistics_table import card_table
from pages.compare.cards_compare.wealth_indexes_chart import card_graf_compare

dash.register_page(
    __name__,
    path="/compare",
    title="Compare financial assets : okama",
    name="Compare assets",
    description="""Okama.io widget to compare financial assets properties:
                rate of return, risk, CVAR, drawdowns, correlation""",
)


def layout(
    tickers=None,
    first_date=None,
    last_date=None,
    ccy=None,
    pf_tickers=None,
    pf_weights=None,
    pf_rebal=None,
    pf_symbol=None,
    pf_abs_dev=None,
    pf_rel_dev=None,
    **kwargs,
):
    # Portfolio handed off from the Portfolio page via URL (issue #23);
    # None for ordinary links without a pf_* group.
    pf_def = parse_url_portfolio_group(pf_tickers, pf_weights, pf_rebal, pf_symbol, pf_abs_dev, pf_rel_dev)
    page = dbc.Container(
        [
            dcc.Store(id="al-url-portfolio", data=pf_def),
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers, first_date, last_date, ccy, pf_def), lg=7),
                    dbc.Col(card_assets_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf_compare, width=12), align="center", style={"display": "none"}, id="al-graf-row"),
            dbc.Row(
                dbc.Col(card_table, width=12), align="center", style={"display": "none"}, id="al-statistics-table-row"
            ),
            dbc.Row(dbc.Col(card_compare_description, width=12), align="left"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="al-wealth-indexes", component_property="figure"),
    Output(component_id="al-wealth-indexes", component_property="config"),
    Output(component_id="al-describe-table", component_property="children"),
    Output(component_id="al-store-chart-data", component_property="data"),
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(component_id="al-submit-button", component_property="n_clicks"),
    # Logarithmic scale button
    Input(component_id="logarithmic-scale-switch", component_property="on"),
    State(component_id="al-symbols-list", component_property="value"),
    State(component_id="al-base-currency", component_property="value"),
    State(component_id="al-first-date", component_property="value"),
    State(component_id="al-last-date", component_property="value"),
    # Options
    State(component_id="al-plot-option", component_property="value"),
    State(component_id="al-inflation-switch", component_property="value"),
    State(component_id="al-rolling-window", component_property="value"),
    State(component_id="al-url-portfolio", component_property="data"),
    # Show the spinner under the Compare button while computing (the chart's
    # own dcc.Loading spinner is below the fold on mobile).
    running=submit_spinner_running("al-submit-spinner"),
    prevent_initial_call=True,
)
def update_graf_compare(
    screen,
    n_clicks,
    log_on: bool,
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    pf_def: dict | None,
):
    trigger = dash.ctx.triggered_id
    if trigger == "logarithmic-scale-switch":
        patched_fig = dash.Patch()
        patched_fig["layout"]["yaxis"]["type"] = "log" if log_on else "linear"
        return (
            patched_fig,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    if not selected_symbols:
        raise dash.exceptions.PreventUpdate
    try:
        return _update_graf_compare_inner(
            screen, log_on, selected_symbols, ccy, fd_value, ld_value, plot_type, inflation_on, rolling_window, pf_def
        )
    except Exception as e:
        alert = make_error_alert(e)
        return go.Figure(), {}, alert, None


def _update_graf_compare_inner(
    screen, log_on, selected_symbols, ccy, fd_value, ld_value, plot_type, inflation_on, rolling_window, pf_def=None
):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    tickers, has_pf = split_portfolio_from_selection(symbols, pf_def)
    assets: list = list(tickers)
    if has_pf:
        # Cached ok.Portfolio from the URL handoff joins the AssetList as an asset.
        assets = [get_or_create_url_portfolio(pf_def, ccy=ccy, first_date=fd_value, last_date=ld_value)] + assets
    al_object, _ = get_or_create(
        obj_type="assetlist",
        constructor_fn=lambda: ok.AssetList(
            assets,
            first_date=fd_value,
            last_date=ld_value,
            ccy=ccy,
            inflation=inflation_on,
        ),
        cache_key_params={
            "symbols": tickers,
            "ccy": ccy,
            "first_date": fd_value,
            "last_date": ld_value,
            "inflation": inflation_on,
            # An AssetList with the URL portfolio must not share a cache slot
            # with the plain one for the same tickers.
            "pf": pf_cache_token(pf_def) if has_pf else None,
        },
        ttl_seconds=TTL_ASSET_LIST,
    )
    log_scale = log_on if plot_type in ("wealth", "cumulative_return") else False
    fig, df_data = get_al_figure(al_object, plot_type, inflation_on, rolling_window, log_scale)
    json_data = df_data.to_json(orient="split", default_handler=str)
    if plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Index")
    elif plot_type == "cumulative_return":
        fig.update_yaxes(title_text="Cumulative Return")
    elif plot_type == "annual_return":
        fig.update_yaxes(title_text="Annual Return, %")
    elif plot_type in ("cagr", "real_cagr"):
        fig.update_yaxes(title_text="CAGR")

    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    if plot_type == "correlation":
        fig.update(layout_showlegend=False)
        fig.update(layout_coloraxis_showscale=False)
        fig.update_xaxes(side="top")
        # Heatmap tick labels are ticker names: keep them outside the plot
        # (mobile mode moves y ticks inside, which would overlay the cells).
        fig.update_yaxes(ticklabelposition="outside")
    fig.update_xaxes(
        # ticks='outside',
        rangeslider_visible=plot_type not in ("correlation", "annual_return"),
        showgrid=False,
        gridcolor="lightgrey",
        zeroline=False,
        zerolinewidth=2,
        zerolinecolor="black",
    )
    fig.update_yaxes(
        # ticks='outside',
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=1,
        showgrid=False,
        gridcolor="lightgrey",
    )
    # Asset List describe() risk-return statistics
    statistics_ag_grid = get_al_statistics_table(al_object)
    return fig, config, statistics_ag_grid, json_data


def get_al_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-4, :]  # crop from Max drawdown date
    statistics_df = add_sharpe_ratio_row(al_object, statistics_df)

    # Build columnDefs with percent formatting for all numeric columns
    # Preserves existing quirk: all numeric values (including Sharpe) get percent formatting.
    # The guard lives in assets/dashAgGridFunctions.js — inline typeof-guards are
    # silently rejected by the dash-ag-grid function-string parser.
    column_defs = [
        {"field": col, "headerName": col, "valueFormatter": {"function": "formatPercentGuarded(params.value)"}}
        for col in statistics_df.columns
    ]

    return dag.AgGrid(
        id="al-describe-table-grid",
        rowData=statistics_df.to_dict("records"),
        columnDefs=column_defs,
        defaultColDef={"resizable": False, "sortable": False},
        columnSize="responsiveSizeToFit",
        # suppressFieldDotNotation: ticker column names contain dots (AAPL.US);
        # without it AG Grid resolves them as nested paths and renders empty cells.
        dashGridOptions={"domLayout": "autoHeight", "suppressFieldDotNotation": True},
        style={"height": None},
    )


def get_al_figure(
    al_object: ok.AssetList, plot_type: str, inflation_on: bool, rolling_window: int, log_scale: bool
) -> typing.Tuple[plotly.graph_objects.Figure, pd.DataFrame]:
    titles = {
        "wealth": "Assets Wealth indexes",
        "cumulative_return": "Assets Cumulative return",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
        "annual_return": "Assets Annual Return",
        "correlation": "Correlation Matrix",
    }

    # Select Plot Type
    if plot_type == "annual_return":
        df = al_object.annual_return_ts * 100
        ind = df.index.to_timestamp(freq="Y")
        fig = px.bar(df, x=ind, y=df.columns, barmode="group", title=titles[plot_type], height=800)
        fig.update_xaxes(dtick="M12", tickformat="%Y", ticklabelmode="instant")
        fig.update_layout(xaxis_title=None, legend_title="Assets")
        add_return_type_subtitle(fig)
        return fig, df
    if plot_type == "wealth":
        df = al_object.wealth_indexes
        return_series = None  # annotations show the final index value in points
    elif plot_type == "cumulative_return":
        df = al_object.get_cumulative_return(real=False)
        return_series = df.iloc[-1]
    elif plot_type in ("cagr", "real_cagr"):
        real = False if plot_type == "cagr" else True
        df = al_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
        return_series = df.iloc[-1, :]
    elif plot_type == "correlation":
        matrix = al_object.assets_ror.corr()
        matrix = matrix.map("{:,.2f}".format)
        fig = px.imshow(matrix, text_auto=True, aspect="equal", labels={"x": "", "y": "", "color": ""})
        return fig, matrix

    ind = df.index.to_timestamp("D")
    chart_first_date = ind[0]
    chart_last_date = ind[-1]

    annotations_xy = [(ind[-1], y) for y in df.iloc[-1].to_numpy()]
    if plot_type == "wealth":
        # Wealth chart labels show the final index value in points, not a return percent.
        annotations_text = list(df.iloc[-1].map(format_points))
    else:
        annotations_text = list((return_series * 100).map("{:,.2f}%".format))

    # inflation must not be in the chart for "Real CAGR"
    plot_inflation_condition = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if plot_inflation_condition else df.columns,
        log_y=log_scale if plot_type == "wealth" else False,
        title=titles[plot_type],
        # width=800,
        height=800,
    )
    if plot_inflation_condition:
        add_inflation_trace(fig, ind, df)
    add_crisis_rectangles(fig, chart_first_date, chart_last_date)
    fig.update_layout(
        xaxis_title=None,
        legend_title="Assets",
    )
    add_last_value_annotations(fig, annotations_xy, annotations_text)

    return fig, df


@callback(
    Output(component_id="al-graf-row", component_property="style"),
    Output(component_id="al-statistics-table-row", component_property="style"),
    Input(component_id="al-submit-button", component_property="n_clicks"),
    State(component_id="al-graf-row", component_property="style"),
)
def show_graf_and_statistics_table_rows(n_clicks, style):
    style = common.update_style.change_style_for_hidden_row(n_clicks, style)
    return style, style


@callback(
    Output("al-statistics-download", "data"),
    Input("al-statistics-export-btn", "n_clicks"),
    State("al-describe-table-grid", "rowData"),
    prevent_initial_call=True,
)
def export_statistics_xlsx(n_clicks, row_data):
    from common.html_elements.grid_export import percent_column_formats, rowdata_to_xlsx_download

    return rowdata_to_xlsx_download(
        n_clicks, row_data, "compare_statistics.xlsx", column_formats=percent_column_formats(row_data)
    )
