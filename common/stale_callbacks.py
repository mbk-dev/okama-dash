"""Graceful handling of callback requests from stale clients.

After a deploy, browser tabs and search-engine bots that rendered the previous
build keep POSTing /_dash-update-component with output ids or input arities
that no longer exist server-side. Dash fails on these BEFORE any callback runs
(KeyError "Callback function not found" from _prepare_callback, or IndexError
from _prepare_grouping on an arity mismatch), turning every such request into
a 500 with a full traceback in the log.

register_stale_callback_guard() answers those pre-dispatch failures with an
empty 204 — the same convention Dash uses for PreventUpdate, which the client
renderer treats as "no update" — and logs a single WARNING line instead.
Exceptions raised inside an actual callback are re-raised untouched and keep
producing a 500 with the full traceback.
"""

import flask
from dash._callback import _invoke_callback
from werkzeug.exceptions import HTTPException

UPDATE_PATH = "/_dash-update-component"


def _is_update_request() -> bool:
    return flask.request.path == UPDATE_PATH


def _raised_inside_callback(err: BaseException) -> bool:
    """True if the exception was raised by the callback body itself.

    Mirrors Dash's own pruned-traceback detection: a frame running
    _invoke_callback means dispatch succeeded and the error is the app's,
    not a stale request that failed during callback preparation.
    """
    tb = err.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code is _invoke_callback.__code__:
            return True
        tb = tb.tb_next
    return False


def _ignore_stale(server: flask.Flask, err: BaseException) -> tuple[str, int]:
    user_agent = flask.request.headers.get("User-Agent", "")
    server.logger.warning(f"Ignored callback request from a stale client: {err!r} ua={user_agent!r}")
    return "", 204


def register_stale_callback_guard(server: flask.Flask) -> None:
    @server.errorhandler(KeyError)
    def _stale_output(err):
        if isinstance(err, HTTPException):
            # werkzeug's BadRequestKeyError subclasses KeyError; keep its status
            return err
        if _is_update_request() and "Callback function not found" in str(err):
            return _ignore_stale(server, err)
        raise err

    @server.errorhandler(IndexError)
    def _stale_arity(err):
        if _is_update_request() and not _raised_inside_callback(err):
            return _ignore_stale(server, err)
        raise err
