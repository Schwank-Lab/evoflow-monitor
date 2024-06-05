# Import necessary libraries
import dash
from dash import html, dcc, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import base64
import json
import psycopg2

from evoflow_ui.mqtt_callbacks import (
    reactor_commands,
    save_experiment_command,
    update_experiment_command,
)


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
        "SELECT experiment_id, name, inserted_at, status FROM experiment WHERE reactor_id = %s and status = 'start';",
        (reactor_id,),
    )
    experiment_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if reactor_data and experiment_data:
        return reactor_data, experiment_data
    return (None, None), (None, None)


# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H3("Select Reactor"),
                    html.Div(
                        id="reactor-id-dropdown-parent",
                        children=[
                            dcc.Dropdown(
                                id="reactor-id-dropdown",
                            ),
                        ],
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
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Button(
                                                        "Start",
                                                        id="start-experiment",
                                                        color="success",
                                                        className="mt-3",
                                                        discabled=True,
                                                    ),
                                                    dbc.Button(
                                                        "Stop",
                                                        id="stop-experiment",
                                                        color="danger",
                                                        className="mt-3",
                                                        discabled=True,
                                                    ),
                                                    dbc.Button(
                                                        "Pause",
                                                        id="pause-experiment",
                                                        color="warning",
                                                        className="mt-3",
                                                        discabled=True,
                                                    ),
                                                ]
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Update Experiment",
                                                    id="update-experiment",
                                                    color="primary",
                                                    className="mt-3",
                                                ),
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Button(
                                                        "New Experiment",
                                                        id="open-new-exp-modal",
                                                        color="primary",
                                                        className="mt-3",
                                                    ),
                                                    dbc.Modal(
                                                        [
                                                            dbc.ModalHeader(
                                                                dbc.ModalTitle(
                                                                    "Create New Experiment"
                                                                )
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
                                                                    ],
                                                                ),
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
                                        ]
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


@app.callback(
    Output("reactor-id-dropdown", "options"),
    Input("reactor-id-dropdown-parent", "n_clicks"),
)
def get_reactor_ids(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    conn = psycopg2.connect(
        dbname="postgres", user="postgres", password="postgres", host="10.66.4.7"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT reactor_id, name FROM reactor ORDER BY name;")
    reactor_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"label": name, "value": str(id)} for id, name in reactor_data]


@app.callback(
    Output("modal-new-exp", "is_open"),
    [Input("open-new-exp-modal", "n_clicks"), Input("save-new-exp", "n_clicks")],
    [State("modal-new-exp", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Callback to handle saving a new experiment
@app.callback(
    Output("modal-new-exp", "is_open", allow_duplicate=True),
    Input("save-new-exp", "n_clicks"),
    State("new-exp-name", "value"),
    State("upload-new-exp-config", "contents"),
    State("reactor-id", "children"),
    prevent_initial_call=True,
)
def save_new_experiment(n_clicks, new_exp_name, contents, reactor_id):
    if n_clicks and new_exp_name and contents and reactor_id:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        experiment_config = json.loads(decoded.decode("utf-8"))

        save_experiment_command(
            reactor_id=reactor_id,
            name=new_exp_name,
            experiment_config=experiment_config,
        )

        # Update the UI with the new experiment data
        return not ctx.states["modal-new-exp.is_open"]

    return no_update


# Callback to handle the upload and update of the experiment configuration file
@app.callback(
    Output("output-exp-config", "children"),
    Input("update-experiment", "n_clicks"),
    State("upload-exp-config", "contents"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def update_experiment_config(n_clicks, contents, reactor_id, experiment_id):
    if n_clicks is not None and contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))
        update_experiment_command(
            reactor_id=reactor_id,
            experiment_id=experiment_id,
            experiment_config=json_data,
        )
        return html.Div(["Experiment configuration updated."])
    return no_update


# Callback to handle the upload and update of the reactor configuration file
@app.callback(
    Output("output-reactor-config", "children"),
    Input("update-reactor", "n_clicks"),
    State("upload-reactor-config", "contents"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def update_reactor_config(n_clicks, contents, reactor_id, experiment_id):
    if n_clicks is not None and contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))
        update_experiment_command(
            reactor_id=reactor_id,
            experiment_id=experiment_id,
            experiment_config=json_data,
        )

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
        return [no_update] * 7


# Callback for the Start button
@app.callback(
    Output("experiment-status", "children", allow_duplicate=True),
    Input("start-experiment", "n_clicks"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def start_experiment(n_clicks, reactor_id, experiment_id):
    print(f"{reactor_id}, {experiment_id}")
    if n_clicks:
        # Call the function or API to start the experiment
        # based on the experiment_id
        experiment_status = "Started"
        print("io" + experiment_status)
        reactor_commands(
            reactor_id=reactor_id, experiment_id=experiment_id, command="start"
        )
        print(experiment_status)
        return experiment_status
    return no_update


# Callback for the Stop button
@app.callback(
    Output("experiment-status", "children", allow_duplicate=True),
    Input("stop-experiment", "n_clicks"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def stop_experiment(n_clicks, reactor_id, experiment_id):
    if n_clicks:
        # Call the function or API to stop the experiment
        # based on the experiment_id
        experiment_status = "Stopped"
        reactor_commands(
            reactor_id=reactor_id, experiment_id=experiment_id, command="stop"
        )
        print(experiment_status)
        return experiment_status
    return no_update


# Callback for the Pause button
@app.callback(
    Output("experiment-status", "children", allow_duplicate=True),
    Input("pause-experiment", "n_clicks"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def pause_experiment(n_clicks, reactor_id, experiment_id):
    if n_clicks:
        # Call the function or API to pause the experiment
        # based on the experiment_id
        experiment_status = "Pausede"
        reactor_commands(
            reactor_id=reactor_id, experiment_id=experiment_id, command="pause"
        )
        print(experiment_status)
        return experiment_status
    return no_update


def main():
    app.run_server(debug=True, host="0.0.0.0", port=8181, use_reloader=True)


# Run the app
if __name__ == "__main__":
    main()
