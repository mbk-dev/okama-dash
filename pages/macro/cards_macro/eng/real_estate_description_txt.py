from dash import dcc

real_estate_description_text = dcc.Markdown(
    """
Russian residential real estate prices from the okama free financial database:
Moscow and Russia-wide averages, primary (new builds) and secondary markets,
in rubles per square meter at monthly granularity since April 2000.

- **Price per m²** — average price level in RUB, or converted to USD at the
  monthly exchange rate.
- **Wealth index** — growth of 1000 invested at the start of the selected
  period, plotted together with inflation: does real estate beat inflation?

The statistics table reports compound return, CAGR over 1 / 5 / 10 years and
the whole period next to inflation, plus risk, CVAR and maximum drawdowns.
"""
)
