import warnings

import dash
import dash.exceptions
from dash import dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import okama as ok

import common.settings as settings
from common.mobile_screens import adopt_small_screens
from pages.compare.cards_compare.asset_list_controls import card_controls
from pages.compare.cards_compare.assets_info import card_assets_info
from pages.compare.cards_compare.compare_description import card_compare_description
from pages.compare.cards_compare.statistics_table import card_table
from pages.compare.cards_compare.wealth_indexes_chart import card_graf_compare
import common.crisis.crisis_data as cr

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path="/compare",
    title="Compare financial assets : okama",
    name="Compare assets",
    description="""Okama widget to compare financial assets properties: 
                rate of return, risk, CVAR, drawdowns, correlation""",
)


def layout(tickers=None, first_date=None, last_date=None, ccy=None, **kwargs):
    page = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers, first_date, last_date, ccy), lg=7),
                    dbc.Col(card_assets_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf_compare, width=12), align="center"),
            dbc.Row(dbc.Col(card_table, width=12), align="center"),
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
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(component_id="al-submit-button", component_property="n_clicks"),
    State(component_id="al-symbols-list", component_property="value"),
    State(component_id="al-base-currency", component_property="value"),
    State(component_id="al-first-date", component_property="value"),
    State(component_id="al-last-date", component_property="value"),
    # Options
    State(component_id="al-plot-option", component_property="value"),
    State(component_id="al-inflation-switch", component_property="value"),
    State(component_id="al-rolling-window", component_property="value"),
    # Logarithmic scale button
    Input(component_id="logarithmic-scale-switch", component_property="on"),
    prevent_initial_call=True,
)
def update_graf_compare(
    screen,
    n_clicks,
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    # Log scale
    log_on: bool,
):
    if not selected_symbols:
        raise dash.exceptions.PreventUpdate
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    al_object = ok.AssetList(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=inflation_on,
    )
    fig = get_al_figure(al_object, plot_type, inflation_on, rolling_window, log_on)
    if plot_type == "correlation":
        fig.update(layout_showlegend=False)
        fig.update(layout_coloraxis_showscale=False)
        fig.update_xaxes(side="top")
    elif plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Index")
    else:
        fig.update_yaxes(title_text="CAGR")

    # Change layout for mobile screens (except correlation matrix)
    fig, config = adopt_small_screens(fig, screen)
    fig.update_xaxes(
        # ticks='outside',
        rangeslider_visible=True,
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
    statistics_dash_table = get_al_statistics_table(al_object)
    return fig, config, statistics_dash_table


def get_al_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-4, :]
    # statistics_df = al_object.describe()
    # statistics_df.iloc[-4:, :] = statistics_df.iloc[-4:, :].applymap(str)
    statistics_dict = statistics_df.to_dict(orient="records")

    columns = [
        dict(id=i, name=i, type="numeric", format=dash_table.FormatTemplate.percentage(2))
        for i in statistics_df.columns
    ]
    return dash_table.DataTable(
        data=statistics_dict,
        columns=columns,
        style_table={"overflowX": "auto"},
    )


def get_al_figure(al_object: ok.AssetList, plot_type: str, inflation_on: bool, rolling_window: int, log_scale: bool):
    titles = {
        "wealth": "Assets Wealth indexes",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
        "correlation": "Correlation Matrix",
    }

    # Select Plot Type
    if plot_type == "wealth":
        df = al_object.wealth_indexes
        # TODO: calculate return_series got portfolio + assets
        return_series = al_object.get_cumulative_return(real=inflation_on)
    elif plot_type in ("cagr", "real_cagr"):
        real = False if plot_type == "cagr" else True
        df = al_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
        return_series = df.iloc[-1, :]
    elif plot_type == "correlation":
        matrix = al_object.assets_ror.corr()
        matrix = matrix.applymap("{:,.2f}".format)
        fig = px.imshow(matrix, text_auto=True, aspect="equal", labels=dict(x="", y="", color=""))
        return fig

    ind = df.index.to_timestamp("D")
    chart_first_date = ind[0]
    chart_last_date = ind[-1]

    annotations_xy = [(ind[-1], y) for y in df.iloc[-1].values]
    annotation_series = (return_series * 100).map("{:,.2f}%".format)
    annotations_text = [cum_return for cum_return in annotation_series]

    # inflation must not be in the chart for "Real CAGR"
    plot_inflation_condition = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if plot_inflation_condition else df.columns,
        log_y=log_scale,
        title=titles[plot_type],
        # width=800,
        height=800,
    )
    # Plot Inflation
    if plot_inflation_condition:
        fig.add_trace(
            go.Scatter(
                x=ind,
                y=df.iloc[:, -1],
                mode="none",
                fill="tozeroy",
                fillcolor="rgba(226,150,65,0.5)",
                name="Inflation",
            )
        )
    # Plot Financial crisis historical data (sample)
    for crisis in cr.crisis_list:
        if (chart_first_date < crisis.first_date_dt) and (chart_last_date > crisis.last_date_dt):
            fig.add_vrect(
                x0=crisis.first_date,
                x1=crisis.last_date,
                annotation_text=crisis.name,
                annotation=dict(align="left", valign="top", textangle=-90),
                fillcolor="red",
                opacity=0.25,
                line_width=0,
            )
    fig.update_layout(
        xaxis_title="Date",
        legend_title="Assets",
    )
    # plot annotations
    for point in zip(annotations_xy, annotations_text):
        fig.add_annotation(
            x=point[0][0],
            y=point[0][1],
            text=point[1],
            showarrow=False,
            xanchor="left",
            bgcolor="grey",
        )

    return fig
