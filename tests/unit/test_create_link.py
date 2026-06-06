import pandas as pd
import pytest

from common.create_link import check_if_list_empty_or_big, create_filename, create_link, scope_cashflow_params

pytestmark = pytest.mark.unit

BASE_PARAMS = {
    "href": "/portfolio",
    "tickers_list": ["AAPL.US", "MSFT.US"],
    "ccy": "USD",
    "first_date": "2020-01",
    "last_date": "2024-12",
}

FILENAME_PARAMS = {
    "tickers_list": ["AAPL.US", "MSFT.US"],
    "ccy": "USD",
    "first_date": "2020-01",
    "last_date": "2024-12",
}


class TestCreateLink:
    def test_basic_link(self):
        url = create_link(**BASE_PARAMS)
        assert url.startswith("/portfolio?tickers=AAPL.US,MSFT.US")
        # Non-default params are emitted
        assert "&first_date=2020-01" in url
        assert "&last_date=2024-12" in url
        # Default ccy=USD is omitted
        assert "&ccy=" not in url

    def test_strips_existing_query_string(self):
        url = create_link(**{**BASE_PARAMS, "href": "/portfolio?old=param"})
        assert "old=param" not in url
        assert url.startswith("/portfolio?tickers=")

    def test_with_weights(self):
        url = create_link(**BASE_PARAMS, weights_list=[50, 50])
        assert "&weights=50,50" in url

    def test_with_rebalancing(self):
        # Default rebal=month is omitted
        url = create_link(**BASE_PARAMS, rebal="month")
        assert "&rebal=" not in url
        # Non-default rebal is emitted
        url = create_link(**BASE_PARAMS, rebal="year")
        assert "&rebal=year" in url

    def test_with_benchmark(self):
        url = create_link(
            href="/benchmark",
            tickers_list=["AAPL.US"],
            ccy="USD",
            first_date="2020-01",
            last_date="2024-12",
            benchmark="SP500TR.INDX",
        )
        assert "&benchmark=SP500TR.INDX" in url

    def test_deviation_params(self):
        url = create_link(**BASE_PARAMS, abs_dev=5, rel_dev=10)
        assert "&abs_dev=5" in url
        assert "&rel_dev=10" in url

    def test_cf_strategy_default_not_added(self):
        url = create_link(**BASE_PARAMS, cf_strategy="indexation")
        assert "&cf_strategy=" not in url

    def test_cf_strategy_non_default_added(self):
        url = create_link(**BASE_PARAMS, cf_strategy="vds")
        assert "&cf_strategy=vds" in url

    def test_cf_freq_default_not_added(self):
        url = create_link(**BASE_PARAMS, cf_freq="month")
        assert "&cf_freq=" not in url

    def test_cf_freq_non_default_added(self):
        url = create_link(**BASE_PARAMS, cf_freq="quarter")
        assert "&cf_freq=quarter" in url

    def test_vds_params(self):
        url = create_link(
            **BASE_PARAMS,
            vds_pct=4,
            vds_min=100,
            vds_max=500,
            vds_adj_mm=False,
            vds_floor=3,
            vds_ceil=5,
        )
        assert "&vds_pct=4" in url
        assert "&vds_min=100" in url
        assert "&vds_max=500" in url
        assert "&vds_adj_mm=0" in url
        assert "&vds_floor=3" in url
        assert "&vds_ceil=5" in url

    def test_vds_adj_fc_true(self):
        url = create_link(**BASE_PARAMS, vds_adj_fc=True)
        assert "&vds_adj_fc=1" in url

    def test_cwd_params(self):
        url = create_link(**BASE_PARAMS, cwd_amount=200, cwd_tr=50)
        assert "&cwd_amount=200" in url
        assert "&cwd_tr=50" in url

    def test_default_portfolio_link_is_minimal(self):
        """THE acceptance test: default-only portfolio link contains only tickers and weights."""
        today = pd.Timestamp.today().strftime("%Y-%m")
        url = create_link(
            href="/portfolio",
            tickers_list=["AGG.US", "SPY.US"],
            weights_list=[20, 80],
            ccy="USD",
            first_date="2000-01",
            last_date=today,
            rebal="month",
            initial_amount=1000,
            symbol="PORTFOLIO",
            cf_amount=0,
            cf_pct=0,
            vds_pct=0,
            cwd_amount=0,
        )
        assert url == "/portfolio?tickers=AGG.US,SPY.US&weights=20,80"

    def test_ccy_default_omitted(self):
        """Default ccy=USD is omitted."""
        url = create_link(
            href="/portfolio",
            tickers_list=["AAPL.US"],
            ccy="USD",
            first_date="2020-01",
            last_date="2024-12",
        )
        assert "&ccy=" not in url

    def test_ccy_non_default_emitted(self):
        """Non-default ccy=EUR is emitted."""
        url = create_link(
            href="/portfolio",
            tickers_list=["AAPL.US"],
            ccy="EUR",
            first_date="2020-01",
            last_date="2024-12",
        )
        assert "&ccy=EUR" in url

    def test_first_date_default_omitted(self):
        """Default first_date=2000-01 is omitted."""
        url = create_link(
            href="/portfolio",
            tickers_list=["AAPL.US"],
            ccy="USD",
            first_date="2000-01",
            last_date="2024-12",
        )
        assert "&first_date=" not in url

    def test_first_date_non_default_emitted(self):
        """Non-default first_date is emitted."""
        url = create_link(
            href="/portfolio",
            tickers_list=["AAPL.US"],
            ccy="USD",
            first_date="2010-05",
            last_date="2024-12",
        )
        assert "&first_date=2010-05" in url

    def test_last_date_default_omitted(self):
        """Default last_date (current month) is omitted."""
        today = pd.Timestamp.today().strftime("%Y-%m")
        url = create_link(
            href="/portfolio",
            tickers_list=["AAPL.US"],
            ccy="USD",
            first_date="2020-01",
            last_date=today,
        )
        assert "&last_date=" not in url

    def test_last_date_non_default_emitted(self):
        """Non-default last_date (past month) is emitted."""
        url = create_link(
            href="/portfolio",
            tickers_list=["AAPL.US"],
            ccy="USD",
            first_date="2020-01",
            last_date="2023-06",
        )
        assert "&last_date=2023-06" in url

    def test_rebal_default_omitted(self):
        """Default rebal=month is omitted."""
        url = create_link(**BASE_PARAMS, rebal="month")
        assert "&rebal=" not in url

    def test_rebal_non_default_emitted(self):
        """Non-default rebal=year is emitted."""
        url = create_link(**BASE_PARAMS, rebal="year")
        assert "&rebal=year" in url

    def test_initial_amount_default_omitted(self):
        """Default initial_amount=1000 is omitted (numeric equality)."""
        url = create_link(**BASE_PARAMS, initial_amount=1000)
        assert "&initial_amount=" not in url

    def test_initial_amount_default_float_omitted(self):
        """1000.0 also treated as default."""
        url = create_link(**BASE_PARAMS, initial_amount=1000.0)
        assert "&initial_amount=" not in url

    def test_initial_amount_non_default_emitted(self):
        """Non-default initial_amount=5000 is emitted."""
        url = create_link(**BASE_PARAMS, initial_amount=5000)
        assert "&initial_amount=5000" in url

    def test_symbol_default_omitted(self):
        """Default symbol=PORTFOLIO is omitted."""
        url = create_link(**BASE_PARAMS, symbol="PORTFOLIO")
        assert "&symbol=" not in url

    def test_symbol_non_default_emitted(self):
        """Non-default symbol=my_pf is emitted."""
        url = create_link(**BASE_PARAMS, symbol="my_pf")
        assert "&symbol=my_pf" in url

    def test_cf_amount_zero_omitted(self):
        """cf_amount=0 (default/unset) is omitted."""
        url = create_link(**BASE_PARAMS, cf_amount=0)
        assert "&cf_amount=" not in url

    def test_cf_amount_nonzero_emitted(self):
        """cf_amount=-1500 (withdrawal) is emitted."""
        url = create_link(**BASE_PARAMS, cf_amount=-1500)
        assert "&cf_amount=-1500" in url

    def test_cf_pct_zero_omitted(self):
        """cf_pct=0 (default/unset) is omitted."""
        url = create_link(**BASE_PARAMS, cf_pct=0)
        assert "&cf_pct=" not in url

    def test_cf_pct_nonzero_emitted(self):
        """cf_pct=5 is emitted."""
        url = create_link(**BASE_PARAMS, cf_pct=5)
        assert "&cf_pct=5" in url

    def test_vds_pct_zero_omitted(self):
        """vds_pct=0 (default/unset) is omitted."""
        url = create_link(**BASE_PARAMS, vds_pct=0)
        assert "&vds_pct=" not in url

    def test_vds_pct_nonzero_emitted(self):
        """vds_pct=4 is emitted."""
        url = create_link(**BASE_PARAMS, vds_pct=4)
        assert "&vds_pct=4" in url

    def test_cwd_amount_zero_omitted(self):
        """cwd_amount=0 (default/unset) is omitted."""
        url = create_link(**BASE_PARAMS, cwd_amount=0)
        assert "&cwd_amount=" not in url

    def test_cwd_amount_nonzero_emitted(self):
        """cwd_amount=200 is emitted."""
        url = create_link(**BASE_PARAMS, cwd_amount=200)
        assert "&cwd_amount=200" in url

    def test_cf_indexation_zero_omitted(self):
        """cf_indexation=0 (default/unset) is omitted."""
        url = create_link(**BASE_PARAMS, cf_indexation=0)
        assert "&cf_indexation=" not in url

    def test_cf_indexation_nonzero_emitted(self):
        """cf_indexation=0.02 is emitted."""
        url = create_link(**BASE_PARAMS, cf_indexation=0.02)
        assert "&cf_indexation=0.02" in url

    def test_cwd_tr_emitted_raw(self):
        """cwd_tr emitted without percent-encoding (colon and comma are legal)."""
        url = create_link(**BASE_PARAMS, cwd_tr="20:40,50:100")
        assert "cwd_tr=20:40,50:100" in url
        assert "%3A" not in url
        assert "%2C" not in url

    def test_cf_ts_emitted_raw(self):
        """cf_ts emitted without percent-encoding."""
        url = create_link(**BASE_PARAMS, cf_ts="2020-01:1000,2021-01:-500")
        assert "cf_ts=2020-01:1000,2021-01:-500" in url
        assert "%3A" not in url
        assert "%2C" not in url


