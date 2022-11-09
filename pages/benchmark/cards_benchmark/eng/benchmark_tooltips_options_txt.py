from dash import dcc

benchmark_options_tooltip_plot = dcc.Markdown(
    """
    **Tracking difference** - the accumulated difference between the returns of a benchmark and those of 
    the ETF replicating it (could be mutual funds, or other types of assets).  
    &NewLine;  
    **Annualized Tracking difference** - annualized tracking difference time series values for the assets.  
    &NewLine;  
    **Annual Tracking difference (bars)** - tracking difference for each calendar year (bar chart).  
    &NewLine;  
    **Tracking Error** - tracking error time series for the rate of return of assets. Tracking error is defined as the 
    standard deviation of the difference between the returns of the asset and the returns of the benchmark.    
    &NewLine;  
    **Correlation** - expanding or rolling correlation with the benchmark time series for the assets.    
    &NewLine;  
    **Beta coefficient** - expanding or rolling beta coefficient time series for the assets.   
"""
)
benchmark_options_tooltip_type = dcc.Markdown(
    """
    **Expanding** chart shows in every point the statistic with all the data available up to that point.
    &NewLine;  
    **Rolling** chart shows in every point the statistic for the last N years (N is a rolling window size).
"""
)

benchmark_options_tooltip_window_size = dcc.Markdown(
    """
    Size of the moving window in years. Window size should be at least 1 year for CAGR.
"""
)
