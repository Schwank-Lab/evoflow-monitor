import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import base64
import json
import atexit

from evoflow_ui.db_callbacks import get_reactor_data, get_reactor_experiment_data
from evoflow_ui.mqtt_callbacks import (
    reset_stepper,
    start_stop_pause_experiment,
    new_experiment_command,
    update_experiment_command,
    get_reactor_state,
)
from evoflow_ui import mqtt_callbacks

external_stylesheets = [
    dbc.themes.VAPOR,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

new_exp_modal =  dbc.Modal(
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
                            ),
                        ),
                    ],
                    id="modal-new-exp",
                    is_open=False,
                )

update_exp_modal =  dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(
                                "Update Experiment"
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
                                                dbc.Label(
                                                    id="update-exp-name",
                                                    className="col-form-label col-sm-4",
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
                                                    id="upload-update-exp-config",
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
                                "Update Experiment",
                                id="update-exp",
                                color="primary",
                                n_clicks=0,
                            ),
                        ),
                    ],
                    id="modal-update-exp",
                    is_open=False,
                )
# Define the layout of the app
app.layout = dbc.Container(
    [
        dcc.Interval(
            id="interval-component",
            interval=2.5 * 1000,  # Update every 5 seconds
            n_intervals=0,
        ),
        dbc.Row(
            [
                dbc.Col(
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
                                                className="custom-dropdown",
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                            style={"margin-bottom": "20px"},
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="tabs",
                                                value="tab-1",
                                                className="custom-tabs",
                                                children=[
                                                    dcc.Tab(
                                                        label="Experiment Setup",
                                                        value="tab-1",
                                                        children=[
                                                            dbc.Form(
                                                                [
                                                                    html.Div(
                                                                        html.P(),
                                                                        style={
                                                                            "marginBottom": 10
                                                                        },
                                                                    ),
                                                                    html.H3(
                                                                        "Experiment Setup"
                                                                    ),
                                                                    dbc.Row(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
                                                                                    dbc.Row(
                                                                                        [
                                                                                            dbc.Label(
                                                                                                "Experiment ID",
                                                                                                className="col-form-label col-sm-4",
                                                                                            ),
                                                                                            dbc.Label(
                                                                                                id="experiment-id",
                                                                                                className="col-sm-8",
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
                                                                                            dbc.Col(
                                                                                                [
                                                                                                dbc.Button(
                                                                                                    "Update Experiment",
                                                                                                    id="open-update-exp-modal",
                                                                                                    color="primary",
                                                                                                    className="mt-3",
                                                                                                    disabled=True,
                                                                                                ),
                                                                                                update_exp_modal,
                                                                                                ]
                                                                                            ),
                                                                                            dbc.Col(
                                                                                                [
                                                                                                    dbc.Button(
                                                                                                        "New Experiment",
                                                                                                        id="open-new-exp-modal",
                                                                                                        color="primary",
                                                                                                        className="mt-3",
                                                                                                        disabled=True,
                                                                                                    ),
                                                                                                    new_exp_modal,
                                                                                                ]
                                                                                            ),
                                                                                        ]
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
                                                                                                        disabled=True,
                                                                                                    ),
                                                                                                ]),
                                                                                        dbc.Col([
                                                                                                    dbc.Button(
                                                                                                        "Stop",
                                                                                                        id="stop-experiment",
                                                                                                        color="danger",
                                                                                                        className="mt-3",
                                                                                                        disabled=True,
                                                                                                    )
                                                                                         ] ),
                                                                                         dbc.Col([

                                                                                                    dbc.Button(
                                                                                                        "Pause",
                                                                                                        id="pause-experiment",
                                                                                                        color="warning",
                                                                                                        className="mt-3",
                                                                                                        disabled=True,
                                                                                                    ),
                                                                                         ]),
                                                                                         ],
                                                                                    ),
                                                                                ],
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    dbc.Row(
                                                                        id="log-row",
                                                                        style={
                                                                            "display": "none"
                                                                        },
                                                                        children=[
                                                                            html.Div(
                                                                                html.P(),
                                                                                style={
                                                                                    "marginBottom": 20
                                                                                },
                                                                            ),
                                                                            html.H3(
                                                                                "Reactor Status ",
                                                                            ),
                                                                            dbc.Card(
                                                                                dbc.CardBody(
                                                                                    [
                                                                                        html.Div(
                                                                                            [
                                                                                                dcc.Textarea(
                                                                                                    id="textarea-mqtt-status",
                                                                                                    value="",
                                                                                                    className="custom-textarea",
                                                                                                    readOnly=True,
                                                                                                ),
                                                                                                html.Div(
                                                                                                    id="textarea-state-example-output",
                                                                                                    style={
                                                                                                        "whiteSpace": "pre-line"
                                                                                                    },
                                                                                                ),
                                                                                            ]
                                                                                        )
                                                                                    ],
                                                                                )
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        id="output-exp-config"
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                    dcc.Tab(
                                                        label="Reactor Setup",
                                                        value="tab-2",
                                                        children=[
                                                            dbc.Form(
                                                                [
                                                                    html.Div(
                                                                        html.P(),
                                                                        style={
                                                                            "marginBottom": 10
                                                                        },
                                                                    ),
                                                                    html.H3(
                                                                        "Reactor Info"
                                                                    ),
                                                                    dbc.Row(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
                                                                                    dbc.Row(
                                                                                        [
                                                                                            dbc.Label(
                                                                                                "Reactor ID",
                                                                                                className="col-form-label col-sm-4",
                                                                                            ),
                                                                                            dbc.Label(
                                                                                                id="reactor-id",
                                                                                                className="col-sm-8",
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
                                                                                                id="reactor-name",
                                                                                                className="col-sm-8",
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
                                                                                                id="network-id",
                                                                                                className="col-sm-8",
                                                                                            ),
                                                                                        ],
                                                                                        className="mb-3",
                                                                                    ),
                                                                                ]
                                                                            )
                                                                        )
                                                                    ),
                                                                    html.Div(
                                                                        html.P(),
                                                                        style={
                                                                            "marginBottom": 20
                                                                        },
                                                                    ),
                                                                    html.H3(
                                                                        "Arabinose Stepper Config "
                                                                    ),
                                                                    dbc.Row(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
                                                                                    dbc.Row(
                                                                                        [
                                                                                            dbc.Label(
                                                                                                "Stepper Volume",
                                                                                                id="stepper-label",
                                                                                                className="col-form-label col-sm-4",
                                                                                            ),
                                                                                            html.Div(
                                                                                                html.P(),
                                                                                                style={
                                                                                                    "marginBottom": 5
                                                                                                },
                                                                                            ),
                                                                                            dcc.Slider(
                                                                                                min=0,
                                                                                                max=1000,
                                                                                                step=5,
                                                                                                value=10,
                                                                                                id="stepper-slider",
                                                                                                marks=None,
                                                                                            ),
                                                                                        ]
                                                                                    ),
                                                                                    html.Div(
                                                                                        html.P(),
                                                                                        style={
                                                                                            "marginBottom": 5
                                                                                        },
                                                                                    ),
                                                                                    dbc.Row(
                                                                                        [
                                                                                            dbc.Col(
                                                                                                [
                                                                                                    dbc.Button(
                                                                                                        "Reset Fwd",
                                                                                                        id="reset-fwd",
                                                                                                        color="primary",
                                                                                                        className="mt-3",
                                                                                                        disabled=True,
                                                                                                    ),
                                                                                                    dbc.Button(
                                                                                                        "Reset Rev",
                                                                                                        id="reset-rev",
                                                                                                        color="primary",
                                                                                                        className="mt-3",
                                                                                                        disabled=True,
                                                                                                    ),
                                                                                                    dbc.Button(
                                                                                                        "Stop",
                                                                                                        id="stop-step",
                                                                                                        color="danger",
                                                                                                        className="mt-3",
                                                                                                        disabled=True,
                                                                                                    ),
                                                                                                ]
                                                                                            ),
                                                                                        ]
                                                                                    ),
                                                                                ]
                                                                            )
                                                                        )
                                                                    ),
                                                                    html.Div(
                                                                        html.P(),
                                                                        style={
                                                                            "marginBottom": 20
                                                                        },
                                                                    ),
                                                                    html.H3(
                                                                        "Reactor Config"
                                                                    ),
                                                                    dbc.Row(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
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
                                                                                    dbc.Button(
                                                                                        "Update Reactor",
                                                                                        id="update-reactor",
                                                                                        color="primary",
                                                                                        className="mt-3",
                                                                                        disabled=True,
                                                                                    ),
                                                                                    html.Div(
                                                                                        id="output-reactor-config"
                                                                                    ),
                                                                                ]
                                                                            ),
                                                                        )
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ]
                                    ),
                                ),
                                width=12,
                            ),
                            className="g-0",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    html.Div(
                        id="testme",
                        children=[
                            html.Img(
                                src="./assets/Asset 1.png",
                                style={
                                    "width": "100%",
                                    "height": "700px",
                                    "border": "none",
                                },
                            )
                        ],
                    ),
                    width=6,
                ),
            ],
            className="g-0",
        ),
    ],
    fluid=True,
    className="py-4",
)


