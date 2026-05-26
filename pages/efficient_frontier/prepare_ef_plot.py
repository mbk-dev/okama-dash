import inspect
import itertools

import numpy as np
import okama
import pandas as pd

from plotly import graph_objects as go
import plotly.express as px

from common import cache
from pages.efficient_frontier.ef_cache import CACHE_TIMEOUT, load_ef_object

DERIVED_CACHE_VERSION = "ef-derived-v1"


def _normalize_plot_types(plot_type) -> list[str]:
    if plot_type is None:
        return []
    if isinstance(plot_type, str):
        return [plot_type]
    normalized = []
    for option in plot_type:
        if option not in normalized:
            normalized.append(option)
    return normalized


def _resolve_return_column(df: pd.DataFrame, return_type: str) -> str:
    if return_type == "Arithmetic":
        candidates = ("Mean return", "Return", "CAGR")
    else:
        candidates = ("CAGR", "Return", "Mean return")
    for column in candidates:
        if column in df.columns:
            return column
    raise KeyError("No return column found in DataFrame.")


def _get_asset_columns(df: pd.DataFrame, ef_object: okama.EfficientFrontier) -> list[str]:
    asset_columns = [symbol for symbol in ef_object.symbols if symbol in df.columns]
    if asset_columns:
        return asset_columns
    ignored_columns = {
        "Risk",
        "Mean return",
        "Return",
        "CAGR",
        "Diversification ratio",
        "Weights",
        "iterations",
        "Risk_monthly",
    }
    return [column for column in df.columns if column not in ignored_columns]


def _get_portfolio_weights_percent(portfolio: dict, symbols: list[str]) -> np.ndarray | None:
    if "Weights" in portfolio:
        return np.asarray(portfolio["Weights"], dtype=float) * 100
    if all(symbol in portfolio for symbol in symbols):
        return np.asarray([portfolio[symbol] for symbol in symbols], dtype=float) * 100
    return None


def _get_column_values(df: pd.DataFrame, candidates: tuple[str, ...]) -> list[float]:
    for column in candidates:
        if column in df.columns:
            return df[column].tolist()
    raise KeyError("No matching return column found in DataFrame.")


def _get_cached_return_values(payload: dict, return_type: str) -> list[float]:
    if return_type == "Arithmetic":
        return payload["mean_return"]
    return payload["cagr"]


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_pairwise_frontier_data_cached(cache_version: str, ef_cache_key: str) -> list[dict]:
    del cache_version
    ef_object = load_ef_object(ef_cache_key)
    pairwise_frontiers = []
    for pair_assets in itertools.combinations(ef_object.asset_obj_dict.values(), 2):
        pair_symbols = [asset.symbol for asset in pair_assets]
        pair_ef_object = _make_pairwise_ef_object(
            ef_object=ef_object,
            pair_assets=list(pair_assets),
        )
        pair_ef = pair_ef_object.ef_points * 100
        pair_asset_columns = _get_asset_columns(pair_ef, pair_ef_object)
        pair_weights = pair_ef[pair_asset_columns].to_numpy()
        weights_array = _expand_weights_to_full_universe(pair_weights, pair_asset_columns, ef_object.symbols)
        pairwise_frontiers.append(
            {
                "name": " / ".join(pair_symbols),
                "risk": pair_ef["Risk"].tolist(),
                "mean_return": _get_column_values(pair_ef, ("Mean return", "Return", "CAGR")),
                "cagr": _get_column_values(pair_ef, ("CAGR", "Return", "Mean return")),
                "weights": weights_array.tolist(),
            }
        )
    return pairwise_frontiers


