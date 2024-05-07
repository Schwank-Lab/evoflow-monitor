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


# Function to fetch reactor and experiment data
def get_reactor_experiment_data(reactor_id):
    conn = psycopg2.connect(
        dbname="postgres", user="postgres", password="postgres", host="10.66.4.7"
    )
    cursor = conn.cursor()
    # Fetch reactor details
    cursor.execute(
        "SELECT name, network_id FROM reactor WHERE reactor_id = %s;",
        (reactor_id,),
    )
    reactor_data = cursor.fetchone()
    # Fetch experiment details
    cursor.execute(
        "SELECT experiment_id, name, inserted_at, status FROM experiment WHERE reactor_id = %s;",
        (reactor_id,),
    )
    experiment_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if reactor_data and experiment_data:
        return reactor_data, experiment_data
    return (None, None), (None, None)


# Function to save JSON data to database
def save_json_to_db(table, json_data):
    conn = psycopg2.connect(
        dbname="postgres", user="postgres", password="postgres", host="10.66.4.7"
    )
    cursor = conn.cursor()
    # Assuming your table and JSON data structure allows this simple query; adjust as needed
    cursor.execute(
        f"UPDATE {table} SET config_data = %s WHERE id = %s;",
        (json.dumps(json_data), json_data["id"]),
    )
    conn.commit()
    cursor.close()
    conn.close()


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
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Experiment ID",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Label(
                                                id="experiment-id", className="col-sm-8"
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
                                            dbc.Label(
                                                id="experiment-name",
                                                className="col-sm-8",
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
                                            dbc.Label(
                                                id="experiment-datetime",
                                                className="col-sm-8",
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Status",
                                                className="col-form-label col-sm-4",
                                            ),
                                            dbc.Label(
                                                id="experiment-status",
                                                className="col-sm-8",
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
                                        "Update Experiment",
                                        id="update-experiment",
                                        color="primary",
                                        className="mt-3",
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
                                            dbc.Label(
                                                id="reactor-id", className="col-sm-8"
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
                                            dbc.Label(
                                                id="reactor-name", className="col-sm-8"
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
                                            dbc.Label(
                                                id="network-id", className="col-sm-8"
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
                                        "Update Reactor",
                                        id="update-reactor",
                                        color="primary",
                                        className="mt-3",
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


# Callback to handle the upload and update of the experiment configuration file
@app.callback(
    Output("output-exp-config", "children"),
    [Input("update-experiment", "n_clicks")],
    [State("upload-exp-config", "contents")],
)
def update_experiment_config(n_clicks, contents):
    if n_clicks is not None and contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))
        save_json_to_db("experiment", json_data)
        return html.Div(["Experiment configuration updated."])
    return no_update


# Callback to handle the upload and update of the reactor configuration file
@app.callback(
    Output("output-reactor-config", "children"),
    [Input("update-reactor", "n_clicks")],
    [State("upload-reactor-config", "contents")],
)
def update_reactor_config(n_clicks, contents):
    if n_clicks is not None and contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))
        save_json_to_db("reactor", json_data)
        return html.Div(["Reactor configuration updated."])
    return no_update


# Callback to update the forms based on the selected reactor ID
@app.callback(
    [
        Output("experiment-id", "children"),
        Output("experiment-name", "children"),
        Output("experiment-datetime", "children"),
        Output("experiment-status", "children"),
        Output("reactor-id", "children"),
        Output("reactor-name", "children"),
        Output("network-id", "children"),
    ],
    [Input("reactor-id-dropdown", "value")],
)
def update_forms(reactor_id):
    if reactor_id:
        reactor_data, experiment_data = get_reactor_experiment_data(reactor_id)
        return [
            experiment_data[0],  # experiment ID
            experiment_data[1],  # experiment Name
            experiment_data[2],  # experiment Date Time
            experiment_data[3],  # experiment Status
            reactor_id,  # Reactor ID (from dropdown, same as input)
            reactor_data[0],  # Reactor Name
            reactor_data[1],  # Network ID
        ]
    else:
        return [no_update] * 6


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
