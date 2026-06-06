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

    def test_indexation_strategy_sets_custom_time_series(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.IndexationStrategy") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="indexation",
                **{**CASHFLOW_DEFAULTS, "cf_amount": 100, "ts_dates": ["2030-01"], "ts_amounts": [5000]},
            )

            assert mock_instance.time_series_dic == {"2030-01": 5000.0}

    def test_percentage_strategy_sets_custom_time_series(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.PercentageStrategy") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="percentage",
                **{**CASHFLOW_DEFAULTS, "cf_percentage": 4, "ts_dates": ["2030-01"], "ts_amounts": [5000]},
            )

            assert mock_instance.time_series_dic == {"2030-01": 5000.0}

    def test_vds_strategy_sets_custom_time_series(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.VanguardDynamicSpending") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="vds",
                **{**CASHFLOW_DEFAULTS, "vds_percentage": 5, "ts_dates": ["2030-01"], "ts_amounts": [5000]},
            )

            assert mock_instance.time_series_dic == {"2030-01": 5000.0}

    def test_cwd_strategy_sets_custom_time_series(self, patched_okama_portfolio):
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
                    "cwd_thresholds": [20, 50],
                    "cwd_reductions": [40, 100],
                    "ts_dates": ["2030-01"],
                    "ts_amounts": [5000],
                },
            )

            assert mock_instance.time_series_dic == {"2030-01": 5000.0}

    def test_no_custom_rows_leaves_time_series_unset(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import _build_cashflow_strategy

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        with patch("pages.portfolio.portfolio.ok.IndexationStrategy") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            _build_cashflow_strategy(
                pf_object=mock_pf,
                strategy_type="indexation",
                **{**CASHFLOW_DEFAULTS, "cf_amount": 100},
            )

            # MagicMock auto-creates attributes on access; a real assignment
            # would replace the child mock with a plain dict.
            assert not isinstance(mock_instance.time_series_dic, dict)


class TestBuildTsDict:
    def test_valid_pairs_build_dict(self):
        from pages.portfolio.portfolio import _build_ts_dict

        assert _build_ts_dict(["2020-01", "2020-06"], [100, -200]) == {"2020-01": 100.0, "2020-06": -200.0}

    def test_invalid_date_skipped(self):
        from pages.portfolio.portfolio import _build_ts_dict

        assert _build_ts_dict(["bad-date", "2020-06"], [100, 200]) == {"2020-06": 200.0}

    def test_empty_inputs_return_empty_dict(self):
        from pages.portfolio.portfolio import _build_ts_dict

        assert _build_ts_dict(None, None) == {}

    def test_row_without_amount_skipped(self):
        from pages.portfolio.portfolio import _build_ts_dict

        assert _build_ts_dict(["2020-01"], [None]) == {}


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


def _walk_components(node):
    """Yield every Dash component node in the tree rooted at node."""
    yield node
    children = getattr(node, "children", None)
    if children is None or isinstance(children, (str, int, float, bool)):
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if child is None or isinstance(child, (str, int, float, bool)):
            continue
        yield from _walk_components(child)


def _find_by_id(node, target_id):
    for n in _walk_components(node):
        if getattr(n, "id", None) == target_id:
            return n
    return None


def _label_texts(node):
    """Return the string children of every html.Label in the subtree."""
    texts = []
    for n in _walk_components(node):
        if type(n).__name__ != "Label":
            continue
        children = n.children
        if not isinstance(children, (list, tuple)):
            children = [children]
        texts.extend(c for c in children if isinstance(c, str))
    return texts


class TestCashflowPercentageInFrequencyRow:
    def test_percentage_input_lives_inside_frequency_row(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        item = cashflow_accordion_item()
        freq_row = _find_by_id(item, "pf-cf-frequency-row")
        assert freq_row is not None, "cash flow frequency row not found"

        assert _find_by_id(freq_row, "pf-cf-percentage") is not None, (
            "Withdrawal/Contribution percentage input must live in the cash flow frequency row"
        )

    def test_percentage_label_omits_the_word_percentage(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        item = cashflow_accordion_item()
        col = _find_by_id(item, "pf-cf-percentage-col")
        assert col is not None, "percentage column not found"

        assert "Withdrawal/Contribution" in _label_texts(col)
        assert "Withdrawal/Contribution percentage" not in _label_texts(col)


class TestWeightRangeValidation:
    def test_negative_weight_is_invalid(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_weight_input

        assert validate_weight_input(-5) is True

    def test_weight_above_100_is_invalid(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_weight_input

        assert validate_weight_input(150) is True

    def test_boundary_and_inner_weights_are_valid(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_weight_input

        assert validate_weight_input(0) is False
        assert validate_weight_input(100) is False
        assert validate_weight_input(50.5) is False

    def test_empty_weight_is_not_flagged(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_weight_input

        assert validate_weight_input(None) is False
        assert validate_weight_input("") is False

    def test_submit_disabled_when_weights_out_of_range_but_sum_100(self):
        """150 + -50 sums to 100 and must still be rejected."""
        from pages.portfolio.cards_portfolio.portfolio_controls import disable_submit_add_link_buttons

        submit_disabled, _, _, _ = disable_submit_add_link_buttons(["AAPL.US", "MSFT.US"], [150, -50], 2, True)
        assert submit_disabled is True

    def test_submit_enabled_for_valid_weights(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import disable_submit_add_link_buttons

        submit_disabled, _, _, _ = disable_submit_add_link_buttons(["AAPL.US", "MSFT.US"], [60, 40], 2, True)
        assert submit_disabled is False


def _find_by_id(component, target_id):
    """Depth-first search of a Dash component tree for an exact string id.

    Walks the ``children`` prop only — ids embedded in other props
    (e.g. an icon inside an AccordionItem ``title``) are not searched.
    """
    if getattr(component, "id", None) == target_id:
        return component
    children = getattr(component, "children", None)
    if children is None:
        return None
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        found = _find_by_id(child, target_id)
        if found is not None:
            return found
    return None


class TestTsAccordionActiveItem:
    def test_collapsed_by_default(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import _ts_accordion_active_item

        assert _ts_accordion_active_item(None, []) is None

    def test_expanded_for_time_series_strategy(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import _ts_accordion_active_item

        assert _ts_accordion_active_item("time_series", []) == "custom-cashflows"

    def test_expanded_when_rows_prefilled(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import _ts_accordion_active_item

        rows = [{"index": 0, "date": "2030-01", "amount": 100.0}]
        assert _ts_accordion_active_item("indexation", rows) == "custom-cashflows"


class TestCashflowNestedAccordionLayout:
    def test_present_and_collapsed_for_default_strategy(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        accordion = _find_by_id(cashflow_accordion_item(), "pf-cf-ts-accordion")
        assert accordion is not None
        assert accordion.start_collapsed is True
        assert getattr(accordion, "active_item", None) is None

    def test_expanded_for_time_series_strategy(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        accordion = _find_by_id(cashflow_accordion_item(cf_strategy="time_series"), "pf-cf-ts-accordion")
        assert accordion.active_item == "custom-cashflows"

    def test_expanded_when_cf_ts_prefilled(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        accordion = _find_by_id(
            cashflow_accordion_item(cf_strategy="indexation", cf_ts=[("2030-01", 5000)]),
            "pf-cf-ts-accordion",
        )
        assert accordion.active_item == "custom-cashflows"

    def test_plain_mode_class_for_time_series_strategy(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        accordion = _find_by_id(cashflow_accordion_item(cf_strategy="time_series"), "pf-cf-ts-accordion")
        assert accordion.class_name == "mt-3 ts-plain"

    def test_accordion_chrome_class_for_other_strategies(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item

        accordion = _find_by_id(cashflow_accordion_item(cf_strategy="indexation"), "pf-cf-ts-accordion")
        assert accordion.class_name == "mt-3"


class TestToggleStrategyPanels:
    def test_returns_description_plus_four_styles(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_strategy_panels

        result = toggle_strategy_panels("indexation")
        assert len(result) == 5  # description + 4 panel styles (TS panel is gone)

    def test_time_series_hides_all_strategy_panels(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_strategy_panels

        _description, indexation, percentage, vds, cwd = toggle_strategy_panels("time_series")
        hide = {"display": "none"}
        assert (indexation, percentage, vds, cwd) == (hide, hide, hide, hide)

    def test_indexation_shows_only_indexation_panel(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_strategy_panels

        _description, indexation, percentage, vds, cwd = toggle_strategy_panels("indexation")
        hide = {"display": "none"}
        assert indexation is None
        assert (percentage, vds, cwd) == (hide, hide, hide)


class TestOpenTsAccordionOnStrategyChange:
    def test_time_series_opens_accordion_in_plain_mode(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import open_ts_accordion_for_time_series

        assert open_ts_accordion_for_time_series("time_series") == ("custom-cashflows", "mt-3 ts-plain")

    def test_other_strategy_closes_accordion_and_restores_chrome(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import open_ts_accordion_for_time_series

        assert open_ts_accordion_for_time_series("indexation") == (None, "mt-3")


class TestManageTsRows:
    """Row container behavior: empty while collapsed, one example row on expand."""

    def _run(self, trigger, active_item, rows=None):
        import dash

        from pages.portfolio.cards_portfolio.cashflow_controls import manage_ts_rows

        rows = rows or []
        ids = [{"index": r["index"]} for r in rows]
        dates = [r["date"] for r in rows]
        amounts = [r["amount"] for r in rows]
        with patch.object(dash, "ctx") as mock_ctx:
            mock_ctx.triggered_id = trigger
            return manage_ts_rows(0, [], active_item, ids, dates, amounts)

    @staticmethod
    def _row_values(row):
        date_input = row.children[0].children[0]
        amount_input = row.children[1].children
        return date_input.value, amount_input.value

    def test_initial_load_collapsed_creates_no_rows(self):
        assert self._run(trigger=None, active_item=None) == []

    def test_expand_with_no_rows_creates_prefilled_withdrawal_row(self):
        result = self._run(trigger="pf-cf-ts-accordion", active_item="custom-cashflows")

        assert len(result) == 1
        assert self._row_values(result[0]) == ("2020-01", -1000)

    def test_initial_load_open_creates_prefilled_row(self):
        result = self._run(trigger=None, active_item="custom-cashflows")

        assert len(result) == 1
        assert self._row_values(result[0]) == ("2020-01", -1000)

    def test_add_appends_empty_row(self):
        existing = [{"index": 0, "date": "2031-05", "amount": -500}]

        result = self._run(trigger="pf-cf-ts-add", active_item="custom-cashflows", rows=existing)

        assert len(result) == 2
        assert self._row_values(result[0]) == ("2031-05", -500)
        assert self._row_values(result[1]) == (None, None)

    def test_remove_last_row_while_open_recreates_prefilled_row(self):
        existing = [{"index": 0, "date": "2031-05", "amount": -500}]

        result = self._run(
            trigger={"type": "pf-cf-ts-remove", "index": 0},
            active_item="custom-cashflows",
            rows=existing,
        )

        assert len(result) == 1
        assert self._row_values(result[0]) == ("2020-01", -1000)

    def test_collapse_keeps_existing_rows(self):
        existing = [{"index": 0, "date": "2031-05", "amount": -500}]

        result = self._run(trigger="pf-cf-ts-accordion", active_item=None, rows=existing)

        assert len(result) == 1
        assert self._row_values(result[0]) == ("2031-05", -500)
