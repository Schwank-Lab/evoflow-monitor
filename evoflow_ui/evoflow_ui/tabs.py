from dash import Dash, dcc, html, Input, Output, callback

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1("EvoHub Control Centre"),
        dcc.Tabs(
            id="main_view",
            value="main_view",
            children=[
                dcc.Tab(label="Experiment Setup", value="exp_set"),
                dcc.Tab(label="Reactor Setup", value="react_set"),
            ],
        ),
        html.Div(id="tabs_contents"),
    ]
)


@callback(
    Output("tabs_contents", "children"),
    Input("main_view", "value"),
)
def render_content(tab):
    if tab == "exp_set":
        return html.Div(
            [
                html.H3("Experiment Setup"),  # Title
                dcc.Graph(
                    figure={"data": [{"x": [1, 2, 3], "y": [3, 1, 2], "type": "bar"}]}
                ),
            ]
        )
    elif tab == "react_set":
        return html.Div(
            [
                html.H3("Reactor Setup"),  # Title
                dcc.Graph(
                    id="graph-2-tabs-dcc",
                    figure={"data": [{"x": [1, 2, 3], "y": [5, 10, 6], "type": "bar"}]},
                ),
            ]
        )


if __name__ == "__main__":
    app.run(debug=True)
