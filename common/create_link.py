import hashlib
from urllib.parse import quote

from common import settings as settings


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
    # Monte Carlo settings
    mc_number=None,
    mc_years=None,
    mc_dist=None,
    mc_backtest=None,
    # Monte Carlo distribution parameters
    mc_mu=None,
    mc_sigma=None,
    mc_ln_shape=None,
    mc_ln_scale=None,
    mc_t_df=None,
    mc_t_loc=None,
    mc_t_scale=None,
    mc_var=None,
) -> str:
    def _q(val) -> str:
        return quote(str(val), safe="")

    # Data-driven builder: (name, value, emit_rule)
    # emit_rule: "always" | "if_not_none" | ("skip_if_default", default_value)
    params = [
        ("benchmark", benchmark, "if_not_none"),
        ("weights", ",".join(str(w) for w in weights_list) if weights_list else None, "if_not_none"),
        ("rebal", rebal, "if_not_none"),
        ("initial_amount", initial_amount, "if_not_none"),
        ("cashflow", cashflow, "if_not_none"),
        ("discount_rate", discount_rate, "if_not_none"),
        ("symbol", symbol, "if_not_none"),
        ("abs_dev", abs_dev, "if_not_none"),
        ("rel_dev", rel_dev, "if_not_none"),
        ("cf_strategy", cf_strategy, ("skip_if_default", "indexation")),
        ("cf_freq", cf_freq, ("skip_if_default", "month")),
        ("cf_amount", cf_amount, "if_not_none"),
        ("cf_indexation", cf_indexation, "if_not_none"),
        ("cf_pct", cf_pct, "if_not_none"),
        ("vds_pct", vds_pct, "if_not_none"),
        ("vds_min", vds_min, "if_not_none"),
        ("vds_max", vds_max, "if_not_none"),
        ("vds_adj_mm", "0" if vds_adj_mm is not None and not vds_adj_mm else None, "if_not_none"),
        ("vds_floor", vds_floor, "if_not_none"),
        ("vds_ceil", vds_ceil, "if_not_none"),
        ("vds_adj_fc", "1" if vds_adj_fc else None, "if_not_none"),
        ("vds_indexation", vds_indexation, "if_not_none"),
        ("cwd_amount", cwd_amount, "if_not_none"),
        ("cwd_tr", cwd_tr, "if_not_none"),
        ("cf_ts", cf_ts, "if_not_none"),
        ("mc_number", mc_number, ("skip_if_default", 0)),
        ("mc_years", mc_years, ("skip_if_default", 10)),
        ("mc_dist", mc_dist, ("skip_if_default", "norm")),
        ("mc_backtest", mc_backtest, ("skip_if_default", "yes")),
        ("mc_mu", mc_mu, "emit_zero"),
        ("mc_sigma", mc_sigma, "emit_zero"),
        ("mc_ln_shape", mc_ln_shape, "emit_zero"),
        ("mc_ln_scale", mc_ln_scale, "emit_zero"),
        ("mc_t_df", mc_t_df, "emit_zero"),
        ("mc_t_loc", mc_t_loc, "emit_zero"),
        ("mc_t_scale", mc_t_scale, "emit_zero"),
        ("mc_var", mc_var, "emit_zero"),
    ]

    tickers_str = "tickers=" + ",".join(_q(s) for s in tickers_list)
    reset_href = href.split("?")[0]
    parts = [
        f"{reset_href}?{tickers_str}",
        f"ccy={_q(ccy)}",
        f"first_date={_q(first_date)}",
        f"last_date={_q(last_date)}",
    ]

    for name, value, rule in params:
        if rule == "if_not_none":
            if value is not None and value != "":
                should_quote = isinstance(value, str) and name not in {"weights", "vds_adj_mm", "vds_adj_fc"}
                parts.append(f"{name}={_q(value) if should_quote else value}")
        elif rule == "emit_zero":
            if value is not None and value != "":
                parts.append(f"{name}={value}")
        elif isinstance(rule, tuple) and rule[0] == "skip_if_default":
            default = rule[1]
            if value is not None and value != default:
                parts.append(f"{name}={_q(value) if isinstance(value, str) else value}")

    return "&".join(parts)


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
