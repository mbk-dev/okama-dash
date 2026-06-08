from dash import dcc

rates_description_text = dcc.Markdown(
    """
Central bank key interest rates from the okama free financial database:
Bank of Russia key rate, US Fed effective federal funds rate, ECB rates
(main refinancing, deposit facility, marginal lending), Bank of England
bank rate, Bank of Israel interest rate, PBoC loan prime rates.

Rates change stepwise, so the chart draws stepped lines at monthly granularity.

Three plot types are available: **Rates** (nominal historical rates with current values),
**Real rates** (nominal rate minus trailing 12-month inflation of the same currency),
and **Current snapshot** (horizontal bar chart of the latest nominal rates, with selected
series highlighted).
"""
)
