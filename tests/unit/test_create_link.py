import pytest

from common.create_link import check_if_list_empty_or_big, create_filename, create_link

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
        assert "&ccy=USD" in url
        assert "&first_date=2020-01" in url
        assert "&last_date=2024-12" in url

    def test_strips_existing_query_string(self):
        url = create_link(**{**BASE_PARAMS, "href": "/portfolio?old=param"})
        assert "old=param" not in url
        assert url.startswith("/portfolio?tickers=")

    def test_with_weights(self):
        url = create_link(**BASE_PARAMS, weights_list=[50, 50])
        assert "&weights=50,50" in url

    def test_with_rebalancing(self):
        url = create_link(**BASE_PARAMS, rebal="month")
        assert "&rebal=month" in url

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
