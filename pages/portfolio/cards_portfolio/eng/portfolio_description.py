from dash import dcc

portfolio_description_text = dcc.Markdown(
    """
    Investment portfolio widget uses adjusted close monthly historical data to calculate risk and return metrics 
    for a combination of financial assets. Adjusted close reflects total return (price and dividend yield).  
    
    Portfolio constructor uses different types of rebalancing strategy.  
    
    The rebalancing is the action of bringing the portfolio that has deviated away
    from original asset allocation back into line. After rebalancing the portfolio assets
    have target weights.  
"""
)
