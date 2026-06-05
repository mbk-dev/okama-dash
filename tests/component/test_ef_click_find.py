from datetime import date
from unittest.mock import MagicMock, patch

import pytest

import dash.exceptions

pytestmark = pytest.mark.component

FRONTIER_MODULE = "pages.efficient_frontier.frontier"


def _make_mock_ef_object(rebalancing_period: str = "month"):
    ef = MagicMock()
    ef.symbols = ["SPY.US", "BND.US"]
    ef.currency = "USD"
    ef.first_date = date(2020, 1, 1)
    ef.last_date = date(2024, 12, 1)
    # Mirrors the real okama contract: EfficientFrontier is built with
    # ok.Rebalance(period=...) exposed as .rebalancing_strategy.period.
    ef.rebalancing_strategy.period = rebalancing_period
    return ef


class TestDisplayClickData:
    def test_no_click_data_raises_prevent_update(self):
        from pages.efficient_frontier.frontier import display_click_data

        with pytest.raises(dash.exceptions.PreventUpdate):
            display_click_data(None, 1, ["SPY.US", "BND.US"], "file.pkl")

    def test_click_without_customdata_returns_unavailable(self):
        from pages.efficient_frontier.frontier import display_click_data

        click_data = {"points": [{"x": 12.34, "y": 8.56}]}
        risk, ret, weights, link = display_click_data(
            click_data, 1, ["SPY.US", "BND.US"], "file.pkl"
        )
        assert risk == "Risk: 12.34%"
        assert ret == "Return: 8.56%"
        assert weights == "Weights: unavailable for this point."
        assert link is None

    def test_click_with_weights_returns_formatted_data(self):
        from pages.efficient_frontier.frontier import display_click_data

        mock_ef = _make_mock_ef_object()
        click_data = {
            "points": [{"x": 10.00, "y": 7.50, "customdata": [60.0, 40.0]}]
        }

        with patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef):
            risk, ret, weights, link = display_click_data(
                click_data, 1, ["SPY.US", "BND.US"], "file.pkl"
            )

        assert risk == "Risk: 10.00%"
        assert ret == "Return: 7.50%"
        assert "SPY.US=60.00%" in weights
        assert "BND.US=40.00%" in weights
        assert link is not None
        assert "/portfolio/" in link
        assert "SPY.US" in link
        assert "BND.US" in link
        # ccy=USD is default, should be omitted
        assert "ccy=" not in link
        assert "first_date=2020-01" in link
        assert "last_date=2024-12" in link

    def test_link_contains_rounded_weights(self):
        from pages.efficient_frontier.frontier import display_click_data

        mock_ef = _make_mock_ef_object()
        click_data = {
            "points": [{"x": 15.0, "y": 9.0, "customdata": [33.333, 66.667]}]
        }

        with patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef):
            _, _, _, link = display_click_data(
                click_data, 1, ["SPY.US", "BND.US"], "file.pkl"
            )

        assert "weights=33.33,66.67" in link

    def test_backtest_link_carries_rebalancing_period(self):
        from pages.efficient_frontier.frontier import display_click_data

        mock_ef = _make_mock_ef_object(rebalancing_period="year")
        click_data = {
            "points": [{"x": 10.00, "y": 7.50, "customdata": [60.0, 40.0]}]
        }

        with patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef):
            _, _, _, link = display_click_data(
                click_data, 1, ["SPY.US", "BND.US"], "file.pkl"
            )

        assert "rebal=year" in link

    def test_backtest_link_omits_default_month_rebalancing(self):
        from pages.efficient_frontier.frontier import display_click_data

        mock_ef = _make_mock_ef_object(rebalancing_period="month")
        click_data = {
            "points": [{"x": 10.00, "y": 7.50, "customdata": [60.0, 40.0]}]
        }

        with patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef):
            _, _, _, link = display_click_data(
                click_data, 1, ["SPY.US", "BND.US"], "file.pkl"
            )

        assert "rebal=" not in link

    def test_backtest_link_omits_rebal_when_ef_object_lacks_strategy(self):
        # Cached EF pickles created before the rebalancing_strategy era (or with an
        # older okama lacking the kwarg) must not break the click handler.
        from pages.efficient_frontier.frontier import display_click_data

        mock_ef = _make_mock_ef_object()
        del mock_ef.rebalancing_strategy
        click_data = {
            "points": [{"x": 10.00, "y": 7.50, "customdata": [60.0, 40.0]}]
        }

        with patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef):
            _, _, _, link = display_click_data(
                click_data, 1, ["SPY.US", "BND.US"], "file.pkl"
            )

        assert link is not None
        assert "rebal=" not in link

    def test_three_asset_weights(self):
        from pages.efficient_frontier.frontier import display_click_data

        mock_ef = _make_mock_ef_object()
        mock_ef.symbols = ["SPY.US", "BND.US", "GLD.US"]
        click_data = {
            "points": [{"x": 11.0, "y": 8.0, "customdata": [50.0, 30.0, 20.0]}]
        }
        symbols = ["SPY.US", "BND.US", "GLD.US"]

        with patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef):
            _, _, weights, link = display_click_data(
                click_data, 1, symbols, "file.pkl"
            )

        assert "SPY.US=50.00%" in weights
        assert "BND.US=30.00%" in weights
        assert "GLD.US=20.00%" in weights
        assert link is not None


