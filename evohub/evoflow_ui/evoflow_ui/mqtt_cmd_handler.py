from collections import deque
import json
import paho.mqtt.client as mqtt
from evoflow_utils.config import Config


class MqttCmdCentre:
    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int,
        topics: list[str],
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
        self.message_queue = deque(maxlen=10)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        self.client.subscribe([(t, 1) for t in self.topics])

    def on_message(self, client, userdata, msg):
        print(
            f"I am the controll centre. This is the topic: {msg.topic}, this is the message {msg}"
        )
        if msg.topic == "status/experiment":
            data = json.loads(msg.payload.decode("utf-8"))
            self.message_queue.append((msg, data))

    def send_cmds(self, topic, msg):
        print(
            f"I am the controll centre. This is the topic {topic}, this is the message {msg}"
        )
        self.client.publish(topic, msg)

    def format_message(self, data):
        return f"""
                {data}
        """

    def get_messages_from_queue(self):
        if len(self.message_queue) > 0:
            return [self.format_message(data) for _, data in self.message_queue]
        return [""]

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


def command_centre():
    cmd_centre = MqttCmdCentre(
        client_id="cmd_centre",
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topics=["commands"],
    )

    return cmd_centre
