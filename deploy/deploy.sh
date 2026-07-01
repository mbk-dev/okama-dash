#!/usr/bin/env bash
#
# okama-dash auto-deploy hook (secondvds).
#
# Invoked over SSH as a *forced command* (~chilango/.ssh/authorized_keys on secondvds):
# the CI deploy key may run ONLY this script — never arbitrary commands — so a leaked key
# cannot open a root shell on prod even though `chilango` has NOPASSWD sudo.
#
# The AUTHORITATIVE copy lives OUTSIDE the git tree at /usr/local/bin/okama-dash-deploy so
# that a `git pull` mid-run never rewrites the script bash is currently executing. This file
# in the repo is the reviewed source of truth — after editing it, re-install:
#   sudo install -m 0755 deploy/deploy.sh /usr/local/bin/okama-dash-deploy
# See deploy/README.md for the full one-time setup.
#
set -euo pipefail

APP_DIR=/var/www/okama-dash
SERVICE=gunicorn_okama_dash.service
POETRY=/home/chilango/.local/bin/poetry   # same poetry binary the systemd unit uses
SOCK="$APP_DIR/gunicorn.sock"

cd "$APP_DIR"

echo "[deploy] fetch + fast-forward pull on master"
git fetch --quiet origin master
before=$(git rev-parse HEAD)
git pull --ff-only origin master
after=$(git rev-parse HEAD)
echo "[deploy] ${before} -> ${after}"

# Dependency handling: only touch the venv when pyproject.toml actually changed in the
# pulled range (plain pull+restart is the safe default, per the deploy log lessons).
if git diff --name-only "${before}" "${after}" | grep -qx 'pyproject.toml'; then
    echo "[deploy] pyproject.toml changed -> ${POETRY} install"
    "${POETRY}" install --no-interaction --no-ansi
else
    echo "[deploy] pyproject.toml unchanged -> skip dependency install"
fi

echo "[deploy] restart ${SERVICE}"
sudo systemctl restart "${SERVICE}"

# Health check: poll the gunicorn unix socket for HTTP 200 (bypasses nginx/DNS).
# Cold start can take ~30s — systemctl restart drains the old workers, then the new
# workers each run a heavy okama import before the socket serves 200 — so poll up to
# ~60s. The loop exits early on the first 200, so a fast boot is not slowed down; the
# larger ceiling only prevents false-negative failures when the boot is slow.
echo "[deploy] health check on ${SOCK}"
code=""
for _ in $(seq 1 60); do
    code=$(curl -s -o /dev/null -w '%{http_code}' --unix-socket "${SOCK}" http://localhost/ || true)
    if [ "${code}" = "200" ]; then
        echo "[deploy] OK: / returned 200 at ${after}"
        exit 0
    fi
    sleep 1
done

echo "[deploy] FAILED: / did not return 200 after restart (last code: ${code:-none})" >&2
exit 1