class TestFindPortfolio:
    def test_zero_clicks_raises_prevent_update(self):
        from pages.efficient_frontier.frontier import find_portfolio

        with pytest.raises(dash.exceptions.PreventUpdate):
            find_portfolio(0, 8.0, "file.pkl")

    def test_none_file_name_raises_prevent_update(self):
        from pages.efficient_frontier.frontier import find_portfolio

        with pytest.raises(dash.exceptions.PreventUpdate):
            find_portfolio(1, 8.0, None)

    def test_optimized_portfolio_with_ticker_keys(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object()
        optimized = {
            "Mean return": 0.085,
            "CAGR": 0.08,
            "Risk": 0.12,
            "SPY.US": 0.6,
            "BND.US": 0.4,
        }

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(f"{FRONTIER_MODULE}.get_minimized_risk_portfolio", return_value=optimized),
        ):
            mean_ret, cagr, risk, weights, link = find_portfolio(1, 8.5, "file.pkl")

        assert mean_ret == "Mean return: 8.50%"
        assert cagr == "CAGR: 8.00%"
        assert risk == "Risk: 12.00%"
        assert "SPY.US=60.00%" in weights
        assert "BND.US=40.00%" in weights
        assert link is not None
        assert "/portfolio/" in link
        # ccy=USD is default, should be omitted
        assert "ccy=" not in link

    def test_optimized_portfolio_with_weights_list_key(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object()
        optimized = {
            "Mean return": 0.07,
            "CAGR": 0.065,
            "Risk": 0.10,
            "Weights": [0.55, 0.45],
        }

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(f"{FRONTIER_MODULE}.get_minimized_risk_portfolio", return_value=optimized),
        ):
            mean_ret, cagr, risk, weights, link = find_portfolio(1, 7.0, "file.pkl")

        assert mean_ret == "Mean return: 7.00%"
        assert "SPY.US=55.00%" in weights
        assert "BND.US=45.00%" in weights
        assert link is not None

    def test_no_solution_when_no_weights_in_result(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object()
        optimized = {
            "Mean return": 0.07,
            "CAGR": 0.065,
            "Risk": 0.10,
        }

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(f"{FRONTIER_MODULE}.get_minimized_risk_portfolio", return_value=optimized),
        ):
            _, _, _, weights, link = find_portfolio(1, 7.0, "file.pkl")

        assert weights == "No solution was found."
        assert link is None

    def test_recursion_error_returns_no_solution(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object()

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(
                f"{FRONTIER_MODULE}.get_minimized_risk_portfolio",
                side_effect=RecursionError,
            ),
        ):
            mean_ret, cagr, risk, weights, link = find_portfolio(1, 8.0, "file.pkl")

        assert mean_ret == ""
        assert cagr == ""
        assert risk == ""
        assert weights == "No solution was found."
        assert link is None

    def test_none_fields_produce_empty_strings(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object()
        optimized = {
            "SPY.US": 0.5,
            "BND.US": 0.5,
        }

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(f"{FRONTIER_MODULE}.get_minimized_risk_portfolio", return_value=optimized),
        ):
            mean_ret, cagr, risk, weights, link = find_portfolio(1, 8.0, "file.pkl")

        assert mean_ret == ""
        assert cagr == ""
        assert risk == ""
        assert "SPY.US=50.00%" in weights
        assert link is not None

    def test_backtest_link_carries_rebalancing_period(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object(rebalancing_period="quarter")
        optimized = {
            "Mean return": 0.085,
            "CAGR": 0.08,
            "Risk": 0.12,
            "SPY.US": 0.6,
            "BND.US": 0.4,
        }

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(f"{FRONTIER_MODULE}.get_minimized_risk_portfolio", return_value=optimized),
        ):
            _, _, _, _, link = find_portfolio(1, 8.5, "file.pkl")

        assert "rebal=quarter" in link

    def test_target_value_divided_by_100(self):
        from pages.efficient_frontier.frontier import find_portfolio

        mock_ef = _make_mock_ef_object()
        optimized = {
            "Mean return": 0.085,
            "CAGR": 0.08,
            "Risk": 0.12,
            "SPY.US": 0.6,
            "BND.US": 0.4,
        }

        with (
            patch(f"{FRONTIER_MODULE}.load_ef_object", return_value=mock_ef),
            patch(f"{FRONTIER_MODULE}.get_minimized_risk_portfolio", return_value=optimized) as mock_min,
        ):
            find_portfolio(1, 8.5, "file.pkl")

        mock_min.assert_called_once_with("file.pkl", 0.085)