def _get_pairwise_frontier_data(ef_cache_key: str) -> list[dict]:
    return _get_pairwise_frontier_data_cached(DERIVED_CACHE_VERSION, ef_cache_key)


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_mdp_frontier_data_cached(cache_version: str, ef_cache_key: str) -> dict:
    del cache_version
    ef_object = load_ef_object(ef_cache_key)
    mdp_frontier = ef_object.mdp_points * 100
    mdp_asset_columns = _get_asset_columns(mdp_frontier, ef_object)
    weights_array = mdp_frontier[mdp_asset_columns].to_numpy() if mdp_asset_columns else None
    return {
        "risk": mdp_frontier["Risk"].tolist(),
        "mean_return": _get_column_values(mdp_frontier, ("Mean return", "Return", "CAGR")),
        "cagr": _get_column_values(mdp_frontier, ("CAGR", "Return", "Mean return")),
        "weights": weights_array.tolist() if weights_array is not None else None,
    }


def _get_mdp_frontier_data(ef_cache_key: str) -> dict:
    return _get_mdp_frontier_data_cached(DERIVED_CACHE_VERSION, ef_cache_key)


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_mdp_portfolio_data_cached(cache_version: str, ef_cache_key: str) -> dict:
    del cache_version
    ef_object = load_ef_object(ef_cache_key)
    mdp_portfolio = ef_object.get_most_diversified_portfolio()
    mdp_weights = _get_portfolio_weights_percent(mdp_portfolio, ef_object.symbols)
    return {
        "risk": mdp_portfolio["Risk"] * 100,
        "mean_return": mdp_portfolio.get("Mean return", mdp_portfolio.get("Return")),
        "cagr": mdp_portfolio.get("CAGR", mdp_portfolio.get("Mean return")),
        "weights": mdp_weights.tolist() if mdp_weights is not None else None,
    }


def _get_mdp_portfolio_data(ef_cache_key: str) -> dict:
    return _get_mdp_portfolio_data_cached(DERIVED_CACHE_VERSION, ef_cache_key)


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_tangency_portfolio_data_cached(
    cache_version: str,
    ef_cache_key: str,
    return_type: str,
    rf_rate: float,
) -> dict:
    del cache_version
    ef_object = load_ef_object(ef_cache_key)
    cagr_option = "cagr" if return_type == "Geometric" else "mean_return"
    tg = ef_object.get_tangency_portfolio(rate_of_return=cagr_option, rf_return=rf_rate / 100)
    return {
        "risk": tg["Risk"] * 100,
        "rate_of_return": tg["Rate_of_return"] * 100,
        "weights": (np.asarray(tg["Weights"], dtype=float) * 100).tolist(),
    }


def _get_tangency_portfolio_data(ef_cache_key: str, return_type: str, rf_rate: float) -> dict:
    return _get_tangency_portfolio_data_cached(DERIVED_CACHE_VERSION, ef_cache_key, return_type, rf_rate)


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_monte_carlo_data_cached(
    cache_version: str,
    ef_cache_key: str,
    n_monte_carlo: int,
    return_type: str,
) -> dict:
    del cache_version
    ef_object = load_ef_object(ef_cache_key)
    df = ef_object.get_monte_carlo(n=n_monte_carlo) * 100
    mc_asset_columns = _get_asset_columns(df, ef_object)
    weights_array = df[mc_asset_columns].to_numpy() if mc_asset_columns else None
    return {
        "risk": df["Risk"].tolist(),
        "mean_return": _get_column_values(df, ("Mean return", "Return", "CAGR")),
        "cagr": _get_column_values(df, ("CAGR", "Return", "Mean return")),
        "weights": weights_array.tolist() if weights_array is not None else None,
    }


def _get_monte_carlo_data(ef_cache_key: str, n_monte_carlo: int, return_type: str) -> dict:
    return _get_monte_carlo_data_cached(
        DERIVED_CACHE_VERSION,
        ef_cache_key,
        n_monte_carlo,
        return_type,
    )


def _to_string_list(text) -> list[str]:
    if text is None:
        return []
    if isinstance(text, str):
        return [text]
    if isinstance(text, np.ndarray):
        return [str(value) for value in text.tolist()]
    if isinstance(text, (list, tuple, pd.Series)):
        return [str(value) for value in text]
    return [str(text)]


