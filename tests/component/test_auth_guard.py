from unittest.mock import patch

import pytest
from flask import Flask

from common.auth import init_auth
from common.auth.service import create_user

pytestmark = pytest.mark.component


@pytest.fixture
def auth_server():
    server = Flask(__name__)
    # Pre-set BEFORE init_auth: init_auth uses setdefault, so this wins over the env default.
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    init_auth(server)
    return server


def test_anonymous_cabinet_redirects_to_login(auth_server):
    client = auth_server.test_client()
    response = client.get("/cabinet")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_authenticated_cabinet_is_not_redirected_to_login(auth_server):
    with auth_server.app_context():
        user, _ = create_user("a@b.co", "long-enough-pw")
        user_id = user.id
    client = auth_server.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)  # how flask-login stores the logged-in user
    response = client.get("/cabinet")
    # Bare Flask app has no /cabinet route -> 404; the point is: no /login redirect.
    assert response.status_code != 302


def test_other_paths_are_not_gated(auth_server):
    client = auth_server.test_client()
    response = client.get("/portfolio")
    assert response.status_code != 302


def test_logout_route_logs_out_and_redirects_home(auth_server):
    client = auth_server.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "1"
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_missing_secret_key_falls_back_with_warning():
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with patch.dict("os.environ", {}, clear=False), patch("common.auth.logging.warning") as warn:
        import os

        os.environ.pop("OKAMA_SECRET_KEY", None)
        init_auth(server)
    assert server.secret_key  # a fallback secret was set
    warn.assert_called_once()


def test_samesite_lax_is_set_by_default():
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with patch.dict("os.environ", {"OKAMA_ENV": ""}, clear=False):
        init_auth(server)
    assert server.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert not server.config.get("SESSION_COOKIE_SECURE")


def test_production_env_enables_secure_cookies():
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with patch.dict("os.environ", {"OKAMA_ENV": "production"}, clear=False):
        init_auth(server)
    assert server.config["SESSION_COOKIE_SECURE"] is True
    assert server.config["REMEMBER_COOKIE_SECURE"] is True
