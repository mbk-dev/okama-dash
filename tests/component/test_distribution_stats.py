"""
Component tests: Portfolio "Distribution test" statistics delegate to okama's
Frame helpers instead of calling scipy.stats directly.

okama-dash used to import skew/kurtosis/jarque_bera/kstest from scipy.stats and
fit distributions by hand. scipy 1.18.0 regressed scipy.stats.kstest (ks_1samp ->
ndtr arity TypeError), which crashed the Distribution test. okama already exposes
scipy-version-safe equivalents on okama.common.helpers.helpers.Frame, so the stats
are computed through okama (matching its methodology) and the direct scipy import
is gone.
"""

import pytest

from okama.common.helpers.helpers import Frame

from tests.mocks.okama_mock import make_mock_portfolio

pytestmark = pytest.mark.component

_KS_DISTRIBUTIONS = [("Normal", "norm"), ("Lognormal", "lognorm"), ("Student's T", "t")]


def test_kstest_values_delegate_to_okama_frame():
    from pages.portfolio.portfolio import compute_distribution_stats

    pf = make_mock_portfolio()
    ror = pf.ror.dropna()
    stats = compute_distribution_stats(pf)

    for label, distr in _KS_DISTRIBUTIONS:
        expected = Frame.kstest_series(ror, distr=distr)
        assert stats["kstest"][label]["statistic"] == pytest.approx(expected["statistic"])
        assert stats["kstest"][label]["p-value"] == pytest.approx(expected["p-value"])


def test_moments_and_jarque_bera_delegate_to_okama_frame():
    from pages.portfolio.portfolio import compute_distribution_stats

    pf = make_mock_portfolio()
    ror = pf.ror.dropna()
    stats = compute_distribution_stats(pf)

    assert stats["skewness"] == pytest.approx(Frame.skewness(ror).iloc[-1])
    assert stats["kurtosis"] == pytest.approx(Frame.kurtosis(ror).iloc[-1])

    expected_jb = Frame.jarque_bera_series(ror)
    assert stats["jarque_bera"]["statistic"] == pytest.approx(expected_jb["statistic"])
    assert stats["jarque_bera"]["p-value"] == pytest.approx(expected_jb["p-value"])


def test_distribution_figure_lognormal_fit_on_gross_returns():
    """The fitted-PDF overlay fits the lognormal on gross returns (1 + r) with
    floc=0 — the same way the KS test does (okama Frame.kstest_series) — instead of
    on raw sign-mixed returns. Keeps the plotted curve consistent with the test and
    avoids 'invalid value encountered in log' from fitting lognorm on negative data.
    """
    import numpy as np
    from scipy.stats import lognorm

    from pages.portfolio.portfolio import _get_distribution_figure

    pf = make_mock_portfolio()
    data = pf.ror
    fig = _get_distribution_figure(pf)

    xmin, xmax = data.min(), data.max()
    x = np.linspace(xmin, xmax, 100)
    bins_number = 50 if data.shape[0] >= 120 else 10
    bin_size = (xmax - xmin) / bins_number
    shape, loc, scale = lognorm.fit(data + 1.0, floc=0)
    expected = lognorm.pdf(x + 1.0, shape, loc, scale) * bin_size

    lognorm_trace = next(tr for tr in fig.data if getattr(tr, "name", None) == "Lognormal")
    np.testing.assert_allclose(np.asarray(lognorm_trace.y, dtype=float), expected, rtol=1e-9)
