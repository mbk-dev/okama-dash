import dash_bootstrap_components as dbc
from dash import html

from pages.benchmark.cards_benchmark.eng.benchmark_description_txt import benchmark_description_text

card_benchmark_description = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Compare with Benchmark widget"),
                    html.Div(benchmark_description_text),
                ]
            )
        ]
    ),
    class_name="my-3",
)
