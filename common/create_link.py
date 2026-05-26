import typing

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
    cf_indexation_type=None,
    cf_pct=None,
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
    vds_indexation_type=None,
    cwd_amount=None,
    cwd_tr=None,
    cwd_indexation_type=None,
    cf_ts=None,
) -> str:
    tickers_str = "tickers=" + ",".join(str(symbol) for symbol in tickers_list)
    reset_href = href.split("?")[0]
    new_url = f"{reset_href}?{tickers_str}"
    if benchmark:
        new_url += f"&benchmark={benchmark}"
    if weights_list:
        weights_str = "&weights=" + ",".join(str(w) for w in weights_list)
        new_url += weights_str
    new_url += f"&ccy={ccy}"
    new_url += f"&first_date={first_date}"
    new_url += f"&last_date={last_date}"
    if rebal:
        new_url += f"&rebal={rebal}"
    if initial_amount:
        new_url += f"&initial_amount={initial_amount}"
    if cashflow:
        new_url += f"&cashflow={cashflow}"
    if discount_rate:
        new_url += f"&discount_rate={discount_rate}"
    if symbol:
        new_url += f"&symbol={symbol}"
    # Rebalancing deviation
    if abs_dev is not None:
        new_url += f"&abs_dev={abs_dev}"
    if rel_dev is not None:
        new_url += f"&rel_dev={rel_dev}"
    # Cashflow strategy
    if cf_strategy and cf_strategy != "indexation":
        new_url += f"&cf_strategy={cf_strategy}"
    if cf_freq and cf_freq != "month":
        new_url += f"&cf_freq={cf_freq}"
    if cf_amount:
        new_url += f"&cf_amount={cf_amount}"
    if cf_indexation is not None:
        new_url += f"&cf_indexation={cf_indexation}"
    if cf_indexation_type and cf_indexation_type != "custom":
        new_url += f"&cf_indexation_type={cf_indexation_type}"
    if cf_pct:
        new_url += f"&cf_pct={cf_pct}"
    if vds_pct:
        new_url += f"&vds_pct={vds_pct}"
    if vds_min is not None:
        new_url += f"&vds_min={vds_min}"
    if vds_max is not None:
        new_url += f"&vds_max={vds_max}"
    if vds_adj_mm is not None and not vds_adj_mm:
        new_url += f"&vds_adj_mm=0"
    if vds_floor is not None:
        new_url += f"&vds_floor={vds_floor}"
    if vds_ceil is not None:
        new_url += f"&vds_ceil={vds_ceil}"
    if vds_adj_fc:
        new_url += f"&vds_adj_fc=1"
    if vds_indexation is not None:
        new_url += f"&vds_indexation={vds_indexation}"
    if vds_indexation_type and vds_indexation_type != "custom":
        new_url += f"&vds_indexation_type={vds_indexation_type}"
    if cwd_amount:
        new_url += f"&cwd_amount={cwd_amount}"
    if cwd_tr:
        new_url += f"&cwd_tr={cwd_tr}"
    if cwd_indexation_type and cwd_indexation_type != "custom":
        new_url += f"&cwd_indexation_type={cwd_indexation_type}"
    if cf_ts:
        new_url += f"&cf_ts={cf_ts}"
    return new_url


def create_filename(
    *,
    tickers_list: list[str],
    ccy: str,
    first_date: str,
    last_date: str,
    # portfolio
    weights_list=None,
    inflation: typing.Optional[bool] = None,
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
) -> str:
    """
    Create filename to serialize EF, Portfolio objects to pickle.
    """
    file_name = "-".join(str(symbol) for symbol in tickers_list)
    if weights_list:
        weights_str = "-w=" + ",".join(str(w) for w in weights_list)
        file_name += weights_str
    file_name += f"-ccy={ccy}"
    file_name += f"-fd={first_date}"
    file_name += f"-ld={last_date}"
    if inflation != None:
        file_name += f"-infl={str(inflation)}"
    if rebal:
        file_name += f"-rb={rebal}"
    if abs_dev is not None:
        file_name += f"-ad={abs_dev}"
    if rel_dev is not None:
        file_name += f"-rd={rel_dev}"
    if initial_amount:
        file_name += f"-ia={initial_amount}"
    if cashflow:
        file_name += f"-cf={cashflow}"
    if discount_rate:
        file_name += f"-dr={discount_rate}"
    if symbol:
        file_name += f"-sb={symbol}"
    if cf_strategy and cf_strategy != "indexation":
        file_name += f"-cs={cf_strategy}"
    if cf_freq and cf_freq != "month":
        file_name += f"-cfq={cf_freq}"
    return file_name + ".pkl"


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
