import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/analytics')

layout = html.Div(children=[
    html.H1(children='This is our Analytics page'),
    html.Div([
        "Select a city: ",
        dcc.RadioItems(['New York City', 'Montreal','San Francisco'],
                       'Montreal',
                       id='analytics-input')
    ]),
    html.Br(),
    html.Div(id='analytics-output'),
])


@callback(
    Output(component_id='analytics-output', component_property='children'),
    Input(component_id='analytics-input', component_property='value')
)
def update_city_selected(input_value):
    return f'You selected: {input_value}'