@app.callback(
    Output("textarea-mqtt-status", "value"),
    Input("interval-component", "n_intervals"),
    State("reactor-id", "children"),
)
def print_reactor_status(n_intevarls, reactor_id):
    if reactor_id is None: 
        return ""
    reactor_state =  get_reactor_state(int(reactor_id))
    if reactor_state is None:
        return "No data available"
    return '\n'.join([f'{key}:\t\t{value}' for key, value in reactor_state.items()])


@app.callback(
    [Output("log-row", "style")],
    [Input("reactor-id-dropdown", "value")],
    [
        State("log-row", "style"),
    ],
    prevent_initial_call=True,
)
def show_experiment_staus(reactor_id, style):
    print(f"show_experiment: {reactor_id}")
    print(f"style: {style}")
    if reactor_id is None:
        raise PreventUpdate

    if reactor_id and style and style.get("display") == "none":
        return [{"display": "block"}]

    if reactor_id and style and style.get("display") == "block":
        return [{"display": "block"}]

    return [{"display": "none"}]


@app.callback(
    Output("testme", "children"),
    [
        Input("reactor-name", "children"),
        Input("experiment-name", "children"),
    ],
    prevent_initial_call=True,
)
def create_iframe_url(reactor_name, experiment_name):
    print(f"io : {reactor_name}")
    print(experiment_name)
    if reactor_name and experiment_name:
        return html.Iframe(
            id="iframe",
            src=(
                "http://10.66.4.7:3000/dashboard/snapshot/LR1PWU9y4wZVg3kTehNY2Avek34piR3U"
                f"?reactor_name={reactor_name}"
                f"&experiment_name={experiment_name}"
                "&update_interval=30s"
                # "&kiosk"
            ),
            style={
                "width": "100%",
                "height": "900px",
                "border": "none",
            },
        )
    return html.Img(
        src="./assets/Asset 1.png",
        style={
            "width": "100%",
            "height": "700px",
            "border": "none",
        },
    )