def _to_position_list(textposition, size: int) -> list[str]:
    if size == 0:
        return []
    if isinstance(textposition, str):
        return [textposition] * size
    if isinstance(textposition, np.ndarray):
        positions = textposition.tolist()
    elif isinstance(textposition, (list, tuple, pd.Series)):
        positions = list(textposition)
    else:
        positions = []
    if not positions:
        return ["middle center"] * size
    if len(positions) < size:
        positions.extend([positions[-1]] * (size - len(positions)))
    return [str(position) for position in positions[:size]]


def _estimate_horizontal_text_padding(fig: go.Figure, compact: bool = False) -> tuple[float, float]:
    x_values = []
    for trace in fig.data:
        trace_x = getattr(trace, "x", None)
        if trace_x is None:
            continue
        for value in np.asarray(trace_x, dtype=object).ravel():
            if pd.notna(value):
                x_values.append(float(value))

    if not x_values:
        return 0.0, 0.0

    x_min = min(x_values)
    x_max = max(x_values)
    x_span = max(x_max - x_min, max(abs(x_min), abs(x_max), 1.0) * 0.1)

    left_padding = 0.0
    right_padding = 0.0
    base_padding = x_span * (0.01 if compact else 0.02)
    char_padding = x_span * (0.004 if compact else 0.009)

    for trace in fig.data:
        texts = _to_string_list(getattr(trace, "text", None))
        if not texts:
            continue
        positions = _to_position_list(getattr(trace, "textposition", None), len(texts))
        for label, position in zip(texts, positions):
            label_padding = base_padding + char_padding * len(label)
            if "left" in position:
                left_padding = max(left_padding, label_padding)
            if "right" in position:
                right_padding = max(right_padding, label_padding)

    return left_padding, right_padding


def _update_xaxis_range_for_labels(fig: go.Figure, compact: bool = False) -> go.Figure:
    x_values = []
    for trace in fig.data:
        trace_x = getattr(trace, "x", None)
        if trace_x is None:
            continue
        for value in np.asarray(trace_x, dtype=object).ravel():
            if pd.notna(value):
                x_values.append(float(value))

    if not x_values:
        return fig

    x_min = min(x_values)
    x_max = max(x_values)
    x_span = max(x_max - x_min, max(abs(x_min), abs(x_max), 1.0) * 0.1)

    left_padding, right_padding = _estimate_horizontal_text_padding(fig, compact=compact)
    # Keep a small visual gap near chart edges even for traces without text labels.
    left_padding = max(left_padding, x_span * (0.02 if compact else 0.06))
    right_padding = max(right_padding, x_span * (0.01 if compact else 0.02))

    fig.update_xaxes(
        range=[x_min - left_padding, x_max + right_padding],
        automargin=True,
    )
    return fig


def _update_figure_layout(fig: go.Figure, compact: bool = False) -> go.Figure:
    _update_xaxis_range_for_labels(fig, compact=compact)
    fig.update_layout(
        height=800,
        xaxis_title="Risk (standard deviation)",
        yaxis_title="Rate of Return",
    )
    return fig


def compact_ef_for_small_screens(fig: go.Figure) -> go.Figure:
    for trace in fig.data:
        mode = getattr(trace, "mode", "") or ""
        if "text" in mode:
            trace.update(textposition="top center")
    return _update_figure_layout(fig, compact=True)


def _add_assets_trace(
    fig: go.Figure,
    ef_object: okama.EfficientFrontier,
    return_type: str,
    trace_name: str = "Assets",
):
    ror = ef_object.mean_return if return_type == "Arithmetic" else ef_object.get_cagr()
    ror_df = ror.iloc[-1] if isinstance(ror, pd.DataFrame) else ror
    df = pd.concat(
        [ror_df, ef_object.risk_annual.iloc[-1]],
        axis=1,
        join="outer",
        copy=False,
        ignore_index=False,
    )
    df *= 100
    df.columns = ["Return", "Risk"]
    df.reset_index(drop=False, inplace=True)
    assets_weights = np.eye(len(df)) * 100
    fig.add_trace(
        go.Scatter(
            x=df["Risk"],
            y=df["Return"],
            customdata=assets_weights,
            mode="markers+text",
            cliponaxis=False,
            marker=dict(size=8, color="orange"),
            text=df.iloc[:, 0].to_list(),
            hovertemplate="<b>Return: %{y:.2f}%<br>Risk: %{x:.2f}%</b><extra></extra>",
            textposition="bottom right",
            name=trace_name,
        )
    )


