from dash import dcc

compare_description_text = dcc.Markdown(
    """
    Compare Assets widget uses monthly **total return** historical data (adjusted close) to calculate risk and 
    return metrics for each asset.  

    Widget constructor can be set to calculate risk and return metrics in different **base currencies** 
    (default base currency is 'USD').
"""
)