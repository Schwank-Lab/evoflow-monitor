import json
import time
import paho.mqtt.client as mqtt
from evoflow_ui.config import Config
from types import TypedDict, Callable
from evoflow_ui.mqtt_callbacks import parse_experiment_commands, parse_reactor_commands


class EvohubTopics(TypedDict):
    topic: str
    script: Callable


mqtt_handlers: EvohubTopics = {
    "commands/experiment": lambda x: parse_experiment_commands(x),
    "commands/reactor": lambda x: parse_reactor_commands(x),
}


class MqttCmdCentre:
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
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        self.topics = topics
        self.topics_handlers = topics_handlers

    def on_connect(self, rc):
        print("Connected with result code " + str(rc))
        self.client.subscribe([(t, 1) for t in self.topics])

    def send_cmds(self):
        pass

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


def main():
    subscriber = MqttCmdCentre(
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
    except KeyboardInterrupt:
        # Gracefully stop the subscriber when interrupted
        subscriber.stop()
        print("Subscriber stopped.")
