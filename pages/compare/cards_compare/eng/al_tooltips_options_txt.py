from dash import dcc

al_options_tooltip_inflation = dcc.Markdown(
    """
    If enabled, inflation will be displayed on the chart.  
    &NewLine;   
    However, with inflation turned on,   
    the chart statistics will not include last month data,   
    as inflation statistics are delayed.  
"""
)
al_options_tooltip_cagr = dcc.Markdown(
    """
    **Wealth index** (Cumulative Wealth Index) - chart of cumulative income for each asset. 
    Cumulative income depends on the price and dividend (coupon) yield reinvested every month. 
    The starting investment for each asset is 1000 in the base currency.  
    &NewLine;  
    **Rolling CAGR** (rolling Compound Annual Growth Rate) - chart of rolling annualized returns calculated 
    for a moving window (at least 1 year).  
    &NewLine;  
    **Rolling Real CAGR** - Inflation adjusted annualized returns (real CAGR) calculated 
    for a moving window (at least 1 year). Requires base currency inflation data.  
    &NewLine;  
    **Correlation Matrix** - show correlation matrix for the assets (heatmap win numbers).  
"""
)
al_options_window = dcc.Markdown(
    """
    Size of the moving window in years. Window size should be at least 1 year for CAGR.
"""
)
