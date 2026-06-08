import hashlib
from urllib.parse import quote

import pandas as pd

from common import settings as settings


# Strategy table: (primary flow value - zero/empty means "inactive", owned param names).
# cf_ts (custom one-off cash flows) is owned by every strategy: okama applies
# time_series_dic on top of any regular strategy.
_STRATEGY_PARAMS = {
    "indexation": ("cf_amount", ("cf_freq", "cf_amount", "cf_indexation", "cf_ts")),
    "percentage": ("cf_pct", ("cf_freq", "cf_pct", "cf_ts")),
    "vds": (
        "vds_pct",
        (
            "vds_pct",
            "vds_min",
            "vds_max",
            "vds_adj_mm",
            "vds_floor",
            "vds_ceil",
            "vds_adj_fc",
            "vds_indexation",
            "cf_ts",
        ),
    ),
    "cwd": ("cwd_amount", ("cf_freq", "cwd_amount", "cwd_tr", "cf_ts")),
    "time_series": ("cf_ts", ("cf_ts",)),
}


def scope_cashflow_params(
    cf_strategy: str,
    *,
    cf_freq=None,
    cf_amount=None,
    cf_indexation=None,
    cf_pct=None,
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
    cwd_amount=None,
    cwd_tr=None,
    cf_ts=None,
) -> dict:
    """
    Return cashflow params scoped to the active strategy only.

    Only the active strategy's params are preserved; all others are set to None.
    A strategy whose primary flow value is 0/None produces no cash flow and is
    treated as "no strategy" (everything None, including the returned
    "cf_strategy" key) — unless custom cash flows (cf_ts) are present, which
    keep the strategy active: indexation/cwd with zero amount, percentage/vds
    with zero percent, time_series with no entries.
    """
    result = {
        "cf_strategy": None,
        "cf_freq": None,
        "cf_amount": None,
        "cf_indexation": None,
        "cf_pct": None,
        "vds_pct": None,
        "vds_min": None,
        "vds_max": None,
        "vds_adj_mm": None,
        "vds_floor": None,
        "vds_ceil": None,
        "vds_adj_fc": None,
        "vds_indexation": None,
        "cwd_amount": None,
        "cwd_tr": None,
        "cf_ts": None,
    }

    values = {
        "cf_freq": cf_freq,
        "cf_amount": cf_amount,
        "cf_indexation": cf_indexation,
        "cf_pct": cf_pct,
        "vds_pct": vds_pct,
        "vds_min": vds_min,
        "vds_max": vds_max,
        "vds_adj_mm": vds_adj_mm,
        "vds_floor": vds_floor,
        "vds_ceil": vds_ceil,
        "vds_adj_fc": vds_adj_fc,
        "vds_indexation": vds_indexation,
        "cwd_amount": cwd_amount,
        "cwd_tr": cwd_tr,
        "cf_ts": cf_ts,
    }
    spec = _STRATEGY_PARAMS.get(cf_strategy)
    if spec is None:
        return result
    primary, owned = spec
    if values[primary] in (None, 0, "") and values["cf_ts"] in (None, ""):
        return result
    result["cf_strategy"] = cf_strategy
    for key in owned:
        result[key] = values[key]
    return result


def _quote_value(val) -> str:
    return quote(str(val), safe="")


# Param values that stay raw in the URL: comma/colon are legal in query strings
# (the tickers CSV proves it end-to-end) and keep pair values human-readable.
_UNQUOTED_PARAMS = {"weights", "vds_adj_mm", "vds_adj_fc", "cwd_tr", "cf_ts", "pf_tickers", "pf_weights"}


