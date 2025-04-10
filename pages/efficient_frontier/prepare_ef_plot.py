import numpy as np
import okama
import pandas as pd

from plotly import graph_objects as go
import plotly.express as px


def prepare_transition_map(ef: pd.DataFrame):
    risk_return_columns = ("Risk", "Mean return", "CAGR")
    y_columns = [column for column in ef.columns if column not in risk_return_columns]
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


def prepare_ef(ef: pd.DataFrame, ef_object: okama.EfficientFrontier, ef_options: dict):
    y_column = "Mean return" if ef_options["plot_type"] == "Arithmetic" else "CAGR"
    weights_array = np.stack([ef[n] for n in ef.columns[3:]], axis=-1)
    hovertemplate = "<b>Return: %{y:.2f}%<br>Risk: %{x:.2f}%</b>" + "<extra></extra>"
    fig = go.Figure(
        data=go.Scatter(
            x=ef["Risk"],
            y=ef[y_column],
            customdata=weights_array,
            hovertemplate=hovertemplate,
            mode="lines",
            name=f"Efficient Frontier - {ef_options['plot_type']} mean",
        )
    )
    # MDP frontier
    if ef_options["mdp"] == "On":
        mdp_frontier = ef_object.mdp_points * 100
        # TODO: add Diversification Ratio to hovertemplate
        # hovertemplate = "<b>Risk: %{x:.2f}%<br>Return: %{y:.2f}%<br>Diversification Ratio:%{text:.2f}</b>" + "<extra></extra>"
        weights_array = np.stack([mdp_frontier[n] for n in mdp_frontier.columns[3:]], axis=-1)
        fig.add_trace(
            go.Scatter(
                x=mdp_frontier["Risk"],
                y=mdp_frontier[y_column],
                customdata=weights_array,
                hovertemplate=hovertemplate,
                # text=[],
                mode="lines",
                name=f"Most diversified portfolios",
            )
        )
        # MPD portfolio
        mdp_portfolio = ef_object.get_most_diversified_portfolio()
        # TODO: add customdata with weights
        # weights_array_mdp = np.expand_dims(mdp_portfolio["Weights"], axis=0)
        fig.add_trace(
            go.Scatter(
                x=[mdp_portfolio['Risk'] * 100],
                y=[mdp_portfolio[y_column] * 100],
                # customdata=weights_array_mdp,
                hovertemplate=hovertemplate,
                mode="markers+text",
                text="MDP",
                textposition="top left",
                name="Most diversified portfolio (MDP)",
                marker=dict(size=8, color="grey"),
            )
        )
    # CML line
    if ef_options["cml"] == "On":
        cagr_option = "cagr" if ef_options["plot_type"] == "Geometric" else "mean_return"
        rf_rate = ef_options["rf_rate"]
        tg = ef_object.get_tangency_portfolio(rate_of_return=cagr_option, rf_return=rf_rate / 100)
        weights_array = np.expand_dims(tg["Weights"], axis=0) * 100
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
                text="MSR",
                textposition="top left",
                name="Tangency portfolio (MSR)",
                marker=dict(size=8, color="grey"),
            )
        )
    # Assets Risk-Return points
    ror_df = ef_object.mean_return if ef_options["plot_type"] == "Arithmetic" else ef_object.get_cagr()
    df = pd.concat(
        [ror_df, ef_object.risk_annual.iloc[-1]],
        axis=1,
        join="outer",
        copy="false",
        ignore_index=False,
    )
    df *= 100
    df.columns = ["Return", "Risk"]
    df.reset_index(drop=False, inplace=True)
    fig.add_trace(
        go.Scatter(
            x=df["Risk"],
            y=df["Return"],
            mode="markers+text",
            marker=dict(size=8, color="orange"),
            text=df.iloc[:, 0].to_list(),
            hovertemplate=hovertemplate,
            textposition="bottom right",
            name="Assets",
        )
    )
    # Monte-Carlo simulation
    if ef_options["n_monte_carlo"]:
        kind = "mean" if ef_options["plot_type"] == "Arithmetic" else "cagr"
        df = ef_object.get_monte_carlo(n=ef_options["n_monte_carlo"], kind=kind) * 100
        weights_array = np.stack([df[n] for n in df.columns[2:]], axis=-1)
        fig.add_trace(
            go.Scatter(
                x=df["Risk"],
                y=df["Return"] if ef_options["plot_type"] == "Arithmetic" else df["CAGR"],
                customdata=weights_array,
                hovertemplate=hovertemplate,
                mode="markers",
                name=f"Monte-Carlo Simulation",
            )
        )
    # X and Y titles
    fig.update_layout(
        height=800,
        xaxis_title="Risk (standard deviation)",
        yaxis_title="Rate of Return",
    )
    return fig
