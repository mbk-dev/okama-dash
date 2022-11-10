from common import settings as settings


def create_link(*, href, tickers_list, weights_list=None, benchmark=None, ccy, first_date, last_date, rebal=None):
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
    return new_url


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
