from dash import dcc


pf_rebalancing_period = dcc.Markdown(
    """
    Rebalancing period (rebalancing frequency)  
    is predetermined time intervals when  
    the investor rebalances the portfolio  
    adjusting the assets weightings to  
    the initial allocation.  
    &NewLine;   
    "Not rebalanced" means the weights change  
     with assets price without any limit.
    """
)

pf_options_tooltip_inflation = dcc.Markdown(
    """
    If enabled, inflation will be displayed on the chart.  
    &NewLine;   
    However, with inflation turned on,   
    the chart statistics will not include last month data,   
    as inflation statistics are delayed.  
"""
)
pf_options_tooltip_cagr = dcc.Markdown(
    """
    **Wealth index** (Cumulative Wealth Index) - chart of cumulative income for the Portfolio and each asset. 
    Cumulative income depends on the price and dividend (coupon) yield reinvested every month. 
    The starting investment for the Portfolio and each asset is 1000 in the base currency.  
    &NewLine;  
    **Rolling CAGR** (rolling Compound Annual Growth Rate) - chart of rolling annualized returns calculated 
    for a moving window (at least 1 year).  
    &NewLine;  
    **Rolling Real CAGR** - Inflation adjusted annualized returns (real CAGR) calculated 
    for a moving window (at least 1 year). Requires base currency inflation data.
"""
)
pf_options_window = dcc.Markdown(
    """
    Size of the moving window in years. Window size should be at least 1 year for CAGR.
"""
)
pf_options_tooltip_initial_amount = dcc.Markdown(
    """
    Portfolio initial investment FV (at last date).
    """
)