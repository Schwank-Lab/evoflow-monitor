import json
import logging
from datetime import datetime

from evoflow_ui.db_callbacks import (
    save_experiment_command_on_db,
    update_experiment_command_on_db,
    update_experiment_state_on_db,
)
from evoflow_utils.config import Config
from evoflow_utils.mqtt_client import MqttClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the logging level for the console handler

# Optionally, set a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)


class ReactorStateListener:

    def __init__(self, time_valid_sec=10): 
        self._reactor_states = {}
        self._time_valid_sec = time_valid_sec
    
    def get_last_reactor_state(self, reactor_id):
        """Get last recieved reactor state for a given reactor. 
        
        If last update is too stale, return None.
        """
        last_update, last_state =  self._reactor_states.get(reactor_id, (None, None))
        if not last_update:
            return None
        time_since_last_update = datetime.now() - last_update 
        if time_since_last_update.total_seconds() > self._time_valid_sec:
            return None
        return last_state 

    def on_reactor_state(self, reactor_state):
        logger.debug(f"Received reactor state: {reactor_state}")
        if 'reactor_id' not in reactor_state.keys():
            logger.debug('Recived a reactor state with not reactor_id')
            return
        self._reactor_states[reactor_state['reactor_id']] = (datetime.now(), reactor_state)

reactor_state_listener = ReactorStateListener()

mqtt_client = MqttClient(
    'evoflow_ui_local_' + str(datetime.now()),
    str(Config.MQTT_HOST),
    int(Config.MQTT_PORT),
    logger=logger, 
    topics_handlers={
        'status/reactor': reactor_state_listener.on_reactor_state,
    }
)

def send_command(reactor_id, command, **kwargs):
    payload = {
        "reactor_id": reactor_id,
        "command": command,
        **kwargs,
    }

    mqtt_client.send_msg(topic="commands", msg=json.dumps(payload))

def start_stop_pause_experiment(reactor_id: int, experiment_id: int, command: str):
    # first update status on db
    update_experiment_state_on_db(reactor_id, experiment_id, command)
    send_command(reactor_id, command)



def update_experiment_command(reactor_id: int, experiment_id: int, experiment_config: json):
    # first update status on db
    update_experiment_command_on_db(experiment_id, experiment_config)
    send_command(reactor_id, "update_experiment", experiment_id=experiment_id, experiment_config=experiment_config)

def new_experiment_command(reactor_id: int, name: str, experiment_config: json):
    print(f"reactor_id {reactor_id}")
    print(f"new_exp_name {name}")
    print(f"exp_config {json.dumps(experiment_config)}")  # first update status on db

    experiment_id = save_experiment_command_on_db(reactor_id, name, experiment_config)

    send_command(reactor_id, "new_experiment", experiment_id=experiment_id, experiment_config=experiment_config)

def get_reactor_state(reactor_id):
    return reactor_state_listener.get_last_reactor_state(reactor_id)