def _format_query_param(name, value, rule) -> str | None:
    """Format one query param per its emission rule; None = omit from the URL.

    Rules: "if_not_none" | "skip_if_zero" (0 means "unset" for cash-flow amounts)
    | ("skip_if_default", default) — equality covers numerics (1000.0 == 1000).
    Every rule treats "" as unset: a cleared dmc.NumberInput reports "" where
    dbc.Input reported None.
    """
    if rule == "if_not_none":
        if value is None or value == "":
            return None
        should_quote = isinstance(value, str) and name not in _UNQUOTED_PARAMS
        return f"{name}={_quote_value(value) if should_quote else value}"
    if rule == "skip_if_zero":
        if value in (None, "", 0):
            return None
        return f"{name}={value}"
    # ("skip_if_default", default)
    default = rule[1]
    if value is None or value == "" or value == default:
        return None
    return f"{name}={_quote_value(value) if isinstance(value, str) else value}"


def create_link(
    *,
    href,
    tickers_list,
    ccy,
    first_date,
    last_date,
    # portfolio
    weights_list=None,
    rebal=None,
    initial_amount=None,
    cashflow=None,
    discount_rate=None,
    symbol=None,
    # benchmark
    benchmark=None,
    # portfolio handoff group (issue #23): a bare rebalanced portfolio carried
    # to Compare/Benchmark as its own self-contained params
    pf_tickers=None,
    pf_weights=None,
    pf_rebal=None,
    pf_symbol=None,
    # rebalancing deviation
    abs_dev=None,
    rel_dev=None,
    # cashflow strategy
    cf_strategy=None,
    cf_freq=None,
    cf_amount=None,
    cf_indexation=None,
    cf_pct=None,
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
    cwd_amount=None,
    cwd_tr=None,
    cf_ts=None,
) -> str:
    # Compute current month for last_date default comparison
    today_str = pd.Timestamp.today().strftime("%Y-%m")

    # Data-driven builder: (name, value, emit_rule)
    # emit_rule: "if_not_none" | ("skip_if_default", default_value) | ("skip_if_zero")
    # Params are emitted in GROUPS so related settings sit together in the URL:
    # base (ccy/dates) -> portfolio identity (weights/symbol/benchmark) ->
    # rebalancing (rebal/abs_dev/rel_dev) -> cash flow (everything else).
    params = [
        ("ccy", ccy, ("skip_if_default", "USD")),
        ("first_date", first_date, ("skip_if_default", "2000-01")),
        ("last_date", last_date, ("skip_if_default", today_str)),
        ("pf_tickers", ",".join(_quote_value(s) for s in pf_tickers) if pf_tickers else None, "if_not_none"),
        # float(w) tolerates string weights from raw form values; :g strips the
        # trailing .0 of float store weights. Callers drop "" before this point.
        ("pf_weights", ",".join(f"{float(w):g}" for w in pf_weights) if pf_weights else None, "if_not_none"),
        ("pf_rebal", pf_rebal, ("skip_if_default", "month")),
        ("pf_symbol", pf_symbol, ("skip_if_default", "PORTFOLIO")),
        ("weights", ",".join(str(w) for w in weights_list) if weights_list else None, "if_not_none"),
        ("symbol", symbol, ("skip_if_default", "PORTFOLIO")),
        ("benchmark", benchmark, "if_not_none"),
        ("rebal", rebal, ("skip_if_default", "month")),
        ("abs_dev", abs_dev, "if_not_none"),
        ("rel_dev", rel_dev, "if_not_none"),
        ("initial_amount", initial_amount, ("skip_if_default", settings.INITIAL_INVESTMENT_DEFAULT)),
        ("cashflow", cashflow, "if_not_none"),
        ("discount_rate", discount_rate, "if_not_none"),
        ("cf_strategy", cf_strategy, ("skip_if_default", "indexation")),
        ("cf_freq", cf_freq, ("skip_if_default", "month")),
        ("cf_amount", cf_amount, "skip_if_zero"),
        ("cf_indexation", cf_indexation, "skip_if_zero"),
        ("cf_pct", cf_pct, "skip_if_zero"),
        ("vds_pct", vds_pct, "skip_if_zero"),
        ("vds_min", vds_min, "if_not_none"),
        ("vds_max", vds_max, "if_not_none"),
        ("vds_adj_mm", "0" if vds_adj_mm is not None and not vds_adj_mm else None, "if_not_none"),
        ("vds_floor", vds_floor, "if_not_none"),
        ("vds_ceil", vds_ceil, "if_not_none"),
        ("vds_adj_fc", "1" if vds_adj_fc else None, "if_not_none"),
        ("vds_indexation", vds_indexation, "if_not_none"),
        ("cwd_amount", cwd_amount, "skip_if_zero"),
        ("cwd_tr", cwd_tr, "if_not_none"),
        ("cf_ts", cf_ts, "if_not_none"),
    ]

    # tickers= is omitted for an empty list: handoff links to Compare/Benchmark
    # carry only the pf_* group, and "?tickers=&pf_tickers=..." would be noise.
    reset_href = href.split("?")[0]
    query_parts = []
    if tickers_list:
        query_parts.append("tickers=" + ",".join(_quote_value(s) for s in tickers_list))

    for name, value, rule in params:
        formatted = _format_query_param(name, value, rule)
        if formatted is not None:
            query_parts.append(formatted)

    return f"{reset_href}?{'&'.join(query_parts)}"