@app.callback(
    Output("reactor-id-dropdown", "options"),
    Input("reactor-id-dropdown-parent", "n_clicks"),
)
def get_reactor_ids(n_clicks):
    reactor_data = get_reactor_data()
    return [{"label": name, "value": str(id)} for id, name in reactor_data]


@app.callback(
    Output("modal-new-exp", "is_open"),
    [Input("open-new-exp-modal", "n_clicks"), Input("save-new-exp", "n_clicks")],
    [State("modal-new-exp", "is_open")],
)
def toggle_new_experiment_modal(open_new_exp_modal, save_new_exp, is_open):
    print('Toggle new experiment modal')
    if open_new_exp_modal:
        return True
    elif save_new_exp:
        return False
    else:
        return is_open 
    

@app.callback(
    Output("modal-update-exp", "is_open"),
    [Input("open-update-exp-modal", "n_clicks"), Input("update-exp", "n_clicks")],
    [State("modal-update-exp", "is_open")],
)
def toggle_update_experiment_modal(open_update_exp_modal, update_exp, is_open):
    print('Toggle new experiment modal')
    if open_update_exp_modal:
        return True
    elif update_exp:
        return False
    else:
        return is_open 
    

@app.callback(
    [Output("open-update-exp-modal", "disabled")],
    [State("reactor-id", "children")],
    [Input("experiment-status", "children")],
    prevent_initial_call="initial_duplicate",
)
def enbale_update_experiment(reactor_id, experiment_status):
    print('Experiment status updated, new status = ', experiment_status)
    return [not reactor_id or experiment_status in {None, 'start', 'stop'}]

