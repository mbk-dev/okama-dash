from unittest.mock import MagicMock, patch

import pytest
from dash.exceptions import PreventUpdate

pytestmark = pytest.mark.component


class TestToggleDeviationControls:
    def test_none_hides(self):
        from pages.portfolio.cards_portfolio.rebalancing_controls import toggle_deviation_controls

        assert toggle_deviation_controls("none") == {"display": "none"}

    def test_month_shows(self):
        from pages.portfolio.cards_portfolio.rebalancing_controls import toggle_deviation_controls

        assert toggle_deviation_controls("month") is None

    def test_quarter_shows(self):
        from pages.portfolio.cards_portfolio.rebalancing_controls import toggle_deviation_controls

        assert toggle_deviation_controls("quarter") is None

    def test_year_shows(self):
        from pages.portfolio.cards_portfolio.rebalancing_controls import toggle_deviation_controls

        assert toggle_deviation_controls("year") is None

    def test_half_year_shows(self):
        from pages.portfolio.cards_portfolio.rebalancing_controls import toggle_deviation_controls

        assert toggle_deviation_controls("half-year") is None


class TestGeneratePieChart:
    def test_equal_weights(self):
        from pages.portfolio.cards_portfolio.portfolio_info import generate_pie_chart

        screen = {"width": 1920, "height": 1080, "in_width": 1920, "in_height": 1080}
        fig, config = generate_pie_chart(["AAPL.US", "MSFT.US"], [50.0, 50.0], screen)
        assert fig is not None
        assert hasattr(fig, "data")

    def test_underweight_adds_not_allocated(self):
        from pages.portfolio.cards_portfolio.portfolio_info import generate_pie_chart

        screen = {"width": 1920, "height": 1080, "in_width": 1920, "in_height": 1080}
        fig, _ = generate_pie_chart(["AAPL.US"], [60.0], screen)
        labels = list(fig.data[0].labels)
        assert "Not Allocated" in labels

    def test_overweight_raises_prevent_update(self):
        from pages.portfolio.cards_portfolio.portfolio_info import generate_pie_chart

        screen = {"width": 1920, "height": 1080, "in_width": 1920, "in_height": 1080}
        with pytest.raises(PreventUpdate):
            generate_pie_chart(["AAPL.US", "MSFT.US"], [60.0, 50.0], screen)

    def test_exact_100_no_not_allocated(self):
        from pages.portfolio.cards_portfolio.portfolio_info import generate_pie_chart

        screen = {"width": 1920, "height": 1080, "in_width": 1920, "in_height": 1080}
        fig, _ = generate_pie_chart(["AAPL.US", "MSFT.US"], [50.0, 50.0], screen)
        labels = list(fig.data[0].labels)
        assert "Not Allocated" not in labels


class TestShowSurvivalStatistics:
    def test_hidden_when_no_monte_carlo(self):
        from pages.portfolio.cards_portfolio.portfolio_info import show_survival_periods_statistics_table

        assert show_survival_periods_statistics_table(1, "wealth", 0) is True

    def test_hidden_when_not_wealth(self):
        from pages.portfolio.cards_portfolio.portfolio_info import show_survival_periods_statistics_table

        assert show_survival_periods_statistics_table(1, "cagr", 100) is True

    def test_shown_when_wealth_with_monte_carlo(self):
        from pages.portfolio.cards_portfolio.portfolio_info import show_survival_periods_statistics_table

        assert show_survival_periods_statistics_table(1, "wealth", 100) is False

    def test_hidden_for_drawdowns(self):
        from pages.portfolio.cards_portfolio.portfolio_info import show_survival_periods_statistics_table

        assert show_survival_periods_statistics_table(1, "drawdowns", 100) is True

    def test_hidden_for_distribution(self):
        from pages.portfolio.cards_portfolio.portfolio_info import show_survival_periods_statistics_table

        assert show_survival_periods_statistics_table(1, "distribution", 100) is True


