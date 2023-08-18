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
    y_value = ef["Mean return"] if ef_options["plot_type"] == "Arithmetic" else ef["CAGR"]
    weights_array = np.stack([ef[n] for n in ef.columns[3:]], axis=-1)
    hovertemplate = "<b>Risk: %{x:.2f}%<br>Return: %{y:.2f}%</b>" + "<extra></extra>"
    fig = go.Figure(
        data=go.Scatter(
            x=ef["Risk"],
            y=y_value,
            customdata=weights_array,
            hovertemplate=hovertemplate,
            mode="lines",
            name=f"Efficient Frontier - {ef_options['plot_type']} mean",
        )
    )
    # CML line
    if ef_options["cml"] == "On":
        cagr_option = ef_options["plot_type"] == "Geometric"
        rf_rate = ef_options["rf_rate"]
        tg = ef_object.get_tangency_portfolio(cagr=cagr_option, rf_return=rf_rate / 100)
        weights_array = np.expand_dims(tg["Weights"], axis=0)
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
        [ror_df, ef_object.risk_annual],
        axis=1,
        join="outer",
        copy="false",
        ignore_index=False,
    )
    df *= 100
    df.rename(columns={0: "Return", 1: "Risk"}, inplace=True)
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
