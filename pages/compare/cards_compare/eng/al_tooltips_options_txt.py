from dash import dcc

al_options_tooltip_inflation = dcc.Markdown(
    """
    If enabled, inflation will be displayed on the chart.  

    However, with inflation turned on,   
    the chart statistics will not include last month data,   
    as inflation statistics are delayed.  
"""
)
al_options_tooltip_cagr = dcc.Markdown(
    """
    **Wealth Index** (Cumulative Wealth Index) - chart of cumulative income for each asset.
    Cumulative income depends on the price and dividend (coupon) yield reinvested every month. 
    The starting investment for each asset is 1000 in the base currency.  

    **Rolling CAGR** (rolling Compound Annual Growth Rate) - chart of rolling annualized returns calculated 
    for a moving window (at least 1 year).  

    **Rolling Real CAGR** - Inflation adjusted annualized returns (real CAGR) calculated 
    for a moving window (at least 1 year). Requires base currency inflation data.  

    **Correlation Matrix** - show correlation matrix for the assets (heatmap with numbers).
"""
)
al_options_window = dcc.Markdown(
    """
    Size of the moving window in years. Window size should be at least 1 year for CAGR.
"""
)
