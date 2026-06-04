import os

if os.environ.get("TESTING") == "1":
    from unittest.mock import MagicMock

    import pandas as pd
    import okama as _ok
    from tests.mocks.okama_mock import (
        get_mock_namespaces,
        mock_symbols_in_namespace,
        PicklableAssetList,
        PicklablePortfolio,
        _CashflowParameters,
        _RebalanceStrategy,
    )

    _ok.assets_namespaces = get_mock_namespaces()
    _ok.namespaces = {ns: f"Mock {ns} namespace" for ns in get_mock_namespaces()}
    _ok.symbols_in_namespace = mock_symbols_in_namespace
    _ok.search = MagicMock(return_value=pd.DataFrame({"symbol": [], "name": []}))
    _ok.Portfolio = lambda *a, **kw: PicklablePortfolio()
    _ok.Rebalance = lambda *a, **kw: _RebalanceStrategy(**{k: v for k, v in kw.items() if k == "period"})
    _ok.AssetList = PicklableAssetList
    _ok.IndexationStrategy = lambda pf, *a, **kw: _CashflowParameters()
    _ok.PercentageStrategy = lambda pf, *a, **kw: _CashflowParameters()
    _ok.VanguardDynamicSpending = lambda *a, **kw: _CashflowParameters()
    _ok.CutWithdrawalsIfDrawdown = lambda *a, **kw: _CashflowParameters()
    _ok.TimeSeriesStrategy = lambda pf, *a, **kw: _CashflowParameters()

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import plotly.io as pio

import navigation
import footer

pio.templates.default = "plotly_white"

app = dash.Dash(
    __name__,
    use_pages=True,
    update_title="Loading okama ...",
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    # Required: pages create components dynamically (grids, export buttons/downloads,
    # constructor rows), so callbacks legitimately reference ids absent at load time.
    suppress_callback_exceptions=True,
)
server = app.server

import common  # noqa: E402 — must be after TESTING block patches okama
common.cache.init_app(server)  # centralised; previously called per-controls-file

app.layout = html.Div([dcc.Store(id="store"), navigation.navbar, dash.page_container, footer.footer()])

app.clientside_callback(
    """
    function(trigger) {
        //  can use any prop to trigger this callback - we just want to store the info on startup
        const inner_width  = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
        const inner_height = window.innerHeight|| document.documentElement.clientHeight|| document.body.clientHeight;
        const screenInfo = {height :screen.height, width: screen.width, in_width: inner_width, in_height: inner_height};

        return screenInfo
    }
    """,
    Output("store", "data"),
    Input("store", "data"),
)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
