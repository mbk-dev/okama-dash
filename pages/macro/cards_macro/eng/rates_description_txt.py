from dash import dcc

rates_description_text = dcc.Markdown(
    """
Central bank key interest rates from the okama free financial database:
Bank of Russia key rate, US Fed effective federal funds rate, ECB rates
(main refinancing, deposit facility, marginal lending), Bank of England
bank rate, Bank of Israel interest rate and PBoC loan prime rates.

Rates change stepwise, so the chart draws stepped lines at monthly
granularity. The statistics table reports mean, median, maximum and minimum
rates over YTD / 1 / 5 / 10 years and the whole selected period.

Russian deposit rates and money-market rates (RUONIA, RUSFAR) are planned
as additional series groups.
"""
)
