import pytest

from tests.mocks.okama_mock import (
    get_mock_namespaces,
    make_mock_portfolio,
    mock_symbols_in_namespace,
)


@pytest.fixture
def mock_okama_symbols(monkeypatch):
    namespaces = get_mock_namespaces()
    monkeypatch.setattr("okama.assets_namespaces", namespaces)
    monkeypatch.setattr("okama.symbols_in_namespace", mock_symbols_in_namespace)
    monkeypatch.setattr("common.settings.namespaces", namespaces)
    return namespaces


@pytest.fixture
def mock_portfolio():
    return make_mock_portfolio()


@pytest.fixture
def null_cache():
    from flask import Flask

    import common

    app = Flask(__name__)
    common.cache.init_app(app, config={"CACHE_TYPE": "NullCache"})
    with app.app_context():
        yield common.cache
