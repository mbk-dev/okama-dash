from dash import dcc

cape10_description_text = dcc.Markdown(
    """
CAPE10 (cyclically adjusted price-to-earnings ratio, Shiller P/E) for 26
countries from the okama free financial database. CAPE10 divides the market
price by the average inflation-adjusted earnings of the last 10 years and is
a widely used valuation gauge: high values signal expensive markets, low
values — cheap ones.

- **History** — CAPE10 time series for the selected countries.
- **Current snapshot** — the latest CAPE10 of all 26 countries side by side,
  selected countries highlighted.

The statistics table reports mean, median, maximum and minimum CAPE10 over
YTD / 1 / 5 / 10 years and the whole selected period — current value vs the
historical median makes over/under-valuation visible.
"""
)
