import json
import datetime
import psycopg2
from evoflow_ui.mqtt_cmd_handler import command_centre
from evoflow_utils.config import Config


def start_stop_pause_experiment(reactor_id: int, experiment_id: int, command: str):
    # first update status on db
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_HOST,
    )
    cursor = conn.cursor()
    # update
    cmd = f"UPDATE experiment SET status = '{command}' WHERE reactor_id = {reactor_id} and experiment_id = {experiment_id};"
    print(cmd)
    cursor.execute(cmd)
    conn.commit()
    cursor.close()
    conn.close()

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
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_HOST,
    )
    cursor = conn.cursor()
    experiment_id = cursor.execute(
        f"select max(experiment_id) FROM experiment where reactor_id = {reactor_id}"
    ).fetchone()
    print(f"max_experiment_id: {experiment_id}")

    # create a new experiment
    cursor.execute(
        f"""
        INSERT INTO experiment (experiment_id, reactor_id, name, timestamp, insert_at, status) 
        VALUES (
            {experiment_id + 1}, 
            {reactor_id}, 
            '{name}', 
            {int(datetime.date.now())}, 
            {datetime.date.now()}, 
            {'stop'}
            )
        """
    )
    conn.commit()

    # get the last exp_config_id
    exp_config_id = cursor.execute(
        "select max(exp_config_id) FROM exp_config"
    ).fetchone()

    # save the config
    cursor.execute(
        f"""
        INSERT INTO exp_config (exp_config_id, experiment_id, exp_config_json, timestamp, insert_at)
        VALUES (
            {exp_config_id + 1},
            {experiment_id},
            %s,
            {int(datetime.date.now())}, 
            {datetime.date.now()}, 
        )
        """,
        (json.dumps(experiment_config),),
    )
    conn.commit()
    cursor.close()
    conn.close()

    payload = {
        "reactor_id": reactor_id,
        "command": "new_experiment",
        "experiment_id": experiment_id,
        "experiment_config": experiment_config,
    }

    # command_centre().send_cmds(topic="commands/experiment", msg=json.dumps(payload))
    command_centre().send_cmds(topic="commands", msg=json.dumps(payload))

    return None
