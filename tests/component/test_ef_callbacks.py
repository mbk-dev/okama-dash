import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.component


class TestNormalizePlotTypes:
    def test_none_returns_empty(self):
        from pages.efficient_frontier.prepare_ef_plot import _normalize_plot_types

        assert _normalize_plot_types(None) == []

    def test_string_returns_single_list(self):
        from pages.efficient_frontier.prepare_ef_plot import _normalize_plot_types

        assert _normalize_plot_types("ef") == ["ef"]

    def test_list_preserved(self):
        from pages.efficient_frontier.prepare_ef_plot import _normalize_plot_types

        assert _normalize_plot_types(["ef", "monte_carlo"]) == ["ef", "monte_carlo"]

    def test_duplicates_removed(self):
        from pages.efficient_frontier.prepare_ef_plot import _normalize_plot_types

        assert _normalize_plot_types(["ef", "ef", "monte_carlo"]) == ["ef", "monte_carlo"]

    def test_empty_list(self):
        from pages.efficient_frontier.prepare_ef_plot import _normalize_plot_types

        assert _normalize_plot_types([]) == []


class TestResolveReturnColumn:
    def test_arithmetic_prefers_mean_return(self):
        from pages.efficient_frontier.prepare_ef_plot import _resolve_return_column

        df = pd.DataFrame({"Mean return": [0.1], "CAGR": [0.08], "Risk": [0.12]})
        assert _resolve_return_column(df, "Arithmetic") == "Mean return"

    def test_geometric_prefers_cagr(self):
        from pages.efficient_frontier.prepare_ef_plot import _resolve_return_column

        df = pd.DataFrame({"Mean return": [0.1], "CAGR": [0.08], "Risk": [0.12]})
        assert _resolve_return_column(df, "Geometric") == "CAGR"

    def test_arithmetic_falls_back_to_return(self):
        from pages.efficient_frontier.prepare_ef_plot import _resolve_return_column

        df = pd.DataFrame({"Return": [0.1], "Risk": [0.12]})
        assert _resolve_return_column(df, "Arithmetic") == "Return"

    def test_geometric_falls_back_to_return(self):
        from pages.efficient_frontier.prepare_ef_plot import _resolve_return_column

        df = pd.DataFrame({"Return": [0.1], "Risk": [0.12]})
        assert _resolve_return_column(df, "Geometric") == "Return"

    def test_raises_if_no_return_column(self):
        from pages.efficient_frontier.prepare_ef_plot import _resolve_return_column

        df = pd.DataFrame({"Risk": [0.12], "Weights": [0.5]})
        with pytest.raises(KeyError, match="No return column"):
            _resolve_return_column(df, "Arithmetic")


class TestGetPortfolioWeightsPercent:
    def test_from_weights_key(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_portfolio_weights_percent

        portfolio = {"Weights": [0.4, 0.6]}
        result = _get_portfolio_weights_percent(portfolio, ["A", "B"])
        np.testing.assert_array_almost_equal(result, [40.0, 60.0])

    def test_from_symbol_keys(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_portfolio_weights_percent

        portfolio = {"AAPL.US": 0.5, "MSFT.US": 0.5}
        result = _get_portfolio_weights_percent(portfolio, ["AAPL.US", "MSFT.US"])
        np.testing.assert_array_almost_equal(result, [50.0, 50.0])

    def test_returns_none_if_missing(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_portfolio_weights_percent

        portfolio = {"Risk": 0.1}
        assert _get_portfolio_weights_percent(portfolio, ["AAPL.US"]) is None


class TestExpandWeightsToFullUniverse:
    def test_expands_correctly(self):
        from pages.efficient_frontier.prepare_ef_plot import _expand_weights_to_full_universe

        weights = np.array([[40.0, 60.0], [30.0, 70.0]])
        asset_columns = ["A", "C"]
        all_symbols = ["A", "B", "C"]
        result = _expand_weights_to_full_universe(weights, asset_columns, all_symbols)
        expected = np.array([[40.0, 0.0, 60.0], [30.0, 0.0, 70.0]])
        np.testing.assert_array_equal(result, expected)

    def test_same_universe_identity(self):
        from pages.efficient_frontier.prepare_ef_plot import _expand_weights_to_full_universe

        weights = np.array([[50.0, 50.0]])
        result = _expand_weights_to_full_universe(weights, ["A", "B"], ["A", "B"])
        np.testing.assert_array_equal(result, weights)

    def test_unknown_symbols_zero_filled(self):
        from pages.efficient_frontier.prepare_ef_plot import _expand_weights_to_full_universe

        weights = np.array([[100.0]])
        result = _expand_weights_to_full_universe(weights, ["A"], ["X", "Y", "A"])
        expected = np.array([[0.0, 0.0, 100.0]])
        np.testing.assert_array_equal(result, expected)


class TestGetColumnValues:
    def test_first_candidate_matched(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_column_values

        df = pd.DataFrame({"Mean return": [0.1, 0.2], "CAGR": [0.08, 0.15]})
        assert _get_column_values(df, ("Mean return", "CAGR")) == [0.1, 0.2]

    def test_fallback_candidate(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_column_values

        df = pd.DataFrame({"CAGR": [0.08, 0.15], "Risk": [0.1, 0.2]})
        assert _get_column_values(df, ("Mean return", "CAGR")) == [0.08, 0.15]

    def test_raises_if_none_found(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_column_values

        df = pd.DataFrame({"Risk": [0.1]})
        with pytest.raises(KeyError):
            _get_column_values(df, ("Mean return", "CAGR"))


class TestGetCachedReturnValues:
    def test_arithmetic(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_cached_return_values

        payload = {"mean_return": [1, 2, 3], "cagr": [4, 5, 6]}
        assert _get_cached_return_values(payload, "Arithmetic") == [1, 2, 3]

    def test_geometric(self):
        from pages.efficient_frontier.prepare_ef_plot import _get_cached_return_values

        payload = {"mean_return": [1, 2, 3], "cagr": [4, 5, 6]}
        assert _get_cached_return_values(payload, "Geometric") == [4, 5, 6]


class TestEFShowHideCallbacks:
    def test_show_backtest_button_visible_when_text(self):
        from pages.efficient_frontier.frontier import show_backtest_portfolio_button_row

        assert show_backtest_portfolio_button_row("Risk: 10%") is None

    def test_show_backtest_button_hidden_when_empty(self):
        from pages.efficient_frontier.frontier import show_backtest_portfolio_button_row

        assert show_backtest_portfolio_button_row("") == {"display": "none"}

    def test_show_backtest_button_hidden_when_none(self):
        from pages.efficient_frontier.frontier import show_backtest_portfolio_button_row

        assert show_backtest_portfolio_button_row(None) == {"display": "none"}

    def test_transition_map_on(self):
        from pages.efficient_frontier.frontier import show_transition_map_row

        assert show_transition_map_row(1, {"display": "none"}, "On") is None

    def test_transition_map_off(self):
        from pages.efficient_frontier.frontier import show_transition_map_row

        assert show_transition_map_row(1, None, "Off") == {"display": "none"}
