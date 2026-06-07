"""API-surface and pickle tests for the macro okama mocks.

E2E runs pickle these objects through common/object_cache, and component tests
rely on the same attribute surface as real okama macro classes: every data
member is a property/attribute, only describe() is a method.
"""

import pickle

import pandas as pd
import pytest

from tests.mocks.okama_mock import PicklableIndicator, PicklableInflation, PicklableRate

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
        assert isinstance(obj.purchasing_power_1000, float)

    def test_describe_shape(self):
        df = PicklableInflation("RUB.INFL").describe()
        assert list(df.columns) == ["property", "period", "RUB.INFL"]
        assert "1000 purchasing power" in df["property"].to_numpy()

    def test_pickle_round_trip(self):
        obj = PicklableInflation("EUR.INFL")
        restored = pickle.loads(pickle.dumps(obj))
        pd.testing.assert_series_equal(restored.values_monthly, obj.values_monthly)


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
