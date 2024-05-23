from typing import Callable, TypedDict
import paho.mqtt.client as mqtt
import json
import time
import logging
from evoflow_listener.config import Config
from evoflow_listener.mqtt_callbacks import (
    write_experiment_status_to_db,
    write_reactor_status_to_db,
    parse_logs_experiment,
    parse_logs_reactor,
    parse_reactor_commands,
    parse_experiment_commands,
)


class EvohubTopics(TypedDict):
    topic: str
    script: Callable


mqtt_handlers: EvohubTopics = {
    "status/experiment": lambda x: write_experiment_status_to_db(x),
    "status/reactor": lambda x: write_reactor_status_to_db(x),
    "logs/experiment": lambda x: parse_logs_experiment(x),
    "logs/reactor": lambda x: parse_logs_reactor(x),
    "commands/experiment": lambda x: parse_experiment_commands(x),
    "commands/reactor": lambda x: parse_reactor_commands(x),
}


class MqttListener:
    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int,
        topics: list[str],
        topics_handlers: EvohubTopics,
    ):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        self.topics = topics
        self.topics_handlers = topics_handlers

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        client.subscribe([(t, 1) for t in self.topics])

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode("utf-8"))
        self.topics_handlers[msg.topic](data)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


def main():
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a file handler
    file_handler = logging.FileHandler("/var/log/mqtt_listener.log")
    file_handler.setLevel(logging.ERROR)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    subscriber = MqttListener(
        client_id="monitor",
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topics=list(mqtt_handlers.keys()),
        topics_handlers=mqtt_handlers,
    )

    try:
        # Run indefinitely
        while True:
            time.sleep(1)  # Sleep to allow MQTT messages to be processed
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    except KeyboardInterrupt:
        # Gracefully stop the subscriber when interrupted
        subscriber.stop()
        logger.info("Subscriber stopped.")
