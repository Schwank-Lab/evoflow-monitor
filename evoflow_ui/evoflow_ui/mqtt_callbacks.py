import json
import datetime
import psycopg2
from evoflow_ui.mqtt_cmd_handler import command_centre
from evoflow_ui.config import Config


def reactor_commands(reactor_id: int, experiment_id: int, command: str):
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
    cursor.execute(
        f"UPDATE exp_config SET exp_config_json = {experiment_config} WHERE experiment_id = {experiment_id}"
    )
    conn.commit()
    cursor.close()
    conn.close()

    payload = {
        "reactor_id": reactor_id,
        "command": "update_experiment",
        "experiment_id": experiment_id,
        "experiment_config": experiment_config,
    }

    command_centre().send_cmds(topic="commands", msg=json.dumps(payload))

    return None


def save_experiment_command(
    reactor_id: int, experiment_id: int, name: str, experiment_config: json
):
    # first update status on db
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_HOST,
    )
    cursor = conn.cursor()
    # create a new experiment
    cursor.execute(
        f"""
        INSERT INTO experiment (experiment_id, reactor_id, name, timestamp, insert_at, status) 
        VALUES (
            {experiment_id}, 
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
            {experiment_config},
            {int(datetime.date.now())}, 
            {datetime.date.now()}, 
        )
        """
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

    command_centre().send_cmds(topic="commands", msg=json.dumps(payload))

    return None
