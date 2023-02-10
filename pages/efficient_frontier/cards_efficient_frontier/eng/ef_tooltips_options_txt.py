from dash import dcc

ef_options_tooltip_ror = dcc.Markdown(
    """
    **Geometric mean** or Compound annual growth rate (CAGR) is the rate of return 
    that would be required for an investment to grow from its initial to its
    final value, assuming all incomes were reinvested.  
    &NewLine;  
    **Arithmetic mean** - annualized mean return (arithmetic mean) for
    the rate of return monthly time series.
    """
)
ef_options_tooltip_cml = dcc.Markdown(
    """
    **Capital Market Line** (CML) is the tangent line drawn from the point of
    the risk-free asset (volatility is zero) to the point of tangency portfolio
    or Maximum Sharpe Ratio (MSR) point.  
    &NewLine;  
    The slope of the CML is the Sharpe ratio of the tangency portfolio."
    """
)
ef_options_tooltip_rf_rate = dcc.Markdown(
    """
    **Risk-free Rate of Return** is the theoretical rate of return of
    an investment with zero risk. Risk-free Rate is required to calculate
    Sharpe Ratio, Tangency portfolio and plot Capital Market Line (CML).
    """
)
ef_options_monte_carlo = dcc.Markdown(
    """
    Generate N random portfolios with Monte Carlo simulation. 
    Risk and Return are calculated for a set of random weights.
    """
)

ef_options_transition_map = dcc.Markdown(
    """
    Transition Map shows the relation between asset weights and optimized portfolios risk (standard deviation).
    """
)
