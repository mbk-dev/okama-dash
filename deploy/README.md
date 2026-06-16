# Auto-deploy (okama.io on secondvds)

Every push to `master` triggers `.github/workflows/deploy.yml`:

1. **test** — installs deps + Playwright Chromium and runs the **full** suite
   (`poetry run pytest -q`, incl. e2e) on Python 3.14 (the secondvds runtime).
   This enforces the *Release gate (master)* rule in `AGENTS.md`.
2. **deploy** — runs only if `test` is green. Connects to secondvds over SSH and
   triggers the server-side forced command `okama-dash-deploy`, which does
   `git pull --ff-only` → (conditional `poetry install`) → `systemctl restart` →
   health check.

The CI key is locked to a single command on the server (SSH forced command), so a
leaked key cannot run arbitrary root commands even though `chilango` has NOPASSWD sudo.

## One-time setup

### 1. Server: install the deploy script (authoritative copy, outside the git tree)

```bash
ssh secondvds 'sudo install -m 0755 /var/www/okama-dash/deploy/deploy.sh /usr/local/bin/okama-dash-deploy'
```

Re-run this whenever `deploy/deploy.sh` changes (a `git pull` does not refresh the
installed copy on purpose — it must not rewrite the script while it is running).

### 2. Server: create a dedicated deploy keypair and lock it to the script

```bash
ssh secondvds '
  ssh-keygen -t ed25519 -N "" -C "okama-dash-ci-deploy" -f ~/.ssh/okama_dash_deploy
  # Forced command: this key can ONLY run okama-dash-deploy, with no shell/forwarding.
  printf "command=\"/usr/local/bin/okama-dash-deploy\",no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty %s\n" \
    "$(cat ~/.ssh/okama_dash_deploy.pub)" >> ~/.ssh/authorized_keys
'
```

### 3. GitHub repo secrets (`mbk-dev/okama-dash` → Settings → Secrets → Actions)

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | `82.146.59.58` |
| `DEPLOY_USER` | `chilango` |
| `DEPLOY_SSH_KEY` | contents of `~/.ssh/okama_dash_deploy` (the **private** key) |
| `DEPLOY_KNOWN_HOSTS` | output of `ssh-keyscan -t ed25519 82.146.59.58` (pins the host key) |

### 4. Enable

Commit the workflow + `deploy/` to `master`. The first push triggers a full
run (test → deploy). Watch it under the repo's **Actions** tab.

## Known limitations

- **Major data-library upgrades still need a manual deploy.** A pandas/okama major
  bump can change the pickle format of cached okama objects; the auto-deploy runs
  `poetry install` but does **not** clear `cache-directory/*.pkl` or Redis. For such
  releases, deploy manually (or pause auto-deploy) and clear caches per the deploy log
  in project memory.
- **`poetry install` only.** It does not run `poetry lock --regenerate`; if a changed
  `pyproject.toml` constraint conflicts with the server's gitignored lock, the install
  fails and the deploy aborts *before* restart (prod stays on the old code, CI goes red).
  Resolve manually, then re-run.

## Disabling

Disable the workflow in the repo's **Actions** tab (or delete `.github/workflows/deploy.yml`),
and optionally remove the forced-command line from `~chilango/.ssh/authorized_keys` on secondvds.