class TestUrlParamGrouping:
    """Related params must sit together in the URL (rebalancing group, cash-flow group)."""

    def test_rebalancing_params_grouped(self):
        url = create_link(**BASE_PARAMS, symbol="PORTFOLIO1", rebal="year", abs_dev=20, rel_dev=50)
        assert "rebal=year&abs_dev=20&rel_dev=50" in url

    def test_symbol_precedes_rebalancing_group(self):
        url = create_link(**BASE_PARAMS, symbol="PORTFOLIO1", rebal="year", abs_dev=20)
        assert url.index("symbol=") < url.index("rebal=")

    def test_cashflow_params_grouped(self):
        url = create_link(
            **BASE_PARAMS,
            initial_amount=5000,
            cf_strategy="percentage",
            cf_freq="year",
            cf_pct=-12,
        )
        assert "initial_amount=5000&cf_strategy=percentage&cf_freq=year&cf_pct=-12" in url


class TestInactiveStrategyOmitted:
    """A strategy whose primary flow value is 0/None produces no cash flow → nothing emitted."""

    def _base(self):
        return {
            "cf_freq": "month",
            "cf_amount": None,
            "cf_indexation": None,
            "cf_pct": None,
            "vds_pct": None,
            "vds_min": None,
            "vds_max": None,
            "vds_adj_mm": None,
            "vds_floor": None,
            "vds_ceil": None,
            "vds_adj_fc": None,
            "vds_indexation": None,
            "cwd_amount": None,
            "cwd_tr": None,
            "cf_ts": None,
        }

    def test_percentage_with_zero_pct_returns_all_none(self):
        result = scope_cashflow_params(cf_strategy="percentage", **{**self._base(), "cf_pct": 0})
        assert all(v is None for v in result.values())

    def test_cwd_with_zero_amount_returns_all_none(self):
        result = scope_cashflow_params(cf_strategy="cwd", **{**self._base(), "cwd_amount": 0, "cwd_tr": "20:40"})
        assert all(v is None for v in result.values())

    def test_vds_with_zero_pct_returns_all_none(self):
        result = scope_cashflow_params(cf_strategy="vds", **{**self._base(), "vds_pct": 0})
        assert all(v is None for v in result.values())

    def test_active_strategy_keeps_cf_strategy(self):
        result = scope_cashflow_params(cf_strategy="percentage", **{**self._base(), "cf_pct": -12})
        assert result["cf_strategy"] == "percentage"

    def test_inactive_strategy_nulls_cf_strategy(self):
        result = scope_cashflow_params(cf_strategy="percentage", **{**self._base(), "cf_pct": 0})
        assert result["cf_strategy"] is None

    def test_zero_amount_with_cf_ts_is_active(self):
        result = scope_cashflow_params(
            cf_strategy="indexation", **{**self._base(), "cf_amount": 0, "cf_ts": "2030-01:5000"}
        )
        assert result["cf_strategy"] == "indexation"
        assert result["cf_ts"] == "2030-01:5000"

    def test_zero_pct_with_cf_ts_is_active(self):
        result = scope_cashflow_params(
            cf_strategy="percentage", **{**self._base(), "cf_pct": 0, "cf_ts": "2030-01:5000"}
        )
        assert result["cf_strategy"] == "percentage"
        assert result["cf_ts"] == "2030-01:5000"


