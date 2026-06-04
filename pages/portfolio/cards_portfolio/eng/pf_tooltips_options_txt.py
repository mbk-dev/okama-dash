from dash import dcc


pf_rebalancing_period = dcc.Markdown(
    """
    Rebalancing period (rebalancing frequency)
    is predetermined time intervals when
    the investor rebalances the portfolio
    adjusting the assets weightings to
    the initial allocation.

    "No rebalancing (buy & hold)" means the weights change
     with asset prices without any limit.
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
    **Wealth Index** (Cumulative Wealth Index) - chart of cumulative income for the Portfolio and each asset.
    Cumulative income depends on the price and dividend (coupon) yield reinvested every month.
    The starting investment for the Portfolio and each asset is 1000 in the base currency.

    **Annual Return** - bar chart of the Portfolio calendar-year rate of return.
    Each year's value is calculated as CAGR (Compound Annual Growth Rate) from the monthly returns within the year.

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
    Initial investment (FV) amount at the start of the calculation period.
    For historical backtesting, this is the investment at the first date.
    For Monte Carlo simulations, this is the investment at the last date.
    Initial investment must be positive.
    """
)
pf_options_tooltip_cash_flow = dcc.Markdown(
    """
    Portfolio regular withdrawal or contribution size.
    Negative value corresponds to withdrawals. Positive value corresponds to contributions.
    Cash flow value is indexed each period by the indexation rate.
    The frequency of withdrawals or contributions is determined by the frequency parameter.
    """
)
pf_options_tooltip_discount_rate = dcc.Markdown(
    """
    Annual effective discount rate for portfolio cash flow, used to convert
    future values to present values. If not provided, the geometric mean (CAGR)
    of inflation is taken; for portfolios without inflation a default value is
    used. Enter as a percent, e.g. 5 = 5%.
    """
)
pf_options_tooltip_ticker = dcc.Markdown(
    """
    Text symbol of portfolio. It is similar to tickers but has namespace information.
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

pf_mc_tooltip_distribution_parameters = dcc.Markdown(
    """
    Parameters of the selected distribution of monthly rates of return,
    estimated automatically from the portfolio's return history.
    """
)
pf_mc_tooltip_var_level = dcc.Markdown(
    """
    VaR confidence level (1-99) at which the degrees of freedom (df) of
    Student's t-distribution are optimized to match the empirical VaR and CVaR
    of the portfolio's monthly returns (e.g. 5 = 5% left tail).
    """
)

# Cash flow strategy tooltips
pf_cf_strategy_type = dcc.Markdown(
    """
    Cash flow strategy determines how withdrawals
    or contributions are calculated over time.
    """
)

pf_cf_frequency = dcc.Markdown(
    """
    The frequency of regular withdrawals or contributions in the strategy:
    none (no regular cash flows), monthly, quarterly, half-year or yearly.
    """
)

pf_cf_rate = dcc.Markdown(
    """
    Effective annual withdrawal or contribution rate: the regular cash-flow
    amount converted to a percentage of the initial investment per year
    (amount × number of cash flows per year ÷ initial investment).
    Calculated automatically.
    """
)

pf_cf_indexation = dcc.Markdown(
    """
    Portfolio cash flow indexation rate: the regular amount is increased by
    this rate each period. If empty, the historical inflation rate (CAGR)
    is used.
    """
)

pf_cf_vds_indexation = dcc.Markdown(
    """
    Indexation rate for the minimum/maximum annual withdrawal and the
    floor/ceiling limits. If empty, the historical inflation rate (CAGR)
    is used.
    """
)

pf_cf_vds_min_max = dcc.Markdown(
    """
    Optional absolute minimum and maximum annual withdrawal amounts
    (positive values).
    """
)

pf_cf_vds_adjust_minmax = dcc.Markdown(
    """
    If enabled, the min/max annual withdrawal bounds are indexed using the
    indexation rate.
    """
)

pf_cf_vds_adjust_fc = dcc.Markdown(
    """
    If enabled, the previous year's withdrawal amount is indexed before
    applying the floor/ceiling limits.
    """
)

pf_cf_cwd_thresholds = dcc.Markdown(
    """
    Pairs of drawdown threshold and withdrawal reduction coefficient.
    Example: threshold 20, reduction 40 means if the portfolio drawdown
    exceeds 20%, the withdrawal is reduced by 40%.
    """
)

pf_cf_time_series = dcc.Markdown(
    """
    User-defined withdrawals and contributions: each entry is a date (YYYY-MM)
    and a cash flow amount. Negative value corresponds to withdrawals,
    positive to contributions.
    """
)

pf_cf_percentage = dcc.Markdown(
    """
    The percentage of withdrawals or contributions. The size of withdrawals
    or contributions is defined as a percentage of portfolio balance per year.
    Negative value corresponds to withdrawals, positive to contributions.
    Enter as a percent, e.g. -12 = -12% per year.
    """
)

pf_cf_vds_percentage = dcc.Markdown(
    """
    The percentage of withdrawals (no contributions are allowed in the VDS
    strategy); the value must be negative. The size of withdrawals is defined
    as a percentage of portfolio balance per year.
    """
)

pf_cf_vds_floor_ceiling = dcc.Markdown(
    """
    Year-to-year withdrawal change limits relative to the previous year's
    withdrawal. Example: Floor=-2.5, Ceiling=5 means the next withdrawal
    cannot be more than 2.5% lower or 5% higher than the previous year's
    withdrawal.
    """
)

pf_cf_cwd_amount = dcc.Markdown(
    """
    Portfolio regular withdrawal size before any drawdown-based reduction;
    must be negative. Cash flow value is indexed each period by the indexation
    rate. The frequency of withdrawals is determined by the frequency parameter.
    """
)