@app.callback(
    [
        Output("upload-new-exp-config", "children", allow_duplicate=True),
    ],
    Input("upload-new-exp-config", "contents"),
    State("upload-new-exp-config", "filename"),
    prevent_initial_call="initial_duplicate",
)
def on_upload_new_experiment_config(contents, filename):
    print(f'Uploaded new experiment config: {filename}')
    if contents is not None:
        return [
            html.Div(
                [
                    html.I(className="fas fa-file"),  # FontAwesome file icon
                    html.Span(f" {filename}"),
                ]
            ),
        ]
    return [no_update]


@app.callback(
    [Output("open-new-exp-modal", "disabled")],
    [State("reactor-id", "children")],
    [Input("experiment-status", "children")],
    prevent_initial_call="initial_duplicate",
)
def enbale_create_new_experiment(reactor_id, experiment_status):
    print('Experiment status updated, new status = ', experiment_status)
    return [not reactor_id or experiment_status == 'start' or experiment_status == 'pause']


# Callback to handle saving a new experiment
@app.callback(
    Output("modal-new-exp", "is_open", allow_duplicate=True),
    Input("save-new-exp", "n_clicks"),
    State("new-exp-name", "value"),
    State("upload-new-exp-config", "contents"),
    State("reactor-id", "children"),
    State("modal-new-exp", "is_open"),
    prevent_initial_call=True,
)
def save_new_experiment(n_clicks, new_exp_name, contents, reactor_id, is_open):
    if n_clicks and new_exp_name and contents and reactor_id:
        print('Saving new experiment')
        print('Experiment config:', contents)
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        experiment_config = json.loads(decoded.decode("utf-8"))

        new_experiment_command(
            reactor_id=reactor_id,
            name=new_exp_name,
            experiment_config=experiment_config,
        )
        return False

    return is_open


# Callback to handle the upload and update of the experiment configuration file
@app.callback(
    Output("modal-update-exp", "is_open", allow_duplicate=True),
    Input("update-exp", "n_clicks"),
    State("upload-update-exp-config", "contents"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    State("modal-update-exp", "is_open"),
    prevent_initial_call=True,
)
def update_experiment_config(n_clicks, contents, reactor_id, experiment_id, is_open):
    if n_clicks is not None and contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))
        update_experiment_command(
            reactor_id=reactor_id,
            experiment_id=experiment_id,
            experiment_config=json_data,
        )
        return False
    return is_open


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
        Output("update-exp-name", "children"),
        Output("experiment-datetime", "children"),
        Output("experiment-status", "children"),
        Output("reactor-id", "children"),
        Output("reactor-name", "children"),
        Output("network-id", "children"),
        Output("start-experiment", "disabled"),
        Output("pause-experiment", "disabled"),
        Output("stop-experiment", "disabled"),
        Output("reset-fwd", "disabled"),
        Output("reset-rev", "disabled"),
        Output("stop-step", "disabled"),
    ],
    [Input("reactor-id-dropdown", "value"), Input("save-new-exp", "n_clicks")],
)
def update_forms(reactor_id, n_clicks):
    print("Selected reactor id: ", reactor_id)
    if reactor_id:
        print('Fetching reactor and experiment data')
        reactor_data, experiment_data = get_reactor_experiment_data(reactor_id)
        print('Reactor data received:',  reactor_data)
        print('Experiment data received:', experiment_data)
        exp_id, exp_name, exp_start, exp_status = experiment_data
        exp_id = exp_id if exp_id else "N/A"
        reactor_name, reactor_ip = reactor_data
        return [
            exp_id,  
            exp_name,
            exp_name,  # update experiment name
            exp_start,  # experiment Date Time
            exp_status,  # experiment Status
            reactor_id,  # Reactor ID (from dropdown, same as input)
            reactor_name,
            reactor_ip,  
            not exp_name, # disable start button
            not exp_name, # disable pause button
            not exp_name, # disable stop button
            not reactor_name,  # disable stepper fwd
            not reactor_name,  # disable stepper rev
            not reactor_name,  # disable stepper stop
        ]
    else:
        return [no_update] * 14