def _expand_weights_to_full_universe(
    weights_array: np.ndarray,
    asset_columns: list[str],
    all_symbols: list[str],
) -> np.ndarray:
    expanded_weights = np.zeros((len(weights_array), len(all_symbols)))
    symbol_to_index = {symbol: index for index, symbol in enumerate(all_symbols)}
    for column_index, symbol in enumerate(asset_columns):
        if symbol in symbol_to_index:
            expanded_weights[:, symbol_to_index[symbol]] = weights_array[:, column_index]
    return expanded_weights


def _make_pairwise_ef_object(
    ef_object: okama.EfficientFrontier,
    pair_assets: list,
) -> okama.EfficientFrontier:
    ef_kwargs = dict(
        ccy=ef_object.currency,
        first_date=ef_object.first_date,
        last_date=ef_object.last_date,
        inflation=hasattr(ef_object, "inflation"),
        full_frontier=True,
        n_points=ef_object.n_points,
    )
    ef_signature = inspect.signature(okama.EfficientFrontier)
    if "rebalancing_strategy" in ef_signature.parameters and hasattr(ef_object, "rebalancing_strategy"):
        ef_kwargs["rebalancing_strategy"] = ef_object.rebalancing_strategy
    return okama.EfficientFrontier(assets=pair_assets, **ef_kwargs)


def prepare_pairwise_ef(
    ef_object: okama.EfficientFrontier,
    return_type: str,
    include_assets: bool = True,
    ef_cache_key: str | None = None,
):
    hovertemplate = "<b>Return: %{y:.2f}%<br>Risk: %{x:.2f}%</b>" + "<extra></extra>"
    fig = go.Figure()
    if ef_cache_key:
        pairwise_frontiers = _get_pairwise_frontier_data(ef_cache_key)
    else:
        pairwise_frontiers = []
        for pair_assets in itertools.combinations(ef_object.asset_obj_dict.values(), 2):
            pair_symbols = [asset.symbol for asset in pair_assets]
            pair_ef_object = _make_pairwise_ef_object(
                ef_object=ef_object,
                pair_assets=list(pair_assets),
            )
            pair_ef = pair_ef_object.ef_points * 100
            pair_asset_columns = _get_asset_columns(pair_ef, pair_ef_object)
            pair_weights = pair_ef[pair_asset_columns].to_numpy()
            weights_array = _expand_weights_to_full_universe(pair_weights, pair_asset_columns, ef_object.symbols)
            pairwise_frontiers.append(
                {
                    "name": " / ".join(pair_symbols),
                    "risk": pair_ef["Risk"].tolist(),
                    "mean_return": _get_column_values(pair_ef, ("Mean return", "Return", "CAGR")),
                    "cagr": _get_column_values(pair_ef, ("CAGR", "Return", "Mean return")),
                    "weights": weights_array.tolist(),
                }
            )
    for pair_data in pairwise_frontiers:
        fig.add_trace(
            go.Scatter(
                x=pair_data["risk"],
                y=_get_cached_return_values(pair_data, return_type),
                customdata=pair_data["weights"],
                hovertemplate=hovertemplate,
                mode="lines",
                name=pair_data["name"],
            )
        )

    if include_assets:
        _add_assets_trace(fig, ef_object, return_type, trace_name="Assets")
    return _update_figure_layout(fig)


def prepare_transition_map(ef: pd.DataFrame):
    ignored_columns = {
        "Risk",
        "Mean return",
        "Return",
        "CAGR",
        "Diversification ratio",
        "Weights",
        "iterations",
        "Risk_monthly",
    }
    y_columns = [
        column for column in ef.columns
        if column not in ignored_columns and pd.api.types.is_numeric_dtype(ef[column])
    ]
    fig = px.line(
        ef,
        x=ef["Risk"],
        y=y_columns,
        height=800,
    )
    # X and Y titles
    fig.update_layout(
        xaxis_title="Risk (standard deviation)",
        yaxis_title="Weights",
        legend_title="Assets:",
    )
    # HoverTemplate
    fig.update_traces(hovertemplate=None)
    fig.update_layout(hovermode="x")
    return fig


