"""Tests for the macro shareable-link builder (defaults omitted, page params appended)."""

import pandas as pd
import pytest

from pages.macro.macro_link import build_macro_link

pytestmark = pytest.mark.unit

TODAY = pd.Timestamp.today().strftime("%Y-%m")


class TestBuildMacroLink:
    def test_defaults_are_omitted(self):
        link = build_macro_link(
            href="http://localhost:8050/macro/inflation?old=1",
            tickers_list=["RUB.INFL", "USD.INFL"],
            first_date="2000-01",
            last_date=TODAY,
        )
        assert link == "http://localhost:8050/macro/inflation?tickers=RUB.INFL,USD.INFL"

    def test_custom_dates_are_emitted(self):
        link = build_macro_link(
            href="http://x/macro/rates",
            tickers_list=["RUS_CBR.RATE"],
            first_date="2010-01",
            last_date="2024-12",
        )
        assert "first_date=2010-01" in link
        assert "last_date=2024-12" in link

    def test_extra_param_with_default_omitted_and_custom_emitted(self):
        base = {
            "href": "http://x/macro/inflation",
            "tickers_list": ["RUB.INFL"],
            "first_date": "2000-01",
            "last_date": TODAY,
        }
        with_default = build_macro_link(**base, plot=("annual", "annual"))
        assert "plot=" not in with_default
        with_custom = build_macro_link(**base, plot=("monthly", "annual"))
        assert "plot=monthly" in with_custom

    def test_flag_param_emitted_only_when_set(self):
        base = {
            "href": "http://x/macro/inflation",
            "tickers_list": ["RUB.INFL"],
            "first_date": "2000-01",
            "last_date": TODAY,
        }
        off = build_macro_link(**base, rates=(None, None))
        assert "rates=" not in off
        on = build_macro_link(**base, rates=("true", None))
        assert "rates=true" in on
