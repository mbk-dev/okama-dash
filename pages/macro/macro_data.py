"""Curated macro-series catalog for the Macro section.

Single source of truth for which okama DB series each macro page exposes,
their display labels, the inflation -> key-rate overlay mapping and per-page
defaults. Every symbol below was verified against the live okama database
(docs/superpowers/specs/2026-06-07-macro-section-design.md, section 2).
Stage 2 extends this file with deposit-rate and money-market groups.
"""

# NOTE: e2e tests (tests/e2e/test_macro_pages.py) assert exact trace counts on
# auto-render; update them when changing the length of any *_DEFAULTS list.

# /macro/inflation — INFL namespace, handled by ok.Inflation
INFLATION_SERIES = {
    "RUB.INFL": "Russia",
    "USD.INFL": "USA",
    "EUR.INFL": "EU",
    "GBP.INFL": "UK",
    "ILS.INFL": "Israel",
    "CNY.INFL": "China",
}
INFLATION_DEFAULTS = ["RUB.INFL", "USD.INFL", "EUR.INFL"]

# Inflation -> central-bank key rate overlay (spec 5.1; ECB rate is MRO by user decision)
INFLATION_TO_KEY_RATE = {
    "RUB.INFL": "RUS_CBR.RATE",
    "USD.INFL": "US_EFFR.RATE",
    "EUR.INFL": "EU_MRO.RATE",
    "GBP.INFL": "UK_BR.RATE",
    "ILS.INFL": "ISR_IR.RATE",
    "CNY.INFL": "CHN_LPR1.RATE",
}

# /macro/rates — RATE namespace, handled by ok.Rate. Key-rates group (see RATES_GROUPS below).
KEY_RATES_SERIES = {
    "RUS_CBR.RATE": "Bank of Russia key rate",
    "US_EFFR.RATE": "US Fed effective funds rate",
    "EU_MRO.RATE": "ECB main refinancing rate",
    "EU_DFR.RATE": "ECB deposit facility rate",
    "EU_MLR.RATE": "ECB marginal lending rate",
    "UK_BR.RATE": "Bank of England bank rate",
    "ISR_IR.RATE": "Bank of Israel interest rate",
    "CHN_LPR1.RATE": "China 1-year LPR",
    "CHN_LPR5.RATE": "China 5-year LPR",
}
RATES_DEFAULTS = ["RUS_CBR.RATE", "US_EFFR.RATE", "EU_MRO.RATE"]

# /macro/rates stage-2 groups. Display labels follow the DB names trimmed for
# the legend (full names verified in the live RATE namespace dump).
DEPOSIT_RATES_SERIES = {
    "RUS_RUB.RATE": "Max deposit rates (RUB)",
    "RUS_RUB_TOP10.RATE": "Max deposit rates TOP-10 (RUB)",
    "RUS_USD.RATE": "Max deposit rates (USD)",
    "RUS_EUR.RATE": "Max deposit rates (EUR)",
}
DEPOSIT_RATES_DEFAULTS = ["RUS_RUB_TOP10.RATE"]

# Money market RU: RUONIA family + base RUSFAR tenors. RT/compound/N variants,
# CNY/USD RUSFAR, RUSFARIND and RUSFAR2M are deliberately excluded (spec §2);
# the tenor list is a one-line edit here.
MONEY_MARKET_SERIES = {
    "RUONIA.RATE": "RUONIA",
    "RUONIA_AVG_1M.RATE": "RUONIA Average 1M",
    "RUONIA_AVG_3M.RATE": "RUONIA Average 3M",
    "RUONIA_AVG_6M.RATE": "RUONIA Average 6M",
    "RUSFAR.RATE": "RUSFAR ON",
    "RUSFAR1W.RATE": "RUSFAR 1W",
    "RUSFAR2W.RATE": "RUSFAR 2W",
    "RUSFAR1M.RATE": "RUSFAR 1M",
    "RUSFAR3M.RATE": "RUSFAR 3M",
}
MONEY_MARKET_DEFAULTS = ["RUONIA.RATE"]

