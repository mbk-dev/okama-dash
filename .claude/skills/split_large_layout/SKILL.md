---
name: split_large_layout
description: Use when a Dash layout in okama-dash has grown too large and needs breaking up — a card/page module that mixes a big layout with many callbacks, a single component-building function spanning hundreds of lines, or any "this file is too big, split it into modules" / "refactor this layout" request. Covers the safe module→feature-package split that keeps every import and callback working.
---

# Splitting a large Dash layout into feature modules

## Overview

okama-dash layout files (`pages/<page>/cards_<page>/*.py`) tend to grow into one
huge component-building function plus a pile of callbacks in the same file. The
fix is to split by **feature**, not by "layout vs callbacks": each strategy /
panel / sub-widget owns *its* sub-layout, *its* callbacks and *its* helpers
together (high cohesion).

This is a **behavior-preserving refactor** — the rendered component tree and the
callback wiring must come out byte-identical. Carve sections verbatim, change
only imports. Codified in `AGENTS.md` → "Layout decomposition (no monolithic
layouts)". Reference implementations:
`pages/portfolio/cards_portfolio/cashflow_controls/` (accordion — one
self-contained child per section),
`pages/portfolio/cards_portfolio/portfolio_controls/` and
`pages/efficient_frontier/cards_efficient_frontier/ef_controls/` (cards whose
multi-row sections are returned as lists and splatted into the body).

## Why it is safe in Dash (the two facts that make this work)

1. **Callbacks register as an import side effect.** A `@callback` runs at import
   time and registers itself with the app. So a callback can live in *any*
   module, as long as that module is imported during app startup.
2. **Callback wiring is by string component id**, invisible to symbol tools.
   Moving a callback to another file never breaks wiring — the ids are unchanged.

So the split is invisible to consumers **if** you keep the public import surface
stable. Do that by turning the module into a **package** whose `__init__.py`
re-exports the public names.

## When to use

- A card/page layout module is large and mixes layout with many callbacks.
- One builder function spans hundreds of lines (~150–200+ is the signal).
- The user says "split this file / layout into modules", "this is too big",
  "refactor cashflow_controls / portfolio_controls / ...".

**Triage by the BUILDER size, not the file size.** Measure the layout-building
function, not the whole module's line count. A 2000-line file whose `layout()` is
only ~100 lines (the bulk being callbacks + business logic, e.g.
`pages/portfolio/portfolio.py`) is NOT this refactor — splitting its *logic* is a
different, riskier job. This skill applies when one *builder* function is the
monolith. Find it (builder start → first `@callback` ≈ builder size):

```bash
grep -nE "^def (card_controls|layout|.*_controls)\b|^@callback" <file> | head
```

Not for: changing what the layout renders (that is a feature change → TDD), or
React/okama-web layouts (this is Dash-specific).

## Procedure

### 1. Map the public API — INCLUDING tests

Per `AGENTS.md`, default `rg` skips `tests/`. You MUST search both, or you will
silently break test imports:

```bash
rg -l "<module_name>" --type py        # production importers
rg -l "<module_name>" tests/           # test importers
rg "from .*<module_name> import" --type py -n
rg "from .*<module_name> import" tests/ -n
```

Collect every name imported anywhere (incl. leading-underscore helpers like
`_ts_accordion_active_item`). That set is what `__init__.py` must re-export.

### 2. Establish a GREEN baseline (refactor discipline)

Branch off `dev` (never work on `master`), then run the consumer tests so a later
red is provably caused by the move:

```bash
git checkout -b refactor/<name> dev
poetry run pytest <consumer_test_files> -q
```

### 3. Carve the package, section by section, VERBATIM

Create `<module>/` with feature submodules. Typical layout (adapt to the file):

```
<module>/
├── __init__.py      # re-export public API + import submodules (registration)
├── constants.py     # option lists, descriptions, limits
├── helpers.py       # shared pure helpers
├── common.py        # shared top section + cross-cutting callbacks
├── <feature>.py     # one per feature: its sub-layout + callbacks + helpers
└── layout.py        # thin assembler: the top builder calling the panel builders
```

Rules while carving:

- **Copy section bodies verbatim.** Do not retype or "clean up" the JSX-like
  tree — a dropped wrapper (e.g. `search_provider(dmc.NumberInput(...))`) is a
  real regression that component tests may NOT catch (they find the inner node by
  id either way). This is the #1 pitfall. Preserving the wrapper means BOTH
  keeping the `search_provider(...)` call AND importing `search_provider` (and the
  wrapped lib, e.g. `dmc`) in the new module — a half-carve drops one or the other.
