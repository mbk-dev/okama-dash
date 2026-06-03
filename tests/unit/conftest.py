import dash
import pytest


@pytest.fixture(autouse=True, scope="session")
def _dash_app():
    """Session-scoped Dash app for unit tests that import pages/ modules."""
    app = dash.Dash(__name__)
    yield app
