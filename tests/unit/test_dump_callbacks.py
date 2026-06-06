"""Tests for tools/dump_callbacks.py — greppable callback wiring map.

The formatter consumes dash's callback registry entries (GLOBAL_CALLBACK_MAP /
app.callback_map values): a dict with the wrapped callback function plus
inputs/state dicts and Output objects. Stubs below mimic those shapes.
"""

import functools
from pathlib import Path

import pytest

from tools.dump_callbacks import format_callback_map, format_entry

pytestmark = pytest.mark.unit

_ROOT = Path(__file__).resolve().parents[2]
_THIS_FILE = "tests/unit/test_dump_callbacks.py"


def _sample_callback(value):
    return value


def _later_callback(value):
    return value


class _Out:
    """Duck-typed stand-in for dash.dependencies.Output."""

    def __init__(self, component_id, component_property):
        self.component_id = component_id
        self.component_property = component_property


def _entry(func, output, inputs, state):
    """Build a callback_map-style entry with a dash-like wrapper around func."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return {"callback": wrapper, "output": output, "inputs": inputs, "state": state}


class TestFormatEntry:
    def test_single_output_line_shows_location_name_and_wiring(self):
        entry = _entry(
            _sample_callback,
            output=_Out("graf", "figure"),
            inputs=[{"id": "submit", "property": "n_clicks"}],
            state=[{"id": "ccy", "property": "value"}],
        )
        line = format_entry(entry, root=_ROOT)
        loc = f"{_THIS_FILE}:{_sample_callback.__code__.co_firstlineno}"
        assert line == (
            f"{loc} _sample_callback | out: graf.figure | in: submit.n_clicks | state: ccy.value"
        )

    def test_state_section_omitted_when_empty(self):
        entry = _entry(
            _sample_callback,
            output=_Out("graf", "figure"),
            inputs=[{"id": "submit", "property": "n_clicks"}],
            state=[],
        )
        line = format_entry(entry, root=_ROOT)
        assert "| state:" not in line
        assert line.endswith("| in: submit.n_clicks")

    def test_multi_output_list_rendered_comma_separated(self):
        entry = _entry(
            _sample_callback,
            output=[_Out("a", "value"), _Out("b", "disabled")],
            inputs=[{"id": "submit", "property": "n_clicks"}],
            state=[],
        )
        line = format_entry(entry, root=_ROOT)
        assert "| out: a.value, b.disabled |" in line

    def test_clientside_entry_marked_without_source_location(self):
        # app.clientside_callback registers an entry with no Python "callback" key
        entry = {
            "output": _Out("store", "data"),
            "inputs": [{"id": "store", "property": "data"}],
            "state": [],
        }
        line = format_entry(entry, root=_ROOT)
        assert line == "<clientside> | out: store.data | in: store.data"

    def test_dict_component_id_is_stringified(self):
        entry = _entry(
            _sample_callback,
            output=_Out("graf", "figure"),
            inputs=[{"id": {"type": "row", "index": 2}, "property": "value"}],
            state=[],
        )
        line = format_entry(entry, root=_ROOT)
        assert "in: {'type': 'row', 'index': 2}.value" in line


class TestFormatCallbackMap:
    def test_lines_sorted_by_file_and_line(self):
        earlier = _entry(
            _sample_callback,
            output=_Out("a", "value"),
            inputs=[{"id": "x", "property": "value"}],
            state=[],
        )
        later = _entry(
            _later_callback,
            output=_Out("b", "value"),
            inputs=[{"id": "y", "property": "value"}],
            state=[],
        )
        # Insertion order deliberately reversed: output must sort by location.
        text = format_callback_map({"k-later": later, "k-earlier": earlier}, root=_ROOT)
        lines = text.splitlines()
        assert len(lines) == 2
        assert " _sample_callback " in lines[0]
        assert " _later_callback " in lines[1]
