# Import necessary libraries
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import base64
import json

# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container(
    [
        dbc.CardGroup(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3("Experiment Setup"),
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Experiment ID",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dbc.Input(
                                                    type="text",
                                                    id="experiment-id",
                                                    placeholder="Unique identifier for the experiment",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Experiment Name",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dbc.Input(
                                                    type="text",
                                                    id="experiment-name",
                                                    placeholder="Enter experiment name",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Date and Time",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dbc.Input(
                                                    type="datetime-local",
                                                    id="experiment-datetime",
                                                    placeholder="Start date and time",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Experiment Configuration",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dcc.Upload(
                                                    id="upload-exp-config",
                                                    children=html.Div(
                                                        [
                                                            "Drag and Drop or ",
                                                            html.A("Select a File"),
                                                        ]
                                                    ),
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                        "margin": "10px",
                                                    },
                                                    multiple=False,
                                                    accept=".json",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Button(
                                        "Submit",
                                        id="submit-experiment",
                                        color="primary",
                                    ),
                                ]
                            ),
                            html.Div(id="output-exp-config"),
                        ]
                    ),
                    style={"width": "50%", "margin-right": "10px", "padding": "20px"},
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3("Reactor Setup"),
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Reactor ID",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dbc.Input(
                                                    type="text",
                                                    id="reactor-id",
                                                    placeholder="Unique identifier for the reactor",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Reactor Name",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dbc.Input(
                                                    type="text",
                                                    id="reactor-name",
                                                    placeholder="Enter reactor name",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Network ID (e.g., IP)",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dbc.Input(
                                                    type="text",
                                                    id="network-id",
                                                    placeholder="Enter network identifier",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Reactor Configuration",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Col(
                                                dcc.Upload(
                                                    id="upload-reactor-config",
                                                    children=html.Div(
                                                        [
                                                            "Drag and Drop or ",
                                                            html.A("Select a File"),
                                                        ]
                                                    ),
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                        "margin": "10px",
                                                    },
                                                    multiple=False,
                                                    accept=".json",
                                                ),
                                                width=8,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Button(
                                        "Submit", id="submit-reactor", color="primary"
                                    ),
                                ]
                            ),
                            html.Div(id="output-reactor-config"),
                        ]
                    ),
                    style={"width": "50%", "margin-left": "10px", "padding": "20px"},
                ),
            ],
            className="g-0",
        ),
    ],
    fluid=True,
    className="py-4",
)


# Callback to handle the upload of the experiment configuration file
@app.callback(
    Output("output-exp-config", "children"),
    [Input("upload-exp-config", "contents")],
    [State("upload-exp-config", "filename")],
)
def update_output_exp(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n) for c, n in zip(list_of_contents, list_of_names)
        ]
        return children


# Callback to handle the upload of the reactor configuration file
@app.callback(
    Output("output-reactor-config", "children"),
    [Input("upload-reactor-config", "contents")],
    [State("upload-reactor-config", "filename")],
)
def update_output_reactor(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n) for c, n in zip(list_of_contents, list_of_names)
        ]
        return children


def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        if "json" in filename:
            # Assume that the user uploaded a JSON file
            json_content = json.loads(decoded.decode("utf-8"))
            json_str = json.dumps(json_content, indent=2)
            return html.Div(
                [
                    html.H5(filename),
                    html.Pre(
                        json_str,
                        style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
                    ),
                ]
            )
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
