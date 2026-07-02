"""Personal-cabinet auth: one wiring point for app.py (init_auth)."""

import logging
import os

from flask import Flask, redirect
from flask_login import logout_user
from werkzeug.wrappers import Response

from common.auth.db import db
from common.auth.guard import register_auth_guard
from common.auth.login_manager import login_manager

_DEV_SECRET = "okama-dev-secret-not-for-production"


def init_auth(server: Flask) -> None:
    secret = os.environ.get("OKAMA_SECRET_KEY")
    if not secret:
        logging.warning("OKAMA_SECRET_KEY is not set — using an insecure dev secret")
        secret = _DEV_SECRET
    server.secret_key = secret

    # setdefault: tests pre-set an in-memory URI before calling init_auth.
    # Default is relative to the Flask instance folder -> <project>/instance/okama.db,
    # which Flask-SQLAlchemy creates automatically.
    server.config.setdefault(
        "SQLALCHEMY_DATABASE_URI", os.environ.get("OKAMA_AUTH_DB_URI", "sqlite:///okama.db")
    )
    db.init_app(server)
    login_manager.init_app(server)
    register_auth_guard(server)
    with server.app_context():
        db.create_all()

    @server.route("/logout")
    def logout() -> Response:
        logout_user()
        return redirect("/")