# Group registry for the /macro/rates group selector: value -> (label, catalog, defaults).
RATES_GROUPS = {
    "key": ("Key rates", KEY_RATES_SERIES, RATES_DEFAULTS),
    "deposit": ("Deposit rates RU", DEPOSIT_RATES_SERIES, DEPOSIT_RATES_DEFAULTS),
    "mm": ("Money market RU", MONEY_MARKET_SERIES, MONEY_MARKET_DEFAULTS),
}

# Union catalog for figure legend labels regardless of the active group.
# Safe regardless of union order: the three groups share no symbols
# (guarded by test_groups_do_not_overlap).
ALL_RATES_SERIES = {**KEY_RATES_SERIES, **DEPOSIT_RATES_SERIES, **MONEY_MARKET_SERIES}


def rates_group_catalog(group: str | None) -> dict[str, str]:
    """Catalog of the requested rates group; unknown/None falls back to key rates."""
    return RATES_GROUPS.get(group, RATES_GROUPS["key"])[1]


# /macro/real-estate — RE namespace; real estate is an ASSET (ok.Asset/AssetList,
# not the macro classes): prices per m² in native RUB, currency-convertible.
RE_SERIES = {
    "MOW_PR.RE": "Moscow primary market",
    "MOW_SEC.RE": "Moscow secondary market",
    "RUS_PR.RE": "Russia primary market",
    "RUS_SEC.RE": "Russia secondary market",
}
RE_DEFAULTS = ["MOW_PR.RE", "MOW_SEC.RE"]

# /macro/cape10 — RATIO namespace, handled by ok.Indicator (all 26 DB countries)
CAPE10_SERIES = {
    "USA_CAPE10.RATIO": "USA",
    "EUR_CAPE10.RATIO": "Europe",
    "RUS_CAPE10.RATIO": "Russia",
    "CHN_CAPE10.RATIO": "China",
    "AUS_CAPE10.RATIO": "Australia",
    "BRA_CAPE10.RATIO": "Brazil",
    "CAN_CAPE10.RATIO": "Canada",
    "CHE_CAPE10.RATIO": "Switzerland",
    "DEU_CAPE10.RATIO": "Germany",
    "ESP_CAPE10.RATIO": "Spain",
    "FRA_CAPE10.RATIO": "France",
    "GBR_CAPE10.RATIO": "UK",
    "HKG_CAPE10.RATIO": "Hong Kong",
    "IND_CAPE10.RATIO": "India",
    "ISR_CAPE10.RATIO": "Israel",
    "ITA_CAPE10.RATIO": "Italy",
    "JPN_CAPE10.RATIO": "Japan",
    "KOR_CAPE10.RATIO": "Korea",
    "MEX_CAPE10.RATIO": "Mexico",
    "NLD_CAPE10.RATIO": "Netherlands",
    "POL_CAPE10.RATIO": "Poland",
    "SGP_CAPE10.RATIO": "Singapore",
    "SWE_CAPE10.RATIO": "Sweden",
    "TUR_CAPE10.RATIO": "Turkey",
    "TWN_CAPE10.RATIO": "Taiwan",
    "ZAF_CAPE10.RATIO": "South Africa",
}
CAPE10_DEFAULTS = ["USA_CAPE10.RATIO", "EUR_CAPE10.RATIO", "RUS_CAPE10.RATIO", "CHN_CAPE10.RATIO"]

# Default chart start for every macro page: covers RU history while skipping the
# hyperinflation 90s (a cumulative RUB chart from 1991 grows x168 928 and is unreadable).
MACRO_FIRST_DATE_DEFAULT = "2000-01"


def filter_known(symbols: list[str] | None, catalog: dict[str, str]) -> list[str]:
    """Keep only symbols present in the curated catalog (URL-prefill guard)."""
    if not symbols:
        return []
    return [s for s in symbols if s in catalog]
