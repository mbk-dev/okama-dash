"""Page-level tests for /macro/real-estate: reactive main callback, ccy/plot
modes, trim wiring, prefill, link/export/copy-link guards."""

from unittest.mock import patch

import dash
import plotly.graph_objects as go
import pytest

from tests.mocks.okama_mock import PicklableAsset, PicklableAssetList

pytestmark = pytest.mark.component


@pytest.fixture
def re_page():
    from pages.macro import real_estate

    return real_estate


@pytest.fixture
def patched_assets(re_page):
    with (
        patch.object(re_page.macro_objects, "get_asset_object", side_effect=lambda s: PicklableAsset(s)),
        patch.object(
            re_page.macro_objects,
            "get_asset_list_object",
            # Keyword names must match the real accessor: the page calls it
            # with ccy=/first_date=/last_date=/inflation= keywords.
            side_effect=lambda symbols, ccy, first_date=None, last_date=None, inflation=False: PicklableAssetList(
                symbols, ccy=ccy, inflation=inflation
            ),
        ),
    ):
        yield


class TestMainCallback:
    def test_price_mode_rub(self, re_page, patched_assets):
        fig, config, store, grid = re_page.update_re_page(None, ["MOW_PR.RE", "MOW_SEC.RE"], "price", "RUB", None, None)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert "RUB" in fig.layout.yaxis.title.text
        assert grid.id == "re-describe-table-grid"

    def test_main_callback_emits_chart_store(self, re_page, patched_assets):
        fig, config, store, grid = re_page.update_re_page(None, ["MOW_PR.RE"], "price", "RUB", None, None)
        assert isinstance(store, str) and "columns" in store

    def test_price_mode_usd_converts(self, re_page, patched_assets):
        fig_rub, *_ = re_page.update_re_page(None, ["MOW_PR.RE"], "price", "RUB", None, None)
        fig_usd, *_ = re_page.update_re_page(None, ["MOW_PR.RE"], "price", "USD", None, None)
        assert max(fig_usd.data[0].y) < max(fig_rub.data[0].y)  # mock divides by 80

    def test_wealth_mode_includes_inflation_line(self, re_page, patched_assets):
        fig, *_ = re_page.update_re_page(None, ["MOW_PR.RE"], "wealth", "RUB", None, None)
        assert {t.name for t in fig.data} == {"Moscow primary market", "RUB.INFL"}

    def test_date_range_masks_price_series(self, re_page, patched_assets):
        fig, *_ = re_page.update_re_page(None, ["MOW_PR.RE"], "price", "RUB", "2022-01", "2022-12")
        xs = fig.data[0].x
        assert str(min(xs))[:7] == "2022-01"
        assert str(max(xs))[:7] == "2022-12"

    def test_empty_selection_prevents_update(self, re_page):
        with pytest.raises(dash.exceptions.PreventUpdate):
            re_page.update_re_page(None, [], "price", "RUB", None, None)

    def test_half_typed_date_prevents_update(self, re_page, patched_assets):
        with pytest.raises(dash.exceptions.PreventUpdate):
            re_page.update_re_page(None, ["MOW_PR.RE"], "price", "RUB", "20", None)

    def test_error_renders_annotation(self, re_page):
        with patch.object(re_page.macro_objects, "get_asset_object", side_effect=ValueError("api down")):
            fig, config, store, grid = re_page.update_re_page(None, ["MOW_PR.RE"], "price", "RUB", None, None)
        assert fig.layout.annotations[0].text == "api down"
        assert grid is None


