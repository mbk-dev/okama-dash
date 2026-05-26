# AGENTS.md — okama-dash

## Project structure

```
okama-dash/
├── app.py                   # Dash app entry point (dev server, port 8050)
├── run_gunicorn.py          # Production WSGI entry point (imports app.server)
├── navigation.py            # Top navigation bar component
├── footer.py                # Footer component
├── clear_redis_cache.py     # Redis cache flush utility
├── pyproject.toml           # Poetry config, ruff/black settings, dependencies
├── requirements.txt         # Pip fallback (keep in sync with pyproject.toml)
├── .python-version          # Python 3.14
│
├── pages/                   # Multi-page Dash widgets (dash.register_page)
│   ├── efficient_frontier/  # "/" — portfolio optimization, EF chart, transition map
│   ├── compare/             # "/compare" — historical asset performance comparison
│   ├── benchmark/           # "/benchmark" — performance vs benchmark index
│   ├── portfolio/           # "/portfolio" — portfolio analysis, rebalancing, cashflows
│   └── database/            # "/database" — search financial DB (stocks, ETFs, currencies)
│
├── common/                  # Shared modules used across pages
│   ├── settings.py          # App-wide constants (max tickers, MC limits, defaults)
│   ├── symbols.py           # Asset symbol utilities
│   ├── validators.py        # Input validation
│   ├── parse_query.py       # URL query string parsing
│   ├── create_link.py       # Shareable link generation
│   ├── date_input.py        # Date picker components
│   ├── chart_helpers.py     # Plotly helpers (inflation traces, crisis shading, alerts)
│   ├── mantine.py           # Dash Mantine component wrappers
│   ├── update_style.py      # Dynamic style manipulation
│   ├── mobile_screens.py    # Responsive layout adapters
│   ├── math.py              # Financial calculations
│   ├── inflation.py         # Inflation data helpers
│   ├── xlsx.py              # Excel export utilities
│   ├── crisis/              # Crisis period data (shaded chart regions)
│   └── html_elements/       # Custom HTML/Dash components (copy-link, info tables)
│
├── assets/                  # Static files served by Dash (CSS, JS, images)
├── cache-directory/         # Runtime file-system cache (Flask-Caching fallback)
└── docs/                    # Specs and plans (not deployed)
```

Each page follows the pattern: `pages/<name>/<name>.py` (layout + callbacks) with a
`cards_<name>/` subfolder for card components and `eng/` for English description text.

**Stack:** Dash + Flask, Plotly charts, okama library (financial data & analytics),
Flask-Caching + Redis, Dash Bootstrap + Dash Mantine, Gunicorn (production).

## Running locally

```bash
poetry install
poetry run python app.py          # http://localhost:8050, debug=True (hot reload)
```

**Environment variables** (all optional, with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `OKAMA_CACHE_BACKEND` | `redis` | Cache backend: `redis` or `filesystem` |
| `OKAMA_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL (only when backend is `redis`) |

When `OKAMA_CACHE_BACKEND=filesystem`, caching falls back to `cache-directory/` — no Redis needed.

## Deployment

Production deployment on **secondvds** via systemd unit `okama-dash.service`,
running Gunicorn (`run_gunicorn.py`). See project memory for paths and recovery commands.

## Environment & dependencies

- Poetry for environment & dependency management.
- Virtualenv lives at `.venv/` inside the project root (`virtualenvs.in-project = true`).
  When recreating, always run `poetry config virtualenvs.in-project true` before `poetry env use`.
- Always use `poetry add` instead of `pip install`.
- Use `poetry run python ...` to run scripts.
- New dependencies must be added in `pyproject.toml` **and** `requirements.txt`
  (the latter is a top-level-only fallback for non-Poetry environments).

## Test-Driven Development (TDD)

Any change to production code (new feature, bugfix, refactor, behavior change) must follow
TDD: **write a failing test first, then the minimal code that makes it pass**. This overrides
the default "write code, then tests" workflow.

The required workflow is the `superpowers:test-driven-development` skill.
Cycle: **RED → verify RED → GREEN → verify GREEN → REFACTOR**.

Rules for this repo:
- Tests run via: `poetry run pytest -q`.
- Before writing code, see the test fail for a real reason (`AssertionError` / missing function),
  not a typo/import error.
- For bugfix: first a test reproducing the bug, then the fix. Without a reproducing test
  the bug is not considered fixed.
- One test = one behavior. Test name describes the behavior meaningfully, no `test1` / `test_works`.
- Real code instead of mocks wherever possible.
- After GREEN, run the full test suite of the file/module to make sure nothing broke;
  output must be clean (no warnings/errors).
- Exceptions where TDD can be skipped: only by explicit user request (one-time data migration
  scripts, generated code, throwaway prototypes). Notebooks — partial exception: cover the
  library code with tests, not the notebook rendering itself.

## Code change workflow

After any code changes, follow this checklist:

1. Determine whether *executable Python code* was changed, not just comments or docstrings.
2. If executable code was changed — always run tests: `poetry run pytest -q`.
3. If only comments, docstrings, or Jupyter Notebook files were changed — do not run tests.
4. If tests reveal failures, attempt to fix and re-run (max 2 retries).
   If still failing, stop and report the remaining issues.
5. Before finishing any code change (including notebooks), run `poetry run ruff check .`
   and fix every reported issue. If a warning is truly unavoidable, silence it with a
   targeted `# noqa: <CODE>` comment on the offending line and include a brief rationale.
   Never disable rules globally or use a bare `# noqa`.

## Python style & modernization

- Write new code with modern syntax and avoid legacy forms:
  - Use built-in generics: `list[int]`, `dict[str, Any]`, `tuple[int, ...]`
    instead of `typing.List` / `Dict` / `Tuple`.
  - Use union syntax `X | Y` and `X | None` instead of `typing.Union` / `typing.Optional`.
  - Prefer literals over constructor calls: `{}`, `[]`, `set()` — avoid `dict()`, `list()`
    when a literal works. In particular, never write `dict()` for an empty dict,
    and never wrap `kwargs`-style pairs as `dict(a=1, b=2)` when a literal is clearer.
  - Use `dict(zip(a, b))` instead of `{k: v for k, v in zip(a, b)}` (ruff C416).
  - Use set literals `{"a", "b"}` instead of `set(["a", "b"])` (ruff C405).
  - Never use mutable default arguments (`def f(x=[])` / `x={}`). Use `None` and
    initialize inside the function body (ruff B006). For simple fixed pairs like
    `figsize=(12, 6)`, prefer a tuple.
  - Keep `matplotlib` `bbox=` / style kwargs as dict literals, not `dict(...)` calls.
- **Ruff configuration** is in `pyproject.toml` (`[tool.ruff.lint]`, selecting `C,E,F,W,B`).
  Treat it as the authoritative style guide — if ruff is silent, the style is acceptable.

## Code conventions

- Always write all code comments, docstrings, and documentation in **English**, even if the
  task description or existing code is in another language (e.g. Russian).
- Use type hints for all function parameters and return types.
- Use f-string formatting for all logging and print messages.
- When editing Jupyter Notebook examples in the `/examples` directory, ensure that the code
  examples are up-to-date with the current codebase in the Git branch.
