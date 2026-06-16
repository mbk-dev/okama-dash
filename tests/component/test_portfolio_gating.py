import pytest

pytestmark = pytest.mark.component


class TestPrintWithdrawalRate:
    """Live withdrawal-rate readout (pf-withdrawal-rate) — gating.py."""

    def test_partial_minus_in_amount_does_not_crash(self):
        # While typing a negative amount the field briefly emits the string '-'
        # (truthy), so float('-') raised ValueError and 500'd the callback
        # (prod 2026-06-15). A mid-typing value must read as 0%, not crash.
        from pages.portfolio.cards_portfolio.portfolio_controls.gating import print_withdrawal_rate

        result = print_withdrawal_rate("1000", None, "-", "cwd", "year")
        assert result == "0%"

    def test_partial_minus_in_initial_amount_does_not_crash(self):
        from pages.portfolio.cards_portfolio.portfolio_controls.gating import print_withdrawal_rate

        result = print_withdrawal_rate("-", None, "100", "cwd", "year")
        assert result == "0%"

    def test_valid_amounts_compute_rate(self):
        # Regression guard: the fix must not swallow real numeric input.
        from pages.portfolio.cards_portfolio.portfolio_controls.gating import print_withdrawal_rate

        result = print_withdrawal_rate("1200", None, "100", "cwd", "month")
        assert result == "100%"
