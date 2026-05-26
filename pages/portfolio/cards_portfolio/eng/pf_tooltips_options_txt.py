from dash import dcc


pf_rebalancing_period = dcc.Markdown(
    """
    Rebalancing period (rebalancing frequency)
    is predetermined time intervals when
    the investor rebalances the portfolio
    adjusting the assets weightings to
    the initial allocation.

    "No rebalancing (buy & hold)" means the weights change
     with assets price without any limit.
    """
)

pf_rebal_abs_deviation = dcc.Markdown(
    """
    Absolute deviation threshold for asset weights.
    Rebalancing is triggered when any asset's weight
    deviates from target by more than this value.
    Example: 5 means rebalance if |actual - target| > 5%.
    Leave empty to ignore.
    """
)

pf_rebal_rel_deviation = dcc.Markdown(
    """
    Relative deviation threshold for asset weights.
    Rebalancing is triggered when any asset's weight
    deviates from target by more than this relative value.
    Example: 10 means rebalance if |actual/target - 1| > 10%.
    Leave empty to ignore.
    """
)

pf_options_tooltip_inflation = dcc.Markdown(
    """
    If enabled, inflation will be displayed on the chart.  

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

    **Rolling CAGR** (rolling Compound Annual Growth Rate) - chart of rolling annualized returns calculated 
    for a moving window (at least 1 year).  

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
    Portfolio initial investment FV (at "Last Date").
    """
)
pf_options_tooltip_cash_flow = dcc.Markdown(
    """
    Portfolio monthly cash flow FV (at last_date). Negative value corresponds to withdrawals. 
    Positive value corresponds to contributions. Cash flow value is indexed each month by discount rate.
    """
)
pf_options_tooltip_discount_rate = dcc.Markdown(
    """
    Cash flow discount rate required to calculate PV values. If not provided geometric mean of inflation is taken.
    For portfolios without inflation the default value from settings is used.
    """
)
pf_options_tooltip_ticker = dcc.Markdown(
    """
    Text symbol of portfolio. It is similar to tickers but have a namespace information.
    Portfolio symbol must end with .PF (all_weather_portfolio.PF). No spaces in ticker are allowed.
    """
)
# Monte Carlo parameters
pf_mc_tooltip_mc_number = dcc.Markdown(
    """
    Number of random wealth indexes to generate with Monte Carlo simulation.
    """
)
pf_mc_tooltip_forecast_period = dcc.Markdown(
    """
    Investment period length for new wealth indexes.
    """
)
pf_mc_tooltip_distribution = dcc.Markdown(
    """
    Distribution type for the rate of return time series.
    """
)
pf_mc_tooltip_backtest = dcc.Markdown(
    """
    Show historical wealth index in the chart or plot only Monte Carlo wealth indexes.
    """
)

# Cash flow strategy tooltips
pf_cf_strategy_type = dcc.Markdown(
    """
    Cash flow strategy determines how withdrawals
    or contributions are calculated over time.
    """
)

pf_cf_percentage = dcc.Markdown(
    """
    Fixed percentage of portfolio balance withdrawn or contributed per year.
    Negative = withdrawal, positive = contribution.
    Example: -12 means withdraw 12% of balance annually.
    """
)

pf_cf_vds_percentage = dcc.Markdown(
    """
    Base withdrawal percentage of portfolio balance per year.
    Must be negative or zero (withdrawals only).
    """
)

pf_cf_vds_floor_ceiling = dcc.Markdown(
    """
    Year-to-year withdrawal change limits relative to previous year.
    Floor: maximum allowed decrease (negative %).
    Ceiling: maximum allowed increase (positive %).
    Example: Floor=-2.5, Ceiling=5 means the next withdrawal
    cannot drop more than 2.5% or rise more than 5% vs last year.
    """
)

pf_cf_cwd_amount = dcc.Markdown(
    """
    Regular withdrawal amount before any drawdown-based reduction.
    Must be negative or zero (withdrawals only).
    """
)
