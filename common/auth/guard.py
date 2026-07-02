"""Gate /cabinet behind login. Dash pages are served by Dash's catch-all route,
so @login_required (a view decorator) cannot protect them — a before_request
hook can (same pattern as common/seo.py and common/stale_callbacks.py)."""

from flask import Flask, redirect, request
from werkzeug.wrappers import Response

from common.auth.helpers import user_is_authenticated


def register_auth_guard(server: Flask) -> None:
    @server.before_request
    def _cabinet_guard() -> Response | None:
        if request.path.rstrip("/") == "/cabinet" and not user_is_authenticated():
            return redirect("/login")
        return None