class TestScopeCashflowParams:
    """Test scope_cashflow_params: only active strategy's params are returned, rest are None."""

    def test_indexation_with_zero_amount_returns_all_none(self):
        """indexation with cf_amount=0 (or None) is 'no strategy' → all values None."""
        result = scope_cashflow_params(
            cf_strategy="indexation",
            cf_freq="month",
            cf_amount=0,
            cf_indexation=0.02,
            cf_pct=None,
            vds_pct=None,
            vds_min=None,
            vds_max=None,
            vds_adj_mm=None,
            vds_floor=None,
            vds_ceil=None,
            vds_adj_fc=None,
            vds_indexation=None,
            cwd_amount=None,
            cwd_tr=None,
            cf_ts=None,
        )
        assert all(v is None for v in result.values())

    def test_indexation_with_nonzero_amount_keeps_indexation_params(self):
        """indexation with cf_amount=-1500 keeps cf_freq, cf_amount, cf_indexation; rest None."""
        result = scope_cashflow_params(
            cf_strategy="indexation",
            cf_freq="month",
            cf_amount=-1500,
            cf_indexation=0.02,
            cf_pct=5,
            vds_pct=4,
            vds_min=100,
            vds_max=500,
            vds_adj_mm=False,
            vds_floor=3,
            vds_ceil=5,
            vds_adj_fc=True,
            vds_indexation=0.03,
            cwd_amount=200,
            cwd_tr="20:40,50:100",
            cf_ts="2020-01:1000",
        )
        assert result["cf_freq"] == "month"
        assert result["cf_amount"] == -1500
        assert result["cf_indexation"] == 0.02
        assert result["cf_pct"] is None
        assert result["vds_pct"] is None
        assert result["vds_min"] is None
        assert result["vds_max"] is None
        assert result["vds_adj_mm"] is None
        assert result["vds_floor"] is None
        assert result["vds_ceil"] is None
        assert result["vds_adj_fc"] is None
        assert result["vds_indexation"] is None
        assert result["cwd_amount"] is None
        assert result["cwd_tr"] is None
        assert result["cf_ts"] == "2020-01:1000"

    def test_percentage_keeps_only_percentage_params(self):
        """percentage keeps cf_freq and cf_pct; rest None."""
        result = scope_cashflow_params(
            cf_strategy="percentage",
            cf_freq="quarter",
            cf_amount=-1500,
            cf_indexation=0.02,
            cf_pct=5,
            vds_pct=4,
            vds_min=None,
            vds_max=None,
            vds_adj_mm=None,
            vds_floor=None,
            vds_ceil=None,
            vds_adj_fc=None,
            vds_indexation=None,
            cwd_amount=200,
            cwd_tr="20:40",
            cf_ts="2020-01:1000",
        )
        assert result["cf_freq"] == "quarter"
        assert result["cf_pct"] == 5
        assert result["cf_amount"] is None
        assert result["cf_indexation"] is None
        assert result["vds_pct"] is None
        assert result["cwd_amount"] is None
        assert result["cwd_tr"] is None
        assert result["cf_ts"] == "2020-01:1000"

    def test_vds_keeps_only_vds_params(self):
        """vds keeps vds_* params; rest None."""
        result = scope_cashflow_params(
            cf_strategy="vds",
            cf_freq="month",
            cf_amount=-1500,
            cf_indexation=0.02,
            cf_pct=5,
            vds_pct=4,
            vds_min=100,
            vds_max=500,
            vds_adj_mm=False,
            vds_floor=3,
            vds_ceil=5,
            vds_adj_fc=True,
            vds_indexation=0.03,
            cwd_amount=200,
            cwd_tr="20:40",
            cf_ts="2020-01:1000",
        )
        assert result["vds_pct"] == 4
        assert result["vds_min"] == 100
        assert result["vds_max"] == 500
        assert result["vds_adj_mm"] is False
        assert result["vds_floor"] == 3
        assert result["vds_ceil"] == 5
        assert result["vds_adj_fc"] is True
        assert result["vds_indexation"] == 0.03
        assert result["cf_freq"] is None
        assert result["cf_amount"] is None
        assert result["cf_indexation"] is None
        assert result["cf_pct"] is None
        assert result["cwd_amount"] is None
        assert result["cwd_tr"] is None
        assert result["cf_ts"] == "2020-01:1000"

    def test_cwd_keeps_only_cwd_params(self):
        """cwd keeps cf_freq, cwd_amount, cwd_tr; rest None."""
        result = scope_cashflow_params(
            cf_strategy="cwd",
            cf_freq="month",
            cf_amount=-1500,
            cf_indexation=0.02,
            cf_pct=5,
            vds_pct=4,
            vds_min=None,
            vds_max=None,
            vds_adj_mm=None,
            vds_floor=None,
            vds_ceil=None,
            vds_adj_fc=None,
            vds_indexation=None,
            cwd_amount=200,
            cwd_tr="20:40,50:100",
            cf_ts="2020-01:1000",
        )
        assert result["cf_freq"] == "month"
        assert result["cwd_amount"] == 200
        assert result["cwd_tr"] == "20:40,50:100"
        assert result["cf_amount"] is None
        assert result["cf_indexation"] is None
        assert result["cf_pct"] is None
        assert result["vds_pct"] is None
        assert result["cf_ts"] == "2020-01:1000"

    def test_time_series_keeps_only_cf_ts(self):
        """time_series keeps cf_ts; rest None."""
        result = scope_cashflow_params(
            cf_strategy="time_series",
            cf_freq="month",
            cf_amount=-1500,
            cf_indexation=0.02,
            cf_pct=5,
            vds_pct=4,
            vds_min=None,
            vds_max=None,
            vds_adj_mm=None,
            vds_floor=None,
            vds_ceil=None,
            vds_adj_fc=None,
            vds_indexation=None,
            cwd_amount=200,
            cwd_tr="20:40",
            cf_ts="2020-01:1000,2021-01:-500",
        )
        assert result["cf_ts"] == "2020-01:1000,2021-01:-500"
        assert result["cf_freq"] is None
        assert result["cf_amount"] is None
        assert result["cf_indexation"] is None
        assert result["cf_pct"] is None
        assert result["vds_pct"] is None
        assert result["cwd_amount"] is None
        assert result["cwd_tr"] is None


