"""End-to-end run of tools/dump_callbacks.py as a subprocess.

Guards the documented invocation (`poetry run python tools/dump_callbacks.py`):
running the script by path puts tools/ — not the repo root — on sys.path, so
the app import must be wired explicitly inside the script.
"""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.component

ROOT = Path(__file__).resolve().parents[2]


def test_script_runs_by_path_and_dumps_full_wiring_map():
    result = subprocess.run(
        [sys.executable, "tools/dump_callbacks.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert len(lines) >= 80  # ~90 callbacks registered across the five pages
    assert any("db_search" in line and "pages/database" in line for line in lines)