class TestStatsGridSerialization:
    """Regression for the /macro/real-estate 500 (GitHub #30).

    okama's real ``AssetList.describe()`` carries a ``Max drawdowns dates`` row
    whose per-asset cells are pandas ``Period`` objects. The page crops only the
    three inception/last-date rows by name, so that ``Period`` reaches the AG Grid
    ``rowData`` and Dash fails to JSON-serialize the callback return with
    ``TypeError: Object of type Period is not JSON serializable``. The shared mock
    uses numeric drawdown-date columns, so it never reproduced this — hence a
    local describe() frame that mirrors the real okama shape.
    """

    @staticmethod
    def _describe_with_period_dates(symbols):
        import pandas as pd

        data = {
            "property": [
                "CAGR",
                "Risk",
                "CVAR",
                "Max drawdowns",
                "Max drawdowns dates",
                "Inception date",
                "Last asset date",
                "Common last data date",
            ],
            "period": ["5 years"] * 5 + [pd.NA] * 3,
        }
        for symbol in symbols:
            data[symbol] = [
                0.10,
                0.05,
                -0.15,
                -0.20,
                pd.Period("2023-03", freq="M"),  # the offending cell
                pd.Period("2000-04", freq="M"),
                pd.Period("2026-03", freq="M"),
                pd.Period("2026-03", freq="M"),
            ]
        return pd.DataFrame(data)

    @pytest.fixture
    def patched_period_describe(self, re_page):
        class _DescribeOnlyAL:
            def __init__(self, symbols):
                self._symbols = symbols

            def describe(self):
                return TestStatsGridSerialization._describe_with_period_dates(self._symbols)

        with (
            patch.object(re_page.macro_objects, "get_asset_object", side_effect=lambda s: PicklableAsset(s)),
            patch.object(
                re_page.macro_objects,
                "get_asset_list_object",
                side_effect=lambda symbols, ccy, first_date=None, last_date=None, inflation=False: _DescribeOnlyAL(
                    symbols
                ),
            ),
        ):
            yield

    def test_stats_grid_rowdata_is_json_serializable(self, re_page, patched_period_describe):
        import json

        _fig, _config, _store, grid = re_page.update_re_page(
            None, ["MOW_PR.RE", "MOW_SEC.RE"], "price", "RUB", None, None
        )
        # This is exactly what Dash does with the callback return value; before
        # the fix it raises "Object of type Period is not JSON serializable".
        json.dumps(grid.rowData)

    def test_stats_grid_drops_max_drawdown_dates_row(self, re_page, patched_period_describe):
        _fig, _config, _store, grid = re_page.update_re_page(
            None, ["MOW_PR.RE", "MOW_SEC.RE"], "price", "RUB", None, None
        )
        properties = {row["property"] for row in grid.rowData}
        # Cropped by name like Compare's describe().iloc[:-4] "crop from Max drawdown date".
        assert "Max drawdowns dates" not in properties


class TestReactiveWiring:
    def test_every_control_is_an_input(self, re_page):
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "re-chart.figure" in str(s["output"]))
        inputs = str(spec["inputs"])
        for control in ("re-series", "re-plot-type", "re-ccy", "re-first-date", "re-last-date"):
            assert control in inputs
        assert "submit" not in inputs
        assert not spec["state"]
        assert not spec["prevent_initial_call"]


class TestLayoutAndLink:
    def test_defaults_and_prefill(self, re_page, mock_okama_symbols, null_cache):
        from pages.macro.macro_data import RE_DEFAULTS

        assert _find_by_id(re_page.layout(), "re-series").value == RE_DEFAULTS
        page = re_page.layout(tickers="RUS_PR.RE", plot="wealth", ccy="usd")
        assert _find_by_id(page, "re-series").value == ["RUS_PR.RE"]
        assert _find_by_id(page, "re-plot-type").value == "wealth"
        assert _find_by_id(page, "re-ccy").value == "USD"  # case-normalized
        page_bad = re_page.layout(ccy="GBP")
        assert _find_by_id(page_bad, "re-ccy").value == "RUB"  # unknown -> default

    def test_link_callback(self, re_page):
        link = re_page.update_re_link(1, "http://x/macro/real-estate", ["MOW_PR.RE"], "wealth", "USD", None, None)
        assert "plot=wealth" in link
        assert "ccy=USD" in link
        link_default = re_page.update_re_link(
            1, "http://x/macro/real-estate", ["MOW_PR.RE"], "price", "RUB", None, None
        )
        assert "plot=" not in link_default and "ccy=" not in link_default

    def test_export_guard(self, re_page):
        with pytest.raises(dash.exceptions.PreventUpdate):
            re_page.export_re_stats(None, [{"property": "x"}])

    def test_empty_selection_disables_copy_link(self, re_page):
        assert re_page.disable_copy_link_re([]) is True
        assert re_page.disable_copy_link_re(["MOW_PR.RE"]) is False


def _find_by_id(component, component_id):
    stack = [component]
    while stack:
        node = stack.pop()
        if getattr(node, "id", None) == component_id:
            return node
        children = getattr(node, "children", None)
        children = children if isinstance(children, list) else [children] if children is not None else []
        stack.extend(children)
    raise AssertionError(f"id {component_id} not found")