class TestCfTsOwnedByAllStrategies:
    """Custom cash flows survive link scoping under every strategy."""

    _CF_TS = "2030-01:5000,2031-06:-1000"

    def _scope(self, cf_strategy, **overrides):
        base = {
            "cf_freq": "month",
            "cf_amount": None,
            "cf_indexation": None,
            "cf_pct": None,
            "vds_pct": None,
            "vds_min": None,
            "vds_max": None,
            "vds_adj_mm": None,
            "vds_floor": None,
            "vds_ceil": None,
            "vds_adj_fc": None,
            "vds_indexation": None,
            "cwd_amount": None,
            "cwd_tr": None,
            "cf_ts": self._CF_TS,
        }
        return scope_cashflow_params(cf_strategy=cf_strategy, **{**base, **overrides})

    def test_indexation_keeps_cf_ts(self):
        assert self._scope("indexation", cf_amount=-1500)["cf_ts"] == self._CF_TS

    def test_percentage_keeps_cf_ts(self):
        assert self._scope("percentage", cf_pct=-12)["cf_ts"] == self._CF_TS

    def test_vds_keeps_cf_ts(self):
        assert self._scope("vds", vds_pct=-8)["cf_ts"] == self._CF_TS

    def test_cwd_keeps_cf_ts(self):
        assert self._scope("cwd", cwd_amount=-200, cwd_tr="20:40")["cf_ts"] == self._CF_TS


