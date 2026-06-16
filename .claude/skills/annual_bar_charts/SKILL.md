---
name: annual-bar-charts
description: Use when building or editing an annual (year-grouped) bar chart in okama-dash — annual inflation, annual return, annual tracking difference, or any new "one bar per year" Plotly chart on a date axis. Also use when a year bar chart shows the latest year-to-date bar under the NEXT year's label, bars look shifted one year too high, or a not-yet-finished future year appears.
---

# Annual bar charts in okama-dash

## Overview
Every "one bar per year" chart on a **date** x-axis MUST be built with
`common.chart_helpers.annual_bar_figure(df, ...)`. Do **not** hand-roll the
`to_timestamp(...)` + `px.bar` + `update_xaxes(dtick="M12", ...)` sequence — that
is exactly how the off-by-one year-label bug is (re)introduced.

**Core principle:** bar placement and the year-tick anchor must be the same instant
(Jan 1). The helper guarantees this; inline code drifts.

## When to use
- Adding/editing an annual bar chart (inflation `annual`, portfolio/compare
  `annual_return`, benchmark `annual_td_bar`, or a brand-new one).
- Debugging a year bar chart whose latest **year-to-date** bar sits under the
  **next** year's label (e.g. a "2027" bar in mid-2026), or every bar reads one
  year too high.

Not for: monthly bars, line charts, or categorical (non-date) axes.

## The trap (root cause)
An annual `Y-DEC` `PeriodIndex` converted with `to_timestamp(freq="Y")` (or
`how="end"`) lands each bar on **Dec 31**. The axis draws year ticks with
`dtick="M12"` + `ticklabelmode="instant"`, which plotly anchors on **Jan 1**. A
Dec-31 bar sits one day before the next year's Jan-1 tick, so its `%Y` label reads
**+1 year**. The data is correct; only the placement-vs-tick mismatch is wrong.
Midpoint (Jul 1) or `how="end"` "fixes" are divergent — don't invent a new anchor.

## Pattern
```python
from common.chart_helpers import annual_bar_figure

# df: columns to plot, index = annual (Y) PeriodIndex
fig = annual_bar_figure(df, title="Portfolio Annual Return", height=800)  # barmode="group" default
fig.update_layout(xaxis_title=None, legend_title="Portfolio")
# barmode="relative" for stacked annual bars (benchmark annual_td_bar)
```

The helper anchors bars at Jan 1 (`to_timestamp()`, the default `how="start"`) and
applies the year ticks, so an overlaid monthly line (key-rate overlay) shares the
same date axis.

## Verify
- **Regression test:** assert every bar trace's x is Jan 1 — see
  `tests/unit/test_chart_helpers.py::TestAnnualBarFigure` and the
  `*_bars_anchored_at_year_start` tests on each page:
  ```python
  x = pd.DatetimeIndex(trace.x)
  assert list(x.month) == [1] * len(x) and list(x.day) == [1] * len(x)
  ```
- **Visual:** the latest bar's label must equal the current year, never +1. Review
  live on the Gunicorn server (`:8051`, see AGENTS.md "Running locally").

## Common mistakes
| Mistake | Why it breaks | Fix |
|---------|---------------|-----|
| `to_timestamp(freq="Y")` / `how="end"` | Dec-31 bars → +1 label vs Jan-1 ticks | `annual_bar_figure` (Jan-1) |
| Inline `px.bar` + `update_xaxes(dtick="M12", ...)` | placement & tick anchor drift apart on copy | call the helper |
| Categorical year strings as x | breaks the shared date axis used by overlays | keep date axis via helper |
| New anchor (Jul-1 midpoint, etc.) | diverges from every other annual chart | use the helper's Jan-1 anchor |
