"""API-surface and pickle tests for the macro okama mocks.

E2E runs pickle these objects through common/object_cache, and component tests
rely on the same attribute surface as real okama macro classes: every data
member is a property/attribute, only describe() is a method.
"""

import pickle

import pandas as pd
import pytest

from tests.mocks.okama_mock import (
    PicklableAsset,
    PicklableAssetList,
    PicklableIndicator,
    PicklableInflation,
    PicklableRate,
)

pytestmark = pytest.mark.unit


class TestPicklableInflation:
    def test_surface_matches_okama(self):
        obj = PicklableInflation("USD.INFL", first_date="2020-01", last_date="2024-12")
        assert obj.symbol == "USD.INFL"
        assert isinstance(obj.values_monthly, pd.Series)
        assert obj.values_monthly.index.freqstr == "M"
        assert isinstance(obj.annual_inflation_ts, pd.Series)
        assert isinstance(obj.cumulative_inflation, pd.Series)
        assert isinstance(obj.rolling_inflation, pd.Series)  # property, not a method
        assert obj.rolling_inflation.name == "USD.INFL"
        assert obj.rolling_inflation.index[0] == pd.Period("2020-12", freq="M")
        assert isinstance(obj.purchasing_power_1000, float)

    def test_describe_shape(self):
        df = PicklableInflation("RUB.INFL").describe()
        assert list(df.columns) == ["property", "period", "RUB.INFL"]
        assert "1000 purchasing power" in df["property"].to_numpy()

    def test_pickle_round_trip(self):
        obj = PicklableInflation("EUR.INFL")
        restored = pickle.loads(pickle.dumps(obj))
        pd.testing.assert_series_equal(restored.values_monthly, obj.values_monthly)
        pd.testing.assert_series_equal(restored.rolling_inflation, obj.rolling_inflation)


class TestPicklableRateAndIndicator:
    def test_rate_surface(self):
        obj = PicklableRate("RUS_CBR.RATE")
        assert isinstance(obj.values_monthly, pd.Series)
        assert obj.values_monthly.name == "RUS_CBR.RATE"
        assert list(obj.describe().columns) == ["property", "period", "RUS_CBR.RATE"]

    def test_indicator_surface(self):
        obj = PicklableIndicator("USA_CAPE10.RATIO")
        assert isinstance(obj.values_monthly, pd.Series)
        # CAPE values are raw decimals, not fractions
        assert obj.values_monthly.mean() > 1.0

    def test_rate_pickles(self):
        obj = PicklableRate("US_EFFR.RATE")
        restored = pickle.loads(pickle.dumps(obj))
        assert restored.symbol == "US_EFFR.RATE"


class TestPicklableAsset:
    def test_surface(self):
        a = PicklableAsset("MOW_PR.RE")
        assert a.symbol == "MOW_PR.RE"
        assert a.currency == "RUB"
        assert isinstance(a.close_monthly, pd.Series)
        assert a.close_monthly.index.freqstr == "M"
        assert a.close_monthly.min() > 1000  # price per m², not a return

    def test_pickles(self):
        a = PicklableAsset("RUS_PR.RE")
        restored = pickle.loads(pickle.dumps(a))
        pd.testing.assert_series_equal(restored.close_monthly, a.close_monthly)


class TestPicklableAssetListExtensions:
    def test_inflation_column_added_when_requested(self):
        al = PicklableAssetList(["MOW_PR.RE"], ccy="RUB", inflation=True)
        assert list(al.wealth_indexes.columns) == ["MOW_PR.RE", "RUB.INFL"]
        al_usd = PicklableAssetList(["MOW_PR.RE"], ccy="USD", inflation=True)
        assert "USD.INFL" in al_usd.wealth_indexes.columns

    def test_no_inflation_column_by_default(self):
        # Existing consumers (compare/benchmark e2e) must keep their column set.
        al = PicklableAssetList(["AAPL.US", "MSFT.US"])
        assert list(al.wealth_indexes.columns) == ["AAPL.US", "MSFT.US"]

    def test_price_conversion_mirrors_private_okama_api(self):
        al = PicklableAssetList(["MOW_PR.RE"], ccy="USD")
        price = PicklableAsset("MOW_PR.RE").close_monthly
        converted = al._adjust_price_to_currency_monthly(price, "RUB")
        assert (converted < price).all()  # USD numbers are smaller than RUB
        al_rub = PicklableAssetList(["MOW_PR.RE"], ccy="RUB")
        pd.testing.assert_series_equal(al_rub._adjust_price_to_currency_monthly(price, "RUB"), price)