def compute_cashflow_hash(**params) -> str | None:
    filtered = {k: v for k, v in sorted(params.items()) if v is not None}
    if not filtered:
        return None
    raw = repr(filtered).encode()
    return hashlib.sha256(raw).hexdigest()[:12]


def create_filename(
    *,
    tickers_list: list[str],
    ccy: str,
    first_date: str,
    last_date: str,
    # portfolio
    weights_list=None,
    inflation: bool | None = None,
    rebal=None,
    initial_amount=None,
    cashflow=None,
    discount_rate=None,
    symbol=None,
    # rebalancing deviation
    abs_dev=None,
    rel_dev=None,
    # cashflow strategy
    cf_strategy=None,
    cf_freq=None,
    # cashflow params digest
    cashflow_hash: str | None = None,
) -> str:
    """
    Create filename to serialize EF, Portfolio objects to pickle.
    """
    # Data-driven builder: (suffix_template, value, rule)
    # rule: "if_not_none" | ("skip_if_default", default_value)
    parts = ["-".join(str(s) for s in tickers_list)]
    params = [
        ("w={}", ",".join(str(w) for w in weights_list) if weights_list else None, "if_not_none"),
        ("ccy={}", ccy, "always"),
        ("fd={}", first_date, "always"),
        ("ld={}", last_date, "always"),
        ("infl={}", inflation, "if_not_none"),
        ("rb={}", rebal, "if_not_none"),
        ("ad={}", abs_dev, "if_not_none"),
        ("rd={}", rel_dev, "if_not_none"),
        ("ia={}", initial_amount, "if_not_none"),
        ("cf={}", cashflow, "if_not_none"),
        ("dr={}", discount_rate, "if_not_none"),
        ("sb={}", symbol, "if_not_none"),
        ("cs={}", cf_strategy, ("skip_if_default", "indexation")),
        ("cfq={}", cf_freq, ("skip_if_default", "month")),
        ("cfh={}", cashflow_hash, "if_not_none"),
    ]

    for template, value, rule in params:
        if rule == "always":
            parts.append(template.format(value))
        elif rule == "if_not_none":
            if value is not None and value != "":
                parts.append(template.format(value))
        elif isinstance(rule, tuple) and rule[0] == "skip_if_default":
            default = rule[1]
            if value and value != default:
                parts.append(template.format(value))

    return "-".join(parts) + ".pkl"


def check_if_list_empty_or_big(tickers_list) -> bool:
    """
    Check if list is empty or larger than allowed.

    Conditions:
    - list of tickers is empty
    - number of tickers is more than allowed (in settings)
    """
    tickers_list = [i for i in tickers_list if i is not None]
    condition1 = len(tickers_list) == 0
    condition2 = len(tickers_list) > settings.ALLOWED_NUMBER_OF_TICKERS
    return condition1 or condition2