- **Multi-row sections: return a LIST, splat with `*`, never add a wrapper.**
  When a section is several *sibling* rows inside a parent (a card's `CardBody`, an
  "attributes" `Div`), the section builder returns a Python list of those rows and
  the assembler splats it: `html.Div([_dates_row(...), *options_section(),
  *monte_carlo_section()])`. Wrapping the rows in a new `Div` to return "one
  component" adds a DOM element and breaks CSS/spacing — that is a behavior change,
  not a pure move. Only the accordion case (cashflow_controls) had a single
  self-contained child per section; cards (portfolio_controls, ef_controls) do not.
- **Module-level side-effect calls move with their section.** Top-level statements
  like `register_date_validation("pf-first-date")` run on import, same as
  `@callback`. Put them in the module that owns their section (date rows →
  `layout.py`); they only fire if that module is imported.
- **A row/section builder used by BOTH the layout and a callback** (e.g.
  `_ts_row`, `_cwd_row`) lives in that feature's module; both the assembler and
  the callback import it from there.
- **Per-module imports must be exact** — import only what each file uses, or ruff
  F401/F811 fails. Build the dependency graph acyclic: `layout` → feature modules
  → `common`/`helpers`/`constants`; feature modules never import `layout` or the
  package `__init__`.
- **The assembler (`layout.py`) keeps the public builder's signature identical.**

### 4. `__init__.py` — re-export + `__all__`

```python
from .layout import cashflow_accordion_item
from .common import toggle_strategy_panels
from .timeseries import open_ts_accordion_for_time_series, manage_ts_rows, _ts_accordion_active_item
# ... every name the production code + tests import ...

__all__ = ["cashflow_accordion_item", "toggle_strategy_panels", ...]
```

`__all__` is required: it lists the re-exported names so ruff treats the
otherwise-"unused" imports as used (suppresses F401). Importing `.layout` pulls
in every feature submodule (it imports their builders), which registers all their
callbacks; the explicit re-export lines also cover any callback-only module the
assembler does not reach.

### 5. Delete the old file and verify

```bash
git rm pages/.../<module>.py
poetry run pytest <consumer_test_files> -q     # must equal the baseline count
poetry run pytest -m "not e2e" -q              # whole project: imports/registration intact
poetry run python tools/dump_callbacks.py | rg "<module>/"   # every callback registers from its new file, same out/in/state
poetry run ruff check .                        # clean
```

Then run the full suite incl. e2e (`poetry run pytest -m e2e -q`) — the page is
rendered for real in the browser, the only check that proves the carved tree is
visually identical.

Verify-step gotchas seen in practice:

- **Run the e2e command on its own.** Chaining a server kill in front of it
  (`pkill ... ; poetry run pytest -m e2e`) repeatedly produced empty output / a
  spurious exit 1 in this environment. Kill any stray `gunicorn run_gunicorn` in a
  *separate* call first (the e2e server + a leftover server OOM together), then run
  e2e alone. Foreground `sleep` is blocked by the harness — don't use it to "wait"
  for the kill.
- **A red in an UNRELATED module is probably not your refactor.** The known flake
  `test_object_cache.py::...::test_corrupt_file_reconstructs` fails under
  concurrent pytest runs (shared `cache-directory/`). Before treating any failure
  as a regression, check whether it is in the *refactored module's* tests; if it is
  elsewhere, re-run it solo and check `AGENTS.md` → "Known gaps".

### 6. Commit

`refactor(<area>): split <module> into a feature package` — note it is a pure
move, behavior preserved, suite green. No new test (TDD-skip rule: no logic
change), the existing suite is the safety net.

## Checklist

- [ ] Triaged by BUILDER size, not file size (logic-heavy file → not this skill)
- [ ] Public API mapped from production AND `tests/`
- [ ] GREEN baseline recorded on a `refactor/*` branch off `dev`
- [ ] Sections carved verbatim (wrappers intact, with their imports)
- [ ] Multi-row sections returned as lists and splatted (no new wrapper `Div`)
- [ ] Module-level side-effect calls (e.g. `register_date_validation`) moved with their section
- [ ] Shared row-builders in their feature module
- [ ] `__init__` re-exports every imported name; `__all__` set
- [ ] Old file `git rm`'d
- [ ] Same test count green (fast + e2e — run e2e alone), `dump_callbacks` shows all callbacks, ruff clean
- [ ] Any unrelated red re-run solo and confirmed a known flake (`AGENTS.md` → Known gaps)
