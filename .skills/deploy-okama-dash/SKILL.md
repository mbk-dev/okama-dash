---
name: deploy-okama-dash
description: Deploy okama-dash (okama.io) to the secondvds production server. Use whenever the user asks to deploy, push to production, release, update the server, or says "задеплой", "деплой на прод", "обнови на сервере", "выкати", "deploy okama-dash". Also use after merging dev→master when the user wants the changes live.
---

# Deploy okama-dash to production

Deploys the current `master` branch of okama-dash to the `secondvds` production server
where okama.io is hosted.

## Production environment

- **Server:** `secondvds` (SSH alias → chilango@82.146.59.58)
- **App directory:** `/var/www/okama-dash`
- **Systemd unit:** `gunicorn_okama_dash.service`
- **WSGI:** Gunicorn with 3 workers, unix socket at `gunicorn.sock`
- **Nginx upstream:** `unix:/var/www/okama-dash/gunicorn.sock`
- **Virtualenv:** Poetry-managed at `~/.cache/pypoetry/virtualenvs/okama-dash-*/`
- **Logs:** `/var/www/okama-dash/log/gunicorn_{access,error}.log`

## Deployment steps

Always confirm with the user before executing. Show the plan first.

### 1. Pre-flight checks (local)

```bash
git status
git log --oneline master..dev  # if on dev, show what hasn't been merged
```

Warn if there are uncommitted changes or if `dev` is ahead of `master`.

### 2. Save rollback point (remote)

```bash
ssh secondvds "cd /var/www/okama-dash && git rev-parse HEAD"
```

Save this commit hash — it's the rollback target if anything goes wrong.

### 3. Pull latest code (remote)

```bash
ssh secondvds "cd /var/www/okama-dash && git pull origin master"
```

If the pull fails (merge conflict, dirty tree), stop and report.

### 4. Install dependencies if needed (remote)

Only run if `pyproject.toml` or `poetry.lock` changed in the pulled commits:

```bash
ssh secondvds "cd /var/www/okama-dash && poetry install --no-interaction"
```

**Stale-lock pitfall (hit during the 4.0.0 deploy):** `poetry.lock` is gitignored, so
the server resolves against its own local lock. After significant `pyproject.toml`
changes a plain `poetry install` installs the OLD pinned versions, and `poetry lock`
does NOT fix it — poetry 2.x preserves locked versions by default. Re-resolve from
scratch instead:

```bash
ssh secondvds "cd /var/www/okama-dash && poetry lock --regenerate && poetry install --no-interaction"
```

Then ALWAYS verify that the versions that actually landed match the locally tested
stack before restarting the service:

```bash
ssh secondvds "cd /var/www/okama-dash && poetry run python -c 'import pandas, plotly, dash, okama; print(pandas.__version__, plotly.__version__, dash.__version__, okama.__version__)'"
```

### 5. Restart the service (remote)

```bash
ssh secondvds "sudo systemctl restart gunicorn_okama_dash.service"
```

### 6. Health check (remote)

Wait 5 seconds, then verify:

```bash
ssh secondvds "sudo systemctl is-active gunicorn_okama_dash.service"
ssh secondvds "curl -s -o /dev/null -w '%{http_code}' --unix-socket /var/www/okama-dash/gunicorn.sock http://localhost/"
```

- Service must be `active`
- HTTP status must be `200`

If either check fails, proceed to rollback.

### 7. Verify externally

```bash
curl -s -o /dev/null -w '%{http_code}' https://okama.io/
```

Expected: `200`.

## Rollback procedure

If health check fails after deploy:

```bash
ssh secondvds "cd /var/www/okama-dash && git checkout <saved-rollback-hash>"
ssh secondvds "sudo systemctl restart gunicorn_okama_dash.service"
ssh secondvds "sudo systemctl is-active gunicorn_okama_dash.service"
```

Report the failure to the user with the error details from the logs:

```bash
ssh secondvds "tail -20 /var/www/okama-dash/log/gunicorn_error.log"
```

## Important

- Never deploy from `dev` directly — only `master`.
- If the user wants to deploy `dev`, suggest merging to `master` first.
- Never run `poetry install` without checking if dependencies actually changed —
  it's slow and can shift the virtualenv Python version.
- The cache directory (`cache-directory/`) on the server contains EF and Portfolio
  pickle files, and Redis holds memoized okama objects. Deploys don't clear either.
  If a code change breaks pickle compatibility (pandas/okama major upgrades), clear both.
  The directory can hold tens of thousands of files (18 472 at the 4.0.0 deploy) — shell
  globs (`rm cache-directory/*.pkl`) overflow ARG_MAX and fail; use `find`:

  ```bash
  ssh secondvds "cd /var/www/okama-dash && find cache-directory -name '*.pkl' -delete"
  ssh secondvds "cd /var/www/okama-dash && poetry run python clear_redis_cache.py"
  ```

  `clear_redis_cache.py` is silent on success — verify with `ssh secondvds "redis-cli dbsize"` (expect 0).
