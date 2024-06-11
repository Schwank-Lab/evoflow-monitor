import json
from evoflow_ui.db_callbacks import (
    save_experiment_command_on_db,
    update_experiment_command_on_db,
)
from evoflow_ui.mqtt_cmd_handler import command_centre


def start_stop_pause_experiment(reactor_id: int, experiment_id: int, command: str):
    # first update status on db
    update_experiment_command_on_db(reactor_id, experiment_id, command)

    payload = {
        "reactor_id": reactor_id,
        "command": command,
    }

    # command_centre().send_cmds(topic="commands/experiment", msg=json.dumps(payload))
    command_centre().send_cmds(topic="commands", msg=json.dumps(payload))

    return None


def update_experiment_command(
    reactor_id: int, experiment_id: int, experiment_config: json
):
    # first update status on db
<<<<<<< HEAD
    update_experiment_command_on_db(experiment_id, experiment_config)
=======
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_HOST,
    )
    cursor = conn.cursor()
    # update
    query = f"""
        UPDATE experiment_config SET exp_config_json = %s WHERE experiment_id = {experiment_id}
        """
    json_string = json.dumps(experiment_config)

    print(query)
    print(json_string)

    cursor.execute(query, (json_string,))
    conn.commit()
    cursor.close()
    conn.close()
>>>>>>> origin/main

    payload = {
        "reactor_id": reactor_id,
        "command": "update_experiment",
        "experiment_id": experiment_id,
        "experiment_config": experiment_config,
    }

    # command_centre().send_cmds(topic="commands/experiment", msg=json.dumps(payload))
    command_centre().send_cmds(topic="commands", msg=json.dumps(payload))

    return None


def new_experiment_command(reactor_id: int, name: str, experiment_config: json):
    print(f"reactor_id {reactor_id}")
    print(f"new_exp_name {name}")
    print(f"exp_config {json.dumps(experiment_config)}")  # first update status on db

    experiment_id = save_experiment_command_on_db(reactor_id, name, experiment_config)

    payload = {
        "reactor_id": reactor_id,
        "command": "new_experiment",
        "experiment_id": experiment_id,
        "experiment_config": experiment_config,
    }

    # command_centre().send_cmds(topic="commands/experiment", msg=json.dumps(payload))
    command_centre().send_cmds(topic="commands", msg=json.dumps(payload))

    return None
