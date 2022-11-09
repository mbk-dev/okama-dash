from dash import dcc

benchmark_description_text = dcc.Markdown(
    """
    Benchmark widget uses monthly **total return** historical data (adjusted close) to compare the performance 
    of assets with a benchmark (stock index or asset).    

    Available charts:  
     
    - Tracking Difference  
    - Tracking Error
    - Correlation
    - Beta coefficient
"""
)
