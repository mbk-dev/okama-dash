"""Adaptive grid-step selection for the Efficient Frontier grid portfolios.

The number of grid portfolios for ``n_assets`` at weight ``step`` (default
bounds) is the number of weak compositions of ``1 / step`` units into
``n_assets`` parts: ``C(1/step + n_assets - 1, n_assets - 1)``. It grows
combinatorially, so the UI picks the finest allowed step whose point count
stays within a budget.
"""

from math import comb

from common.settings import GRID_ALLOWED_STEPS, GRID_POINT_BUDGET

AUTO_STEP = "Auto"


def predicted_grid_points(n_assets: int, step: float) -> int:
    """Number of grid portfolios for ``n_assets`` at weight ``step`` (default bounds)."""
    if n_assets < 1:
        return 0
    n_steps = round(1.0 / step)
    return comb(n_steps + n_assets - 1, n_assets - 1)


def resolve_grid_step(
    n_assets: int,
    budget: int = GRID_POINT_BUDGET,
    allowed_steps: tuple[float, ...] = GRID_ALLOWED_STEPS,
) -> float:
    """Return the finest allowed step whose point count is within ``budget``.

    Steps are tried finest-first (smallest step value). If even the coarsest
    step exceeds the budget, the coarsest step is returned (okama's
    ``max_points`` guardrail is the final backstop).
    """
    effective_assets = max(n_assets, 2)
    steps_fine_to_coarse = sorted(allowed_steps)
    for step in steps_fine_to_coarse:
        if predicted_grid_points(effective_assets, step) <= budget:
            return step
    return steps_fine_to_coarse[-1]


def grid_step_options(
    n_assets: int,
    budget: int = GRID_POINT_BUDGET,
    allowed_steps: tuple[float, ...] = GRID_ALLOWED_STEPS,
) -> list[dict]:
    """Dropdown options for the grid step.

    "Auto" is always enabled and first. Each explicit step is labelled with its
    point count and disabled when that count exceeds ``budget``.
    """
    effective_assets = max(n_assets, 2)
    options: list[dict] = [{"label": "Auto", "value": AUTO_STEP, "disabled": False}]
    for step in sorted(allowed_steps):
        points = predicted_grid_points(effective_assets, step)
        percent = round(step * 100)
        options.append(
            {
                "label": f"{percent}% ({points:,} pts)",
                "value": str(step),
                "disabled": points > budget,
            }
        )
    return options


def parse_grid_step_value(
    value: str | None,
    n_assets: int,
    budget: int = GRID_POINT_BUDGET,
    allowed_steps: tuple[float, ...] = GRID_ALLOWED_STEPS,
) -> float:
    """Turn a dropdown value into a concrete step. ``Auto`` resolves by asset count."""
    if value is None or value == AUTO_STEP:
        return resolve_grid_step(n_assets, budget, allowed_steps)
    return float(value)
