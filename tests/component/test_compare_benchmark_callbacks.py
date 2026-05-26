import pytest

from common.update_style import change_style_for_hidden_row

pytestmark = pytest.mark.component


class TestChangeStyleForHiddenRow:
    def test_nonzero_clicks_shows(self):
        assert change_style_for_hidden_row(1, {"display": "none"}) is None

    def test_zero_clicks_no_style_hides(self):
        assert change_style_for_hidden_row(0, None) == {"display": "none"}

    def test_zero_clicks_empty_dict_hides(self):
        assert change_style_for_hidden_row(0, {}) == {"display": "none"}

    def test_zero_clicks_with_style_keeps(self):
        style = {"display": "none"}
        assert change_style_for_hidden_row(0, style) == {"display": "none"}

    def test_large_clicks_shows(self):
        assert change_style_for_hidden_row(100, {"display": "none"}) is None


class TestCompareShowHide:
    def test_show_after_click(self):
        from pages.compare.compare import show_graf_and_statistics_table_rows

        s1, s2 = show_graf_and_statistics_table_rows(1, {"display": "none"})
        assert s1 is None
        assert s2 is None

    def test_hidden_before_click(self):
        from pages.compare.compare import show_graf_and_statistics_table_rows

        s1, s2 = show_graf_and_statistics_table_rows(0, None)
        assert s1 == {"display": "none"}
        assert s2 == {"display": "none"}


class TestBenchmarkShowHide:
    def test_show_after_click(self):
        from pages.benchmark.benchmark import show_graf_row

        assert show_graf_row(1, {"display": "none"}) is None

    def test_hidden_before_click(self):
        from pages.benchmark.benchmark import show_graf_row

        assert show_graf_row(0, None) == {"display": "none"}


class TestBenchmarkGetYTitle:
    def test_tracking_difference(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("td") == "Tracking difference, %"

    def test_annualized_td(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("annualized_td") == "Annualized Tracking difference, %"

    def test_tracking_error(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("te") == "Tracking Error, %"

    def test_correlation(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("correlation") == "Correlation"

    def test_beta(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("beta") == "Beta coefficient"

    def test_annual_td_bar(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("annual_td_bar") == "Annual Tracking difference, %"

    def test_unknown_returns_none(self):
        from pages.benchmark.benchmark import get_y_title

        assert get_y_title("unknown") is None
