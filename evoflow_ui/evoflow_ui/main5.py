# Import necessary libraries
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import base64
import json
import psycopg2


# Database connection function
def get_reactor_ids():
    conn = psycopg2.connect(
        dbname="postgres", user="postgres", password="postgres", host="10.66.4.7"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT reactor_id FROM reactor;")
    reactor_ids = cursor.fetchall()
    cursor.close()
    conn.close()
    return [str(id[0]) for id in reactor_ids]


# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H3("Select Reactor"),
                    dcc.Dropdown(
                        id="reactor-id-dropdown",
                        options=[{"label": i, "value": i} for i in get_reactor_ids()],
                        placeholder="Select a Reactor ID",
                    ),
                ]
            ),
            style={"margin-bottom": "20px"},
        ),
        dbc.CardGroup(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3("Experiment Setup"),
                            dbc.Button(
                                "New Experiment",
                                id="open-new-exp-modal",
                                color="primary",
                                className="mb-3",
                            ),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(
                                        dbc.ModalTitle("Create New Experiment")
                                    ),
                                    dbc.ModalBody(
                                        dbc.Form(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Label(
                                                            "Experiment Name",
                                                            className="col-form-label col-sm-4",
                                                        ),
                                                        dbc.Col(
                                                            dbc.Input(
                                                                type="text",
                                                                id="new-exp-name",
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
                                                            "Experiment Configuration",
                                                            className="col-form-label col-sm-4",
                                                        ),
                                                        dbc.Col(
                                                            dcc.Upload(
                                                                id="upload-new-exp-config",
                                                                children=html.Div(
                                                                    [
                                                                        "Drag and Drop or ",
                                                                        html.A(
                                                                            "Select a File"
                                                                        ),
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
                                            ]
                                        )
                                    ),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Save Experiment",
                                            id="save-new-exp",
                                            color="primary",
                                            n_clicks=0,
                                        )
                                    ),
                                ],
                                id="modal-new-exp",
                                is_open=False,
                            ),
                        ]
                    ),
                    style={"width": "50%", "margin-right": "10px", "padding": "20px"},
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3("Reactor Setup"),
                            # Existing Reactor Setup form elements...
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


@app.callback(
    Output("modal-new-exp", "is_open"),
    [Input("open-new-exp-modal", "n_clicks"), Input("save-new-exp", "n_clicks")],
    [State("modal-new-exp", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
