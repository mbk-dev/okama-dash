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

Three series groups are available: central bank key rates, maximum deposit
rates in Russian banks (RUB / RUB TOP-10 / USD / EUR) and Russian money-market
rates (RUONIA and its averages, RUSFAR ON/1W/2W/1M/3M).
"""
)
