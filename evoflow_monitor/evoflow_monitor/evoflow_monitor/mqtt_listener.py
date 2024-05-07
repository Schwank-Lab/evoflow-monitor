from typing import Callable, TypedDict
import paho.mqtt.client as mqtt
import json
import time
from config import Config
from db.tables_definition.schemas.idec import ReactorState
from evoflow_monitor.tasks import write_to_database


def write_experiment_data_to_db(x):
    print("Write experiment data to db")
    print(x)


def write_reactor_status_to_db(x):
    print("Write reactor status to db")
    print(x)


def parse_logs(x):
    print("Parsing logs")
    print(x)


def parse_commands(x):
    print("Parsing commands")
    print(x)


class EvohubTopics(TypedDict):
    topic: str
    script: Callable


mqtt_handlers: EvohubTopics = {
    "experiment_monitor": lambda x: write_experiment_data_to_db(x),
    "reactor_monitor": lambda x: write_reactor_status_to_db(x),
    "logs": lambda x: parse_commands(x),
    "commands": lambda x: parse_commands(x),
}


class MqttListener:
    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int,
        topic: str,
        topic_handlers: EvohubTopics,
    ):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        self.topic = topic
        self.topic_handlers = topic_handlers

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        data = json.loads(msg.payload.decode("utf-8"))
        self.topic_handlers[msg.topic](data)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    subscriber = MqttListener(
        client_id="monitor",
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topic="experiment_monitor",
        topic_handlers=mqtt_handlers,
    )

    try:
        # Run indefinitely
        while True:
            time.sleep(1)  # Sleep to allow MQTT messages to be processed
    except KeyboardInterrupt:
        # Gracefully stop the subscriber when interrupted
        subscriber.stop()
        print("Subscriber stopped.")