class TestCreateFilename:
    def test_basic_filename(self):
        name = create_filename(**FILENAME_PARAMS)
        assert name.endswith(".pkl")
        assert "AAPL.US-MSFT.US" in name
        assert "ccy=USD" in name

    def test_deterministic(self):
        assert create_filename(**FILENAME_PARAMS) == create_filename(**FILENAME_PARAMS)

    def test_different_params_different_name(self):
        name1 = create_filename(**FILENAME_PARAMS)
        name2 = create_filename(**{**FILENAME_PARAMS, "tickers_list": ["MSFT.US"]})
        assert name1 != name2

    def test_with_weights_and_rebal(self):
        name = create_filename(**FILENAME_PARAMS, weights_list=[0.5, 0.5], rebal="month")
        assert "-w=0.5,0.5" in name
        assert "-rb=month" in name

    def test_with_inflation(self):
        name = create_filename(**FILENAME_PARAMS, inflation=True)
        assert "-infl=True" in name

    def test_cf_strategy_default_not_in_name(self):
        name = create_filename(**FILENAME_PARAMS, cf_strategy="indexation")
        assert "-cs=" not in name

    def test_cf_strategy_non_default_in_name(self):
        name = create_filename(**FILENAME_PARAMS, cf_strategy="vds")
        assert "-cs=vds" in name

    def test_deviation_in_name(self):
        name = create_filename(**FILENAME_PARAMS, abs_dev=5, rel_dev=10)
        assert "-ad=5" in name
        assert "-rd=10" in name


class TestCheckIfListEmptyOrBig:
    def test_empty_list(self):
        assert check_if_list_empty_or_big([]) is True

    def test_list_with_none_only(self):
        assert check_if_list_empty_or_big([None, None]) is True

    def test_normal_list(self):
        assert check_if_list_empty_or_big(["AAPL.US", "MSFT.US"]) is False

    def test_exactly_max_allowed(self):
        tickers = [f"T{i}.US" for i in range(12)]
        assert check_if_list_empty_or_big(tickers) is False

    def test_exceeds_max_allowed(self):
        tickers = [f"T{i}.US" for i in range(13)]
        assert check_if_list_empty_or_big(tickers) is True

    def test_list_with_some_nones(self):
        assert check_if_list_empty_or_big(["AAPL.US", None, "MSFT.US"]) is False
