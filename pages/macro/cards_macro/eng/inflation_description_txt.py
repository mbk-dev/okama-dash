from dash import dcc

inflation_description_text = dcc.Markdown(
    """
Consumer price inflation indexes for Russia, USA, EU, UK, Israel and China
from the okama free financial database.

- **Annual inflation** — year-by-year compound inflation.
- **Rolling 12m inflation** — compound inflation over a sliding 12-month window.
- **Cumulative inflation** — total price-level growth over the selected period.
- **Monthly inflation** — raw monthly prints of the index.
- **Show key rates** — overlays the matching central-bank key rates
  (Bank of Russia, US Fed EFFR, ECB MRO, Bank of England, Bank of Israel,
  PBoC 1-year LPR) as stepped dotted lines.

The statistics table reports annual and compound inflation, the worst
12-month window and the purchasing power of 1000 currency units over
YTD / 1 / 5 / 10 years and the whole selected period.
"""
)