def _prepare_single_ef(
    ef: pd.DataFrame,
    ef_object: okama.EfficientFrontier,
    ef_options: dict,
    fig: go.Figure | None = None,
    include_assets: bool = True,
    line_width: float = 2.0,
    ef_cache_key: str | None = None,
):
    return_type = ef_options["return_type"]
    y_column = _resolve_return_column(ef, return_type)
    ef_asset_columns = _get_asset_columns(ef, ef_object)
    weights_array = ef[ef_asset_columns].to_numpy()
    hovertemplate = "<b>Return: %{y:.2f}%<br>Risk: %{x:.2f}%</b>" + "<extra></extra>"
    fig = fig or go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ef["Risk"],
            y=ef[y_column],
            customdata=weights_array,
            hovertemplate=hovertemplate,
            mode="lines",
            name=f"Efficient Frontier - {return_type} mean",
            line=dict(width=line_width),
        )
    )
    # MDP frontier
    if ef_options["mdp"] == "On":
        if ef_cache_key:
            mdp_frontier_data = _get_mdp_frontier_data(ef_cache_key)
            mdp_weights_array = mdp_frontier_data["weights"]
        else:
            mdp_frontier = ef_object.mdp_points * 100
            mdp_frontier_data = {
                "risk": mdp_frontier["Risk"].tolist(),
                "mean_return": _get_column_values(mdp_frontier, ("Mean return", "Return", "CAGR")),
                "cagr": _get_column_values(mdp_frontier, ("CAGR", "Return", "Mean return")),
            }
            mdp_asset_columns = _get_asset_columns(mdp_frontier, ef_object)
            mdp_weights = mdp_frontier[mdp_asset_columns].to_numpy()
            mdp_weights_array = mdp_weights.tolist()
        # TODO: add Diversification Ratio to hovertemplate
        # hovertemplate = "<b>Risk: %{x:.2f}%<br>Return: %{y:.2f}%<br>Diversification Ratio:%{text:.2f}</b>" + "<extra></extra>"
        fig.add_trace(
            go.Scatter(
                x=mdp_frontier_data["risk"],
                y=_get_cached_return_values(mdp_frontier_data, return_type),
                customdata=mdp_weights_array,
                hovertemplate=hovertemplate,
                # text=[],
                mode="lines",
                name=f"Most diversified portfolios",
            )
        )
        # MPD portfolio
        mdp_portfolio = _get_mdp_portfolio_data(ef_cache_key) if ef_cache_key else None
        if mdp_portfolio is None:
            raw_mdp_portfolio = ef_object.get_most_diversified_portfolio()
            raw_mdp_weights = _get_portfolio_weights_percent(raw_mdp_portfolio, ef_object.symbols)
            mdp_portfolio = {
                "risk": raw_mdp_portfolio["Risk"] * 100,
                "mean_return": raw_mdp_portfolio.get("Mean return", raw_mdp_portfolio.get("Return")),
                "cagr": raw_mdp_portfolio.get("CAGR", raw_mdp_portfolio.get("Mean return")),
                "weights": raw_mdp_weights.tolist() if raw_mdp_weights is not None else None,
            }
        mdp_return = mdp_portfolio["mean_return"] if return_type == "Arithmetic" else mdp_portfolio["cagr"]
        if mdp_return is None:
            raise KeyError("No return value found for most diversified portfolio.")
        mdp_weights = mdp_portfolio["weights"]
        weights_array_mdp = [mdp_weights] if mdp_weights is not None else None
        fig.add_trace(
            go.Scatter(
                x=[mdp_portfolio["risk"]],
                y=[mdp_return * 100],
                customdata=weights_array_mdp,
                hovertemplate=hovertemplate,
                mode="markers+text",
                cliponaxis=False,
                text=["MDP"],
                textposition="top left",
                name="Most diversified portfolio (MDP)",
                marker=dict(size=8, color="grey"),
            )
        )
    # CML line
    if ef_options["cml"] == "On":
        rf_rate = ef_options["rf_rate"]
        if ef_cache_key:
            tg = _get_tangency_portfolio_data(ef_cache_key, return_type, rf_rate)
            weights_array = [tg["weights"]]
            x_cml, y_cml = [0, tg["risk"]], [rf_rate, tg["rate_of_return"]]
        else:
            cagr_option = "cagr" if return_type == "Geometric" else "mean_return"
            tg = ef_object.get_tangency_portfolio(rate_of_return=cagr_option, rf_return=rf_rate / 100)
            weights_array = (np.expand_dims(tg["Weights"], axis=0) * 100).tolist()
            x_cml, y_cml = [0, tg["Risk"] * 100], [rf_rate, tg["Rate_of_return"] * 100]
        fig.add_trace(
            go.Scatter(
                x=x_cml,
                y=y_cml,
                mode="lines",
                name="Capital Market Line (CML)",
                line=dict(width=0.5, color="green"),
            )
        )
        # Tangency portfolio
        fig.add_trace(
            go.Scatter(
                x=[x_cml[1]],
                y=[y_cml[1]],
                customdata=weights_array,
                hovertemplate=hovertemplate,
                mode="markers+text",
                cliponaxis=False,
                text="MSR",
                textposition="top left",
                name="Tangency portfolio (MSR)",
                marker=dict(size=8, color="grey"),
            )
        )
    if include_assets:
        _add_assets_trace(fig, ef_object, return_type, trace_name="Assets")
    # Monte-Carlo simulation
    if ef_options["n_monte_carlo"]:
        if ef_cache_key:
            mc_data = _get_monte_carlo_data(ef_cache_key, ef_options["n_monte_carlo"], return_type)
            mc_x = mc_data["risk"]
            mc_y = _get_cached_return_values(mc_data, return_type)
            weights_array = mc_data["weights"]
        else:
            df = ef_object.get_monte_carlo(n=ef_options["n_monte_carlo"]) * 100
            mc_y_column = _resolve_return_column(df, return_type)
            mc_asset_columns = _get_asset_columns(df, ef_object)
            weights_array = df[mc_asset_columns].to_numpy().tolist() if mc_asset_columns else None
            mc_x = df["Risk"].tolist()
            mc_y = df[mc_y_column].tolist()
        fig.add_trace(
            go.Scatter(
                x=mc_x,
                y=mc_y,
                customdata=weights_array,
                hovertemplate=hovertemplate,
                mode="markers",
                name=f"Monte-Carlo Simulation",
            )
        )
    return _update_figure_layout(fig)


def prepare_ef(
    ef: pd.DataFrame,
    ef_object: okama.EfficientFrontier,
    ef_options: dict,
    ef_cache_key: str | None = None,
):
    plot_types = _normalize_plot_types(ef_options.get("plot_type")) or ["Frontier"]
    return_type = ef_options.get("return_type", "Geometric")
    fig = go.Figure()

    if "Frontier" in plot_types:
        fig = _prepare_single_ef(
            ef,
            ef_object,
            {**ef_options, "return_type": return_type},
            fig=fig,
            include_assets="Pairwise" not in plot_types,
            line_width=4.0 if "Pairwise" in plot_types else 2.0,
            ef_cache_key=ef_cache_key,
        )

    if "Pairwise" in plot_types:
        pairwise_fig = prepare_pairwise_ef(
            ef_object,
            return_type=return_type,
            include_assets="Frontier" not in plot_types,
            ef_cache_key=ef_cache_key,
        )
        for trace in pairwise_fig.data:
            fig.add_trace(trace)

    if not any(getattr(trace, "name", None) == "Assets" for trace in fig.data):
        _add_assets_trace(fig, ef_object, return_type, trace_name="Assets")

    return _update_figure_layout(fig)
