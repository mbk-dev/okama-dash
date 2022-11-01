from dash import dcc

ef_description_text = dcc.Markdown(
    """
    Efficient Frontier widget uses monthly total return historical data to calculate optimized portfolio points.
    Optimization uses annualized risk (annualized standard deviation) as an utility function. 
    
    Widget constructor has different types of portfolio rebalancing strategy (not rebalanced, monthly or annually rebalanced).  

    The rebalancing is the action of bringing the portfolio that has deviated away
    from original asset allocation back into line. After rebalancing the portfolio assets
    have target weights.  
"""
)
