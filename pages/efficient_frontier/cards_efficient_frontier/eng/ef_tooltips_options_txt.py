from dash import dcc

ef_options_tooltip_ror = dcc.Markdown(
    """
    Select one or both plot types.

    **Efficient frontier** shows portfolios with the minimum risk for each selected level of return.

    **Pairwise efficiency frontiers** show efficient frontiers built separately for every pair of selected assets.
    """
)
ef_options_tooltip_mean_type = dcc.Markdown(
    """
    **Geometric mean** or Compound annual growth rate (CAGR) is the rate of return
    that would be required for an investment to grow from its initial to its
    final value, assuming all incomes were reinvested.

    **Arithmetic mean** is the annualized average return.
    """
)
ef_options_tooltip_cml = dcc.Markdown(
    """
    **Capital Market Line** (CML) is the tangent line drawn from the point of
    the risk-free asset (volatility is zero) to the point of tangency portfolio
    or Maximum Sharpe Ratio (MSR) point.  

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
ef_options_tooltip_mdp = dcc.Markdown(
    """
    Each point on the **Most diversified portfolios (MDP)** line is a portfolio with optimized "Diversification ratio"
    for a given return.
    """
)

ef_options_simulation = dcc.Markdown(
    """
    Fill the interior of the efficient frontier. The two methods are alternatives.

    **Monte Carlo** generates N random portfolios.

    **Grid** enumerates all portfolios on a fixed weight step (minimum 10 %). The step is
    chosen automatically so the number of portfolios stays within a safe budget; you can
    also pick a coarser step manually.
    """
)

ef_options_transition_map = dcc.Markdown(
    """
    **Transition Map** shows the relation between asset weights and optimized portfolios risk (standard deviation).
    """
)