class TestResolveIndexation:
    def test_percent_value_divided_by_100(self):
        from pages.portfolio.portfolio import _resolve_indexation

        assert _resolve_indexation(3) == 0.03

    def test_none_with_inflation_returns_inflation_string(self):
        from pages.portfolio.portfolio import _resolve_indexation

        assert _resolve_indexation(None, has_inflation=True) == "inflation"

    def test_none_without_inflation_returns_zero(self):
        from pages.portfolio.portfolio import _resolve_indexation

        assert _resolve_indexation(None, has_inflation=False) == 0

    def test_percent_value_overrides_inflation(self):
        from pages.portfolio.portfolio import _resolve_indexation

        assert _resolve_indexation(5, has_inflation=True) == 0.05

    def test_string_percent_value_converted_and_divided(self):
        from pages.portfolio.portfolio import _resolve_indexation

        assert _resolve_indexation("3") == 0.03

    def test_zero_percent_returns_zero(self):
        from pages.portfolio.portfolio import _resolve_indexation

        assert _resolve_indexation(0) == 0.0


class TestResolveDiscountRate:
    def test_none_passes_through(self):
        from pages.portfolio.portfolio import _resolve_discount_rate

        assert _resolve_discount_rate(None) is None

    def test_percent_value_divided_by_100(self):
        from pages.portfolio.portfolio import _resolve_discount_rate

        assert _resolve_discount_rate(5) == 0.05

    def test_zero_returns_zero(self):
        from pages.portfolio.portfolio import _resolve_discount_rate

        assert _resolve_discount_rate(0) == 0.0

    def test_string_value_converted_and_divided(self):
        from pages.portfolio.portfolio import _resolve_discount_rate

        assert _resolve_discount_rate("10") == 0.10


CASHFLOW_DEFAULTS = {
    "frequency": "month",
    "initial_amount": 1000.0,
    "cf_amount": None,
    "cf_indexation": None,
    "cf_percentage": None,
    "vds_percentage": None,
    "vds_min_withdrawal": None,
    "vds_max_withdrawal": None,
    "vds_adjust_minmax": None,
    "vds_floor": None,
    "vds_ceiling": None,
    "vds_adjust_fc": None,
    "vds_indexation": None,
    "cwd_amount": None,
    "cwd_indexation": None,
    "cwd_thresholds": None,
    "cwd_reductions": None,
    "ts_dates": None,
    "ts_amounts": None,
    "has_inflation": True,
}


class TestBuildCashflowStrategy:
    def test_default_indexation_strategy(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.IndexationStrategy") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="indexation",
                **{**CASHFLOW_DEFAULTS, "cf_amount": 100, "cf_indexation": 3},
            )

            mock_cls.assert_called_once_with(mock_pf)
            assert mock_instance.initial_investment == 1000.0
            assert mock_instance.amount == 100.0
            assert mock_instance.frequency == "month"
            assert mock_instance.indexation == 0.03

    def test_percentage_strategy(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.PercentageStrategy") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="percentage",
                **{**CASHFLOW_DEFAULTS, "cf_percentage": 4},
            )

            mock_cls.assert_called_once_with(mock_pf)
            assert mock_instance.percentage == 0.04
            assert mock_instance.initial_investment == 1000.0

    def test_vds_strategy(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.VanguardDynamicSpending") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="vds",
                **{
                    **CASHFLOW_DEFAULTS,
                    "vds_percentage": 5,
                    "vds_min_withdrawal": 100,
                    "vds_max_withdrawal": 500,
                    "vds_adjust_minmax": True,
                    "vds_floor": 3,
                    "vds_ceiling": 5,
                    "vds_adjust_fc": False,
                    "vds_indexation": 3,
                },
            )

            mock_cls.assert_called_once()
            kw = mock_cls.call_args[1]
            assert kw["percentage"] == 0.05
            assert kw["min_max_annual_withdrawals"] == (100.0, 500.0)
            assert kw["floor_ceiling"] == (0.03, 0.05)
            assert kw["adjust_min_max"] is True
            assert kw["adjust_floor_ceiling"] is False
            assert kw["indexation"] == 0.03

    def test_cwd_strategy_with_thresholds(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.CutWithdrawalsIfDrawdown") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="cwd",
                **{
                    **CASHFLOW_DEFAULTS,
                    "cwd_amount": 200,
                    "cwd_indexation": 2,
                    "cwd_thresholds": [20, 50],
                    "cwd_reductions": [40, 100],
                },
            )

            mock_cls.assert_called_once()
            kw = mock_cls.call_args[1]
            assert kw["amount"] == 200.0
            assert kw["indexation"] == 0.02
            assert kw["crash_threshold_reduction"] == [(0.2, 0.4), (0.5, 1.0)]

    def test_cwd_raises_when_thresholds_empty(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with pytest.raises(ValueError, match="threshold"):
            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="cwd",
                **{
                    **CASHFLOW_DEFAULTS,
                    "cwd_amount": 200,
                    "cwd_indexation": 2,
                    "cwd_thresholds": [],
                    "cwd_reductions": [],
                },
            )

    def test_time_series_strategy(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.TimeSeriesStrategy") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="time_series",
                **{
                    **CASHFLOW_DEFAULTS,
                    "ts_dates": ["2020-01", "2020-06"],
                    "ts_amounts": [100, 200],
                },
            )

            mock_cls.assert_called_once_with(mock_pf)
            assert mock_instance.initial_investment == 1000.0
            assert mock_instance.time_series_dic == {"2020-01": 100.0, "2020-06": 200.0}


