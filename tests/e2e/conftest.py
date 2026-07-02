import os
import signal
import socket
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"Dash server did not start on port {port} within {timeout}s")


@pytest.fixture(scope="session")
def dash_server_url(tmp_path_factory):
    port = _find_free_port()
    env = os.environ.copy()
    env["TESTING"] = "1"
    # Auth: deterministic secret (2 workers must share it) + a session-temp SQLite file,
    # so e2e runs never touch <project>/instance/okama.db.
    env["OKAMA_SECRET_KEY"] = "e2e-test-secret"
    auth_db_dir = tmp_path_factory.mktemp("auth-db")
    env["OKAMA_AUTH_DB_URI"] = f"sqlite:///{auth_db_dir}/okama-e2e.db"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gunicorn",
            "run_gunicorn:server",
            "--bind",
            f"127.0.0.1:{port}",
            "--workers",
            "2",
            "--timeout",
            "30",
        ],
        env=env,
        cwd=PROJECT_ROOT,
        # DEVNULL, not PIPE: nobody drains these pipes, so once the app's logging
        # fills the 64 KiB pipe buffer (~17 navigations since reactive MC estimation
        # logs per page load), gunicorn blocks on write and every later request
        # times out. See the 2026-06-04 E2E stall incident.
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_server(port)
        yield f"http://localhost:{port}"
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


@pytest.fixture
def portfolio_page(page, dash_server_url):
    page.goto(f"{dash_server_url}/portfolio", wait_until="domcontentloaded")
    return page
