---
name: check-prod-errors
description: Use when checking okama.io production errors on secondvds — "проверь ошибки на проде", "what's failing in production", triaging 500s, reading okama-dash server logs/tracebacks, or verifying error rates after a deploy.
---

# Check okama-dash production errors (secondvds)

## Overview

Tracebacks are NOT in the gunicorn error log. App stderr goes to **journald**;
`/var/www/okama-dash/log/gunicorn_error.log` holds only gunicorn lifecycle
lines (boot/SIGTERM/USR1), so an empty error log proves nothing.

## Where things are

| What | Where |
|---|---|
| systemd unit | `gunicorn_okama_dash.service` (NOT okama-dash.service) |
| App tracebacks | `sudo -n journalctl -u gunicorn_okama_dash.service` (no sudo → empty + adm-group hint) |
| Access log | `/var/www/okama-dash/log/gunicorn_access.log` — remote addr is EMPTY (unix socket), so HTTP status is awk field **$8**, not $9 |
| Rotated logs | `gunicorn_access.log-YYYYMMDD[.gz]` (dateext, delaycompress) |
| okama-API errors | same host, unit `gunicorn_api.service`, code `/var/www/api` |

## Triage workflow

```bash
# 1. Unhandled 500s (the real failures) — count + types
ssh secondvds "sudo -n journalctl -u gunicorn_okama_dash.service --since '3 days ago' --no-pager \
  | grep -c 'Exception on /'"
ssh secondvds "sudo -n journalctl -u gunicorn_okama_dash.service --since '3 days ago' --no-pager \
  | grep -oE '(AttributeError|KeyError|ValueError|TypeError|IndexError|HTTPError|RuntimeError|ConnectionError|TimeoutError|RetryError).*' \
  | sort | uniq -c | sort -rn | head -20"

# 2. App frames for one error type (where to fix)
ssh secondvds "sudo -n journalctl -u gunicorn_okama_dash.service --since '3 days ago' --no-pager \
  | grep -B30 '<ERROR TEXT>' | grep 'File \"/var/www/okama-dash' | sort | uniq -c | sort -rn"

# 3. 5xx with referer URLs (which page/link triggers it). Current file = today
# only (daily rotation); for an arbitrary window also scan the rotated files.
ssh secondvds "awk '\$8 ~ /^5[0-9][0-9]\$/' /var/www/okama-dash/log/gunicorn_access.log | tail -20"
```

Caveats for step 1's type-grep:
- It also matches **raise-site source lines** quoted inside traceback frames
  (e.g. `RetryError(_pool, url, reason) from reason`, `ConnectionError(`) and
  each link of a chained exception (NameResolution→MaxRetry→Connection = 3
  hits for 1 failure). Treat counts as an overview; for exact numbers count
  `Exception on /` markers and attribute each block (see below).
- journald **interleaves lines of the 3 gunicorn workers** (`poetry[<pid>]`),
  so `grep -B/-A` context can mix blocks from different workers. To attribute
  a traceback to its marker reliably, key by worker pid:

```bash
ssh secondvds "sudo -n journalctl -u gunicorn_okama_dash.service --since '...' --no-pager \
  | awk 'match(\$0,/poetry\[[0-9]+\]/){pid=substr(\$0,RSTART,RLENGTH)} /Exception on \//{m[pid]=\$0} /^.*[A-Za-z]+Error: /{if (m[pid]) {print m[pid]; print \$0; m[pid]=\"\"}}'"
```

## Interpreting what you find

- **Unhandled 500** = traceback preceded by `ERROR - Exception on /...` (Flask).
  Only these reach users as 500.
- **Handled, not a bug**: traceback preceded by `Callback error` /
  `df recompute failed` / `Estimate parameters failed` — `logging.exception`
  inside a try/except that already shows a toast. Don't "fix" these as 500s.
- **`stale client` warnings** = the 204 guard (`common/stale_callbacks.py`)
  absorbing post-deploy bots/old tabs. Expected noise, not errors.
- **api.okama.io RetryError/Timeout/NameResolution** — upstream/network blips;
  check if clustered in one minute (incident) vs spread (real problem). For a
  persistent 500 on ONE ticker → classifier↔data desync, see
  `okama-scripts/AGENTS.md` "Adding a new ticker" (PLTRUB case); reproduce with
  `curl "https://api.okama.io/api/ts/ror/<TICKER>?first_date=1913-01-01&last_date=2100-01-01&period=M"`
  (quote the URL — `&` forks the shell otherwise) and read the
  `gunicorn_api.service` journal.
- **`TypeError: layout() got an unexpected keyword argument`** — a page layout
  missing `**kwargs` hit by a query param (utm_*). Every `def layout(...)` in
  `pages/` must end with `**kwargs`.

## Common mistakes

| Mistake | Reality |
|---|---|
| `journalctl -u okama-dash.service` → "No entries" → "no errors" | Wrong unit name; use `gunicorn_okama_dash.service` |
| journalctl without `sudo -n` looks clean | User can't see system journal; output is empty, not clean |
| `tail gunicorn_error.log` is clean → done | Tracebacks are only in journald |
| `awk '$9 ~ /^5/'` on the access log | Matches response SIZE; status is `$8` here |
| Counting every journal traceback as a 500 | Handled `logging.exception` tracebacks are not 500s — check the marker line above the traceback |

After fixing anything: AGENTS.md "Code change workflow" + release gate (full
suite incl. e2e) apply; deploy = `git pull --ff-only` + `systemctl restart`
(see memory `okama-dash-deployment`).
