"""Pure helpers for the Find max withdrawal block (issue #22): result mapping and formatting."""

from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit


def _result(withdrawal_abs=-1598.95, withdrawal_rel=0.159895, error_rel=0.048, success=True):
    return SimpleNamespace(
        success=success,
        withdrawal_abs=withdrawal_abs,
        withdrawal_rel=withdrawal_rel,
        error_rel=error_rel,
    )


class TestMapFindResult:
    def test_indexation_gets_negative_absolute_amount(self):
        from pages.portfolio.portfolio import _map_find_result

        assert _map_find_result("indexation", _result()) == -1598.95

    def test_cwd_gets_negative_absolute_amount(self):
        from pages.portfolio.portfolio import _map_find_result

        assert _map_find_result("cwd", _result()) == -1598.95

    def test_percentage_gets_negative_percent(self):
        from pages.portfolio.portfolio import _map_find_result

        assert _map_find_result("percentage", _result()) == -15.99

    def test_vds_gets_negative_percent(self):
        from pages.portfolio.portfolio import _map_find_result

        assert _map_find_result("vds", _result()) == -15.99


class TestFormatFindResult:
    def test_amount_strategy_shows_value_relative_share_and_accuracy(self):
        from pages.portfolio.portfolio import _format_find_result

        text = _format_find_result("indexation", _result())
        assert text == "Withdrawal: -1 599 (16.0% of initial) · accuracy ±4.8%"

    def test_percentage_strategy_shows_percent_and_accuracy(self):
        from pages.portfolio.portfolio import _format_find_result

        text = _format_find_result("percentage", _result())
        assert text == "Withdrawal: -16.0% · accuracy ±4.8%"

    def test_amount_uses_space_thousands_separator(self):
        from pages.portfolio.portfolio import _format_find_result

        text = _format_find_result("cwd", _result(withdrawal_abs=-1234567.0, withdrawal_rel=0.12))
        assert "-1 234 567" in text