# Callback for the Start button
@app.callback(
    [
        Output("experiment-status", "children", allow_duplicate=True),
        Output("open-new-exp-modal", "disabled", allow_duplicate=True),
    ],
    Input("start-experiment", "n_clicks"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def start_experiment(n_clicks, reactor_id, experiment_id):
    if n_clicks:
        experiment_status = "start"
        start_stop_pause_experiment(
            reactor_id=reactor_id, experiment_id=experiment_id, command="start"
        )
        return [experiment_status, True]
    return no_update


# Callback for the Stop button
@app.callback(
    [
        Output("experiment-status", "children", allow_duplicate=True),
        Output("open-new-exp-modal", "disabled", allow_duplicate=True),
    ],
    Input("stop-experiment", "n_clicks"),
    State("reactor-id", "children"),
    State("experiment-id", "children"),
    prevent_initial_call=True,
)
def stop_experiment(n_clicks, reactor_id, experiment_id):
    if n_clicks:
        experiment_status = "stop"
        start_stop_pause_experiment(
            reactor_id=reactor_id, experiment_id=experiment_id, command="stop"
        )
        return [experiment_status, False]
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
        experiment_status = "pause"
        start_stop_pause_experiment(
            reactor_id=reactor_id, experiment_id=experiment_id, command="pause"
        )
        return experiment_status
    return no_update


@app.callback(Output("stepper-label", "children"), Input("stepper-slider", "value"))
def update_stepper_target_volume(value):
    return 'Stepper Volume ("{}")'.format(value)


# Callback for the reset stepper fwd
@app.callback(
    [
        State("reactor-id", "children"),
        Input("stepper-slider", "value"),
        Input("reset-fwd", "n_clicks"),
    ]
)
def reset_stepper_fwd(reactor_id, stepper_volume, n_clicks):
    if n_clicks:
        reset_stepper(reactor_id, "stepper_forward", stepper_volume)

    return no_update


# Callback for the reset stepper reverse
@app.callback(
    [
        State("reactor-id", "children"),
        Input("stepper-slider", "value"),
        Input("reset-rev", "n_clicks"),
    ]
)
def reset_stepper_reverse(reactor_id, stepper_volume, n_clicks):
    if n_clicks:
        reset_stepper(reactor_id, "stepper_reverse", stepper_volume)

    return no_update


# Callback for the reset stepper stop
@app.callback([State("reactor-id", "children"), Input("stop-step", "n_clicks")])
def reset_stepper_stop(reactor_id, n_clicks):
    if n_clicks:
        reset_stepper(reactor_id, "stepper_stop")

    return no_update

@atexit.register
def disconnect_from_mqtt():
    print('App: disconnecting from mqtt client')
    mqtt_callbacks.mqtt_client.stop()


def main():
    mqtt_callbacks.mqtt_client.connect()
    app.run_server(
        debug=True,
        host="0.0.0.0",
        port=8181,
        use_reloader=True,
    )


# Run the app
if __name__ == "__main__":
    main()
