from unittest.mock import MagicMock, patch

import dash
import pytest

from tests.mocks.okama_mock import make_mock_portfolio


@pytest.fixture(autouse=True, scope="session")
def _dash_app():
    app = dash.Dash(__name__)
    yield app


@pytest.fixture
def patched_okama_portfolio(tmp_path):
    mock_pf = make_mock_portfolio()

    with (
        patch("pages.portfolio.portfolio.get_or_create", return_value=(mock_pf, "test.pkl")),
        patch("pages.portfolio.portfolio.ok.Portfolio", return_value=mock_pf) as mock_cls,
        patch("pages.portfolio.portfolio.ok.Rebalance") as mock_rebal,
        patch("pages.portfolio.portfolio.ok.IndexationStrategy") as mock_idx_strat,
    ):
        mock_idx_instance = MagicMock()
        mock_idx_strat.return_value = mock_idx_instance
        yield {
            "portfolio_cls": mock_cls,
            "rebalance_cls": mock_rebal,
            "portfolio_instance": mock_pf,
            "indexation_strategy": mock_idx_instance,
        }