class TestValidateCwdThresholds:
    def test_valid_pair_returns_none(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        assert validate_cwd_thresholds([20, 50], [40, 100]) is None

    def test_all_empty_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([None, None], [None, None])
        assert result is not None
        assert "threshold" in result.lower()

    def test_empty_lists_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([], [])
        assert result is not None

    def test_partial_threshold_only_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, 30], [40, None])
        assert result is not None
        assert "partially" in result.lower() or "incomplete" in result.lower()

    def test_partial_reduction_only_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, None], [40, 100])
        assert result is not None

    def test_valid_with_trailing_empty_row_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, 50, None], [40, 100, None])
        assert result is None

    def test_mixed_valid_and_partial_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, 30, 50], [40, None, 100])
        assert result is not None

    def test_decreasing_thresholds_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([50, 20], [40, 100])
        assert result is not None
        assert "increase" in result.lower() or "ascending" in result.lower()

    def test_decreasing_reductions_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, 50], [100, 40])
        assert result is not None

    def test_equal_thresholds_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, 20], [40, 100])
        assert result is not None

    def test_equal_reductions_returns_error(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        result = validate_cwd_thresholds([20, 50], [40, 40])
        assert result is not None

    def test_ascending_values_valid(self):
        from pages.portfolio.portfolio import validate_cwd_thresholds

        assert validate_cwd_thresholds([10, 20, 50], [30, 60, 100]) is None


class TestCwdBuildRaisesOnInvalidThresholds:
    def test_cwd_raises_on_all_empty(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with pytest.raises(ValueError, match="threshold"):
            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="cwd",
                **{
                    **CASHFLOW_DEFAULTS,
                    "cwd_amount": 200,
                    "cwd_indexation": 2,
                    "cwd_thresholds": [None, None],
                    "cwd_reductions": [None, None],
                },
            )

    def test_cwd_raises_on_partial_row(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with pytest.raises(ValueError):
            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="cwd",
                **{
                    **CASHFLOW_DEFAULTS,
                    "cwd_amount": 200,
                    "cwd_indexation": 2,
                    "cwd_thresholds": [20, 30],
                    "cwd_reductions": [40, None],
                },
            )


class TestDisableCwdAddButton:
    def test_disabled_when_last_row_empty(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import should_disable_cwd_add

        assert should_disable_cwd_add([20, None], [40, None]) is True

    def test_disabled_when_last_threshold_only(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import should_disable_cwd_add

        assert should_disable_cwd_add([20, 30], [40, None]) is True

    def test_disabled_when_last_reduction_only(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import should_disable_cwd_add

        assert should_disable_cwd_add([20, None], [40, 100]) is True

    def test_enabled_when_all_complete(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import should_disable_cwd_add

        assert should_disable_cwd_add([20, 50], [40, 100]) is False

    def test_enabled_when_empty_lists(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import should_disable_cwd_add

        assert should_disable_cwd_add([], []) is False


class TestNextCwdPlaceholder:
    def test_increments_by_10(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import next_cwd_placeholder

        assert next_cwd_placeholder(20, 40) == (30, 50)

    def test_caps_at_100(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import next_cwd_placeholder

        assert next_cwd_placeholder(95, 95) == (100, 100)

    def test_already_100_stays_100(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import next_cwd_placeholder

        assert next_cwd_placeholder(100, 100) == (100, 100)

    def test_no_previous_returns_defaults(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import next_cwd_placeholder

        assert next_cwd_placeholder(None, None) == (20, 40)

    def test_mixed_cap(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import next_cwd_placeholder

        assert next_cwd_placeholder(50, 95) == (60, 100)
