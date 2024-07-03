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
    return new_url


def create_filename(
    *,
    tickers_list: list[str],
    ccy: str,
    first_date: str,
    last_date: str,
    # portfolio
    weights_list=None,
    rebal=None,
    initial_amount=None,
    cashflow=None,
    discount_rate=None,
    symbol=None,
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
    if rebal:
        file_name += f"-rb={rebal}"
    if initial_amount:
        file_name += f"-ia={initial_amount}"
    if cashflow:
        file_name += f"-cf={cashflow}"
    if discount_rate:
        file_name += f"-dr={discount_rate}"
    if symbol:
        file_name += f"-sb={symbol}"
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
