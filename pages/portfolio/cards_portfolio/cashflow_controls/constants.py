"""Static option lists, descriptions and limits for the Cash Flow card."""

STRATEGY_OPTIONS = [
    {"label": "Fixed Amount (Indexation)", "value": "indexation"},
    {"label": "Fixed Percentage", "value": "percentage"},
    {"label": "Custom Time Series", "value": "time_series"},
    {"label": "Vanguard Dynamic Spending (VDS)", "value": "vds"},
    {"label": "Cut Withdrawals if Drawdown (CWD)", "value": "cwd"},
]

FIND_GOAL_OPTIONS = [
    {"label": "Keep purchasing power (PV)", "value": "maintain_balance_pv"},
    {"label": "Keep nominal balance (FV)", "value": "maintain_balance_fv"},
    {"label": "Survive N years", "value": "survival_period"},
]

FREQUENCY_OPTIONS = [
    {"label": "None", "value": "none"},
    {"label": "Monthly", "value": "month"},
    {"label": "Quarterly", "value": "quarter"},
    {"label": "Half-year", "value": "half-year"},
    {"label": "Yearly", "value": "year"},
]

STRATEGY_DESCRIPTIONS = {
    "indexation": "Regular withdrawals/contributions indexed by a fixed rate or inflation.",
    "percentage": "Withdrawals/contributions as a fixed percentage of portfolio balance.",
    "time_series": "User-defined cash flows with specific dates and amounts.",
    "vds": "Percentage-based withdrawals with floor/ceiling constraints and min/max bounds. Annual only.",
    "cwd": "Reduce withdrawals when portfolio drawdown exceeds thresholds.",
}

MAX_TIMESERIES_ENTRIES = 50

# Example entry shown when the Custom cash flows block opens empty in the
# time_series strategy (the block IS the strategy): one past-dated withdrawal
# the user can edit. Other strategies open the block with a blank row.
TS_DEFAULT_DATE = "2020-01"
TS_DEFAULT_AMOUNT = -1000
