"""Stale-client callback requests answer 204, real callback errors stay 500.

After a deploy, browser tabs and search-engine bots that rendered the previous
build keep POSTing /_dash-update-component with output ids or input arities
that no longer exist server-side. Dash fails on these before any callback runs;
the guard converts that pre-dispatch failure into an empty 204 (the
PreventUpdate convention) with a one-line warning instead of a 500 + traceback.
"""

import logging

import dash
import pytest
from dash import Input, Output, dcc, html
from werkzeug.exceptions import BadRequestKeyError

from common.stale_callbacks import _raised_inside_callback, register_stale_callback_guard

pytestmark = pytest.mark.component

UPDATE_PATH = "/_dash-update-component"


@pytest.fixture()
def guarded_app():
    # The toy app's _setup_server (before_request) drains dash's GLOBAL_CALLBACK_MAP
    # and clears GLOBAL_CALLBACK_LIST — state other tests read for already-imported
    # pages modules. Snapshot and restore it around the test.
    from dash import _callback as dash_callback

    saved_map = dict(dash_callback.GLOBAL_CALLBACK_MAP)
    saved_list = list(dash_callback.GLOBAL_CALLBACK_LIST)

    app = dash.Dash("stale_guard_test")
    app.layout = html.Div(
        [dcc.Input(id="a"), dcc.Input(id="b"), html.Div(id="out"), html.Div(id="boom")]
    )

    @app.callback(Output("out", "children"), Input("a", "value"), Input("b", "value"))
    def _two_inputs(a, b):
        return f"{a}-{b}"

    @app.callback(Output("boom", "children"), Input("a", "value"))
    def _raises_index_error(_a):
        return [][0]

    register_stale_callback_guard(app.server)
    yield app

    dash_callback.GLOBAL_CALLBACK_MAP.clear()
    dash_callback.GLOBAL_CALLBACK_MAP.update(saved_map)
    dash_callback.GLOBAL_CALLBACK_LIST[:] = saved_list


@pytest.fixture()
def client(guarded_app):
    return guarded_app.server.test_client()


def _body(output_id: str, output_prop: str, inputs: list[dict]) -> dict:
    return {
        "output": f"{output_id}.{output_prop}",
        "outputs": {"id": output_id, "property": output_prop},
        "inputs": inputs,
        "changedPropIds": [f"{inputs[0]['id']}.{inputs[0]['property']}" if inputs else ""],
    }


class TestStaleRequestsGet204:
    def test_unknown_output_returns_204(self, client, caplog):
        # A client built before a deploy posts an output id that no longer exists.
        body = _body("ghost", "children", [{"id": "a", "property": "value", "value": 1}])
        with caplog.at_level(logging.WARNING):
            resp = client.post(UPDATE_PATH, json=body)
        assert resp.status_code == 204
        assert resp.data == b""
        assert any("stale client" in r.message for r in caplog.records)

    def test_arity_mismatch_returns_204(self, client):
        # The output still exists but the old client sends fewer inputs than
        # the current callback signature expects (IndexError in _prepare_grouping).
        body = _body("out", "children", [{"id": "a", "property": "value", "value": 1}])
        resp = client.post(UPDATE_PATH, json=body)
        assert resp.status_code == 204
        assert resp.data == b""


class TestRealErrorsStay500:
    def test_index_error_inside_callback_stays_500(self, client):
        # An IndexError raised by the callback itself is a genuine bug and
        # must keep producing a 500, not be swallowed as stale-client noise.
        body = _body("boom", "children", [{"id": "a", "property": "value", "value": 1}])
        resp = client.post(UPDATE_PATH, json=body)
        assert resp.status_code == 500

    def test_http_keyerror_subclass_keeps_its_status(self, guarded_app):
        # werkzeug's BadRequestKeyError subclasses KeyError; the guard must
        # return it untouched so its 400 status is preserved.
        server = guarded_app.server

        @server.route("/form-boom")
        def _form_boom():
            raise BadRequestKeyError("missing-field")

        resp = server.test_client().get("/form-boom")
        assert resp.status_code == 400


class TestRaisedInsideCallbackDiscriminator:
    def test_true_for_exception_from_invoke_callback(self):
        from dash._callback import _invoke_callback

        try:
            _invoke_callback(lambda: [][0])
        except IndexError as err:
            assert _raised_inside_callback(err) is True
        else:
            pytest.fail("expected IndexError")

    def test_false_for_exception_raised_elsewhere(self):
        try:
            _ = [][0]
        except IndexError as err:
            assert _raised_inside_callback(err) is False
